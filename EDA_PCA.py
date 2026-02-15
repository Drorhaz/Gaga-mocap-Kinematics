"""
EDA & PCA for Motor Repertoire Expansion (3-Branch: ω, q, XYZ).
All processing logic and data classes; notebook 10_EDA_PCA.ipynb calls this module.
Phase 0: Batch config parsing, file existence, structural alignment, Hips origin, temporal checks.
Phase 1: Unified loader & longitudinal scaling (fit scaler on T1+T2+T3, transform each separately).
Phase 2: 3-branch PCA (fit on combined, project T1/T2/T3 into 3D PC space; full variance spectrum for N90).
Phase 3: Exploration metrics (N90 per branch/timepoint, 3D convex hull volume per branch/timepoint).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy.spatial import ConvexHull


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EXPECTED_OMEGA_COLS = 19
EXPECTED_Q_COLS = 76   # 4 * 19
EXPECTED_XYZ_COLS = 57  # 3 * 19
HIP_TOL_MEAN = 1e-5   # Hips position columns should be ~0 (origin)
HIP_TOL_STD = 0.01  # Hips should not move; flag if std > this
GAP_MULTIPLIER = 2.0   # no gap > 2 * (1/fs)
SCALING_MEAN_TOL = 1e-5   # scaled features combined mean ≈ 0
SCALING_STD_TOL = 1e-5    # scaled features combined std ≈ 1


def load_batch_config(
    batch_config_path: str | Path | None = None,
    subject_id: str | None = None,
    project_root: str | Path = ".",
) -> dict[str, Any]:
    """
    Load JSON batch configuration. Prefer batch_config_path; if subject_id only,
    resolve to batch_configs/subject_{subject_id}_all.json.
    """
    root = Path(project_root)
    if batch_config_path is not None:
        path = Path(batch_config_path)
        if not path.is_absolute():
            path = root / path
    elif subject_id is not None:
        path = root / "batch_configs" / f"subject_{subject_id}_all.json"
    else:
        raise ValueError("Provide either batch_config_path or subject_id")
    if not path.exists():
        raise FileNotFoundError(f"Batch config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _timepoint_from_csv_path(csv_path: str) -> str:
    """Extract T1, T2, or T3 from path like 671/T1/... or 734/T3/..."""
    path = csv_path.replace("\\", "/")
    for tp in ("T1", "T2", "T3"):
        if f"/{tp}/" in path or path.startswith(f"{tp}/"):
            return tp
    return "UNKNOWN"


def get_session_mapping(
    batch_config: dict[str, Any],
    project_root: str | Path = ".",
) -> list[dict[str, Any]]:
    root = Path(project_root)
    data_dir = root / "data"
    deriv_dir = root / "derivatives" / "step_06_kinematics"
    out = []
    for csv_rel in batch_config.get("csv_files", []):
        parts = csv_rel.replace("\\", "/").split("/")
        csv_path = data_dir / Path(*parts)
        run_id = Path(parts[-1]).stem
        timepoint = _timepoint_from_csv_path(csv_rel)
        parquet_path = deriv_dir / f"{run_id}__kinematics_master.parquet"
        out.append({
            "timepoint": timepoint,
            "csv_rel": csv_rel,
            "run_id": run_id,
            "parquet_path": parquet_path,
            "csv_path": csv_path,
        })
    return out


def _omega_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.endswith("__zeroed_rel_omega_mag")]


def _q_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if re.match(r".+__zeroed_rel_q[wxyz]$", c)]


def _xyz_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if re.match(r".+__lin_rel_p[xyz]$", c)]


def _joints_from_omega_cols(cols: list[str]) -> set[str]:
    return {c.replace("__zeroed_rel_omega_mag", "") for c in cols}


def _joints_from_q_cols(cols: list[str]) -> set[str]:
    return {re.sub(r"__zeroed_rel_q[wxyz]$", "", c) for c in cols}


def _joints_from_xyz_cols(cols: list[str]) -> set[str]:
    return {re.sub(r"__lin_rel_p[xyz]$", "", c) for c in cols}


def _load_parquet_light(path: Path) -> pd.DataFrame:
    """Load parquet; use only columns we need for checks to keep memory low."""
    return pd.read_parquet(path)


def run_integrity_checks(
    batch_config: str | Path | dict | None = None,
    subject_id: str | None = None,
    project_root: str | Path = ".",
) -> dict[str, Any]:
    """
    Phase 0 integrity checks. Use batch_config (path or dict) or subject_id.
    Returns dict with:
      - table_rows: list of dicts for Numerical Verification Table
      - passed: bool (overall PASS/FAIL)
      - errors: list of error messages
      - session_mapping: list of session dicts (timepoint, parquet_path, ...)
    """
    errors: list[str] = []
    if isinstance(batch_config, dict):
        config = batch_config
    else:
        config = load_batch_config(
            batch_config_path=batch_config,
            subject_id=subject_id,
            project_root=project_root,
        )
    root = Path(project_root)
    mapping = get_session_mapping(config, root)

    # 1) Require T1, T2, T3 each present (one representative per timepoint)
    by_tp: dict[str, list[dict]] = {}
    for m in mapping:
        tp = m["timepoint"]
        by_tp.setdefault(tp, []).append(m)
    for required in ("T1", "T2", "T3"):
        if required not in by_tp:
            errors.append(f"Timepoint {required} has no session in batch config.")

    # Representative: one session per timepoint (for table and checks)
    representative: list[dict] = []
    for tp in ("T1", "T2", "T3"):
        if tp in by_tp:
            representative.append(by_tp[tp][0])
    if not representative:
        return {
            "table_rows": [],
            "passed": False,
            "errors": errors,
            "session_mapping": mapping,
        }

    # 2) File existence
    for m in representative:
        if not m["parquet_path"].exists():
            errors.append(f"Parquet missing: {m['parquet_path']}")
    if errors:
        return {
            "table_rows": [],
            "passed": False,
            "errors": errors,
            "session_mapping": mapping,
        }

    # Load parquets for the three sessions
    dfs: list[pd.DataFrame] = []
    for m in representative:
        dfs.append(_load_parquet_light(m["parquet_path"]))

    # 3) Branch column counts and joint intersection
    omega_cols_per_session = [_omega_columns(df) for df in dfs]
    q_cols_per_session = [_q_columns(df) for df in dfs]
    xyz_cols_per_session = [_xyz_columns(df) for df in dfs]

    joints_omega = [_joints_from_omega_cols(c) for c in omega_cols_per_session]
    joints_q = [_joints_from_q_cols(c) for c in q_cols_per_session]
    joints_xyz = [_joints_from_xyz_cols(c) for c in xyz_cols_per_session]

    inter_omega = set.intersection(*joints_omega) if joints_omega else set()
    inter_q = set.intersection(*joints_q) if joints_q else set()
    inter_xyz = set.intersection(*joints_xyz) if joints_xyz else set()

    for i, (j1, j2, j3) in enumerate(zip(joints_omega, joints_q, joints_xyz)):
        only_t1 = (j1 - inter_omega) or (j2 - inter_q) or (j3 - inter_xyz)
        if only_t1:
            errors.append(f"Session {representative[i]['timepoint']}: joints not present in all sessions: {only_t1}")
    if len(omega_cols_per_session[0]) != EXPECTED_OMEGA_COLS:
        errors.append(f"Branch ω: expected {EXPECTED_OMEGA_COLS} columns, got {len(omega_cols_per_session[0])}")
    if len(q_cols_per_session[0]) != EXPECTED_Q_COLS:
        errors.append(f"Branch q: expected {EXPECTED_Q_COLS} columns, got {len(q_cols_per_session[0])}")
    if len(xyz_cols_per_session[0]) != EXPECTED_XYZ_COLS:
        errors.append(f"Branch XYZ: expected {EXPECTED_XYZ_COLS} columns, got {len(xyz_cols_per_session[0])}")

    # 4) Hips at origin (mean and std ≈ 0)
    hips_cols = ["Hips__lin_rel_px", "Hips__lin_rel_py", "Hips__lin_rel_pz"]
    for i, df in enumerate(dfs):
        for col in hips_cols:
            if col not in df.columns:
                errors.append(f"Session {representative[i]['timepoint']}: missing {col}")
                continue
            mu = float(df[col].mean())
            sigma = float(df[col].std())
            if abs(mu) > HIP_TOL_MEAN or sigma > HIP_TOL_STD:
                errors.append(
                    f"Session {representative[i]['timepoint']}: Hips {col} mean={mu:.6f} std={sigma:.6f} (expected ~0). "
                    "Branch C is not 'reach relative to body' (Hips are moving)."
                )

    # 5) Temporal: median fs, consistency, max gap
    time_col = "time_s"
    table_rows: list[dict[str, Any]] = []
    fs_list: list[float] = []
    for i, df in enumerate(dfs):
        if time_col not in df.columns:
            errors.append(f"Session {representative[i]['timepoint']}: missing '{time_col}'")
            table_rows.append({
                "Session ID": representative[i]["timepoint"],
                "Frames": len(df),
                "Median fs (Hz)": None,
                "Max Gap (ms)": None,
                "n_omega": len(omega_cols_per_session[i]),
                "n_q": len(q_cols_per_session[i]),
                "n_xyz": len(xyz_cols_per_session[i]),
            })
            continue
        t = df[time_col].values
        dt = np.diff(t)
        dt_ms = dt * 1000.0
        median_dt = np.median(dt)
        if median_dt <= 0:
            fs_hz = None
            max_gap_ms = float(np.max(dt_ms)) if len(dt_ms) else None
        else:
            fs_hz = 1.0 / median_dt
            max_gap_ms = float(np.max(dt_ms))
        fs_list.append(fs_hz)
        threshold_ms = (GAP_MULTIPLIER / fs_hz * 1000.0) if fs_hz else None
        if threshold_ms is not None and max_gap_ms is not None and max_gap_ms > threshold_ms:
            bad_idx = np.argmax(dt)
            errors.append(
                f"Session {representative[i]['timepoint']}: gap {max_gap_ms:.2f} ms at index {bad_idx} "
                f"(threshold {threshold_ms:.2f} ms = 2×1/fs)."
            )
        table_rows.append({
            "Session ID": representative[i]["timepoint"],
            "Frames": len(df),
            "Median fs (Hz)": round(fs_hz, 2) if fs_hz is not None else None,
            "Max Gap (ms)": round(max_gap_ms, 2) if max_gap_ms is not None else None,
            "n_omega": len(omega_cols_per_session[i]),
            "n_q": len(q_cols_per_session[i]),
            "n_xyz": len(xyz_cols_per_session[i]),
        })

    # Sampling consistency: fs equal across sessions
    if len(fs_list) >= 2 and all(f is not None for f in fs_list):
        if max(fs_list) - min(fs_list) > 0.01:
            errors.append(
                f"Median sampling rate differs across sessions: {fs_list}. "
                "Require f_s1 = f_s2 = f_s3."
            )

    passed = len(errors) == 0
    return {
        "table_rows": table_rows,
        "passed": passed,
        "errors": errors,
        "session_mapping": mapping,
    }


# ---------------------------------------------------------------------------
# Phase 1: Unified Loader & Longitudinal Scaling
# ---------------------------------------------------------------------------


def _get_representative_sessions_with_parquets(
    session_mapping: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Filter to sessions with existing parquet; pick one per timepoint (T1, T2, T3 order)."""
    existing = [m for m in session_mapping if Path(m["parquet_path"]).exists()]
    by_tp: dict[str, list[dict]] = {}
    for m in existing:
        by_tp.setdefault(m["timepoint"], []).append(m)
    representative = []
    for tp in ("T1", "T2", "T3"):
        if tp in by_tp:
            representative.append(by_tp[tp][0])
    return representative


