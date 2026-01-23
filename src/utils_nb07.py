"""
utils_nb07.py - Utility functions for Master Quality Report (Notebook 07)

This module centralizes:
1. JSON loading and validation
2. Parameter extraction with safe access
3. Quality scoring functions
4. Excel export utilities

Author: Gaga Pipeline
Version: 2.0 (Optimized)
"""

import os
import json
import glob
import hashlib
import subprocess
import numpy as np
import pandas as pd
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple, Union


# ============================================================
# SCHEMA DEFINITION - All JSON parameters used in the report
# ============================================================

PARAMETER_SCHEMA = {
    "step_01": {
        "file_suffix": "__step01_loader_report.json",
        "description": "Raw data loader report - initial parsing results",
        "parameters": {
            "identity.run_id": {"type": "str", "section": "S0", "description": "Unique recording identifier"},
            "identity.processing_timestamp": {"type": "str", "section": "S0", "description": "When pipeline ran"},
            "identity.pipeline_version": {"type": "str", "section": "S0", "description": "Pipeline version string"},
            "identity.csv_source": {"type": "str", "section": "S0", "description": "Path to raw CSV file"},
            "raw_data_quality.total_frames": {"type": "int", "section": "S2", "description": "Total frames in recording"},
            "raw_data_quality.missing_data_percent": {"type": "str", "section": "S3", "description": "Percentage of missing data"},
            "raw_data_quality.sampling_rate_actual": {"type": "float", "section": "S2", "description": "Actual sampling rate (Hz)"},
            "raw_data_quality.optitrack_mean_error_mm": {"type": "float", "section": "S1", "description": "OptiTrack calibration error (mm)"},
            "raw_data_quality.optitrack_version": {"type": "str", "section": "S0", "description": "OptiTrack software version"},
            "calibration.pointer_tip_rms_error_mm": {"type": "float", "section": "S1", "description": "Pointer tip RMS error (mm)"},
            "calibration.wand_error_mm": {"type": "float", "section": "S1", "description": "Wand calibration error (mm)"},
            "calibration.export_date": {"type": "str", "section": "S0", "description": "Data export date"},
            "skeleton_info.segments_found_count": {"type": "int", "section": "S1", "description": "Number of skeleton segments found"},
            "skeleton_info.segments_missing_count": {"type": "int", "section": "S1", "description": "Number of missing segments"},
            "duration_sec": {"type": "float", "section": "S2", "description": "Recording duration in seconds"},
        }
    },
    "step_02": {
        "file_suffix": "__preprocess_summary.json",
        "description": "Preprocessing summary - gap filling and bone stability",
        "parameters": {
            "run_id": {"type": "str", "section": "S0", "description": "Recording identifier"},
            "raw_missing_percent": {"type": "float", "section": "S3", "description": "Raw missing data percentage"},
            "post_missing_percent": {"type": "float", "section": "S3", "description": "Missing data after interpolation"},
            "max_interpolation_gap": {"type": "int", "section": "S3", "description": "Maximum gap frames allowed for interpolation"},
            "bone_qc_mean_cv": {"type": "float", "section": "S1", "description": "Mean coefficient of variation for bone lengths"},
            "bone_qc_status": {"type": "str", "section": "S1", "description": "Bone QC status (GOLD/SILVER/BRONZE/FAIL)"},
            "bone_qc_alerts": {"type": "list", "section": "S1", "description": "List of bones with alerts"},
            "worst_bone": {"type": "str", "section": "S1", "description": "Bone with highest CV"},
            "interpolation_method": {"type": "str", "section": "S3", "description": "Global interpolation method used"},
        }
    },
    "step_04": {
        "file_suffix": "__filtering_summary.json",
        "description": "Filtering summary - Winter residual analysis",
        "parameters": {
            "run_id": {"type": "str", "section": "S0", "description": "Recording identifier"},
            "identity.timestamp": {"type": "str", "section": "S0", "description": "Filtering timestamp"},
            "identity.pipeline_version": {"type": "str", "section": "S0", "description": "Pipeline version"},
            "subject_metadata.mass_kg": {"type": "float", "section": "S0", "description": "Subject mass (kg)"},
            "subject_metadata.height_cm": {"type": "float", "section": "S0", "description": "Subject height (cm)"},
            "raw_quality.total_frames": {"type": "int", "section": "S2", "description": "Total frames"},
            "raw_quality.sampling_rate_actual": {"type": "float", "section": "S2", "description": "Sampling rate (Hz)"},
            "filter_params.filter_type": {"type": "str", "section": "S4", "description": "Filter type description"},
            "filter_params.filter_method": {"type": "str", "section": "S4", "description": "Filter method name"},
            "filter_params.filter_cutoff_hz": {"type": "float", "section": "S4", "description": "Cutoff frequency (Hz)"},
            "filter_params.filter_range_hz": {"type": "list", "section": "S4", "description": "Filter range [min, max] Hz"},
            "filter_params.filter_order": {"type": "int", "section": "S4", "description": "Butterworth filter order"},
            "filter_params.winter_analysis_failed": {"type": "bool", "section": "S4", "description": "Whether Winter analysis failed"},
            "filter_params.biomechanical_guardrails.enabled": {"type": "bool", "section": "S4", "description": "Guardrails enabled"},
        }
    },
    "step_05": {
        "file_suffix": "__reference_summary.json",
        "description": "Reference detection - static pose alignment",
        "parameters": {
            "run_id": {"type": "str", "section": "S0", "description": "Recording identifier"},
            "subject_context.height_cm": {"type": "float", "section": "S0", "description": "Estimated height (cm)"},
            "subject_context.scaling_factor": {"type": "float", "section": "S0", "description": "Scaling factor applied"},
            "static_offset_audit.Left.measured_angle_deg": {"type": "float", "section": "S1", "description": "Left shoulder offset (deg)"},
            "static_offset_audit.Right.measured_angle_deg": {"type": "float", "section": "S1", "description": "Right shoulder offset (deg)"},
            "window_metadata.start_time_sec": {"type": "float", "section": "S5", "description": "Reference window start (sec)"},
            "window_metadata.end_time_sec": {"type": "float", "section": "S5", "description": "Reference window end (sec)"},
            "window_metadata.variance_score": {"type": "float", "section": "S5", "description": "Window stability score"},
            "window_metadata.ref_quality_score": {"type": "float", "section": "S5", "description": "Reference quality score"},
            "window_metadata.confidence_level": {"type": "str", "section": "S5", "description": "Confidence level (HIGH/MEDIUM/LOW)"},
            "window_metadata.detection_method": {"type": "str", "section": "S5", "description": "Detection method used"},
            "metadata.grade": {"type": "str", "section": "S5", "description": "Reference grade"},
            "metadata.status": {"type": "str", "section": "S5", "description": "Reference status (LOCKED/PROVISIONAL)"},
        }
    },
    "step_06": {
        "file_suffix": "__kinematics_summary.json",
        "description": "Kinematics summary - angular velocities and outliers",
        "parameters": {
            "run_id": {"type": "str", "section": "S0", "description": "Recording identifier"},
            "overall_status": {"type": "str", "section": "S8", "description": "Overall pipeline status (PASS/FAIL)"},
            "metrics.angular_velocity.max": {"type": "float", "section": "S6", "description": "Max angular velocity (deg/s)"},
            "metrics.angular_velocity.limit": {"type": "float", "section": "S6", "description": "Angular velocity limit"},
            "metrics.angular_accel.max": {"type": "float", "section": "S6", "description": "Max angular acceleration (deg/s²)"},
            "metrics.linear_accel.max": {"type": "float", "section": "S6", "description": "Max linear acceleration (mm/s²)"},
            "signal_quality.avg_residual_rms": {"type": "float", "section": "S7", "description": "Average residual RMS"},
            "signal_quality.max_quat_norm_err": {"type": "float", "section": "S2", "description": "Max quaternion normalization error"},
            "movement_metrics.path_length_mm": {"type": "float", "section": "S6", "description": "Total path length (mm)"},
            "movement_metrics.intensity_index": {"type": "float", "section": "S6", "description": "Movement intensity index"},
            "outlier_analysis.counts.total_outliers": {"type": "int", "section": "S6", "description": "Total outlier frames"},
            "outlier_analysis.percentages.total_outliers": {"type": "float", "section": "S6", "description": "Outlier percentage"},
            "outlier_analysis.consecutive_runs.max_consecutive_any_outlier": {"type": "int", "section": "S6", "description": "Max consecutive outliers"},
            "pipeline_params.sg_window_sec": {"type": "float", "section": "S6", "description": "Savitzky-Golay window (sec)"},
            "pipeline_params.fs_target": {"type": "float", "section": "S2", "description": "Target sampling rate"},
        }
    }
}

