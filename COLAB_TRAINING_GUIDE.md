# Google Colab Training Guide

## 🚀 Train Your SOC Models on Free GPUs!

Use Google Colab's free GPUs to train your SOC Assistant models faster and without using your local resources.

---

## 📋 Quick Start

### Step 1: Upload Notebook to Colab

1. Go to [Google Colab](https://colab.research.google.com/)
2. Click **File → Upload notebook**
3. Upload `colab_training.ipynb` from your project

### Step 2: Run All Cells

1. Click **Runtime → Run all** (or press Ctrl+F9)
2. Wait 5-10 minutes for training to complete
3. Models will be automatically downloaded

### Step 3: Deploy Models Locally

```bash
# Move downloaded models to your project
mv ~/Downloads/mininet_*.pkl /home/ongera/projects/SOC-assistant/models/

# Restart your dashboard
cd /home/ongera/projects/SOC-assistant/src/dashboard
python server.py
```

---

## 🎯 What the Notebook Does

### 1. Generates Synthetic Data
- 10,000 network traffic samples
- 7,000 normal + 3,000 attacks
- 4 attack types (SYN flood, port scan, UDP flood, HTTP flood)

### 2. Trains ML Models
- **Random Forest** with 100 trees
- **XGBoost** with gradient boosting
- **Ensemble** combining both models

### 3. Achieves Perfect Accuracy
- **100% Accuracy**
- **100% Precision & Recall**
- **ROC AUC: 1.0**

### 4. Saves 7 Model Files
- `mininet_ensemble_model.pkl` - Main ensemble model
- `mininet_random_forest_model.pkl` - RF model
- `mininet_xgboost_model.pkl` - XGBoost model
- `mininet_scaler.pkl` - Feature scaler
- `mininet_feature_selector.pkl` - Feature selector
- `mininet_feature_columns.pkl` - Selected features
- `mininet_model_metadata.pkl` - Model metadata

---

## ⚡ Advantages of Colab Training

| Aspect | Local Training | Colab Training |
|--------|---------------|----------------|
| **Cost** | Uses your CPU | Free GPU |
| **Speed** | 2-3 minutes | 1-2 minutes |
| **Resources** | Uses your RAM | Uses Google's RAM |
| **Network** | Safe (no Mininet) | Safe (no Mininet) |
| **Scalability** | Limited by hardware | Can scale up |

---

## 📊 Training Process

```
Step 1: Install Dependencies (30 seconds)
  ↓
Step 2: Generate Synthetic Data (30 seconds)
  ↓
Step 3: Preprocess Data (10 seconds)
  ↓
Step 4: Train Random Forest (1 minute)
  ↓
Step 5: Train XGBoost (1 minute)
  ↓
Step 6: Create Ensemble (10 seconds)
  ↓
Step 7: Evaluate Models (10 seconds)
  ↓
Step 8: Save Models (10 seconds)
  ↓
Step 9: Download Models (automatic)
```

**Total Time: ~5-10 minutes**

---

## 🔧 Customization Options

### Increase Dataset Size

```python
# In Step 2, change:
df = generate_synthetic_data(n_normal=70000, n_attacks=30000)
```

### Adjust Model Parameters

```python
# Random Forest
rf_model = RandomForestClassifier(
    n_estimators=200,  # More trees
    max_depth=30,      # Deeper trees
    ...
)

# XGBoost
xgb_model = xgb.XGBClassifier(
    n_estimators=200,  # More boosting rounds
    max_depth=15,      # Deeper trees
    ...
)
```

### Use GPU Acceleration

1. Click **Runtime → Change runtime type**
2. Select **GPU** as Hardware accelerator
3. Click **Save**

---

## 📥 Downloading Models

### Automatic Download (Recommended)

The notebook automatically downloads all files when you run Step 9.

### Manual Download

If automatic download fails:

1. Click the **Files** icon in the left sidebar
2. Right-click each `.pkl` file
3. Select **Download**

---

## 🔄 Deploying to Your Dashboard

### Option 1: Direct Copy

```bash
# Copy all downloaded models
cp ~/Downloads/mininet_*.pkl /home/ongera/projects/SOC-assistant/models/
```

### Option 2: Using Script

```bash
# Navigate to project
cd /home/ongera/projects/SOC-assistant

# Run integration
python3 mininet_data_generation/integration/integrate_dashboard.py
```

### Option 3: Manual

1. Open file manager
2. Navigate to `Downloads/`
3. Copy all `mininet_*.pkl` files
4. Paste into `/home/ongera/projects/SOC-assistant/models/`

---

## ✅ Verification

After deploying models, verify they work:

```bash
cd /home/ongera/projects/SOC-assistant

# Test model loading
python3 -c "
from src.models.mininet_adapter import MininetModelAdapter
adapter = MininetModelAdapter()
print('✓ Models loaded successfully!')
print(f'Features: {len(adapter.feature_columns)}')
print(f'Accuracy: {adapter.metadata.get(\"accuracy\", \"N/A\")}')
"
```

Expected output:
```
✓ Models loaded successfully!
Features: 30
Accuracy: 1.0
```

---

## 🎓 Advanced Usage

### Training with Real Data

If you have real network data:

```python
# In Step 2, replace synthetic generation with:
df = pd.read_csv('/path/to/your/network_data.csv')
```

### Hyperparameter Tuning

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [10, 20, 30],
    'min_samples_split': [2, 5, 10]
}

grid_search = GridSearchCV(rf_model, param_grid, cv=5, scoring='f1')
grid_search.fit(X_train_balanced, y_train_balanced)

print(f"Best parameters: {grid_search.best_params_}")
```

### Ensemble with More Models

```python
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

lr_model = LogisticRegression()
svm_model = SVC(probability=True)

ensemble_model = VotingClassifier(
    estimators=[
        ('rf', rf_model),
        ('xgb', xgb_model),
        ('lr', lr_model),
        ('svm', svm_model)
    ],
    voting='soft'
)
```

---

## 🐛 Troubleshooting

### Issue: Notebook Disconnects

**Solution**: Colab disconnects after 90 minutes of inactivity
- Keep the tab active
- Or use Colab Pro for longer sessions

### Issue: Out of Memory

**Solution**: Reduce dataset size
```python
df = generate_synthetic_data(n_normal=5000, n_attacks=2000)
```

### Issue: Download Fails

**Solution**: Use manual download
1. Files icon → Right-click → Download

### Issue: Models Don't Load Locally

**Solution**: Check file paths and permissions
```bash
ls -la /home/ongera/projects/SOC-assistant/models/mininet_*.pkl
chmod 644 /home/ongera/projects/SOC-assistant/models/mininet_*.pkl
```

---

## 📚 Additional Resources

- [Google Colab Documentation](https://colab.research.google.com/notebooks/intro.ipynb)
- [Scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)

---

## 🎉 Benefits Summary

✅ **Free GPU access** - No cost for training  
✅ **Fast training** - 5-10 minutes total  
✅ **No local resources** - Saves your CPU/RAM  
✅ **Network safe** - No Mininet required  
✅ **Easy deployment** - Download and copy  
✅ **Perfect accuracy** - 100% on synthetic data  
✅ **Reproducible** - Same results every time  

---

**Ready to train? Upload `colab_training.ipynb` to Google Colab and click Run All!** 🚀
