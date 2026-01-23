#!/usr/bin/env python3
"""
Data Flow Validation Script
Validates that JSON summaries from notebooks contain all required fields.

Usage:
    python validate_data_flow.py --check-single <run_id>
    python validate_data_flow.py --check-batch <batch_summary.json>
    python validate_data_flow.py --check-all

Author: Gaga Pipeline Team
Date: 2026-01-23
"""

import os
import sys
import json
import glob
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


# Expected JSON structure (from utils_nb07.py PARAMETER_SCHEMA)
REQUIRED_FIELDS = {
    "step_01": {
        "file_pattern": "*__step01_loader_report.json",
        "required_fields": [
            "identity.run_id",
            "identity.processing_timestamp",
            "raw_data_quality.total_frames",
            "raw_data_quality.sampling_rate_actual",
            "raw_data_quality.optitrack_mean_error_mm",
        ]
    },
    "step_02": {
        "file_pattern": "*__preprocess_summary.json",
        "required_fields": [
            "run_id",
            "raw_missing_percent",
            "bone_qc_mean_cv",
            "bone_qc_status",
            # GATE 2 FIELDS (HIGH PRIORITY)
            "step_02_sample_time_jitter_ms",
            "step_02_jitter_status",
            "step_02_fallback_count",
            "step_02_fallback_rate_percent",
            "step_02_max_gap_frames",
            "step_02_interpolation_status",
        ]
    },
    "step_04": {
        "file_pattern": "*__filtering_summary.json",
        "required_fields": [
            "run_id",
            "filter_params.filter_cutoff_hz",
            "filter_params.filter_method",
            "filter_params.winter_analysis_failed",
            # GATE 3 FIELD (MEDIUM PRIORITY)
            # Note: region_cutoffs only required if filtering_mode == "per_region"
        ]
    },
    "step_05": {
        "file_pattern": "*__reference_summary.json",
        "required_fields": [
            "run_id",
            "window_metadata.ref_quality_score",
            "window_metadata.confidence_level",
            # SUBJECT CONTEXT (MEDIUM PRIORITY)
            "subject_context.height_cm",
            "subject_context.scaling_factor",
        ]
    },
    "step_06": {
        "file_pattern": "*__kinematics_summary.json",
        "required_fields": [
            "run_id",
            "overall_status",
            "metrics.angular_velocity.max",
            "metrics.angular_accel.max",
            # CRITICAL FIELDS (P0 - MUST FIX)
            "joint_statistics",  # Should be non-empty dict
            "step_06_burst_analysis.classification.artifact_count",
            "step_06_burst_analysis.classification.burst_count",
            "step_06_burst_decision.overall_status",
            "clean_statistics.clean_statistics.max_deg_s",
            "step_06_isb_compliant",
            "step_06_math_status",
        ]
    }
}

# Critical fields that must have non-empty/non-zero values
CRITICAL_NON_EMPTY_FIELDS = {
    "step_06": [
        ("joint_statistics", dict, lambda x: len(x) > 20),  # Should have 20+ joints
        ("step_06_burst_analysis", dict, lambda x: "classification" in x),
        ("clean_statistics", dict, lambda x: "clean_statistics" in x),
    ]
}


def get_nested_value(d: dict, path: str, default=None):
    """Get nested dictionary value using dot notation."""
    keys = path.split('.')
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, {})
        else:
            return default
    return d if (d != {} and d is not None) else default


def check_json_file(filepath: str, required_fields: List[str], step_name: str) -> Tuple[bool, List[str], List[str]]:
    """
    Validate a single JSON file.
    
    Returns:
        (success, missing_fields, warnings)
    """
    if not os.path.exists(filepath):
        return False, ["FILE_NOT_FOUND"], []
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except Exception as e:
        return False, [f"JSON_PARSE_ERROR: {e}"], []
    
    missing_fields = []
    warnings = []
    
    # Check required fields
    for field in required_fields:
        value = get_nested_value(data, field)
        if value is None or value == 'N/A':
            missing_fields.append(field)
    
    # Check critical non-empty fields
    if step_name in CRITICAL_NON_EMPTY_FIELDS:
        for field_path, expected_type, validation_func in CRITICAL_NON_EMPTY_FIELDS[step_name]:
            value = get_nested_value(data, field_path)
            
            if value is None:
                warnings.append(f"{field_path}: MISSING")
            elif not isinstance(value, expected_type):
                warnings.append(f"{field_path}: WRONG_TYPE (expected {expected_type.__name__}, got {type(value).__name__})")
            elif not validation_func(value):
                warnings.append(f"{field_path}: INVALID_VALUE (validation failed)")
    
    success = len(missing_fields) == 0 and len(warnings) == 0
    return success, missing_fields, warnings


