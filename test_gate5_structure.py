#!/usr/bin/env python3
"""
Test Gate 5 Integration: Simulate Expected Output
==================================================
This script shows what the Step 06 JSON should contain after Gate 5 processing.
It creates a mock example to demonstrate the expected data structure.

Run this to understand what data structure you're looking for when verifying
that Gate 5 has been properly executed.

Author: Gaga Pipeline
Date: 2026-01-23
"""

import json
from pprint import pprint

def create_mock_gate5_data():
    """
    Create a mock example of what Gate 5 adds to the Step 06 JSON.
    """
    return {
        # ... existing Step 06 fields (metrics, signal_quality, etc.) ...
        
        # =====================================================================
        # GATE 5 ADDITIONS START HERE
        # =====================================================================
        
        "step_06_burst_analysis": {
            "classification": {
                "artifact_count": 234,    # Tier 1: 1-3 frames, EXCLUDE
                "burst_count": 45,         # Tier 2: 4-7 frames, REVIEW
                "flow_count": 12,          # Tier 3: 8+ frames, ACCEPT
                "total_events": 291        # Sum of all events
            },
            "frame_statistics": {
                "total_frames": 30798,
                "artifact_frames": 567,    # Total frames marked as artifacts
                "burst_frames": 234,       # Total frames in burst events
                "flow_frames": 189,        # Total frames in flow events
                "artifact_rate_percent": 1.84,    # 567/30798 * 100
                "outlier_frames_total": 990,      # artifact + burst + flow frames
                "outlier_rate_percent": 3.21      # 990/30798 * 100
            },
            "timing": {
                "recording_duration_sec": 256.65,
                "burst_events_per_min": 6.81,    # Event density assessment
                "max_consecutive_frames": 23,     # Longest event duration
                "mean_event_duration_ms": 18.45,
                "max_event_duration_ms": 175.2
            },
            "density_assessment": {
                "status": "ACCEPTABLE",           # ACCEPTABLE / HIGH / EXCESSIVE
                "reason": "Event density within normal range for Gaga movement"
            },
            "events": [
                # First 50 events (truncated for JSON size)
                {
                    "event_id": 1,
                    "joint": "Left_Shoulder_Flexion",
                    "joint_idx": 3,
                    "start_frame": 1234,
                    "end_frame": 1237,
                    "duration_frames": 3,
                    "duration_ms": 25.0,
                    "max_velocity_deg_s": 2156.7,
                    "mean_velocity_deg_s": 2089.3,
                    "tier": 1,                   # 1=ARTIFACT, 2=BURST, 3=FLOW
                    "tier_name": "ARTIFACT",
                    "status": "REVIEW",
                    "action": "EXCLUDE"
                },
                {
                    "event_id": 2,
                    "joint": "Right_Elbow_Flexion",
                    "joint_idx": 7,
                    "start_frame": 2456,
                    "end_frame": 2462,
                    "duration_frames": 6,
                    "duration_ms": 50.0,
                    "max_velocity_deg_s": 2234.1,
                    "mean_velocity_deg_s": 2178.5,
                    "tier": 2,
                    "tier_name": "BURST",
                    "status": "REVIEW",
                    "action": "INCLUDE_FLAGGED"
                },
                {
                    "event_id": 3,
                    "joint": "Left_Shoulder_Abduction",
                    "joint_idx": 4,
                    "start_frame": 5678,
                    "end_frame": 5690,
                    "duration_frames": 12,
                    "duration_ms": 100.0,
                    "max_velocity_deg_s": 2445.3,
                    "mean_velocity_deg_s": 2289.7,
                    "tier": 3,
                    "tier_name": "FLOW",
                    "status": "ACCEPT_HIGH_INTENSITY",
                    "action": "INCLUDE"
                }
                # ... up to 50 events total
            ]
        },
        
        "step_06_burst_decision": {
            "overall_status": "ACCEPT_HIGH_INTENSITY",   # or REVIEW or REJECT
            "primary_reason": "High-intensity movement confirmed: 12 sustained flow events (>65ms each)"
        },
        
        "step_06_frames_to_exclude": [
            # Artifact frames (Tier 1) to exclude from statistics
            # Truncated to first 1000 for JSON size
            1234, 1235, 1236, 3456, 3457, 3458, 
            # ... etc
        ],
        
        "step_06_frames_to_review": [
            # Burst/Flow frames (Tier 2/3) for manual review
            # Truncated to first 1000 for JSON size
            2456, 2457, 2458, 2459, 2460, 2461, 2462,
            5678, 5679, 5680, 5681, 5682, 5683, 5684, 5685, 5686, 5687, 5688, 5689, 5690,
            # ... etc
        ],
        
        "step_06_data_validity": {
            "usable": True,
            "excluded_frame_count": 567,
            "excluded_frame_percent": 1.84,
            "note": "567 artifact frames excluded; burst/flow frames preserved"
        },
        
        # Additional Gate 4 fields (ISB Euler compliance)
        "step_06_isb_compliant": True,
        "step_06_euler_sequences": {
            "Shoulder_Left": "YXY",
            "Shoulder_Right": "YXY",
            "Elbow_Left": "ZXY",
            "Elbow_Right": "ZXY"
        },
        "step_06_math_status": "PASS",
        "step_06_math_decision_reason": "Quaternion stability maintained (max norm error: 0.000001)",
        
        # Overall gate status (combination of Gate 4 and Gate 5)
        "overall_gate_status": "ACCEPT_HIGH_INTENSITY",
        
        # Reference to the parquet mask file
        "step_06_joint_status_mask_file": "734_T1_P1_R1_Take 2025-12-01 02.18.27 PM__joint_status_mask.parquet"
    }


