import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from sklearn.preprocessing import StandardScaler, LabelEncoder
import pickle

def create_sample_cert_data():
    """Create sample CERT-like insider threat data for development"""
    np.random.seed(42)
    
    # Generate sample data that mimics CERT insider threat dataset
    n_samples = 1000
    
    data = {
        'date': pd.date_range('2024-01-01', periods=n_samples, freq='H'),
        'user': np.random.choice(['alice.smith', 'bob.jones', 'charlie.brown', 'diana.wilson', 'eve.davis'], n_samples),
        'pc': np.random.choice(['PC-001', 'PC-002', 'PC-003', 'PC-004', 'PC-005'], n_samples),
        'activity': np.random.choice(['Logon', 'Logoff', 'Connect', 'Disconnect', 'Copy', 'Write'], n_samples),
        'file': np.random.choice(['document.pdf', 'data.xlsx', 'report.docx', 'config.txt', 'database.db'], n_samples),
        'from_removable': np.random.choice([True, False], n_samples, p=[0.1, 0.9]),
        'to_removable': np.random.choice([True, False], n_samples, p=[0.1, 0.9]),
        'content': np.random.choice(['Confidential', 'Public', 'Internal', 'Restricted'], n_samples),
        'size': np.random.exponential(1000, n_samples).astype(int),
        'anomaly_label': np.random.choice([0, 1], n_samples, p=[0.95, 0.05])  # 5% anomalies
    }
    
    df = pd.DataFrame(data)
    
    # Add some realistic patterns for anomalies
    anomaly_indices = df[df['anomaly_label'] == 1].index
    df.loc[anomaly_indices, 'size'] = np.random.exponential(10000, len(anomaly_indices)).astype(int)
    df.loc[anomaly_indices, 'from_removable'] = True
    df.loc[anomaly_indices, 'content'] = 'Confidential'
    
    return df

