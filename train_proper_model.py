#!/usr/bin/env python3
"""
Proper Model Training Pipeline with Cross-Validation
Prevents overfitting and provides realistic performance metrics
"""

import sys
import os
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (classification_report, confusion_matrix, accuracy_score,
                            precision_score, recall_score, f1_score, roc_auc_score)
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
import matplotlib.pyplot as plt
import seaborn as sns

def load_and_prepare_data():
    """Load and prepare data with proper train/val/test split"""
    
    print("="*70)
    print("LOADING AND PREPARING DATA")
    print("="*70 + "\n")
    
    # Load full dataset
    data_file = 'data/mininet_training_data_20251121_152637.csv'
    
    if not os.path.exists(data_file):
        print(f"✗ Data file not found: {data_file}")
        print("Run: python3 train_with_pcaps.py first to generate training data")
        return None, None, None, None, None, None, None
    
    print(f"Loading data from: {data_file}")
    data = pd.read_csv(data_file)
    
    print(f"✓ Loaded {len(data)} samples")
    print(f"  Normal: {sum(data['label'] == 0)}")
    print(f"  Attack: {sum(data['label'] == 1)}")
    
    # Separate features and labels
    feature_cols = [c for c in data.columns if c not in ['label', 'attack_type', 'src_ip', 'dst_ip']]
    
    X = data[feature_cols]
    y = data['label']
    
    # Split: 60% train, 20% validation, 20% test
    print("\nSplitting data: 60% train, 20% validation, 20% test")
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp  # 0.25 of 0.8 = 0.2
    )
    
    print(f"\nTrain set: {len(X_train)} samples")
    print(f"  Normal: {sum(y_train == 0)}, Attack: {sum(y_train == 1)}")
    
    print(f"\nValidation set: {len(X_val)} samples")
    print(f"  Normal: {sum(y_val == 0)}, Attack: {sum(y_val == 1)}")
    
    print(f"\nTest set: {len(X_test)} samples")
    print(f"  Normal: {sum(y_test == 0)}, Attack: {sum(y_test == 1)}")
    
    return X_train, X_val, X_test, y_train, y_val, y_test, feature_cols