def print_expected_structure():
    """Print the expected JSON structure with explanations."""
    print("=" * 100)
    print("EXPECTED GATE 5 DATA STRUCTURE")
    print("=" * 100)
    print("\nThis is what should be ADDED to the Step 06 kinematics_summary.json file")
    print("after running the 'GATE 4 & 5 INTEGRATION' cell in notebook 06.")
    print("\n" + "=" * 100)
    
    mock_data = create_mock_gate5_data()
    
    # Pretty print the mock data
    pprint(mock_data, width=100, indent=2)
    
    print("\n" + "=" * 100)
    print("KEY FIELDS EXPLANATION")
    print("=" * 100)
    
    explanations = {
        "step_06_burst_analysis.classification": 
            "Event counts by tier (artifact/burst/flow)",
        
        "step_06_burst_analysis.frame_statistics": 
            "Frame-level statistics including artifact rate %",
        
        "step_06_burst_analysis.timing": 
            "Temporal metrics for event duration and density",
        
        "step_06_burst_analysis.density_assessment": 
            "Assessment of whether event frequency indicates data quality issue",
        
        "step_06_burst_analysis.events": 
            "List of individual high-velocity events (first 50)",
        
        "step_06_burst_decision": 
            "Overall quality decision (ACCEPT_HIGH_INTENSITY/REVIEW/REJECT)",
        
        "step_06_frames_to_exclude": 
            "Frame indices marked as Tier 1 artifacts (EXCLUDE from stats)",
        
        "step_06_frames_to_review": 
            "Frame indices marked as Tier 2/3 (bursts/flows) for manual review",
        
        "step_06_data_validity": 
            "Usability assessment and frame exclusion summary",
        
        "step_06_joint_status_mask_file": 
            "Reference to parquet file with per-frame status codes"
    }
    
    print()
    for field, explanation in explanations.items():
        print(f"  {field:<50} - {explanation}")
    
    print("\n" + "=" * 100)
    print("TIER CLASSIFICATION LOGIC")
    print("=" * 100)
    print("""
  Tier 1 - ARTIFACT (1-3 frames, <25ms):
    - Physically impossible spike
    - Action: EXCLUDE from all statistics
    - Example: Sensor glitch, momentary occlusion
    
  Tier 2 - BURST (4-7 frames, 33-58ms):
    - Rapid movement, possible whip/shake
    - Action: INCLUDE but flag for REVIEW
    - Example: Quick arm flick, sudden weight shift
    
  Tier 3 - FLOW (8+ frames, >65ms):
    - Sustained high-velocity movement
    - Action: ACCEPT as legitimate Gaga movement
    - Example: Continuous spinning, sustained jump
    """)
    
    print("\n" + "=" * 100)
    print("STEP 07 COLUMNS POPULATED BY THIS DATA")
    print("=" * 100)
    print("""
  The Master Quality Report (notebook 07) extracts these fields to populate
  the following columns in the Excel output:
  
  From step_06_burst_analysis.classification:
    - Burst_Artifact_Count
    - Burst_Count
    - Burst_Flow_Count
    - Burst_Total_Events
    
  From step_06_burst_analysis.frame_statistics:
    - Artifact_Rate_%
    
  From step_06_burst_analysis.timing:
    - Max_Consecutive_Frames
    - Mean_Event_Duration_ms
    
  From step_06_burst_decision:
    - Burst_Decision
    - Burst_Decision_Reason
    
  From step_06_frames_to_exclude:
    - Artifact_Frame_Ranges (converted to readable ranges like "1234-1236")
    
  From step_06_frames_to_review:
    - Burst_Frame_Ranges
    
  From step_06_data_validity:
    - Data_Usable
    - Excluded_Frames
    """)
    
    print("\n" + "=" * 100)
    print("HOW TO VERIFY")
    print("=" * 100)
    print("""
  After running the Gate 5 cell for a recording:
  
  1. Check the JSON file manually:
     
     import json
     json_path = "derivatives/step_06_kinematics/{RUN_ID}__kinematics_summary.json"
     with open(json_path) as f:
         data = json.load(f)
     
     # Should return True:
     print('step_06_burst_analysis' in data)
     print('step_06_burst_decision' in data)
     
     # Print event counts:
     print(data['step_06_burst_analysis']['classification'])
     
  2. Run the verification script:
     
     python verify_gate5_data.py
     
     Should show: "[OK] With Gate 5 Data: 1 (X%)"
     
  3. Check the parquet mask file exists:
     
     import os
     mask_file = f"derivatives/step_06_kinematics/{RUN_ID}__joint_status_mask.parquet"
     print(os.path.exists(mask_file))  # Should be True
    """)
    
    print("=" * 100)


def save_mock_json_example():
    """Save a mock JSON file for reference."""
    mock_data = {
        "run_id": "MOCK_EXAMPLE_RUN",
        "overall_status": "PASS",
        "metrics": {
            "angular_velocity": {"max": 1026.98, "limit": 1500.0, "status": True}
        },
        **create_mock_gate5_data()
    }
    
    output_path = "docs/examples/mock_gate5_kinematics_summary.json"
    
    # Create directory if needed
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(mock_data, f, indent=4)
    
    print(f"\n[OK] Mock JSON example saved to: {output_path}")
    print("     Use this as a reference for what the Gate 5 data should look like.")


if __name__ == "__main__":
    print_expected_structure()
    
    # Optionally save a mock example
    try:
        save_mock_json_example()
    except Exception as e:
        print(f"\n[WARNING] Could not save mock JSON: {e}")
        print("         (This is OK - the printed structure above is the main reference)")
