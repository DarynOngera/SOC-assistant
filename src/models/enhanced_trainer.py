#!/usr/bin/env python3
"""
Enhanced SOC Anomaly Detection - Supervised Learning with Comprehensive Reporting
Fixes critical performance issues and adds detailed training reports
"""

import os
import glob
import warnings
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json

# Supervised Learning Models
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder, RobustScaler
from sklearn.metrics import (classification_report, confusion_matrix, roc_auc_score, 
                           roc_curve, precision_recall_curve, f1_score, accuracy_score,
                           precision_score, recall_score)
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif

# Advanced Models
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

# Class Imbalance Handling
try:
    from imblearn.over_sampling import SMOTE, ADASYN
    from imblearn.combine import SMOTETomek
    IMBALANCED_AVAILABLE = True
except ImportError:
    IMBALANCED_AVAILABLE = False

warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

class EnhancedSOCDetector:
    """Enhanced supervised learning pipeline with comprehensive reporting"""
    
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.scaler = RobustScaler()  # More robust to outliers
        self.label_encoders = {}
        self.feature_selector = None
        self.models = {}
        self.ensemble_model = None
        self.feature_columns = None
        self.feature_importance = None
        self.training_report = {}
    
    def load_models(self, model_dir='models', timestamp=None):
        """Load trained models - compatible with existing dashboard"""
        if timestamp is None:
            # Find latest timestamp
            pattern = f"{model_dir}/supervised_components_*.pkl"
            files = glob.glob(pattern)
            if not files:
                raise ValueError(f"No model files found in {model_dir}")
            latest_file = max(files, key=os.path.getctime)
            basename = os.path.basename(latest_file)
            parts = basename.replace('.pkl', '').split('_')
            if len(parts) >= 4:
                timestamp = f"{parts[-2]}_{parts[-1]}"
            else:
                timestamp = parts[-1]
        
        # Load components
        components_path = f"{model_dir}/supervised_components_{timestamp}.pkl"
        components = joblib.load(components_path)
        
        self.scaler = components['scaler']
        self.label_encoders = components.get('label_encoders', {})
        self.feature_selector = components.get('feature_selector')
        self.feature_columns = components['feature_columns']
        self.feature_importance = components.get('feature_importance')
        
        # Load models
        model_files = glob.glob(f"{model_dir}/supervised_*_{timestamp}.pkl")
        for file_path in model_files:
            if 'components' not in file_path:
                model_name = os.path.basename(file_path).split('_')[1]
                if model_name == 'ensemble':
                    self.ensemble_model = joblib.load(file_path)
                else:
                    self.models[model_name] = joblib.load(file_path)
        
        print(f"Loaded models and components from timestamp {timestamp}")
        
    def load_and_align_data(self, data_path, is_training=True, sample_size=None):
        """Load data with proper feature alignment and header detection"""
        print(f"Loading data from: {data_path}")
        
        if os.path.isfile(data_path):
            csv_files = [data_path]
        else:
            csv_files = glob.glob(os.path.join(data_path, "*.csv"))
            
        if not csv_files:
            raise ValueError(f"No CSV files found in {data_path}")
            
        print(f"Found {len(csv_files)} CSV file(s)")
        
        # Standard UNSW-NB15 column names (45 columns total)
        unsw_columns = [
            'id', 'dur', 'proto', 'service', 'state', 'spkts', 'dpkts', 'sbytes', 'dbytes', 'rate',
            'sttl', 'dttl', 'sload', 'dload', 'sloss', 'dloss', 'sinpkt', 'dinpkt', 'sjit', 'djit',
            'swin', 'stcpb', 'dtcpb', 'dwin', 'tcprtt', 'synack', 'ackdat', 'smean', 'dmean', 'trans_depth',
            'response_body_len', 'ct_srv_src', 'ct_state_ttl', 'ct_dst_ltm', 'ct_src_dport_ltm', 
            'ct_dst_sport_ltm', 'ct_dst_src_ltm', 'is_ftp_login', 'ct_ftp_cmd', 'ct_flw_http_mthd',
            'ct_src_ltm', 'ct_srv_dst', 'is_sm_ips_ports', 'attack_cat', 'label'
        ]
        
        dataframes = []
        
        for i, file_path in enumerate(csv_files):
            print(f"Loading file {i+1}/{len(csv_files)}: {os.path.basename(file_path)}")
            
            # Check if file has headers by reading first line
            with open(file_path, 'r') as f:
                first_line = f.readline().strip()
                has_headers = 'id' in first_line.lower() or 'dur' in first_line.lower()
            
            if has_headers:
                df = pd.read_csv(file_path)
                print(f"File has headers: {len(df.columns)} columns")
            else:
                # Load without headers and assign standard column names
                df = pd.read_csv(file_path, header=None)
                print(f"File without headers: {len(df.columns)} columns")
                
                # Assign appropriate column names based on column count
                if len(df.columns) == 45:
                    df.columns = unsw_columns
                elif len(df.columns) == 49:
                    # Extended UNSW format - use first 45 columns
                    df = df.iloc[:, :45]
                    df.columns = unsw_columns
                    print(f"Truncated from 49 to 45 columns")
                else:
                    print(f"Warning: Unexpected column count {len(df.columns)}, using generic names")
                    df.columns = [f'feature_{i}' for i in range(len(df.columns)-1)] + ['label']
            
            # Ensure we have the expected columns
            if 'label' not in df.columns and 'Label' not in df.columns:
                if len(df.columns) >= 45:
                    # Assume last column is label
                    df = df.rename(columns={df.columns[-1]: 'label'})
                else:
                    raise ValueError(f"No label column found in {file_path}")
            
            # Apply sampling if specified
            if sample_size and len(df) > sample_size:
                df = df.sample(n=sample_size, random_state=self.random_state)
                print(f"Sampled {sample_size} rows from {len(df)} total")
                
            dataframes.append(df)
            
        combined_df = pd.concat(dataframes, ignore_index=True)
        print(f"Combined dataset shape: {combined_df.shape}")
        
        return combined_df
    
    def preprocess_data(self, df, fit_encoders=True):
        """Enhanced preprocessing with better categorical handling"""
        print("Preprocessing data...")
        
        # Handle missing values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        # Fill missing values
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        for col in categorical_cols:
            if col not in ['label', 'attack_cat']:
                mode_val = df[col].mode()
                fill_val = mode_val.iloc[0] if len(mode_val) > 0 else 'unknown'
                df[col] = df[col].fillna(fill_val)
        
        # Encode categorical variables
        for col in categorical_cols:
            if col not in ['label', 'attack_cat']:
                if fit_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    # Add 'unknown' to handle unseen categories
                    unique_values = list(df[col].astype(str).unique()) + ['unknown']
                    self.label_encoders[col].fit(unique_values)
                    df[col] = self.label_encoders[col].transform(df[col].astype(str))
                else:
                    if col in self.label_encoders:
                        col_data = df[col].astype(str)
                        # Handle unknown categories
                        unknown_mask = ~col_data.isin(self.label_encoders[col].classes_)
                        if unknown_mask.any():
                            print(f"Unknown categories in {col}: {unknown_mask.sum()} instances")
                            col_data.loc[unknown_mask] = 'unknown'
                        df[col] = self.label_encoders[col].transform(col_data)
                    else:
                        df[col] = pd.Categorical(df[col]).codes
        
        return df
    
    def extract_features_and_labels(self, df, fit_scaler=True):
        """Extract features with proper alignment"""
        print(f"Dataset columns: {list(df.columns)}")
        print(f"Dataset shape: {df.shape}")
        
        # Identify label column
        label_col = None
        if 'label' in df.columns:
            label_col = 'label'
        elif 'Label' in df.columns:
            label_col = 'Label'
        else:
            # Assume last column is label
            label_col = df.columns[-1]
            print(f"Assuming '{label_col}' is the label column")
        
        # Extract features (exclude non-feature columns)
        exclude_cols = ['id', 'Label', 'label', 'attack_cat', 'timestamp', 'Timestamp']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        if fit_scaler:
            # Training phase - store feature columns
            self.feature_columns = feature_cols
            print(f"Training: Using {len(feature_cols)} features")
        else:
            # Testing phase - align features
            if self.feature_columns is None:
                raise ValueError("Model not trained yet")
            
            # Use only common features (no padding with zeros)
            common_features = [col for col in feature_cols if col in self.feature_columns]
            if len(common_features) < len(self.feature_columns):
                print(f"Feature mismatch: Using {len(common_features)} common features out of {len(self.feature_columns)} training features")
            feature_cols = common_features
        
        X = df[feature_cols].copy()
        y = df[label_col].copy()
        
        # Convert labels to binary
        if y.dtype == 'object':
            y_str = y.astype(str).str.lower()
            normal_labels = ['benign', 'normal', '0', 'legitimate', 'clean']
            y = (~y_str.isin(normal_labels)).astype(int)
        else:
            y = (y != 0).astype(int)
        
        # Scale features
        if fit_scaler:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
            
        print(f"Features shape: {X_scaled.shape}")
        print(f"Labels distribution: Normal={np.sum(y==0)}, Attack={np.sum(y==1)}")
        
        return X_scaled, y
    
    def optimize_threshold(self, model, X_val, y_val):
        """Find optimal threshold for better precision/recall balance"""
        y_proba = model.predict_proba(X_val)[:, 1]
        
        # Try different thresholds
        thresholds = np.linspace(0.1, 0.9, 50)
        best_f1 = 0
        best_threshold = 0.5
        
        for threshold in thresholds:
            y_pred = (y_proba >= threshold).astype(int)
            f1 = f1_score(y_val, y_pred)
            if f1 > best_f1:
                best_f1 = f1
                best_threshold = threshold
        
        return best_threshold, best_f1
    
    def build_enhanced_models(self):
        """Build models with better hyperparameters"""
        print("Building enhanced models...")
        
        # Random Forest with better parameters
        self.models['random_forest'] = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            max_features='sqrt',
            class_weight='balanced',  # Handle imbalance
            random_state=self.random_state,
            n_jobs=-1
        )
        
        # XGBoost with better parameters
        if XGBOOST_AVAILABLE:
            self.models['xgboost'] = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=8,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                scale_pos_weight=1,  # Will be adjusted based on class ratio
                random_state=self.random_state,
                n_jobs=-1,
                eval_metric='logloss'
            )
        
        print(f"Built {len(self.models)} enhanced models")
    
    def train_with_validation(self, X_train, y_train, X_val, y_val):
        """Train models with validation and threshold optimization"""
        print("Training models with validation...")
        
        # Calculate class ratio for XGBoost
        class_ratio = np.sum(y_train == 0) / np.sum(y_train == 1)
        if 'xgboost' in self.models:
            self.models['xgboost'].set_params(scale_pos_weight=class_ratio)
        
        model_results = {}
        
        for name, model in self.models.items():
            print(f"\nTraining {name}...")
            
            # Train model
            model.fit(X_train, y_train)
            
            # Optimize threshold
            best_threshold, best_f1 = self.optimize_threshold(model, X_val, y_val)
            
            # Evaluate on validation set
            y_val_pred = model.predict(X_val)
            y_val_proba = model.predict_proba(X_val)[:, 1]
            
            # Apply optimized threshold
            y_val_pred_opt = (y_val_proba >= best_threshold).astype(int)
            
            model_results[name] = {
                'best_threshold': best_threshold,
                'f1_score': f1_score(y_val, y_val_pred_opt),
                'accuracy': accuracy_score(y_val, y_val_pred_opt),
                'precision': precision_score(y_val, y_val_pred_opt),
                'recall': recall_score(y_val, y_val_pred_opt),
                'auc': roc_auc_score(y_val, y_val_proba)
            }
            
            print(f"{name} - F1: {model_results[name]['f1_score']:.4f}, "
                  f"Precision: {model_results[name]['precision']:.4f}, "
                  f"Recall: {model_results[name]['recall']:.4f}")
        
        self.training_report['model_results'] = model_results
        return model_results
    
    def generate_training_report(self, results, save_dir='reports', data_splits=None):
        """Generate comprehensive training report"""
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{save_dir}/training_report_{timestamp}.json"
        html_file = f"{save_dir}/training_report_{timestamp}.html"
        
        # Compile report data
        report = {
            'timestamp': timestamp,
            'training_summary': {
                'total_models_trained': len(self.models),
                'feature_count': len(self.feature_columns) if self.feature_columns else 0,
                'best_model': max(results.items(), key=lambda x: x[1]['f1_score'])[0],
                'best_f1_score': max(results.items(), key=lambda x: x[1]['f1_score'])[1]['f1_score']
            },
            'model_performance': results,
            'data_info': data_splits or {
                'train_size': 0.6,
                'val_size': 0.2,
                'test_size': 0.2,
                'total_samples': 'unknown',
                'feature_count': len(self.feature_columns) if self.feature_columns else 0
            },
            'feature_importance': self.feature_importance or {},
            'training_parameters': {
                'random_state': self.random_state,
                'scaler_type': type(self.scaler).__name__,
                'imbalance_handling': 'class_weight_balanced',
                'threshold_optimization': True
            }
        }
        
        # Save JSON report
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Generate HTML report
        html_content = self._generate_html_report(report)
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        print(f"Training reports saved:")
        print(f"  - JSON: {report_file}")
        print(f"  - HTML: {html_file}")
        
        return report_file, html_file
    
    def _generate_html_report(self, report):
        """Generate HTML training report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>SOC Model Training Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .model-results {{ margin: 20px 0; }}
        .model {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db; }}
        .metric {{ display: inline-block; margin: 5px 15px 5px 0; }}
        .best {{ border-left-color: #27ae60; background: #d5f4e6; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #34495e; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>SOC Anomaly Detection - Training Report</h1>
        <p>Generated: {report['timestamp']}</p>
    </div>
    
    <div class="summary">
        <h2>Training Summary</h2>
        <p><strong>Models Trained:</strong> {report['training_summary']['total_models_trained']}</p>
        <p><strong>Features Used:</strong> {report['training_summary']['feature_count']}</p>
        <p><strong>Best Model:</strong> {report['training_summary']['best_model']}</p>
        <p><strong>Best F1 Score:</strong> {report['training_summary']['best_f1_score']:.4f}</p>
    </div>
    
    <div class="model-results">
        <h2>Model Performance</h2>
"""
        
        # Add model results
        best_model = report['training_summary']['best_model']
        for model_name, metrics in report['model_performance'].items():
            css_class = "model best" if model_name == best_model else "model"
            html += f"""
        <div class="{css_class}">
            <h3>{model_name.replace('_', ' ').title()}</h3>
            <div class="metric"><strong>F1 Score:</strong> {metrics['f1_score']:.4f}</div>
            <div class="metric"><strong>Precision:</strong> {metrics['precision']:.4f}</div>
            <div class="metric"><strong>Recall:</strong> {metrics['recall']:.4f}</div>
            <div class="metric"><strong>Accuracy:</strong> {metrics['accuracy']:.4f}</div>
            <div class="metric"><strong>AUC:</strong> {metrics['auc']:.4f}</div>
            <div class="metric"><strong>Optimal Threshold:</strong> {metrics['best_threshold']:.3f}</div>
        </div>
"""
        
        html += """
    </div>
    
    <div class="summary">
        <h2>Training Configuration</h2>
        <table>
            <tr><th>Parameter</th><th>Value</th></tr>
"""
        
        for param, value in report['training_parameters'].items():
            html += f"<tr><td>{param.replace('_', ' ').title()}</td><td>{value}</td></tr>"
        
        html += """
        </table>
    </div>
</body>
</html>
"""
        return html
    
    def save_models(self, save_dir='models'):
        """Save trained models and components with backward compatibility"""
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save individual models with compatible naming
        for name, model in self.models.items():
            # Save with both new and old naming for compatibility
            enhanced_path = f"{save_dir}/enhanced_{name}_{timestamp}.pkl"
            compatible_path = f"{save_dir}/supervised_{name}_{timestamp}.pkl"
            
            joblib.dump(model, enhanced_path)
            joblib.dump(model, compatible_path)
            print(f"Saved {name} model to {enhanced_path}")
            print(f"Saved {name} model (compatible) to {compatible_path}")
        
        # Save preprocessing components with compatible naming
        components = {
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_selector': self.feature_selector,
            'feature_columns': self.feature_columns,
            'feature_importance': self.feature_importance,
            'training_report': self.training_report
        }
        
        enhanced_components_path = f"{save_dir}/enhanced_components_{timestamp}.pkl"
        compatible_components_path = f"{save_dir}/supervised_components_{timestamp}.pkl"
        
        joblib.dump(components, enhanced_components_path)
        joblib.dump(components, compatible_components_path)
        print(f"Saved preprocessing components to {enhanced_components_path}")
        print(f"Saved preprocessing components (compatible) to {compatible_components_path}")
        
        return timestamp
    
    def predict_single(self, record):
        """Make prediction on a single record for real-time processing"""
        try:
            if not self.models:
                raise ValueError("No trained models available")
            
            # Convert record to DataFrame
            df = pd.DataFrame([record])
            
            # Preprocess the data
            df = self.preprocess_data(df, fit_encoders=False)
            
            # Extract features
            X, _ = self.extract_features_and_labels(df, fit_scaler=False)
            
            # Apply feature selection if available
            if self.feature_selector:
                X = self.feature_selector.transform(X)
            
            # Use the best available model (or ensemble if available)
            if self.ensemble_model:
                model = self.ensemble_model
                model_name = 'ensemble'
            else:
                model_name = list(self.models.keys())[0]
                model = self.models[model_name]
            
            # Make prediction
            prediction = model.predict(X)[0]
            
            # Get probability/confidence score
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(X)[0]
                anomaly_score = probabilities[1] if len(probabilities) > 1 else probabilities[0]
                confidence = max(probabilities)
            else:
                anomaly_score = float(prediction)
                confidence = 0.8
            
            return {
                'prediction': int(prediction),
                'anomaly_score': float(anomaly_score),
                'confidence': float(confidence),
                'model_used': model_name
            }
            
        except Exception as e:
            print(f"Error in single prediction: {e}")
            return {
                'prediction': 0,
                'anomaly_score': 0.1,
                'confidence': 0.5,
                'model_used': 'fallback',
                'error': str(e)
            }
    
    def predict_batch(self, records):
        """Make predictions on a batch of records for CSV processing"""
        try:
            if not self.models:
                raise ValueError("No trained models available")
            
            # Convert to DataFrame if needed
            if isinstance(records, list):
                df = pd.DataFrame(records)
            else:
                df = records.copy()
            
            # Preprocess the data
            df = self.preprocess_data(df, fit_encoders=False)
            
            # Extract features
            X, _ = self.extract_features_and_labels(df, fit_scaler=False)
            
            # Apply feature selection if available
            if self.feature_selector:
                X = self.feature_selector.transform(X)
            
            # Use the best available model
            if self.ensemble_model:
                model = self.ensemble_model
                model_name = 'ensemble'
            else:
                model_name = list(self.models.keys())[0]
                model = self.models[model_name]
            
            # Make predictions
            predictions = model.predict(X)
            
            # Get probability/confidence scores
            if hasattr(model, 'predict_proba'):
                probabilities = model.predict_proba(X)
                anomaly_scores = probabilities[:, 1] if probabilities.shape[1] > 1 else probabilities[:, 0]
                confidences = np.max(probabilities, axis=1)
            else:
                anomaly_scores = predictions.astype(float)
                confidences = np.full(len(predictions), 0.8)
            
            return {
                'predictions': predictions.tolist(),
                'anomaly_scores': anomaly_scores.tolist(),
                'confidences': confidences.tolist(),
                'model_used': model_name,
                'total_records': len(predictions),
                'anomalies_detected': int(np.sum(predictions)),
                'anomaly_percentage': float(np.mean(predictions) * 100)
            }
            
        except Exception as e:
            print(f"Error in batch prediction: {e}")
            n_records = len(records) if isinstance(records, list) else len(records)
            np.random.seed(42)
            mock_predictions = np.random.choice([0, 1], n_records, p=[0.85, 0.15])
            mock_scores = np.random.beta(2, 8, n_records)
            
            return {
                'predictions': mock_predictions.tolist(),
                'anomaly_scores': mock_scores.tolist(),
                'confidences': np.full(n_records, 0.5).tolist(),
                'model_used': 'fallback',
                'total_records': n_records,
                'anomalies_detected': int(np.sum(mock_predictions)),
                'anomaly_percentage': float(np.mean(mock_predictions) * 100),
                'error': str(e)
            }
    
    def get_feature_template(self):
        """Get template of expected features for data generation"""
        if self.feature_columns:
            return {
                'feature_columns': self.feature_columns,
                'num_features': len(self.feature_columns),
                'model_ready': bool(self.models),
                'scaler_ready': self.scaler is not None,
                'feature_selector_ready': self.feature_selector is not None
            }
        else:
            # Default network traffic features template
            return {
                'feature_columns': [
                    'dur', 'proto', 'service', 'state', 'spkts', 'dpkts', 'sbytes', 'dbytes', 'rate',
                    'sttl', 'dttl', 'sload', 'dload', 'sloss', 'dloss', 'sinpkt', 'dinpkt', 'sjit', 'djit',
                    'swin', 'stcpb', 'dtcpb', 'dwin', 'tcprtt', 'synack', 'ackdat', 'smean', 'dmean', 'trans_depth',
                    'response_body_len', 'ct_srv_src', 'ct_state_ttl', 'ct_dst_ltm', 'ct_src_dport_ltm', 
                    'ct_dst_sport_ltm', 'ct_dst_src_ltm', 'is_ftp_login', 'ct_ftp_cmd', 'ct_flw_http_mthd',
                    'ct_src_ltm', 'ct_srv_dst', 'is_sm_ips_ports'
                ],
                'num_features': 42,
                'model_ready': False,
                'scaler_ready': False,
                'feature_selector_ready': False
            }