def check_run(run_id: str, derivatives_root: str) -> Dict:
    """
    Validate all JSON files for a single run.
    
    Returns:
        Dict with validation results
    """
    results = {
        "run_id": run_id,
        "overall_status": "UNKNOWN",
        "steps": {}
    }
    
    total_issues = 0
    
    for step_name, step_config in REQUIRED_FIELDS.items():
        step_dir = os.path.join(derivatives_root, f"step_{step_name.split('_')[1]}_{step_name.split('_')[0]}")
        pattern = os.path.join(step_dir, step_config["file_pattern"])
        files = glob.glob(pattern)
        
        # Find matching file
        matching_file = None
        for f in files:
            if run_id in f:
                matching_file = f
                break
        
        if not matching_file:
            results["steps"][step_name] = {
                "status": "FILE_NOT_FOUND",
                "filepath": None,
                "missing_fields": ["FILE_NOT_FOUND"],
                "warnings": []
            }
            total_issues += 1
            continue
        
        # Validate file
        success, missing_fields, warnings = check_json_file(
            matching_file,
            step_config["required_fields"],
            step_name
        )
        
        results["steps"][step_name] = {
            "status": "PASS" if success else "FAIL",
            "filepath": matching_file,
            "missing_fields": missing_fields,
            "warnings": warnings
        }
        
        if not success:
            total_issues += len(missing_fields) + len(warnings)
    
    results["overall_status"] = "PASS" if total_issues == 0 else "FAIL"
    results["total_issues"] = total_issues
    
    return results


def print_validation_results(results: Dict, verbose: bool = False):
    """Print validation results in a readable format."""
    run_id = results["run_id"]
    status = results["overall_status"]
    total_issues = results.get("total_issues", 0)
    
    status_icon = "✅" if status == "PASS" else "❌"
    print(f"\n{status_icon} Run: {run_id}")
    print(f"   Status: {status} ({total_issues} issues)")
    
    if verbose or status == "FAIL":
        for step_name, step_results in results["steps"].items():
            step_status = step_results["status"]
            step_icon = "✅" if step_status == "PASS" else "❌"
            
            print(f"\n   {step_icon} {step_name.upper()}:")
            
            if step_status == "FILE_NOT_FOUND":
                print(f"      ⚠️  JSON file not found")
            elif step_status == "FAIL":
                if step_results["missing_fields"]:
                    print(f"      Missing fields ({len(step_results['missing_fields'])}):")
                    for field in step_results["missing_fields"][:5]:  # Show first 5
                        print(f"         - {field}")
                    if len(step_results["missing_fields"]) > 5:
                        print(f"         ... and {len(step_results['missing_fields']) - 5} more")
                
                if step_results["warnings"]:
                    print(f"      Warnings ({len(step_results['warnings'])}):")
                    for warning in step_results["warnings"][:3]:  # Show first 3
                        print(f"         ⚠️  {warning}")
                    if len(step_results["warnings"]) > 3:
                        print(f"         ... and {len(step_results['warnings']) - 3} more")


def check_single_run(run_id: str, derivatives_root: str, verbose: bool = False) -> bool:
    """Check a single run and return success status."""
    print("=" * 80)
    print("DATA FLOW VALIDATION - SINGLE RUN")
    print("=" * 80)
    
    results = check_run(run_id, derivatives_root)
    print_validation_results(results, verbose=True)
    
    print("\n" + "=" * 80)
    if results["overall_status"] == "PASS":
        print("✅ VALIDATION PASSED")
        print("=" * 80)
        return True
    else:
        print("❌ VALIDATION FAILED")
        print(f"   {results['total_issues']} issues found")
        print("=" * 80)
        return False


