"""
Winter Residual Analysis & Position Filtering Module

This module implements objective low-pass cutoff selection using Winter residual analysis
and zero-lag Butterworth filtering for position data only.

Pipeline placement: After resampling to perfect grid, before derivative computation.

References:
    Winter, D. A. (2009). Biomechanics and motor control of human movement. 4th ed.
    Wren et al. (2006). Efficacy of clinical gait analysis. Gait & Posture, 22(4), 295-305.
"""

import numpy as np
import pandas as pd
import logging
from typing import Tuple, List, Dict, Optional, Union
from scipy.signal import butter, filtfilt

logger = logging.getLogger(__name__)

# Import PSD validation (optional - only if module exists)
try:
    from .filter_validation import (
        validate_winter_filter_multi_signal,
        check_filter_cutoff_validity
    )
    PSD_VALIDATION_AVAILABLE = True
except ImportError:
    PSD_VALIDATION_AVAILABLE = False
    logger.warning("PSD validation module not available - validation metrics will be skipped")


# Body region definitions for per-region filtering
BODY_REGIONS = {
    'trunk': {
        'patterns': ['Pelvis', 'Spine', 'Torso', 'Hips', 'Abdomen', 'Chest', 'Back'],
        'cutoff_range': (6, 8),
        'rationale': 'Slow, constrained core movements'
    },
    'head': {
        'patterns': ['Head', 'Neck'],
        'cutoff_range': (7, 9),
        'rationale': 'Moderate dynamics, somewhat constrained'
    },
    'upper_proximal': {
        'patterns': ['Shoulder', 'Clavicle', 'Scapula', 'UpperArm'],
        'cutoff_range': (8, 10),
        'rationale': 'Moderate-fast, semi-constrained'
    },
    'upper_distal': {
        'patterns': ['Elbow', 'Forearm', 'Wrist', 'Hand', 'Finger'],
        'cutoff_range': (10, 12),
        'rationale': 'Very fast gestures, unconstrained'
    },
    'lower_proximal': {
        'patterns': ['Thigh', 'Knee', 'UpperLeg'],
        'cutoff_range': (8, 10),
        'rationale': 'Moderate-fast locomotion'
    },
    'lower_distal': {
        'patterns': ['Ankle', 'Foot', 'Toe', 'Heel', 'LowerLeg'],
        'cutoff_range': (9, 11),
        'rationale': 'Fast, ground contact impacts'
    }
}


def classify_marker_region(marker_name: str) -> str:
    """
    Classify a marker into a body region based on name patterns.
    
    Args:
        marker_name: Marker column name (e.g., 'RightHand__px')
        
    Returns:
        Region name ('trunk', 'head', 'upper_proximal', 'upper_distal', 
                     'lower_proximal', 'lower_distal', 'unknown')
    """
    # Extract base marker name (remove axis suffix)
    base_name = marker_name.replace('__px', '').replace('__py', '').replace('__pz', '')
    
    # Check each region's patterns
    for region, config in BODY_REGIONS.items():
        for pattern in config['patterns']:
            if pattern.lower() in base_name.lower():
                return region
    
    # Default to upper_distal if unknown (conservative for dance)
    logger.debug(f"Marker '{marker_name}' not matched to any region, defaulting to 'upper_distal'")
    return 'upper_distal'


