"""
Validate Step 06 Overall Status Fix

This script validates that the classification-based status logic is working correctly.

Usage:
    python validate_step06_fix.py [derivatives_path]

What it checks:
    1. overall_status values match classification logic
    2. Artifact rate thresholds are correctly applied
    3. RMS quality grading is present and correct
    4. High-intensity files show "PASS (HIGH INTENSITY)" not "FAIL"

Author: Cursor AI
Date: 2026-01-23
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def load_step06_summary(summary_path: Path) -> Dict:
    """Load Step 06 kinematics summary JSON."""
    with open(summary_path, 'r') as f:
        return json.load(f)


def validate_status_logic(summary: Dict, run_id: str) -> Tuple[bool, List[str]]:
    """
    Validate that overall_status matches the classification logic.
    
    Returns:
        (is_valid, issues_list)
    """
    issues = []
    
    # Extract relevant fields
    overall_status = summary.get('overall_status', 'UNKNOWN')
    status_reason = summary.get('overall_status_reason', '')
    
    # Get artifact rate from Gate 5
    artifact_rate = 0.0
    if 'step_06_burst_analysis' in summary:
        frame_stats = summary.get('step_06_burst_analysis', {}).get('frame_statistics', {})
        artifact_rate = frame_stats.get('artifact_rate_percent', 0.0)
    
    # Get burst decision
    burst_decision = 'PASS'
    if 'step_06_burst_decision' in summary:
        burst_decision = summary.get('step_06_burst_decision', {}).get('overall_status', 'PASS')
    
    # Get biomechanical metrics
    metrics = summary.get('metrics', {})
    max_ang_vel = metrics.get('angular_velocity', {}).get('max', 0)
    
    # =========================================================================
    # Validation Rule 1: Artifact Rate > 1.0% → FAIL
    # =========================================================================
    if artifact_rate > 1.0:
        if overall_status != 'FAIL':
            issues.append(
                f"❌ FAIL: Artifact rate {artifact_rate:.2f}% > 1.0%, "
                f"but status is '{overall_status}' (expected 'FAIL')"
            )
    
    # =========================================================================
    # Validation Rule 2: Artifact Rate 0.1-1.0% → REVIEW
    # =========================================================================
    elif artifact_rate > 0.1:
        if overall_status not in ['REVIEW', 'FAIL']:
            issues.append(
                f"⚠️  WARNING: Artifact rate {artifact_rate:.2f}% > 0.1%, "
                f"but status is '{overall_status}' (expected 'REVIEW')"
            )
    
    # =========================================================================
    # Validation Rule 3: High Intensity → PASS (HIGH INTENSITY)
    # =========================================================================
    if burst_decision == 'ACCEPT_HIGH_INTENSITY':
        if overall_status != 'PASS (HIGH INTENSITY)':
            issues.append(
                f"⚠️  WARNING: Burst decision is 'ACCEPT_HIGH_INTENSITY', "
                f"but overall_status is '{overall_status}' (expected 'PASS (HIGH INTENSITY)')"
            )
    
    # =========================================================================
    # Validation Rule 4: OLD ERROR LOGIC SHOULD BE GONE
    # =========================================================================
    # If max velocity > 1500 but artifact rate < 1.0%, should NOT be FAIL
    if max_ang_vel > 1500 and artifact_rate < 1.0:
        if overall_status == 'FAIL':
            issues.append(
                f"❌ ERROR: Old error-based logic detected! "
                f"Max velocity {max_ang_vel:.0f} > 1500 with artifact rate {artifact_rate:.2f}% < 1.0% "
                f"should NOT result in FAIL status"
            )
    
    # =========================================================================
    # Validation Rule 5: Status Reason Field Should Exist
    # =========================================================================
    if not status_reason and overall_status not in ['PASS', 'PRELIMINARY_CHECK']:
        issues.append(
            f"⚠️  WARNING: overall_status_reason is missing for status '{overall_status}'"
        )
    
    is_valid = len(issues) == 0
    return is_valid, issues


def validate_rms_grading(summary: Dict, run_id: str) -> Tuple[bool, List[str]]:
    """
    Validate RMS quality grading.
    
    Returns:
        (is_valid, issues_list)
    """
    issues = []
    
    signal_quality = summary.get('signal_quality', {})
    
    # Check for new fields
    rms_mm = signal_quality.get('avg_residual_rms_mm')
    rms_grade = signal_quality.get('rms_quality_grade')
    rms_interp = signal_quality.get('rms_interpretation')
    
    if rms_mm is None:
        issues.append("⚠️  WARNING: avg_residual_rms_mm field is missing")
        return False, issues
    
    if rms_grade is None:
        issues.append("⚠️  WARNING: rms_quality_grade field is missing")
        return False, issues
    
    # Validate grading logic
    if rms_mm < 15.0:
        expected_grade = 'GOLD'
    elif rms_mm < 30.0:
        expected_grade = 'SILVER'
    else:
        expected_grade = 'REVIEW'
    
    if rms_grade != expected_grade:
        issues.append(
            f"❌ ERROR: RMS grading incorrect. "
            f"RMS = {rms_mm:.2f}mm → expected '{expected_grade}', got '{rms_grade}'"
        )
    
    is_valid = len(issues) == 0
    return is_valid, issues


def scan_derivatives(derivatives_path: Path) -> List[Path]:
    """Find all step_06 kinematics summary files."""
    step06_dir = derivatives_path / "step_06_kinematics"
    
    if not step06_dir.exists():
        return []
    
    summary_files = list(step06_dir.glob("*__validation_report.json"))
    return sorted(summary_files)


def main(derivatives_path: Path = None):
    """Main validation routine."""
    
    print(f"\n{'='*80}")
    print("STEP 06 OVERALL STATUS FIX - VALIDATION")
    print(f"{'='*80}\n")
    
    # Find derivatives directory
    if derivatives_path is None:
        derivatives_path = Path(__file__).parent / "derivatives"
    
    if not derivatives_path.exists():
        print(f"❌ ERROR: Derivatives path not found: {derivatives_path}")
        return 1
    
    # Find all step 06 summaries
    summary_files = scan_derivatives(derivatives_path)
    
    if not summary_files:
        print(f"⚠️  WARNING: No Step 06 summary files found in {derivatives_path / 'step_06_kinematics'}")
        print("\nThis is expected if:")
        print("- You haven't run the updated notebook yet")
        print("- The notebook is still using the old logic")
        return 0
    
    print(f"📂 Found {len(summary_files)} Step 06 summary files\n")
    
    # Validation results
    total_files = len(summary_files)
    files_with_new_logic = 0
    files_with_old_logic = 0
    files_with_rms_grading = 0
    files_passed = 0
    all_issues = []
    
    # Process each file
    for summary_path in summary_files:
        run_id = summary_path.stem.replace('__kinematics_summary', '')
        
        try:
            summary = load_step06_summary(summary_path)
            
            # Check for new logic indicators
            has_status_reason = 'overall_status_reason' in summary
            has_rms_grading = 'rms_quality_grade' in summary.get('signal_quality', {})
            overall_status = summary.get('overall_status', 'UNKNOWN')
            
            if has_status_reason:
                files_with_new_logic += 1
            else:
                files_with_old_logic += 1
            
            if has_rms_grading:
                files_with_rms_grading += 1
            
            # Validate status logic
            status_valid, status_issues = validate_status_logic(summary, run_id)
            
            # Validate RMS grading (if present)
            rms_valid, rms_issues = True, []
            if has_rms_grading:
                rms_valid, rms_issues = validate_rms_grading(summary, run_id)
            
            # Report results for this file
            if status_valid and rms_valid:
                files_passed += 1
                print(f"✅ {run_id[:50]}")
                print(f"   Status: {overall_status}")
                if has_rms_grading:
                    rms_grade = summary.get('signal_quality', {}).get('rms_quality_grade')
                    rms_mm = summary.get('signal_quality', {}).get('avg_residual_rms_mm', 0)
                    print(f"   RMS: {rms_mm:.2f}mm ({rms_grade})")
            else:
                print(f"❌ {run_id[:50]}")
                for issue in status_issues + rms_issues:
                    print(f"   {issue}")
                    all_issues.append((run_id, issue))
            print()
        
        except Exception as e:
            print(f"❌ {run_id[:50]}")
            print(f"   ERROR: {e}\n")
            all_issues.append((run_id, str(e)))
    
    # Final summary
    print(f"{'='*80}")
    print("VALIDATION SUMMARY")
    print(f"{'='*80}\n")
    print(f"Total files scanned:        {total_files}")
    print(f"Files with new logic:       {files_with_new_logic}")
    print(f"Files with old logic:       {files_with_old_logic}")
    print(f"Files with RMS grading:     {files_with_rms_grading}")
    print(f"Files passed validation:    {files_passed}")
    print(f"Files failed validation:    {total_files - files_passed}")
    
    if files_with_old_logic > 0:
        print(f"\n⚠️  {files_with_old_logic} files are still using old logic")
        print("   → Run the updated notebook to regenerate these files")
    
    if files_with_rms_grading < files_with_new_logic:
        print(f"\n⚠️  {files_with_new_logic - files_with_rms_grading} files missing RMS grading")
        print("   → Ensure the RMS grading code is present in the notebook")
    
    if all_issues:
        print(f"\n{'='*80}")
        print(f"ISSUES FOUND ({len(all_issues)} total)")
        print(f"{'='*80}\n")
        for run_id, issue in all_issues[:10]:  # Show first 10
            print(f"📄 {run_id[:50]}")
            print(f"   {issue}\n")
        
        if len(all_issues) > 10:
            print(f"... and {len(all_issues) - 10} more issues")
    
    print(f"\n{'='*80}\n")
    
    # Return 0 if all files passed, 1 otherwise
    return 0 if files_passed == total_files else 1


if __name__ == "__main__":
    derivatives_path = None
    if len(sys.argv) > 1:
        derivatives_path = Path(sys.argv[1])
    
    sys.exit(main(derivatives_path))