# Section descriptions for documentation
SECTION_DESCRIPTIONS = {
    "S0": "Data Lineage & Provenance",
    "S1": "Rácz Calibration Layer",
    "S2": "Temporal Quality & Sampling",
    "S3": "Gap & Interpolation Transparency",
    "S4": "Winter's Residual Validation",
    "S5": "Reference Detection & Stability",
    "S6": "Biomechanics & Outlier Analysis",
    "S7": "Signal-to-Noise Quantification",
    "S8": "Decision Matrix"
}


# ============================================================
# SAFE ACCESS UTILITIES
# ============================================================

def safe_get(d: dict, *keys, default='N/A') -> Any:
    """
    Safe nested dictionary access with default fallback.
    
    Args:
        d: Dictionary to access
        *keys: Sequence of keys for nested access
        default: Default value if key not found
        
    Returns:
        Value at nested path or default
    """
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, {})
        else:
            return default
    return d if (d != {} and d is not None) else default


def safe_get_path(d: dict, path: str, default='N/A') -> Any:
    """
    Safe nested dictionary access using dot-notation path.
    
    Args:
        d: Dictionary to access
        path: Dot-separated path (e.g., "identity.run_id")
        default: Default value if path not found
        
    Returns:
        Value at path or default
    """
    keys = path.split('.')
    return safe_get(d, *keys, default=default)


