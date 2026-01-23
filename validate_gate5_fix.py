#!/usr/bin/env python3
"""
Gate 5 Fix Validation Script
=============================
This script validates that the Gate 5 fix has been successfully applied
by checking multiple aspects of the data pipeline.

Usage:
    python validate_gate5_fix.py [RUN_ID]
    
    If RUN_ID is provided, validates that specific recording.
    If no RUN_ID, validates all recordings.

Author: Gaga Pipeline
Date: 2026-01-23
"""

import os
import json
import glob
import pandas as pd
from typing import Dict, List, Tuple, Optional

def validate_single_recording(run_id: str, deriv_root: str = "derivatives") -> Dict:
    """
    Validate Gate 5 data for a single recording.
    
    Returns dict with validation results.
    """
    results = {
        'run_id': run_id,
        'valid': True,
        'checks': {},
        'warnings': [],
        'errors': []
    }
    
    step_06_dir = os.path.join(deriv_root, "step_06_kinematics")
    json_path = os.path.join(step_06_dir, f"{run_id}__kinematics_summary.json")
    mask_path = os.path.join(step_06_dir, f"{run_id}__joint_status_mask.parquet")
    
    # CHECK 1: JSON file exists
    if not os.path.exists(json_path):
        results['valid'] = False
        results['errors'].append(f"JSON file not found: {json_path}")
        return results
    
    results['checks']['json_exists'] = True
    
    # CHECK 2: Load JSON
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        results['checks']['json_loads'] = True
    except Exception as e:
        results['valid'] = False
        results['errors'].append(f"Failed to load JSON: {e}")
        return results
    
    # CHECK 3: Gate 5 fields present
    required_fields = [
        'step_06_burst_analysis',
        'step_06_burst_decision',
        'step_06_frames_to_exclude',
        'step_06_data_validity'
    ]
    
    missing_fields = []
    for field in required_fields:
        if field in data:
            results['checks'][f'{field}_present'] = True
        else:
            results['checks'][f'{field}_present'] = False
            missing_fields.append(field)
            results['valid'] = False
    
    if missing_fields:
        results['errors'].append(f"Missing Gate 5 fields: {', '.join(missing_fields)}")
        return results
    
    # CHECK 4: Burst analysis structure
    try:
        burst_analysis = data['step_06_burst_analysis']
        
        # Check classification counts
        classification = burst_analysis.get('classification', {})
        artifact_count = classification.get('artifact_count', None)
        burst_count = classification.get('burst_count', None)
        flow_count = classification.get('flow_count', None)
        total_events = classification.get('total_events', None)
        
        if None in [artifact_count, burst_count, flow_count, total_events]:
            results['valid'] = False
            results['errors'].append("Classification counts missing or None")
        else:
            results['checks']['classification_complete'] = True
            results['event_counts'] = {
                'artifacts': artifact_count,
                'bursts': burst_count,
                'flows': flow_count,
                'total': total_events
            }
            
            # Validate total
            expected_total = artifact_count + burst_count + flow_count
            if total_events != expected_total:
                results['warnings'].append(
                    f"Total events mismatch: {total_events} != {expected_total}"
                )
        
        # Check frame statistics
        frame_stats = burst_analysis.get('frame_statistics', {})
        artifact_rate = frame_stats.get('artifact_rate_percent', None)
        if artifact_rate is not None:
            results['checks']['frame_statistics_present'] = True
            results['artifact_rate_percent'] = artifact_rate
        else:
            results['warnings'].append("Artifact rate percent not found")
            
    except Exception as e:
        results['valid'] = False
        results['errors'].append(f"Error parsing burst_analysis: {e}")
    
    # CHECK 5: Burst decision structure
    try:
        decision = data['step_06_burst_decision']
        status = decision.get('overall_status', None)
        reason = decision.get('primary_reason', None)
        
        if status and reason:
            results['checks']['burst_decision_complete'] = True
            results['decision_status'] = status
            results['decision_reason'] = reason
        else:
            results['warnings'].append("Burst decision incomplete")
            
        # Validate status value
        valid_statuses = ['ACCEPT_HIGH_INTENSITY', 'REVIEW', 'REJECT', 'PASS']
        if status and status not in valid_statuses:
            results['warnings'].append(f"Unknown decision status: {status}")
            
    except Exception as e:
        results['valid'] = False
        results['errors'].append(f"Error parsing burst_decision: {e}")
    
    # CHECK 6: Frames to exclude
    try:
        frames_to_exclude = data['step_06_frames_to_exclude']
        if isinstance(frames_to_exclude, list):
            results['checks']['frames_to_exclude_valid'] = True
            results['exclude_frame_count'] = len(frames_to_exclude)
        else:
            results['warnings'].append("frames_to_exclude is not a list")
    except Exception as e:
        results['warnings'].append(f"Error checking frames_to_exclude: {e}")
    
    # CHECK 7: Parquet mask file exists
    if os.path.exists(mask_path):
        results['checks']['mask_parquet_exists'] = True
        
        # Try to load it
        try:
            df_mask = pd.read_parquet(mask_path)
            results['checks']['mask_parquet_loads'] = True
            results['mask_shape'] = df_mask.shape
            
            # Check for expected columns
            expected_cols = ['frame_idx', 'time_s', 'any_outlier', 'max_tier']
            missing_cols = [c for c in expected_cols if c not in df_mask.columns]
            if not missing_cols:
                results['checks']['mask_columns_valid'] = True
            else:
                results['warnings'].append(f"Mask missing columns: {missing_cols}")
                
        except Exception as e:
            results['warnings'].append(f"Failed to load mask parquet: {e}")
    else:
        results['warnings'].append(f"Mask parquet not found: {mask_path}")
    
    # CHECK 8: Gate 4 fields (should also be present)
    gate4_fields = ['step_06_isb_compliant', 'step_06_math_status']
    for field in gate4_fields:
        if field in data:
            results['checks'][f'{field}_present'] = True
        else:
            results['warnings'].append(f"Gate 4 field missing: {field}")
    
    # CHECK 9: Overall gate status
    if 'overall_gate_status' in data:
        results['checks']['overall_gate_status_present'] = True
        results['overall_gate_status'] = data['overall_gate_status']
    else:
        results['warnings'].append("overall_gate_status field missing")
    
    return results


