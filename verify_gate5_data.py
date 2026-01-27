#!/usr/bin/env python3
"""
Gate 5 Data Verification Script
================================
This script checks which Step 06 JSON files have Gate 5 burst classification data
and provides a report of what needs to be re-processed.

Usage:
    python verify_gate5_data.py

Author: Gaga Pipeline
Date: 2026-01-23
"""

import os
import json
import glob
from typing import Dict, List, Tuple

def check_gate5_presence(deriv_root: str = "derivatives") -> Tuple[List[Dict], List[Dict]]:
    """
    Check all Step 06 JSON files for Gate 5 data presence.
    
    Returns:
        Tuple of (recordings_with_gate5, recordings_missing_gate5)
    """
    step_06_dir = os.path.join(deriv_root, "step_06_kinematics")
    
    if not os.path.exists(step_06_dir):
        print(f"[WARNING] Step 06 directory not found: {step_06_dir}")
        return [], []
    
    json_pattern = os.path.join(step_06_dir, "*__kinematics_summary.json")
    json_files = glob.glob(json_pattern)
    
    if not json_files:
        print(f"[WARNING] No JSON files found in {step_06_dir}")
        return [], []
    
    with_gate5 = []
    missing_gate5 = []
    
    for json_path in json_files:
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            run_id = data.get('run_id', os.path.basename(json_path).replace('__kinematics_summary.json', ''))
            
            # Check for Gate 5 fields
            has_burst_analysis = 'step_06_burst_analysis' in data
            has_burst_decision = 'step_06_burst_decision' in data
            has_frames_to_exclude = 'step_06_frames_to_exclude' in data
            
            has_gate5 = has_burst_analysis and has_burst_decision
            
            info = {
                'run_id': run_id,
                'json_path': json_path,
                'has_burst_analysis': has_burst_analysis,
                'has_burst_decision': has_burst_decision,
                'has_frames_to_exclude': has_frames_to_exclude
            }
            
            if has_gate5:
                # Extract burst metrics
                burst_class = data['step_06_burst_analysis']['classification']
                info['artifact_count'] = burst_class['artifact_count']
                info['burst_count'] = burst_class['burst_count']
                info['flow_count'] = burst_class['flow_count']
                info['total_events'] = burst_class['total_events']
                
                # Get decision
                info['decision_status'] = data['step_06_burst_decision']['overall_status']
                info['decision_reason'] = data['step_06_burst_decision']['primary_reason']
                
                with_gate5.append(info)
            else:
                missing_gate5.append(info)
                
        except Exception as e:
            print(f"[WARNING] Failed to read {json_path}: {e}")
            missing_gate5.append({
                'run_id': os.path.basename(json_path).replace('__kinematics_summary.json', ''),
                'json_path': json_path,
                'error': str(e)
            })
    
    return with_gate5, missing_gate5


