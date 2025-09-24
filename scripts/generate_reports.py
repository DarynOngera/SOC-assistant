#!/usr/bin/env python3
"""
Generate Comprehensive Training Reports
Creates PDF and visualized reports from existing training data
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Generate comprehensive reports from latest training data"""
    print("="*60)
    print("REPORT GENERATOR")
    print("="*60)
    
    # Change to project root
    os.chdir(project_root)
    
    # Find latest JSON report
    reports_dir = Path("reports")
    if not reports_dir.exists():
        print("✗ No reports directory found")
        print("Please run model training first: python scripts/train_models.py")
        return False
    
    # Find latest JSON report
    json_reports = list(reports_dir.glob("training_report_*.json"))
    if not json_reports:
        print("✗ No training reports found")
        print("Please run model training first: python scripts/train_models.py")
        return False
    
    latest_report = max(json_reports, key=lambda x: x.stat().st_mtime)
    print(f"✓ Found latest report: {latest_report.name}")
    
    try:
        from src.utils.report_generator import generate_comprehensive_reports
        
        print("\n📊 Generating comprehensive reports...")
        results = generate_comprehensive_reports(str(latest_report))
        
        print("\n✓ Report generation completed!")
        print("\nGenerated files:")
        
        # List visualization files
        if 'visualizations' in results:
            print("\n📈 Visualizations:")
            for plot_name, plot_path in results['visualizations'].items():
                if os.path.exists(plot_path):
                    print(f"  - {plot_name.replace('_', ' ').title()}: {plot_path}")
        
        # PDF report
        if results.get('pdf_report'):
            print(f"\n📄 PDF Report: {results['pdf_report']}")
        else:
            print("\n⚠ PDF report not generated (install reportlab: pip install reportlab)")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Please ensure all dependencies are installed")
        return False
    except Exception as e:
        print(f"✗ Report generation failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Report generation completed successfully!")
    else:
        print("\n❌ Report generation failed!")
    sys.exit(0 if success else 1)