def prepare_3branch_data(
    session_mapping: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Load parquets for representative sessions (one per T1/T2/T3 present), extract branch
    columns, fit one StandardScaler per branch on concatenated T1+T2+T3, transform each
    session separately. Zero-variance/NaN in scaled output are filled with 0.

    Returns:
        prepared: dict with keys "dynamics", "pose", "reach". Each branch has:
          - scaled_arrays: list of ndarray (one per session, in timepoint order)
          - columns: list of column names
          - scaler: fitted StandardScaler
          - n_frames_per_session: list of int
          - timepoints: list of str (e.g. ["T1", "T2", "T3"] or subset)
        Also "representative_sessions": list of session dicts used.
    """
    representative = _get_representative_sessions_with_parquets(session_mapping)
    if not representative:
        raise ValueError(
            "No parquet files found for session_mapping. Ensure at least one session has "
            "derivatives/step_06_kinematics/{run_id}__kinematics_master.parquet."
        )

    dfs: list[pd.DataFrame] = []
    for m in representative:
        dfs.append(pd.read_parquet(m["parquet_path"]))

    # Column intersection across sessions so all have same feature set
    omega_sets = [set(_omega_columns(df)) for df in dfs]
    q_sets = [set(_q_columns(df)) for df in dfs]
    xyz_sets = [set(_xyz_columns(df)) for df in dfs]
    omega_cols = sorted(set.intersection(*omega_sets)) if omega_sets else []
    q_cols = sorted(set.intersection(*q_sets)) if q_sets else []
    xyz_cols = sorted(set.intersection(*xyz_sets)) if xyz_sets else []

    if not omega_cols or not q_cols or not xyz_cols:
        raise ValueError(
            "Missing branch columns: omega=%s, q=%s, xyz=%s."
            % (len(omega_cols), len(q_cols), len(xyz_cols))
        )

    timepoints = [m["timepoint"] for m in representative]

    def _scale_branch(cols: list[str], branch_name: str) -> dict[str, Any]:
        # Extract and concatenate
        blocks = [df[cols].values for df in dfs]
        combined = np.vstack(blocks)
        # Fit scaler on combined, transform each block separately
        scaler = StandardScaler()
        scaler.fit(combined)
        scaled_arrays = []
        n_frames_per_session = []
        for i, df in enumerate(dfs):
            X = df[cols].values
            n_frames_per_session.append(len(X))
            s = scaler.transform(X)
            # Handle NaN (e.g. zero-variance): fill with 0
            np.nan_to_num(s, copy=False, nan=0.0, posinf=0.0, neginf=0.0)
            scaled_arrays.append(s)
        return {
            "scaled_arrays": scaled_arrays,
            "columns": cols,
            "scaler": scaler,
            "n_frames_per_session": n_frames_per_session,
            "timepoints": timepoints,
        }

    prepared = {
        "dynamics": _scale_branch(omega_cols, "dynamics"),
        "pose": _scale_branch(q_cols, "pose"),
        "reach": _scale_branch(xyz_cols, "reach"),
        "representative_sessions": representative,
    }
    return prepared


def check_scaling_integrity(prepared: dict[str, Any]) -> dict[str, Any]:
    """
    Assert combined (T1+T2+T3) scaled features: mean ≈ 0, std ≈ 1 or std ≈ 0 (constant), no NaN.
    Zero-variance columns (e.g. Hips position at origin in Reach branch) are valid: scaled = 0, std = 0.
    Returns dict: branch_name -> "PASS" | "FAIL".
    """
    results: dict[str, str] = {}
    for branch_key in ("dynamics", "pose", "reach"):
        data = prepared.get(branch_key)
        if not data:
            results[branch_key] = "FAIL"
            continue
        scaled_arrays = data["scaled_arrays"]
        combined = np.vstack(scaled_arrays)

        if np.any(np.isnan(combined)):
            results[branch_key] = "FAIL"
            continue

        mean_ok = np.all(np.abs(np.mean(combined, axis=0)) < SCALING_MEAN_TOL)
        stds = np.std(combined, axis=0)
        # Accept std ≈ 1 (normal scaled) or std ≈ 0 (constant column, e.g. Hips at origin)
        std_ok = np.all(
            (np.abs(stds - 1.0) < SCALING_STD_TOL) | (stds < SCALING_STD_TOL)
        )
        results[branch_key] = "PASS" if (mean_ok and std_ok) else "FAIL"

    return results


# ---------------------------------------------------------------------------
# Phase 2: 3-Branch PCA Engine
# ---------------------------------------------------------------------------


def run_3branch_pca(scaled_data_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Fit PCA on combined (T1+T2+T3) scaled data per branch; project each session
    into 3D (PC1, PC2, PC3). Full variance spectrum is retained for N90 in Phase 3.
    PCA objects are stored for loadings in Phase 4.

    Args:
        scaled_data_dict: output of prepare_3branch_data() with keys "dynamics", "pose", "reach".

    Returns:
        pca_results: for each branch:
          - pca: fitted sklearn PCA (fitted on all components for full variance spectrum)
          - projected_arrays: list of (n_frames, 3) arrays (PC1, PC2, PC3) per session
          - explained_variance_ratio_: full spectrum (for N90)
          - timepoints: list of session labels
          - n_features: number of input features
    """
    pca_results: dict[str, Any] = {}
    for branch_key in ("dynamics", "pose", "reach"):
        data = scaled_data_dict.get(branch_key)
        if not data:
            continue
        scaled_arrays = data["scaled_arrays"]
        columns = data["columns"]
        timepoints = data["timepoints"]
        combined = np.vstack(scaled_arrays)
        n_samples, n_features = combined.shape

        # Fit PCA on all components to get full variance spectrum (for N90)
        n_components_full = min(n_samples, n_features)
        pca = PCA(n_components=n_components_full)
        pca.fit(combined)

        # Project each session into 3D (first 3 components)
        projected_arrays = []
        for X in scaled_arrays:
            # X @ components_[:3].T = (n_frames, 3)
            proj_3d = X @ pca.components_[:3].T
            projected_arrays.append(proj_3d)

        pca_results[branch_key] = {
            "pca": pca,
            "projected_arrays": projected_arrays,
            "explained_variance_ratio_": pca.explained_variance_ratio_.copy(),
            "timepoints": timepoints,
            "n_features": n_features,
            "columns": columns,
        }
    return pca_results


# ---------------------------------------------------------------------------
# Phase 3: Exploration Metrics (N90 & 3D Convex Hull)
# ---------------------------------------------------------------------------


def calculate_n90(
    pca_results: dict[str, Any],
    prepared: dict[str, Any],
) -> dict[str, Any]:
    """
    For each branch and each timepoint, find the number of components required
    to reach 90% cumulative explained variance (N90). Cumulative variance is
    computed **per session**: we project that session's scaled data onto all
    PCs and use that session's variance along each PC. So even if the global
    PCA needs 40 components for 90% on combined data, T1 might need only 12;
    a jump to a higher N90 in T2 is evidence of increased entropy/complexity.

    Returns:
        n90_results: dict branch_key -> {
            "timepoints": ["T1", "T2", "T3"],
            "n90_per_session": [n90_t1, n90_t2, n90_t3],
        }
        So table: Branch | T1 N90 | T2 N90 | T3 N90.
    """
    n90_results: dict[str, Any] = {}
    for branch_key in ("dynamics", "pose", "reach"):
        res = pca_results.get(branch_key)
        prep = prepared.get(branch_key)
        if not res or not prep:
            continue
        pca = res["pca"]
        timepoints = res["timepoints"]
        scaled_arrays = prep["scaled_arrays"]
        n90_per_session = []
        for X in scaled_arrays:
            # Project this session onto all components; variance is per-session
            Y = X @ pca.components_.T  # (n_frames, n_components)
            var_per_pc = np.var(Y, axis=0)
            total_var = np.sum(var_per_pc)
            if total_var <= 0:
                n90_per_session.append(0)
                continue
            # Cumulative explained variance for this session only
            explained_ratio = var_per_pc / total_var
            cum = np.cumsum(explained_ratio)
            # Smallest k (1-based count) such that cum[k-1] >= 0.9
            idx = np.searchsorted(cum, 0.9)
            n90 = int(idx) + 1
            n90_per_session.append(n90)
        n90_results[branch_key] = {
            "timepoints": timepoints,
            "n90_per_session": n90_per_session,
        }
    return n90_results


def calculate_3d_hull_volume(pca_results: dict[str, Any]) -> dict[str, Any]:
    """
    For each branch and each timepoint, compute the volume of the 3D convex hull
    of the points (PC1, PC2, PC3). Requires at least 4 points; otherwise volume = 0.
    Uses qhull_options='QJ' (joggled input) to avoid precision errors on nearly flat
    or degenerate point sets (e.g. Reach/XYZ with little vertical movement in T1).

    Returns:
        volume_results: dict branch_key -> {
            "timepoints": ["T1", "T2", "T3"],
            "volumes": [v_t1, v_t2, v_t3],
        }
        So table: Branch | T1 Volume | T2 Volume | T3 Volume.
    """
    volume_results: dict[str, Any] = {}
    for branch_key in ("dynamics", "pose", "reach"):
        res = pca_results.get(branch_key)
        if not res:
            continue
        projected_arrays = res["projected_arrays"]
        timepoints = res["timepoints"]
        volumes = []
        for points in projected_arrays:
            if points.shape[0] < 4:
                volumes.append(0.0)
                continue
            try:
                hull = ConvexHull(points, qhull_options="QJ")
                volumes.append(float(hull.volume))
            except Exception:
                volumes.append(0.0)
        volume_results[branch_key] = {
            "timepoints": timepoints,
            "volumes": volumes,
        }
    return volume_results


# ---------------------------------------------------------------------------
# Phase 4: Anatomical Loadings (Top 5 Joint Contributors)
# ---------------------------------------------------------------------------

# Number of top joints to report per branch
TOP_N_JOINTS = 5


def _feature_to_joint(column_name: str) -> str:
    """Extract joint name from branch column (e.g. 'Hips__zeroed_rel_omega_mag' -> 'Hips')."""
    return column_name.split("__")[0]


def calculate_joint_loadings(pca_results: dict[str, Any]) -> dict[str, Any]:
    """
    For each branch, compute Anatomical Contribution Index: sum of squared loadings
    for PC1, PC2, PC3 per feature, aggregated by joint, normalized to 100%.
    Returns Top 5 joints per branch for the "Who" of the movement.

    Steps:
      - Take PCA.components_ for PC1, PC2, PC3.
      - Per feature: Loadings_Total = sqrt(PC1^2 + PC2^2 + PC3^2).
      - Aggregate by joint (sum over features belonging to that joint).
      - Normalize so total across joints = 1.0 (report as %).
      - Rank and return Top 5 joints with highest contribution.

    Returns:
        loadings_results: dict branch_key -> {
            "top5_joints": [joint1, joint2, ...],
            "top5_pct": [pct1, pct2, ...],  # 0-100
        }
    """
    loadings_results: dict[str, Any] = {}
    for branch_key in ("dynamics", "pose", "reach"):
        res = pca_results.get(branch_key)
        if not res:
            continue
        pca = res["pca"]
        columns = res["columns"]
        # (3, n_features) loadings for PC1, PC2, PC3
        loadings_3 = pca.components_[:3, :]
        n_features = loadings_3.shape[1]
        if n_features != len(columns):
            continue
        # Per-feature contribution: L2 norm of (PC1, PC2, PC3) loadings
        contribution_per_feature = np.sqrt(np.sum(loadings_3 ** 2, axis=0))
        # Aggregate by joint
        joint_score: dict[str, float] = {}
        for j, col in enumerate(columns):
            joint = _feature_to_joint(col)
            joint_score[joint] = joint_score.get(joint, 0.0) + contribution_per_feature[j]
        total = sum(joint_score.values())
        if total <= 0:
            loadings_results[branch_key] = {"top5_joints": [], "top5_pct": []}
            continue
        # Normalize to 1.0 (we'll report as %)
        for k in joint_score:
            joint_score[k] /= total
        # Top 5
        sorted_joints = sorted(
            joint_score.items(), key=lambda x: x[1], reverse=True
        )[:TOP_N_JOINTS]
        top5_joints = [j for j, _ in sorted_joints]
        top5_pct = [round(100.0 * pct, 2) for _, pct in sorted_joints]
        loadings_results[branch_key] = {
            "top5_joints": top5_joints,
            "top5_pct": top5_pct,
        }
    return loadings_results


def calculate_session_joint_loadings(
    pca_results: dict[str, Any],
    prepared_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Per-session (per-T) anatomical loadings: for each branch and each timepoint
    (T1, T2, T3), project that session's scaled data onto PC1–PC3, compute each
    joint's variance contribution in that 3D projection, normalize to 100%.
    Enables longitudinal comparison and delta (T2% - T1%).

    For each session: contribution of joint J = sum over PC dims of Var(partial
    projection of J's features onto PC1, PC2, PC3), then normalize so joints sum to 100%.

    Returns:
        session_loadings: dict branch_key -> {
            "timepoints": ["T1", "T2", "T3"],
            "joint_pct_per_session": [
                {"JointA": pct_t1, "JointB": ...},  # T1
                {"JointA": pct_t2, ...},             # T2
                {"JointA": pct_t3, ...},             # T3
            ],
        }
    """
    session_loadings: dict[str, Any] = {}
    for branch_key in ("dynamics", "pose", "reach"):
        res = pca_results.get(branch_key)
        prep = prepared_data.get(branch_key)
        if not res or not prep:
            continue
        pca = res["pca"]
        columns = res["columns"]
        scaled_arrays = prep["scaled_arrays"]
        timepoints = res["timepoints"]
        components_3 = pca.components_[:3, :]  # (3, n_features)

        # Build joint -> list of column indices
        joint_to_idx: dict[str, list[int]] = {}
        for j, col in enumerate(columns):
            joint = _feature_to_joint(col)
            joint_to_idx.setdefault(joint, []).append(j)

        joint_pct_per_session: list[dict[str, float]] = []
        for X in scaled_arrays:
            # Per-joint variance in 3D projection for this session
            joint_var: dict[str, float] = {}
            for joint, idx in joint_to_idx.items():
                # Partial projection: this session's data for these features onto PC1–PC3
                Y_j = X[:, idx] @ components_3[:, idx].T  # (n_frames, 3)
                var_contribution = float(np.sum(np.var(Y_j, axis=0)))
                joint_var[joint] = var_contribution
            total = sum(joint_var.values())
            if total <= 0:
                joint_pct_per_session.append({j: 0.0 for j in joint_var})
                continue
            joint_pct = {j: 100.0 * (v / total) for j, v in joint_var.items()}
            joint_pct_per_session.append(joint_pct)
        session_loadings[branch_key] = {
            "timepoints": timepoints,
            "joint_pct_per_session": joint_pct_per_session,
        }
    return session_loadings


def longitudinal_joint_shift_table(
    session_loadings: dict[str, Any],
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """
    Build Longitudinal Joint Shift table: Branch | Joint | T1 % | T2 % | T3 % | Change (T2-T1).
    Top N joints per branch ranked by absolute Change (T2 - T1). If only one session, no Change.

    Returns:
        List of row dicts for DataFrame.
    """
    rows: list[dict[str, Any]] = []
    for branch_key in ("dynamics", "pose", "reach"):
        data = session_loadings.get(branch_key)
        if not data:
            continue
        timepoints = data["timepoints"]
        joint_pct = data["joint_pct_per_session"]
        if len(timepoints) < 2 or len(joint_pct) < 2:
            # No T2 to compute change; show top N by T1 %
            all_joints = sorted(joint_pct[0].keys()) if joint_pct else []
            t1_order = sorted(all_joints, key=lambda j: joint_pct[0].get(j, 0.0), reverse=True)[:top_n]
            for joint in t1_order:
                r = {"Branch": branch_key, "Joint": joint}
                r["T1 %"] = round(joint_pct[0].get(joint, 0.0), 2)
                r["T2 %"] = round(joint_pct[1].get(joint, 0.0), 2) if len(joint_pct) > 1 else None
                r["T3 %"] = round(joint_pct[2].get(joint, 0.0), 2) if len(joint_pct) > 2 else None
                r["Change (T2-T1)"] = None
                rows.append(r)
            continue
        all_joints = sorted(joint_pct[0].keys())
        t1_pct = joint_pct[0]
        t2_pct = joint_pct[1]
        t3_pct = joint_pct[2] if len(joint_pct) > 2 else {}
        changes = [(j, t2_pct.get(j, 0.0) - t1_pct.get(j, 0.0)) for j in all_joints]
        changes.sort(key=lambda x: abs(x[1]), reverse=True)
        top_joints = [j for j, _ in changes[:top_n]]
        for joint in top_joints:
            r = {
                "Branch": branch_key,
                "Joint": joint,
                "T1 %": round(t1_pct.get(joint, 0.0), 2),
                "T2 %": round(t2_pct.get(joint, 0.0), 2),
                "T3 %": round(t3_pct.get(joint, 0.0), 2) if t3_pct else None,
            }
            r["Change (T2-T1)"] = round(t2_pct.get(joint, 0.0) - t1_pct.get(joint, 0.0), 2)
            rows.append(r)
    return rows


# ---------------------------------------------------------------------------
# Phase 4 Upgrade: Whole-System Statistics (Gini, Shannon, Axial-Peripheral, Sparseness)
# ---------------------------------------------------------------------------

AXIAL_JOINTS = ("Spine", "Spine1", "Neck", "Hips", "Head")
PERIPHERAL_JOINTS = ("LeftHand", "RightHand", "LeftFoot", "RightFoot")


def _gini(proportions: np.ndarray) -> float:
    """Gini coefficient (0 = equality, 1 = one has all). proportions sum to 1."""
    p = np.asarray(proportions).flatten()
    p = p[p >= 0]
    if len(p) == 0 or np.sum(p) <= 0:
        return 0.0
    p = np.sort(p)
    n = len(p)
    cumsum = np.cumsum(p)
    return float((2 * np.sum(cumsum)) / (n * np.sum(p)) - (n + 1) / n)


def _shannon_entropy(proportions: np.ndarray) -> float:
    """Shannon entropy (natural log). proportions sum to 1. 0*log(0)=0."""
    p = np.asarray(proportions).flatten()
    p = p[p > 0]
    return float(-np.sum(p * np.log(p)))


def _axial_peripheral_ratio(joint_pct: dict[str, float]) -> float:
    """Central (Spine/Neck/Hips/Head) vs Distal (Hands/Feet). Ratio = axial_sum / peripheral_sum (%)."""
    axial = sum(joint_pct.get(j, 0.0) for j in AXIAL_JOINTS)
    peripheral = sum(joint_pct.get(j, 0.0) for j in PERIPHERAL_JOINTS)
    if peripheral <= 0:
        return float(axial) if axial > 0 else 0.0
    return axial / peripheral


def _sparseness(joint_pct: dict[str, float]) -> float:
    """Percentage of joints with <1% contribution (silent)."""
    if not joint_pct:
        return 0.0
    n_silent = sum(1 for v in joint_pct.values() if v < 1.0)
    return 100.0 * n_silent / len(joint_pct)


def get_index_definitions() -> dict[str, str]:
    """Return short names and full definitions for the four whole-system indices (for Legend)."""
    return {
        "Gini Coefficient (Inequality)": (
            "Calculated by reconstructing session variance from the full PCA weight matrix. "
            "A low Gini in T2 indicates that the 'movement budget' has shifted from being dominated "
            "by a few joints to a more democratic, whole-body integration."
        ),
        "Shannon Entropy (Diversity)": (
            "Measures the information density of the joint-variance distribution. "
            "Based on the probability of each joint contributing to the total movement. "
            "Higher entropy in T2 suggests the motor system is exploring a more diverse and less "
            "predictable set of joint combinations."
        ),
        "Axial-Peripheral Ratio (Core vs. Limbs)": (
            "A comparison of 'Central' (Spine/Neck/Hips) vs. 'Distal' (Hands/Feet) variance loadings. "
            "An increase in T2 suggests the subject has shifted toward 'embodied' movement, "
            "where the core of the body drives the behavioral complexity rather than just the extremities."
        ),
        "Sparseness (System Activation)": (
            "The percentage of the body that remains 'silent' (<1% contribution). "
            "Lower sparseness in T2 indicates that a larger portion of the subject's physical "
            "degrees of freedom have been 'awakened' by the intervention."
        ),
    }


def calculate_whole_system_stats(
    pca_results: dict[str, Any],
    prepared_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Whole-system indices per branch and per session: project session onto global PCA (Y = X·V),
    attribute variance back to features via squared loadings scaled by session PC variance,
    aggregate by joint, then compute Gini, Shannon entropy, Axial-Peripheral ratio, Sparseness.

    Returns:
        stats: dict branch_key -> {
            "timepoints": ["T1", "T2", "T3"],
            "metrics_per_session": [
                {"Gini": v, "Shannon": v, "AxialPeripheral": v, "Sparseness": v},  # T1
                ...
            ],
        }
    """
    stats: dict[str, Any] = {}
    for branch_key in ("dynamics", "pose", "reach"):
        res = pca_results.get(branch_key)
        prep = prepared_data.get(branch_key)
        if not res or not prep:
            continue
        pca = res["pca"]
        columns = res["columns"]
        scaled_arrays = prep["scaled_arrays"]
        timepoints = res["timepoints"]
        V = pca.components_[:3, :]  # (3, n_features)
        joint_to_idx: dict[str, list[int]] = {}
        for j, col in enumerate(columns):
            joint = _feature_to_joint(col)
            joint_to_idx.setdefault(joint, []).append(j)

        metrics_per_session: list[dict[str, float]] = []
        for X in scaled_arrays:
            Y = X @ V.T  # (n_frames, 3)
            var_pc = np.var(Y, axis=0)  # (3,)
            # Attribute variance to each feature: sum over k of V[k,j]^2 * var_pc[k]
            attr_per_feature = np.sum(V ** 2 * var_pc[np.newaxis, :], axis=0)
            total_attr = np.sum(attr_per_feature)
            if total_attr <= 0:
                joint_pct = {j: 100.0 / len(joint_to_idx) for j in joint_to_idx}
            else:
                joint_attr = {}
                for joint, idx in joint_to_idx.items():
                    joint_attr[joint] = float(np.sum(attr_per_feature[idx]))
                s = sum(joint_attr.values())
                joint_pct = {j: 100.0 * (v / s) for j, v in joint_attr.items()}
            p_prop = np.array([joint_pct.get(j, 0.0) / 100.0 for j in joint_to_idx])
            p_prop = p_prop / np.sum(p_prop) if np.sum(p_prop) > 0 else p_prop
            metrics_per_session.append({
                "Gini": _gini(p_prop),
                "Shannon": _shannon_entropy(p_prop),
                "AxialPeripheral": _axial_peripheral_ratio(joint_pct),
                "Sparseness": _sparseness(joint_pct),
            })
        stats[branch_key] = {
            "timepoints": timepoints,
            "metrics_per_session": metrics_per_session,
        }
    return stats


def longitudinal_strategy_table(stats_results: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Build Longitudinal Strategy Table: Branch | Metric | T1 | T2 | T3 | % Change (T1 vs T2).
    One row per (branch, metric). % Change = (T2 - T1) / |T1| * 100 when T1 != 0.
    """
    metric_keys = ["Gini", "Shannon", "AxialPeripheral", "Sparseness"]
    rows: list[dict[str, Any]] = []
    for branch_key in ("dynamics", "pose", "reach"):
        data = stats_results.get(branch_key)
        if not data:
            continue
        timepoints = data["timepoints"]
        metrics_per = data["metrics_per_session"]
        n = len(timepoints)
        for mk in metric_keys:
            t1 = metrics_per[0].get(mk, 0.0) if len(metrics_per) > 0 else None
            t2 = metrics_per[1].get(mk, 0.0) if len(metrics_per) > 1 else None
            t3 = metrics_per[2].get(mk, 0.0) if len(metrics_per) > 2 else None
            if t1 is not None and t2 is not None and (isinstance(t1, (int, float)) and isinstance(t2, (int, float))):
                pct_change = (t2 - t1) / (abs(t1) + 1e-12) * 100.0
            else:
                pct_change = None
            rows.append({
                "Branch": branch_key,
                "Metric": mk,
                "T1": round(t1, 4) if t1 is not None else None,
                "T2": round(t2, 4) if t2 is not None else None,
                "T3": round(t3, 4) if t3 is not None else None,
                "% Change (T1 vs T2)": round(pct_change, 2) if pct_change is not None else None,
            })
    return rows

