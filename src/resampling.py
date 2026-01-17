import numpy as np
from scipy.interpolate import CubicSpline, interp1d
from scipy.spatial.transform import Rotation as R, Slerp

from .quaternion_ops import (
    quat_normalize,
    quat_shortest,
    quat_enforce_continuity
)

def estimate_fs(time_s):
    dt = np.diff(time_s)
    dt = dt[np.isfinite(dt)]
    if len(dt) == 0:
        return float("nan")
    return float(1.0 / np.median(dt))

def resample_time_grid(time_s, fs_target):
    t0 = float(time_s[0])
    t1 = float(time_s[-1])
    n = int(round((t1 - t0) * fs_target)) + 1
    return t0 + np.arange(n) / fs_target

def resample_pos(time_s, pos, t_dst, method):
    T, J, C = pos.shape
    out = np.full((len(t_dst), J, C), np.nan)
    for j in range(J):
        for c in range(C):
            x = pos[:, j, c]
            valid = np.isfinite(x) & np.isfinite(time_s)
            if valid.sum() < 4:
                if valid.sum() >= 2:
                    f = interp1d(time_s[valid], x[valid],
                                 kind="linear",
                                 bounds_error=False,
                                 fill_value=np.nan,
                                 assume_sorted=True)
                    out[:, j, c] = f(t_dst)
                continue
            tv = time_s[valid]
            xv = x[valid]
            if method == "linear":
                f = interp1d(tv, xv, kind="linear",
                             bounds_error=False,
                             fill_value=np.nan,
                             assume_sorted=True)
                out[:, j, c] = f(t_dst)
            elif method == "cubic_spline":
                cs = CubicSpline(tv, xv, extrapolate=False)
                out[:, j, c] = cs(t_dst)
            else:
                raise ValueError(f"Unknown resample method: {method}")
    return out

def resample_quat_slerp(time_s, q, t_dst):
    T, J, _ = q.shape
    out = np.full((len(t_dst), J, 4), np.nan)
    for j in range(J):
        qj = q[:, j, :]
        valid = np.isfinite(qj).all(axis=1)
        if valid.sum() < 2:
            continue
        tv = time_s[valid]
        qv = quat_enforce_continuity(quat_normalize(qj[valid]))
        rot = R.from_quat(qv)
        s = Slerp(tv, rot)
        mask = (t_dst >= tv[0]) & (t_dst <= tv[-1])
        if mask.any():
            out[mask, j, :] = s(t_dst[mask]).as_quat()
        out[:, j, :] = quat_shortest(quat_normalize(out[:, j, :]))
    return out