def safe_float(x, default=0.0) -> float:
    """
    Convert to float safely, handling %, None, N/A.
    
    Args:
        x: Value to convert
        default: Default if conversion fails
        
    Returns:
        Float value
    """
    if x is None or x == 'N/A':
        return default
    try:
        if isinstance(x, str):
            x = x.replace('%', '').strip()
        return float(x)
    except (ValueError, TypeError):
        return default


def safe_int(x, default=0) -> int:
    """Convert to int safely."""
    try:
        return int(safe_float(x, default))
    except (ValueError, TypeError):
        return default


# ============================================================
# FILE DISCOVERY & LOADING
# ============================================================

def discover_json_files(deriv_root: str) -> Dict[str, Dict[str, str]]:
    """
    Discover all valid JSON summary files grouped by run_id.
    
    Args:
        deriv_root: Path to derivatives folder
        
    Returns:
        Dict mapping run_id -> {step_name: file_path}
    """
    # Scan for all JSON files
    json_files = glob.glob(os.path.join(deriv_root, "**", "*.json"), recursive=True)
    
    # Filter out archive folder
    json_files = [f for f in json_files if "archive" not in f.lower()]
    
    # Group by run_id and step
    runs = defaultdict(dict)
    
    for json_path in json_files:
        filename = os.path.basename(json_path)
        
        # Match against known suffixes
        for step_name, step_info in PARAMETER_SCHEMA.items():
            suffix = step_info["file_suffix"]
            if filename.endswith(suffix):
                run_id = filename.replace(suffix, "")
                runs[run_id][step_name] = json_path
                break
    
    return dict(runs)