def clean_data(df):
    """Clean and preprocess the dataset"""
    print("Starting data cleaning...")
    
    # Handle missing values
    df = df.dropna()
    
    # Remove duplicates
    initial_rows = len(df)
    df = df.drop_duplicates()
    print(f"Removed {initial_rows - len(df)} duplicate rows")
    
    # Convert date to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # Feature engineering
    df['hour'] = df['date'].dt.hour
    df['day_of_week'] = df['date'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['is_after_hours'] = ((df['hour'] < 8) | (df['hour'] > 18)).astype(int)
    
    print(f"Cleaned dataset shape: {df.shape}")
    return df

def encode_features(df):
    """Encode categorical features for ML models"""
    print("Encoding categorical features...")
    
    # Create a copy for encoding
    df_encoded = df.copy()
    
    # Label encode categorical columns
    categorical_cols = ['user', 'pc', 'activity', 'file', 'content']
    encoders = {}
    
    for col in categorical_cols:
        le = LabelEncoder()
        df_encoded[f'{col}_encoded'] = le.fit_transform(df_encoded[col])
        encoders[col] = le
    
    # One-hot encode boolean columns
    df_encoded['from_removable'] = df_encoded['from_removable'].astype(int)
    df_encoded['to_removable'] = df_encoded['to_removable'].astype(int)
    
    return df_encoded, encoders

def create_sequences(df, user_col='user', window_size=10):
    """Create sequential data for LSTM training"""
    print(f"Creating sequences with window size {window_size}...")
    
    # Features for sequence modeling
    feature_cols = [
        'user_encoded', 'pc_encoded', 'activity_encoded', 'file_encoded', 
        'content_encoded', 'from_removable', 'to_removable', 'size',
        'hour', 'day_of_week', 'is_weekend', 'is_after_hours'
    ]
    
    sequences = []
    labels = []
    
    # Group by user and create sequences
    for user in df[user_col].unique():
        user_data = df[df[user_col] == user].sort_values('date')
        
        if len(user_data) < window_size:
            continue
            
        for i in range(len(user_data) - window_size + 1):
            sequence = user_data[feature_cols].iloc[i:i+window_size].values
            label = user_data['anomaly_label'].iloc[i+window_size-1]
            
            sequences.append(sequence)
            labels.append(label)
    
    sequences = np.array(sequences)
    labels = np.array(labels)
    
    print(f"Created {len(sequences)} sequences of shape {sequences.shape}")
    return sequences, labels

def normalize_features(sequences):
    """Normalize sequence features"""
    print("Normalizing features...")
    
    # Reshape for normalization
    n_samples, n_timesteps, n_features = sequences.shape
    sequences_reshaped = sequences.reshape(-1, n_features)
    
    # Fit scaler
    scaler = StandardScaler()
    sequences_normalized = scaler.fit_transform(sequences_reshaped)
    
    # Reshape back
    sequences_normalized = sequences_normalized.reshape(n_samples, n_timesteps, n_features)
    
    return sequences_normalized, scaler

def save_processed_data(sequences, labels, scaler, encoders, output_dir='data/processed'):
    """Save processed data and preprocessing objects"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Save sequences and labels
    np.save(os.path.join(output_dir, 'sequences.npy'), sequences)
    np.save(os.path.join(output_dir, 'labels.npy'), labels)
    
    # Save preprocessing objects
    with open(os.path.join(output_dir, 'scaler.pkl'), 'wb') as f:
        pickle.dump(scaler, f)
    
    with open(os.path.join(output_dir, 'encoders.pkl'), 'wb') as f:
        pickle.dump(encoders, f)
    
    # Save metadata
    metadata = {
        'n_samples': len(sequences),
        'sequence_length': sequences.shape[1],
        'n_features': sequences.shape[2],
        'n_anomalies': int(labels.sum()),
        'anomaly_rate': float(labels.mean()),
        'processed_date': datetime.now().isoformat()
    }
    
    with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Saved processed data to {output_dir}")
    return metadata

def generate_sample_alerts(df, n_alerts=10):
    """Generate sample alerts for UI testing"""
    # Get recent anomalies
    anomalies = df[df['anomaly_label'] == 1].tail(n_alerts)
    
    alerts = []
    for idx, row in anomalies.iterrows():
        alert = {
            'id': int(idx),
            'timestamp': row['date'].strftime('%Y-%m-%d %H:%M:%S'),
            'alert': f"Suspicious {row['activity'].lower()} activity by {row['user']} on {row['pc']}",
            'severity': 'High' if row['size'] > 5000 else 'Medium',
            'anomaly_score': np.random.uniform(0.7, 0.95),
            'source_ip': f"192.168.{np.random.randint(1,255)}.{np.random.randint(1,255)}",
            'user': row['user'],
            'status': 'active'
        }
        alerts.append(alert)
    
    # Save alerts for UI
    os.makedirs('output', exist_ok=True)
    with open('output/alerts.json', 'w') as f:
        json.dump(alerts, f, indent=2)
    
    print(f"Generated {len(alerts)} sample alerts")
    return alerts

def main():
    """Main data processing pipeline"""
    print("=" * 50)
    print("SOC Assistant Data Processing Pipeline")
    print("=" * 50)
    
    # Check if raw data exists, otherwise create sample data
    raw_data_path = 'data/raw'
    if not os.path.exists(raw_data_path) or not os.listdir(raw_data_path):
        print("No raw data found. Creating sample CERT-like dataset...")
        df = create_sample_cert_data()
        
        # Save sample data
        os.makedirs(raw_data_path, exist_ok=True)
        df.to_csv(os.path.join(raw_data_path, 'sample_cert_data.csv'), index=False)
        print("Sample data created and saved")
    else:
        print("Loading existing raw data...")
        # Try to load existing data
        csv_files = [f for f in os.listdir(raw_data_path) if f.endswith('.csv')]
        if csv_files:
            df = pd.read_csv(os.path.join(raw_data_path, csv_files[0]))
        else:
            print("No CSV files found. Creating sample data...")
            df = create_sample_cert_data()
    
    # Process the data
    df_clean = clean_data(df)
    df_encoded, encoders = encode_features(df_clean)
    sequences, labels = create_sequences(df_encoded)
    sequences_normalized, scaler = normalize_features(sequences)
    
    # Save processed data
    metadata = save_processed_data(sequences_normalized, labels, scaler, encoders)
    
    # Generate sample alerts for UI
    alerts = generate_sample_alerts(df_clean)
    
    print("\n" + "=" * 50)
    print("Data Processing Complete!")
    print("=" * 50)
    print(f"Processed {metadata['n_samples']} sequences")
    print(f"Anomaly rate: {metadata['anomaly_rate']:.2%}")
    print(f"Sequence shape: ({metadata['sequence_length']}, {metadata['n_features']})")
    print(f"Generated {len(alerts)} alerts for UI")
    
    return df_clean, sequences_normalized, labels, metadata

if __name__ == "__main__":
    main()