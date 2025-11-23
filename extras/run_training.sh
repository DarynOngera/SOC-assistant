#!/bin/bash
# Wrapper script to run training in virtual environment

cd /home/ongera/projects/SOC-assistant

# Activate virtual environment
source venv/bin/activate

# Run training
python3 train_comprehensive_model.py

# Deactivate
deactivate
