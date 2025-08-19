import torch
import torch.nn as nn
import numpy as np

class LSTMAutoencoder(nn.Module):
    def __init__(self, input_size, hidden_size=64, num_layers=2, dropout=0.2):
        super(LSTMAutoencoder, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # Encoder
        self.encoder_lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Decoder
        self.decoder_lstm = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        # Output layer to reconstruct input
        self.output_layer = nn.Linear(hidden_size, input_size)
        
    def forward(self, x):
        batch_size, seq_len, _ = x.size()
        
        # Encode
        encoded, (hidden, cell) = self.encoder_lstm(x)
        
        # Use the last hidden state as the compressed representation
        context = encoded[:, -1, :].unsqueeze(1)  # (batch_size, 1, hidden_size)
        
        # Decode - repeat context for each timestep
        context_repeated = context.repeat(1, seq_len, 1)  # (batch_size, seq_len, hidden_size)
        
        decoded, _ = self.decoder_lstm(context_repeated)
        
        # Reconstruct input
        reconstructed = self.output_layer(decoded)
        
        return reconstructed
    
    def encode(self, x):
        """Get the encoded representation"""
        with torch.no_grad():
            encoded, _ = self.encoder_lstm(x)
            return encoded[:, -1, :]  # Return last hidden state

class AnomalyDetector:
    def __init__(self, model, threshold=None):
        self.model = model
        self.threshold = threshold
        
    def compute_reconstruction_error(self, x):
        """Compute reconstruction error for anomaly detection"""
        self.model.eval()
        with torch.no_grad():
            reconstructed = self.model(x)
            mse = torch.mean((x - reconstructed) ** 2, dim=(1, 2))
            return mse.numpy()
    
    def predict_anomalies(self, x, threshold=None):
        """Predict anomalies based on reconstruction error"""
        if threshold is None:
            threshold = self.threshold
        
        if threshold is None:
            raise ValueError("Threshold must be provided either during initialization or prediction")
        
        errors = self.compute_reconstruction_error(x)
        predictions = (errors > threshold).astype(int)
        
        return predictions, errors
    
    def fit_threshold(self, x_normal, percentile=95):
        """Fit threshold based on normal data reconstruction errors"""
        errors = self.compute_reconstruction_error(x_normal)
        self.threshold = np.percentile(errors, percentile)
        return self.threshold

def create_model(input_size, hidden_size=64, num_layers=2, dropout=0.2):
    """Factory function to create LSTM Autoencoder"""
    return LSTMAutoencoder(
        input_size=input_size,
        hidden_size=hidden_size,
        num_layers=num_layers,
        dropout=dropout
    )

def save_model(model, filepath):
    """Save model state dict"""
    torch.save(model.state_dict(), filepath)
    print(f"Model saved to {filepath}")

def load_model(filepath, input_size, hidden_size=64, num_layers=2, dropout=0.2):
    """Load model from state dict"""
    model = create_model(input_size, hidden_size, num_layers, dropout)
    model.load_state_dict(torch.load(filepath, map_location='cpu'))
    model.eval()
    print(f"Model loaded from {filepath}")
    return model
