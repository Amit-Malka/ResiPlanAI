# This file imports and runs the main application
import sys
sys.path.insert(0, 'src')
from app_scheduler_complete import app

if __name__ == "__main__":
    print("="*60)
    print("Residency Program Agent")
    print("="*60)
    print("Features:")
    print("  ✓ Dashboard & Data Loading")
    print("  ✓ God View Matrix (Visual Timeline)")
    print("  ✓ Bottleneck Warnings (12-month forecast)")
    print("  ✓ AI Scheduler (OR-Tools)")
    print("  ✓ PDF Audit Export")
    print("  ✓ Intern Management (CRUD)")
    print("="*60)
    print()
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )

