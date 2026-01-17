import pandas as pd
import numpy as np
import csv
import re
from pathlib import Path
from utils import normalize_joint_name

def correct_motive_name(raw_name):
    """
    Maps Motive/OptiTrack abbreviations to standard schema names.
    """
    # 1. Handle "Asset:Bone" format
    if ":" in raw_name:
        parts = raw_name.split(":")
        asset = parts[0]
        bone = parts[-1]
        
        # FIX: If Bone Name == Asset Name (e.g. "763:763"), it is the Hips/Root
        if asset == bone:
            return "Hips"
        
        name = bone
    else:
        name = raw_name
        
    name = name.strip()

    # 2. Manual Mapping Dictionary
    mapping = {
        # Torso
        "Ab": "Spine",
        "Chest": "Spine1",
        "Hip": "Hips", 
        "Root": "Hips", # Just in case
        
        # Left Arm
        "LShoulder": "LeftShoulder",
        "LUArm": "LeftArm",
        "LFArm": "LeftForeArm",
        "LHand": "LeftHand",
        
        # Right Arm
        "RShoulder": "RightShoulder",
        "RUArm": "RightArm",
        "RFArm": "RightForeArm",
        "RHand": "RightHand",
        
        # Left Leg
        "LThigh": "LeftUpLeg",
        "LShin": "LeftLeg",
        "LFoot": "LeftFoot",
        "LToe": "LeftToeBase",
        
        # Right Leg
        "RThigh": "RightUpLeg",
        "RShin": "RightLeg",
        "RFoot": "RightFoot",
        "RToe": "RightToeBase",
        
        # Hands (Fingers)
        "LThumb1": "LeftHandThumb1", "LThumb2": "LeftHandThumb2", "LThumb3": "LeftHandThumb3",
        "LIndex1": "LeftHandIndex1", "LIndex2": "LeftHandIndex2", "LIndex3": "LeftHandIndex3",
        "LMiddle1": "LeftHandMiddle1", "LMiddle2": "LeftHandMiddle2", "LMiddle3": "LeftHandMiddle3",
        "LRing1": "LeftHandRing1", "LRing2": "LeftHandRing2", "LRing3": "LeftHandRing3",
        "LPinky1": "LeftHandPinky1", "LPinky2": "LeftHandPinky2", "LPinky3": "LeftHandPinky3",
        
        "RThumb1": "RightHandThumb1", "RThumb2": "RightHandThumb2", "RThumb3": "RightHandThumb3",
        "RIndex1": "RightHandIndex1", "RIndex2": "RightHandIndex2", "RIndex3": "RightHandIndex3",
        "RMiddle1": "RightHandMiddle1", "RMiddle2": "RightHandMiddle2", "RMiddle3": "RightHandMiddle3",
        "RRing1": "RightHandRing1", "RRing2": "RightHandRing2", "RRing3": "RightHandRing3",
        "RPinky1": "RightHandPinky1", "RPinky2": "RightHandPinky2", "RPinky3": "RightHandPinky3",
    }
    
    return mapping.get(name, name)

