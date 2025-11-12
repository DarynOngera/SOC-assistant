# Performance Visualization Add-on

Add this cell after Step 9 (Evaluation) in the Colab notebook for comprehensive visualizations:

```python
## COMPREHENSIVE PERFORMANCE VISUALIZATIONS

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

print("\\n" + "="*60)
print("COMPREHENSIVE PERFORMANCE VISUALIZATIONS")
print("="*60)

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (20, 15)

# Create comprehensive visualization
fig = plt.figure(figsize=(20, 15))
gs = fig.add_gridspec(4, 3, hspace=0.3, wspace=0.3)

# 1. Model Performance Comparison (Bar Chart)
ax1 = fig.add_subplot(gs[0, :])
metrics = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
x = np.arange(len(metrics))
width = 0.25

for i, (model_name, model_results) in enumerate(results.items()):
    values = [model_results[m] for m in metrics]
    ax1.bar(x + i*width, values, width, label=model_name, alpha=0.8)

ax1.set_xlabel('Metrics', fontsize=12, fontweight='bold')
ax1.set_ylabel('Score', fontsize=12, fontweight='bold')
ax1.set_title('Model Performance Comparison - All Metrics', fontsize=14, fontweight='bold')
ax1.set_xticks(x + width)
ax1.set_xticklabels(['Accuracy', 'Precision', 'Recall', 'F1-Score', 'ROC AUC'])
ax1.legend(loc='lower right')
ax1.set_ylim([0, 1.1])
ax1.grid(axis='y', alpha=0.3)

# Add value labels on bars
for i, (model_name, model_results) in enumerate(results.items()):
    values = [model_results[m] for m in metrics]
    for j, v in enumerate(values):
        ax1.text(j + i*width, v + 0.02, f'{v:.3f}', ha='center', va='bottom', fontsize=8)

# 2. Confusion Matrices (3 models)
for idx, (name, model) in enumerate(models.items()):
    ax = fig.add_subplot(gs[1, idx])
    y_pred = model.predict(X_test_selected)
    cm = confusion_matrix(y_test, y_pred)
    
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=['Normal', 'Attack'],
                yticklabels=['Normal', 'Attack'],
                cbar_kws={'label': 'Count'})
    ax.set_title(f'{name}\\nAccuracy: {accuracy_score(y_test, y_pred):.4f}',
                fontsize=11, fontweight='bold')
    ax.set_ylabel('True Label')
    ax.set_xlabel('Predicted Label')

# 3. ROC Curves
ax4 = fig.add_subplot(gs[2, 0])
for name, model in models.items():
    y_pred_proba = model.predict_proba(X_test_selected)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
    auc = roc_auc_score(y_test, y_pred_proba)
    ax4.plot(fpr, tpr, label=f'{name} (AUC={auc:.4f})', linewidth=2)

ax4.plot([0, 1], [0, 1], 'k--', label='Random', linewidth=2)
ax4.set_xlabel('False Positive Rate', fontsize=11, fontweight='bold')
ax4.set_ylabel('True Positive Rate', fontsize=11, fontweight='bold')
ax4.set_title('ROC Curves', fontsize=12, fontweight='bold')
ax4.legend(loc='lower right')
ax4.grid(alpha=0.3)

# 4. Precision-Recall Curves
ax5 = fig.add_subplot(gs[2, 1])
for name, model in models.items():
    y_pred_proba = model.predict_proba(X_test_selected)[:, 1]
    precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
    ap = average_precision_score(y_test, y_pred_proba)
    ax5.plot(recall, precision, label=f'{name} (AP={ap:.4f})', linewidth=2)

ax5.set_xlabel('Recall', fontsize=11, fontweight='bold')
ax5.set_ylabel('Precision', fontsize=11, fontweight='bold')
ax5.set_title('Precision-Recall Curves', fontsize=12, fontweight='bold')
ax5.legend(loc='lower left')
ax5.grid(alpha=0.3)

# 5. Feature Importance (Top 15)
ax6 = fig.add_subplot(gs[2, 2])
feature_scores_top = feature_scores.head(15)
ax6.barh(range(len(feature_scores_top)), feature_scores_top['score'], color='coral')
ax6.set_yticks(range(len(feature_scores_top)))
ax6.set_yticklabels(feature_scores_top['feature'], fontsize=9)
ax6.set_xlabel('Importance Score', fontsize=11, fontweight='bold')
ax6.set_title('Top 15 Feature Importance', fontsize=12, fontweight='bold')
ax6.invert_yaxis()
ax6.grid(axis='x', alpha=0.3)

# 6. Training vs Validation Performance
ax7 = fig.add_subplot(gs[3, 0])
train_scores = []
val_scores = []
for name, model in models.items():
    train_score = model.score(X_train_selected, y_train)
    val_score = model.score(X_val_selected, y_val)
    train_scores.append(train_score)
    val_scores.append(val_score)

x_pos = np.arange(len(models))
width = 0.35
ax7.bar(x_pos - width/2, train_scores, width, label='Training', alpha=0.8, color='skyblue')
ax7.bar(x_pos + width/2, val_scores, width, label='Validation', alpha=0.8, color='lightcoral')
ax7.set_xlabel('Model', fontsize=11, fontweight='bold')
ax7.set_ylabel('Accuracy', fontsize=11, fontweight='bold')
ax7.set_title('Training vs Validation Accuracy', fontsize=12, fontweight='bold')
ax7.set_xticks(x_pos)
ax7.set_xticklabels(models.keys(), rotation=15, ha='right')
ax7.legend()
ax7.set_ylim([0, 1.1])
ax7.grid(axis='y', alpha=0.3)

# Add value labels
for i, (train, val) in enumerate(zip(train_scores, val_scores)):
    ax7.text(i - width/2, train + 0.02, f'{train:.3f}', ha='center', fontsize=9)
    ax7.text(i + width/2, val + 0.02, f'{val:.3f}', ha='center', fontsize=9)

# 7. Class Distribution
ax8 = fig.add_subplot(gs[3, 1])
class_counts = [sum(y_train == 0), sum(y_train == 1)]
colors = ['green', 'red']
wedges, texts, autotexts = ax8.pie(class_counts, labels=['Normal', 'Attack'],
                                     autopct='%1.1f%%', colors=colors,
                                     startangle=90, textprops={'fontsize': 11})
ax8.set_title('Training Data Distribution', fontsize=12, fontweight='bold')

# 8. Performance Metrics Heatmap
ax9 = fig.add_subplot(gs[3, 2])
metrics_matrix = []
for name in models.keys():
    metrics_matrix.append([
        results[name]['accuracy'],
        results[name]['precision'],
        results[name]['recall'],
        results[name]['f1'],
        results[name]['roc_auc']
    ])

sns.heatmap(metrics_matrix, annot=True, fmt='.3f', cmap='YlGnBu', ax=ax9,
            xticklabels=['Accuracy', 'Precision', 'Recall', 'F1', 'ROC AUC'],
            yticklabels=list(models.keys()),
            cbar_kws={'label': 'Score'})
ax9.set_title('Performance Metrics Heatmap', fontsize=12, fontweight='bold')
ax9.set_xlabel('Metrics', fontsize=11, fontweight='bold')
ax9.set_ylabel('Models', fontsize=11, fontweight='bold')

plt.suptitle('Comprehensive Model Performance Analysis', fontsize=16, fontweight='bold', y=0.995)
plt.savefig('comprehensive_performance.png', dpi=300, bbox_inches='tight')
plt.show()

print("\\n✓ Comprehensive visualization saved: comprehensive_performance.png")

# Additional detailed metrics table
print("\\n" + "="*60)
print("DETAILED PERFORMANCE METRICS")
print("="*60)

detailed_metrics = pd.DataFrame({
    'Model': list(models.keys()),
    'Accuracy': [results[m]['accuracy'] for m in models.keys()],
    'Precision': [results[m]['precision'] for m in models.keys()],
    'Recall': [results[m]['recall'] for m in models.keys()],
    'F1-Score': [results[m]['f1'] for m in models.keys()],
    'ROC AUC': [results[m]['roc_auc'] for m in models.keys()],
    'Train Acc': train_scores,
    'Val Acc': val_scores
})

print("\\n", detailed_metrics.to_string(index=False))

# Calculate overfitting indicators
print("\\n" + "="*60)
print("OVERFITTING ANALYSIS")
print("="*60)

for i, (name, train_acc, val_acc) in enumerate(zip(models.keys(), train_scores, val_scores)):
    gap = train_acc - val_acc
    status = "✓ Good" if gap < 0.05 else "⚠ Possible Overfitting" if gap < 0.10 else "❌ Overfitting"
    print(f"\\n{name}:")
    print(f"  Train Accuracy: {train_acc:.4f}")
    print(f"  Val Accuracy: {val_acc:.4f}")
    print(f"  Gap: {gap:.4f}")
    print(f"  Status: {status}")

print("\\n" + "="*60)
```

