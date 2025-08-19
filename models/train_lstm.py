import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import os
import json
from sklearn.model_selection import train_test_split
from lstm_autoencoder import LSTMAutoencoder, AnomalyDetector, save_model
import matplotlib.pyplot as plt

def load_processed_data(data_dir='../data/processed'):
    """Load processed sequences and labels"""
    sequences = np.load(os.path.join(data_dir, 'sequences.npy'))
    labels = np.load(os.path.join(data_dir, 'labels.npy'))
    
    with open(os.path.join(data_dir, 'metadata.json'), 'r') as f:
        metadata = json.load(f)
    
    print(f"Loaded data: {sequences.shape}, Labels: {labels.shape}")
    print(f"Anomaly rate: {labels.mean():.2%}")
    
    return sequences, labels, metadata

def prepare_training_data(sequences, labels, test_size=0.2, normal_only=True):
    """Prepare training data - use only normal sequences for autoencoder training"""
    
    if normal_only:
        # Use only normal sequences for training autoencoder
        normal_indices = labels == 0
        train_sequences = sequences[normal_indices]
        print(f"Using {len(train_sequences)} normal sequences for training")
        
        # Split normal data for training/validation
        X_train, X_val = train_test_split(train_sequences, test_size=test_size, random_state=42)
        
        # Keep all data for testing (including anomalies)
        X_test = sequences
        y_test = labels
        
    else:
        # Use all data
        X_train, X_test, _, y_test = train_test_split(
            sequences, labels, test_size=test_size, random_state=42, stratify=labels
        )
        X_train, X_val = train_test_split(X_train, test_size=0.2, random_state=42)
    
    print(f"Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")
    
    return X_train, X_val, X_test, y_test

def create_data_loaders(X_train, X_val, batch_size=32):
    """Create PyTorch data loaders"""
    
    # Convert to tensors
    X_train_tensor = torch.FloatTensor(X_train)
    X_val_tensor = torch.FloatTensor(X_val)
    
    # Create datasets (for autoencoder, input = target)
    train_dataset = TensorDataset(X_train_tensor, X_train_tensor)
    val_dataset = TensorDataset(X_val_tensor, X_val_tensor)
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loader, val_loader

def train_model(model, train_loader, val_loader, num_epochs=50, learning_rate=0.001, patience=10):
    """Train the LSTM Autoencoder"""
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
    
    train_losses = []
    val_losses = []
    best_val_loss = float('inf')
    patience_counter = 0
    
    print(f"Training on device: {device}")
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    for epoch in range(num_epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                outputs = model(batch_x)
                loss = criterion(outputs, batch_y)
                val_loss += loss.item()
        
        # Calculate average losses
        avg_train_loss = train_loss / len(train_loader)
        avg_val_loss = val_loss / len(val_loader)
        
        train_losses.append(avg_train_loss)
        val_losses.append(avg_val_loss)
        
        # Learning rate scheduling
        scheduler.step(avg_val_loss)
        
        # Early stopping
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            # Save best model
            os.makedirs('checkpoints', exist_ok=True)
            save_model(model, 'checkpoints/best_model.pth')
        else:
            patience_counter += 1
        
        if epoch % 10 == 0 or patience_counter >= patience:
            print(f'Epoch [{epoch+1}/{num_epochs}], Train Loss: {avg_train_loss:.6f}, Val Loss: {avg_val_loss:.6f}')
        
        if patience_counter >= patience:
            print(f"Early stopping at epoch {epoch+1}")
            break
    
    # Load best model
    model.load_state_dict(torch.load('checkpoints/best_model.pth', map_location=device))
    
    return model, train_losses, val_losses

def evaluate_model(model, X_test, y_test):
    """Evaluate the model on test data"""
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    
    # Create anomaly detector
    detector = AnomalyDetector(model)
    
    # Convert test data to tensor
    X_test_tensor = torch.FloatTensor(X_test).to(device)
    
    # Compute reconstruction errors
    reconstruction_errors = detector.compute_reconstruction_error(X_test_tensor)
    
    # Fit threshold on normal data
    normal_indices = y_test == 0
    normal_errors = reconstruction_errors[normal_indices]
    threshold = detector.fit_threshold(torch.FloatTensor(X_test[normal_indices]).to(device))
    
    # Predict anomalies
    predictions, errors = detector.predict_anomalies(X_test_tensor)
    
    # Calculate metrics
    from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
    
    precision = precision_score(y_test, predictions)
    recall = recall_score(y_test, predictions)
    f1 = f1_score(y_test, predictions)
    auc = roc_auc_score(y_test, reconstruction_errors)
    
    # False Negative Rate
    fn = np.sum((y_test == 1) & (predictions == 0))
    tp = np.sum((y_test == 1) & (predictions == 1))
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
    
    metrics = {
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'auc_roc': auc,
        'false_negative_rate': fnr,
        'threshold': threshold
    }
    
    print("\nEvaluation Results:")
    print(f"Precision: {precision:.3f}")
    print(f"Recall: {recall:.3f}")
    print(f"F1-Score: {f1:.3f}")
    print(f"AUC-ROC: {auc:.3f}")
    print(f"False Negative Rate: {fnr:.3f}")
    print(f"Threshold: {threshold:.6f}")
    
    return metrics, reconstruction_errors, predictions

def plot_training_history(train_losses, val_losses):
    """Plot training history"""
    plt.figure(figsize=(10, 6))
    plt.plot(train_losses, label='Training Loss')
    plt.plot(val_losses, label='Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training History')
    plt.legend()
    plt.grid(True)
    plt.savefig('training_history.png')
    plt.show()

def save_results(metrics, model_config):
    """Save training results"""
    results = {
        'model_config': model_config,
        'metrics': metrics,
        'timestamp': torch.datetime.now().isoformat() if hasattr(torch, 'datetime') else 'unknown'
    }
    
    os.makedirs('../logs', exist_ok=True)
    with open('../logs/training_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("Results saved to ../logs/training_results.json")

def main():
    """Main training pipeline"""
    print("=" * 50)
    print("LSTM Autoencoder Training")
    print("=" * 50)
    
    # Load data
    sequences, labels, metadata = load_processed_data()
    
    # Prepare training data
    X_train, X_val, X_test, y_test = prepare_training_data(sequences, labels)
    
    # Create data loaders
    train_loader, val_loader = create_data_loaders(X_train, X_val, batch_size=32)
    
    # Model configuration
    input_size = sequences.shape[2]
    hidden_size = 64
    num_layers = 2
    dropout = 0.2
    
    model_config = {
        'input_size': input_size,
        'hidden_size': hidden_size,
        'num_layers': num_layers,
        'dropout': dropout
    }
    
    # Create model
    model = LSTMAutoencoder(
        input_size=input_size,
        hidden_size=hidden_size,
        num_layers=num_layers,
        dropout=dropout
    )
    
    print(f"Model created with {sum(p.numel() for p in model.parameters()):,} parameters")
    
    # Train model
    model, train_losses, val_losses = train_model(
        model, train_loader, val_loader, 
        num_epochs=100, learning_rate=0.001, patience=15
    )
    
    # Evaluate model
    metrics, reconstruction_errors, predictions = evaluate_model(model, X_test, y_test)
    
    # Plot training history
    plot_training_history(train_losses, val_losses)
    
    # Save final model
    os.makedirs('checkpoints', exist_ok=True)
    save_model(model, 'checkpoints/final_model.pth')
    
    # Save results
    save_results(metrics, model_config)
    
    print("\n" + "=" * 50)
    print("Training Complete!")
    print("=" * 50)
    
    return model, metrics

if __name__ == "__main__":
    main()
