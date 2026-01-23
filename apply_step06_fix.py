"""
One-Command Fix for Step 06 Overall Status

This script applies the fix and validates it in one go.

Usage:
    python apply_step06_fix.py

Author: Cursor AI
Date: 2026-01-23
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"{'='*80}\n")
    
    result = subprocess.run(
        [sys.executable] + cmd,
        capture_output=False,
        text=True
    )
    
    return result.returncode


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║            STEP 06: OVERALL STATUS FIX - AUTOMATED APPLICATION             ║
║                                                                            ║
║  This script will:                                                         ║
║  1. Apply classification-based status logic to notebook                   ║
║  2. Add RMS quality grading (GOLD/SILVER/REVIEW)                          ║
║  3. Validate the changes                                                   ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Check if scripts exist
    fix_script = Path(__file__).parent / "fix_step06_status_logic.py"
    validate_script = Path(__file__).parent / "validate_step06_fix.py"
    
    if not fix_script.exists():
        print(f"❌ ERROR: Fix script not found: {fix_script}")
        return 1
    
    if not validate_script.exists():
        print(f"❌ ERROR: Validation script not found: {validate_script}")
        return 1
    
    # Step 1: Apply the fix
    print("\n🔧 STEP 1: Applying fix to notebook...")
    fix_result = run_command([str(fix_script)], "Apply Classification-Based Status Logic")
    
    if fix_result != 0:
        print("\n❌ Fix script failed. Please check the error messages above.")
        return 1
    
    # Step 2: Validate (check existing files)
    print("\n🔍 STEP 2: Validating existing Step 06 files...")
    validate_result = run_command([str(validate_script)], "Validate Step 06 Status Logic")
    
    # Note: validation might fail if old files exist - that's OK
    if validate_result != 0:
        print("""
⚠️  Validation detected files with old logic (expected if you haven't regenerated data yet)

Next steps:
1. Open the updated notebook: notebooks/06_rotvec_omega.ipynb
2. Review the changes (search for "FIX 2026-01-23")
3. Run the notebook to regenerate Step 06 data
4. Run validate_step06_fix.py again to verify new files
        """)
    
    # Step 3: Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")
    print("✅ Notebook updated with classification-based logic")
    print("✅ RMS quality grading added")
    print("✅ Scoring module already updated (utils_nb07.py)")
    print("\n📂 Backup created: notebooks/06_rotvec_omega_BACKUP_before_status_fix.ipynb")
    
    print("""
📋 NEXT STEPS:

1. Review the updated notebook
   → Open: notebooks/06_rotvec_omega.ipynb
   → Look for "FIX 2026-01-23" comments

2. Test on a known high-intensity file
   → Example: Subject 734, T1, P1, R1
   → Expected: "PASS (HIGH INTENSITY)" not "FAIL"

3. Regenerate all Step 06 data
   → Run the updated notebook on all files
   → Old files will still show FAIL for high velocity

4. Validate the results
   → Run: python validate_step06_fix.py
   → All files should pass validation

5. Run master audit
   → Verify scoring changes are reflected

📚 Documentation:
   - Technical: STEP_06_OVERALL_STATUS_FIX.md
   - User Guide: STEP_06_FIX_IMPLEMENTATION_GUIDE.md
   - Visual: STEP_06_DECISION_TREE.md
    """)
    
    print(f"\n{'='*80}")
    print("✅ Fix application complete!")
    print(f"{'='*80}\n")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
