import numpy as np
from scipy.spatial.transform import Rotation as R
import logging

from .quaternion_ops import (
    quat_normalize,
    quat_shortest,
    quat_enforce_continuity,
    quat_mul,
    quat_inv,
)

logger = logging.getLogger(__name__)

# Import reference validation (optional - only if module exists)
try:
    from .reference_validation import (
        validate_reference_window,
        validate_reference_stability,
        compute_motion_profile
    )
    REF_VALIDATION_AVAILABLE = True
except ImportError:
    REF_VALIDATION_AVAILABLE = False
    logger.warning("Reference validation module not available - validation metrics will be skipped")

def markley_mean_quat(Q):
    A = np.zeros((4, 4))
    for q in Q:
        A += np.outer(q, q)
    vals, vecs = np.linalg.eigh(A)
    q_mean = vecs[:, np.argmax(vals)]
    if q_mean[3] < 0:
        q_mean *= -1.0
    return quat_shortest(quat_normalize(q_mean))

def detect_static_reference(time_s, q_local, joints_viz_idx, cfg):
    fs = cfg["FS_TARGET"]
    dt = 1.0 / fs
    search_sec = cfg["REF_SEARCH_SEC"]
    win_sec = cfg["REF_WINDOW_SEC"]
    step_sec = cfg["STATIC_SEARCH_STEP_SEC"]

    thr_low = cfg["MOTION_THR_LOW"]
    thr_std = cfg["MOTION_THR_STD"]

    mask_search = time_s <= (time_s[0] + search_sec)
    idxs = np.where(mask_search)[0]
    if len(idxs) < 3:
        return {
            "ref_start": float(time_s[0]),
            "ref_end": float(time_s[min(len(time_s)-1, int(round(win_sec*fs)))]),
            "ref_is_fallback": True,
            "method": "fallback_insufficient_search",
            "metrics": {"mean_motion": np.nan, "std_motion": np.nan},
        }

    T = len(time_s)
    motion = np.full(T-1, np.nan)

    for t in range(T-1):
        if not (mask_search[t] and mask_search[t+1]):
            continue
        mags = []
        for j in joints_viz_idx:
            q0 = q_local[t, j]
            q1 = q_local[t+1, j]
            if np.isfinite(q0).all() and np.isfinite(q1).all():
                dq = quat_mul(quat_inv(q0), q1)
                dq = quat_shortest(quat_normalize(dq))
                rv = R.from_quat(dq).as_rotvec()
                mags.append(float(np.linalg.norm(rv) / dt))
        if mags:
            motion[t] = np.median(mags)

    win_n = int(round(win_sec * fs))
    step_n = max(1, int(round(step_sec * fs)))

    best = None
    best_mean = float("inf")
    start_min = idxs[0]
    start_max = idxs[-1] - win_n
    if start_max <= start_min:
        start_max = start_min

    for start in range(start_min, start_max+1, step_n):
        end = start + win_n
        mwin = motion[start:end]
        mwin = mwin[np.isfinite(mwin)]
        if len(mwin) < max(3, win_n//3):
            continue
        mean_m = float(np.mean(mwin))
        std_m = float(np.std(mwin))

        if mean_m < thr_low and std_m < thr_std:
            best = (start, end, mean_m, std_m, False, "criteria")
            break

        if mean_m < best_mean:
            best_mean = mean_m
            best = (start, end, mean_m, std_m, True, "fallback_min_motion")

    if best is None:
        start = start_min
        end = min(start + win_n, len(time_s)-1)
        return {
            "ref_start": float(time_s[start]),
            "ref_end": float(time_s[end]),
            "ref_is_fallback": True,
            "method": "fallback_first_window",
            "metrics": {"mean_motion": np.nan, "std_motion": np.nan},
        }

    start, end, mean_m, std_m, is_fb, method = best

    return {
        "ref_start": float(time_s[start]),
        "ref_end": float(time_s[min(end, len(time_s)-1)]),
        "ref_is_fallback": bool(is_fb),
        "method": method,
        "metrics": {"mean_motion": mean_m, "std_motion": std_m},
    }


def compute_q_ref_and_ref_qc(time_s, q_local, ref_info, joints_export_idx, joints_viz_idx, cfg):
    t0, t1 = ref_info["ref_start"], ref_info["ref_end"]
    mask = (time_s >= t0) & (time_s <= t1)
    idxs = np.where(mask)[0]

    if len(idxs) < 3:
        idxs = np.arange(min(len(time_s), int(round(cfg["REF_WINDOW_SEC"] * cfg["FS_TARGET"]))))

    J = q_local.shape[1]
    q_ref = np.full((J, 4), np.nan)

    for j in joints_export_idx:
        Q = q_local[idxs, j, :]
        Q = Q[np.isfinite(Q).all(axis=1)]
        if len(Q) < 3:
            continue
        Q = quat_shortest(quat_normalize(Q))
        Q = quat_enforce_continuity(Q)
        q_ref[j] = markley_mean_quat(Q)

    identity_errors = {}
    ref_stds = {}

    for j in joints_viz_idx:
        if not np.isfinite(q_ref[j]).all():
            continue
        qd = quat_mul(quat_inv(q_ref[j]), q_local[idxs, j])
        qd = quat_shortest(quat_normalize(qd))
        rv = R.from_quat(qd).as_rotvec()
        mag = np.linalg.norm(rv, axis=1)
        identity_errors[j] = float(np.mean(mag))
        ref_stds[j] = float(np.std(mag))

    identity_med = np.median(list(identity_errors.values())) if identity_errors else float("nan")
    ref_quality_score = np.median(list(ref_stds.values())) if ref_stds else float("nan")

    qc = {
        "identity_error_ref_med": float(identity_med),
        "ref_quality_score": float(ref_quality_score),
        "identity_errors_by_joint_idx": identity_errors,
        "ref_std_by_joint_idx": ref_stds,
    }
    
    # Reference Validation (Research Validation Phase 1 - Item 2)
    if REF_VALIDATION_AVAILABLE:
        try:
            logger.info("Running reference validation to verify reference quality...")
            
            # Validate reference window quality
            window_validation = validate_reference_window(
                time_s, q_local, ref_info["ref_start"], ref_info["ref_end"],
                joints_viz_idx, cfg["FS_TARGET"], strict_thresholds=True
            )
            qc['reference_window_validation'] = window_validation
            
            # Validate reference stability
            stability_validation = validate_reference_stability(
                q_ref, q_local, ref_info["ref_start"], ref_info["ref_end"],
                time_s, joints_viz_idx
            )
            qc['reference_stability_validation'] = stability_validation
            
            logger.info(f"Reference Validation: Window status={window_validation.get('status', 'UNKNOWN')}, "
                       f"Mean motion={window_validation.get('mean_motion_rad_s', 0):.3f} rad/s")
            
        except Exception as e:
            logger.warning(f"Reference validation failed: {e}")
            qc['reference_validation'] = {'status': 'ERROR', 'error': str(e)}
    else:
        logger.info("Reference validation skipped (module not available)")

    return q_ref, qc