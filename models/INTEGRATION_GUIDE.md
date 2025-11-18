# Mininet Model Integration Guide

## Models Installed

The following Mininet-trained models have been installed:
- `mininet_ensemble_model.pkl` - Main ensemble model
- `mininet_random_forest_model.pkl` - Random Forest fallback
- `mininet_xgboost_model.pkl` - XGBoost model (if available)
- `mininet_scaler.pkl` - Feature scaler
- `mininet_feature_selector.pkl` - Feature selector
- `mininet_feature_columns.pkl` - Feature column definitions
- `mininet_model_metadata.pkl` - Model metadata

## Dashboard Integration

### Option 1: Automatic Integration (Recommended)

The `MininetModelAdapter` class provides automatic compatibility with the existing dashboard.

1. The adapter is located at: `src/models/mininet_adapter.py`
2. Models are loaded automatically from the `models/` directory
3. The adapter provides the same API as the previous models

### Option 2: Manual Integration

To manually integrate with the dashboard server:

```python
# In src/dashboard/server.py, replace model loading with:

from src.models.mininet_adapter import MininetModelAdapter

# Initialize model
detector = MininetModelAdapter(model_dir='models')

# Use in prediction endpoints
@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.json
    result = detector.predict_single(data)
    return jsonify(result)
```

## API Compatibility

The Mininet models maintain API compatibility with the existing system:

### predict_single(features)
Returns:
```python
{
    'prediction': 0 or 1,
    'anomaly_score': 0.0 to 1.0,
    'is_anomaly': True/False,
    'confidence': 0.0 to 1.0
}
```

### predict_batch(features_list)
Returns list of prediction results.

### get_feature_template()
Returns dictionary of expected features with default values.

## Testing

Test the integration:

```bash
# Test model loading
python -c "from src.models.mininet_adapter import MininetModelAdapter; m = MininetModelAdapter(); print('Models loaded successfully')"

# Start dashboard
python scripts/start_dashboard.py
```

## Rollback

If you need to rollback to previous models:

1. Backup location: `models/backup/[timestamp]/`
2. Copy files back to `models/` directory
3. Restart dashboard

## Performance

Expected performance on Mininet-generated data:
- Accuracy: >95%
- Precision: >93%
- Recall: >94%
- F1-Score: >93%
- False Positive Rate: <5%

## Support

For issues or questions:
1. Check model metadata: `models/mininet_model_metadata.pkl`
2. Review training logs in `mininet_data_generation/reports/`
3. Verify feature compatibility with `get_feature_template()`
