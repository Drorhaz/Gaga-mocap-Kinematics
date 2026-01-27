"""
Fix Step 06 Overall Status Logic - Shift from Error-Based to Classification-Based

This script updates notebook 06_rotvec_omega.ipynb to implement the new
classification-based status logic that treats high-intensity Gaga movement
as legitimate rather than as errors.

Usage:
    python fix_step06_status_logic.py

What it does:
    1. Updates 3 cells in 06_rotvec_omega.ipynb
    2. Changes overall_status logic from ERROR-based to CLASSIFICATION-based
    3. Adds RMS quality grading (GOLD/SILVER/REVIEW)

Author: Cursor AI
Date: 2026-01-23
"""

import json
import sys
from pathlib import Path


def fix_notebook_status_logic(notebook_path):
    """
    Fix the overall_status logic in 06_rotvec_omega.ipynb.
    
    Changes made:
    - Cell 7 (export_final_results function): Add note that status will be updated by Gate 5
    - Cell 10 (first summary build): Change to preliminary status
    - Cell 11 (second summary build): Change to preliminary status
    - Cell 13 (Gate integration): Implement proper classification logic
    """
    print(f"\n{'='*80}")
    print("STEP 06 OVERALL STATUS FIX - Classification-Based Logic")
    print(f"{'='*80}\n")
    
    # Load notebook
    print(f"📖 Loading notebook: {notebook_path}")
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    changes_made = 0
    
    # =========================================================================
    # FIX 1: Cell with export_final_results function (around line 1393)
    # =========================================================================
    for cell_idx, cell in enumerate(notebook['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            
            # Find the export_final_results function cell
            if 'def export_final_results' in source and 'overall_status = "PASS" if (v_pass and aa_pass and la_pass) else "FAIL"' in source:
                print(f"\n✏️  Fix 1: Updating export_final_results() in cell {cell_idx}")
                
                # Replace the old logic
                old_logic = '    overall_status = "PASS" if (v_pass and aa_pass and la_pass) else "FAIL"'
                new_logic = '''    # FIX 2026-01-23: PRELIMINARY status (will be updated by Gate 5 integration)
    # New Logic: Status is CLASSIFICATION-based, not ERROR-based
    # This preliminary status will be overwritten when Gate 4/5 results are integrated
    overall_status = "PASS" if (v_pass and aa_pass and la_pass) else "PRELIMINARY_CHECK"'''
                
                updated_source = source.replace(old_logic, new_logic)
                
                if updated_source != source:
                    cell['source'] = updated_source.split('\n')
                    # Ensure each line ends with \n except the last
                    cell['source'] = [line + '\n' if i < len(cell['source']) - 1 else line 
                                     for i, line in enumerate(cell['source'])]
                    changes_made += 1
                    print(f"   ✅ Updated: Changed 'FAIL' to 'PRELIMINARY_CHECK'")
                else:
                    print(f"   ⚠️  Warning: Could not find exact match for replacement")
    
    # =========================================================================
    # FIX 2 & 3: Standalone summary build cells (lines ~1529 and ~1664)
    # =========================================================================
    for cell_idx, cell in enumerate(notebook['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            
            # Find cells with standalone status calculation (not in a function)
            if ('overall_status = "PASS" if (max_ang_vel < 1500' in source and 
                'def export_final_results' not in source and
                '"run_id": RUN_ID' in source):
                
                print(f"\n✏️  Fix {changes_made + 1}: Updating standalone summary in cell {cell_idx}")
                
                old_logic = 'overall_status = "PASS" if (max_ang_vel < 1500 and max_ang_acc < 50000 and max_lin_acc < 100000) else "FAIL"'
                new_logic = '''# FIX 2026-01-23: PRELIMINARY status (will be updated by Gate 5 integration later in notebook)
# This is a basic biomechanical check - the final status depends on Gate 5 burst classification
overall_status = "PASS" if (max_ang_vel < 1500 and max_ang_acc < 50000 and max_lin_acc < 100000) else "PRELIMINARY_CHECK"'''
                
                updated_source = source.replace(old_logic, new_logic)
                
                if updated_source != source:
                    cell['source'] = updated_source.split('\n')
                    cell['source'] = [line + '\n' if i < len(cell['source']) - 1 else line 
                                     for i, line in enumerate(cell['source'])]
                    changes_made += 1
                    print(f"   ✅ Updated: Changed 'FAIL' to 'PRELIMINARY_CHECK'")
    
    # =========================================================================
    # FIX 4: Gate Integration Cell - Add proper classification logic
    # =========================================================================
    for cell_idx, cell in enumerate(notebook['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            
            # Find the gate integration cell (around line 2469)
            if ('updated_summary.update(gate_4_euler)' in source and 
                'updated_summary.update(gate_4_quat)' in source and
                "updated_summary['overall_gate_status']" in source):
                
                print(f"\n✏️  Fix {changes_made + 1}: Adding classification logic to Gate integration cell {cell_idx}")
                
                # Find the section that determines overall_gate_status
                old_block = '''# Determine overall gate status
gate_statuses = [
    gate_4_quat.get('step_06_math_status', 'PASS'),
    gate_5_fields.get('step_06_burst_decision', {}).get('overall_status', 'PASS') if gate_5_fields else 'PASS'
]

if 'REJECT' in gate_statuses:
    updated_summary['overall_gate_status'] = 'REJECT'
elif 'REVIEW' in gate_statuses:
    updated_summary['overall_gate_status'] = 'REVIEW'
elif 'ACCEPT_HIGH_INTENSITY' in gate_statuses:
    updated_summary['overall_gate_status'] = 'ACCEPT_HIGH_INTENSITY'
else:
    updated_summary['overall_gate_status'] = 'PASS' '''
                
                new_block = '''# =====================================================================
# FIX 2026-01-23: Classification-Based Status (Gaga-Specific Logic)
# =====================================================================
# NEW LOGIC: Status depends on Tier 1 artifact rate, not max velocity
#
# FAIL:                   Tier 1 artifacts > 1.0% of frames
# REVIEW:                 Tier 1 artifacts > 0.1% of frames
# PASS (HIGH INTENSITY):  Tier 2/3 present (legitimate Gaga movement)
# PASS:                   Standard movement within limits

# Get Gate 5 burst classification results
artifact_rate = 0.0
burst_decision_status = 'PASS'

if gate_5_fields:
    # Extract artifact rate from Gate 5 analysis
    frame_stats = gate_5_fields.get('step_06_burst_analysis', {}).get('frame_statistics', {})
    artifact_rate = frame_stats.get('artifact_rate_percent', 0.0)
    
    # Get burst decision
    burst_decision = gate_5_fields.get('step_06_burst_decision', {})
    burst_decision_status = burst_decision.get('overall_status', 'PASS')

# Determine overall_status based on NEW classification logic
if artifact_rate > 1.0:
    updated_summary['overall_status'] = 'FAIL'
    updated_summary['overall_status_reason'] = f'Tier 1 artifacts exceed 1.0% threshold ({artifact_rate:.2f}%)'
elif artifact_rate > 0.1:
    updated_summary['overall_status'] = 'REVIEW'
    updated_summary['overall_status_reason'] = f'Tier 1 artifacts exceed 0.1% threshold ({artifact_rate:.2f}%)'
elif burst_decision_status == 'ACCEPT_HIGH_INTENSITY':
    updated_summary['overall_status'] = 'PASS (HIGH INTENSITY)'
    updated_summary['overall_status_reason'] = 'High-intensity Gaga movement confirmed (Tier 2/3 flows present)'
elif burst_decision_status == 'REVIEW':
    updated_summary['overall_status'] = 'REVIEW'
    updated_summary['overall_status_reason'] = 'Manual review required for burst events'
elif burst_decision_status == 'REJECT':
    updated_summary['overall_status'] = 'FAIL'
    updated_summary['overall_status_reason'] = 'Gate 5 rejected due to data quality issues'
else:
    updated_summary['overall_status'] = 'PASS'
    updated_summary['overall_status_reason'] = 'Standard gait within physiological limits'

# Gate-level status (keep existing priority logic)
gate_statuses = [
    gate_4_quat.get('step_06_math_status', 'PASS'),
    burst_decision_status
]

if 'REJECT' in gate_statuses:
    updated_summary['overall_gate_status'] = 'REJECT'
elif 'REVIEW' in gate_statuses:
    updated_summary['overall_gate_status'] = 'REVIEW'
elif 'ACCEPT_HIGH_INTENSITY' in gate_statuses:
    updated_summary['overall_gate_status'] = 'ACCEPT_HIGH_INTENSITY'
else:
    updated_summary['overall_gate_status'] = 'PASS' '''
                
                if old_block in source:
                    updated_source = source.replace(old_block, new_block)
                    cell['source'] = updated_source.split('\n')
                    cell['source'] = [line + '\n' if i < len(cell['source']) - 1 else line 
                                     for i, line in enumerate(cell['source'])]
                    changes_made += 1
                    print(f"   ✅ Added: Classification-based status logic")
                    print(f"   ✅ Added: overall_status_reason field")
                else:
                    print(f"   ⚠️  Warning: Could not find exact gate status block")
    
    # =========================================================================
    # FIX 5: Add RMS Quality Grading
    # =========================================================================
    for cell_idx, cell in enumerate(notebook['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            
            # Find cell that builds signal_quality section
            if ('"signal_quality": {' in source and 
                '"avg_residual_rms":' in source and
                'res_vals = [v for k, v in ang_audit_metrics.items()' in source):
                
                print(f"\n✏️  Fix {changes_made + 1}: Adding RMS quality grading in cell {cell_idx}")
                
                # Find the location after avg_res_rms calculation
                marker = 'if norm_vals: max_norm_err = float(np.max(norm_vals))'
                
                if marker in source:
                    rms_grading_code = '''

# =====================================================================
# FIX 2026-01-23: Residual RMS Quality Grading - "Price of Smoothing"
# =====================================================================
# GOLD (<15mm):   Excellent tracking, minimal filtering distortion
# SILVER (15-30mm): Acceptable tracking, moderate filtering  
# REVIEW (>30mm):  High distortion - movement is truly explosive

rms_quality_grade = 'UNKNOWN'
rms_interpretation = 'No RMS data available'

if avg_res_rms > 0:
    if avg_res_rms < 15.0:
        rms_quality_grade = 'GOLD'
        rms_interpretation = 'Excellent tracking, minimal filtering distortion'
    elif avg_res_rms < 30.0:
        rms_quality_grade = 'SILVER'
        rms_interpretation = 'Acceptable tracking, moderate filtering'
    else:
        rms_quality_grade = 'REVIEW'
        rms_interpretation = 'High filtering distortion - movement is truly explosive (filter is fighting the movement)'
'''
                    
                    insertion_point = source.find(marker) + len(marker)
                    updated_source = source[:insertion_point] + rms_grading_code + source[insertion_point:]
                    
                    # Also update the signal_quality dict to include new fields
                    old_sig_qual = '"signal_quality": {\n        "avg_residual_rms": round(avg_res_rms, 6),'
                    new_sig_qual = '"signal_quality": {\n        "avg_residual_rms_mm": round(avg_res_rms, 2),\n        "rms_quality_grade": rms_quality_grade,\n        "rms_interpretation": rms_interpretation,\n        "avg_residual_rms": round(avg_res_rms, 6),'
                    
                    updated_source = updated_source.replace(old_sig_qual, new_sig_qual)
                    
                    cell['source'] = updated_source.split('\n')
                    cell['source'] = [line + '\n' if i < len(cell['source']) - 1 else line 
                                     for i, line in enumerate(cell['source'])]
                    changes_made += 1
                    print(f"   ✅ Added: RMS quality grading (GOLD/SILVER/REVIEW)")
                    print(f"   ✅ Added: avg_residual_rms_mm field")
    
    # Save updated notebook
    if changes_made > 0:
        # Create backup
        backup_path = notebook_path.parent / f"{notebook_path.stem}_BACKUP_before_status_fix{notebook_path.suffix}"
        print(f"\n💾 Creating backup: {backup_path}")
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=1)
        
        # Save updated notebook
        print(f"💾 Saving updated notebook: {notebook_path}")
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(notebook, f, indent=1)
        
        print(f"\n{'='*80}")
        print(f"✅ SUCCESS: Applied {changes_made} fixes to notebook")
        print(f"{'='*80}\n")
        print("Next steps:")
        print("1. Review the changes in Jupyter")
        print("2. Run the updated notebook on a test file")
        print("3. Verify that high-intensity files now show 'PASS (HIGH INTENSITY)' instead of 'FAIL'")
        print("\nBackup saved to:", backup_path)
    else:
        print(f"\n{'='*80}")
        print("⚠️  WARNING: No changes were made")
        print(f"{'='*80}\n")
        print("This might mean:")
        print("- The notebook has already been fixed")
        print("- The structure has changed significantly")
        print("- The search patterns need to be updated")
    
    return changes_made


def main():
    # Find the notebook
    notebook_path = Path(__file__).parent / "notebooks" / "06_rotvec_omega.ipynb"
    
    if not notebook_path.exists():
        print(f"❌ ERROR: Notebook not found at {notebook_path}")
        sys.exit(1)
    
    try:
        changes = fix_notebook_status_logic(notebook_path)
        return 0 if changes > 0 else 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
