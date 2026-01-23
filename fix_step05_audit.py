"""
Fix Step 05 Reference Summary - Add Height Status Field
2026-01-23

This script adds the missing height_status field to existing reference_summary.json files.
"""

import json
from pathlib import Path
from typing import Dict, Any

def validate_height(height_cm: float) -> str:
    """
    Validate computed height against physiological ranges.
    
    Returns:
        "PASS" - Normal adult range (140-210 cm)
        "REVIEW" - Edge case (very short/tall, or child)
        "FAIL" - Unphysiological (<120cm or >250cm)
    """
    if height_cm <= 0:
        return "FAIL"  # Invalid height
    elif 140 <= height_cm <= 210:
        return "PASS"  # Normal adult range
    elif 120 < height_cm < 140 or 210 < height_cm < 250:
        return "REVIEW"  # Edge cases (very short/tall, or child)
    else:
        return "FAIL"  # Unphysiological


def fix_reference_summary(summary_path: Path) -> Dict[str, Any]:
    """
    Fix a reference summary JSON by adding height_status field.
    
    Args:
        summary_path: Path to existing reference_summary.json
        
    Returns:
        Updated summary dict
    """
    # Load existing summary
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    
    run_id = summary.get('run_id', 'unknown')
    print(f"\n[FIX] Processing: {run_id}")
    
    # Get height from subject_context
    subject_context = summary.get('subject_context', {})
    height_cm = subject_context.get('height_cm', 0)
    
    # Validate and add status
    height_status = validate_height(height_cm)
    subject_context['height_status'] = height_status
    
    # Update summary
    summary['subject_context'] = subject_context
    
    print(f"  [OK] Height: {height_cm:.2f} cm")
    print(f"  [OK] Status: {height_status}")
    
    return summary


def main():
    """Fix all reference summary files."""
    print("=" * 80)
    print("STEP 05 REFERENCE SUMMARY FIX - HEIGHT VALIDATION STATUS")
    print("=" * 80)
    print("Target: Add height_status field to existing reference summaries")
    print("Date: 2026-01-23")
    print()
    
    # Find all reference summary files
    deriv_reference = Path("derivatives/step_05_reference")
    summary_files = list(deriv_reference.glob("*__reference_summary.json"))
    
    print(f"Found {len(summary_files)} reference summary files")
    
    if not summary_files:
        print("[ERROR] No reference summary files found!")
        print("   Run Step 05 (Notebook 05_reference.ipynb) first")
        return
    
    # Fix each file
    fixed_count = 0
    for summary_path in summary_files:
        try:
            updated_summary = fix_reference_summary(summary_path)
            
            # Save back to file
            with open(summary_path, 'w') as f:
                json.dump(updated_summary, f, indent=2)
            
            print(f"  [SAVE] Saved updated summary")
            fixed_count += 1
            
        except Exception as e:
            print(f"  [ERROR] Error fixing {summary_path.name}: {e}")
    
    print()
    print("=" * 80)
    print(f"[SUCCESS] COMPLETED: Fixed {fixed_count}/{len(summary_files)} files")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
