#!/usr/bin/env python3
"""
Model Training Script
Simplified script to train SOC anomaly detection models
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Main training function"""
    print("="*60)
    print("SOC ANOMALY DETECTION - MODEL TRAINING")
    print("="*60)
    
    # Change to project root directory
    os.chdir(project_root)
    print(f"Working directory: {os.getcwd()}")
    
    # Check for required directories
    data_dir = Path("data")
    test_dir = Path("test")
    models_dir = Path("models")
    
    if not data_dir.exists():
        print(f"✗ Data directory not found: {data_dir}")
        print("Please ensure training data is available in the 'data/' directory")
        return False
    
    if not test_dir.exists():
        print(f"✗ Test directory not found: {test_dir}")
        print("Please ensure test data is available in the 'test/' directory")
        return False
    
    # Create models directory if it doesn't exist
    if not models_dir.exists():
        models_dir.mkdir()
        print(f"✓ Created models directory: {models_dir}")
    
    # Import and run training
    try:
        from src.models.supervised_trainer import SupervisedSOCDetector, main as train_main
        
        print("✓ Starting model training pipeline...")
        train_main()
        print("\n✓ Model training completed successfully!")
        
        # Verify model files were created
        model_files = list(models_dir.glob("*.pkl")) + list(models_dir.glob("*.h5"))
        if model_files:
            print(f"✓ Generated {len(model_files)} model files:")
            for model_file in model_files:
                print(f"  - {model_file.name}")
        else:
            print("⚠ Warning: No model files found after training")
            
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Please ensure all dependencies are installed: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"✗ Model training failed: {e}")
        print("Check the error above and ensure data files are in the correct format")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Training script completed successfully!")
        print("You can now start the dashboard with: python scripts/start_dashboard.py")
    else:
        print("\n❌ Training script failed!")
    sys.exit(0 if success else 1)
