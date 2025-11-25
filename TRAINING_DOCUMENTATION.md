# SOC Assistant - Training Process Documentation

## Overview
This document provides comprehensive insights into the preprocessing, optimization, and training processes for the SOC Assistant anomaly detection system.

---

## 1. PREPROCESSING PIPELINE

### 1.1 NLP Model Preprocessing (`train_from_real_alerts.py`)

#### **Data Loading**
- **Source**: MongoDB real alerts (up to 5,000 samples)
- **Fallback**: Synthetic data generation if insufficient real data
- **Features**: Alert descriptions combining attack type, source IP, destination IP, and port

#### **Data Augmentation**
```python
Target: 2,000 balanced samples (500 per severity class)
Methods:
  - Oversampling: Repeat with text variations (e.g., "attack" → "threat")
  - Undersampling: Random sampling for over-represented classes
  - Synthetic Generation: Template-based alerts for missing severity levels
```

#### **Label Encoding**
```python
Severity Mapping:
  - low: 0
  - medium: 1
  - high: 2
  - critical: 3
```

#### **Text Processing**
- **Vectorization**: TF-IDF (Term Frequency-Inverse Document Frequency)
- **Max Features**: 5,000 terms
- **N-grams**: Unigrams and bigrams
- **Stop Words**: English stop words removed

---

### 1.2 Supervised ML Preprocessing (`supervised_trainer.py`, `enhanced_trainer.py`)

#### **Data Loading**
```python
CSV Format Support:
  - Headerless CSV: Auto-detects and assigns UNSW-NB15 column names
  - Header CSV: Uses provided column names
  - Memory-efficient chunked reading for files > 100MB
  - Sample size limiting to prevent memory issues
```

#### **Feature Alignment**
```python
Training Phase:
  - Store feature columns for consistency
  - 45 standard UNSW-NB15 columns expected
  
Testing Phase:
  - Use only common features (no zero-padding)
  - Intelligent defaults for missing features:
    * Rates/ratios → 0.0
    * Counts → 0
    * Binary flags → 0
    * Bytes/sizes → 0
```

#### **Missing Value Handling**
```python
Numeric Columns: Filled with median
Categorical Columns: Filled with mode or 'unknown'
Infinite Values: Replaced with 0
```

#### **Categorical Encoding**
```python
Method: Label Encoding
Special Handling:
  - Add 'unknown' category during training
  - Map unseen categories to 'unknown' during testing
  - Separate encoder for each categorical column
```

#### **Feature Scaling**
```python
Scaler: RobustScaler (enhanced) or StandardScaler (supervised)
Reason: RobustScaler is more robust to outliers
Formula: (X - median) / IQR
```

#### **Feature Selection**
```python
Method: SelectKBest with mutual_info_classif
Top K Features: 30-50 features (configurable)
Benefit: Reduces dimensionality and prevents overfitting
```

---

### 1.3 Mininet PCAP Preprocessing (`train_mininet_pcaps.py`)

#### **Noise Injection (Overfitting Prevention)**
```python
Gaussian Noise: 45% of feature standard deviation
Feature Corruption: 8% random value replacement
Label Noise: 2% label flipping
Purpose: Simulate real-world measurement errors and misclassifications
```

#### **Data Cleaning**
```python
- Drop non-numeric columns
- Fill NaN with 0
- Replace infinite values with 0
- Convert all to numeric type
```

---

## 2. OPTIMIZATION TECHNIQUES

### 2.1 Hyperparameter Optimization

#### **Random Forest (Enhanced)**
```python
n_estimators: 200 (increased from 100)
max_depth: 15 (moderate depth to prevent overfitting)
min_samples_split: 10 (increased to require more samples)
min_samples_leaf: 5 (increased to prevent overfitting)
max_features: 'sqrt' (feature subsampling)
class_weight: 'balanced' (handle class imbalance)
```

#### **XGBoost (Enhanced)**
```python
n_estimators: 200
max_depth: 8 (moderate depth)
learning_rate: 0.05 (slower learning for better generalization)
subsample: 0.8 (row subsampling)
colsample_bytree: 0.8 (column subsampling)
scale_pos_weight: Auto-calculated based on class ratio
eval_metric: 'logloss'
```

#### **Mininet PCAP Models (Regularized)**
```python
Random Forest:
  n_estimators: 50 (reduced to prevent overfitting)
  max_depth: 10 (reduced from 20)
  min_samples_split: 10 (increased from 5)
  min_samples_leaf: 4 (increased from 2)
  min_impurity_decrease: 0.001 (minimum improvement required)

XGBoost:
  n_estimators: 50
  max_depth: 6
  learning_rate: 0.03 (very slow learning)
  subsample: 0.7
  colsample_bytree: 0.7
  reg_alpha: 0.1 (L1 regularization)
  reg_lambda: 1.0 (L2 regularization)
```

### 2.2 Threshold Optimization

```python
Method: Grid search over thresholds [0.1, 0.9]
Metric: F1 Score maximization
Steps: 50 threshold values tested
Purpose: Balance precision and recall for optimal performance
```

