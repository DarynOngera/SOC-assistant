"""
Network Traffic LSTM Autoencoder Training Module
Simple implementation for low compute environments
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, LSTM, Dense, RepeatVector, TimeDistributed
from tensorflow.keras.callbacks import EarlyStopping
import matplotlib.pyplot as plt
import joblib
import os

class NetworkTrafficProcessor:
    """Data preprocessing for network traffic features"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.encoders = {}
        self.feature_columns = []
    
    def load_data(self, filepath):
        """Load network traffic dataset"""
        df = pd.read_csv(filepath)
        print(f"Loaded {len(df)} records")
        
        # Fix: Handle different label column names
        if 'label' in df.columns and 'Label' not in df.columns:
            df = df.rename(columns={'label': 'Label'})
        elif 'Label' not in df.columns and 'label' not in df.columns:
            print("Warning: No label column found!")
            return df
            
        print(f"Normal records: {len(df[df['Label'] == 0])}")
        print(f"Attack records: {len(df[df['Label'] == 1])}")
        return df
    
    def select_features(self, df):
        """Select features that actually exist in your dataset"""
        # Get actual numeric columns from your dataset
        exclude_cols = ['id', 'Label', 'attack_cat']  # Don't use these for training
        
        # Get numeric columns
        numeric_features = []
        categorical_features = []
        
        for col in df.columns:
            if col in exclude_cols:
                continue
            elif df[col].dtype in ['int64', 'float64']:
                numeric_features.append(col)
            elif df[col].dtype == 'object' and df[col].nunique() < 100:  # Categorical with reasonable cardinality
                categorical_features.append(col)
        
        print(f"Selected {len(numeric_features)} numeric features")
        print(f"Selected {len(categorical_features)} categorical features") 
        print(f"Total features: {len(numeric_features) + len(categorical_features)}")
        
        return numeric_features, categorical_features, []
    
    def preprocess_data(self, df, fit=True):
        """Preprocess network traffic features"""
        # Use only NORMAL traffic for training (Label == 0)
        if fit:
            normal_df = df[df['Label'] == 0].copy()
            print(f"Training on {len(normal_df)} normal records only")
        else:
            normal_df = df.copy()
        
        numeric_features, categorical_features, _ = self.select_features(normal_df)
        
        # Handle missing values for numeric features
        for col in numeric_features:
            if col in normal_df.columns:
                normal_df[col] = pd.to_numeric(normal_df[col], errors='coerce')
                normal_df[col] = normal_df[col].fillna(normal_df[col].median())
        
        # Encode categorical features
        for col in categorical_features:
            if col in normal_df.columns:
                if fit:
                    le = LabelEncoder()
                    normal_df[col + '_encoded'] = le.fit_transform(normal_df[col].astype(str))
                    self.encoders[col] = le
                else:
                    if col in self.encoders:
                        # Handle unseen categories
                        def safe_transform(x):
                            try:
                                return self.encoders[col].transform([str(x)])[0]
                            except ValueError:
                                return 0  # Default for unseen categories
                        normal_df[col + '_encoded'] = normal_df[col].apply(safe_transform)
                    else:
                        # If encoder doesn't exist, create dummy encoding
                        normal_df[col + '_encoded'] = 0
        
        # Combine features
        encoded_categorical = [col + '_encoded' for col in categorical_features if col in normal_df.columns]
        all_features = numeric_features + encoded_categorical
        
        print(f"Final feature set: {len(all_features)} features")
        print("Feature breakdown:")
        print(f"  - Numeric: {len(numeric_features)}")
        print(f"  - Categorical (encoded): {len(encoded_categorical)}")
        
        feature_data = normal_df[all_features]
        
        # Scale features
        if fit:
            scaled_data = self.scaler.fit_transform(feature_data)
            self.feature_columns = all_features
        else:
            scaled_data = self.scaler.transform(feature_data)
        
        return scaled_data, normal_df['Label'].values if 'Label' in normal_df.columns else None
    
    def create_sequences(self, data, sequence_length=10):
        """Create time-based sequences for LSTM"""
        sequences = []
        
        # Simple sliding window approach
        for i in range(len(data) - sequence_length + 1):
            sequences.append(data[i:i + sequence_length])
        
        return np.array(sequences)

class NetworkLSTMModel:
    """LSTM Autoencoder for network anomaly detection"""
    
    def __init__(self, sequence_length=10, n_features=50):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.model = None
        self.threshold = None
    
    def build_model(self, encoding_dim=32):
        """Build LSTM Autoencoder"""
        # Input layer
        inputs = Input(shape=(self.sequence_length, self.n_features))
        
        # Encoder
        encoded = LSTM(64, return_sequences=True)(inputs)
        encoded = LSTM(encoding_dim, return_sequences=False)(encoded)
        
        # Decoder
        decoded = RepeatVector(self.sequence_length)(encoded)
        decoded = LSTM(encoding_dim, return_sequences=True)(decoded)
        decoded = LSTM(64, return_sequences=True)(decoded)
        decoded = TimeDistributed(Dense(self.n_features))(decoded)
        
        # Create model
        self.model = Model(inputs, decoded)
        self.model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        print(f"Model built: {self.model.count_params()} parameters")
        print(f"Input shape: ({self.sequence_length}, {self.n_features})")
        return self.model
    
    def train(self, X_train, epochs=50, batch_size=64, validation_split=0.2):
        """Train the LSTM Autoencoder"""
        callbacks = [
            EarlyStopping(patience=10, restore_best_weights=True, verbose=1)
        ]
        
        history = self.model.fit(
            X_train, X_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=callbacks,
            verbose=1
        )
        
        return history
    
    def calculate_threshold(self, X_train, percentile=95):
        """Calculate anomaly threshold based on training data"""
        # Predict on training data
        predictions = self.model.predict(X_train, verbose=0)
        
        # Calculate reconstruction errors
        mse = np.mean(np.power(X_train - predictions, 2), axis=(1, 2))
        
        # Set threshold at percentile
        self.threshold = np.percentile(mse, percentile)
        print(f"Anomaly threshold set at: {self.threshold:.4f}")
        
        return self.threshold
    
    def predict_anomalies(self, X_test):
        """Predict anomalies in test data"""
        # Reconstruct sequences
        predictions = self.model.predict(X_test, verbose=0)
        
        # Calculate reconstruction errors
        mse = np.mean(np.power(X_test - predictions, 2), axis=(1, 2))
        
        # Flag anomalies
        anomalies = mse > self.threshold
        
        return anomalies, mse
    
    def save_model(self, filepath):
        """Save trained model"""
        self.model.save(filepath)
        joblib.dump({
            'threshold': self.threshold,
            'sequence_length': self.sequence_length,
            'n_features': self.n_features
        }, filepath.replace('.h5', '_config.pkl'))

