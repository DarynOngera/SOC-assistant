#!/usr/bin/env python3
"""
Data Utilities
Common data processing functions for SOC assistant
"""

import os
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional

def load_csv_files(data_path: str, sample_size: Optional[int] = None, max_file_size_mb: int = 100) -> pd.DataFrame:
    """
    Memory-efficient CSV loading with chunked reading for large files
    
    Args:
        data_path: Path to CSV file or directory containing CSV files
        sample_size: Optional limit on number of rows to load
        max_file_size_mb: Maximum file size before using chunked reading
        
    Returns:
        Combined DataFrame from all CSV files
    """
    import glob
    
    if os.path.isfile(data_path):
        csv_files = [data_path]
    else:
        csv_files = glob.glob(os.path.join(data_path, "*.csv"))
        
    if not csv_files:
        raise ValueError(f"No CSV files found in {data_path}")
        
    print(f"Found {len(csv_files)} CSV file(s)")
    dataframes = []
    
    for i, file_path in enumerate(csv_files):
        print(f"Loading file {i+1}/{len(csv_files)}: {os.path.basename(file_path)}")
        
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        
        if file_size_mb > max_file_size_mb:
            print(f"Large file detected ({file_size_mb:.1f}MB). Using chunked reading...")
            chunks = []
            chunk_size = 10000
            
            for chunk in pd.read_csv(file_path, chunksize=chunk_size):
                chunks.append(chunk)
                if sample_size and len(pd.concat(chunks)) >= sample_size:
                    break
                    
            df = pd.concat(chunks, ignore_index=True)
        else:
            df = pd.read_csv(file_path)
            
        if sample_size and len(df) > sample_size:
            df = df.sample(n=sample_size, random_state=42)
            print(f"Sampled {sample_size} rows from {len(df)} total")
            
        dataframes.append(df)
        
    combined_df = pd.concat(dataframes, ignore_index=True)
    print(f"Combined dataset shape: {combined_df.shape}")
    
    # Memory cleanup
    del dataframes
    
    return combined_df

def validate_network_features(data: Dict[str, Any]) -> bool:
    """
    Validate that network traffic data contains required features
    
    Args:
        data: Dictionary containing network traffic features
        
    Returns:
        True if data is valid, False otherwise
    """
    required_features = ['dur', 'proto', 'spkts', 'dpkts', 'sbytes', 'dbytes']
    
    for feature in required_features:
        if feature not in data:
            return False
            
    return True

def normalize_protocol_names(proto: str) -> str:
    """
    Normalize protocol names to standard format
    
    Args:
        proto: Protocol name (e.g., 'TCP', 'tcp', 'Tcp')
        
    Returns:
        Normalized protocol name in lowercase
    """
    return str(proto).lower().strip()

def calculate_flow_features(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate additional flow-based features from basic network data
    
    Args:
        record: Network traffic record
        
    Returns:
        Record with additional calculated features
    """
    enhanced_record = record.copy()
    
    # Calculate rates if duration is available
    if 'dur' in record and record['dur'] > 0:
        if 'sbytes' in record:
            enhanced_record['sbytes_rate'] = record['sbytes'] / record['dur']
        if 'dbytes' in record:
            enhanced_record['dbytes_rate'] = record['dbytes'] / record['dur']
        if 'spkts' in record:
            enhanced_record['spkts_rate'] = record['spkts'] / record['dur']
        if 'dpkts' in record:
            enhanced_record['dpkts_rate'] = record['dpkts'] / record['dur']
    
    # Calculate packet size averages
    if 'sbytes' in record and 'spkts' in record and record['spkts'] > 0:
        enhanced_record['avg_spkt_size'] = record['sbytes'] / record['spkts']
    if 'dbytes' in record and 'dpkts' in record and record['dpkts'] > 0:
        enhanced_record['avg_dpkt_size'] = record['dbytes'] / record['dpkts']
    
    return enhanced_record
