# Clean Max Velocity - Visual Explanation

**What is "Clean Max Velocity" and why does it matter?**

---

## Scenario: Gaga Performance with Sensor Glitch

### Timeline at 120 Hz (120 samples/second)

```
Time: 0.0s ────────────────────────────────────────────────────── 30.0s

                    Sensor Glitch         Real Gaga Movement
                         ↓                        ↓
Frame:  0 ──── 99 ─ 100-101 ─ 102 ──── 499 ─ 500──515 ─ 516 ──── 3600

Velocity:
        ░░░░░░░░░░░░                         ████████████░░░░░░░░░
        Normal      ▲▲                       High        Normal
        (100-800)   Spike                    Intensity   (100-800)
                    2847                     (1400-1500)
                    deg/s                    deg/s
                    
Duration:            16.7 ms                 125 ms
Classification:      ARTIFACT                FLOW
                     (too short)             (sustained)
```

---

## Artifact Detection Logic

### Step 1: Trigger Analysis (2000 deg/s threshold)

```
IF angular_velocity > 2000 deg/s:
    → Trigger burst classification
ELSE:
    → Normal movement, no analysis needed
```

**In this example**:
- ✅ Frames 100-101: 2847 deg/s → Triggers analysis
- ✅ Frames 500-515: 1423 deg/s → Below trigger (no analysis, accepted as-is)

### Step 2: Duration Classification

```
Event detected at frames 100-101:
  Duration: 2 frames = 16.7 ms
  
  IF duration ≤ 3 frames (≤25 ms):
      → Tier 1: ARTIFACT
      → ACTION: EXCLUDE from statistics
  ELIF duration ≤ 7 frames (≤58 ms):
      → Tier 2: BURST
      → ACTION: PRESERVE but flag for review
  ELSE:
      → Tier 3: FLOW
      → ACTION: PRESERVE and accept
```

**Result**: Frames 100-101 classified as **Tier 1 ARTIFACT** → **EXCLUDED**

---

## Statistics Calculation

### WITHOUT Neutralization (❌ Old System)

```python
# Uses ALL frames
all_velocities = [
    frames_1_99:    [100, 150, ..., 800],    # Normal
    frames_100_101: [2847, 2847],            # Sensor glitch ← PROBLEM!
    frames_102_499: [120, 200, ..., 750],    # Normal
    frames_500_515: [1400, 1450, ..., 1500], # Real Gaga
    frames_516_end: [100, 180, ..., 650]     # Normal
]

Raw Max Velocity = 2847 deg/s  ← Includes glitch

IF max_velocity > 1500:
    score -= 20  # Penalty applied
    
Result: Biomechanics Score = 17.7% ❌
Assessment: "MODERATE_EXCESS" (falsely flagged)
```

### WITH Neutralization (✅ New System)

```python
# Step 1: Detect artifacts
artifacts = detect_artifacts(velocities, threshold=2000, max_frames=3)
# Result: artifacts = [100, 101]

# Step 2: Exclude artifacts (set to NaN)
clean_velocities = [
    frames_1_99:    [100, 150, ..., 800],    # Normal
    frames_100_101: [NaN, NaN],              # EXCLUDED ✓
    frames_102_499: [120, 200, ..., 750],    # Normal
    frames_500_515: [1400, 1450, ..., 1500], # Real Gaga
    frames_516_end: [100, 180, ..., 650]     # Normal
]

Clean Max Velocity = 1500 deg/s  ← Glitch excluded, real max preserved

IF max_velocity > 1500:
    score -= 20  # No penalty (1500 at threshold)
    
Result: Biomechanics Score = 87.3% ✅
Assessment: "PLAUSIBLE" or "ACCEPT_HIGH_INTENSITY"
```

---

## The Thresholds Explained

### Why 2000 deg/s?

| Joint | Max Velocity (Literature) | Source |
|-------|---------------------------|--------|
| Shoulder (elite athletes) | 1200-1500 deg/s | Wu et al., 2005 |
| Elbow (fast movement) | 800-1200 deg/s | Winter, 2009 |
| Wrist (rapid gesture) | 1000-1400 deg/s | Cereatti et al., 2024 |

**Safety Margin**: 2000 deg/s is 33% above maximum documented velocity, catching artifacts while preserving extreme (but real) Gaga movements.

### Why ≤3 frames (≤25ms)?

**Human biomechanical constraints**:
1. **Muscle activation time**: ~30-50ms minimum
2. **Force development**: ~50-100ms to reach peak
3. **Neural transmission**: ~10-20ms delay

**Physically impossible** for human to:
- Accelerate joint to >2000 deg/s
- Maintain for <25ms
- Immediately decelerate

**Typical sensor artifacts**:
- Marker occlusion: 1-2 frames (marker blocked, interpolation fails)
- Marker swap: 1-3 frames (system confuses two markers briefly)
- Reflective surface: 1-2 frames (false reflection detected)

**Real rapid movements**:
- Arm whip: 50-200ms (6-24 frames)
- Hand shake: 80-150ms (10-18 frames)
- Head turn: 100-300ms (12-36 frames)

---

## Visual Comparison