def train_network_model(data_path, model_save_path='models/'):
    """Main training pipeline for network traffic"""
    
    print("=== Network Traffic LSTM Training (ALL FEATURES) ===")
    
    # Create model directory
    os.makedirs(model_save_path, exist_ok=True)
    
    # Initialize processor
    processor = NetworkTrafficProcessor()
    
    # Load and preprocess data
    df = processor.load_data(data_path)
    X_scaled, y = processor.preprocess_data(df, fit=True)
    
    print(f"Preprocessed data shape: {X_scaled.shape}")
    print(f"Features: {len(processor.feature_columns)}")
    print("Feature names:", processor.feature_columns[:10], "...")  # Show first 10
    
    # Create sequences (small window for manageable compute)
    sequence_length = 10
    X_sequences = processor.create_sequences(X_scaled, sequence_length)
    
    print(f"Created {len(X_sequences)} sequences of length {sequence_length}")
    print(f"Sequence shape: {X_sequences.shape}")
    
    # Initialize and build model
    n_features = X_scaled.shape[1]
    model = NetworkLSTMModel(sequence_length=sequence_length, n_features=n_features)
    model.build_model(encoding_dim=min(32, n_features//2))  # Adjust encoding size
    
    # Train model
    print("Training model...")
    history = model.train(
        X_sequences, 
        epochs=50,
        batch_size=64
    )
    
    # Calculate threshold
    threshold = model.calculate_threshold(X_sequences)
    
    # Save model and processor
    model_path = os.path.join(model_save_path, 'network_lstm_model.h5')
    processor_path = os.path.join(model_save_path, 'network_processor.pkl')
    
    model.save_model(model_path)
    joblib.dump(processor, processor_path)
    
    print(f"Model saved to: {model_path}")
    print(f"Processor saved to: {processor_path}")
    print(f"Total features processed: {n_features}")
    
    # Plot training history
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 3, 1)
    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.title('Model Loss (All Features)')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    
    plt.subplot(1, 3, 2)
    plt.plot(history.history['mae'], label='Training MAE')
    plt.plot(history.history['val_mae'], label='Validation MAE')
    plt.title('Model MAE (All Features)')
    plt.xlabel('Epoch')
    plt.ylabel('MAE')
    plt.legend()
    
    plt.subplot(1, 3, 3)
    plt.text(0.1, 0.8, f"Total Features: {n_features}", fontsize=12, transform=plt.gca().transAxes)
    plt.text(0.1, 0.7, f"Sequences: {len(X_sequences)}", fontsize=12, transform=plt.gca().transAxes)
    plt.text(0.1, 0.6, f"Parameters: {model.model.count_params()}", fontsize=12, transform=plt.gca().transAxes)
    plt.text(0.1, 0.5, f"Threshold: {threshold:.4f}", fontsize=12, transform=plt.gca().transAxes)
    plt.title('Model Summary')
    plt.axis('off')
    
    plt.tight_layout()
    plt.savefig(os.path.join(model_save_path, 'network_training_history.png'))
    plt.show()
    
    return model, processor

def test_model(data_path, model_save_path='models/'):
    """Test the trained model"""
    
    print("=== Testing Network Model ===")
    
    # Load processor and model
    processor = joblib.load(os.path.join(model_save_path, 'network_processor.pkl'))
    
    # Load test data
    df = processor.load_data(data_path)
    X_scaled, y_true = processor.preprocess_data(df, fit=False)
    
    # Create sequences
    X_sequences = processor.create_sequences(X_scaled, sequence_length=10)
    
    # Load model
    from tensorflow.keras.models import load_model
    model_config = joblib.load(os.path.join(model_save_path, 'network_lstm_model_config.pkl'))
    
    # Create model instance and load weights
    model = NetworkLSTMModel(
        sequence_length=model_config['sequence_length'],
        n_features=model_config['n_features']
    )
    model.model = load_model(os.path.join(model_save_path, 'network_lstm_model.h5'))
    model.threshold = model_config['threshold']
    
    # Predict anomalies
    anomalies, scores = model.predict_anomalies(X_sequences)
    
    print(f"Detected {np.sum(anomalies)} anomalies out of {len(X_sequences)} sequences")
    print(f"Anomaly rate: {np.mean(anomalies):.2%}")
    
    return anomalies, scores

if __name__ == "__main__":
    # Example usage
    data_file = "data/train.csv"  # Your dataset file
    
    # Train model
    model, processor = train_network_model(data_file)
    
    # Test model (optional)
    # anomalies, scores = test_model(data_file)
