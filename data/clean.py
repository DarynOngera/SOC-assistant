# clean.py
"""
Data cleaning and preprocessing module for SOC Analysis Assistant
using Microsoft Cybersecurity dataset.

Responsibilities:
- Load raw dataset(s)
- Handle missing values & duplicates
- Normalize and standardize columns
- Encode categorical features
- Save cleaned dataset for modeling
"""

import os
import argparse
import pandas as pd


class SOCDataCleaner:
    def __init__(self, input_path: str, output_path: str):
        self.input_path = input_path
        self.output_path = output_path
        self.df = None

    def load_data(self):
        """Load dataset from CSV file."""
        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Dataset not found at {self.input_path}")
        self.df = pd.read_csv(self.input_path)
        print(f"[INFO] Loaded dataset with {self.df.shape[0]} rows and {self.df.shape[1]} columns")

    def clean_data(self):
        """Perform basic cleaning: remove duplicates, handle NaN, normalize column names."""
        if self.df is None:
            raise ValueError("Data not loaded. Run load_data() first.")

        # Normalize column names
        self.df.columns = [col.strip().lower().replace(" ", "_") for col in self.df.columns]

        # Drop duplicates
        before = self.df.shape[0]
        self.df.drop_duplicates(inplace=True)
        after = self.df.shape[0]
        print(f"[INFO] Dropped {before - after} duplicate rows")

        # Handle missing values (fill NaN with "unknown" for categorical, mean for numeric)
        for col in self.df.columns:
            if self.df[col].dtype == "object":
                self.df[col] = self.df[col].fillna("unknown")
            else:
                self.df[col] = self.df[col].fillna(self.df[col].mean())

    def save_clean_data(self):
        """Save cleaned dataset to CSV."""
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        self.df.to_csv(self.output_path, index=False)
        print(f"[INFO] Cleaned dataset saved to {self.output_path}")

    def run_pipeline(self):
        """Run the entire cleaning pipeline."""
        self.load_data()
        self.clean_data()
        self.save_clean_data()


def main():
    parser = argparse.ArgumentParser(description="Clean SOC dataset")
    parser.add_argument(
        "--input",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "raw", "microsoft_incident_data.csv"),
        help="Path to raw dataset (CSV file)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "processed", "microsoft_cleaned.csv"),
        help="Path to save cleaned dataset (CSV file)"
    )

    args = parser.parse_args()

    cleaner = SOCDataCleaner(input_path=args.input, output_path=args.output)
    cleaner.run_pipeline()


if __name__ == "__main__":
    main()