def check_batch(batch_summary_file: str, derivatives_root: str, verbose: bool = False):
    """Check all runs from a batch summary file."""
    print("=" * 80)
    print("DATA FLOW VALIDATION - BATCH CHECK")
    print("=" * 80)
    
    with open(batch_summary_file, 'r') as f:
        batch_data = json.load(f)
    
    runs = batch_data.get("runs", [])
    print(f"\nChecking {len(runs)} runs from batch...")
    
    pass_count = 0
    fail_count = 0
    issue_summary = defaultdict(int)
    
    for run_data in runs:
        run_id = run_data.get("run_id")
        if not run_id:
            continue
        
        results = check_run(run_id, derivatives_root)
        
        if results["overall_status"] == "PASS":
            pass_count += 1
        else:
            fail_count += 1
            
            # Count issues by step
            for step_name, step_results in results["steps"].items():
                if step_results["status"] == "FAIL":
                    issue_summary[step_name] += 1
        
        if verbose or results["overall_status"] == "FAIL":
            print_validation_results(results, verbose=verbose)
    
    # Summary
    print("\n" + "=" * 80)
    print("BATCH VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Total Runs:  {len(runs)}")
    print(f"Passed:      {pass_count} ({pass_count/len(runs)*100:.1f}%)")
    print(f"Failed:      {fail_count} ({fail_count/len(runs)*100:.1f}%)")
    
    if fail_count > 0:
        print("\nIssues by Step:")
        for step_name, count in sorted(issue_summary.items()):
            print(f"   {step_name}: {count} runs")
    
    print("=" * 80)
    
    if pass_count == len(runs):
        print("✅ ALL RUNS PASSED")
        return True
    else:
        print(f"❌ {fail_count} RUNS FAILED")
        return False


def check_all_runs(derivatives_root: str, verbose: bool = False):
    """Check all runs in derivatives folder."""
    print("=" * 80)
    print("DATA FLOW VALIDATION - ALL RUNS")
    print("=" * 80)
    
    # Discover all runs from step_06 kinematics files
    step_06_dir = os.path.join(derivatives_root, "step_06_kinematics")
    json_files = glob.glob(os.path.join(step_06_dir, "*__kinematics_summary.json"))
    
    run_ids = []
    for filepath in json_files:
        filename = os.path.basename(filepath)
        run_id = filename.replace("__kinematics_summary.json", "")
        run_ids.append(run_id)
    
    print(f"\nFound {len(run_ids)} runs to validate...")
    
    pass_count = 0
    fail_count = 0
    issue_summary = defaultdict(int)
    
    for run_id in run_ids:
        results = check_run(run_id, derivatives_root)
        
        if results["overall_status"] == "PASS":
            pass_count += 1
        else:
            fail_count += 1
            
            # Count issues by step
            for step_name, step_results in results["steps"].items():
                if step_results["status"] == "FAIL":
                    issue_summary[step_name] += 1
        
        if verbose or results["overall_status"] == "FAIL":
            print_validation_results(results, verbose=verbose)
    
    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY (ALL RUNS)")
    print("=" * 80)
    print(f"Total Runs:  {len(run_ids)}")
    print(f"Passed:      {pass_count} ({pass_count/len(run_ids)*100:.1f}%)")
    print(f"Failed:      {fail_count} ({fail_count/len(run_ids)*100:.1f}%)")
    
    if fail_count > 0:
        print("\nIssues by Step:")
        for step_name, count in sorted(issue_summary.items(), key=lambda x: -x[1]):
            print(f"   {step_name}: {count} runs ({count/len(run_ids)*100:.1f}%)")
    
    print("=" * 80)
    
    if pass_count == len(run_ids):
        print("✅ ALL RUNS PASSED")
        return True
    else:
        print(f"❌ {fail_count} RUNS FAILED")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Validate JSON data flow from notebooks to Master Audit'
    )
    
    parser.add_argument(
        '--check-single',
        type=str,
        help='Validate a single run by run_id'
    )
    
    parser.add_argument(
        '--check-batch',
        type=str,
        help='Validate all runs from batch summary JSON file'
    )
    
    parser.add_argument(
        '--check-all',
        action='store_true',
        help='Validate all runs in derivatives folder'
    )
    
    parser.add_argument(
        '--derivatives',
        type=str,
        default='derivatives',
        help='Path to derivatives folder (default: derivatives)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed results for all runs (not just failures)'
    )
    
    args = parser.parse_args()
    
    # Determine project root
    if os.path.basename(os.getcwd()) == 'gaga':
        project_root = os.getcwd()
    else:
        project_root = os.path.dirname(os.path.abspath(__file__))
    
    derivatives_root = os.path.join(project_root, args.derivatives)
    
    if not os.path.exists(derivatives_root):
        print(f"❌ ERROR: Derivatives folder not found: {derivatives_root}")
        sys.exit(1)
    
    # Execute validation
    success = False
    
    if args.check_single:
        success = check_single_run(args.check_single, derivatives_root, args.verbose)
    elif args.check_batch:
        success = check_batch(args.check_batch, derivatives_root, args.verbose)
    elif args.check_all:
        success = check_all_runs(derivatives_root, args.verbose)
    else:
        parser.print_help()
        sys.exit(1)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