### Raw vs Clean Data

```
Raw Max Velocity (includes glitch):
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│    ▲                                                        │
│ 3000│                                                       │
│    │                                                        │
│ 2500│         ██  ← Sensor glitch (2 frames)               │
│    │         ██                                             │
│ 2000│─────────██─────────────────────────────────────────  │ Trigger
│    │         ██                                             │
│ 1500│         ██                      ████████              │ ← Real Gaga
│    │  ░░░░░░░██░░░░░░░░░░░░░░░░░░░░░████████░░░░░░░       │
│ 1000│  ░░░░░░░██░░░░░░░░░░░░░░░░░░░░████████░░░░░░░       │
│    │  ░░░░░░░██░░░░░░░░░░░░░░░░░░████████░░░░░░░░░       │
│  500│░░░░░░░░██░░░░░░░░░░░░░░░░████████░░░░░░░░░░░       │
│    │░░░░░░░░██░░░░░░░░░░░░░░████████░░░░░░░░░░░░░       │
│    0└─────────────────────────────────────────────────────  │
│      0    100    200    300    400    500    600    700     │
│                    Frame Number                              │
└─────────────────────────────────────────────────────────────┘
         Max = 2847 deg/s  ❌ Penalized


Clean Max Velocity (glitch excluded):
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│    ▲                                                        │
│ 3000│                                                       │
│    │                                                        │
│ 2500│         XX  ← EXCLUDED                                │
│    │         XX                                             │
│ 2000│─────────XX─────────────────────────────────────────  │
│    │         XX                                             │
│ 1500│         XX                      ████████              │ ← Real max
│    │  ░░░░░░░XX░░░░░░░░░░░░░░░░░░░░░████████░░░░░░░       │
│ 1000│  ░░░░░░░XX░░░░░░░░░░░░░░░░░░░░████████░░░░░░░       │
│    │  ░░░░░░░XX░░░░░░░░░░░░░░░░░░████████░░░░░░░░░       │
│  500│░░░░░░░░XX░░░░░░░░░░░░░░░░████████░░░░░░░░░░░       │
│    │░░░░░░░░XX░░░░░░░░░░░░░░████████░░░░░░░░░░░░░       │
│    0└─────────────────────────────────────────────────────  │
│      0    100    200    300    400    500    600    700     │
│                    Frame Number                              │
└─────────────────────────────────────────────────────────────┘
         Max = 1500 deg/s  ✅ Not penalized
```

---

## How to Read Your Audit Log

### Column: `Biomech_Velocity_Source`

| Value | Meaning |
|-------|---------|
| `clean` | ✅ Neutralization applied, artifacts excluded |
| `raw` | ⚠️ No artifacts detected, or analysis not run |

### Column: `Clean_Max_Vel_deg_s`

**If this is LESS than `Max_Ang_Vel_deg_s`**:
- ✅ Artifacts were found and excluded
- The difference shows how much the glitches inflated the raw max

**Example**:
```
Max_Ang_Vel_deg_s:      2847.3 deg/s  (raw)
Clean_Max_Vel_deg_s:    1423.1 deg/s  (cleaned)
Max_Vel_Reduction_%:    50.1%
→ Interpretation: Half the "maximum" was a sensor glitch!
```

### Column: `Data_Retained_%`

**Percentage of frames kept after artifact exclusion**:
- 99.9%+ → Excellent, minimal artifacts
- 98-99% → Good, few artifacts removed
- <98% → Review needed, many frames excluded

**Example**:
```
Total_Frames:          3600
Excluded_Frames:       2
Data_Retained_%:       99.94%
→ Interpretation: Only 2 frames (0.06%) were artifacts
```

---

## Quick Validation

After re-running notebooks, check your audit:

```python
import pandas as pd
df = pd.read_excel("reports/master_audit_*.xlsx")

# Check if neutralization is working
neutralized = df['Biomech_Velocity_Source'] == 'clean'
print(f"Runs with clean data: {neutralized.sum()} / {len(df)}")

# Check artifact impact
artifact_runs = df[df['Clean_Max_Vel_deg_s'] < df['Max_Ang_Vel_deg_s']]
if len(artifact_runs) > 0:
    avg_reduction = (
        artifact_runs['Max_Ang_Vel_deg_s'] - artifact_runs['Clean_Max_Vel_deg_s']
    ).mean()
    print(f"Average artifact inflation: {avg_reduction:.1f} deg/s")
```

---

## Summary

**Clean Max Velocity** = Real maximum velocity with sensor glitches removed

**Artifact Threshold**:
- **Velocity**: >2000 deg/s (triggers analysis)
- **Duration**: ≤3 frames (≤25ms at 120Hz)
- **Action**: EXCLUDE from statistics

**Result**: Biomechanics scoring now reflects **actual movement quality**, not sensor noise.

---

For full technical details, see:
- [BIOMECHANICS_SCORING_TRANSPARENCY.md](../docs/quality_control/BIOMECHANICS_SCORING_TRANSPARENCY.md)
- [BIOMECHANICS_SCORECARD_QUICK_REF.md](../BIOMECHANICS_SCORECARD_QUICK_REF.md)
