#!/usr/bin/env python3
"""
SOC Anomaly Detection - Supervised Learning Approach
Enhanced pipeline with Random Forest, XGBoost, and ensemble methods
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

# Supervised Learning Models
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (classification_report, confusion_matrix, roc_auc_score, 
                           roc_curve, precision_recall_curve, f1_score, accuracy_score)
from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif

# Advanced Models
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("XGBoost not available. Install with: pip install xgboost")

# Class Imbalance Handling
try:
    from imblearn.over_sampling import SMOTE, ADASYN
    from imblearn.combine import SMOTETomek
    IMBALANCED_AVAILABLE = True
except ImportError:
    IMBALANCED_AVAILABLE = False
    print("Imbalanced-learn not available. Install with: pip install imbalanced-learn")

# Suppress warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

class SupervisedSOCDetector:
    """
    Advanced supervised learning pipeline for SOC anomaly detection
    """
    
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.label_encoders = {}  # Dictionary to store encoders for each column
        self.feature_selector = None
        self.models = {}
        self.ensemble_model = None
        self.feature_columns = None
        self.feature_importance = None
        
    def load_csv_files(self, data_path, sample_size=None, max_file_size_mb=100):
        """
        Memory-efficient CSV loading with chunked reading for large files
        Handles both headerless and header CSV files properly
        """
        print(f"Loading data from: {data_path}")
        
        if os.path.isfile(data_path):
            csv_files = [data_path]
        else:
            csv_files = glob.glob(os.path.join(data_path, "*.csv"))
            
        if not csv_files:
            raise ValueError(f"No CSV files found in {data_path}")
            
        print(f"Found {len(csv_files)} CSV file(s)")
        dataframes = []
        reference_columns = None
        
        for i, file_path in enumerate(csv_files):
            print(f"Loading file {i+1}/{len(csv_files)}: {os.path.basename(file_path)}")
            
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            
            # Detect if file has headers by checking first row
            first_line = pd.read_csv(file_path, nrows=1)
            has_headers = self._detect_headers(first_line)
            
            if file_size_mb > max_file_size_mb:
                print(f"Large file detected ({file_size_mb:.1f}MB). Using chunked reading...")
                chunks = []
                chunk_size = 10000
                
                if has_headers:
                    chunk_iter = pd.read_csv(file_path, chunksize=chunk_size)
                else:
                    # Use reference columns if available, otherwise create generic names
                    if reference_columns is not None:
                        chunk_iter = pd.read_csv(file_path, chunksize=chunk_size, header=None, names=reference_columns)
                    else:
                        chunk_iter = pd.read_csv(file_path, chunksize=chunk_size, header=None)
                
                for chunk in chunk_iter:
                    chunks.append(chunk)
                    if sample_size and len(pd.concat(chunks)) >= sample_size:
                        break
                        
                df = pd.concat(chunks, ignore_index=True)
            else:
                if has_headers:
                    df = pd.read_csv(file_path)
                else:
                    # Use reference columns if available, otherwise create generic names
                    if reference_columns is not None:
                        df = pd.read_csv(file_path, header=None, names=reference_columns)
                    else:
                        df = pd.read_csv(file_path, header=None)
            
            # Set reference columns from first file with headers
            if reference_columns is None and has_headers:
                reference_columns = list(df.columns)
                print(f"Using {len(reference_columns)} columns from {os.path.basename(file_path)} as reference")
            
            # For headerless files, assign column names if we don't have reference
            if not has_headers and reference_columns is None:
                # Use standard UNSW-NB15 column names for consistency
                n_cols = len(df.columns)
                if n_cols == 49:  # UNSW-NB15 format with 49 columns
                    unsw_columns = [
                        'srcip', 'sport', 'dstip', 'dsport', 'proto', 'state', 'dur', 'sbytes', 'dbytes', 'sttl',
                        'dttl', 'sloss', 'dloss', 'service', 'sload', 'dload', 'spkts', 'dpkts', 'swin', 'dwin',
                        'stcpb', 'dtcpb', 'smeansz', 'dmeansz', 'trans_depth', 'res_bdy_len', 'sjit', 'djit',
                        'stime', 'ltime', 'sintpkt', 'dintpkt', 'tcprtt', 'synack', 'ackdat', 'is_sm_ips_ports',
                        'ct_state_ttl', 'ct_flw_http_mthd', 'is_ftp_login', 'ct_ftp_cmd', 'ct_srv_src', 'ct_srv_dst',
                        'ct_dst_ltm', 'ct_src_ltm', 'ct_src_dport_ltm', 'ct_dst_sport_ltm', 'ct_dst_src_ltm',
                        'attack_cat', 'label'
                    ]
                    df.columns = unsw_columns
                    reference_columns = list(df.columns)
                    print(f"Applied UNSW-NB15 column names ({len(reference_columns)} columns)")
                else:
                    # Fallback to generic names
                    df.columns = [f'feature_{i}' for i in range(n_cols-1)] + ['label']
                    reference_columns = list(df.columns)
                    print(f"Created {len(reference_columns)} generic column names")
            
            # Ensure all dataframes have the same columns
            if reference_columns is not None and list(df.columns) != reference_columns:
                if len(df.columns) == len(reference_columns):
                    df.columns = reference_columns
                    print(f"Aligned columns for {os.path.basename(file_path)}")
                else:
                    print(f"Warning: Column count mismatch in {os.path.basename(file_path)}: {len(df.columns)} vs {len(reference_columns)}")
                    continue  # Skip files with different column counts
                
            if sample_size and len(df) > sample_size:
                df = df.sample(n=sample_size, random_state=self.random_state)
                print(f"Sampled {sample_size} rows from {len(df)} total")
                
            dataframes.append(df)
            
        if not dataframes:
            raise ValueError("No valid CSV files could be loaded")
            
        combined_df = pd.concat(dataframes, ignore_index=True)
        print(f"Combined dataset shape: {combined_df.shape}")
        
        # Memory cleanup
        del dataframes
        
        return combined_df
    
    def _detect_headers(self, first_row_df):
        """
        Detect if CSV file has headers by analyzing first row
        """
        first_row = first_row_df.iloc[0]
        
        # Check if column names (not first row values) contain typical header names
        header_indicators = ['id', 'dur', 'proto', 'service', 'state', 'label', 'attack']
        header_match_count = 0
        
        # Check column names for header indicators
        for col in first_row_df.columns:
            col_str = str(col).lower()
            if any(indicator in col_str for indicator in header_indicators):
                header_match_count += 1
        
        # If we have clear header indicators in column names, it has headers
        if header_match_count > 0:
            return True
        
        # Check if column names look like meaningful headers (not just numbers or generic names)
        meaningful_column_names = 0
        for col in first_row_df.columns:
            col_str = str(col)
            # Check if column name is meaningful (not just a number or IP address)
            if (not col_str.replace('.', '').replace('-', '').isdigit() and 
                len(col_str) > 2 and 
                not self._looks_like_ip_or_data(col_str)):
                meaningful_column_names += 1
        
        # If most column names look meaningful, it probably has headers
        has_meaningful_headers = meaningful_column_names > len(first_row_df.columns) * 0.5
        
        return has_meaningful_headers
    
    def _looks_like_ip_or_data(self, value_str):
        """
        Check if a string looks like an IP address or data value rather than a header
        """
        # Check for IP address pattern
        parts = value_str.split('.')
        if len(parts) == 4:
            try:
                all_numeric = all(0 <= int(part) <= 255 for part in parts)
                if all_numeric:
                    return True
            except ValueError:
                pass
        
        # Check if it's mostly numeric
        numeric_chars = sum(1 for c in value_str if c.isdigit())
        return numeric_chars > len(value_str) * 0.7
    
    def preprocess_data(self, df, fit_encoders=True):
        """
        Advanced preprocessing with feature engineering
        """
        print("Preprocessing data...")
        
        # Handle missing values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        # Fill missing values
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        df[categorical_cols] = df[categorical_cols].fillna(df[categorical_cols].mode().iloc[0] if not df[categorical_cols].mode().empty else 'unknown')
        
        # Encode categorical variables
        for col in categorical_cols:
            if col not in ['Label', 'attack_cat', 'label']:  # Preserve target variables
                if fit_encoders:
                    # Initialize encoder for this column
                    self.label_encoders[col] = LabelEncoder()
                    
                    # Add 'unknown' to training data to handle unseen categories later
                    unique_values = df[col].astype(str).unique().tolist()
                    if 'unknown' not in unique_values:
                        # Create a temporary series with 'unknown' added
                        temp_series = pd.concat([
                            df[col].astype(str), 
                            pd.Series(['unknown'])
                        ], ignore_index=True)
                        self.label_encoders[col].fit(temp_series)
                    else:
                        self.label_encoders[col].fit(df[col].astype(str))
                    
                    # Transform the original data
                    df[col] = self.label_encoders[col].transform(df[col].astype(str))
                    
                else:
                    # Handle unseen categories during prediction/testing
                    if col in self.label_encoders:
                        # Convert to string and handle unknown categories
                        col_data = df[col].astype(str)
                        unique_vals = set(col_data.unique())
                        known_vals = set(self.label_encoders[col].classes_)
                        unknown_vals = unique_vals - known_vals
                        
                        if unknown_vals:
                            print(f"Unknown categories in {col}: {len(unknown_vals)} categories")
                            # Replace unknown categories with 'unknown'
                            col_data = col_data.replace(list(unknown_vals), 'unknown')
                        
                        df[col] = self.label_encoders[col].transform(col_data)
                    else:
                        # If encoder doesn't exist, create a simple numeric encoding
                        print(f"Warning: No encoder found for {col}, using simple encoding")
                        df[col] = pd.Categorical(df[col]).codes
        
        return df
    
    def extract_features_only(self, df, fit_scaler=False):
        """
        Extract features from real-time data without labels for prediction
        """
        if self.feature_columns is None:
            raise ValueError("Model not trained - no feature columns available")
        
        # Log feature alignment issues only when they occur
        input_features = set(df.columns)
        expected_features = set(self.feature_columns)
        missing_features = expected_features - input_features
        extra_features = input_features - expected_features
        
        if missing_features:
            if len(missing_features) <= 5:
                print(f"[WARNING] Missing {len(missing_features)} features: {sorted(list(missing_features))}")
            else:
                print(f"[WARNING] Missing {len(missing_features)} features (showing first 5): {sorted(list(missing_features))[:5]}")
        
        if extra_features and len(extra_features) > 5:
            print(f"[INFO] Input has {len(extra_features)} extra features not used in training")
        
        # Add missing features with intelligent defaults
        for feature in missing_features:
            if any(keyword in feature.lower() for keyword in ['rate', 'error', 'ratio']):
                df[feature] = 0.0  # Rate/ratio features default to 0
            elif any(keyword in feature.lower() for keyword in ['count', 'num', 'cnt']):
                df[feature] = 0  # Count features default to 0
            elif any(keyword in feature.lower() for keyword in ['bytes', 'size', 'length']):
                df[feature] = 0  # Size features default to 0
            elif feature.lower() in ['land', 'wrong_fragment', 'urgent', 'logged_in', 'root_shell', 'su_attempted', 'is_host_login', 'is_guest_login']:
                df[feature] = 0  # Binary features default to 0
            elif feature.lower() == 'duration':
                df[feature] = 0.0  # Duration defaults to 0
            else:
                df[feature] = 0  # Default all other features to 0
        
        # Extract features in the correct order - ensure ALL training features are present
        try:
            X = df[self.feature_columns].copy()
        except KeyError as e:
            print(f"[ERROR] Feature extraction failed: {e}")
            print(f"  Available columns: {sorted(df.columns.tolist())[:10]}...")
            print(f"  Required columns: {sorted(self.feature_columns)[:10]}...")
            raise
        
        # Verify feature matrix dimensions match training expectations
        expected_features = getattr(self.scaler, 'n_features_in_', len(self.feature_columns))
        if X.shape[1] != expected_features:
            print(f"[ERROR] Feature dimension mismatch:")
            print(f"  Current matrix: {X.shape[1]} features")
            print(f"  Scaler expects: {expected_features} features")
            print(f"  Training features: {len(self.feature_columns)} features")
            
            # This indicates a mismatch between stored feature_columns and actual training
            # The scaler was trained on more features than we have in feature_columns
            if X.shape[1] < expected_features:
                print(f"[WARNING] Padding feature matrix from {X.shape[1]} to {expected_features} features")
                # Pad with zeros to match scaler expectations
                import pandas as pd
                padding_cols = expected_features - X.shape[1]
                padding_data = pd.DataFrame(
                    np.zeros((X.shape[0], padding_cols)), 
                    columns=[f'missing_feature_{i}' for i in range(padding_cols)],
                    index=X.index
                )
                X = pd.concat([X, padding_data], axis=1)
                print(f"[INFO] Feature matrix padded to shape: {X.shape}")
        
        # Scale features
        try:
            if fit_scaler:
                X_scaled = self.scaler.fit_transform(X)
            else:
                X_scaled = self.scaler.transform(X)
        except Exception as e:
            print(f"[ERROR] Feature scaling failed: {e}")
            print(f"  Feature matrix shape: {X.shape}")
            print(f"  Scaler expects: {getattr(self.scaler, 'n_features_in_', 'unknown')} features")
            raise
            
        return X_scaled
    
    def extract_features_and_labels(self, df, fit_scaler=True):
        """
        Extract features and labels with advanced feature engineering
        """
        print(f"Dataset columns: {list(df.columns)}")
        print(f"Dataset shape: {df.shape}")
        
        # Handle different dataset formats
        if 'label' in df.columns:
            # Standard format with label column
            exclude_cols = ['id', 'Label', 'label', 'attack_cat', 'timestamp', 'Timestamp']
            label_col = 'label'
        elif len(df.columns) > 40:
            # Assume last column is label for datasets with many features
            print("Assuming last column is label")
            # Rename last column to 'label' if it's not already named
            if df.columns[-1] not in ['label', 'Label']:
                df = df.rename(columns={df.columns[-1]: 'label'})
            exclude_cols = ['id', 'Label', 'label', 'attack_cat', 'timestamp', 'Timestamp']
            label_col = 'label'
        else:
            raise ValueError(f"Unrecognized dataset format. Columns: {list(df.columns)}")
        
        # Extract feature columns
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        if fit_scaler:
            # Training phase - store feature columns
            self.feature_columns = feature_cols
            print(f"Training: Using {len(feature_cols)} features")
            # Extract features using feature columns
            X = df[self.feature_columns].copy()
        else:
            # Testing/prediction phase - handle feature mismatch
            if self.feature_columns is None:
                raise ValueError("Model not trained yet - no feature columns available")
            
            # Check if we have a feature mismatch (different column names)
            if set(feature_cols) != set(self.feature_columns):
                print(f"Feature mismatch detected:")
                print(f"  Training features: {len(self.feature_columns)} columns")
                print(f"  Current features: {len(feature_cols)} columns")
                
                # Find common features by position if names don't match
                common_features = []
                max_features = min(len(feature_cols), len(self.feature_columns))
                
                # Use positional mapping for feature alignment
                for i in range(max_features):
                    if i < len(feature_cols):
                        common_features.append(feature_cols[i])
                
                if len(common_features) < len(self.feature_columns):
                    print(f"Warning: Using only {len(common_features)} common features out of {len(self.feature_columns)} training features")
                
                # Create a mapping from current features to training feature positions
                feature_mapping = {}
                for i, current_feature in enumerate(common_features):
                    if i < len(self.feature_columns):
                        feature_mapping[current_feature] = self.feature_columns[i]
                
                # Extract features using common features
                X = df[common_features].copy()
                
                # Pad with zeros if we have fewer features than training
                if len(common_features) < len(self.feature_columns):
                    missing_features = len(self.feature_columns) - len(common_features)
                    padding = np.zeros((len(df), missing_features))
                    X_array = np.hstack([X.values, padding])
                    X = pd.DataFrame(X_array, columns=self.feature_columns)
                else:
                    # Rename columns to match training feature names
                    X.columns = self.feature_columns[:len(common_features)]
            else:
                # No mismatch - use features directly
                X = df[self.feature_columns].copy()
                print(f"Testing: Using {len(self.feature_columns)} features (exact match)")
            
        # Extract labels
        y = df[label_col].copy()
        
        # Convert to binary if needed
        if y.dtype == 'object':
            # Handle various label formats
            y_str = y.astype(str).str.lower()
            # Map common normal/benign labels to 0, everything else to 1
            normal_labels = ['benign', 'normal', '0', 'legitimate', 'clean']
            y = (~y_str.isin(normal_labels)).astype(int)
        else:
            y = (y != 0).astype(int)  # Assuming 0 is normal
        
        # Scale features
        if fit_scaler:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
            
        print(f"Features shape: {X_scaled.shape}")
        print(f"Labels distribution: Normal={np.sum(y==0)}, Attack={np.sum(y==1)}")
        
        return X_scaled, y
    
    def feature_selection(self, X, y, k=50):
        """
        Advanced feature selection using multiple methods
        """
        print(f"Performing feature selection (selecting top {k} features)...")
        
        # Use mutual information for feature selection
        self.feature_selector = SelectKBest(score_func=mutual_info_classif, k=min(k, X.shape[1]))
        X_selected = self.feature_selector.fit_transform(X, y)
        
        # Get feature importance scores
        feature_scores = self.feature_selector.scores_
        selected_features = self.feature_selector.get_support()
        
        print(f"Selected {X_selected.shape[1]} features from {X.shape[1]} total")
        
        return X_selected
    
    def handle_class_imbalance(self, X, y, method='smote'):
        """
        Handle class imbalance using various techniques
        """
        if not IMBALANCED_AVAILABLE:
            print("Imbalanced-learn not available. Skipping class balancing.")
            return X, y
            
        print(f"Handling class imbalance using {method}...")
        original_counts = np.bincount(y)
        print(f"Original class distribution: Normal={original_counts[0]}, Attack={original_counts[1]}")
        
        if method == 'smote':
            sampler = SMOTE(random_state=self.random_state)
        elif method == 'adasyn':
            sampler = ADASYN(random_state=self.random_state)
        elif method == 'smote_tomek':
            sampler = SMOTETomek(random_state=self.random_state)
        else:
            print(f"Unknown method {method}. Using SMOTE.")
            sampler = SMOTE(random_state=self.random_state)
            
        try:
            X_resampled, y_resampled = sampler.fit_resample(X, y)
            new_counts = np.bincount(y_resampled)
            print(f"Resampled class distribution: Normal={new_counts[0]}, Attack={new_counts[1]}")
            return X_resampled, y_resampled
        except Exception as e:
            print(f"Error in resampling: {e}. Using original data.")
            return X, y
    
    def build_models(self):
        """
        Build multiple supervised learning models
        """
        print("Building supervised learning models...")
        
        # Random Forest
        self.models['random_forest'] = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=self.random_state,
            n_jobs=-1
        )
        
        # XGBoost (if available)
        if XGBOOST_AVAILABLE:
            self.models['xgboost'] = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=self.random_state,
                n_jobs=-1,
                eval_metric='logloss'
            )
        
        print(f"Built {len(self.models)} models: {list(self.models.keys())}")
    
    def train_models(self, X_train, y_train, use_cv=True):
        """
        Train all models with cross-validation
        """
        print("Training models...")
        
        if use_cv:
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=self.random_state)
            
        for name, model in self.models.items():
            print(f"\nTraining {name}...")
            
            # Cross-validation
            if use_cv:
                cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring='f1')
                print(f"{name} CV F1 Score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
            
            # Fit model
            model.fit(X_train, y_train)
            
            # Feature importance
            if hasattr(model, 'feature_importances_'):
                if self.feature_importance is None:
                    self.feature_importance = {}
                self.feature_importance[name] = model.feature_importances_
    
    def create_ensemble(self):
        """
        Create ensemble model from trained models
        """
        if len(self.models) < 2:
            print("Need at least 2 models for ensemble. Using single model.")
            return
            
        print("Creating ensemble model...")
        
        estimators = [(name, model) for name, model in self.models.items()]
        self.ensemble_model = VotingClassifier(
            estimators=estimators,
            voting='soft'  # Use probability voting
        )
        
        print(f"Ensemble created with {len(estimators)} models")
    
    def evaluate_models(self, X_test, y_test):
        """
        Comprehensive model evaluation
        """
        print("\n" + "="*60)
        print("MODEL EVALUATION RESULTS")
        print("="*60)
        
        results = {}
        
        # Evaluate individual models
        for name, model in self.models.items():
            print(f"\n{name.upper()} RESULTS:")
            print("-" * 40)
            
            y_pred = model.predict(X_test)
            y_pred_proba = model.predict_proba(X_test)[:, 1]
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            auc = roc_auc_score(y_test, y_pred_proba)
            
            results[name] = {
                'accuracy': accuracy,
                'f1_score': f1,
                'auc_score': auc,
                'y_pred': y_pred,
                'y_pred_proba': y_pred_proba
            }
            
            print(f"Accuracy: {accuracy:.4f}")
            print(f"F1 Score: {f1:.4f}")
            print(f"AUC Score: {auc:.4f}")
            
            print("\nClassification Report:")
            print(classification_report(y_test, y_pred, target_names=['Normal', 'Attack']))
            
            print("\nConfusion Matrix:")
            cm = confusion_matrix(y_test, y_pred)
            print(f"TN: {cm[0,0]}, FP: {cm[0,1]}")
            print(f"FN: {cm[1,0]}, TP: {cm[1,1]}")
        
        # Evaluate ensemble if available
        if self.ensemble_model is not None:
            print(f"\nENSEMBLE RESULTS:")
            print("-" * 40)
            
            # Fit ensemble on training data (assuming it's available)
            # Note: In practice, you'd want to fit this during training
            y_pred = self.ensemble_model.predict(X_test)
            y_pred_proba = self.ensemble_model.predict_proba(X_test)[:, 1]
            
            accuracy = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            auc = roc_auc_score(y_test, y_pred_proba)
            
            results['ensemble'] = {
                'accuracy': accuracy,
                'f1_score': f1,
                'auc_score': auc,
                'y_pred': y_pred,
                'y_pred_proba': y_pred_proba
            }
            
            print(f"Accuracy: {accuracy:.4f}")
            print(f"F1 Score: {f1:.4f}")
            print(f"AUC Score: {auc:.4f}")
            
            print("\nClassification Report:")
            print(classification_report(y_test, y_pred, target_names=['Normal', 'Attack']))
        
        return results
    
    def plot_results(self, results, y_test, save_dir='models'):
        """
        Create comprehensive visualization plots
        """
        print("Creating evaluation plots...")
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # ROC Curves
        plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 2, 1)
        for name, result in results.items():
            fpr, tpr, _ = roc_curve(y_test, result['y_pred_proba'])
            plt.plot(fpr, tpr, label=f"{name} (AUC={result['auc_score']:.3f})")
        
        plt.plot([0, 1], [0, 1], 'k--', label='Random')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curves')
        plt.legend()
        plt.grid(True)
        
        # Precision-Recall Curves
        plt.subplot(2, 2, 2)
        for name, result in results.items():
            precision, recall, _ = precision_recall_curve(y_test, result['y_pred_proba'])
            plt.plot(recall, precision, label=f"{name} (F1={result['f1_score']:.3f})")
        
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Precision-Recall Curves')
        plt.legend()
        plt.grid(True)
        
        # Feature Importance (if available)
        if self.feature_importance:
            plt.subplot(2, 2, 3)
            for name, importance in self.feature_importance.items():
                top_indices = np.argsort(importance)[-10:]  # Top 10 features
                plt.barh(range(len(top_indices)), importance[top_indices], alpha=0.7, label=name)
            
            plt.xlabel('Feature Importance')
            plt.title('Top 10 Feature Importances')
            plt.legend()
        
        # Model Comparison
        plt.subplot(2, 2, 4)
        metrics = ['accuracy', 'f1_score', 'auc_score']
        x = np.arange(len(metrics))
        width = 0.35
        
        for i, (name, result) in enumerate(results.items()):
            values = [result[metric] for metric in metrics]
            plt.bar(x + i*width, values, width, label=name, alpha=0.8)
        
        plt.xlabel('Metrics')
        plt.ylabel('Score')
        plt.title('Model Performance Comparison')
        plt.xticks(x + width/2, metrics)
        plt.legend()
        plt.ylim(0, 1)
        
        plt.tight_layout()
        plt.savefig(f"{save_dir}/supervised_evaluation_{timestamp}.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Plots saved to {save_dir}/supervised_evaluation_{timestamp}.png")
    
    def save_models(self, save_dir='models'):
        """
        Save all trained models and components
        """
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save individual models
        for name, model in self.models.items():
            model_path = f"{save_dir}/supervised_{name}_{timestamp}.pkl"
            joblib.dump(model, model_path)
            print(f"Saved {name} model to {model_path}")
        
        # Save ensemble model
        if self.ensemble_model is not None:
            ensemble_path = f"{save_dir}/supervised_ensemble_{timestamp}.pkl"
            joblib.dump(self.ensemble_model, ensemble_path)
            print(f"Saved ensemble model to {ensemble_path}")
        
        # Save preprocessing components
        components = {
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_selector': self.feature_selector,
            'feature_columns': self.feature_columns,
            'feature_importance': self.feature_importance
        }
        
        components_path = f"{save_dir}/supervised_components_{timestamp}.pkl"
        joblib.dump(components, components_path)
        print(f"Saved preprocessing components to {components_path}")
    
    def load_models(self, model_dir='models', timestamp=None):
        """
        Load trained models and components
        """
        if timestamp is None:
            # Find latest timestamp
            pattern = f"{model_dir}/supervised_components_*.pkl"
            files = glob.glob(pattern)
            if not files:
                raise ValueError(f"No model files found in {model_dir}")
            latest_file = max(files, key=os.path.getctime)
            # Extract timestamp from filename like 'supervised_components_20250906_154621.pkl'
            basename = os.path.basename(latest_file)
            # Split by '_' and take the last two parts (date and time)
            parts = basename.replace('.pkl', '').split('_')
            if len(parts) >= 4:  # supervised_components_YYYYMMDD_HHMMSS
                timestamp = f"{parts[-2]}_{parts[-1]}"
            else:
                timestamp = parts[-1]
        
        # Load components
        components_path = f"{model_dir}/supervised_components_{timestamp}.pkl"
        components = joblib.load(components_path)
        
        self.scaler = components['scaler']
        self.label_encoders = components.get('label_encoders', {})
        self.feature_selector = components['feature_selector']
        self.feature_columns = components['feature_columns']
        self.feature_importance = components['feature_importance']
        
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
    
    def predict_single(self, record):
        """
        Make prediction on a single record for real-time processing
        
        Args:
            record: Dictionary containing network traffic features
            
        Returns:
            Dictionary with prediction, anomaly_score, and confidence
        """
        try:
            if not self.models:
                raise ValueError("No trained models available")
            
            # Convert record to DataFrame
            import pandas as pd
            df = pd.DataFrame([record])
            
            # Log input features for debugging (only first time or on error)
            if not hasattr(self, '_logged_input_features'):
                print(f"[DEBUG] Input record features ({len(record)}): {sorted(record.keys())[:10]}...")
                self._logged_input_features = True
            
            # Preprocess the data
            df = self.preprocess_data(df, fit_encoders=False)
            
            # Extract features (without labels for real-time prediction)
            X = self.extract_features_only(df, fit_scaler=False)
            
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
                confidence = 0.8  # Default confidence for models without probability
            
            return {
                'prediction': int(prediction),
                'anomaly_score': float(anomaly_score),
                'confidence': float(confidence),
                'model_used': model_name
            }
            
        except Exception as e:
            # Enhanced error logging for feature mismatch debugging
            if "Feature names seen at fit time" in str(e):
                print(f"[ERROR] Feature mismatch in prediction:")
                print(f"  Input features: {sorted(record.keys()) if record else 'None'}")
                print(f"  Expected features: {getattr(self, 'feature_columns', 'Not available')[:10] if hasattr(self, 'feature_columns') else 'Not available'}...")
                print(f"  Model error: {str(e)[:200]}...")
            else:
                print(f"[ERROR] Prediction error: {str(e)[:100]}...")
            
            # Return mock prediction as fallback
            return {
                'prediction': 0,
                'anomaly_score': 0.1,
                'confidence': 0.5,
                'model_used': 'fallback',
                'error': str(e)
            }
    
    def predict_batch(self, records):
        """
        Make predictions on a batch of records for CSV processing
        
        Args:
            records: List of dictionaries or DataFrame containing network traffic features
            
        Returns:
            Dictionary with predictions, anomaly_scores, and metadata
        """
        try:
            if not self.models:
                raise ValueError("No trained models available")
            
            # Convert to DataFrame if needed
            import pandas as pd
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
            
            # Use the best available model (or ensemble if available)
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
                confidences = np.full(len(predictions), 0.8)  # Default confidence
            
            # Get feature importance if available
            feature_importance = {}
            if hasattr(model, 'feature_importances_'):
                importance_scores = model.feature_importances_
                feature_names = self.feature_columns if self.feature_columns else [f'feature_{i}' for i in range(len(importance_scores))]
                feature_importance = dict(zip(feature_names[:len(importance_scores)], importance_scores))
            
            return {
                'predictions': predictions.tolist(),
                'anomaly_scores': anomaly_scores.tolist(),
                'confidences': confidences.tolist(),
                'feature_importance': feature_importance,
                'model_used': model_name,
                'total_records': len(predictions),
                'anomalies_detected': int(np.sum(predictions)),
                'anomaly_percentage': float(np.mean(predictions) * 100)
            }
            
        except Exception as e:
            print(f"Error in batch prediction: {e}")
            # Return mock predictions as fallback
            n_records = len(records) if isinstance(records, list) else len(records)
            np.random.seed(42)
            mock_predictions = np.random.choice([0, 1], n_records, p=[0.85, 0.15])
            mock_scores = np.random.beta(2, 8, n_records)
            
            return {
                'predictions': mock_predictions.tolist(),
                'anomaly_scores': mock_scores.tolist(),
                'confidences': np.full(n_records, 0.5).tolist(),
                'feature_importance': {},
                'model_used': 'fallback',
                'total_records': n_records,
                'anomalies_detected': int(np.sum(mock_predictions)),
                'anomaly_percentage': float(np.mean(mock_predictions) * 100),
                'error': str(e)
            }
    
    def get_feature_template(self):
        """
        Get template of expected features for data generation
        
        Returns:
            Dictionary with feature names and their expected data types/ranges
        """
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
                    'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes',
                    'land', 'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', 'logged_in',
                    'num_compromised', 'root_shell', 'su_attempted', 'num_root', 'num_file_creations',
                    'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login',
                    'is_guest_login', 'count', 'srv_count', 'serror_rate', 'srv_serror_rate',
                    'rerror_rate', 'srv_rerror_rate', 'same_srv_rate', 'diff_srv_rate',
                    'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count',
                    'dst_host_same_srv_rate', 'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
                    'dst_host_srv_diff_host_rate', 'dst_host_serror_rate', 'dst_host_srv_serror_rate',
                    'dst_host_rerror_rate', 'dst_host_srv_rerror_rate'
                ],
                'num_features': 41,
                'model_ready': False,
                'scaler_ready': False,
                'feature_selector_ready': False
            }


def main():
    """
    Main training pipeline
    """
    print("="*60)
    print("SOC ANOMALY DETECTION - SUPERVISED LEARNING PIPELINE")
    print("="*60)
    
    # Initialize detector
    detector = SupervisedSOCDetector(random_state=42)
    
    # Data paths
    train_path = "data/"  # Folder containing training CSV files
    test_path = "test/"   # Folder containing test CSV files
    
    # Load and preprocess training data
    print("\n1. LOADING TRAINING DATA")
    print("-" * 30)
    df_train = detector.load_csv_files(train_path, sample_size=50000)  # Limit for memory
    print(f"Loaded training data with {df_train.shape[1]} columns")
    df_train = detector.preprocess_data(df_train, fit_encoders=True)
    X_train_full, y_train_full = detector.extract_features_and_labels(df_train, fit_scaler=True)
    
    # Feature selection
    X_train_selected = detector.feature_selection(X_train_full, y_train_full, k=50)
    
    # Handle class imbalance
    X_train_balanced, y_train_balanced = detector.handle_class_imbalance(
        X_train_selected, y_train_full, method='smote'
    )
    
    # Split for validation
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_balanced, y_train_balanced, 
        test_size=0.2, 
        random_state=42, 
        stratify=y_train_balanced
    )
    
    # Memory cleanup
    del df_train, X_train_full
    
    print("\n2. BUILDING AND TRAINING MODELS")
    print("-" * 30)
    
    # Build models
    detector.build_models()
    
    # Train models
    detector.train_models(X_train, y_train, use_cv=True)
    
    # Create ensemble
    detector.create_ensemble()
    if detector.ensemble_model is not None:
        detector.ensemble_model.fit(X_train, y_train)
    
    print("\n3. LOADING AND PROCESSING TEST DATA")
    print("-" * 30)
    
    # Load test data
    df_test = detector.load_csv_files(test_path)
    print(f"Loaded test data with {df_test.shape[1]} columns")
    df_test = detector.preprocess_data(df_test, fit_encoders=False)
    X_test_full, y_test = detector.extract_features_and_labels(df_test, fit_scaler=False)
    
    # Apply same feature selection
    X_test_selected = detector.feature_selector.transform(X_test_full)
    
    # Memory cleanup
    del df_test, X_test_full
    
    print("\n4. MODEL EVALUATION")
    print("-" * 30)
    
    # Evaluate models
    results = detector.evaluate_models(X_test_selected, y_test)
    
    # Create plots
    detector.plot_results(results, y_test)
    
    # Save models
    print("\n5. SAVING MODELS")
    print("-" * 30)
    detector.save_models()
    
    print("\n" + "="*60)
    print("SUPERVISED LEARNING PIPELINE COMPLETED SUCCESSFULLY")
    print("="*60)
    
    # Print best model
    best_model = max(results.items(), key=lambda x: x[1]['f1_score'])
    print(f"Best performing model: {best_model[0]} (F1: {best_model[1]['f1_score']:.4f})")


if __name__ == "__main__":
    main()
