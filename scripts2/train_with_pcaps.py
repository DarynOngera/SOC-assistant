#!/usr/bin/env python3
"""
Train Model with Aggregated Normal and Attack Traffic
Processes all PCAPs and trains the model for better detection
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.append('/home/ongera/projects/SOC-assistant')

from mininet_data_generation.data_capture.preprocess_pcap import PCAPPreprocessor
from src.models.supervised_trainer import SupervisedSOCDetector

def aggregate_pcap_data():
    """Aggregate data from all PCAPs"""
    
    print("="*70)
    print("AGGREGATING PCAP DATA FOR TRAINING")
    print("="*70 + "\n")
    
    pcap_dir = '/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/pcaps'
    
    if not os.path.exists(pcap_dir):
        print(f"✗ PCAP directory not found: {pcap_dir}")
        return None
    
    # Get all PCAPs
    all_pcaps = [f for f in os.listdir(pcap_dir) if f.endswith('.pcap')]
    
    if not all_pcaps:
        print(f"✗ No PCAP files found in {pcap_dir}")
        return None
    
    print(f"Found {len(all_pcaps)} PCAP files\n")
    
    # Separate normal and attack
    normal_pcaps = [p for p in all_pcaps if 'normal_traffic' in p]
    attack_pcaps = [p for p in all_pcaps if 'attack_' in p]
    
    print(f"Normal traffic PCAPs: {len(normal_pcaps)}")
    print(f"Attack PCAPs: {len(attack_pcaps)}\n")
    
    # Initialize preprocessor
    preprocessor = PCAPPreprocessor()
    
    all_data = []
    
    # Process normal traffic
    print("[1/2] Processing Normal Traffic PCAPs...")
    for pcap in normal_pcaps:
        pcap_path = os.path.join(pcap_dir, pcap)
        print(f"  Processing: {pcap}")
        
        try:
            # Use process_pcap_file method
            features_list = preprocessor.process_pcap_file(pcap_path)
            
            if features_list and len(features_list) > 0:
                # Convert to DataFrame
                data = pd.DataFrame(features_list)
                # Label as normal (0)
                data['label'] = 0
                data['attack_type'] = 'normal'
                all_data.append(data)
                print(f"    ✓ Extracted {len(data)} flows")
            else:
                print(f"    ⚠ No data extracted")
        except Exception as e:
            print(f"    ✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Process attack traffic
    print("\n[2/2] Processing Attack PCAPs...")
    for pcap in attack_pcaps:
        pcap_path = os.path.join(pcap_dir, pcap)
        
        # Extract attack type from filename
        attack_type = pcap.split('_')[1]  # e.g., 'syn' from 'attack_syn_flood_...'
        
        print(f"  Processing: {pcap} ({attack_type})")
        
        try:
            # Use process_pcap_file method
            features_list = preprocessor.process_pcap_file(pcap_path)
            
            if features_list and len(features_list) > 0:
                # Convert to DataFrame
                data = pd.DataFrame(features_list)
                # Label as attack (1)
                data['label'] = 1
                data['attack_type'] = attack_type
                all_data.append(data)
                print(f"    ✓ Extracted {len(data)} flows")
            else:
                print(f"    ⚠ No data extracted")
        except Exception as e:
            print(f"    ✗ Error: {e}")
            import traceback
            traceback.print_exc()
    
    if not all_data:
        print("\n✗ No data extracted from PCAPs")
        return None
    
    # Combine all data
    print("\n" + "="*70)
    print("AGGREGATING DATA")
    print("="*70 + "\n")
    
    combined_data = pd.concat(all_data, ignore_index=True)
    
    print(f"Total flows: {len(combined_data)}")
    print(f"Normal flows: {len(combined_data[combined_data['label'] == 0])}")
    print(f"Attack flows: {len(combined_data[combined_data['label'] == 1])}")
    
    print("\nAttack type distribution:")
    attack_dist = combined_data[combined_data['label'] == 1]['attack_type'].value_counts()
    for attack_type, count in attack_dist.items():
        print(f"  • {attack_type}: {count} flows")
    
    return combined_data

def save_training_data(data, output_dir='data'):
    """Save aggregated data for training"""
    
    print("\n" + "="*70)
    print("SAVING TRAINING DATA")
    print("="*70 + "\n")
    
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save full dataset
    full_path = os.path.join(output_dir, f'mininet_training_data_{timestamp}.csv')
    data.to_csv(full_path, index=False)
    print(f"✓ Saved full dataset: {full_path}")
    print(f"  Size: {os.path.getsize(full_path):,} bytes")
    print(f"  Rows: {len(data)}")
    print(f"  Columns: {len(data.columns)}")
    
    # Save train/test split
    from sklearn.model_selection import train_test_split
    
    train_data, test_data = train_test_split(data, test_size=0.2, random_state=42, stratify=data['label'])
    
    train_path = os.path.join(output_dir, f'mininet_train_{timestamp}.csv')
    test_path = os.path.join(output_dir, f'mininet_test_{timestamp}.csv')
    
    train_data.to_csv(train_path, index=False)
    test_data.to_csv(test_path, index=False)
    
    print(f"\n✓ Saved train set: {train_path}")
    print(f"  Rows: {len(train_data)}")
    print(f"  Normal: {len(train_data[train_data['label'] == 0])}")
    print(f"  Attack: {len(train_data[train_data['label'] == 1])}")
    
    print(f"\n✓ Saved test set: {test_path}")
    print(f"  Rows: {len(test_data)}")
    print(f"  Normal: {len(test_data[test_data['label'] == 0])}")
    print(f"  Attack: {len(test_data[test_data['label'] == 1])}")
    
    return train_path, test_path

def train_model(train_path):
    """Train model with aggregated data"""
    
    print("\n" + "="*70)
    print("TRAINING MODEL")
    print("="*70 + "\n")
    
    # Initialize detector
    detector = SupervisedSOCDetector(random_state=42)
    
    print("Loading training data...")
    train_data = pd.read_csv(train_path)
    
    print(f"✓ Loaded {len(train_data)} training samples")
    print(f"  Normal: {len(train_data[train_data['label'] == 0])}")
    print(f"  Attack: {len(train_data[train_data['label'] == 1])}")
    
    # Train model
    print("\nTraining model...")
    print("This may take a few minutes...\n")
    
    try:
        results = detector.train(train_data)
        
        print("\n" + "="*70)
        print("TRAINING COMPLETE")
        print("="*70 + "\n")
        
        print("Model Performance:")
        print(f"  • Accuracy: {results.get('accuracy', 'N/A'):.4f}")
        print(f"  • Precision: {results.get('precision', 'N/A'):.4f}")
        print(f"  • Recall: {results.get('recall', 'N/A'):.4f}")
        print(f"  • F1 Score: {results.get('f1_score', 'N/A'):.4f}")
        
        if 'confusion_matrix' in results:
            cm = results['confusion_matrix']
            print(f"\nConfusion Matrix:")
            print(f"  TN: {cm[0][0]}, FP: {cm[0][1]}")
            print(f"  FN: {cm[1][0]}, TP: {cm[1][1]}")
        
        print(f"\nModel saved to: models/")
        print(f"  • mininet_model.pkl")
        print(f"  • mininet_scaler.pkl")
        print(f"  • mininet_feature_columns.pkl")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model(test_path):
    """Test trained model"""
    
    print("\n" + "="*70)
    print("TESTING MODEL")
    print("="*70 + "\n")
    
    # Load model
    detector = SupervisedSOCDetector(random_state=42)
    detector.load_models()
    
    # Load test data
    test_data = pd.read_csv(test_path)
    
    print(f"Testing on {len(test_data)} samples...")
    
    # Make predictions
    predictions = []
    actuals = []
    
    for idx, row in test_data.iterrows():
        row_dict = row.to_dict()
        actual = row_dict.pop('label')
        row_dict.pop('attack_type', None)
        
        result = detector.predict_single(row_dict)
        
        predictions.append(result['prediction'])
        actuals.append(actual)
    
    # Calculate metrics
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
    
    accuracy = accuracy_score(actuals, predictions)
    precision = precision_score(actuals, predictions)
    recall = recall_score(actuals, predictions)
    f1 = f1_score(actuals, predictions)
    cm = confusion_matrix(actuals, predictions)
    
    print("\nTest Results:")
    print(f"  • Accuracy: {accuracy:.4f}")
    print(f"  • Precision: {precision:.4f}")
    print(f"  • Recall: {recall:.4f}")
    print(f"  • F1 Score: {f1:.4f}")
    
    print(f"\nConfusion Matrix:")
    print(f"  TN: {cm[0][0]}, FP: {cm[0][1]}")
    print(f"  FN: {cm[1][0]}, TP: {cm[1][1]}")
    
    # Calculate detection rates
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
    
    return True

def main():
    """Main training pipeline"""
    
    print("\n" + "="*70)
    print("MININET MODEL TRAINING PIPELINE")
    print("="*70 + "\n")
    
    # Step 1: Aggregate data
    data = aggregate_pcap_data()
    
    if data is None or len(data) == 0:
        print("\n✗ Failed to aggregate PCAP data")
        return False
    
    # Step 2: Save training data
    train_path, test_path = save_training_data(data)
    
    # Step 3: Train model
    success = train_model(train_path)
    
    if not success:
        print("\n✗ Training failed")
        return False
    
    # Step 4: Test model
    test_model(test_path)
    
    # Final summary
    print("\n" + "="*70)
    print("PIPELINE COMPLETE")
    print("="*70 + "\n")
    
    print("✅ Model trained successfully!")
    print("\nNext steps:")
    print("  1. Restart dashboard: cd src/dashboard && python3 server.py")
    print("  2. Test simulations in UI")
    print("  3. Verify improved attack detection")
    
    print("\nModel files:")
    print("  • models/mininet_model.pkl")
    print("  • models/mininet_scaler.pkl")
    print("  • models/mininet_feature_columns.pkl")
    
    print("\nTraining data:")
    print(f"  • {train_path}")
    print(f"  • {test_path}")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
