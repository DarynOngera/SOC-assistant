#!/usr/bin/env python3
"""
Simple Model Training Script for Mininet Data
Uses the existing training data CSV files
"""

import sys
import os
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split

def train_simple_model():
    """Train a simple Random Forest model with the aggregated data"""
    
    print("="*70)
    print("SIMPLE MININET MODEL TRAINING")
    print("="*70 + "\n")
    
    # Load the most recent training data
    train_file = 'data/mininet_train_20251121_152637.csv'
    test_file = 'data/mininet_test_20251121_152637.csv'
    
    if not os.path.exists(train_file):
        print(f"✗ Training file not found: {train_file}")
        print("Run: python3 train_with_pcaps.py first to generate training data")
        return False
    
    print(f"Loading training data from: {train_file}")
    train_data = pd.read_csv(train_file)
    
    print(f"Loading test data from: {test_file}")
    test_data = pd.read_csv(test_file)
    
    print(f"\n✓ Loaded {len(train_data)} training samples")
    print(f"✓ Loaded {len(test_data)} test samples")
    
    # Separate features and labels
    feature_cols = [c for c in train_data.columns if c not in ['label', 'attack_type', 'src_ip', 'dst_ip']]
    
    print(f"\nFeatures ({len(feature_cols)}):")
    for i, col in enumerate(feature_cols, 1):
        print(f"  {i:2d}. {col}")
    
    X_train = train_data[feature_cols]
    y_train = train_data['label']
    
    X_test = test_data[feature_cols]
    y_test = test_data['label']
    
    print(f"\nTraining set:")
    print(f"  Normal: {sum(y_train == 0)}")
    print(f"  Attack: {sum(y_train == 1)}")
    
    print(f"\nTest set:")
    print(f"  Normal: {sum(y_test == 0)}")
    print(f"  Attack: {sum(y_test == 1)}")
    
    # Scale features
    print("\nScaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest
    print("\nTraining Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train_scaled, y_train)
    print("✓ Model trained")
    
    # Evaluate
    print("\nEvaluating model...")
    y_pred = model.predict(X_test_scaled)
    
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n✓ Accuracy: {accuracy:.4f}")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Attack']))
    
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"  TN: {cm[0][0]:3d}  FP: {cm[0][1]:3d}")
    print(f"  FN: {cm[1][0]:3d}  TP: {cm[1][1]:3d}")
    
    # Calculate metrics
    tn, fp, fn, tp = cm.ravel()
    
    if (tp + fn) > 0:
        attack_detection_rate = tp / (tp + fn)
        print(f"\n  • Attack Detection Rate: {attack_detection_rate:.2%}")
    
    if (tn + fp) > 0:
        normal_accuracy = tn / (tn + fp)
        print(f"  • Normal Traffic Accuracy: {normal_accuracy:.2%}")
    
    if (fp + tn) > 0:
        false_positive_rate = fp / (fp + tn)
        print(f"  • False Positive Rate: {false_positive_rate:.2%}")
    
    # Save model
    print("\n" + "="*70)
    print("SAVING MODEL")
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
    
    # Feature importance
    print("\nTop 10 Important Features:")
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for idx, row in feature_importance.head(10).iterrows():
        print(f"  {row['feature']:30s}: {row['importance']:.4f}")
    
    print("\n" + "="*70)
    print("TRAINING COMPLETE!")
    print("="*70)
    
    print("\nModel files saved:")
    print(f"  • {model_path}")
    print(f"  • {scaler_path}")
    print(f"  • {feature_cols_path}")
    
    print("\nNext steps:")
    print("  1. Restart dashboard: cd src/dashboard && python3 server.py")
    print("  2. Test simulations in UI")
    print("  3. Verify improved attack detection")
    
    return True

if __name__ == '__main__':
    try:
        success = train_simple_model()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
