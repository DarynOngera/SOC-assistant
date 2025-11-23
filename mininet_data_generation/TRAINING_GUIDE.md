# Mininet PCAP Training Guide

## Overview
Train ML models using Mininet-generated PCAP data with the same comprehensive structure as `colab_training_v2.ipynb`.

## Quick Start

### 1. Generate PCAPs (if not done)
```bash
cd /home/ongera/projects/SOC-assistant/mininet_data_generation
sudo bash generate_pcaps_centos.sh
```

### 2. Process PCAPs to CSV
```bash
# Process all PCAPs into a single CSV
cd /home/ongera/projects/SOC-assistant
python3 scripts2/process_mininet_pcaps.py
```

This will create: `mininet_data_generation/data_capture/processed/mininet_dataset_YYYYMMDD_HHMMSS.csv`

### 3. Train Models
```bash
# Using the training script
python3 scripts2/train_mininet_pcaps.py \
    mininet_data_generation/data_capture/processed/mininet_dataset_*.csv \
    --output training_output
```

## What Gets Generated

### Models (in `training_output/models/`)
1. **mininet_random_forest_model.pkl** - Random Forest classifier
2. **mininet_xgboost_model.pkl** - XGBoost classifier (if available)
3. **mininet_ensemble_model.pkl** - Voting ensemble
4. **mininet_scaler.pkl** - Feature scaler
5. **mininet_feature_selector.pkl** - Feature selector
6. **mininet_feature_columns.pkl** - Selected feature names
7. **mininet_model_metadata.pkl** - Training metadata

### Visualizations (in `training_output/visualizations/`)
1. **class_distribution.png** - Normal vs Attack distribution
2. **data_split.png** - Train/Val/Test split visualization
3. **feature_importance.png** - Top 20 feature importance
4. **confusion_matrices.png** - Confusion matrices for all models
5. **roc_curves.png** - ROC curves comparison

### Reports (in `training_output/reports/`)
1. **training_report.json** - Comprehensive JSON report

## Training Pipeline

The script follows the same structure as `colab_training_v2.ipynb`:

### Step 1: Load Data
- Loads CSV from PCAP processing
- Analyzes class distribution
- Checks for attack types

### Step 2: Preprocess
- Separates features and labels
- Handles missing/infinite values
- Removes non-numeric columns

### Step 3: Split Data
- 60% training
- 20% validation
- 20% test
- Stratified splitting

### Step 4: Feature Engineering
- StandardScaler normalization
- SelectKBest feature selection (top 30)
- Mutual information scoring

### Step 5: Balance Classes
- SMOTE oversampling
- Balances normal/attack ratio

### Step 6: Train Models
- **Random Forest**: 100 trees, max_depth=20
- **XGBoost**: 100 estimators, learning_rate=0.1
- **Ensemble**: Soft voting of RF + XGBoost

### Step 7: Evaluate
- Accuracy, Precision, Recall, F1, ROC AUC
- Confusion matrices
- ROC curves
- Model comparison

### Step 8: Save Everything
- All models and artifacts
- Visualizations
- JSON report

## Expected Performance

With good Mininet PCAP data:
- **Accuracy**: 95-99%
- **Precision**: 90-98%
- **Recall**: 90-98%
- **F1-Score**: 92-98%
- **ROC AUC**: 95-99%

## Using Trained Models

### Copy to Models Directory
```bash
cp training_output/models/* /home/ongera/projects/SOC-assistant/models/
```

### Update Dashboard
The dashboard will automatically detect and load the new models:
```bash
cd /home/ongera/projects/SOC-assistant
python3 src/dashboard/server.py
```

## Comparison: Colab vs Local Training

| Feature | Colab Notebook | Local Script |
|---------|---------------|--------------|
| Data Upload | Manual upload | File path argument |
| Dependencies | `!pip install` | Pre-installed |
| Visualizations | Inline display | Saved to disk |
| Downloads | Manual download | Auto-saved |
| GPU Support | Yes (optional) | CPU only |
| Automation | Manual cells | Single command |

## Advanced Usage

### Custom Output Directory
```bash
python3 scripts2/train_mininet_pcaps.py \
    data.csv \
    --output my_training_results
```

### Process Specific PCAPs
```bash
# Only SYN flood
python3 scripts2/process_mininet_pcaps.py \
    --pcap mininet_data_generation/data_capture/mininet/syn_flood.pcap \
    --output syn_flood_dataset.csv

# Train on it
python3 scripts2/train_mininet_pcaps.py \
    syn_flood_dataset.csv \
    --output syn_flood_training
```

## Troubleshooting

### Issue: "XGBoost not installed"
```bash
pip3 install xgboost
```
Script will still work with Random Forest only.

### Issue: "Not enough samples"
Generate more PCAPs:
```bash
cd mininet_data_generation/topology
sudo python3 generate_syn_flood_centos.py --samples 5000
```

### Issue: "Imbalanced classes"
The script automatically applies SMOTE, but you can generate more attack samples:
```bash
# Generate more varied attacks
sudo bash generate_pcaps_centos.sh
```

### Issue: "Low accuracy"
1. Check PCAP quality: `tcpdump -r file.pcap -c 10`
2. Verify IPv4 traffic: `tcpdump -r file.pcap ip -c 10`
3. Increase samples: `--samples 10000`
4. Check feature extraction in processing script

## Integration with Dashboard

After training, the models integrate seamlessly:

1. **Copy models**: `cp training_output/models/* models/`
2. **Restart server**: `python3 src/dashboard/server.py`
3. **Dashboard loads**: Automatically detects new models
4. **Real-time detection**: Uses trained models for alerts

## Next Steps

1. ✅ Generate PCAPs with Mininet
2. ✅ Process to CSV
3. ✅ Train models
4. ✅ Evaluate performance
5. ✅ Deploy to dashboard
6. ✅ Monitor real-time detection

**Your Mininet PCAP data is now powering ML-based threat detection!** 🎯