def parse_optitrack_csv(csv_path, schema):
    path = Path(csv_path)
    
    # --- 1. Robustly Read Rows ---
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            rows.append(row)
            if i >= 300: break

    # Find Header Row
    hdr_row_idx = None
    for i, row in enumerate(rows):
        row_lower = [str(x).strip().lower() for x in row]
        if "frame" in row_lower and any(t in row_lower for t in ["time", "time (seconds)"]):
            hdr_row_idx = i
            break
            
    if hdr_row_idx is None:
        raise ValueError("CRITICAL: Could not locate 'Frame' and 'Time' row.")

    # Find Name Row
    name_row = None
    name_row_idx = None
    for i in range(hdr_row_idx):
        if len(rows[i]) > 1 and str(rows[i][1]).strip().lower() == "name":
            name_row = rows[i]
            name_row_idx = i
            break
            
    # --- 2. Load Data ---
    df = pd.read_csv(path, header=None, skiprows=hdr_row_idx + 1, engine="python")
    
    # --- 3. Frame/Time ---
    header_tokens = [str(x).strip() for x in rows[hdr_row_idx]]
    header_lower = [x.lower() for x in header_tokens]
    
    col_frame = header_lower.index("frame") if "frame" in header_lower else 0
    col_time = -1
    for t in ["time (seconds)", "time"]:
        if t in header_lower: col_time = header_lower.index(t); break
    if col_time == -1: col_time = 1

    frame_idx = pd.to_numeric(df.iloc[:, col_frame], errors='coerce').fillna(0).astype(int).values
    time_s = pd.to_numeric(df.iloc[:, col_time], errors='coerce').fillna(0.0).astype(float).values
    T = len(time_s)

    # --- 4. Scan Headers & Map Names ---
    found_cols = {} 
    
    i = 0
    while i < len(header_tokens) - 3:
        if header_tokens[i:i+4] == ["X", "Y", "Z", "W"]:
            raw_name = f"Unknown_{i}"
            if name_row and i < len(name_row):
                raw_name = str(name_row[i]).strip()
            
            # *** APPLY FIX HERE ***
            corrected_name = correct_motive_name(raw_name)
            norm_name = normalize_joint_name(corrected_name)
            
            if norm_name not in found_cols:
                found_cols[norm_name] = {'rot': None, 'pos': None}
            
            found_cols[norm_name]['rot'] = [i, i+1, i+2, i+3]
            i += 4
            
            if i < len(header_tokens) - 2 and header_tokens[i:i+3] == ["X", "Y", "Z"]:
                found_cols[norm_name]['pos'] = [i, i+1, i+2]
                i += 3
        else:
            i += 1

    # --- 5. Fill Arrays ---
    target_joints = list(schema['joint_names'])
    J = len(target_joints)
    
    pos_mm = np.full((T, J, 3), np.nan)
    q_global = np.full((T, J, 4), np.nan)
    
    joints_found = []
    joints_missing = []
    
    for idx, target_name in enumerate(target_joints):
        norm_target = normalize_joint_name(target_name)
        
        if norm_target in found_cols:
            joints_found.append(target_name)
            col = found_cols[norm_target]
            
            if col['rot']:
                indices = col['rot']
                q_global[:, idx, 0] = pd.to_numeric(df.iloc[:, indices[0]], errors='coerce').values
                q_global[:, idx, 1] = pd.to_numeric(df.iloc[:, indices[1]], errors='coerce').values
                q_global[:, idx, 2] = pd.to_numeric(df.iloc[:, indices[2]], errors='coerce').values
                q_global[:, idx, 3] = pd.to_numeric(df.iloc[:, indices[3]], errors='coerce').values
                
            if col['pos']:
                indices = col['pos']
                pos_mm[:, idx, 0] = pd.to_numeric(df.iloc[:, indices[0]], errors='coerce').values
                pos_mm[:, idx, 1] = pd.to_numeric(df.iloc[:, indices[1]], errors='coerce').values
                pos_mm[:, idx, 2] = pd.to_numeric(df.iloc[:, indices[2]], errors='coerce').values
        else:
            joints_missing.append(target_name)

# ... inside parse_optitrack_csv, after the loop ...

    # --- 6. Report ---
    # MISSING LINES ADDED HERE:
    nan_pos_pct = np.mean(np.isnan(pos_mm)) * 100
    nan_rot_pct = np.mean(np.isnan(q_global)) * 100
    
    loader_report = {
        "file_path": str(csv_path),
        "total_frames": T,
        "duration_sec": time_s[-1] - time_s[0] if T > 0 else 0,
        "fps_estimated": 1.0 / np.median(np.diff(time_s)) if T > 1 else 0,
        "segments_expected": J,
        "segments_found_count": len(joints_found),
        "segments_missing_count": len(joints_missing),
        "segments_found_list": joints_found,
        "segments_missing_list": joints_missing,
        "data_quality": {
            "nan_position_percent": f"{nan_pos_pct:.2f}%",
            "nan_rotation_percent": f"{nan_rot_pct:.2f}%"
        },
        "structure_info": {
            "header_row_index": hdr_row_idx,
            "name_row_index": name_row_idx,
            "total_columns": len(header_tokens)
        }
    }

    return frame_idx, time_s, pos_mm, q_global, loader_report