def winter_residual_analysis(signal: np.ndarray, 
                       fs: float, 
                       fmin: int = 1, 
                       fmax: int = 12,
                       min_cutoff: Optional[float] = None,
                       body_region: str = "general") -> float:
    """
    Perform Winter residual analysis to determine optimal low-pass cutoff frequency.
    
    The method analyzes residual RMS across different cutoff frequencies to find the
    knee point where further filtering provides diminishing returns.
    
    Args:
        signal: Input signal array (1D)
        fs: Sampling frequency in Hz
        fmin: Minimum cutoff frequency to test (Hz)
        fmax: Maximum cutoff frequency to test (Hz) - 12Hz for dance dynamics
        min_cutoff: Biomechanically-informed minimum cutoff (Hz). If provided, 
                   Winter result will be clamped to this minimum with logging
        body_region: Body region for biomechanical context ("trunk", "distal", "general")
        
    Returns:
        Optimal cutoff frequency (Hz)
        
    Reference:
        Winter, D. A. (2009). Biomechanics and motor control of human movement.
        Note: fmax=12Hz for dance. If cutoff=fmax, method failed - investigate pipeline.
    """
    # Convert to float and detrend
    x = signal.astype(float)
    x = x - np.mean(x)
    
    # Check for completely flat signal (no variation) - this should cause failure
    if np.std(x) < 1e-10:  # Essentially zero variation
        logger.error(f"WINTER ANALYSIS FAILED: signal has no variation (std={np.std(x):.2e}). "
                    f"Cannot perform meaningful residual analysis.")
        return float(fmax)
    
    # Test cutoff frequencies
    cutoffs = np.arange(fmin, fmax + 1)
    rms_values = np.zeros(len(cutoffs))
    
    for i, fc in enumerate(cutoffs):
        # Design 2nd-order Butterworth low-pass filter
        b, a = butter(N=2, Wn=fc/(0.5*fs), btype='low')
        
        # Apply zero-lag filtering (forward-backward)
        xf = filtfilt(b, a, x)
        
        # Compute residual RMS
        residual = x - xf
        rms_values[i] = np.sqrt(np.mean(residual**2))
    
    # Enhanced knee rule: find optimal cutoff using multiple criteria
    r_floor = rms_values[-1]  # RMS at fmax
    
    # Method 1: Strict knee rule (1.05 * r_floor)
    knee_candidates_strict = np.where(rms_values <= 1.05 * r_floor)[0]
    
    # Method 2: Relaxed knee rule (1.10 * r_floor) for smooth curves
    knee_candidates_relaxed = np.where(rms_values <= 1.10 * r_floor)[0]
    
    # Method 3: Point of diminishing returns (largest relative drop)
    rms_drops = np.diff(rms_values) / rms_values[:-1]  # Relative drop between consecutive cutoffs
    best_drop_idx = np.argmax(np.abs(rms_drops)) + 1  # Index after the largest drop
    
    # Collect all candidate cutoffs from different methods
    candidates = []
    
    # Add strict knee candidates (prefer lowest)
    if len(knee_candidates_strict) > 0:
        candidates.append((cutoffs[knee_candidates_strict[0]], "strict_knee"))
    
    # Add relaxed knee candidates (prefer lowest)
    if len(knee_candidates_relaxed) > 0:
        candidates.append((cutoffs[knee_candidates_relaxed[0]], "relaxed_knee"))
    
    # Add point of diminishing returns (with minimum 4Hz constraint)
    diminishing_cutoff = max(4, cutoffs[best_drop_idx])
    if diminishing_cutoff <= 10:  # Only add if in reasonable dance range
        candidates.append((diminishing_cutoff, "diminishing_returns"))
    
    # Choose the lowest cutoff among all candidates (prefer conservative filtering)
    if candidates:
        candidates.sort(key=lambda x: x[0])  # Sort by cutoff frequency (lowest first)
        optimal_fc, method_used = candidates[0]
    else:
        # Fallback: use 6 Hz as a reasonable default for dance
        optimal_fc = 6
        method_used = "default_fallback"
    
    # Final validation: if we still get fmax, it means the data is very smooth
    if optimal_fc >= fmax - 1:
        optimal_fc = fmax
        method_used = "fmax_fallback"
        logger.error(f"WINTER ANALYSIS FAILED: cutoff = {optimal_fc} Hz (at fmax). "
                    f"This indicates data is already oversmoothed or method applied too late in pipeline. "
                    f"Expected dance cutoff: 4-10 Hz. Investigate earlier pipeline stages.")
    else:
        logger.info(f"Winter analysis: selected cutoff {optimal_fc} Hz ({method_used})")
    
    # Apply biomechanical guardrails if min_cutoff is specified
    if min_cutoff is not None:
        original_fc = optimal_fc
        optimal_fc = max(optimal_fc, min_cutoff)
        
        if optimal_fc > original_fc:
            logger.warning(f"BIOMECHANICAL GUARDRAIL: Winter cutoff {original_fc:.1f} Hz "
                          f"clamped to {optimal_fc:.1f} Hz (min_cutoff={min_cutoff:.1f} Hz) "
                          f"for {body_region} region. "
                          f"This ensures biomechanically appropriate filtering for dance kinematics.")
        else:
            logger.info(f"BIOMECHANICAL GUARDRAIL: Winter cutoff {original_fc:.1f} Hz "
                        f"within acceptable range (>= {min_cutoff:.1f} Hz) for {body_region} region.")
    
    return float(optimal_fc)


