"""
ISB Joint Angle Extraction Module

This module implements anatomical joint angle extraction using ISB (International Society of Biomechanics)
standard Euler sequences for relative joint rotations.

Pipeline placement: After filtering (Ticket 10), before joint angle analysis.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
from scipy.spatial.transform import Rotation

logger = logging.getLogger(__name__)

# ISB standard Euler sequences by joint
EULER_SEQ_BY_JOINT = {
    'Shoulder': 'yxy',  # ISB recommendation for shoulder
    'Knee': 'zxy',     # ISB recommendation for knee  
    'Elbow': 'zxy',     # ISB recommendation for elbow
    # Default for all other joints
    'default': 'zxy'
}


def get_euler_sequence(joint_name: str) -> str:
    """
    Get ISB Euler sequence for a given joint.
    
    Args:
        joint_name: Name of the joint
        
    Returns:
        Euler sequence string (e.g., 'zxy', 'yxy')
    """
    return EULER_SEQ_BY_JOINT.get(joint_name, EULER_SEQ_BY_JOINT['default'])


def extract_isb_euler(df: pd.DataFrame, 
                    joint_map: Dict[str, Dict[str, str]]) -> pd.DataFrame:
    """
    Extract ISB anatomical joint angles using relative rotations.
    
    Computes relative rotation between parent and child segments:
    R_rel = R_parent.inv() * R_child
    
    Args:
        df: DataFrame with aligned quaternion columns from Ticket 8
        joint_map: Dictionary mapping joint names to parent/child relationships
                   Format: {joint_name: {'parent': 'parent_joint', 'child': 'child_joint'}}
    
    Returns:
        DataFrame with added Euler angle columns: {joint}__e1_deg, {joint}__e2_deg, {joint}__e3_deg
        
    Raises:
        ValueError: If required quaternion columns are missing
    """
    df_out = df.copy()
    
    for joint_name, relationships in joint_map.items():
        parent_joint = relationships['parent']
        child_joint = relationships['child']
        
        # Get Euler sequence for this joint
        euler_seq = get_euler_sequence(joint_name)
        
        logger.info(f"Processing {joint_name}: {parent_joint} -> {child_joint}, sequence: {euler_seq}")
        
        # Extract aligned quaternions (from Ticket 8)
        parent_quat = _extract_aligned_quaternion(df, parent_joint)
        child_quat = _extract_aligned_quaternion(df, child_joint)
        
        # Validate inputs
        if parent_quat is None or child_quat is None:
            missing = []
            if parent_quat is None:
                missing.append(f"{parent_joint}__q_aligned")
            if child_quat is None:
                missing.append(f"{child_joint}__q_aligned")
            raise ValueError(f"Missing aligned quaternion columns: {missing}")
        
        # Convert to Rotation objects
        R_parent = Rotation.from_quat(parent_quat)
        R_child = Rotation.from_quat(child_quat)
        
        # Compute relative rotation: R_rel = R_parent.inv() * R_child
        R_rel = R_parent.inv() * R_child
        
        # Extract Euler angles in degrees
        euler_angles = R_rel.as_euler(euler_seq, degrees=True)
        
        # Store in DataFrame
        df_out[f'{joint_name}__e1_deg'] = euler_angles[:, 0]
        df_out[f'{joint_name}__e2_deg'] = euler_angles[:, 1] 
        df_out[f'{joint_name}__e3_deg'] = euler_angles[:, 2]
        
        logger.info(f"Extracted {joint_name} Euler angles: {euler_seq} sequence")
    
    return df_out


def _extract_aligned_quaternion(df: pd.DataFrame, joint_name: str) -> Optional[np.ndarray]:
    """
    Extract aligned quaternion for a joint from DataFrame.
    
    Args:
        df: DataFrame with quaternion columns
        joint_name: Name of the joint
        
    Returns:
        Quaternion array (N, 4) in xyzw order, or None if not found
    """
    # Try different suffix patterns for aligned quaternions
    suffixes = ['__q_aligned', '__qx_aligned', '__qy_aligned', '__qz_aligned', '__qw_aligned']
    
    # First try single quaternion column
    quat_col = f'{joint_name}__q_aligned'
    if quat_col in df.columns:
        return df[quat_col].values
    
    # Then try separate quaternion components
    qx_col = f'{joint_name}__qx_aligned'
    qy_col = f'{joint_name}__qy_aligned' 
    qz_col = f'{joint_name}__qz_aligned'
    qw_col = f'{joint_name}__qw_aligned'
    
    quat_cols = [qx_col, qy_col, qz_col, qw_col]
    if all(col in df.columns for col in quat_cols):
        # Combine separate components into quaternion array
        quat_array = np.column_stack([
            df[qx_col].values,
            df[qy_col].values, 
            df[qz_col].values,
            df[qw_col].values
        ])
        return quat_array
    
    # Try non-aligned quaternions as fallback
    fallback_suffixes = ['__quat', '__qx', '__qy', '__qz', '__qw']
    for suffix in fallback_suffixes:
        if suffix == '__quat':
            col = f'{joint_name}{suffix}'
        else:
            col = f'{joint_name}{suffix}'
        
        if col in df.columns:
            if suffix == '__quat':
                return df[col].values
            else:
                # Need to combine components
                base_suffix = suffix.replace('_x', '').replace('_y', '').replace('_z', '').replace('_w', '')
                qx_col = f'{joint_name}__qx'
                qy_col = f'{joint_name}__qy'
                qz_col = f'{joint_name}__qz' 
                qw_col = f'{joint_name}__qw'
                
                if all(col in df.columns for col in [qx_col, qy_col, qz_col, qw_col]):
                    quat_array = np.column_stack([
                        df[qx_col].values,
                        df[qy_col].values,
                        df[qz_col].values,
                        df[qw_col].values
                    ])
                    return quat_array
    
    logger.warning(f"No quaternion data found for joint {joint_name}")
    return None


def validate_joint_angles(df: pd.DataFrame, 
                      joint_map: Dict[str, Dict[str, str]],
                      tolerance: float = 1e-6) -> Dict[str, bool]:
    """
    Validate joint angle extraction by testing identity case.
    
    Test: If R_child == R_parent, then all 3 angles should be 0.0 ± tolerance.
    
    Args:
        df: DataFrame with joint angles
        joint_map: Joint mapping used for extraction
        tolerance: Tolerance for zero angles (degrees)
        
    Returns:
        Dictionary mapping joint names to validation results
    """
    validation_results = {}
    
    for joint_name in joint_map.keys():
        e1_col = f'{joint_name}__e1_deg'
        e2_col = f'{joint_name}__e2_deg'
        e3_col = f'{joint_name}__e3_deg'
        
        if all(col in df.columns for col in [e1_col, e2_col, e3_col]):
            e1_angles = df[e1_col].values
            e2_angles = df[e2_col].values
            e3_angles = df[e3_col].values
            
            # Check if angles are close to zero
            e1_valid = np.allclose(e1_angles, 0.0, atol=tolerance)
            e2_valid = np.allclose(e2_angles, 0.0, atol=tolerance)
            e3_valid = np.allclose(e3_angles, 0.0, atol=tolerance)
            
            validation_results[joint_name] = e1_valid and e2_valid and e3_valid
            
            if not validation_results[joint_name]:
                logger.warning(f"Joint {joint_name} identity validation failed: "
                           f"e1_max={np.max(np.abs(e1_angles)):.2e}, "
                           f"e2_max={np.max(np.abs(e2_angles)):.2e}, "
                           f"e3_max={np.max(np.abs(e3_angles)):.2e}")
        else:
            validation_results[joint_name] = False
            logger.warning(f"Missing angle columns for joint {joint_name}")
    
    return validation_results


def get_euler_columns(joint_name: str) -> List[str]:
    """
    Get standard Euler angle column names for a joint.
    
    Args:
        joint_name: Name of the joint
        
    Returns:
        List of column names: [e1, e2, e3]
    """
    return [
        f'{joint_name}__e1_deg',
        f'{joint_name}__e2_deg',
        f'{joint_name}__e3_deg'
    ]


def get_joint_angle_summary(df: pd.DataFrame, 
                        joint_names: List[str]) -> pd.DataFrame:
    """
    Generate summary statistics for joint angles.
    
    Args:
        df: DataFrame with joint angles
        joint_names: List of joint names to summarize
        
    Returns:
        DataFrame with summary statistics for each joint
    """
    summary_data = []
    
    for joint_name in joint_names:
        euler_cols = get_euler_columns(joint_name)
        
        if all(col in df.columns for col in euler_cols):
            for i, col in enumerate(euler_cols):
                angles = df[col].values
                
                # Remove NaN values for statistics
                valid_angles = angles[~np.isnan(angles)]
                
                if len(valid_angles) > 0:
                    summary_data.append({
                        'joint': joint_name,
                        'axis': f'e{i+1}',
                        'mean_deg': np.mean(valid_angles),
                        'std_deg': np.std(valid_angles),
                        'min_deg': np.min(valid_angles),
                        'max_deg': np.max(valid_angles),
                        'range_deg': np.max(valid_angles) - np.min(valid_angles),
                        'n_samples': len(valid_angles)
                    })
                else:
                    summary_data.append({
                        'joint': joint_name,
                        'axis': f'e{i+1}',
                        'mean_deg': np.nan,
                        'std_deg': np.nan,
                        'min_deg': np.nan,
                        'max_deg': np.nan,
                        'range_deg': np.nan,
                        'n_samples': 0
                    })
    
    return pd.DataFrame(summary_data)


def check_euler_gimbal_lock(df: pd.DataFrame, 
                          joint_name: str,
                          threshold: float = 85.0) -> Dict[str, any]:
    """
    Check for potential gimbal lock conditions in Euler angles.
    
    Args:
        df: DataFrame with joint angles
        joint_name: Name of the joint to check
        threshold: Angle threshold (degrees) to flag potential gimbal lock
        
    Returns:
        Dictionary with gimbal lock analysis results
    """
    euler_cols = get_euler_columns(joint_name)
    
    if not all(col in df.columns for col in euler_cols):
        return {'error': f'Missing Euler columns for {joint_name}'}
    
    e2_angles = df[euler_cols[1]].values  # Middle angle is most prone to gimbal lock
    
    # Check for angles near ±90 degrees (gimbal lock condition)
    near_90 = np.abs(e2_angles - 90.0) < threshold
    near_minus_90 = np.abs(e2_angles + 90.0) < threshold
    
    gimbal_frames = np.where(near_90 | near_minus_90)[0]
    
    return {
        'joint': joint_name,
        'gimbal_frames': gimbal_frames,
        'n_gimbal_frames': len(gimbal_frames),
        'percentage_gimbal': 100.0 * len(gimbal_frames) / len(e2_angles),
        'e2_range': [np.min(e2_angles), np.max(e2_angles)],
        'threshold_deg': threshold
    }


def create_standard_joint_map() -> Dict[str, Dict[str, str]]:
    """
    Create a standard joint mapping for common biomechanical joints.
    
    Returns:
        Dictionary mapping joint names to parent-child relationships
    """
    return {
        'RightShoulder': {'parent': 'Thorax', 'child': 'RightUpperArm'},
        'LeftShoulder': {'parent': 'Thorax', 'child': 'LeftUpperArm'},
        'RightElbow': {'parent': 'RightUpperArm', 'child': 'RightForearm'},
        'LeftElbow': {'parent': 'LeftUpperArm', 'child': 'LeftForearm'},
        'RightKnee': {'parent': 'RightThigh', 'child': 'RightShank'},
        'LeftKnee': {'parent': 'LeftThigh', 'child': 'LeftShank'},
        'RightHip': {'parent': 'Pelvis', 'child': 'RightThigh'},
        'LeftHip': {'parent': 'Pelvis', 'child': 'LeftThigh'}
    }
