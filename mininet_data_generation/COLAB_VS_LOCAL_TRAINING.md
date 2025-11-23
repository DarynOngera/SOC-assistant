# Colab vs Local Training Comparison

## Overview

We've adapted the comprehensive training structure from `extras/colab_training_v2.ipynb` for local Mininet PCAP training.

## Side-by-Side Comparison

### Training Pipeline

| Step | Colab Notebook | Local Script |
|------|---------------|--------------|
| **1. Dependencies** | `!pip install packages` | Pre-installed via requirements.txt |
| **2. Data Upload** | Manual file upload widget | Command-line argument |
| **3. Data Loading** | `pd.read_csv(uploaded_file)` | `pd.read_csv(csv_path)` |
| **4. Preprocessing** | Interactive cells | Automated pipeline |
| **5. Visualization** | Inline matplotlib display | Saved to `visualizations/` folder |
| **6. Training** | Cell-by-cell execution | Single command execution |
| **7. Evaluation** | Interactive metrics display | Printed + saved reports |
| **8. Model Saving** | Manual joblib.dump | Automated to `models/` folder |
| **9. Downloads** | `files.download()` widget | Already on local filesystem |

### Features Comparison

| Feature | Colab | Local |
|---------|-------|-------|
| **GPU Support** | ✅ Free GPU (T4/P100) | ❌ CPU only |
| **Automation** | ❌ Manual cell execution | ✅ Single command |
| **Data Upload** | ❌ Manual upload | ✅ File path |
| **Reproducibility** | ⚠️ Requires re-running cells | ✅ Scripted pipeline |
| **Integration** | ❌ Manual model download | ✅ Direct to models/ |
| **Scheduling** | ❌ Manual only | ✅ Can be automated |
| **Cost** | ✅ Free (with limits) | ✅ Free (local compute) |
| **Internet Required** | ✅ Yes | ❌ No |

### Code Structure Mapping

#### Colab Notebook → Local Script

```python
# COLAB: Cell 4 - Upload data
uploaded = files.upload()
csv_file = list(uploaded.keys())[0]
df = pd.read_csv(csv_file)

# LOCAL: Constructor + load_data()
trainer = MininetPCAPTrainer(csv_path)
trainer.load_data()
```

```python
# COLAB: Cell 7 - Preprocessing
X = df.drop(['label', 'attack_type'], axis=1, errors='ignore')
y = df['label']
X = X.fillna(0).replace([np.inf, -np.inf], 0)

# LOCAL: preprocess_data()
trainer.preprocess_data()
# Same logic, encapsulated in method
```

```python
# COLAB: Cell 15 - Train Random Forest
rf_model = RandomForestClassifier(...)
rf_model.fit(X_train_balanced, y_train_balanced)

# LOCAL: train_models()
models = trainer.train_models(X_train_bal, y_train_bal, X_val, y_val)
# Returns dict with all models
```

```python
# COLAB: Cell 29 - Save models
joblib.dump(ensemble_model, 'mininet_ensemble_model.pkl')
joblib.dump(rf_model, 'mininet_random_forest_model.pkl')
# ... manual saves

# LOCAL: save_models()
trainer.save_models(models, scaler, selector)
# Automated saving of all artifacts
```

```python
# COLAB: Cell 31 - Download
files.download('mininet_ensemble_model.pkl')
files.download('training_report.json')
# ... manual downloads

# LOCAL: Already saved locally
# No download needed, files in training_output/
```

## Usage Comparison

### Colab Workflow

```bash
# 1. Open notebook in browser
https://colab.research.google.com

# 2. Upload notebook
Upload: extras/colab_training_v2.ipynb

# 3. Run cells manually
Click "Runtime" → "Run all"

# 4. Upload CSV when prompted
Click upload button, select file

# 5. Wait for training
Monitor cell outputs

# 6. Download results
Click download for each file
```

### Local Workflow

```bash
# 1. Single command
cd /home/ongera/projects/SOC-assistant
python3 scripts2/train_mininet_pcaps.py \
    mininet_data_generation/data_capture/processed/dataset.csv \
    --output training_output

# 2. Results automatically saved
ls training_output/
# models/  visualizations/  reports/

# 3. Deploy to dashboard
cp training_output/models/* models/
python3 src/dashboard/server.py
```