def validate_all_recordings(deriv_root: str = "derivatives") -> Tuple[List[Dict], List[Dict]]:
    """
    Validate all recordings.
    
    Returns:
        (valid_recordings, invalid_recordings)
    """
    step_06_dir = os.path.join(deriv_root, "step_06_kinematics")
    json_files = glob.glob(os.path.join(step_06_dir, "*__kinematics_summary.json"))
    
    valid = []
    invalid = []
    
    for json_path in json_files:
        run_id = os.path.basename(json_path).replace('__kinematics_summary.json', '')
        result = validate_single_recording(run_id, deriv_root)
        
        if result['valid']:
            valid.append(result)
        else:
            invalid.append(result)
    
    return valid, invalid


def print_validation_report(valid: List[Dict], invalid: List[Dict]):
    """Print formatted validation report."""
    total = len(valid) + len(invalid)
    
    print("=" * 100)
    print("GATE 5 FIX VALIDATION REPORT")
    print("=" * 100)
    print(f"\nTotal Recordings: {total}")
    print(f"  [OK] Valid: {len(valid)} ({len(valid)/total*100:.1f}%)" if total > 0 else "")
    print(f"  [FAIL] Invalid: {len(invalid)} ({len(invalid)/total*100:.1f}%)" if total > 0 else "")
    
    # Summary statistics from valid recordings
    if valid:
        print("\n" + "=" * 100)
        print("[OK] VALID RECORDINGS - GATE 5 DATA PRESENT")
        print("=" * 100)
        
        total_artifacts = sum(r.get('event_counts', {}).get('artifacts', 0) for r in valid)
        total_bursts = sum(r.get('event_counts', {}).get('bursts', 0) for r in valid)
        total_flows = sum(r.get('event_counts', {}).get('flows', 0) for r in valid)
        total_events = sum(r.get('event_counts', {}).get('total', 0) for r in valid)
        
        print(f"\nAggregate Event Statistics:")
        print(f"  Total Artifacts (Tier 1): {total_artifacts:,}")
        print(f"  Total Bursts (Tier 2): {total_bursts:,}")
        print(f"  Total Flows (Tier 3): {total_flows:,}")
        print(f"  Total Events: {total_events:,}")
        
        print(f"\nPer-Recording Averages:")
        print(f"  Mean Artifacts: {total_artifacts/len(valid):.1f}")
        print(f"  Mean Bursts: {total_bursts/len(valid):.1f}")
        print(f"  Mean Flows: {total_flows/len(valid):.1f}")
        
        # Decision distribution
        decisions = {}
        for r in valid:
            status = r.get('decision_status', 'UNKNOWN')
            decisions[status] = decisions.get(status, 0) + 1
        
        print(f"\nDecision Status Distribution:")
        for status, count in sorted(decisions.items(), key=lambda x: -x[1]):
            print(f"  {status}: {count}/{len(valid)} ({count/len(valid)*100:.1f}%)")
        
        # Show recordings with warnings
        with_warnings = [r for r in valid if r.get('warnings')]
        if with_warnings:
            print(f"\n[WARNING] {len(with_warnings)} recording(s) have warnings:")
            for r in with_warnings[:5]:  # Show first 5
                print(f"\n  {r['run_id'][:60]}")
                for warning in r['warnings'][:3]:  # Show first 3 warnings
                    print(f"    - {warning}")
            if len(with_warnings) > 5:
                print(f"  ... and {len(with_warnings)-5} more with warnings")
    
    # Invalid recordings
    if invalid:
        print("\n" + "=" * 100)
        print("[FAIL] INVALID RECORDINGS - GATE 5 DATA MISSING OR INCOMPLETE")
        print("=" * 100)
        
        for r in invalid:
            print(f"\n{r['run_id'][:70]}")
            
            if r.get('errors'):
                print("  Errors:")
                for error in r['errors']:
                    print(f"    [X] {error}")
            
            if r.get('warnings'):
                print("  Warnings:")
                for warning in r['warnings'][:3]:
                    print(f"    [!] {warning}")
        
        print("\n" + "=" * 100)
        print("[ACTION] Re-run Gate 5 cell for these recordings")
        print("=" * 100)
    
    # Overall summary
    print("\n" + "=" * 100)
    print("VALIDATION SUMMARY")
    print("=" * 100)
    
    if not invalid:
        print("\n[SUCCESS] All recordings have valid Gate 5 data!")
        print("  - Step 06 JSON files contain complete burst analysis")
        print("  - Event counts are properly populated")
        print("  - Ready for Step 07 Master Quality Report")
        print("\nNext step: Run notebook 07_master_quality_report.ipynb")
    else:
        print(f"\n[INCOMPLETE] {len(invalid)} recording(s) need Gate 5 processing")
        print(f"  - Complete: {len(valid)}/{total} ({len(valid)/total*100:.1f}%)")
        print("\nNext steps:")
        print("  1. Process the invalid recordings listed above")
        print("  2. Re-run this validation script")
        print("  3. When all pass, run notebook 07")
    
    print("=" * 100)


