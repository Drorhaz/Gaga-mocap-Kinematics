import numpy as np
import pandas as pd

def bone_length_qc(pos_m, schema, joints_export_mask, cfg, use_bvh_offsets=False):
    """
    Bone length quality control based on consistency (CV%).
    
    Parameters:
    -----------
    pos_m : np.ndarray
        Position data (T, J, 3) in meters
    schema : dict
        Skeleton schema with joint_names, bones, and optionally offsets
    joints_export_mask : np.ndarray
        Boolean mask for which joints to include
    cfg : dict
        Configuration with THRESH values
    use_bvh_offsets : bool, default=False
        If True, compares actual bone lengths to BVH offsets (requires per-session offsets).
        If False, only checks consistency (CV%) - recommended for multi-subject data.
        
    Returns:
    --------
    df_bones : pd.DataFrame
        Bone length QC results
    summary : dict
        Summary statistics
    """
    joint_names = schema["joint_names"]
    idx = {j:i for i,j in enumerate(joint_names)}
    bones = schema["bones"]
    
    # Only extract offsets if BVH comparison is enabled
    offsets = schema.get("offsets", {}) if use_bvh_offsets else {}

    rows = []
    for p_name, c_name in bones:
        if p_name not in idx or c_name not in idx:
            continue
        p = idx[p_name]
        c = idx[c_name]
        if not (joints_export_mask[p] and joints_export_mask[c]):
            continue

        P = pos_m[:, p, :]
        C = pos_m[:, c, :]
        valid = np.isfinite(P).all(axis=1) & np.isfinite(C).all(axis=1)
        if valid.sum() < 10:
            continue

        L = np.linalg.norm(C[valid] - P[valid], axis=1)
        median_L = float(np.median(L))
        mean_L = float(np.mean(L))
        std_L = float(np.std(L))
        cv = float(std_L / mean_L) if mean_L > 0 else float("inf")
        p95_abs_dev = float(np.percentile(np.abs(L - median_L), 95))
        max_jump = float(np.max(np.abs(np.diff(L)))) if len(L) > 1 else 0.0

        status = "PASS"
        if cv > cfg["THRESH"]["BONE_CV_ALERT"] or max_jump > cfg["THRESH"]["BONE_MAX_JUMP_ALERT_M"]:
            status = "ALALERT"
        elif cv > cfg["THRESH"]["BONE_CV_WARN"] or p95_abs_dev > cfg["THRESH"]["BONE_P95_ABS_DEV_WARN_M"]:
            status = "WARN"

        # Build result row
        row = {
            "bone": f"{p_name}->{c_name}",
            "parent": p_name,
            "child": c_name,
            "median_L_m": median_L,
            "mean_L_m": mean_L,
            "std_L_m": std_L,
            "cv": cv,
            "p95_abs_dev_m": p95_abs_dev,
            "max_jump_m": max_jump,
            "status": status,
        }
        
        # Only add BVH comparison if enabled and offsets available
        if use_bvh_offsets and offsets:
            off = offsets.get(c_name, [np.nan, np.nan, np.nan])
            L_bvh = float(np.linalg.norm(off)) if np.all(np.isfinite(off)) else np.nan
            ratio = float(median_L / L_bvh) if (np.isfinite(L_bvh) and L_bvh > 0) else np.nan
            row["bvh_offset_len"] = L_bvh
            row["ratio_median_to_bvh"] = ratio
        
        rows.append(row)

    df_bones = pd.DataFrame(rows)

    n_warn = int((df_bones["status"] == "WARN").sum()) if len(df_bones) else 0
    n_alert = int((df_bones["status"] == "ALERT").sum()) if len(df_bones) else 0

    worst = df_bones.sort_values(["cv","max_jump_m"], ascending=[False,False]).head(10).to_dict("records") if len(df_bones) else []

    summary = {
        "bone_n_warn": n_warn,
        "bone_n_alert": n_alert,
        "worst_bones": worst
    }

    return df_bones, summary