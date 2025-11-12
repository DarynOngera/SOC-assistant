#!/usr/bin/env python3
"""
Mininet Model Adapter for SOC Dashboard
Provides compatibility layer between Mininet models and dashboard
"""

import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

class MininetModelAdapter:
    """Adapter for Mininet-trained models"""
    
    def __init__(self, model_dir='models'):
        self.model_dir = Path(model_dir)
        self.model = None
        self.scaler = None
        self.feature_selector = None
        self.feature_columns = None
        self.metadata = None
        
        self.load_models()
    
    def load_models(self):
        """Load Mininet models"""
        try:
            # Load ensemble model (preferred)
            model_path = self.model_dir / 'mininet_ensemble_model.pkl'
            if model_path.exists():
                self.model = joblib.load(model_path)
            else:
                # Fallback to random forest
                model_path = self.model_dir / 'mininet_random_forest_model.pkl'
                self.model = joblib.load(model_path)
            
            # Load preprocessors
            self.scaler = joblib.load(self.model_dir / 'mininet_scaler.pkl')
            
            selector_path = self.model_dir / 'mininet_feature_selector.pkl'
            if selector_path.exists():
                self.feature_selector = joblib.load(selector_path)
            
            # Load feature columns
            self.feature_columns = joblib.load(self.model_dir / 'mininet_feature_columns.pkl')
            
            # Load metadata
            metadata_path = self.model_dir / 'mininet_model_metadata.pkl'
            if metadata_path.exists():
                self.metadata = joblib.load(metadata_path)
            
            return True
            
        except Exception as e:
            print(f"Error loading Mininet models: {e}")
            return False
    
    def predict_single(self, features):
        """Predict single sample (dashboard compatibility)"""
        try:
            # Convert to DataFrame
            if isinstance(features, dict):
                df = pd.DataFrame([features])
            else:
                df = pd.DataFrame([features])
            
            # Ensure all feature columns exist
            for col in self.feature_columns:
                if col not in df.columns:
                    df[col] = 0
            
            # Select only training features
            df = df[self.feature_columns]
            
            # Handle missing/infinite values
            df = df.fillna(0)
            df = df.replace([np.inf, -np.inf], 0)
            
            # Scale
            X_scaled = self.scaler.transform(df)
            
            # Feature selection
            if self.feature_selector:
                X_selected = self.feature_selector.transform(X_scaled)
            else:
                X_selected = X_scaled
            
            # Predict
            prediction = self.model.predict(X_selected)[0]
            probability = self.model.predict_proba(X_selected)[0]
            
            return {
                'prediction': int(prediction),
                'anomaly_score': float(probability[1]),
                'is_anomaly': bool(prediction == 1),
                'confidence': float(max(probability))
            }
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return {
                'prediction': 0,
                'anomaly_score': 0.0,
                'is_anomaly': False,
                'confidence': 0.0
            }
    
    def predict_batch(self, features_list):
        """Predict batch of samples"""
        results = []
        for features in features_list:
            result = self.predict_single(features)
            results.append(result)
        return results
    
    def get_feature_template(self):
        """Get feature template for data generation"""
        template = {col: 0.0 for col in self.feature_columns}
        return template
    
    def get_model_info(self):
        """Get model information"""
        return {
            'model_type': 'mininet_ensemble',
            'n_features': len(self.feature_columns),
            'feature_columns': self.feature_columns,
            'metadata': self.metadata
        }

# Backward compatibility aliases
SupervisedSOCDetector = MininetModelAdapter
