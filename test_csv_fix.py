#!/usr/bin/env python3
"""
Quick test to verify CSV upload path handling fix
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append('.')

from src.utils.csv_processor import CSVProcessor

def test_path_handling():
    """Test that Path objects work correctly with file operations"""
    try:
        # Initialize CSV processor
        processor = CSVProcessor(
            detector=None,
            upload_dir="test_uploads",
            reports_dir="test_reports"
        )
        
        print(f"Upload dir type: {type(processor.upload_dir)}")
        print(f"Upload dir path: {processor.upload_dir}")
        
        # Test Path operations
        test_filename = "test_file.csv"
        file_path = str(processor.upload_dir / test_filename)
        print(f"Generated file path: {file_path}")
        
        # Test directory creation
        processor.upload_dir.mkdir(parents=True, exist_ok=True)
        print(f"Directory exists: {processor.upload_dir.exists()}")
        
        # Cleanup
        if processor.upload_dir.exists():
            import shutil
            shutil.rmtree(processor.upload_dir)
        if processor.reports_dir.exists():
            import shutil
            shutil.rmtree(processor.reports_dir)
        
        print("✅ Path handling test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Path handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_path_handling()
