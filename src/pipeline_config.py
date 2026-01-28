import os
import yaml

# --- 1. Path Setup ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR) # Go up one level to root
CONFIG_YAML_PATH = os.path.join(PROJECT_ROOT, "config", "config_v1.yaml")

# --- 2. Load YAML (Directories) ---
def load_yaml_config():
    if not os.path.exists(CONFIG_YAML_PATH):
        print(f"WARNING: Config file not found at {CONFIG_YAML_PATH}. Using default paths.")
        return {
            "project_root": ".",
            "derivatives_dir": "derivatives",
            "qc_dir": "qc",
            "data_dir": "data"
        }
        
    with open(CONFIG_YAML_PATH, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")
            return {}

# --- 3. Define Pipeline Settings (Hardcoded defaults) ---
PIPELINE_SETTINGS = {
    "PIPELINE_VERSION": "v1.0_scipy",
    "FS_TARGET": 120.0,

    "TIME_REG_POLICY": "resample_to_fs_target",
    "POS_RESAMPLE_METHOD": "cubic_spline",
    "QUAT_RESAMPLE_METHOD": "slerp",

    "EXCLUDE_GROUPS": ["Fingers", "Toes"],
    "exclude_fingers": False,  # Exclude finger and toe segments from preprocessing

    "JOINTS_VIZ": ["Hips", "Spine", "Spine1", "Neck", "Head", "LeftArm", "RightArm", "LeftUpLeg", "RightUpLeg"],
    "REQUIRED_JOINTS": ["Hips", "Spine", "Head"],

    "CROP_SEC": [10.0, 110.0],

    "REF_ANCHOR": "static_detection_pre_crop",
    "REF_SEARCH_SEC": 8.0,
    "REF_WINDOW_SEC": 1.0,
    "STATIC_SEARCH_STEP_SEC": 0.1,

    "MOTION_THR_LOW": 0.30,
    "MOTION_THR_STD": 0.15,

    "MISSING_POLICY_POS": "interp_linear_or_spline",
    "MISSING_POLICY_QUAT": "interp_slerp",
    "MAX_GAP_POS_SEC": 1.0,
    "MAX_GAP_QUAT_SEC": 0.25,

    "SHORTEST_ROTATION": True,
    "ROTATION_REP": "rotvec_relative_reference",
    "OMEGA_METHOD": "quat_log",
    "OMEGA_FRAME": "child_body",

    "DERIV_METHOD": "savgol",
    "SG_TARGETS": "derivatives_only",
    "SG_WINDOW_SEC": 0.175,
    "SG_POLYORDER": 3,

    "WRITE_FULL_CSV": True,
    "WRITE_FULL_PARQUET": True,
    "WRITE_VIZ_CSV": True,

    "WRITE_RUN_LOG_JSONL": False,
    "WRITE_GLOBAL_EVENTS_JSONL": False,

    "REGISTRY_COMMIT_MODE": "batch_commit_only",

    "THRESH": {
        "FS_TOL_FRAC": 0.01,
        "MISSING_WARN_FRAC": 0.05,
        "MISSING_ALERT_FRAC": 0.10,
        "EPS_REF_RV_RAD": 0.02,
        "REF_QUALITY_STD_RAD_WARN": 0.03,
        "REF_QUALITY_STD_RAD_ALERT": 0.05,
        "OMEGA_P99_WARN": 30.0,
        "OMEGA_P99_ALERT": 60.0,
        "BONE_CV_WARN": 0.02,
        "BONE_CV_ALERT": 0.05,
        "BONE_P95_ABS_DEV_WARN_M": 0.01,
        "BONE_MAX_JUMP_ALERT_M": 0.03,
    },

    "HEALTH_FALLBACK_CAP": 59,
    "HEALTH_WEIGHTS": {"missing": 25.0, "ref": 25.0, "omega": 25.0, "bone": 25.0},
}

# --- 4. Merge & Export Final CONFIG ---
# Start with pipeline settings
CONFIG = PIPELINE_SETTINGS.copy()

# Update with paths from YAML (this adds 'derivatives_dir', etc.)
yaml_settings = load_yaml_config()
CONFIG.update(yaml_settings)