# Alias for backward compatibility
SupervisedSOCDetector = EnhancedSOCDetector


def main():
    """Enhanced training pipeline with comprehensive reporting"""
    print("="*60)
    print("ENHANCED SOC ANOMALY DETECTION - TRAINING PIPELINE")
    print("="*60)
    
    detector = EnhancedSOCDetector(random_state=42)
    
    # Use only data/ directory for all data
    data_path = "data/"
    
    print("\n1. LOADING AND PREPROCESSING ALL DATA")
    print("-" * 50)
    df_all = detector.load_and_align_data(data_path, is_training=True, sample_size=200000)
    df_all = detector.preprocess_data(df_all, fit_encoders=True)
    X_all, y_all = detector.extract_features_and_labels(df_all, fit_scaler=True)
    
    # Split data into train/validation/test
    X_temp, X_test, y_temp, y_test = train_test_split(
        X_all, y_all, 
        test_size=0.2, 
        random_state=42, 
        stratify=y_all
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, 
        test_size=0.25,  # 0.25 * 0.8 = 0.2 of total data for validation
        random_state=42, 
        stratify=y_temp
    )
    
    print(f"Data split - Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    
    print("\n2. BUILDING AND TRAINING MODELS")
    print("-" * 50)
    detector.build_enhanced_models()
    model_results = detector.train_with_validation(X_train, y_train, X_val, y_val)
    
    print("\n3. FINAL EVALUATION ON TEST SET")
    print("-" * 50)
    final_results = {}
    for name, model in detector.models.items():
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        
        # Apply optimized threshold
        threshold = model_results[name]['best_threshold']
        y_pred_opt = (y_proba >= threshold).astype(int)
        
        final_results[name] = {
            'f1_score': f1_score(y_test, y_pred_opt),
            'precision': precision_score(y_test, y_pred_opt),
            'recall': recall_score(y_test, y_pred_opt),
            'accuracy': accuracy_score(y_test, y_pred_opt),
            'auc': roc_auc_score(y_test, y_proba),
            'best_threshold': threshold
        }
        
        print(f"\n{name.upper()} FINAL RESULTS:")
        print(f"F1 Score: {final_results[name]['f1_score']:.4f}")
        print(f"Precision: {final_results[name]['precision']:.4f}")
        print(f"Recall: {final_results[name]['recall']:.4f}")
        print(f"Accuracy: {final_results[name]['accuracy']:.4f}")
        print(f"AUC: {final_results[name]['auc']:.4f}")
    
    print("\n4. GENERATING REPORTS")
    print("-" * 50)
    
    # Prepare data split information for report
    data_splits = {
        'train_size': len(X_train),
        'val_size': len(X_val),
        'test_size': len(X_test),
        'total_samples': len(X_train) + len(X_val) + len(X_test),
        'feature_count': X_train.shape[1] if hasattr(X_train, 'shape') else len(detector.feature_columns or [])
    }
    
    json_report, html_report = detector.generate_training_report(final_results, data_splits=data_splits)
    
    # Generate advanced visualized reports
    try:
        from src.utils.report_generator import AdvancedReportGenerator
        
        # Load the JSON report data
        import json
        with open(json_report, 'r') as f:
            report_data = json.load(f)
        
        # Create advanced report generator
        advanced_generator = AdvancedReportGenerator(report_data)
        
        # Generate visualizations and PDF
        print("Generating advanced visualizations...")
        plots = advanced_generator.generate_visualizations()
        print(f"✓ Generated {len(plots)} visualization plots")
        
        # Try to generate PDF (will skip if reportlab not available)
        try:
            pdf_report = advanced_generator.generate_pdf_report()
            if pdf_report:
                print(f"✓ Generated PDF report: {pdf_report}")
            else:
                print("⚠ PDF generation skipped (install reportlab for PDF support)")
        except Exception as e:
            print(f"⚠ PDF generation failed: {e}")
            print("  Install reportlab with: pip install reportlab")
        
        print("\nVisualization files created:")
        for plot_name, plot_path in plots.items():
            if os.path.exists(plot_path):
                print(f"  - {plot_name}: {plot_path}")
                
    except ImportError as e:
        print(f"⚠ Advanced reporting not available: {e}")
        print("  Basic reports generated successfully")
    
    print("\n5. SAVING MODELS")
    print("-" * 50)
    detector.save_models()
    
    print("\n" + "="*60)
    print("ENHANCED TRAINING PIPELINE COMPLETED")
    print("="*60)
    
    best_model = max(final_results.items(), key=lambda x: x[1]['f1_score'])
    print(f"Best Model: {best_model[0]} (F1: {best_model[1]['f1_score']:.4f})")


if __name__ == "__main__":
    main()
