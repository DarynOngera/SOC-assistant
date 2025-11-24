#!/usr/bin/env python3
"""
Simple NLP Alert Classifier Training
Uses scikit-learn (no transformers required)
Trains TF-IDF + Random Forest for alert classification
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    confusion_matrix, classification_report
)
import joblib

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleNLPTrainer:
    """Train simple NLP classifier using TF-IDF + Random Forest"""
    
    def __init__(self, output_dir: str = "training_output/nlp_models"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.severity_labels = ['low', 'medium', 'high', 'critical']
        self.label2id = {label: i for i, label in enumerate(self.severity_labels)}
        self.id2label = {i: label for label, i in self.label2id.items()}
        
        self.vectorizer = None
        self.model = None
        
        logger.info(f"SimpleNLPTrainer initialized (output: {self.output_dir})")
    
    def create_synthetic_dataset(self, n_samples: int = 1000) -> pd.DataFrame:
        """Create synthetic training data"""
        logger.info(f"Creating synthetic dataset with {n_samples} samples")
        
        templates = {
            'critical': [
                "Critical ransomware attack detected - {action}",
                "Data breach in progress from {ip} - {action}",
                "Zero-day exploit CVE-{cve} detected - {action}",
                "APT activity detected targeting {target} - {action}",
                "Root access compromised on {target} - {action}",
                "Backdoor installed on {target} - {action}",
                "Command and control traffic to {ip} - {action}",
                "Data exfiltration detected to {ip} - {action}"
            ],
            'high': [
                "Malware detected in {target} - {action}",
                "SQL injection attempt on {target} - {action}",
                "DDoS attack from {ip} - {action}",
                "Brute force attack on {target} - {action}",
                "Exploit attempt CVE-{cve} - {action}",
                "Trojan detected in email attachment - {action}",
                "Privilege escalation attempt - {action}",
                "Unauthorized access from {ip} - {action}"
            ],
            'medium': [
                "Port scan detected from {ip}",
                "Suspicious activity from {ip}",
                "Unusual traffic pattern to {target}",
                "Failed login attempts from {ip}",
                "Policy violation on {target}",
                "Network reconnaissance from {ip}",
                "Suspicious connection to {ip}",
                "Anomaly detected in traffic to {target}"
            ],
            'low': [
                "Informational alert - {action}",
                "Configuration change on {target}",
                "Routine maintenance on {target}",
                "Normal traffic spike to {target}",
                "Update notification for {target}",
                "Scheduled scan completed",
                "Backup completed successfully",
                "System health check passed"
            ]
        }
        
        actions = [
            "immediate response required",
            "investigating",
            "blocked by firewall",
            "user notified",
            "logged for review",
            "quarantined",
            "mitigated",
            "escalated to SOC"
        ]
        
        targets = [
            "web server", "database", "mail server", "file server",
            "domain controller", "workstation", "application server"
        ]
        
        ips = [f"192.168.{np.random.randint(1,255)}.{np.random.randint(1,255)}" 
               for _ in range(100)]
        
        cves = [f"2024-{np.random.randint(1000,9999)}" for _ in range(50)]
        
        data = []
        samples_per_class = n_samples // len(self.severity_labels)
        
        for severity in self.severity_labels:
            for _ in range(samples_per_class):
                template = np.random.choice(templates[severity])
                text = template.format(
                    action=np.random.choice(actions),
                    ip=np.random.choice(ips),
                    target=np.random.choice(targets),
                    cve=np.random.choice(cves)
                )
                data.append({
                    'text': text,
                    'severity': severity,
                    'label': self.label2id[severity]
                })
        
        df = pd.DataFrame(data)
        
        # Shuffle
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        logger.info(f"✓ Created {len(df)} synthetic alerts")
        logger.info(f"Distribution:\n{df['severity'].value_counts().sort_index()}")
        
        return df
    
    def prepare_data(self, df: pd.DataFrame, test_size: float = 0.2, val_size: float = 0.1):
        """Split data into train/val/test sets"""
        logger.info("Preparing data splits...")
        
        # Split train and test
        train_val_df, test_df = train_test_split(
            df, test_size=test_size, random_state=42, stratify=df['label']
        )
        
        # Split train and validation
        train_df, val_df = train_test_split(
            train_val_df, test_size=val_size/(1-test_size), 
            random_state=42, stratify=train_val_df['label']
        )
        
        logger.info(f"Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
        
        return train_df, val_df, test_df
    
    def train(self, train_df: pd.DataFrame, val_df: pd.DataFrame):
        """Train TF-IDF + Random Forest model"""
        logger.info("Training TF-IDF + Random Forest model...")
        
        # Initialize TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8,
            stop_words='english'
        )
        
        # Fit vectorizer and transform training data
        X_train = self.vectorizer.fit_transform(train_df['text'])
        y_train = train_df['label'].values
        
        logger.info(f"TF-IDF features: {X_train.shape[1]}")
        
        # Train Random Forest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        
        # Validate
        X_val = self.vectorizer.transform(val_df['text'])
        y_val = val_df['label'].values
        val_accuracy = self.model.score(X_val, y_val)
        
        logger.info(f"✓ Training complete - Validation Accuracy: {val_accuracy:.4f}")
        
        return val_accuracy
    
    def evaluate(self, test_df: pd.DataFrame):
        """Evaluate model on test set"""
        logger.info("Evaluating model...")
        
        X_test = self.vectorizer.transform(test_df['text'])
        y_test = test_df['label'].values
        
        # Predictions
        y_pred = self.model.predict(X_test)
        
        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average='weighted'
        )
        
        results = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1)
        }
        
        logger.info(f"Test Results: {results}")
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Classification report
        report = classification_report(
            y_test, y_pred,
            target_names=self.severity_labels,
            output_dict=True
        )
        
        return results, cm, report
    
    def visualize_results(self, cm, report, results):
        """Generate visualizations"""
        logger.info("Generating visualizations...")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Confusion Matrix
        ax1 = axes[0, 0]
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax1,
                   xticklabels=self.severity_labels,
                   yticklabels=self.severity_labels)
        ax1.set_title('Confusion Matrix', fontsize=14, fontweight='bold')
        ax1.set_ylabel('True Label')
        ax1.set_xlabel('Predicted Label')
        
        # 2. Per-class Performance
        ax2 = axes[0, 1]
        metrics_df = pd.DataFrame({
            'Precision': [report[label]['precision'] for label in self.severity_labels],
            'Recall': [report[label]['recall'] for label in self.severity_labels],
            'F1-Score': [report[label]['f1-score'] for label in self.severity_labels]
        }, index=self.severity_labels)
        
        metrics_df.plot(kind='bar', ax=ax2, rot=0)
        ax2.set_title('Per-Class Performance', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Score')
        ax2.set_ylim([0, 1.1])
        ax2.legend(loc='lower right')
        ax2.grid(axis='y', alpha=0.3)
        
        # 3. Overall Metrics
        ax3 = axes[1, 0]
        metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
        values = [results['accuracy'], results['precision'], results['recall'], results['f1_score']]
        colors = ['skyblue', 'lightcoral', 'lightgreen', 'lightyellow']
        bars = ax3.bar(metrics, values, color=colors)
        ax3.set_title('Overall Metrics', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Score')
        ax3.set_ylim([0, 1.1])
        ax3.grid(axis='y', alpha=0.3)
        
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}', ha='center', va='bottom')
        
        # 4. Feature Importance (Top 20)
        ax4 = axes[1, 1]
        feature_names = self.vectorizer.get_feature_names_out()
        importances = self.model.feature_importances_
        indices = np.argsort(importances)[-20:]
        
        ax4.barh(range(20), importances[indices], color='mediumpurple', alpha=0.7)
        ax4.set_yticks(range(20))
        ax4.set_yticklabels([feature_names[i] for i in indices], fontsize=8)
        ax4.set_title('Top 20 Important Features', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Importance')
        ax4.grid(axis='x', alpha=0.3)
        
        plt.tight_layout()
        
        # Save
        viz_path = self.output_dir / "training_results.png"
        plt.savefig(viz_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✓ Saved visualization to {viz_path}")
        
        return str(viz_path)
    
    def save_model(self):
        """Save trained model and vectorizer"""
        model_path = self.output_dir / "simple_classifier"
        model_path.mkdir(exist_ok=True)
        
        # Save vectorizer
        joblib.dump(self.vectorizer, model_path / "vectorizer.pkl")
        
        # Save model
        joblib.dump(self.model, model_path / "model.pkl")
        
        # Save label mappings
        with open(model_path / "labels.json", 'w') as f:
            json.dump({
                'label2id': self.label2id,
                'id2label': self.id2label,
                'severity_labels': self.severity_labels
            }, f, indent=2)
        
        logger.info(f"✓ Model saved to {model_path}")
        
        return str(model_path)
    
    def save_report(self, results, report):
        """Save training report"""
        report_data = {
            'model': 'TF-IDF + Random Forest',
            'task': 'alert_severity_classification',
            'num_labels': len(self.severity_labels),
            'labels': self.severity_labels,
            'test_results': results,
            'per_class_report': report,
            'timestamp': datetime.now().isoformat()
        }
        
        report_path = self.output_dir / "training_report.json"
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"✓ Report saved to {report_path}")
        
        return str(report_path)


def main():
    """Main training pipeline"""
    print("\n" + "="*80)
    print("SIMPLE NLP ALERT CLASSIFIER TRAINING")
    print("TF-IDF + Random Forest (No Transformers Required)")
    print("="*80 + "\n")
    
    # Initialize trainer
    trainer = SimpleNLPTrainer()
    
    # Create synthetic dataset
    df = trainer.create_synthetic_dataset(n_samples=2000)
    
    # Prepare data
    train_df, val_df, test_df = trainer.prepare_data(df)
    
    # Train
    val_accuracy = trainer.train(train_df, val_df)
    
    # Evaluate
    results, cm, report = trainer.evaluate(test_df)
    
    # Visualize
    viz_path = trainer.visualize_results(cm, report, results)
    
    # Save model
    model_path = trainer.save_model()
    
    # Save report
    report_path = trainer.save_report(results, report)
    
    print("\n" + "="*80)
    print("✓ TRAINING COMPLETE")
    print("="*80)
    print(f"\nModel: {model_path}")
    print(f"Visualization: {viz_path}")
    print(f"Report: {report_path}")
    print(f"\nTest Accuracy: {results['accuracy']:.4f}")
    print(f"Test Precision: {results['precision']:.4f}")
    print(f"Test Recall: {results['recall']:.4f}")
    print(f"Test F1-Score: {results['f1_score']:.4f}")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
