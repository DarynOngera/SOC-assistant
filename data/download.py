# data/clean.py
import os
import pandas as pd

class DataCleaner:
    def __init__(self, input_filename="microsoft_incident_data.csv"):
        # Get the absolute path to this script's directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Point to raw and processed subfolders
        self.input_path = os.path.join(base_dir, "raw", input_filename)
        self.output_path = os.path.join(base_dir, "processed", "microsoft_incident_data_cleaned.csv")
        
        # Will hold the DataFrame
        self.df = None

    def load_data(self):
        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Dataset not found at {self.input_path}")
        self.df = pd.read_csv(self.input_path)
        print(f"✅ Loaded dataset with {self.df.shape[0]} rows, {self.df.shape[1]} columns")

    def clean_data(self):
        # Example cleaning steps
        self.df.dropna(inplace=True)
        self.df.drop_duplicates(inplace=True)
        print(f"🧹 Cleaned dataset now has {self.df.shape[0]} rows")

    def save_data(self):
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        self.df.to_csv(self.output_path, index=False)
        print(f"💾 Saved cleaned dataset to {self.output_path}")

    def run_pipeline(self):
        self.load_data()
        self.clean_data()
        self.save_data()

if __name__ == "__main__":
    cleaner = DataCleaner()
    cleaner.run_pipeline()

