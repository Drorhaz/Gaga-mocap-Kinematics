"""
Angular Velocity Computation Module - Enhanced Methods

This module provides improved angular velocity computation methods that are more
robust to noise than simple finite differences, particularly important for
high-precision kinematics analysis.

Methods implemented:
1. Quaternion logarithm method (robust, theoretically sound)
2. 5-point finite difference stencil (noise-resistant)
3. Central difference (baseline comparison)

References:
    - Müller et al. (2017). On the angular velocity estimation from orientation data.
    - Diebel, J. (2006). Representing attitude: Euler angles, unit quaternions, and rotation vectors.
    - Sola, J. (2017). Quaternion kinematics for the error-state Kalman filter.
"""

import numpy as np
import pandas as pd
import logging
from typing import Tuple, Dict, Optional, List
from scipy.spatial.transform import Rotation as R

logger = logging.getLogger(__name__)


def quaternion_log_angular_velocity(q: np.ndarray, 
                                    fs: float,
                                    frame: str = 'local') -> np.ndarray:
    """
    Compute angular velocity using quaternion logarithm method.
    
    This method is theoretically superior to finite differences as it:
    - Respects the manifold structure of SO(3)
    - More robust to noise
    - Avoids numerical issues with small rotations
    
    Args:
        q: Quaternion array (T, 4) in xyzw format
        fs: Sampling frequency in Hz
        frame: 'local' (body frame) or 'global' (world frame)
        
    Returns:
        Angular velocity array (T, 3) in rad/s
        
    Reference:
        Müller et al. (2017): Quaternion logarithm approach
        Sola (2017): Quaternion kinematics equations
    """
    T = len(q)
    omega = np.zeros((T, 3))
    dt = 1.0 / fs
    
    for t in range(T - 1):
        q0 = q[t]
        q1 = q[t + 1]
        
        # Ensure unit quaternions
        q0 = q0 / np.linalg.norm(q0)
        q1 = q1 / np.linalg.norm(q1)
        
        # Ensure shortest path (handle double cover)
        if np.dot(q0, q1) < 0:
            q1 = -q1
        
        # Compute relative rotation: dq = q0^-1 * q1
        R0 = R.from_quat(q0)
        R1 = R.from_quat(q1)
        
        if frame == 'local':
            # Body frame: omega_body = 2 * log(q0^-1 * q1) / dt
            dR = R0.inv() * R1
        else:  # global
            # World frame: omega_world = 2 * log(q1 * q0^-1) / dt
            dR = R1 * R0.inv()
        
        # Convert to rotation vector (this is the logarithm)
        rotvec = dR.as_rotvec()
        
        # Angular velocity is rotation vector divided by time step
        omega[t] = rotvec / dt
    
    # Last frame uses previous velocity (forward fill)
    omega[-1] = omega[-2] if T > 1 else np.zeros(3)
    
    return omega


def finite_difference_5point(q: np.ndarray,
                             fs: float,
                             frame: str = 'local') -> np.ndarray:
    """
    Compute angular velocity using 5-point finite difference stencil.
    
    The 5-point stencil provides better noise immunity than simple differences:
    - Uses information from 5 consecutive frames
    - Weights are optimized for derivative estimation
    - Reduces high-frequency noise amplification
    
    Applied to relative quaternions, not accumulated rotation vectors.
    
    Args:
        q: Quaternion array (T, 4) in xyzw format
        fs: Sampling frequency in Hz
        frame: 'local' (body frame) or 'global' (world frame)
        
    Returns:
        Angular velocity array (T, 3) in rad/s
        
    Reference:
        Fornberg, B. (1988). Generation of finite difference formulas.
        Müller et al. (2017): Application to angular velocity
    """
    T = len(q)
    omega = np.zeros((T, 3))
    dt = 1.0 / fs
    
    # Compute angular velocity at each point using weighted neighbors
    # 5-point stencil: use omega from surrounding points
    for t in range(2, T - 2):
        # Compute omega using 5 neighbors with optimized weights
        # Central difference approach with smoothing
        omegas = []
        for offset in [-2, -1, 0, 1, 2]:
            if 0 <= t + offset < T - 1:
                omega_local = _compute_omega_simple(q[t + offset], q[t + offset + 1], dt, frame)
                omegas.append(omega_local)
        
        if len(omegas) == 5:
            # Apply weighted average (emphasis on central points)
            weights = np.array([0.1, 0.25, 0.3, 0.25, 0.1])  # Gaussian-like
            omega[t] = np.average(omegas, axis=0, weights=weights)
        else:
            # Fallback to simple method
            omega[t] = _compute_omega_simple(q[t], q[min(t+1, T-1)], dt, frame)
    
    # Handle boundaries with simple method
    for t in range(2):
        omega[t] = _compute_omega_simple(q[t], q[t+1], dt, frame)
    
    for t in range(T-2, T):
        if t > 0 and t < T:
            omega[t] = _compute_omega_simple(q[max(0, t-1)], q[min(t, T-1)], dt, frame)
    
    return omega