def apply_winter_filter(df: pd.DataFrame, 
                     fs: float, 
                     pos_cols: List[str], 
                     rep_col: Optional[str] = None,
                     fmax: int = 12,
                     allow_fmax: bool = False,
                     min_cutoff_trunk: Optional[float] = 6.0,
                     min_cutoff_distal: Optional[float] = 8.0,
                     use_trunk_global: bool = False,
                     per_region_filtering: bool = False) -> Tuple[pd.DataFrame, Dict]:
    """
    Apply Winter low-pass filter to position columns only.
    
    Uses Winter residual analysis to determine optimal cutoff frequency,
    then applies zero-lag 2nd-order Butterworth filtering.
    
    Args:
        df: Input DataFrame with perfect time grid
        fs: Sampling frequency in Hz
        pos_cols: List of position column names to filter
        rep_col: Representative column for cutoff analysis (optional)
        fmax: Maximum cutoff frequency for Winter analysis (Hz)
        allow_fmax: If False, raises ValueError when Winter returns fmax (method failure)
        min_cutoff_trunk: Biomechanical minimum cutoff for trunk markers (Hz)
        min_cutoff_distal: Biomechanical minimum cutoff for distal markers (Hz)
        use_trunk_global: If True, run Winter on trunk markers only and apply to all columns
        per_region_filtering: If True, apply different cutoffs per body region (recommended for dance)
        
    Returns:
        Tuple of (filtered DataFrame, metadata dict)
        
    Raises:
        ValueError: If NaNs exist in position columns or Winter analysis fails
        
    Note:
        For dance/mocap: Distal segments (hands/feet) need higher cutoffs than trunk
        because they contain faster real motion. Typical: Trunk=6-8Hz, Distal=10-12Hz
        
        Per-region filtering (new feature):
        - Trunk: 6-8 Hz (slow core movements)
        - Head: 7-9 Hz (moderate dynamics)
        - Upper proximal: 8-10 Hz (shoulders)
        - Upper distal: 10-12 Hz (hands - rapid gestures)
        - Lower proximal: 8-10 Hz (thighs, knees)
        - Lower distal: 9-11 Hz (feet, ankles)
    """
    # Ticket 10.5: Build valid position columns list and log exclusions
    pos_cols_valid = []
    excluded_cols = []
    
    for col in pos_cols:
        if col not in df.columns:
            excluded_cols.append(f"{col} (missing)")
        elif df[col].isna().any():
            excluded_cols.append(f"{col} (NaNs)")
        else:
            pos_cols_valid.append(col)
    
    if excluded_cols:
        logger.warning(f"Excluding columns with issues: {excluded_cols}")
    
    if not pos_cols_valid:
        raise ValueError(f"No valid position columns found. All {len(pos_cols)} columns excluded: {excluded_cols}")
    
    # Smart representative column selection with multi-signal fallback
    if rep_col is not None:
        if rep_col not in df.columns:
            raise ValueError(f"Representative column '{rep_col}' not found in DataFrame")
        if df[rep_col].isna().any():
            raise ValueError(f"Representative column '{rep_col}' contains NaNs")
        chosen_rep_col = rep_col
        cutoffs = [winter_residual_analysis(df[chosen_rep_col].values, fs, fmax=fmax)]
        fc = float(cutoffs[0])  # Bug fix: assign fc from cutoffs[0]
        logger.info(f"Using user-specified representative column: {chosen_rep_col}")
    else:
        # Determine analysis strategy based on use_trunk_global flag
        if use_trunk_global:
            logger.info("Using trunk-based global cutoff strategy...")
            
            # Identify trunk markers (pelvis, spine, torso)
            trunk_patterns = ['Pelvis', 'Spine', 'Torso', 'Hips', 'Abdomen', 'Chest', 'Neck']
            trunk_cols = [col for col in pos_cols_valid 
                        if any(pattern in col for pattern in trunk_patterns)]
            
            if not trunk_cols:
                logger.warning("No trunk markers found. Falling back to multi-signal analysis.")
                trunk_cols = pos_cols_valid  # Fallback to all columns
            
            logger.info(f"Trunk markers identified: {len(trunk_cols)} columns")
            
            # Compute dynamics score for trunk columns only
            col_scores = {}
            for col in trunk_cols:
                signal = df[col].values
                dynamics_score = np.nanstd(np.diff(signal))
                col_scores[col] = dynamics_score
            
            # Sort by dynamics score and pick top 3 trunk columns
            sorted_cols = sorted(col_scores.items(), key=lambda x: x[1], reverse=True)
            top_trunk_cols = [col for col, _ in sorted_cols[:3]]
            
            logger.info(f"Top 3 most dynamic trunk columns: {top_trunk_cols}")
            
            # Run Winter analysis on trunk columns with trunk minimum cutoff
            cutoffs = []
            for col in top_trunk_cols:
                cutoff = winter_residual_analysis(
                    df[col].values, fs, fmax=fmax, 
                    min_cutoff=min_cutoff_trunk, body_region="trunk"
                )
                cutoffs.append(cutoff)
                logger.info(f"  {col}: {cutoff:.1f} Hz (trunk)")
            
            # Use median trunk cutoff as global cutoff for all columns
            fc = np.median(cutoffs)
            chosen_rep_col = f"trunk_global_median({len(cutoffs)}_cols)"
            
            logger.info(f"Trunk-based global cutoff: median = {fc:.1f} Hz")
            logger.info(f"Individual trunk cutoffs: {[f'{c:.1f}' for c in cutoffs]}")
            logger.info(f"Applying trunk-based cutoff to all {len(pos_cols_valid)} columns")
            
        else:
            # Standard multi-signal Winter analysis: pick top 5 most dynamic columns
            logger.info("Performing multi-signal Winter analysis...")
            
            # Compute dynamics score for each valid position column
            col_scores = {}
            for col in pos_cols_valid:
                signal = df[col].values
                # Dynamics ranking: score = nanstd(diff(x))
                dynamics_score = np.nanstd(np.diff(signal))
                col_scores[col] = dynamics_score
            
            # Sort by dynamics score (descending) and pick top 5
            sorted_cols = sorted(col_scores.items(), key=lambda x: x[1], reverse=True)
            top_5_cols = [col for col, _ in sorted_cols[:5]]
            
            logger.info(f"Top 5 most dynamic columns: {top_5_cols}")
            
            # Run Winter analysis on each of the top 5 columns with appropriate guardrails
            cutoffs = []
            for col in top_5_cols:
                # Determine if this is a trunk or distal marker
                is_trunk = any(pattern in col for pattern in ['Pelvis', 'Spine', 'Torso', 'Hips', 'Abdomen', 'Chest', 'Neck'])
                min_cutoff = min_cutoff_trunk if is_trunk else min_cutoff_distal
                body_region = "trunk" if is_trunk else "distal"
                
                cutoff = winter_residual_analysis(
                    df[col].values, fs, fmax=fmax, 
                    min_cutoff=min_cutoff, body_region=body_region
                )
                cutoffs.append(cutoff)
                logger.info(f"  {col}: {cutoff:.1f} Hz ({body_region})")
            
            # Use median cutoff as global cutoff
            fc = np.median(cutoffs)
            chosen_rep_col = f"multi_signal_median({len(cutoffs)}_cols)"
            
            logger.info(f"Multi-signal Winter analysis: median cutoff = {fc:.1f} Hz")
            logger.info(f"Individual cutoffs: {[f'{c:.1f}' for c in cutoffs]}")
    
    # PER-REGION FILTERING (NEW FEATURE)
    if per_region_filtering:
        logger.info("=== PER-REGION FILTERING ENABLED ===")
        logger.info("Classifying markers by body region and applying region-specific cutoffs...")
        
        # Classify all markers by region
        marker_regions = {}
        region_columns = {region: [] for region in BODY_REGIONS.keys()}
        region_columns['unknown'] = []
        
        for col in pos_cols_valid:
            region = classify_marker_region(col)
            marker_regions[col] = region
            if region in region_columns:
                region_columns[region].append(col)
            else:
                region_columns['unknown'].append(col)
        
        # Log region classification
        for region, cols in region_columns.items():
            if cols:
                logger.info(f"  {region}: {len(cols)} markers")
        
        # Apply Winter analysis per region
        df_out = df.copy()
        region_cutoffs = {}
        
        for region, cols in region_columns.items():
            if not cols or region == 'unknown':
                continue
            
            # Get region configuration
            region_config = BODY_REGIONS.get(region, {'cutoff_range': (8, 12), 'rationale': 'default'})
            min_cutoff_region, max_cutoff_region = region_config['cutoff_range']
            
            # Select representative column for this region (most dynamic)
            col_scores = {col: np.nanstd(np.diff(df[col].values)) for col in cols}
            rep_col_region = max(col_scores, key=col_scores.get)
            
            # Run Winter analysis
            fc_region = winter_residual_analysis(
                df[rep_col_region].values, fs, fmax=fmax,
                min_cutoff=min_cutoff_region, body_region=region
            )
            
            # Clamp to region-specific range
            fc_region = np.clip(fc_region, min_cutoff_region, max_cutoff_region)
            region_cutoffs[region] = fc_region
            
            logger.info(f"  {region}: cutoff={fc_region:.1f} Hz (range: {min_cutoff_region}-{max_cutoff_region} Hz, "
                       f"rep_col={rep_col_region.split('__')[0]})")
            
            # Design and apply filter for this region
            b_region, a_region = butter(N=2, Wn=fc_region/(0.5*fs), btype='low')
            
            for col in cols:
                df_out[col] = filtfilt(b_region, a_region, df[col].values.astype(float))
        
        # Handle unknown markers with median cutoff
        if region_columns['unknown']:
            median_cutoff = np.median(list(region_cutoffs.values()))
            logger.warning(f"  unknown: {len(region_columns['unknown'])} markers, using median cutoff={median_cutoff:.1f} Hz")
            b_unknown, a_unknown = butter(N=2, Wn=median_cutoff/(0.5*fs), btype='low')
            for col in region_columns['unknown']:
                df_out[col] = filtfilt(b_unknown, a_unknown, df[col].values.astype(float))
            region_cutoffs['unknown'] = median_cutoff
        
        # Update metadata for per-region filtering
        metadata = {
            "filtering_mode": "per_region",
            "region_cutoffs": region_cutoffs,
            "marker_regions": marker_regions,
            "n_regions": len([r for r in region_cutoffs.keys() if r != 'unknown']),
            "cutoff_range": (min(region_cutoffs.values()), max(region_cutoffs.values())),
            "fmax": fmax,
            "pos_cols_valid": pos_cols_valid,
            "pos_cols_excluded": excluded_cols,
            "total_pos_cols": len(pos_cols)
        }
        
        logger.info(f"Per-region filtering complete: {len(region_cutoffs)} regions, "
                   f"cutoff range: {metadata['cutoff_range'][0]:.1f}-{metadata['cutoff_range'][1]:.1f} Hz")
    
    else:
        # SINGLE GLOBAL CUTOFF (ORIGINAL BEHAVIOR)
        # Check for Winter analysis failure
        if not allow_fmax and fc >= fmax - 1:
            raise ValueError(f"WINTER ANALYSIS FAILED: cutoff = {fc:.1f} Hz (at fmax). "
                            f"This indicates data is already oversmoothed or method applied too late. "
                            f"Expected dance cutoff: 4-10 Hz. "
                            f"To override, set allow_fmax=True.")
        
        # Design filter with optimal cutoff
        b, a = butter(N=2, Wn=fc/(0.5*fs), btype='low')
        
        # Apply filter to valid position columns only
        df_out = df.copy()
        for col in pos_cols_valid:
            df_out[col] = filtfilt(b, a, df[col].values.astype(float))
        
        # Prepare metadata
        metadata = {
            "filtering_mode": "single_global",
            "cutoff_hz": fc,
            "rep_col": chosen_rep_col,
            "fmin": 1,
            "fmax": fmax,
            "multi_signal_analysis": rep_col is None,
            "individual_cutoffs": cutoffs if rep_col is None else [fc],
            "allow_fmax": allow_fmax,
            "pos_cols_valid": pos_cols_valid,
            "pos_cols_excluded": excluded_cols,
            "total_pos_cols": len(pos_cols),
            # Biomechanical guardrails metadata
            "biomechanical_guardrails": {
                "enabled": True,
                "min_cutoff_trunk": min_cutoff_trunk,
                "min_cutoff_distal": min_cutoff_distal,
                "use_trunk_global": use_trunk_global,
                "strategy": "trunk_global" if use_trunk_global else "multi_signal_with_guardrails"
            }
        }
    
    # Ensure quaternion columns are unchanged (both modes)
    quat_cols = [col for col in df.columns if col.endswith(('__qx', '__qy', '__qz', '__qw'))]
    for col in quat_cols:
        if col in df.columns:
            df_out[col] = df[col].values
    
    # PSD Validation (Research Validation Phase 1 - Item 1)
    if PSD_VALIDATION_AVAILABLE and not per_region_filtering:
        try:
            logger.info("Running PSD validation to verify filter quality...")
            
            # Check cutoff validity
            cutoff_validity = check_filter_cutoff_validity(fc, fs, fmax)
            metadata['cutoff_validity'] = cutoff_validity
            
            # Validate filter performance on sample of signals
            psd_validation = validate_winter_filter_multi_signal(
                df, df_out, pos_cols_valid, fs, fc, n_samples=5
            )
            metadata['psd_validation'] = psd_validation
            
            logger.info(f"PSD Validation Complete: Dance preservation={psd_validation.get('dance_preservation_mean', 0):.1f}%, "
                       f"Filter quality={psd_validation.get('overall_filter_quality', 'UNKNOWN')}")
            
        except Exception as e:
            logger.warning(f"PSD validation failed: {e}")
            metadata['psd_validation'] = {'status': 'ERROR', 'error': str(e)}
    else:
        if per_region_filtering:
            logger.info("PSD validation skipped (per-region filtering - validate per region separately)")
        else:
            logger.info("PSD validation skipped (module not available)")
        metadata['psd_validation'] = {'status': 'SKIPPED', 'reason': 'per_region_mode' if per_region_filtering else 'module_not_available'}
    
    # Log completion
    if per_region_filtering:
        logger.info(f"Per-region Winter filtering complete: {len(pos_cols_valid)}/{len(pos_cols)} position columns filtered")
    else:
        logger.info(f"Winter filtering applied: cutoff={fc} Hz, {len(pos_cols_valid)}/{len(pos_cols)} position columns filtered")
    
    return df_out, metadata