def print_report(with_gate5: List[Dict], missing_gate5: List[Dict]):
    """Print a formatted report of Gate 5 data status."""
    
    total = len(with_gate5) + len(missing_gate5)
    
    print("=" * 100)
    print("GATE 5 DATA VERIFICATION REPORT")
    print("=" * 100)
    print(f"\nTotal Recordings: {total}")
    print(f"  [OK] With Gate 5 Data: {len(with_gate5)} ({len(with_gate5)/total*100:.1f}%)" if total > 0 else "")
    print(f"  [MISSING] Missing Gate 5: {len(missing_gate5)} ({len(missing_gate5)/total*100:.1f}%)" if total > 0 else "")
    
    # Report recordings WITH Gate 5 data
    if with_gate5:
        print("\n" + "=" * 100)
        print("[OK] RECORDINGS WITH GATE 5 DATA")
        print("=" * 100)
        print(f"{'Run ID':<60} | {'Artifacts':<10} | {'Bursts':<8} | {'Flows':<7} | {'Total':<7} | Status")
        print("-" * 100)
        
        for rec in with_gate5:
            run_id_short = rec['run_id'][:58] if len(rec['run_id']) > 58 else rec['run_id']
            status_icon = "[OK]" if rec['decision_status'] == 'ACCEPT_HIGH_INTENSITY' else "[!]" if rec['decision_status'] == 'REVIEW' else "[X]"
            
            print(f"{run_id_short:<60} | {rec['artifact_count']:<10} | {rec['burst_count']:<8} | "
                  f"{rec['flow_count']:<7} | {rec['total_events']:<7} | {status_icon} {rec['decision_status']}")
        
        print("\nSummary Statistics:")
        total_artifacts = sum(r['artifact_count'] for r in with_gate5)
        total_bursts = sum(r['burst_count'] for r in with_gate5)
        total_flows = sum(r['flow_count'] for r in with_gate5)
        total_events = sum(r['total_events'] for r in with_gate5)
        
        print(f"   Total Artifacts (Tier 1): {total_artifacts:,}")
        print(f"   Total Bursts (Tier 2): {total_bursts:,}")
        print(f"   Total Flows (Tier 3): {total_flows:,}")
        print(f"   Total Events: {total_events:,}")
        
        # Decision distribution
        decisions = {}
        for r in with_gate5:
            status = r['decision_status']
            decisions[status] = decisions.get(status, 0) + 1
        
        print(f"\nDecision Distribution:")
        for status, count in sorted(decisions.items()):
            print(f"   {status}: {count}/{len(with_gate5)}")
    
    # Report recordings MISSING Gate 5 data
    if missing_gate5:
        print("\n" + "=" * 100)
        print("[MISSING] RECORDINGS MISSING GATE 5 DATA (ACTION REQUIRED)")
        print("=" * 100)
        print(f"{'Run ID':<60} | Status")
        print("-" * 100)
        
        for rec in missing_gate5:
            run_id_short = rec['run_id'][:58] if len(rec['run_id']) > 58 else rec['run_id']
            
            if 'error' in rec:
                print(f"{run_id_short:<60} | ERROR: {rec['error'][:30]}")
            else:
                missing_fields = []
                if not rec.get('has_burst_analysis'):
                    missing_fields.append('burst_analysis')
                if not rec.get('has_burst_decision'):
                    missing_fields.append('burst_decision')
                if not rec.get('has_frames_to_exclude'):
                    missing_fields.append('frames_to_exclude')
                
                print(f"{run_id_short:<60} | Missing: {', '.join(missing_fields)}")
        
        print("\n" + "=" * 100)
        print("ACTION REQUIRED:")
        print("=" * 100)
        print("For each recording listed above, you must:")
        print("  1. Open notebook: 06_rotvec_omega.ipynb")
        print("  2. Set RUN_ID to the recording identifier")
        print("  3. Execute the 'GATE 4 & 5 INTEGRATION' cell")
        print("  4. Verify the JSON file is updated with burst metrics")
        print("\nAfter processing all recordings, re-run notebook 07 to update the Master Quality Report.")
        print("=" * 100)
    
    # Final summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    
    if not missing_gate5:
        print("[OK] All recordings have Gate 5 data!")
        print("   You can proceed to run notebook 07 (Master Quality Report)")
    else:
        print(f"[ACTION] {len(missing_gate5)} recording(s) need Gate 5 processing")
        print(f"   Complete percentage: {len(with_gate5)/total*100:.1f}%" if total > 0 else "")
        print(f"\n   Next steps:")
        print(f"   1. Process the {len(missing_gate5)} recordings listed above")
        print(f"   2. Re-run this script to verify completion")
        print(f"   3. Run notebook 07 to generate updated Master Quality Report")
    
    print("=" * 100)


def main():
    """Main execution function."""
    import sys
    
    # Get project root (assuming script is in project root)
    project_root = os.path.dirname(os.path.abspath(__file__))
    deriv_root = os.path.join(project_root, "derivatives")
    
    print(f"\nScanning for Step 06 JSON files...")
    print(f"   Derivatives root: {deriv_root}")
    
    with_gate5, missing_gate5 = check_gate5_presence(deriv_root)
    
    if not with_gate5 and not missing_gate5:
        print("\n[ERROR] No Step 06 JSON files found. Have you run notebook 06 yet?")
        sys.exit(1)
    
    print_report(with_gate5, missing_gate5)
    
    # Exit code: 0 if all have Gate 5, 1 if some are missing
    sys.exit(0 if not missing_gate5 else 1)


if __name__ == "__main__":
    main()
