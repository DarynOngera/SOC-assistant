import pytest
import pandas as pd
import numpy as np
import os
import sys
sys.path.append('../data')
from clean import create_sample_cert_data, clean_data, encode_features, create_sequences

class TestDataProcessing:
    
    def test_create_sample_cert_data(self):
        """Test sample data creation"""
        df = create_sample_cert_data()
        
        assert len(df) == 1000
        assert 'date' in df.columns
        assert 'user' in df.columns
        assert 'anomaly_label' in df.columns
        assert df['anomaly_label'].sum() > 0  # Should have some anomalies
        assert df['anomaly_label'].mean() <= 0.1  # Should be minority class
    
    def test_clean_data(self):
        """Test data cleaning function"""
        df = create_sample_cert_data()
        
        # Add some missing values and duplicates for testing
        df.loc[0, 'user'] = None
        df.loc[1] = df.loc[0]  # Create duplicate
        
        df_clean = clean_data(df)
        
        assert len(df_clean) < len(df)  # Should remove rows
        assert not df_clean.isnull().any().any()  # No missing values
        assert 'hour' in df_clean.columns  # Feature engineering
        assert 'is_weekend' in df_clean.columns
    
    def test_encode_features(self):
        """Test feature encoding"""
        df = create_sample_cert_data()
        df_clean = clean_data(df)
        df_encoded, encoders = encode_features(df_clean)
        
        assert 'user_encoded' in df_encoded.columns
        assert 'pc_encoded' in df_encoded.columns
        assert len(encoders) == 5  # Should have 5 categorical encoders
        assert df_encoded['from_removable'].dtype in [int, bool]
    
    def test_create_sequences(self):
        """Test sequence creation"""
        df = create_sample_cert_data()
        df_clean = clean_data(df)
        df_encoded, encoders = encode_features(df_clean)
        
        sequences, labels = create_sequences(df_encoded, window_size=5)
        
        assert len(sequences) > 0
        assert len(sequences) == len(labels)
        assert sequences.shape[1] == 5  # Window size
        assert sequences.shape[2] == 12  # Number of features

if __name__ == "__main__":
    pytest.main([__file__])