def print_single_validation(result: Dict):
    """Print validation result for single recording."""
    print("=" * 100)
    print(f"VALIDATION: {result['run_id']}")
    print("=" * 100)
    
    if result['valid']:
        print("\n[OK] Gate 5 data is VALID")
    else:
        print("\n[FAIL] Gate 5 data is INVALID")
    
    print("\nChecks:")
    for check, passed in result['checks'].items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {check}")
    
    if result.get('event_counts'):
        print("\nEvent Counts:")
        counts = result['event_counts']
        print(f"  Artifacts (Tier 1): {counts.get('artifacts', 0)}")
        print(f"  Bursts (Tier 2): {counts.get('bursts', 0)}")
        print(f"  Flows (Tier 3): {counts.get('flows', 0)}")
        print(f"  Total Events: {counts.get('total', 0)}")
    
    if result.get('decision_status'):
        print(f"\nDecision: {result['decision_status']}")
        print(f"Reason: {result['decision_reason']}")
    
    if result.get('artifact_rate_percent') is not None:
        print(f"\nArtifact Rate: {result['artifact_rate_percent']:.4f}%")
    
    if result.get('exclude_frame_count') is not None:
        print(f"Frames to Exclude: {result['exclude_frame_count']}")
    
    if result.get('mask_shape'):
        print(f"\nMask Parquet Shape: {result['mask_shape']}")
    
    if result.get('warnings'):
        print("\nWarnings:")
        for warning in result['warnings']:
            print(f"  [!] {warning}")
    
    if result.get('errors'):
        print("\nErrors:")
        for error in result['errors']:
            print(f"  [X] {error}")
    
    print("=" * 100)


def main():
    import sys
    
    # Get project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    deriv_root = os.path.join(project_root, "derivatives")
    
    # Check if specific RUN_ID provided
    if len(sys.argv) > 1:
        run_id = sys.argv[1]
        print(f"\nValidating specific recording: {run_id}\n")
        result = validate_single_recording(run_id, deriv_root)
        print_single_validation(result)
        sys.exit(0 if result['valid'] else 1)
    
    # Validate all recordings
    print("\nValidating all recordings...\n")
    valid, invalid = validate_all_recordings(deriv_root)
    
    if not valid and not invalid:
        print("[ERROR] No Step 06 JSON files found")
        sys.exit(1)
    
    print_validation_report(valid, invalid)
    
    # Exit code: 0 if all valid, 1 if any invalid
    sys.exit(0 if not invalid else 1)


if __name__ == "__main__":
    main()