### 2.3 Class Imbalance Handling

```python
Techniques:
  1. SMOTE (Synthetic Minority Over-sampling Technique)
     - Generates synthetic samples for minority class
     - Applied only to training set
  
  2. Class Weights
     - Random Forest: class_weight='balanced'
     - XGBoost: scale_pos_weight = N_normal / N_attack
  
  3. Stratified Sampling
     - Maintains class distribution in train/val/test splits
```

### 2.4 Cross-Validation

```python
Method: Stratified K-Fold (5 folds)
Purpose: Robust performance estimation
Scoring: F1 Score
Applied: During training phase for model validation
```

---

## 3. TRAINING PROCESS

### 3.1 Data Splitting Strategy

```python
Standard Split (60/20/20):
  - Training: 60% (model learning)
  - Validation: 20% (hyperparameter tuning, threshold optimization)
  - Test: 20% (final evaluation, never seen during training)

Stratification: Maintains class distribution across all splits
Random State: 42 (reproducibility)
```

### 3.2 Training Pipeline

#### **Step 1: Data Loading**
```
→ Load CSV files from data/ directory
→ Detect headers automatically
→ Align columns to standard format
→ Sample if dataset too large
```

#### **Step 2: Preprocessing**
```
→ Handle missing values
→ Encode categorical variables
→ Extract features and labels
→ Scale features (RobustScaler/StandardScaler)
```

#### **Step 3: Feature Engineering**
```
→ Feature selection (SelectKBest)
→ Class balancing (SMOTE)
→ Train/Val/Test split
```

#### **Step 4: Model Training**
```
→ Train Random Forest
→ Train XGBoost (if available)
→ Cross-validation for each model
→ Optimize thresholds on validation set
```

#### **Step 5: Ensemble Creation**
```
→ Voting Classifier (soft voting)
→ Combines Random Forest + XGBoost
→ Uses probability-based voting
```

#### **Step 6: Evaluation**
```
→ Test on held-out test set
→ Generate confusion matrix
→ Calculate metrics (Accuracy, Precision, Recall, F1, AUC)
→ Apply optimized thresholds
```

#### **Step 7: Model Saving**
```
→ Save individual models (.pkl)
→ Save ensemble model (.pkl)
→ Save preprocessing components (scaler, encoders, selector)
→ Save feature columns list
→ Generate training reports (JSON, HTML)
```

### 3.3 Training Metrics

#### **Primary Metrics**
```python
F1 Score: Harmonic mean of precision and recall
  - Best for imbalanced datasets
  - Range: 0-1 (higher is better)

AUC-ROC: Area under ROC curve
  - Measures classifier's ability to distinguish classes
  - Range: 0-1 (0.5 = random, 1.0 = perfect)

Precision: TP / (TP + FP)
  - Measures false positive rate
  - Important for SOC (minimize false alarms)

Recall: TP / (TP + FN)
  - Measures false negative rate
  - Important for security (catch all attacks)
```

#### **Secondary Metrics**
```python
Accuracy: (TP + TN) / Total
  - Overall correctness
  - Can be misleading with imbalanced data

Specificity: TN / (TN + FP)
  - True negative rate
  - Important for normal traffic classification
```

### 3.4 Overfitting Prevention

```python
Techniques Applied:
  1. Regularization
     - L1/L2 penalties in XGBoost
     - min_impurity_decrease in Random Forest
  
  2. Early Stopping
     - Monitor validation performance
     - Stop if no improvement
  
  3. Feature Subsampling
     - max_features='sqrt' in Random Forest
     - colsample_bytree in XGBoost
  
  4. Data Augmentation
     - Noise injection (45% Gaussian)
     - Feature corruption (8%)
     - Label noise (2%)
  
  5. Cross-Validation
     - 5-fold stratified CV
     - Detect overfitting early
  
  6. Validation Monitoring
     - Track train-val gap
     - Alert if gap > 5%
```

---

## 4. MODEL DEPLOYMENT

### 4.1 Model Loading

```python
Compatible Methods:
  - load_models(): Load from timestamp
  - Auto-detect latest models if no timestamp provided
  - Backward compatible naming (supervised_* and enhanced_*)
```

### 4.2 Real-Time Prediction

```python
predict_single(record):
  - Single record prediction
  - Returns: prediction, anomaly_score, confidence
  - Handles feature mismatches gracefully
  - Fallback to mock prediction on error

predict_batch(records):
  - Batch prediction for CSV files
  - Returns: predictions, scores, statistics
  - Memory-efficient processing
```

### 4.3 Feature Template

```python
get_feature_template():
  - Returns expected feature columns
  - Used for data generation
  - Ensures compatibility with trained models
```

---

## 5. TRAINING OUTPUTS

### 5.1 Model Files

```
models/
  ├── supervised_random_forest_YYYYMMDD_HHMMSS.pkl
  ├── supervised_xgboost_YYYYMMDD_HHMMSS.pkl
  ├── supervised_ensemble_YYYYMMDD_HHMMSS.pkl
  └── supervised_components_YYYYMMDD_HHMMSS.pkl
      ├── scaler
      ├── label_encoders
      ├── feature_selector
      ├── feature_columns
      └── feature_importance
```

