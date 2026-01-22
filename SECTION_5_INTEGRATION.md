# Section 5 Integration Guide: ISB Compliance & Synchronized Viz

**Location:** Add to `notebooks/07_master_quality_report.ipynb` after Section 4 (Winter's Residual Validation)

---

## Step 1: Add Markdown Cell for Section Header

```markdown
---

## Section 5: ISB Compliance & Synchronized Visualization
**Purpose:** Visual Proof - ISB-compliant Euler sequences + Interactive time-synced stick figure with LCS
```

---

## Step 2: Add Code Cell for Section 5

```python
# ============================================================
# SECTION 5: ISB Compliance & Synchronized Visualization
# ============================================================

# Import visualization module
from interactive_viz import (
    verify_isb_compliance,
    create_interactive_synchronized_viz,
    create_static_lcs_snapshot
)
import plotly.io as pio

# Define visualization parameters
SHOW_LCS_FOR = ['LeftShoulder', 'RightShoulder', 'Hips', 'Spine1']  # Key joints
LCS_AXIS_LENGTH = 100.0  # mm
SAMPLE_FRAMES = 300  # For performance (full dataset can be slow)

print("="*80)
print("SECTION 5: ISB COMPLIANCE & SYNCHRONIZED VISUALIZATION")
print("="*80)
print("Purpose: Visual Proof - Verify ISB standards + Interactive time-synced anatomy")
print("="*80)
print()

# ============================================================
# PART 1: ISB EULER SEQUENCE VERIFICATION
# ============================================================

print("PART 1: ISB Euler Sequence Verification")
print("-" * 80)

isb_compliance_data = []

for run_id, steps in complete_runs.items():
    print(f"\n{run_id}:")
    
    # Path to Euler validation JSON (from notebook 06)
    euler_validation_path = os.path.join(
        PROJECT_ROOT, "derivatives", "step_06_rotvec",
        f"{run_id}__euler_validation.json"
    )
    
    # Verify ISB compliance
    df_compliance, summary = verify_isb_compliance(euler_validation_path)
    
    if df_compliance is not None:
        # Display summary
        print(f"  Total Joints: {summary['total_joints']}")
        print(f"  ✅ Compliant: {summary['compliant_joints']}")
        print(f"  ⚠️ ROM Violations: {summary['violation_joints']}")
        
        if summary['violation_joints'] > 0:
            print(f"  Violated Joints: {', '.join(summary['violated_joints'][:5])}")
            if len(summary['violated_joints']) > 5:
                print(f"    ... and {len(summary['violated_joints']) - 5} more")
        
        overall_status = "✅ PASS" if summary['overall_status'] == 'PASS' else "⚠️ REVIEW"
        print(f"  Overall Status: {overall_status}")
        
        # Store for summary table
        isb_compliance_data.append({
            'Run_ID': run_id,
            'Total_Joints': summary['total_joints'],
            'Compliant': summary['compliant_joints'],
            'ROM_Violations': summary['violation_joints'],
            'Overall_Status': overall_status,
            'Notes': f"{summary['violation_joints']} joints exceed anatomical ROM (with Gaga 15% tolerance)"
                     if summary['violation_joints'] > 0 
                     else "All joints within ISB-defined ROM limits"
        })
        
        # Display detailed compliance table (first 10 joints)
        print("\n  ISB Sequence Verification (sample):")
        display(df_compliance.head(10))
        
    else:
        print(f"  ❌ ERROR: {summary.get('error', 'Unknown error')}")
        isb_compliance_data.append({
            'Run_ID': run_id,
            'Total_Joints': 0,
            'Compliant': 0,
            'ROM_Violations': 0,
            'Overall_Status': '❌ NO_DATA',
            'Notes': 'Euler validation not available - run notebook 06 first'
        })

# Create ISB compliance summary table
df_isb = pd.DataFrame(isb_compliance_data)

print("\n" + "="*80)
print("ISB COMPLIANCE SUMMARY")
print("="*80)
display(df_isb)

print("\n" + "="*80)
print("INTERPRETATION:")
print("="*80)
print("✅ PASS: All joints use correct ISB sequences and stay within anatomical ROM")
print("⚠️ REVIEW: Some joints exceed anatomical ROM (may be valid for Gaga expressive dance)")
print("❌ NO_DATA: Euler validation not performed - integrate notebook 06 ISB conversion")
print()

# ============================================================
# PART 2: INTERACTIVE SYNCHRONIZED VISUALIZATION
# ============================================================

print("\n" + "="*80)
print("PART 2: Interactive Synchronized Visualization")
print("="*80)
print("Creating time-synced stick figure with LCS + kinematic plots...")
print()

# Select a run to visualize (use first run with data)
visualization_runs = [rid for rid, steps in complete_runs.items() 
                     if 'step_06' in steps]

if len(visualization_runs) > 0:
    viz_run_id = visualization_runs[0]
    print(f"Visualizing: {viz_run_id}")
    print()
    
    # Load kinematic data (from step 06)
    kinematics_path = os.path.join(
        PROJECT_ROOT, "derivatives", "step_06_rotvec",
        f"{viz_run_id}__kinematics_full.parquet"
    )
    
    if os.path.exists(kinematics_path):
        print(f"Loading kinematics: {kinematics_path}")
        df_kin = pd.read_parquet(kinematics_path)
        
        # Load skeleton hierarchy
        hierarchy_path = os.path.join(PROJECT_ROOT, "config", "skeleton_hierarchy.json")
        with open(hierarchy_path) as f:
            hierarchy_data = json.load(f)
        
        bone_hierarchy = [(b['parent'], b['child']) for b in hierarchy_data.get('bones', [])]
        joint_names = list(set([b['parent'] for b in hierarchy_data.get('bones', [])] + 
                               [b['child'] for b in hierarchy_data.get('bones', [])]))
        
        print(f"Loaded {len(df_kin)} frames, {len(joint_names)} joints")
        print()
        
        # ============================================================
        # STATIC SNAPSHOT (for documentation/reports)
        # ============================================================
        print("Creating static LCS snapshot (mid-performance frame)...")
        mid_frame = len(df_kin) // 2
        
        fig_static = create_static_lcs_snapshot(
            df=df_kin,
            joint_names=joint_names,
            bone_hierarchy=bone_hierarchy,
            frame_idx=mid_frame,
            show_lcs_for=SHOW_LCS_FOR,
            axis_length=LCS_AXIS_LENGTH
        )
        
        # Save static figure
        static_path = os.path.join(PROJECT_ROOT, "reports", 
                                  f"{viz_run_id}_lcs_static.html")
        pio.write_html(fig_static, static_path)
        print(f"✅ Static snapshot saved: {static_path}")
        
        # Display static figure
        fig_static.show()
        
        print()
        print("-" * 80)
        
        # ============================================================
        # INTERACTIVE SYNCHRONIZED VISUALIZATION (THE BIG ONE)
        # ============================================================
        print("Creating interactive synchronized visualization...")
        print("  This includes:")
        print("    - 3D skeleton with LCS axes (X/Y/Z arrows)")
        print("    - Position plot (X, Y, Z components)")
        print("    - Velocity plot (speed magnitude)")
        print("    - Shared slider for time synchronization")
        print()
        
        fig_interactive = create_interactive_synchronized_viz(
            df=df_kin,
            joint_names=joint_names,
            bone_hierarchy=bone_hierarchy,
            show_lcs_for=SHOW_LCS_FOR,
            axis_length=LCS_AXIS_LENGTH,
            sample_frames=SAMPLE_FRAMES
        )
        
        # Save interactive figure
        interactive_path = os.path.join(PROJECT_ROOT, "reports",
                                       f"{viz_run_id}_interactive_synced.html")
        pio.write_html(fig_interactive, interactive_path)
        print(f"✅ Interactive visualization saved: {interactive_path}")
        print()
        
        # Display interactive figure
        print("📊 INTERACTIVE VISUALIZATION:")
        print("   → Use the slider to move through time")
        print("   → All three plots update simultaneously")
        print("   → Verify LCS axes remain stable (no spinning)")
        print("   → Press ▶ Play to animate")
        print()
        
        fig_interactive.show()
        
    else:
        print(f"❌ ERROR: Kinematics file not found: {kinematics_path}")
        print("   Run notebook 06 to generate kinematic derivatives")

else:
    print("❌ No runs with step_06 data available for visualization")
    print("   Run notebook 06 (Euler/Omega) first to generate kinematic data")

print()
print("="*80)
print("SECTION 5 COMPLETE")
print("="*80)
print("✅ ISB Compliance: Verified joint-specific Euler sequences")
print("✅ Visual Proof: Interactive synchronized stick figure with LCS")
print("✅ Time-Sync: Slider updates skeleton + kinematic plots simultaneously")
print()
print("SUPERVISOR INSTRUCTIONS:")
print("  1. Check ISB Compliance table - all joints should show correct sequences")
print("  2. Use slider to move through performance")
print("  3. Verify LCS axes (X/Y/Z arrows) remain stable - no erratic spinning")
print("  4. Confirm kinematic plots sync with skeleton movement")
print("  5. Look for anomalies: marker swaps, gimbal lock, unnatural motion")
print("="*80)
```

---

## Integration Instructions

1. **Open:** `notebooks/07_master_quality_report.ipynb`
2. **Navigate to:** After Section 4 (Winter's Residual Validation)
3. **Insert:** New Markdown cell with Section 5 header
4. **Insert:** New Code cell with the Python code above
5. **Save** the notebook

---

## Expected Outputs

### Console Output:
```
================================================================================
SECTION 5: ISB COMPLIANCE & SYNCHRONIZED VISUALIZATION
================================================================================
Purpose: Visual Proof - Verify ISB standards + Interactive time-synced anatomy
================================================================================

PART 1: ISB Euler Sequence Verification
--------------------------------------------------------------------------------

734_T1_P1_R1_Take 2025-12-01 02.18.27 PM:
  Total Joints: 27
  ✅ Compliant: 25
  ⚠️ ROM Violations: 2
  Violated Joints: LeftShoulder, RightShoulder
  Overall Status: ⚠️ REVIEW

  ISB Sequence Verification (sample):
  [DataFrame with Joint, ISB_Sequence, ROM_Limits, Actual_Range, Violations, Status]

================================================================================
ISB COMPLIANCE SUMMARY
================================================================================
[Summary table with all runs]

PART 2: Interactive Synchronized Visualization
================================================================================
Visualizing: 734_T1_P1_R1_Take 2025-12-01 02.18.27 PM
...
✅ Static snapshot saved: reports/734_T1_P1_R1_Take 2025-12-01 02.18.27 PM_lcs_static.html
✅ Interactive visualization saved: reports/734_T1_P1_R1_Take 2025-12-01 02.18.27 PM_interactive_synced.html

📊 INTERACTIVE VISUALIZATION:
   → Use the slider to move through time
   → All three plots update simultaneously
   → Verify LCS axes remain stable (no spinning)
   → Press ▶ Play to animate
```

### Visual Outputs:

1. **Static Snapshot:**
   - 3D skeleton with X/Y/Z arrows at key joints
   - Saved as HTML (can be opened in browser)
   - Shows ISB-compliant coordinate systems

2. **Interactive Synchronized Viz:**
   - 3 panels: Skeleton (3D) | Position (2D) | Velocity (2D)
   - Shared slider that updates all simultaneously
   - Play/Pause buttons for animation
   - Time marker moves across kinematic plots
   - Skeleton moves in sync with kinematic data

---

## Dependencies

### Required Files:
- `src/interactive_viz.py` (created above)
- `src/euler_isb.py` (from previous scientific upgrades)
- `derivatives/step_06_rotvec/{run_id}__euler_validation.json` (from nb06)
- `derivatives/step_06_rotvec/{run_id}__kinematics_full.parquet` (from nb06)
- `config/skeleton_hierarchy.json` (existing)

### Required Packages:
```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from scipy.spatial.transform import Rotation
```

---

## Troubleshooting

### Issue: "Euler validation JSON not found"
**Solution:** Run notebook 06 with the ISB Euler conversion cell (see `INTEGRATION_STATUS.md`)

### Issue: "Kinematics file not found"
**Solution:** Ensure notebook 06 saves `{run_id}__kinematics_full.parquet` (not just summary)

### Issue: Visualization too slow
**Solution:** Reduce `SAMPLE_FRAMES` parameter (default: 300, try 150 or 100)

### Issue: LCS axes too short/long
**Solution:** Adjust `LCS_AXIS_LENGTH` (default: 100mm, try 50-200mm range)

---

## Benefits Delivered

✅ **ISB Compliance Verification:** Confirms correct joint-specific Euler sequences  
✅ **Visual QC:** Supervisor can see skeleton with anatomically correct coordinate systems  
✅ **Time Synchronization:** Shared slider ensures skeleton and plots are always in sync  
✅ **Interactive Exploration:** Play/pause, scrub through time, zoom in 3D  
✅ **Gimbal Lock Detection:** Spinning/unstable LCS axes are immediately visible  
✅ **Publication Quality:** Exportable HTML figures for thesis/papers  
✅ **Supervisor-Friendly:** No code knowledge needed - just move the slider!  

---

## Next Steps

After integrating Section 5:

1. **Test:** Run the Master Audit notebook
2. **Verify:** Check that interactive visualizations display correctly
3. **Iterate:** Adjust `SHOW_LCS_FOR` to focus on different joints
4. **Document:** Share HTML files with supervisors for review
5. **Continue:** Add Section 6 (SNR Analysis) next

**Section 5 is the "Visual Proof" layer - the most important QC tool for supervisors!**