def train_with_cross_validation(X_train, y_train, feature_cols):
    """Train model with cross-validation to prevent overfitting"""
    
    print("\n" + "="*70)
    print("TRAINING WITH CROSS-VALIDATION")
    print("="*70 + "\n")
    
    # Scale features
    print("Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    # Define model with regularization to prevent overfitting
    print("\nTraining Random Forest with regularization...")
    model = RandomForestClassifier(
        n_estimators=50,          # Reduced from 100
        max_depth=8,              # Reduced from 10
        min_samples_split=10,     # Increased from 5
        min_samples_leaf=4,       # Increased from 2
        max_features='sqrt',      # Use sqrt of features
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'   # Handle class imbalance
    )
    
    # Cross-validation
    print("\nPerforming 5-fold cross-validation...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='accuracy')
    cv_precision = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='precision')
    cv_recall = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='recall')
    cv_f1 = cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='f1')
    
    print("\nCross-Validation Results:")
    print(f"  Accuracy:  {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    print(f"  Precision: {cv_precision.mean():.4f} (+/- {cv_precision.std() * 2:.4f})")
    print(f"  Recall:    {cv_recall.mean():.4f} (+/- {cv_recall.std() * 2:.4f})")
    print(f"  F1 Score:  {cv_f1.mean():.4f} (+/- {cv_f1.std() * 2:.4f})")
    
    # Train final model
    print("\nTraining final model on full training set...")
    model.fit(X_train_scaled, y_train)
    print("✓ Model trained")
    
    return model, scaler

def evaluate_model(model, scaler, X_val, y_val, X_test, y_test, feature_cols):
    """Comprehensive model evaluation"""
    
    print("\n" + "="*70)
    print("MODEL EVALUATION")
    print("="*70)
    
    # Validation set evaluation
    print("\n[1/2] VALIDATION SET PERFORMANCE")
    print("-" * 70)
    
    X_val_scaled = scaler.transform(X_val)
    y_val_pred = model.predict(X_val_scaled)
    y_val_proba = model.predict_proba(X_val_scaled)[:, 1]
    
    val_accuracy = accuracy_score(y_val, y_val_pred)
    val_precision = precision_score(y_val, y_val_pred)
    val_recall = recall_score(y_val, y_val_pred)
    val_f1 = f1_score(y_val, y_val_pred)
    val_auc = roc_auc_score(y_val, y_val_proba)
    
    print(f"\nValidation Metrics:")
    print(f"  Accuracy:  {val_accuracy:.4f}")
    print(f"  Precision: {val_precision:.4f}")
    print(f"  Recall:    {val_recall:.4f}")
    print(f"  F1 Score:  {val_f1:.4f}")
    print(f"  ROC AUC:   {val_auc:.4f}")
    
    print("\nValidation Confusion Matrix:")
    val_cm = confusion_matrix(y_val, y_val_pred)
    print(f"  TN: {val_cm[0][0]:3d}  FP: {val_cm[0][1]:3d}")
    print(f"  FN: {val_cm[1][0]:3d}  TP: {val_cm[1][1]:3d}")
    
    # Test set evaluation
    print("\n[2/2] TEST SET PERFORMANCE (FINAL)")
    print("-" * 70)
    
    X_test_scaled = scaler.transform(X_test)
    y_test_pred = model.predict(X_test_scaled)
    y_test_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    test_accuracy = accuracy_score(y_test, y_test_pred)
    test_precision = precision_score(y_test, y_test_pred)
    test_recall = recall_score(y_test, y_test_pred)
    test_f1 = f1_score(y_test, y_test_pred)
    test_auc = roc_auc_score(y_test, y_test_proba)
    
    print(f"\nTest Metrics:")
    print(f"  Accuracy:  {test_accuracy:.4f}")
    print(f"  Precision: {test_precision:.4f}")
    print(f"  Recall:    {test_recall:.4f}")
    print(f"  F1 Score:  {test_f1:.4f}")
    print(f"  ROC AUC:   {test_auc:.4f}")
    
    print("\nTest Confusion Matrix:")
    test_cm = confusion_matrix(y_test, y_test_pred)
    print(f"  TN: {test_cm[0][0]:3d}  FP: {test_cm[0][1]:3d}")
    print(f"  FN: {test_cm[1][0]:3d}  TP: {test_cm[1][1]:3d}")
    
    # Calculate detailed metrics
    tn, fp, fn, tp = test_cm.ravel()
    
    if (tp + fn) > 0:
        attack_detection_rate = tp / (tp + fn)
        print(f"\n  • Attack Detection Rate: {attack_detection_rate:.2%}")
    
    if (tn + fp) > 0:
        normal_accuracy = tn / (tn + fp)
        print(f"  • Normal Traffic Accuracy: {normal_accuracy:.2%}")
    
    if (fp + tn) > 0:
        false_positive_rate = fp / (fp + tn)
        print(f"  • False Positive Rate: {false_positive_rate:.2%}")
    
    # Classification report
    print("\nDetailed Classification Report:")
    print(classification_report(y_test, y_test_pred, target_names=['Normal', 'Attack']))
    
    # Feature importance
    print("\nTop 10 Important Features:")
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for idx, row in feature_importance.head(10).iterrows():
        print(f"  {row['feature']:30s}: {row['importance']:.4f}")
    
    return {
        'val_accuracy': val_accuracy,
        'val_f1': val_f1,
        'test_accuracy': test_accuracy,
        'test_f1': test_f1,
        'test_precision': test_precision,
        'test_recall': test_recall,
        'test_auc': test_auc
    }

def save_model_and_artifacts(model, scaler, feature_cols, metrics):
    """Save model and training artifacts"""
    
    print("\n" + "="*70)
    print("SAVING MODEL AND ARTIFACTS")
    print("="*70 + "\n")
    
    model_dir = 'models'
    os.makedirs(model_dir, exist_ok=True)
    
    # Save model
    model_path = os.path.join(model_dir, 'mininet_model.pkl')
    joblib.dump(model, model_path)
    print(f"✓ Saved model: {model_path}")
    
    # Save scaler
    scaler_path = os.path.join(model_dir, 'mininet_scaler.pkl')
    joblib.dump(scaler, scaler_path)
    print(f"✓ Saved scaler: {scaler_path}")
    
    # Save feature columns
    feature_cols_path = os.path.join(model_dir, 'mininet_feature_columns.pkl')
    joblib.dump(feature_cols, feature_cols_path)
    print(f"✓ Saved feature columns: {feature_cols_path}")
    
    # Save metrics
    metrics_path = os.path.join(model_dir, 'training_metrics.pkl')
    joblib.dump(metrics, metrics_path)
    print(f"✓ Saved training metrics: {metrics_path}")
    
    return model_path, scaler_path, feature_cols_path

def main():
    """Main training pipeline"""
    
    print("\n" + "="*70)
    print("PROPER MODEL TRAINING PIPELINE")
    print("="*70 + "\n")
    
    # Load and prepare data
    X_train, X_val, X_test, y_train, y_val, y_test, feature_cols = load_and_prepare_data()
    
    if X_train is None:
        return False
    
    # Train with cross-validation
    model, scaler = train_with_cross_validation(X_train, y_train, feature_cols)
    
    # Evaluate
    metrics = evaluate_model(model, scaler, X_val, y_val, X_test, y_test, feature_cols)
    
    # Save
    model_path, scaler_path, feature_cols_path = save_model_and_artifacts(
        model, scaler, feature_cols, metrics
    )
    
    # Summary
    print("\n" + "="*70)
    print("TRAINING COMPLETE!")
    print("="*70)
    
    print("\nFinal Test Performance:")
    print(f"  • Accuracy:  {metrics['test_accuracy']:.4f}")
    print(f"  • Precision: {metrics['test_precision']:.4f}")
    print(f"  • Recall:    {metrics['test_recall']:.4f}")
    print(f"  • F1 Score:  {metrics['test_f1']:.4f}")
    print(f"  • ROC AUC:   {metrics['test_auc']:.4f}")
    
    print("\nModel files saved:")
    print(f"  • {model_path}")
    print(f"  • {scaler_path}")
    print(f"  • {feature_cols_path}")
    
    print("\nModel Configuration:")
    print("  • Regularization: Applied (max_depth=8, min_samples_split=10)")
    print("  • Class balancing: Enabled")
    print("  • Cross-validation: 5-fold stratified")
    print("  • Train/Val/Test split: 60/20/20")
    
    print("\nNext steps:")
    print("  1. Restart dashboard: cd src/dashboard && python3 server.py")
    print("  2. Test simulations in UI")
    print("  3. Monitor for overfitting in production")
    
    # Warning if performance is too good
    if metrics['test_accuracy'] > 0.98:
        print("\n⚠️  WARNING: Very high accuracy detected!")
        print("   This might indicate:")
        print("   • Data leakage between train/test")
        print("   • Need more diverse attack patterns")
        print("   • Need more normal traffic samples")
        print("   Consider generating more varied PCAP data")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