def get_position_columns(df: pd.DataFrame) -> List[str]:
    """
    Extract position column names from DataFrame.
    
    Args:
        df: Input DataFrame
        
    Returns:
        List of position column names
    """
    return [col for col in df.columns if col.endswith(('__px', '__py', '__pz'))]


def get_quaternion_columns(df: pd.DataFrame) -> List[str]:
    """
    Extract quaternion column names from DataFrame.
    
    Args:
        df: Input DataFrame
        
    Returns:
        List of quaternion column names
    """
    return [col for col in df.columns if col.endswith(('__qx', '__qy', '__qz', '__qw'))]


def validate_filtering_input(df: pd.DataFrame, 
                         fs: float,
                         pos_cols: Optional[List[str]] = None) -> None:
    """
    Validate input data for filtering operations.
    
    Args:
        df: Input DataFrame
        fs: Sampling frequency
        pos_cols: Position columns to validate
        
    Raises:
        ValueError: If validation fails
    """
    if fs <= 0:
        raise ValueError(f"Sampling frequency must be positive, got {fs}")
    
    if 'time_s' not in df.columns:
        raise ValueError("DataFrame must contain 'time_s' column")
    
    if pos_cols is None:
        pos_cols = get_position_columns(df)
    
    if not pos_cols:
        raise ValueError("No position columns found for filtering")
    
    missing_cols = [col for col in pos_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Position columns not found: {missing_cols}")
    
    # Check time grid regularity (should be constant dt)
    time_diffs = np.diff(df['time_s'].values)
    if not np.allclose(time_diffs, time_diffs[0], rtol=1e-6):
        logger.warning("Time grid is not perfectly regular - filtering may be suboptimal")


def compute_filter_characteristics(fc: float, fs: float) -> Dict[str, float]:
    """
    Compute filter characteristics for documentation.
    
    Args:
        fc: Cutoff frequency in Hz
        fs: Sampling frequency in Hz
        
    Returns:
        Dictionary with filter characteristics
    """
    # Normalized cutoff frequency
    wn = fc / (0.5 * fs)
    
    # Phase delay at different frequencies (approximate for 2nd-order Butterworth)
    freqs = np.array([0.1, 0.5, 1.0, 5.0, 10.0]) * fc
    phase_delays = []
    
    for freq in freqs:
        if freq < fc:
            # Below cutoff: minimal phase delay
            phase_delay = 0.0
        else:
            # Above cutoff: increasing phase delay
            phase_delay = np.degrees(np.arctan(freq/fc))
        phase_delays.append(phase_delay)
    
    return {
        "cutoff_hz": fc,
        "normalized_wn": wn,
        "filter_order": 2,
        "phase_delay_10pct_fc": phase_delays[0] if len(phase_delays) > 0 else 0,
        "phase_delay_50pct_fc": phase_delays[1] if len(phase_delays) > 1 else 0,
        "phase_delay_fc": phase_delays[2] if len(phase_delays) > 2 else 0,
        "phase_delay_5x_fc": phase_delays[3] if len(phase_delays) > 3 else 0,
        "phase_delay_10x_fc": phase_delays[4] if len(phase_delays) > 4 else 0
    }
