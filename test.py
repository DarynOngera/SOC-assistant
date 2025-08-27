import pandas as pd
import os

# Check what CSV files are available
data_dir = "data/"  # Adjust path as needed
if os.path.exists(data_dir):
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    print("Available CSV files:")
    for file in csv_files:
        print(f"  - {file}")
else:
    print("Data directory not found. Looking for CSV files in current directory...")
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    for file in csv_files:
        print(f"  - {file}")

# Check the most likely dataset file
dataset_files = ['network_traffic.csv', 'data.csv', 'dataset.csv', 'train.csv']
found_file = None

for filename in dataset_files:
    full_path = os.path.join(data_dir, filename) if os.path.exists(data_dir) else filename
    if os.path.exists(full_path):
        found_file = full_path
        break

if found_file:
    print(f"\nInspecting: {found_file}")
    df = pd.read_csv(found_file)
    
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print("\nFirst few rows:")
    print(df.head())
    
    # Check for potential label columns
    potential_labels = [col for col in df.columns if 'label' in col.lower() or 'class' in col.lower() or 'target' in col.lower()]
    if potential_labels:
        print(f"\nPotential label columns found: {potential_labels}")
        for col in potential_labels:
            print(f"{col} unique values: {df[col].unique()}")
    else:
        print("\nNo obvious label column found. All columns:")
        for col in df.columns:
            unique_vals = df[col].nunique()
            print(f"  {col}: {unique_vals} unique values")
            if unique_vals <= 10:  # Show unique values for categorical columns
                print(f"    Values: {list(df[col].unique())}")
else:
    print("No dataset file found. Please check your file path.")