### Complete Pipeline (Local Only)

```bash
# One script does everything
cd mininet_data_generation
bash train_from_pcaps.sh

# Automatically:
# 1. Checks for PCAPs
# 2. Processes to CSV
# 3. Trains models
# 4. Saves everything
# 5. Shows deployment instructions
```

## Output Comparison

### Colab Outputs

```
extras/colab_training_v2.ipynb generates:

Downloaded Files:
├── mininet_ensemble_model.pkl
├── mininet_random_forest_model.pkl
├── mininet_xgboost_model.pkl
├── mininet_scaler.pkl
├── mininet_feature_selector.pkl
├── mininet_feature_columns.pkl
├── mininet_model_metadata.pkl
├── training_report.json
├── training_report.html
├── class_distribution.png
├── data_split.png
├── feature_importance.png
├── smote_balancing.png
├── confusion_matrices.png
├── roc_curves.png
├── precision_recall_curves.png
├── model_comparison.png
└── attack_type_performance.png
```

### Local Outputs

```
training_output/
├── models/
│   ├── mininet_ensemble_model.pkl
│   ├── mininet_random_forest_model.pkl
│   ├── mininet_xgboost_model.pkl
│   ├── mininet_scaler.pkl
│   ├── mininet_feature_selector.pkl
│   ├── mininet_feature_columns.pkl
│   └── mininet_model_metadata.pkl
├── visualizations/
│   ├── class_distribution.png
│   ├── data_split.png
│   ├── feature_importance.png
│   ├── confusion_matrices.png
│   └── roc_curves.png
└── reports/
    └── training_report.json
```

## When to Use Each

### Use Colab When:
- ✅ Need GPU acceleration
- ✅ Don't have local Python environment
- ✅ Want interactive exploration
- ✅ Sharing with non-technical users
- ✅ Quick experiments

### Use Local Script When:
- ✅ Automating training pipeline
- ✅ Integrating with CI/CD
- ✅ Training on production data
- ✅ No internet connection
- ✅ Deploying directly to dashboard
- ✅ Scheduling regular retraining

## Migration Path

### From Colab to Local

1. **Download models from Colab**
   ```python
   # In Colab, after training
   files.download('mininet_ensemble_model.pkl')
   # ... download all .pkl files
   ```

2. **Upload to local**
   ```bash
   # On local machine
   cp ~/Downloads/*.pkl /home/ongera/projects/SOC-assistant/models/
   ```

3. **Use in dashboard**
   ```bash
   python3 src/dashboard/server.py
   # Automatically loads models/
   ```

### From Local to Colab

1. **Export CSV**
   ```bash
   # Create CSV from PCAPs
   python3 scripts2/process_mininet_pcaps.py
   ```

2. **Upload to Colab**
   ```python
   # In Colab notebook
   uploaded = files.upload()
   # Select the CSV file
   ```

3. **Train in Colab**
   ```python
   # Run all cells
   # Download results
   ```

## Best Practice: Hybrid Approach

### Development Phase
- Use **Colab** for experimentation
- Try different hyperparameters
- Visualize results interactively

### Production Phase
- Use **Local Script** for automation
- Schedule regular retraining
- Direct integration with dashboard

### Example Workflow

```bash
# 1. Experiment in Colab
# - Try different features
# - Tune hyperparameters
# - Find best model

# 2. Implement in local script
# - Add best parameters
# - Automate pipeline
# - Integrate with system

# 3. Deploy and monitor
# - Run local training
# - Deploy to dashboard
# - Monitor performance

# 4. Retrain as needed
# - Automated via cron
# - Or manual when needed
```

## Summary

| Aspect | Colab | Local |
|--------|-------|-------|
| **Best For** | Experimentation | Production |
| **Speed** | GPU-accelerated | CPU-based |
| **Ease** | Interactive | Automated |
| **Integration** | Manual | Direct |
| **Cost** | Free (limited) | Free (unlimited) |
| **Reliability** | Internet-dependent | Offline-capable |

**Both approaches use the same comprehensive training structure from `colab_training_v2.ipynb`!** 🎯
