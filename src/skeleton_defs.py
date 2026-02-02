# src/skeleton_defs.py


# Format: 'JointName': {'parent': 'ParentName', 'angle_name': 'OutputName'}

def is_finger_or_toe_segment(joint_name):
    """
    Determines if a joint name represents a finger or toe segment.
    
    Hand Fingers: All segments containing Hand(Thumb|Index|Middle|Ring|Pinky)
    Foot Toes: LeftToeBase, RightToeBase
    
    Parameters:
    -----------
    joint_name : str
        The joint name to check
        
    Returns:
    --------
    bool
        True if the joint is a finger or toe segment, False otherwise
    """
    # Check for hand fingers (Thumb, Index, Middle, Ring, Pinky)
    finger_patterns = ['HandThumb', 'HandIndex', 'HandMiddle', 'HandRing', 'HandPinky']
    if any(pattern in joint_name for pattern in finger_patterns):
        return True
    
    # Check for toe segments
    if joint_name in ['LeftToeBase', 'RightToeBase']:
        return True
    
    return False

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
    
    # --- Fingers (Left) ---
    "LeftHandThumb1": {"parent": "LeftHand", "angle_name": "L_Thumb1"},
    "LeftHandThumb2": {"parent": "LeftHandThumb1", "angle_name": "L_Thumb2"},
    "LeftHandThumb3": {"parent": "LeftHandThumb2", "angle_name": "L_Thumb3"},
    "LeftHandIndex1": {"parent": "LeftHand", "angle_name": "L_Index1"},
    "LeftHandIndex2": {"parent": "LeftHandIndex1", "angle_name": "L_Index2"},
    "LeftHandIndex3": {"parent": "LeftHandIndex2", "angle_name": "L_Index3"},
    "LeftHandMiddle1": {"parent": "LeftHand", "angle_name": "L_Middle1"},
    "LeftHandMiddle2": {"parent": "LeftHandMiddle1", "angle_name": "L_Middle2"},
    "LeftHandMiddle3": {"parent": "LeftHandMiddle2", "angle_name": "L_Middle3"},
    "LeftHandRing1": {"parent": "LeftHand", "angle_name": "L_Ring1"},
    "LeftHandRing2": {"parent": "LeftHandRing1", "angle_name": "L_Ring2"},
    "LeftHandRing3": {"parent": "LeftHandRing2", "angle_name": "L_Ring3"},
    "LeftHandPinky1": {"parent": "LeftHand", "angle_name": "L_Pinky1"},
    "LeftHandPinky2": {"parent": "LeftHandPinky1", "angle_name": "L_Pinky2"},
    "LeftHandPinky3": {"parent": "LeftHandPinky2", "angle_name": "L_Pinky3"},
    
    # --- Fingers (Right) ---
    "RightHandThumb1": {"parent": "RightHand", "angle_name": "R_Thumb1"},
    "RightHandThumb2": {"parent": "RightHandThumb1", "angle_name": "R_Thumb2"},
    "RightHandThumb3": {"parent": "RightHandThumb2", "angle_name": "R_Thumb3"},
    "RightHandIndex1": {"parent": "RightHand", "angle_name": "R_Index1"},
    "RightHandIndex2": {"parent": "RightHandIndex1", "angle_name": "R_Index2"},
    "RightHandIndex3": {"parent": "RightHandIndex2", "angle_name": "R_Index3"},
    "RightHandMiddle1": {"parent": "RightHand", "angle_name": "R_Middle1"},
    "RightHandMiddle2": {"parent": "RightHandMiddle1", "angle_name": "R_Middle2"},
    "RightHandMiddle3": {"parent": "RightHandMiddle2", "angle_name": "R_Middle3"},
    "RightHandRing1": {"parent": "RightHand", "angle_name": "R_Ring1"},
    "RightHandRing2": {"parent": "RightHandRing1", "angle_name": "R_Ring2"},
    "RightHandRing3": {"parent": "RightHandRing2", "angle_name": "R_Ring3"},
    "RightHandPinky1": {"parent": "RightHand", "angle_name": "R_Pinky1"},
    "RightHandPinky2": {"parent": "RightHandPinky1", "angle_name": "R_Pinky2"},
    "RightHandPinky3": {"parent": "RightHandPinky2", "angle_name": "R_Pinky3"},
}