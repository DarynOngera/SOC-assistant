#!/usr/bin/env python3
"""
Comprehensive Model Training with Realistic Evaluation
Includes detailed performance reports and visualizations
"""

import os
import sys
import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score,
    precision_score, recall_score, f1_score, roc_auc_score,
    roc_curve, precision_recall_curve, average_precision_score
)
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.append('/home/ongera/projects/SOC-assistant')
from mininet_data_generation.data_capture.preprocess_pcap import PCAPPreprocessor

class ComprehensiveModelTrainer:
    """Comprehensive model training with detailed evaluation"""
    
    def __init__(self):
        self.pcap_dir = '/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/pcaps'
        self.output_dir = 'training_reports'
        self.model_dir = 'models'
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def aggregate_all_pcaps(self):
        """Aggregate all PCAP data"""
        
        print("="*70)
        print("STEP 1: AGGREGATING PCAP DATA")
        print("="*70 + "\n")
        
        pcap_files = [f for f in os.listdir(self.pcap_dir) if f.endswith('.pcap')]
        
        if not pcap_files:
            print(f"✗ No PCAP files found in {self.pcap_dir}")
            return None
        
        print(f"Found {len(pcap_files)} PCAP files\n")
        
        # Separate by type
        normal_pcaps = [f for f in pcap_files if 'normal_traffic' in f]
        attack_pcaps = [f for f in pcap_files if 'attack_' in f]
        
        print(f"Normal traffic PCAPs: {len(normal_pcaps)}")
        print(f"Attack PCAPs: {len(attack_pcaps)}\n")
        
        preprocessor = PCAPPreprocessor()
        all_data = []
        
        # Process normal traffic
        print("Processing Normal Traffic...")
        for idx, pcap in enumerate(normal_pcaps, 1):
            pcap_path = os.path.join(self.pcap_dir, pcap)
            print(f"  [{idx}/{len(normal_pcaps)}] {pcap}")
            
            try:
                features_list = preprocessor.process_pcap_file(pcap_path)
                if features_list and len(features_list) > 0:
                    data = pd.DataFrame(features_list)
                    data['label'] = 0
                    data['attack_type'] = 'normal'
                    data['pcap_source'] = pcap
                    all_data.append(data)
                    print(f"      ✓ {len(data)} flows")
            except Exception as e:
                print(f"      ✗ Error: {e}")
        
        # Process attack traffic
        print("\nProcessing Attack Traffic...")
        for idx, pcap in enumerate(attack_pcaps, 1):
            pcap_path = os.path.join(self.pcap_dir, pcap)
            
            # Extract attack type
            if 'syn_flood' in pcap:
                attack_type = 'syn_flood'
            elif 'port_scan' in pcap:
                attack_type = 'port_scan'
            elif 'udp_flood' in pcap:
                attack_type = 'udp_flood'
            elif 'http_flood' in pcap:
                attack_type = 'http_flood'
            elif 'icmp_flood' in pcap:
                attack_type = 'icmp_flood'
            else:
                attack_type = 'unknown'
            
            print(f"  [{idx}/{len(attack_pcaps)}] {pcap} ({attack_type})")
            
            try:
                features_list = preprocessor.process_pcap_file(pcap_path)
                if features_list and len(features_list) > 0:
                    data = pd.DataFrame(features_list)
                    data['label'] = 1
                    data['attack_type'] = attack_type
                    data['pcap_source'] = pcap
                    all_data.append(data)
                    print(f"      ✓ {len(data)} flows")
            except Exception as e:
                print(f"      ✗ Error: {e}")
        
        if not all_data:
            print("\n✗ No data extracted")
            return None
        
        # Combine
        combined_data = pd.concat(all_data, ignore_index=True)
        
        print("\n" + "="*70)
        print("DATA AGGREGATION SUMMARY")
        print("="*70)
        print(f"\nTotal flows: {len(combined_data)}")
        print(f"Normal flows: {len(combined_data[combined_data['label'] == 0])}")
        print(f"Attack flows: {len(combined_data[combined_data['label'] == 1])}")
        
        print("\nAttack type distribution:")
        attack_dist = combined_data[combined_data['label'] == 1]['attack_type'].value_counts()
        for attack_type, count in attack_dist.items():
            print(f"  • {attack_type}: {count} flows")
        
        # Save aggregated data
        data_path = os.path.join('data', f'aggregated_data_{self.timestamp}.csv')
        os.makedirs('data', exist_ok=True)
        combined_data.to_csv(data_path, index=False)
        print(f"\n✓ Saved aggregated data: {data_path}")
        
        return combined_data
    
    def prepare_data(self, data):
        """Prepare data for training"""
        
        print("\n" + "="*70)
        print("STEP 2: PREPARING DATA")
        print("="*70 + "\n")
        
        # Remove non-feature columns
        feature_cols = [c for c in data.columns 
                       if c not in ['label', 'attack_type', 'pcap_source', 'src_ip', 'dst_ip']]
        
        print(f"Features: {len(feature_cols)}")
        
        X = data[feature_cols]
        y = data['label']
        
        # Split: 60% train, 20% validation, 20% test
        print("\nSplitting data: 60% train, 20% validation, 20% test")
        
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp
        )
        
        print(f"\nTrain: {len(X_train)} samples (Normal: {sum(y_train==0)}, Attack: {sum(y_train==1)})")
        print(f"Val:   {len(X_val)} samples (Normal: {sum(y_val==0)}, Attack: {sum(y_val==1)})")
        print(f"Test:  {len(X_test)} samples (Normal: {sum(y_test==0)}, Attack: {sum(y_test==1)})")
        
        return X_train, X_val, X_test, y_train, y_val, y_test, feature_cols
    
    def train_model(self, X_train, y_train, feature_cols):
        """Train model with cross-validation"""
        
        print("\n" + "="*70)
        print("STEP 3: TRAINING MODEL")
        print("="*70 + "\n")
        
        # Scale features
        print("Scaling features...")
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        
        # Model with regularization
        print("\nTraining Random Forest with regularization...")
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=10,
            min_samples_leaf=4,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )
        
        # Cross-validation
        print("\nPerforming 5-fold cross-validation...")
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        
        cv_scores = {
            'accuracy': cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='accuracy'),
            'precision': cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='precision'),
            'recall': cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='recall'),
            'f1': cross_val_score(model, X_train_scaled, y_train, cv=cv, scoring='f1')
        }
        
        print("\nCross-Validation Results:")
        for metric, scores in cv_scores.items():
            print(f"  {metric.capitalize():12s}: {scores.mean():.4f} (+/- {scores.std() * 2:.4f})")
        
        # Train final model
        print("\nTraining final model...")
        model.fit(X_train_scaled, y_train)
        print("✓ Model trained")
        
        return model, scaler, cv_scores
    
    def evaluate_model(self, model, scaler, X_val, y_val, X_test, y_test, feature_cols):
        """Comprehensive model evaluation"""
        
        print("\n" + "="*70)
        print("STEP 4: MODEL EVALUATION")
        print("="*70)
        
        results = {}
        
        # Validation evaluation
        print("\n[VALIDATION SET]")
        print("-" * 70)
        
        X_val_scaled = scaler.transform(X_val)
        y_val_pred = model.predict(X_val_scaled)
        y_val_proba = model.predict_proba(X_val_scaled)[:, 1]
        
        val_metrics = {
            'accuracy': accuracy_score(y_val, y_val_pred),
            'precision': precision_score(y_val, y_val_pred, zero_division=0),
            'recall': recall_score(y_val, y_val_pred, zero_division=0),
            'f1': f1_score(y_val, y_val_pred, zero_division=0),
            'roc_auc': roc_auc_score(y_val, y_val_proba) if len(np.unique(y_val)) > 1 else 0
        }
        
        print(f"\nMetrics:")
        for metric, value in val_metrics.items():
            print(f"  {metric.capitalize():12s}: {value:.4f}")
        
        val_cm = confusion_matrix(y_val, y_val_pred)
        print(f"\nConfusion Matrix:")
        print(f"  TN: {val_cm[0][0]:4d}  FP: {val_cm[0][1]:4d}")
        print(f"  FN: {val_cm[1][0]:4d}  TP: {val_cm[1][1]:4d}")
        
        results['validation'] = {
            'metrics': val_metrics,
            'confusion_matrix': val_cm.tolist(),
            'predictions': y_val_pred.tolist(),
            'probabilities': y_val_proba.tolist()
        }
        
        # Test evaluation
        print("\n[TEST SET - FINAL PERFORMANCE]")
        print("-" * 70)
        
        X_test_scaled = scaler.transform(X_test)
        y_test_pred = model.predict(X_test_scaled)
        y_test_proba = model.predict_proba(X_test_scaled)[:, 1]
        
        test_metrics = {
            'accuracy': accuracy_score(y_test, y_test_pred),
            'precision': precision_score(y_test, y_test_pred, zero_division=0),
            'recall': recall_score(y_test, y_test_pred, zero_division=0),
            'f1': f1_score(y_test, y_test_pred, zero_division=0),
            'roc_auc': roc_auc_score(y_test, y_test_proba) if len(np.unique(y_test)) > 1 else 0
        }
        
        print(f"\nMetrics:")
        for metric, value in test_metrics.items():
            print(f"  {metric.capitalize():12s}: {value:.4f}")
        
        test_cm = confusion_matrix(y_test, y_test_pred)
        print(f"\nConfusion Matrix:")
        print(f"  TN: {test_cm[0][0]:4d}  FP: {test_cm[0][1]:4d}")
        print(f"  FN: {test_cm[1][0]:4d}  TP: {test_cm[1][1]:4d}")
        
        # Detailed metrics
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
        
        print("\nClassification Report:")
        print(classification_report(y_test, y_test_pred, target_names=['Normal', 'Attack']))
        
        results['test'] = {
            'metrics': test_metrics,
            'confusion_matrix': test_cm.tolist(),
            'predictions': y_test_pred.tolist(),
            'probabilities': y_test_proba.tolist()
        }
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 10 Important Features:")
        for idx, row in feature_importance.head(10).iterrows():
            print(f"  {row['feature']:30s}: {row['importance']:.4f}")
        
        results['feature_importance'] = feature_importance.to_dict('records')
        
        return results
    
    def generate_visualizations(self, model, scaler, X_test, y_test, results):
        """Generate comprehensive visualizations"""
        
        print("\n" + "="*70)
        print("STEP 5: GENERATING VISUALIZATIONS")
        print("="*70 + "\n")
        
        fig = plt.figure(figsize=(20, 12))
        
        # 1. Confusion Matrix
        ax1 = plt.subplot(2, 3, 1)
        cm = np.array(results['test']['confusion_matrix'])
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax1)
        ax1.set_title('Confusion Matrix (Test Set)', fontsize=14, fontweight='bold')
        ax1.set_ylabel('True Label')
        ax1.set_xlabel('Predicted Label')
        ax1.set_xticklabels(['Normal', 'Attack'])
        ax1.set_yticklabels(['Normal', 'Attack'])
        
        # 2. ROC Curve
        ax2 = plt.subplot(2, 3, 2)
        X_test_scaled = scaler.transform(X_test)
        y_test_proba = model.predict_proba(X_test_scaled)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, y_test_proba)
        roc_auc = results['test']['metrics']['roc_auc']
        
        ax2.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.4f})')
        ax2.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
        ax2.set_xlim([0.0, 1.0])
        ax2.set_ylim([0.0, 1.05])
        ax2.set_xlabel('False Positive Rate')
        ax2.set_ylabel('True Positive Rate')
        ax2.set_title('ROC Curve', fontsize=14, fontweight='bold')
        ax2.legend(loc="lower right")
        ax2.grid(True, alpha=0.3)
        
        # 3. Precision-Recall Curve
        ax3 = plt.subplot(2, 3, 3)
        precision, recall, _ = precision_recall_curve(y_test, y_test_proba)
        avg_precision = average_precision_score(y_test, y_test_proba)
        
        ax3.plot(recall, precision, color='blue', lw=2, label=f'PR curve (AP = {avg_precision:.4f})')
        ax3.set_xlabel('Recall')
        ax3.set_ylabel('Precision')
        ax3.set_title('Precision-Recall Curve', fontsize=14, fontweight='bold')
        ax3.legend(loc="lower left")
        ax3.grid(True, alpha=0.3)
        
        # 4. Feature Importance
        ax4 = plt.subplot(2, 3, 4)
        feature_imp = pd.DataFrame(results['feature_importance']).head(10)
        ax4.barh(range(len(feature_imp)), feature_imp['importance'])
        ax4.set_yticks(range(len(feature_imp)))
        ax4.set_yticklabels(feature_imp['feature'])
        ax4.set_xlabel('Importance')
        ax4.set_title('Top 10 Feature Importance', fontsize=14, fontweight='bold')
        ax4.invert_yaxis()
        
        # 5. Metrics Comparison
        ax5 = plt.subplot(2, 3, 5)
        metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1', 'ROC AUC']
        metric_keys = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
        val_values = [results['validation']['metrics'][k] for k in metric_keys]
        test_values = [results['test']['metrics'][k] for k in metric_keys]
        
        x = np.arange(len(metrics_names))
        width = 0.35
        
        ax5.bar(x - width/2, val_values, width, label='Validation', alpha=0.8)
        ax5.bar(x + width/2, test_values, width, label='Test', alpha=0.8)
        ax5.set_ylabel('Score')
        ax5.set_title('Metrics Comparison', fontsize=14, fontweight='bold')
        ax5.set_xticks(x)
        ax5.set_xticklabels(metrics_names, rotation=45, ha='right')
        ax5.legend()
        ax5.set_ylim([0, 1.1])
        ax5.grid(True, alpha=0.3, axis='y')
        
        # 6. Prediction Distribution
        ax6 = plt.subplot(2, 3, 6)
        y_test_pred = model.predict(X_test_scaled)
        
        correct = y_test == y_test_pred
        incorrect = ~correct
        
        ax6.scatter(y_test_proba[correct], y_test[correct], c='green', alpha=0.5, label='Correct', s=50)
        ax6.scatter(y_test_proba[incorrect], y_test[incorrect], c='red', alpha=0.5, label='Incorrect', s=50, marker='x')
        ax6.axvline(x=0.5, color='black', linestyle='--', label='Threshold')
        ax6.set_xlabel('Predicted Probability')
        ax6.set_ylabel('True Label')
        ax6.set_title('Prediction Distribution', fontsize=14, fontweight='bold')
        ax6.legend()
        ax6.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save
        viz_path = os.path.join(self.output_dir, f'model_evaluation_{self.timestamp}.png')
        plt.savefig(viz_path, dpi=300, bbox_inches='tight')
        print(f"✓ Saved visualizations: {viz_path}")
        plt.close()
        
        return viz_path
    
    def save_model_and_report(self, model, scaler, feature_cols, results, cv_scores):
        """Save model and generate comprehensive report"""
        
        print("\n" + "="*70)
        print("STEP 6: SAVING MODEL AND REPORTS")
        print("="*70 + "\n")
        
        # Save model
        model_path = os.path.join(self.model_dir, 'mininet_model.pkl')
        joblib.dump(model, model_path)
        print(f"✓ Saved model: {model_path}")
        
        scaler_path = os.path.join(self.model_dir, 'mininet_scaler.pkl')
        joblib.dump(scaler, scaler_path)
        print(f"✓ Saved scaler: {scaler_path}")
        
        feature_path = os.path.join(self.model_dir, 'mininet_feature_columns.pkl')
        joblib.dump(feature_cols, feature_path)
        print(f"✓ Saved feature columns: {feature_path}")
        
        # Generate JSON report
        report = {
            'timestamp': self.timestamp,
            'model_config': {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 10,
                'min_samples_leaf': 4,
                'class_weight': 'balanced'
            },
            'cross_validation': {
                metric: {
                    'mean': float(scores.mean()),
                    'std': float(scores.std()),
                    'scores': scores.tolist()
                }
                for metric, scores in cv_scores.items()
            },
            'validation_performance': results['validation']['metrics'],
            'test_performance': results['test']['metrics'],
            'confusion_matrix': {
                'validation': results['validation']['confusion_matrix'],
                'test': results['test']['confusion_matrix']
            },
            'feature_importance': results['feature_importance'][:20],  # Top 20
            'num_features': len(feature_cols)
        }
        
        report_path = os.path.join(self.output_dir, f'training_report_{self.timestamp}.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✓ Saved JSON report: {report_path}")
        
        # Generate text report
        text_report_path = os.path.join(self.output_dir, f'training_report_{self.timestamp}.txt')
        with open(text_report_path, 'w') as f:
            f.write("="*70 + "\n")
            f.write("MODEL TRAINING REPORT\n")
            f.write("="*70 + "\n\n")
            f.write(f"Timestamp: {self.timestamp}\n\n")
            
            f.write("MODEL CONFIGURATION\n")
            f.write("-" * 70 + "\n")
            for key, value in report['model_config'].items():
                f.write(f"  {key}: {value}\n")
            
            f.write("\n\nCROSS-VALIDATION RESULTS (5-fold)\n")
            f.write("-" * 70 + "\n")
            for metric, data in report['cross_validation'].items():
                f.write(f"  {metric.capitalize():12s}: {data['mean']:.4f} (+/- {data['std']*2:.4f})\n")
            
            f.write("\n\nVALIDATION PERFORMANCE\n")
            f.write("-" * 70 + "\n")
            for metric, value in report['validation_performance'].items():
                f.write(f"  {metric.capitalize():12s}: {value:.4f}\n")
            
            f.write("\n\nTEST PERFORMANCE (FINAL)\n")
            f.write("-" * 70 + "\n")
            for metric, value in report['test_performance'].items():
                f.write(f"  {metric.capitalize():12s}: {value:.4f}\n")
            
            f.write("\n\nTOP 10 IMPORTANT FEATURES\n")
            f.write("-" * 70 + "\n")
            for i, feat in enumerate(report['feature_importance'][:10], 1):
                f.write(f"  {i:2d}. {feat['feature']:30s}: {feat['importance']:.4f}\n")
        
        print(f"✓ Saved text report: {text_report_path}")
        
        return report_path, text_report_path
    
    def run_complete_pipeline(self):
        """Run complete training pipeline"""
        
        print("\n" + "="*70)
        print("COMPREHENSIVE MODEL TRAINING PIPELINE")
        print("="*70 + "\n")
        
        # Step 1: Aggregate data
        data = self.aggregate_all_pcaps()
        if data is None:
            return False
        
        # Step 2: Prepare data
        X_train, X_val, X_test, y_train, y_val, y_test, feature_cols = self.prepare_data(data)
        
        # Step 3: Train model
        model, scaler, cv_scores = self.train_model(X_train, y_train, feature_cols)
        
        # Step 4: Evaluate
        results = self.evaluate_model(model, scaler, X_val, y_val, X_test, y_test, feature_cols)
        
        # Step 5: Visualizations
        viz_path = self.generate_visualizations(model, scaler, X_test, y_test, results)
        
        # Step 6: Save everything
        report_path, text_report_path = self.save_model_and_report(
            model, scaler, feature_cols, results, cv_scores
        )
        
        # Final summary
        print("\n" + "="*70)
        print("TRAINING COMPLETE!")
        print("="*70)
        
        print("\nFinal Test Performance:")
        for metric, value in results['test']['metrics'].items():
            print(f"  • {metric.capitalize():12s}: {value:.4f}")
        
        print("\nGenerated Files:")
        print(f"  • Model: models/mininet_model.pkl")
        print(f"  • Scaler: models/mininet_scaler.pkl")
        print(f"  • Features: models/mininet_feature_columns.pkl")
        print(f"  • Visualizations: {viz_path}")
        print(f"  • JSON Report: {report_path}")
        print(f"  • Text Report: {text_report_path}")
        
        print("\nNext Steps:")
        print("  1. Review reports in training_reports/")
        print("  2. Restart dashboard: cd src/dashboard && python3 server.py")
        print("  3. Test simulations in UI")
        
        return True

def main():
    trainer = ComprehensiveModelTrainer()
    success = trainer.run_complete_pipeline()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n✗ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