## Additional Visualization: Learning Curves

Add this for learning curve analysis:

```python
## LEARNING CURVES

from sklearn.model_selection import learning_curve

print("\\nGenerating learning curves...")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

for ax, (name, model) in zip(axes, models.items()):
    train_sizes, train_scores, val_scores = learning_curve(
        model, X_train_selected, y_train,
        train_sizes=np.linspace(0.1, 1.0, 10),
        cv=5, scoring='f1', n_jobs=-1
    )
    
    train_mean = np.mean(train_scores, axis=1)
    train_std = np.std(train_scores, axis=1)
    val_mean = np.mean(val_scores, axis=1)
    val_std = np.std(val_scores, axis=1)
    
    ax.plot(train_sizes, train_mean, label='Training score', color='blue', linewidth=2)
    ax.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.1, color='blue')
    
    ax.plot(train_sizes, val_mean, label='Cross-validation score', color='red', linewidth=2)
    ax.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.1, color='red')
    
    ax.set_title(f'{name} Learning Curve', fontsize=12, fontweight='bold')
    ax.set_xlabel('Training Examples', fontsize=11)
    ax.set_ylabel('F1 Score', fontsize=11)
    ax.legend(loc='lower right')
    ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('learning_curves.png', dpi=300, bbox_inches='tight')
plt.show()

print("✓ Learning curves saved: learning_curves.png")
```

## Download All Visualizations

Add at the end:

```python
## DOWNLOAD ALL VISUALIZATIONS

print("\\nDownloading all visualizations...")

viz_files = [
    'comprehensive_performance.png',
    'confusion_matrix.png',
    'learning_curves.png',
    'prediction_analysis.png'
]

for file in viz_files:
    if os.path.exists(file):
        files.download(file)
        print(f"  ✓ Downloaded: {file}")

print("\\n✓ All visualizations downloaded!")
```