def load_json_safe(filepath: str) -> Optional[dict]:
    """
    Load JSON file with error handling.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Parsed JSON dict or None on error
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load {filepath}: {e}")
        return None


def load_all_runs(deriv_root: str) -> Dict[str, Dict[str, dict]]:
    """
    Load all JSON data for all runs.
    
    Args:
        deriv_root: Path to derivatives folder
        
    Returns:
        Dict mapping run_id -> {step_name: json_data}
    """
    file_map = discover_json_files(deriv_root)
    
    runs_data = {}
    for run_id, files in file_map.items():
        runs_data[run_id] = {}
        for step_name, filepath in files.items():
            data = load_json_safe(filepath)
            if data:
                runs_data[run_id][step_name] = data
    
    return runs_data


def filter_complete_runs(runs_data: Dict[str, Dict[str, dict]], 
                         required_steps: List[str] = None) -> Dict[str, Dict[str, dict]]:
    """
    Filter to runs that have all required steps.
    
    Args:
        runs_data: All loaded run data
        required_steps: List of required step names (default: step_01, step_06)
        
    Returns:
        Filtered dict with only complete runs
    """
    if required_steps is None:
        required_steps = ["step_01", "step_06"]
    
    return {
        run_id: steps 
        for run_id, steps in runs_data.items()
        if all(step in steps for step in required_steps)
    }


# ============================================================
# PARAMETER EXTRACTION
# ============================================================

def extract_all_parameters(run_id: str, steps: Dict[str, dict]) -> Dict[str, Any]:
    """
    Extract all parameters from a run's JSON files.
    
    Args:
        run_id: The run identifier
        steps: Dict of step_name -> json_data
        
    Returns:
        Flat dict of all extracted parameters with metadata
    """
    extracted = {"run_id": run_id}
    
    for step_name, step_schema in PARAMETER_SCHEMA.items():
        step_data = steps.get(step_name, {})
        
        for param_path, param_info in step_schema["parameters"].items():
            # Create unique key
            key = f"{step_name}.{param_path}"
            
            # Extract value
            value = safe_get_path(step_data, param_path)
            
            extracted[key] = {
                "value": value,
                "type": param_info["type"],
                "section": param_info["section"],
                "description": param_info["description"],
                "found": value != 'N/A'
            }
    
    return extracted


def extract_parameters_flat(run_id: str, steps: Dict[str, dict]) -> Dict[str, Any]:
    """
    Extract all parameters as a flat dict (values only).
    
    Args:
        run_id: The run identifier
        steps: Dict of step_name -> json_data
        
    Returns:
        Flat dict of parameter_key -> value
    """
    flat = {"Run_ID": run_id}
    
    for step_name, step_schema in PARAMETER_SCHEMA.items():
        step_data = steps.get(step_name, {})
        
        for param_path, param_info in step_schema["parameters"].items():
            # Create readable key
            key = f"{step_name}_{param_path}".replace(".", "_")
            
            # Extract value
            value = safe_get_path(step_data, param_path)
            flat[key] = value
    
    return flat


# ============================================================
# QUALITY SCORING FUNCTIONS
# ============================================================

def score_calibration(steps: Dict[str, dict]) -> float:
    """Score calibration quality (0-100)."""
    s01 = steps.get("step_01", {})
    s02 = steps.get("step_02", {})
    s05 = steps.get("step_05", {})
    
    score = 100.0
    
    # OptiTrack error
    optitrack_err = safe_float(safe_get_path(s01, "raw_data_quality.optitrack_mean_error_mm"))
    if optitrack_err > 1.0:
        score -= 20
    
    # Bone stability
    bone_cv = safe_float(safe_get_path(s02, "bone_qc_mean_cv"))
    if bone_cv > 1.5:
        score -= 30
    elif bone_cv > 1.0:
        score -= 15
    elif bone_cv > 0.5:
        score -= 5
    
    # Static offset
    left_offset = safe_float(safe_get_path(s05, "static_offset_audit.Left.measured_angle_deg"))
    right_offset = safe_float(safe_get_path(s05, "static_offset_audit.Right.measured_angle_deg"))
    max_offset = max(abs(left_offset), abs(right_offset))
    if max_offset > 15:
        score -= 20
    elif max_offset > 10:
        score -= 10
    
    return max(0, score)


def score_temporal_quality(steps: Dict[str, dict]) -> float:
    """Score temporal/sampling quality (0-100)."""
    s01 = steps.get("step_01", {})
    
    score = 100.0
    
    # Check sampling rate (expect ~120 Hz)
    fs = safe_float(safe_get_path(s01, "raw_data_quality.sampling_rate_actual"))
    if fs < 115 or fs > 125:
        score -= 20
    
    # Check duration (minimum viable)
    duration = safe_float(safe_get_path(s01, "duration_sec"))
    if duration < 30:
        score -= 30
    elif duration < 60:
        score -= 10
    
    return max(0, score)


def score_interpolation(steps: Dict[str, dict]) -> float:
    """Score interpolation/gap filling quality (0-100)."""
    s02 = steps.get("step_02", {})
    
    score = 100.0
    
    # Missing data percentage
    raw_missing = safe_float(safe_get_path(s02, "raw_missing_percent"))
    if raw_missing > 5:
        score -= 40
    elif raw_missing > 2:
        score -= 20
    elif raw_missing > 0.5:
        score -= 10
    
    # Interpolation method penalty
    method = safe_get_path(s02, "interpolation_method", default="")
    if "linear" in str(method).lower() and "quaternion" not in str(method).lower():
        score -= 10  # Linear fallback penalty
    
    return max(0, score)


def score_filtering(steps: Dict[str, dict]) -> float:
    """Score filtering quality based on Winter analysis (0-100)."""
    s04 = steps.get("step_04", {})
    
    score = 100.0
    
    # Check if Winter analysis succeeded
    winter_failed = safe_get_path(s04, "filter_params.winter_analysis_failed")
    if winter_failed:
        score -= 30
    
    # Check cutoff is in reasonable range (4-12 Hz for dance)
    cutoff = safe_float(safe_get_path(s04, "filter_params.filter_cutoff_hz"))
    if cutoff < 4 or cutoff > 12:
        score -= 20
    
    # Check guardrails enabled
    guardrails = safe_get_path(s04, "filter_params.biomechanical_guardrails.enabled")
    if not guardrails:
        score -= 10
    
    return max(0, score)


def score_reference(steps: Dict[str, dict]) -> float:
    """Score reference detection quality (0-100)."""
    s05 = steps.get("step_05", {})
    
    score = 100.0
    
    # Reference quality score
    ref_quality = safe_float(safe_get_path(s05, "window_metadata.ref_quality_score"))
    if ref_quality < 0.5:
        score -= 40
    elif ref_quality < 0.7:
        score -= 20
    elif ref_quality < 0.8:
        score -= 10
    
    # Confidence level
    confidence = safe_get_path(s05, "window_metadata.confidence_level")
    if confidence == "LOW":
        score -= 20
    elif confidence == "MEDIUM":
        score -= 10
    
    # Grade
    grade = safe_get_path(s05, "metadata.grade")
    if grade == "LOW":
        score -= 20
    
    return max(0, score)


def score_biomechanics(steps: Dict[str, dict]) -> float:
    """Score biomechanical plausibility (0-100)."""
    s06 = steps.get("step_06", {})
    
    score = 100.0
    
    # Overall status
    status = safe_get_path(s06, "overall_status")
    if status == "FAIL":
        score -= 50
    
    # Outlier percentage
    outlier_pct = safe_float(safe_get_path(s06, "outlier_analysis.percentages.total_outliers"))
    if outlier_pct > 5:
        score -= 30
    elif outlier_pct > 2:
        score -= 15
    elif outlier_pct > 1:
        score -= 5
    
    # Max angular velocity check
    max_ang_vel = safe_float(safe_get_path(s06, "metrics.angular_velocity.max"))
    limit = safe_float(safe_get_path(s06, "metrics.angular_velocity.limit"), default=1500)
    if max_ang_vel > limit:
        score -= 20
    
    return max(0, score)


def score_signal_quality(steps: Dict[str, dict]) -> float:
    """Score signal quality (0-100)."""
    s06 = steps.get("step_06", {})
    
    score = 100.0
    
    # Residual RMS (lower is better)
    rms = safe_float(safe_get_path(s06, "signal_quality.avg_residual_rms"))
    if rms > 20:
        score -= 30
    elif rms > 15:
        score -= 20
    elif rms > 10:
        score -= 10
    
    # Quaternion norm error
    quat_err = safe_float(safe_get_path(s06, "signal_quality.max_quat_norm_err"))
    if quat_err > 0.01:
        score -= 20
    elif quat_err > 0.001:
        score -= 10
    
    return max(0, score)


def compute_overall_score(steps: Dict[str, dict]) -> Tuple[float, str, Dict[str, float]]:
    """
    Compute overall quality score from all components.
    
    Args:
        steps: Dict of step_name -> json_data
        
    Returns:
        Tuple of (overall_score, decision, component_scores)
    """
    # Weights (sum to 1.0)
    weights = {
        "calibration": 0.15,
        "temporal": 0.10,
        "interpolation": 0.15,
        "filtering": 0.10,
        "reference": 0.15,
        "biomechanics": 0.15,
        "signal": 0.20
    }
    
    # Compute component scores
    component_scores = {
        "calibration": score_calibration(steps),
        "temporal": score_temporal_quality(steps),
        "interpolation": score_interpolation(steps),
        "filtering": score_filtering(steps),
        "reference": score_reference(steps),
        "biomechanics": score_biomechanics(steps),
        "signal": score_signal_quality(steps)
    }
    
    # Weighted sum
    overall = sum(
        component_scores[k] * weights[k] 
        for k in weights
    )
    
    # Decision thresholds
    if overall >= 80:
        decision = "ACCEPT"
    elif overall >= 60:
        decision = "REVIEW"
    else:
        decision = "REJECT"
    
    return round(overall, 2), decision, component_scores


# ============================================================
# AGGREGATED METRICS EXTRACTION
# ============================================================

def build_quality_row(run_id: str, steps: Dict[str, dict]) -> Dict[str, Any]:
    """
    Build a single row of quality metrics for a run.
    
    Args:
        run_id: The run identifier
        steps: Dict of step_name -> json_data
        
    Returns:
        Dict with all quality metrics
    """
    s01 = steps.get("step_01", {})
    s02 = steps.get("step_02", {})
    s04 = steps.get("step_04", {})
    s05 = steps.get("step_05", {})
    s06 = steps.get("step_06", {})
    
    # Compute scores
    overall_score, decision, component_scores = compute_overall_score(steps)
    
    # Parse run_id for subject info
    parts = run_id.split('_')
    subject_id = parts[0] if len(parts) > 0 else 'N/A'
    session_id = parts[1] if len(parts) > 1 else 'N/A'
    
    return {
        # Identity
        "Run_ID": run_id,
        "Subject_ID": subject_id,
        "Session_ID": session_id,
        "Processing_Date": safe_get_path(s01, "identity.processing_timestamp"),
        "Pipeline_Version": safe_get_path(s01, "identity.pipeline_version"),
        
        # Raw Data Quality
        "Total_Frames": safe_int(safe_get_path(s01, "raw_data_quality.total_frames")),
        "Duration_Sec": round(safe_float(safe_get_path(s01, "duration_sec")), 1),
        "Sampling_Rate_Hz": round(safe_float(safe_get_path(s01, "raw_data_quality.sampling_rate_actual")), 2),
        "OptiTrack_Error_mm": round(safe_float(safe_get_path(s01, "raw_data_quality.optitrack_mean_error_mm")), 3),
        
        # Preprocessing
        "Raw_Missing_%": round(safe_float(safe_get_path(s02, "raw_missing_percent")), 2),
        "Bone_CV_%": round(safe_float(safe_get_path(s02, "bone_qc_mean_cv")), 3),
        "Bone_Status": safe_get_path(s02, "bone_qc_status"),
        "Worst_Bone": safe_get_path(s02, "worst_bone"),
        "Interpolation_Method": safe_get_path(s02, "interpolation_method"),
        
        # Filtering
        "Filter_Cutoff_Hz": round(safe_float(safe_get_path(s04, "filter_params.filter_cutoff_hz")), 1),
        "Filter_Method": safe_get_path(s04, "filter_params.filter_method"),
        "Winter_Failed": safe_get_path(s04, "filter_params.winter_analysis_failed"),
        
        # Reference
        "Ref_Quality_Score": round(safe_float(safe_get_path(s05, "window_metadata.ref_quality_score")), 3),
        "Ref_Confidence": safe_get_path(s05, "window_metadata.confidence_level"),
        "Left_Offset_Deg": round(safe_float(safe_get_path(s05, "static_offset_audit.Left.measured_angle_deg")), 2),
        "Right_Offset_Deg": round(safe_float(safe_get_path(s05, "static_offset_audit.Right.measured_angle_deg")), 2),
        
        # Kinematics
        "Pipeline_Status": safe_get_path(s06, "overall_status"),
        "Max_Ang_Vel_deg_s": round(safe_float(safe_get_path(s06, "metrics.angular_velocity.max")), 2),
        "Max_Ang_Accel": round(safe_float(safe_get_path(s06, "metrics.angular_accel.max")), 2),
        "Max_Lin_Accel": round(safe_float(safe_get_path(s06, "metrics.linear_accel.max")), 2),
        "Outlier_Frames": safe_int(safe_get_path(s06, "outlier_analysis.counts.total_outliers")),
        "Outlier_%": round(safe_float(safe_get_path(s06, "outlier_analysis.percentages.total_outliers")), 3),
        "Residual_RMS": round(safe_float(safe_get_path(s06, "signal_quality.avg_residual_rms")), 3),
        "Quat_Norm_Err": round(safe_float(safe_get_path(s06, "signal_quality.max_quat_norm_err")), 6),
        "Path_Length_mm": round(safe_float(safe_get_path(s06, "movement_metrics.path_length_mm")), 1),
        "Intensity_Index": round(safe_float(safe_get_path(s06, "movement_metrics.intensity_index")), 3),
        
        # Scores
        "Quality_Score": overall_score,
        "Research_Decision": decision,
        "Score_Calibration": component_scores["calibration"],
        "Score_Temporal": component_scores["temporal"],
        "Score_Interpolation": component_scores["interpolation"],
        "Score_Filtering": component_scores["filtering"],
        "Score_Reference": component_scores["reference"],
        "Score_Biomechanics": component_scores["biomechanics"],
        "Score_Signal": component_scores["signal"]
    }


# ============================================================
# EXCEL EXPORT UTILITIES
# ============================================================

def export_to_excel(
    runs_data: Dict[str, Dict[str, dict]],
    output_path: str,
    project_root: str
) -> str:
    """
    Export complete audit report to Excel with 4 sheets.
    
    Args:
        runs_data: Dict of run_id -> {step_name: json_data}
        output_path: Path for output Excel file
        project_root: Project root for git hash
        
    Returns:
        Path to created Excel file
    """
    # Build all data structures
    quality_rows = []
    parameter_rows = []
    
    for run_id, steps in runs_data.items():
        quality_rows.append(build_quality_row(run_id, steps))
        parameter_rows.append(extract_parameters_flat(run_id, steps))
    
    # Create DataFrames
    df_quality = pd.DataFrame(quality_rows)
    df_quality = df_quality.sort_values("Quality_Score", ascending=False).reset_index(drop=True)
    
    df_params = pd.DataFrame(parameter_rows)
    
    # Build schema DataFrame
    schema_rows = []
    for step_name, step_info in PARAMETER_SCHEMA.items():
        for param_path, param_info in step_info["parameters"].items():
            schema_rows.append({
                "Step": step_name,
                "Parameter_Path": param_path,
                "Type": param_info["type"],
                "Section": param_info["section"],
                "Section_Name": SECTION_DESCRIPTIONS.get(param_info["section"], ""),
                "Description": param_info["description"]
            })
    df_schema = pd.DataFrame(schema_rows)
    
    # Get git hash
    try:
        git_hash = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=project_root
        ).decode('ascii').strip()
    except:
        git_hash = "unknown"
    
    # Write to Excel
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Formats
        title_fmt = workbook.add_format({
            'bold': True, 'font_size': 16, 
            'bg_color': '#2E75B6', 'font_color': 'white'
        })
        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#4472C4', 
            'font_color': 'white', 'text_wrap': True
        })
        green_fmt = workbook.add_format({
            'bg_color': '#C6EFCE', 'font_color': '#006100'
        })
        yellow_fmt = workbook.add_format({
            'bg_color': '#FFEB9C', 'font_color': '#9C6500'
        })
        red_fmt = workbook.add_format({
            'bg_color': '#FFC7CE', 'font_color': '#9C0006'
        })
        
        # ============================================================
        # SHEET 1: EXECUTIVE SUMMARY
        # ============================================================
        exec_sheet = workbook.add_worksheet('Executive_Summary')
        
        exec_sheet.merge_range('A1:E1', 'MASTER QUALITY AUDIT - EXECUTIVE SUMMARY', title_fmt)
        exec_sheet.write('A2', f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        exec_sheet.write('A3', f"Git Hash: {git_hash}")
        
        row = 5
        
        # Dataset Overview
        exec_sheet.merge_range(row, 0, row, 4, 'DATASET OVERVIEW', header_fmt)
        row += 1
        
        total_runs = len(df_quality)
        accept_count = (df_quality['Research_Decision'] == 'ACCEPT').sum()
        review_count = (df_quality['Research_Decision'] == 'REVIEW').sum()
        reject_count = (df_quality['Research_Decision'] == 'REJECT').sum()
        
        exec_sheet.write(row, 0, 'Total Recordings:')
        exec_sheet.write(row, 1, total_runs)
        row += 1
        
        exec_sheet.write(row, 0, 'Accepted:')
        exec_sheet.write(row, 1, accept_count)
        exec_sheet.write(row, 2, f"{accept_count/total_runs*100:.1f}%" if total_runs > 0 else "0%")
        exec_sheet.write(row, 3, 'ACCEPT', green_fmt)
        row += 1
        
        exec_sheet.write(row, 0, 'Need Review:')
        exec_sheet.write(row, 1, review_count)
        exec_sheet.write(row, 2, f"{review_count/total_runs*100:.1f}%" if total_runs > 0 else "0%")
        exec_sheet.write(row, 3, 'REVIEW', yellow_fmt)
        row += 1
        
        exec_sheet.write(row, 0, 'Rejected:')
        exec_sheet.write(row, 1, reject_count)
        exec_sheet.write(row, 2, f"{reject_count/total_runs*100:.1f}%" if total_runs > 0 else "0%")
        exec_sheet.write(row, 3, 'REJECT', red_fmt)
        row += 2
        
        # Quality Score Stats
        exec_sheet.merge_range(row, 0, row, 4, 'QUALITY SCORE STATISTICS', header_fmt)
        row += 1
        
        exec_sheet.write(row, 0, 'Mean Score:')
        exec_sheet.write(row, 1, f"{df_quality['Quality_Score'].mean():.2f}")
        row += 1
        exec_sheet.write(row, 0, 'Min Score:')
        exec_sheet.write(row, 1, f"{df_quality['Quality_Score'].min():.2f}")
        row += 1
        exec_sheet.write(row, 0, 'Max Score:')
        exec_sheet.write(row, 1, f"{df_quality['Quality_Score'].max():.2f}")
        row += 2
        
        # Component Scores Summary
        exec_sheet.merge_range(row, 0, row, 4, 'COMPONENT SCORES (MEAN)', header_fmt)
        row += 1
        
        for score_col in ['Score_Calibration', 'Score_Temporal', 'Score_Interpolation',
                          'Score_Filtering', 'Score_Reference', 'Score_Biomechanics', 'Score_Signal']:
            label = score_col.replace('Score_', '')
            exec_sheet.write(row, 0, f'{label}:')
            exec_sheet.write(row, 1, f"{df_quality[score_col].mean():.1f}")
            row += 1
        
        exec_sheet.set_column('A:A', 25)
        exec_sheet.set_column('B:E', 15)
        
        # ============================================================
        # SHEET 2: QUALITY REPORT
        # ============================================================
        df_quality.to_excel(writer, index=False, sheet_name='Quality_Report')
        
        ws_quality = writer.sheets['Quality_Report']
        for col_num, value in enumerate(df_quality.columns):
            ws_quality.write(0, col_num, value, header_fmt)
        
        # Conditional formatting for decision column
        decision_col = df_quality.columns.get_loc('Research_Decision')
        for row_num in range(1, len(df_quality) + 1):
            decision = df_quality.iloc[row_num-1]['Research_Decision']
            fmt = green_fmt if decision == 'ACCEPT' else (yellow_fmt if decision == 'REVIEW' else red_fmt)
            ws_quality.write(row_num, decision_col, decision, fmt)
        
        # Auto-fit columns
        for i, col in enumerate(df_quality.columns):
            max_len = max(df_quality[col].astype(str).str.len().max(), len(str(col)))
            ws_quality.set_column(i, i, min(max_len + 2, 40))
        
        # ============================================================
        # SHEET 3: PARAMETER AUDIT
        # ============================================================
        df_params.to_excel(writer, index=False, sheet_name='Parameter_Audit')
        
        ws_params = writer.sheets['Parameter_Audit']
        for col_num, value in enumerate(df_params.columns):
            ws_params.write(0, col_num, value, header_fmt)
        
        for i, col in enumerate(df_params.columns):
            max_len = max(df_params[col].astype(str).str.len().max(), len(str(col)))
            ws_params.set_column(i, i, min(max_len + 2, 50))
        
        # ============================================================
        # SHEET 4: PARAMETER SCHEMA
        # ============================================================
        df_schema.to_excel(writer, index=False, sheet_name='Parameter_Schema')
        
        ws_schema = writer.sheets['Parameter_Schema']
        for col_num, value in enumerate(df_schema.columns):
            ws_schema.write(0, col_num, value, header_fmt)
        
        for i, col in enumerate(df_schema.columns):
            max_len = max(df_schema[col].astype(str).str.len().max(), len(str(col)))
            ws_schema.set_column(i, i, min(max_len + 2, 60))
    
    return output_path


# ============================================================
# SCHEMA EXPORT UTILITIES
# ============================================================

def export_schema_json(output_path: str) -> str:
    """Export parameter schema to JSON file."""
    schema_export = {
        "version": "2.0",
        "generated": datetime.now().isoformat(),
        "sections": SECTION_DESCRIPTIONS,
        "steps": PARAMETER_SCHEMA
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(schema_export, f, indent=2)
    
    return output_path


def export_schema_markdown(output_path: str) -> str:
    """Export parameter schema to Markdown file."""
    lines = [
        "# Parameter Schema - Master Quality Report (NB07)",
        "",
        "This document describes all JSON parameters extracted by the Master Quality Report.",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
        "## Section Overview",
        "",
        "| Section | Name | Description |",
        "|---------|------|-------------|"
    ]
    
    for section_id, section_name in SECTION_DESCRIPTIONS.items():
        lines.append(f"| {section_id} | {section_name} | Report section |")
    
    lines.extend(["", "---", ""])
    
    for step_name, step_info in PARAMETER_SCHEMA.items():
        lines.extend([
            f"## {step_name}: {step_info['description']}",
            "",
            f"**File Suffix:** `{step_info['file_suffix']}`",
            "",
            "| Parameter Path | Type | Section | Description |",
            "|----------------|------|---------|-------------|"
        ])
        
        for param_path, param_info in step_info["parameters"].items():
            lines.append(
                f"| `{param_path}` | {param_info['type']} | {param_info['section']} | {param_info['description']} |"
            )
        
        lines.extend(["", "---", ""])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return output_path


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def compute_file_hash(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    if not os.path.exists(filepath):
        return 'FILE_NOT_FOUND'
    
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        return f'ERROR: {str(e)}'


def get_git_hash(project_root: str) -> str:
    """Get current git commit hash."""
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=project_root
        ).decode('ascii').strip()
    except:
        return "unknown"


def print_section_header(title: str, width: int = 80):
    """Print a formatted section header."""
    print("=" * width)
    print(title)
    print("=" * width)
