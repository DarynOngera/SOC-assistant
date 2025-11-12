#!/usr/bin/env python3
"""
Train ML Models on Mininet-Generated Data
Replaces existing models with Mininet-trained models
"""

import os
import sys
import glob
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    roc_curve, precision_recall_curve, accuracy_score, f1_score
)
from sklearn.feature_selection import SelectKBest, mutual_info_classif
import warnings
warnings.filterwarnings('ignore')

# Try to import advanced models
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("XGBoost not available")

try:
    from imblearn.over_sampling import SMOTE
    SMOTE_AVAILABLE = True
except ImportError:
    SMOTE_AVAILABLE = False
    print("SMOTE not available")

class MininetModelTrainer:
    """Train intrusion detection models on Mininet data"""
    
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_selector = None
        self.models = {}
        self.ensemble_model = None
        self.feature_columns = None
        self.feature_importance = None
        self.attack_type_encoder = LabelEncoder()
        
    def load_data(self, data_path):
        """Load preprocessed Mininet dataset"""
        print(f"Loading data from: {data_path}")
        
        if os.path.isfile(data_path):
            df = pd.read_csv(data_path)
        else:
            # Find latest dataset (try both mininet and synthetic)
            csv_files = glob.glob(os.path.join(data_path, 'mininet_dataset_*.csv'))
            csv_files += glob.glob(os.path.join(data_path, 'synthetic_dataset_*.csv'))
            
            if not csv_files:
                raise ValueError(f"No dataset found in {data_path}")
            
            # Get most recent file
            csv_files.sort()
            data_path = csv_files[-1]
            print(f"Using latest dataset: {os.path.basename(data_path)}")
            df = pd.read_csv(data_path)
        
        print(f"Loaded {len(df)} samples with {len(df.columns)} columns")
        
        return df
    
    def preprocess_data(self, df):
        """Preprocess data for training"""
        print("\nPreprocessing data...")
        
        # Separate features and labels
        X = df.drop(['label', 'attack_type'], axis=1, errors='ignore')
        y = df['label']
        
        # Store attack types for analysis
        attack_types = df['attack_type'] if 'attack_type' in df.columns else None
        
        # Drop non-numeric columns (IP addresses, protocol strings, etc.)
        non_numeric_cols = X.select_dtypes(include=['object']).columns.tolist()
        if non_numeric_cols:
            print(f"Dropping non-numeric columns: {non_numeric_cols}")
            X = X.drop(columns=non_numeric_cols)
        
        # Handle missing values
        X = X.fillna(0)
        
        # Handle infinite values
        X = X.replace([np.inf, -np.inf], 0)
        
        # Ensure all columns are numeric
        X = X.apply(pd.to_numeric, errors='coerce').fillna(0)
        
        # Store feature columns
        self.feature_columns = X.columns.tolist()
        
        print(f"Features: {len(self.feature_columns)}")
        print(f"Samples: {len(X)}")
        print(f"Normal: {sum(y == 0)}, Attack: {sum(y == 1)}")
        
        return X, y, attack_types
    
    def split_data(self, X, y, test_size=0.2, val_size=0.1):
        """Split data into train, validation, and test sets"""
        print("\nSplitting data...")
        
        # First split: train+val and test
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state, stratify=y
        )
        
        # Second split: train and val
        val_ratio = val_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_ratio, random_state=self.random_state, stratify=y_temp
        )
        
        print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def scale_features(self, X_train, X_val, X_test):
        """Scale features using StandardScaler"""
        print("\nScaling features...")
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)
        
        return X_train_scaled, X_val_scaled, X_test_scaled
    
    def select_features(self, X_train, y_train, k=30):
        """Select top k features using mutual information"""
        print(f"\nSelecting top {k} features...")
        
        self.feature_selector = SelectKBest(mutual_info_classif, k=min(k, X_train.shape[1]))
        X_train_selected = self.feature_selector.fit_transform(X_train, y_train)
        
        # Get selected feature names
        selected_indices = self.feature_selector.get_support(indices=True)
        selected_features = [self.feature_columns[i] for i in selected_indices]
        
        print(f"Selected features: {selected_features[:10]}...")
        
        return X_train_selected, selected_features
    
    def balance_data(self, X_train, y_train):
        """Balance training data using SMOTE"""
        if not SMOTE_AVAILABLE:
            print("SMOTE not available, skipping data balancing")
            return X_train, y_train
        
        print("\nBalancing data with SMOTE...")
        
        smote = SMOTE(random_state=self.random_state)
        X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
        
        print(f"Before SMOTE: {len(X_train)}")
        print(f"After SMOTE: {len(X_train_balanced)}")
        print(f"Normal: {sum(y_train_balanced == 0)}, Attack: {sum(y_train_balanced == 1)}")
        
        return X_train_balanced, y_train_balanced
    
    def train_random_forest(self, X_train, y_train):
        """Train Random Forest classifier"""
        print("\nTraining Random Forest...")
        
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=self.random_state,
            n_jobs=-1,
            class_weight='balanced'
        )
        
        rf_model.fit(X_train, y_train)
        
        # Cross-validation
        cv_scores = cross_val_score(
            rf_model, X_train, y_train, cv=5, scoring='f1', n_jobs=-1
        )
        print(f"CV F1 Score: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        
        self.models['random_forest'] = rf_model
        
        return rf_model
    
    def train_xgboost(self, X_train, y_train):
        """Train XGBoost classifier"""
        if not XGBOOST_AVAILABLE:
            print("XGBoost not available, skipping")
            return None
        
        print("\nTraining XGBoost...")
        
        xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=10,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=self.random_state,
            n_jobs=-1,
            scale_pos_weight=1
        )
        
        xgb_model.fit(X_train, y_train)
        
        # Cross-validation
        cv_scores = cross_val_score(
            xgb_model, X_train, y_train, cv=5, scoring='f1', n_jobs=-1
        )
        print(f"CV F1 Score: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        
        self.models['xgboost'] = xgb_model
        
        return xgb_model
    
    def create_ensemble(self, X_train, y_train):
        """Create ensemble model"""
        print("\nCreating ensemble model...")
        
        estimators = [('rf', self.models['random_forest'])]
        
        if 'xgboost' in self.models and self.models['xgboost'] is not None:
            estimators.append(('xgb', self.models['xgboost']))
        
        self.ensemble_model = VotingClassifier(
            estimators=estimators,
            voting='soft',
            n_jobs=-1
        )
        
        self.ensemble_model.fit(X_train, y_train)
        
        return self.ensemble_model
    
    def evaluate_model(self, model, X_test, y_test, model_name='Model'):
        """Evaluate model performance"""
        print(f"\nEvaluating {model_name}...")
        
        # Predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        print(f"Accuracy: {accuracy:.4f}")
        print(f"F1 Score: {f1:.4f}")
        
        # Classification report
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=['Normal', 'Attack']))
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        print("\nConfusion Matrix:")
        print(cm)
        
        # ROC AUC
        try:
            roc_auc = roc_auc_score(y_test, y_pred_proba)
            print(f"ROC AUC: {roc_auc:.4f}")
        except:
            roc_auc = None
        
        return {
            'accuracy': accuracy,
            'f1_score': f1,
            'roc_auc': roc_auc,
            'confusion_matrix': cm,
            'y_pred': y_pred,
            'y_pred_proba': y_pred_proba
        }
    
    def plot_results(self, results, output_dir='../reports'):
        """Plot training results"""
        os.makedirs(output_dir, exist_ok=True)
        
        print("\nGenerating visualizations...")
        
        # Confusion matrix heatmap
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            results['confusion_matrix'],
            annot=True,
            fmt='d',
            cmap='Blues',
            xticklabels=['Normal', 'Attack'],
            yticklabels=['Normal', 'Attack']
        )
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'confusion_matrix.png'))
        plt.close()
        
        print(f"Saved confusion matrix to {output_dir}/confusion_matrix.png")
    
    def save_models(self, output_dir='../../models'):
        """Save trained models"""
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\nSaving models to {output_dir}...")
        
        # Save ensemble model
        if self.ensemble_model:
            model_path = os.path.join(output_dir, 'mininet_ensemble_model.pkl')
            joblib.dump(self.ensemble_model, model_path)
            print(f"Saved ensemble model: {model_path}")
        
        # Save individual models
        for name, model in self.models.items():
            if model is not None:
                model_path = os.path.join(output_dir, f'mininet_{name}_model.pkl')
                joblib.dump(model, model_path)
                print(f"Saved {name} model: {model_path}")
        
        # Save preprocessors
        scaler_path = os.path.join(output_dir, 'mininet_scaler.pkl')
        joblib.dump(self.scaler, scaler_path)
        print(f"Saved scaler: {scaler_path}")
        
        if self.feature_selector:
            selector_path = os.path.join(output_dir, 'mininet_feature_selector.pkl')
            joblib.dump(self.feature_selector, selector_path)
            print(f"Saved feature selector: {selector_path}")
        
        # Save feature columns
        features_path = os.path.join(output_dir, 'mininet_feature_columns.pkl')
        joblib.dump(self.feature_columns, features_path)
        print(f"Saved feature columns: {features_path}")
        
        # Save metadata
        metadata = {
            'training_date': datetime.now().isoformat(),
            'n_features': len(self.feature_columns),
            'feature_columns': self.feature_columns,
            'models': list(self.models.keys()),
            'data_source': 'mininet'
        }
        metadata_path = os.path.join(output_dir, 'mininet_model_metadata.pkl')
        joblib.dump(metadata, metadata_path)
        print(f"Saved metadata: {metadata_path}")
    
    def train_pipeline(self, data_path):
        """Complete training pipeline"""
        print("="*60)
        print("MININET MODEL TRAINING PIPELINE")
        print("="*60)
        
        # Load data
        df = self.load_data(data_path)
        
        # Preprocess
        X, y, attack_types = self.preprocess_data(df)
        
        # Split data
        X_train, X_val, X_test, y_train, y_val, y_test = self.split_data(X, y)
        
        # Scale features
        X_train_scaled, X_val_scaled, X_test_scaled = self.scale_features(
            X_train, X_val, X_test
        )
        
        # Feature selection
        X_train_selected, selected_features = self.select_features(
            X_train_scaled, y_train, k=30
        )
        X_val_selected = self.feature_selector.transform(X_val_scaled)
        X_test_selected = self.feature_selector.transform(X_test_scaled)
        
        # Balance data
        X_train_balanced, y_train_balanced = self.balance_data(
            X_train_selected, y_train
        )
        
        # Train models
        self.train_random_forest(X_train_balanced, y_train_balanced)
        self.train_xgboost(X_train_balanced, y_train_balanced)
        
        # Create ensemble
        self.create_ensemble(X_train_balanced, y_train_balanced)
        
        # Evaluate on test set
        results = self.evaluate_model(
            self.ensemble_model, X_test_selected, y_test, 
            model_name='Ensemble Model'
        )
        
        # Plot results
        self.plot_results(results)
        
        # Save models
        self.save_models()
        
        print("\n" + "="*60)
        print("TRAINING COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Accuracy: {results['accuracy']:.4f}")
        print(f"F1 Score: {results['f1_score']:.4f}")
        if results['roc_auc']:
            print(f"ROC AUC: {results['roc_auc']:.4f}")
        print("="*60)
        
        return results

def main():
    """Main function"""
    # Find processed data (try multiple locations)
    possible_dirs = [
        'data_capture/processed',  # When run from mininet_data_generation/
        '../data_capture/processed'  # When run from mininet_data_generation/models/
    ]
    
    data_dir = None
    for dir_path in possible_dirs:
        if os.path.exists(dir_path):
            data_dir = dir_path
            break
    
    if not data_dir:
        print(f"ERROR: Data directory not found in: {possible_dirs}")
        print("Please run preprocess_pcap.py or generate_synthetic_data.py first")
        sys.exit(1)
    
    # Create trainer
    trainer = MininetModelTrainer()
    
    # Train models
    results = trainer.train_pipeline(data_dir)
    
    print("\nNext steps:")
    print("1. Test models: python ../simulation/realtime_attack_sim.py")
    print("2. Integrate with dashboard: python ../integration/integrate_dashboard.py")

if __name__ == '__main__':
    main()