### 5.2 Visualization Files

```
reports/visualizations/
  ├── class_distribution.png
  ├── data_split.png
  ├── feature_importance.png
  ├── confusion_matrix.png
  ├── roc_curve.png
  ├── precision_recall_curve.png
  └── model_comparison.png
```

### 5.3 Report Files

```
reports/
  ├── training_report_YYYYMMDD_HHMMSS.json
  ├── training_report_YYYYMMDD_HHMMSS.html
  └── training_report_YYYYMMDD_HHMMSS.pdf (if reportlab installed)
```

---

## 6. PERFORMANCE EXPECTATIONS

### 6.1 Target Metrics

```python
Production Targets (Realistic):
  - Accuracy: 93-95%
  - Precision: 90-95%
  - Recall: 88-93%
  - F1 Score: 90-94%
  - AUC: 0.95-0.98

Note: 100% accuracy indicates overfitting on synthetic data
```

### 6.2 Training Time

```python
Estimated Training Times (200K samples):
  - Data Loading: 1-2 minutes
  - Preprocessing: 2-3 minutes
  - Feature Selection: 1-2 minutes
  - SMOTE: 1-2 minutes
  - Random Forest: 3-5 minutes
  - XGBoost: 5-10 minutes
  - Ensemble: 1 minute
  - Evaluation: 1-2 minutes
  
Total: ~15-30 minutes
```

---

## 7. TROUBLESHOOTING

### 7.1 Common Issues

#### **Feature Mismatch**
```
Problem: "Feature names seen at fit time, yet now missing"
Solution: 
  - Use only common features (no zero-padding)
  - Intelligent defaults for missing features
  - Feature alignment in extract_features_only()
```

#### **Memory Issues**
```
Problem: Out of memory during training
Solution:
  - Use sample_size parameter
  - Enable chunked reading for large files
  - Reduce max_file_size_mb threshold
```

#### **Overfitting**
```
Problem: 100% training accuracy, poor test performance
Solution:
  - Add noise to synthetic data
  - Reduce model complexity (depth, trees)
  - Increase regularization
  - Use cross-validation
```

#### **Class Imbalance**
```
Problem: Model predicts only majority class
Solution:
  - Apply SMOTE
  - Use class_weight='balanced'
  - Adjust scale_pos_weight in XGBoost
  - Optimize threshold for better recall
```

---

## 8. BEST PRACTICES

### 8.1 Data Preparation
```
✓ Always check for missing values
✓ Verify label distribution
✓ Use stratified splitting
✓ Apply feature scaling
✓ Handle categorical variables properly
✓ Remove or impute infinite values
```

### 8.2 Model Training
```
✓ Use cross-validation
✓ Monitor train-val gap
✓ Optimize thresholds
✓ Save all preprocessing components
✓ Generate comprehensive reports
✓ Version control model artifacts
```

### 8.3 Model Evaluation
```
✓ Test on held-out data
✓ Use multiple metrics (not just accuracy)
✓ Analyze confusion matrix
✓ Check precision-recall trade-off
✓ Validate on real-world data
✓ Monitor false positive rate
```

---

## 9. KEY INSIGHTS

### 9.1 Why These Techniques?

**RobustScaler vs StandardScaler**
- RobustScaler uses median and IQR (robust to outliers)
- Network data often has extreme values (DDoS attacks)
- Better generalization on unseen attack patterns

**Mutual Information for Feature Selection**
- Captures non-linear relationships
- Better than correlation for security features
- Identifies complex attack patterns

**SMOTE for Class Balancing**
- Generates synthetic minority samples
- Better than simple oversampling
- Preserves feature relationships

**Threshold Optimization**
- Default 0.5 threshold may not be optimal
- Security applications need tunable precision/recall
- Reduces false positives in production

**Ensemble Methods**
- Combines strengths of multiple models
- More robust to data variations
- Better generalization

### 9.2 Production Considerations

```python
Model Selection:
  - Use ensemble for best performance
  - Use Random Forest for speed
  - Use XGBoost for accuracy

Deployment:
  - Load models once at startup
  - Cache preprocessing components
  - Batch predictions when possible
  - Monitor prediction latency

Monitoring:
  - Track prediction distribution
  - Alert on anomaly score spikes
  - Log feature mismatches
  - Retrain periodically with new data
```

---

## 10. REFERENCES

### 10.1 Training Scripts
- `src/models/supervised_trainer.py` - Base supervised learning
- `src/models/enhanced_trainer.py` - Enhanced with reporting
- `ml_training/nlp/train_from_real_alerts.py` - NLP classifier
- `scripts2/train_mininet_pcaps.py` - Mininet PCAP training
- `scripts/train_models.py` - Main training entry point

### 10.2 Key Libraries
- scikit-learn: ML algorithms and preprocessing
- XGBoost: Gradient boosting
- imbalanced-learn: SMOTE and class balancing
- pandas/numpy: Data manipulation
- matplotlib/seaborn: Visualization

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Author**: SOC Assistant Team
