#!/bin/bash
# Clean up mininet_data_generation folder for VM training-only setup
# Keeps only essential files for Mininet + model training

set -e

echo "============================================================"
echo "CLEANING MININET FOLDER FOR VM TRAINING-ONLY"
echo "============================================================"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Create backup directory
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

print_info "Creating backup in: $BACKUP_DIR"

# Files to KEEP (essential for VM training)
KEEP_FILES=(
    "setup_vm_training_only.sh"
    "vm_config.json"
    "requirements.txt"
    "README.md"
)

# Directories to KEEP (essential for VM training)
KEEP_DIRS=(
    "topology"
    "data_capture"
    "processing"
    "models"
    "integration"
    "simulation"
)

# Documentation to KEEP (minimal essential docs)
KEEP_DOCS=(
    "MINIMAL_SETUP_GUIDE.md"
    "VM_DEPLOYMENT_GUIDE.md"
)

echo ""
echo "Files and directories to keep:"
echo "Essential scripts:"
for file in "${KEEP_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file (missing)"
    fi
done

echo "Essential directories:"
for dir in "${KEEP_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir/"
    else
        echo "  ✗ $dir/ (missing)"
    fi
done

echo "Essential documentation:"
for doc in "${KEEP_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo "  ✓ $doc"
    else
        echo "  ✗ $doc (missing)"
    fi
done

echo ""
read -p "Continue with cleanup? This will move unused files to backup. (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Moving unused files to backup..."

# Move all markdown files except essential ones to backup
for file in *.md; do
    if [ -f "$file" ]; then
        keep_file=false
        for keep_doc in "${KEEP_DOCS[@]}"; do
            if [ "$file" = "$keep_doc" ]; then
                keep_file=true
                break
            fi
        done
        
        if [ "$keep_file" = false ] && [ "$file" != "README.md" ]; then
            mv "$file" "$BACKUP_DIR/"
            print_status "Moved $file to backup"
        fi
    fi
done

# Move unused setup scripts to backup
UNUSED_SCRIPTS=(
    "setup_centos_mininet.sh"
    "setup_minimal_centos.sh"
    "setup_mininet_pipeline.sh"
    "setup_vm_mininet.sh"
    "run_complete_pipeline.py"
    "run_mininet_pipeline.py"
    "run_safe_pipeline.sh"
    "run_with_system_python.sh"
    "cleanup.sh"
    "combine_pcaps.sh"
    "fix_network.sh"
    "prepare_for_colab.sh"
)

for script in "${UNUSED_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" "$BACKUP_DIR/"
        print_status "Moved $script to backup"
    fi
done

# Move unused Python files to backup
UNUSED_PYTHON=(
    "generate_synthetic_data.py"
    "test_mininet.py"
    "ensure_feature_compatibility.py"
    "validate_pipeline_integration.py"
)

for py_file in "${UNUSED_PYTHON[@]}"; do
    if [ -f "$py_file" ]; then
        mv "$py_file" "$BACKUP_DIR/"
        print_status "Moved $py_file to backup"
    fi
done

# Move unused directories to backup
UNUSED_DIRS=(
    "colab_upload"
    "reports"
)

for dir in "${UNUSED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        mv "$dir" "$BACKUP_DIR/"
        print_status "Moved $dir/ to backup"
    fi
done

# Move Jupyter notebooks to backup
for notebook in *.ipynb; do
    if [ -f "$notebook" ]; then
        mv "$notebook" "$BACKUP_DIR/"
        print_status "Moved $notebook to backup"
    fi
done

# Clean up empty directories
find . -type d -empty -delete 2>/dev/null || true

echo ""
echo "============================================================"
echo "CLEANUP COMPLETED!"
echo "============================================================"

echo ""
echo "Remaining files in mininet_data_generation/:"
echo ""

# Show current directory structure
echo "📁 Current structure:"
find . -maxdepth 2 -type f -name "*.sh" -o -name "*.py" -o -name "*.md" -o -name "*.json" | sort

echo ""
echo "📁 Directories:"
find . -maxdepth 1 -type d ! -name "." ! -name "$BACKUP_DIR" | sort

echo ""
echo "📦 Backup created: $BACKUP_DIR"
echo "   Contains all moved files for recovery if needed"

echo ""
echo "✅ VM training folder cleaned!"
echo "Ready for minimal VM training setup with:"
echo "  • Essential Mininet topology scripts"
echo "  • Data capture and processing"
echo "  • Model training capabilities"
echo "  • VM-specific setup script"

echo ""
echo "Next steps:"
echo "1. Run: ./setup_vm_training_only.sh"
echo "2. Execute VM training pipeline"
echo "3. Export models for host system"
