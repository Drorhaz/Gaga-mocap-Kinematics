import numpy as np
import pandas as pd
import os
import gc
import json
from scipy.spatial.transform import Rotation as R
from scipy.signal import savgol_filter

from .config import CONFIG
from .utils import ensure_dirs, fingerprint_file, write_json, log_event
from .preprocessing import parse_optitrack_csv
from .resampling import estimate_fs, resample_time_grid, resample_pos, resample_quat_slerp
from .quaternion_ops import quat_normalize, quat_shortest, quat_enforce_continuity, quat_mul, quat_inv
from .reference import detect_static_reference, compute_q_ref_and_ref_qc
from .qc import bone_length_qc
from .export_tables import build_master_tables

class RunCtx:
    def __init__(self, run_id, out_dir):
        self.run_id = run_id
        self.out_dir = out_dir
        self.warnings = []
        self.alerts = {}
        self.stage_status = {}
        self.metrics = {}
        self.meta = {}

def compute_q_local(q_global, schema):
    joint_names = schema["joint_names"]
    parent_map = schema["parent_map"]
    depth_order = schema["depth_order"]
    idx = {j: i for i, j in enumerate(joint_names)}
    T, J, _ = q_global.shape
    q_local = np.full_like(q_global, np.nan)

    for t in range(T):
        for jname in depth_order:
            j = idx[jname]
            parent = parent_map.get(jname, None)
            if parent is None:
                q_local[t, j] = q_global[t, j]
            else:
                p = idx[parent]
                if (np.isfinite(q_global[t, p]).all() and np.isfinite(q_global[t, j]).all()):
                    q_local[t, j] = quat_mul(quat_inv(q_global[t, p]), q_global[t, j])
    
    return quat_enforce_continuity(quat_shortest(quat_normalize(q_local)))

def compute_kinematics(q_local, q_ref, fs):
    dt = 1.0 / fs
    T, J, _ = q_local.shape
    rotvec = np.full((T, J, 3), np.nan)
    rv_mag = np.full((T, J), np.nan)
    omega = np.full((T, J, 3), np.nan)
    omega_mag = np.full((T, J), np.nan)

    for j in range(J):
        if not np.isfinite(q_ref[j]).all(): continue
        
        # Rotvec
        qd = quat_mul(quat_inv(q_ref[j]), q_local[:, j])
        qd = quat_shortest(quat_normalize(qd))
        rv = R.from_quat(qd).as_rotvec()
        rotvec[:, j, :] = rv
        rv_mag[:, j] = np.linalg.norm(rv, axis=1)

        # Omega
        qj = q_local[:, j]
        for t in range(T - 1):
            q0, q1 = qj[t], qj[t+1]
            if np.isfinite(q0).all() and np.isfinite(q1).all():
                dq = quat_mul(quat_inv(q0), q1)
                dq = quat_shortest(quat_normalize(dq))
                om = R.from_quat(dq).as_rotvec() / dt
                omega[t, j] = om
                omega_mag[t, j] = np.linalg.norm(om)
    return rotvec, rv_mag, omega, omega_mag

def compute_derivatives(pos, fs, cfg):
    win = int(round(cfg["SG_WINDOW_SEC"] * fs))
    if win < 5: win = 5
    if win % 2 == 0: win += 1
    return savgol_filter(pos, window_length=win, polyorder=cfg["SG_POLYORDER"], deriv=1, delta=1.0/fs, axis=0, mode='interp')

def run_pipeline(csv_path, schema, seg_map, run_id="run1", cfg=CONFIG, output_root="analysis"):
    out_dir = os.path.join(output_root, run_id)
    ensure_dirs(out_dir, os.path.join(out_dir, "debug"))
    ctx = RunCtx(run_id, out_dir)
    
    try:
        # 1. Load
        frame_idx, time_s, pos_mm, q_global, loader_report = parse_optitrack_csv(csv_path, schema)
        pos_m = pos_mm / 1000.0
        q_global = quat_enforce_continuity(quat_shortest(quat_normalize(q_global)))
        
        # 2. Resample
        fs_target = cfg["FS_TARGET"]
        t_dst = resample_time_grid(time_s, fs_target)
        if cfg["TIME_REG_POLICY"] == "resample_to_fs_target":
            pos_m = resample_pos(time_s, pos_m, t_dst, method=cfg["POS_RESAMPLE_METHOD"])
            q_global = resample_quat_slerp(time_s, q_global, t_dst)
            frame_idx = np.arange(len(t_dst))
            time_s = t_dst

        # 3. Local & Ref
        q_local = compute_q_local(q_global, schema)
        
        joint_names = list(schema["joint_names"])
        j2i = {j: i for i, j in enumerate(joint_names)}
        viz_idx = [j2i[j] for j in cfg["JOINTS_VIZ"] if j in j2i]
        
        ref_info = detect_static_reference(time_s, q_local, viz_idx, cfg)
        export_idx = [i for i, g in enumerate(seg_map["group"]) if g not in cfg["EXCLUDE_GROUPS"]]
        q_ref, ref_qc = compute_q_ref_and_ref_qc(time_s, q_local, ref_info, export_idx, viz_idx, cfg)

        # 4. Kinematics & QC
        rotvec, rv_mag, omega, omega_mag = compute_kinematics(q_local, q_ref, fs_target)
        df_bones, bone_sum = bone_length_qc(pos_m, schema, np.ones(len(joint_names), dtype=bool), cfg)

        # 5. Crop
        t0, t1 = cfg["CROP_SEC"]
        mask = (time_s >= (time_s[0] + t0)) & (time_s <= (time_s[0] + t1))
        idxs = np.where(mask)[0]
        if len(idxs) < 5: idxs = np.arange(len(time_s)) # Fallback
        
        # Helper to crop
        crop = lambda x: x[idxs] if x is not None else None
        
        # 6. Derivatives
        vpos_world = compute_derivatives(crop(pos_m), fs_target, cfg)
        root_idx = j2i.get(schema.get("root_joint", "Hips"), 0)
        pos_rootrel = crop(pos_m) - crop(pos_m)[:, root_idx:root_idx+1, :]
        vpos_rootrel = compute_derivatives(pos_rootrel, fs_target, cfg)

        # 7. Export
        qc_valid = np.ones(len(idxs), dtype=bool) # Simplified validity
        joints_export_mask = np.array([g not in cfg["EXCLUDE_GROUPS"] for g in seg_map["group"]])
        joints_viz_mask = np.array([j in cfg["JOINTS_VIZ"] for j in joint_names])

        df_full, df_viz = build_master_tables(
            run_id, crop(time_s), crop(frame_idx), joint_names,
            joints_export_mask, joints_viz_mask, qc_valid,
            crop(pos_m), pos_rootrel, crop(rotvec), crop(rv_mag),
            crop(omega), crop(omega_mag), vpos_world, vpos_rootrel
        )
        
        if cfg["WRITE_FULL_CSV"]: df_full.to_csv(os.path.join(out_dir, f"{run_id}__full.csv"), index=False)
        if cfg["WRITE_VIZ_CSV"]: df_viz.to_csv(os.path.join(out_dir, f"{run_id}__viz.csv"), index=False)
        
        ctx.metrics.update(ref_qc)
        ctx.metrics.update(bone_sum)
        write_json(os.path.join(out_dir, f"{run_id}__metrics.json"), ctx.metrics)
        
        return {"status": "PASS", "out_dir": out_dir}

    except Exception as e:
        print(f"Pipeline failed: {e}")
        return {"status": "FAIL", "error": str(e)}
    finally:
        gc.collect()