#!/usr/bin/env python3
"""
Train Alert Severity Classifier
Fine-tune DistilBERT on security alert data
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
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    confusion_matrix, classification_report
)

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import transformers
try:
    import os
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings
    os.environ['USE_TORCH'] = '1'  # Force PyTorch backend
    
    from transformers import (
        AutoTokenizer,
        AutoModelForSequenceClassification,
        TrainingArguments,
        Trainer,
        EarlyStoppingCallback
    )
    import torch
    from torch.utils.data import Dataset
    TRANSFORMERS_AVAILABLE = True
except ImportError as e:
    TRANSFORMERS_AVAILABLE = False
    logger.error(f"Transformers not available: {e}")
    logger.error("Install with: pip install transformers torch")
    sys.exit(1)


class AlertDataset(Dataset):
    """Custom dataset for alert classification"""
    
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding='max_length',
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }


class AlertClassifierTrainer:
    """Train and evaluate alert severity classifier"""
    
    def __init__(self, output_dir: str = "training_output/nlp_models"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.severity_labels = ['low', 'medium', 'high', 'critical']
        self.label2id = {label: i for i, label in enumerate(self.severity_labels)}
        self.id2label = {i: label for label, i in self.label2id.items()}
        
        self.tokenizer = None
        self.model = None
        self.trainer = None
        
        logger.info(f"AlertClassifierTrainer initialized (output: {self.output_dir})")
    
    def create_synthetic_dataset(self, n_samples: int = 1000) -> pd.DataFrame:
        """
        Create synthetic training data
        (In production, use real labeled alerts)
        """
        logger.info(f"Creating synthetic dataset with {n_samples} samples")
        
        # Templates for each severity
        templates = {
            'critical': [
                "Critical ransomware attack detected - {action}",
                "Data breach in progress - {action}",
                "Zero-day exploit detected - {action}",
                "APT activity detected - {action}",
                "Root access compromised - {action}"
            ],
            'high': [
                "Malware detected - {action}",
                "SQL injection attempt - {action}",
                "DDoS attack detected - {action}",
                "Brute force attack - {action}",
                "Exploit attempt blocked - {action}"
            ],
            'medium': [
                "Port scan detected from {ip}",
                "Suspicious activity from {ip}",
                "Unusual traffic pattern detected",
                "Failed login attempts from {ip}",
                "Policy violation detected"
            ],
            'low': [
                "Informational alert - {action}",
                "Configuration change detected",
                "Routine maintenance alert",
                "Normal traffic spike",
                "Update notification"
            ]
        }
        
        actions = [
            "immediate response required",
            "investigating",
            "blocked by firewall",
            "user notified",
            "logged for review"
        ]
        
        ips = [f"192.168.{np.random.randint(1,255)}.{np.random.randint(1,255)}" 
               for _ in range(100)]
        
        data = []
        samples_per_class = n_samples // len(self.severity_labels)
        
        for severity in self.severity_labels:
            for _ in range(samples_per_class):
                template = np.random.choice(templates[severity])
                text = template.format(
                    action=np.random.choice(actions),
                    ip=np.random.choice(ips)
                )
                data.append({
                    'text': text,
                    'severity': severity,
                    'label': self.label2id[severity]
                })
        
        df = pd.DataFrame(data)
        logger.info(f"✓ Created {len(df)} synthetic alerts")
        logger.info(f"Distribution:\n{df['severity'].value_counts()}")
        
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
    
    def initialize_model(self, model_name: str = "distilbert-base-uncased"):
        """Initialize tokenizer and model"""
        logger.info(f"Initializing model: {model_name}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=len(self.severity_labels),
            id2label=self.id2label,
            label2id=self.label2id
        )
        
        logger.info("✓ Model initialized")
    
    def train(self, train_df: pd.DataFrame, val_df: pd.DataFrame, 
              epochs: int = 3, batch_size: int = 16):
        """Train the model"""
        logger.info("Starting training...")
        
        # Create datasets
        train_dataset = AlertDataset(
            train_df['text'].values,
            train_df['label'].values,
            self.tokenizer
        )
        
        val_dataset = AlertDataset(
            val_df['text'].values,
            val_df['label'].values,
            self.tokenizer
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=str(self.output_dir / "checkpoints"),
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            warmup_steps=100,
            weight_decay=0.01,
            logging_dir=str(self.output_dir / "logs"),
            logging_steps=50,
            evaluation_strategy="epoch",
            save_strategy="epoch",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            save_total_limit=2
        )
        
        # Trainer
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
        )
        
        # Train
        self.trainer.train()
        
        logger.info("✓ Training complete")
    
    def evaluate(self, test_df: pd.DataFrame):
        """Evaluate model on test set"""
        logger.info("Evaluating model...")
        
        test_dataset = AlertDataset(
            test_df['text'].values,
            test_df['label'].values,
            self.tokenizer
        )
        
        # Get predictions
        predictions = self.trainer.predict(test_dataset)
        pred_labels = np.argmax(predictions.predictions, axis=1)
        true_labels = test_df['label'].values
        
        # Calculate metrics
        accuracy = accuracy_score(true_labels, pred_labels)
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_labels, pred_labels, average='weighted'
        )
        
        results = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1)
        }
        
        logger.info(f"Test Results: {results}")
        
        # Confusion matrix
        cm = confusion_matrix(true_labels, pred_labels)
        
        # Classification report
        report = classification_report(
            true_labels, pred_labels,
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
        bars = ax3.bar(metrics, values, color=['skyblue', 'lightcoral', 'lightgreen', 'lightyellow'])
        ax3.set_title('Overall Metrics', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Score')
        ax3.set_ylim([0, 1.1])
        ax3.grid(axis='y', alpha=0.3)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}', ha='center', va='bottom')
        
        # 4. Support per class
        ax4 = axes[1, 1]
        support = [report[label]['support'] for label in self.severity_labels]
        ax4.bar(self.severity_labels, support, color='mediumpurple', alpha=0.7)
        ax4.set_title('Samples per Class (Test Set)', fontsize=14, fontweight='bold')
        ax4.set_ylabel('Count')
        ax4.grid(axis='y', alpha=0.3)
        
        # Add value labels
        for i, v in enumerate(support):
            ax4.text(i, v, str(int(v)), ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Save
        viz_path = self.output_dir / "training_results.png"
        plt.savefig(viz_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"✓ Saved visualization to {viz_path}")
        
        return str(viz_path)
    
    def save_model(self):
        """Save trained model and tokenizer"""
        model_path = self.output_dir / "severity_classifier"
        model_path.mkdir(exist_ok=True)
        
        self.model.save_pretrained(model_path)
        self.tokenizer.save_pretrained(model_path)
        
        logger.info(f"✓ Model saved to {model_path}")
        
        return str(model_path)
    
    def save_report(self, results, report):
        """Save training report"""
        report_data = {
            'model': 'distilbert-base-uncased',
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
    print("ALERT SEVERITY CLASSIFIER TRAINING")
    print("="*80 + "\n")
    
    # Initialize trainer
    trainer = AlertClassifierTrainer()
    
    # Create synthetic dataset
    df = trainer.create_synthetic_dataset(n_samples=1000)
    
    # Prepare data
    train_df, val_df, test_df = trainer.prepare_data(df)
    
    # Initialize model
    trainer.initialize_model()
    
    # Train
    trainer.train(train_df, val_df, epochs=3, batch_size=16)
    
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
    print(f"Test F1-Score: {results['f1_score']:.4f}")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