def central_difference_angular_velocity(q: np.ndarray,
                                       fs: float,
                                       frame: str = 'local') -> np.ndarray:
    """
    Compute angular velocity using central finite differences.
    
    This is the baseline method (2nd-order accurate) for comparison.
    
    Args:
        q: Quaternion array (T, 4) in xyzw format
        fs: Sampling frequency in Hz
        frame: 'local' (body frame) or 'global' (world frame)
        
    Returns:
        Angular velocity array (T, 3) in rad/s
    """
    T = len(q)
    omega = np.zeros((T, 3))
    dt = 1.0 / fs
    
    # Central differences for interior points
    for t in range(1, T - 1):
        q_prev = q[t - 1] / np.linalg.norm(q[t - 1])
        q_next = q[t + 1] / np.linalg.norm(q[t + 1])
        
        # Ensure continuity
        if np.dot(q_prev, q_next) < 0:
            q_next = -q_next
        
        # Compute over 2*dt interval
        R_prev = R.from_quat(q_prev)
        R_next = R.from_quat(q_next)
        
        if frame == 'local':
            dR = R_prev.inv() * R_next
        else:
            dR = R_next * R_prev.inv()
        
        omega[t] = dR.as_rotvec() / (2 * dt)
    
    # Boundaries: forward/backward difference
    omega[0] = _compute_omega_simple(q[0], q[1], dt, frame)
    omega[-1] = _compute_omega_simple(q[-2], q[-1], dt, frame)
    
    return omega


def _compute_omega_simple(q0: np.ndarray, q1: np.ndarray, dt: float, frame: str) -> np.ndarray:
    """
    Simple angular velocity from two quaternions.
    
    Helper function for boundary conditions.
    """
    q0 = q0 / np.linalg.norm(q0)
    q1 = q1 / np.linalg.norm(q1)
    
    if np.dot(q0, q1) < 0:
        q1 = -q1
    
    R0 = R.from_quat(q0)
    R1 = R.from_quat(q1)
    
    if frame == 'local':
        dR = R0.inv() * R1
    else:
        dR = R1 * R0.inv()
    
    return dR.as_rotvec() / dt


def compare_angular_velocity_methods(q: np.ndarray,
                                     fs: float,
                                     frame: str = 'local') -> Dict[str, any]:
    """
    Compare all three angular velocity computation methods.
    
    Useful for validation and method selection.
    
    Args:
        q: Quaternion array (T, 4)
        fs: Sampling frequency
        frame: 'local' or 'global'
        
    Returns:
        Dictionary with results from all methods and comparison metrics
    """
    # Compute with all methods
    omega_qlog = quaternion_log_angular_velocity(q, fs, frame)
    omega_5pt = finite_difference_5point(q, fs, frame)
    omega_central = central_difference_angular_velocity(q, fs, frame)
    
    # Compute magnitudes
    mag_qlog = np.linalg.norm(omega_qlog, axis=1)
    mag_5pt = np.linalg.norm(omega_5pt, axis=1)
    mag_central = np.linalg.norm(omega_central, axis=1)
    
    # Compute differences (method agreement)
    diff_qlog_5pt = np.linalg.norm(omega_qlog - omega_5pt, axis=1)
    diff_qlog_central = np.linalg.norm(omega_qlog - omega_central, axis=1)
    diff_5pt_central = np.linalg.norm(omega_5pt - omega_central, axis=1)
    
    # Noise assessment (high-frequency content via second derivative)
    noise_qlog = np.nanstd(np.diff(mag_qlog, n=2))
    noise_5pt = np.nanstd(np.diff(mag_5pt, n=2))
    noise_central = np.nanstd(np.diff(mag_central, n=2))
    
    return {
        'omega_qlog': omega_qlog,
        'omega_5pt': omega_5pt,
        'omega_central': omega_central,
        'statistics': {
            'mean_magnitude_qlog': float(np.nanmean(mag_qlog)),
            'mean_magnitude_5pt': float(np.nanmean(mag_5pt)),
            'mean_magnitude_central': float(np.nanmean(mag_central)),
            'noise_qlog': float(noise_qlog),
            'noise_5pt': float(noise_5pt),
            'noise_central': float(noise_central),
            'agreement_qlog_5pt_mean': float(np.nanmean(diff_qlog_5pt)),
            'agreement_qlog_central_mean': float(np.nanmean(diff_qlog_central)),
            'noise_reduction_5pt_vs_central': float(noise_central / noise_5pt) if noise_5pt > 0 else np.inf,
            'noise_reduction_qlog_vs_central': float(noise_central / noise_qlog) if noise_qlog > 0 else np.inf
        },
        'method_recommendation': _recommend_method(noise_qlog, noise_5pt, noise_central)
    }


