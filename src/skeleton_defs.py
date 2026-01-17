# src/skeleton_defs.py


# Format: 'JointName': {'parent': 'ParentName', 'angle_name': 'OutputName'}

SKELETON_HIERARCHY = {
    # --- Root (Global) ---
    "Hips": {
        "parent": None, 
        "angle_name": "Pelvis_Global_Orientation (World Space)"
    },
    
    # --- Spine ---
    "Spine":   {"parent": "Hips",   "angle_name": "Lumbar_Angle"},
    "Spine1":  {"parent": "Spine",  "angle_name": "Thoracic_Angle"},
    "Neck":    {"parent": "Spine1", "angle_name": "Neck_Base_Angle"},
    "Head":    {"parent": "Neck",   "angle_name": "Head_Angle"},

    # --- Left Leg ---
    "LeftUpLeg":   {"parent": "Hips",      "angle_name": "LeftHip_Angle"},
    "LeftLeg":     {"parent": "LeftUpLeg", "angle_name": "LeftKnee_Angle"},
    "LeftFoot":    {"parent": "LeftLeg",   "angle_name": "LeftAnkle_Angle"},
    "LeftToeBase": {"parent": "LeftFoot",  "angle_name": "LeftToe_Angle"},

    # --- Right Leg ---
    "RightUpLeg":   {"parent": "Hips",       "angle_name": "RightHip_Angle"},
    "RightLeg":     {"parent": "RightUpLeg", "angle_name": "RightKnee_Angle"},
    "RightFoot":    {"parent": "RightLeg",   "angle_name": "RightAnkle_Angle"},
    "RightToeBase": {"parent": "RightFoot",  "angle_name": "RightToe_Angle"},

    # --- Left Arm ---
    "LeftShoulder": {"parent": "Spine1",       "angle_name": "LeftClavicle_Angle"},
    "LeftArm":      {"parent": "LeftShoulder", "angle_name": "LeftShoulder_Joint_Angle"},
    "LeftForeArm":  {"parent": "LeftArm",      "angle_name": "LeftElbow_Angle"},
    "LeftHand":     {"parent": "LeftForeArm",  "angle_name": "LeftWrist_Angle"},

    # --- Right Arm ---
    "RightShoulder": {"parent": "Spine1",        "angle_name": "RightClavicle_Angle"},
    "RightArm":      {"parent": "RightShoulder", "angle_name": "RightShoulder_Joint_Angle"},
    "RightForeArm":  {"parent": "RightArm",      "angle_name": "RightElbow_Angle"},
    "RightHand":     {"parent": "RightForeArm",  "angle_name": "RightWrist_Angle"},
    
    # --- Fingers (Left) - הוסף את כל האצבעות אם אתה דורש בדיקה קשיחה ---
    "LeftHandThumb1": {"parent": "LeftHand", "angle_name": "L_Thumb1"},
    "LeftHandThumb2": {"parent": "LeftHandThumb1", "angle_name": "L_Thumb2"},
    "LeftHandThumb3": {"parent": "LeftHandThumb2", "angle_name": "L_Thumb3"},
    "LeftHandIndex1": {"parent": "LeftHand", "angle_name": "L_Index1"},
    "LeftHandIndex2": {"parent": "LeftHandIndex1", "angle_name": "L_Index2"},
    "LeftHandIndex3": {"parent": "LeftHandIndex2", "angle_name": "L_Index3"},
    # ... להוסיף את שאר האצבעות לפי ה-Schema שלך ...
}