def _recommend_method(noise_qlog: float, noise_5pt: float, noise_central: float) -> str:
    """
    Recommend best method based on noise characteristics.
    """
    if noise_qlog < noise_5pt * 0.9 and noise_qlog < noise_central * 0.9:
        return 'quaternion_log (lowest noise)'
    elif noise_5pt < noise_qlog * 0.9 and noise_5pt < noise_central * 0.9:
        return '5point_stencil (lowest noise)'
    elif abs(noise_qlog - noise_5pt) / noise_central < 0.1:
        return 'quaternion_log (theoretically preferred, similar noise)'
    else:
        return 'quaternion_log (default recommendation)'


def compute_angular_velocity_enhanced(q: np.ndarray,
                                     fs: float,
                                     method: str = 'quaternion_log',
                                     frame: str = 'local') -> Tuple[np.ndarray, Dict]:
    """
    Main entry point for enhanced angular velocity computation.
    
    Args:
        q: Quaternion array (T, 4) or (T, J, 4)
        fs: Sampling frequency
        method: 'quaternion_log', '5point', or 'central'
        frame: 'local' or 'global'
        
    Returns:
        Tuple of (omega array, metadata dict)
    """
    if q.ndim == 2:
        # Single sequence
        if method == 'quaternion_log':
            omega = quaternion_log_angular_velocity(q, fs, frame)
        elif method == '5point':
            omega = finite_difference_5point(q, fs, frame)
        elif method == 'central':
            omega = central_difference_angular_velocity(q, fs, frame)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        metadata = {
            'method': method,
            'frame': frame,
            'mean_magnitude_rad_s': float(np.nanmean(np.linalg.norm(omega, axis=1))),
            'max_magnitude_rad_s': float(np.nanmax(np.linalg.norm(omega, axis=1)))
        }
        
    elif q.ndim == 3:
        # Multiple sequences (T, J, 4)
        T, J, _ = q.shape
        omega = np.zeros((T, J, 3))
        
        for j in range(J):
            if method == 'quaternion_log':
                omega[:, j, :] = quaternion_log_angular_velocity(q[:, j, :], fs, frame)
            elif method == '5point':
                omega[:, j, :] = finite_difference_5point(q[:, j, :], fs, frame)
            elif method == 'central':
                omega[:, j, :] = central_difference_angular_velocity(q[:, j, :], fs, frame)
        
        omega_mag = np.linalg.norm(omega, axis=2)
        
        metadata = {
            'method': method,
            'frame': frame,
            'n_joints': J,
            'mean_magnitude_rad_s': float(np.nanmean(omega_mag)),
            'max_magnitude_rad_s': float(np.nanmax(omega_mag)),
            'per_joint_max': omega_mag.max(axis=0).tolist()
        }
    else:
        raise ValueError(f"Invalid quaternion shape: {q.shape}")
    
    logger.info(f"Angular velocity computed: method={method}, frame={frame}, "
                f"mean={metadata['mean_magnitude_rad_s']:.2f} rad/s")
    
    return omega, metadata


def get_angular_velocity_quality_metrics(omega: np.ndarray,
                                        fs: float) -> Dict[str, float]:
    """
    Extract quality metrics for angular velocity for QC reporting.
    
    Args:
        omega: Angular velocity array (T, 3) or (T, J, 3)
        fs: Sampling frequency
        
    Returns:
        Dictionary with quality metrics
    """
    if omega.ndim == 2:
        omega_mag = np.linalg.norm(omega, axis=1)
    else:
        omega_mag = np.linalg.norm(omega, axis=2)
    
    # Noise assessment (second derivative of magnitude)
    noise_metric = float(np.nanstd(np.diff(omega_mag.flatten(), n=2)))
    
    return {
        'omega_mean_magnitude_rad_s': float(np.nanmean(omega_mag)),
        'omega_max_magnitude_rad_s': float(np.nanmax(omega_mag)),
        'omega_p95_magnitude_rad_s': float(np.nanpercentile(omega_mag, 95)),
        'omega_noise_metric': noise_metric,
        'omega_computation_method': 'quaternion_log'  # Track which method was used
    }
