# Biomechanics Scoring - Critical Thresholds Cheat Sheet

**Quick reference for artifact detection and scoring logic**

---

## Artifact Detection Thresholds

### Primary Thresholds (Always Applied)

| Threshold | Value | Unit | Purpose |
|-----------|-------|------|---------|
| **Velocity Trigger** | **2000** | deg/s | Triggers burst analysis |
| **Artifact Max Duration** | **3** | frames | ≤3 frames = ARTIFACT (excluded) |
| **Burst Max Duration** | **7** | frames | 4-7 frames = BURST (review) |
| **Flow Min Duration** | **8** | frames | ≥8 frames = FLOW (accept) |

### Time Equivalents at 120 Hz

| Frames | Milliseconds | Classification |
|--------|--------------|----------------|
| 1 | 8.3 ms | ARTIFACT |
| 2 | 16.7 ms | ARTIFACT |
| 3 | 25 ms | ARTIFACT (max) |
| 4 | 33 ms | BURST (min) |
| 5 | 42 ms | BURST |
| 6 | 50 ms | BURST |
| 7 | 58 ms | BURST (max) |
| 8 | 67 ms | FLOW (min) |
| 15 | 125 ms | FLOW (typical Gaga) |
| 24 | 200 ms | FLOW (sustained) |

---

## Biomechanics Scoring Thresholds

### Physiological Plausibility (40% weight)

| Metric | Threshold | Penalty | Assessment |
|--------|-----------|---------|------------|
| **Velocity (clean)** | ≤1500 deg/s | 0 | PLAUSIBLE |
| | 1501-2250 deg/s | -20 | MODERATE_EXCESS |
| | >2250 deg/s | -40 | SEVERE_EXCESS |
| **Angular Accel** | ≤30000 deg/s² | 0 | ACCEPTABLE |
| | 30001-50000 deg/s² | -15 | HIGH |
| | >50000 deg/s² | -30 | EXTREME |
| **Linear Accel** | ≤50 m/s² | 0 | SAFE (~5g) |
| | 51-100 m/s² | -10 | ELEVATED (~10g) |
| | >100 m/s² | -20 | SEVERE (>10g) |

### Skeleton Stability (30% weight)

| Bone CV | Penalty | Assessment |
|---------|---------|------------|
| ≤0.5% | 0 | EXCELLENT |
| 0.51-1.0% | -10 | GOOD |
| 1.01-2.0% | -30 | MARGINAL |
| >2.0% | -50 | POOR |

### Movement Continuity (30% weight)

| Factor | Threshold | Penalty | Assessment |
|--------|-----------|---------|------------|
| **Burst Decision** | PASS | 0 | NORMAL |
| | ACCEPT_HIGH_INTENSITY | 0 | HIGH_INTENSITY_LEGITIMATE |
| | REVIEW | -15 | REQUIRES_VISUAL_AUDIT |
| | REJECT | -50 | DATA_QUALITY_ISSUE |
| **Artifact Rate** | ≤0.5% | 0 | MINIMAL |
| | 0.51-1.0% | -10 | ELEVATED |
| | >1.0% | -25 | EXCESSIVE |
| **Data Retained** | ≥99% | 0 | EXCELLENT |
| | 95-98.9% | -10 | FAIR |
| | <95% | -25 | POOR |

---

## Literature Support

### Velocity Thresholds

| Joint | Max Velocity | Study |
|-------|--------------|-------|
| Shoulder (elite) | 1200-1500 deg/s | Wu et al., 2005 |
| Elbow (fast) | 800-1200 deg/s | Winter, 2009 |
| Wrist (rapid) | 1000-1400 deg/s | Cereatti et al., 2024 |

**Trigger at 2000 deg/s** = 33% safety margin above documented maximum

### Duration Rationale

| Duration | Physiology |
|----------|------------|
| <25ms | Impossible: Muscle activation requires 30-50ms minimum |
| 33-58ms | Possible: Rapid twitch but requires visual verification |
| >65ms | Plausible: Sustained force development possible |

---

## Quick Decision Matrix

### Is this an artifact?

```
IF velocity > 2000 deg/s:
    IF duration ≤ 3 frames (≤25ms):
        → ARTIFACT: Exclude from scoring
    ELIF duration ≤ 7 frames (≤58ms):
        → BURST: Preserve but flag for review
    ELSE:
        → FLOW: Preserve and accept as valid
ELSE:
    → NORMAL: No action needed
```

### How is it scored?

```
Biomechanics Score = 
    Physiological (40%) +
    Skeleton (30%) +
    Continuity (30%)

Where:
    Physiological uses CLEAN max velocity
    Skeleton uses bone CV from preprocessing
    Continuity uses artifact rate and burst decision
```

---

## Common Scenarios

### Scenario 1: Clean Gaga Recording
```
Raw Max Velocity:      1423 deg/s
Clean Max Velocity:    1423 deg/s (no artifacts)
Velocity Source:       clean
Velocity Assessment:   PLAUSIBLE
Bone CV:               0.34%
Artifact Rate:         0.02%
Burst Decision:        PASS

Physiological Score:   100 (no penalty)
Skeleton Score:        100 (excellent)
Continuity Score:      100 (minimal artifacts)
→ Biomechanics Score:  100.0 ✅
```

### Scenario 2: High-Intensity with Artifacts
```
Raw Max Velocity:      2847 deg/s (2-frame glitch)
Clean Max Velocity:    1423 deg/s (glitch removed)
Velocity Source:       clean
Velocity Assessment:   PLAUSIBLE
Bone CV:               0.41%
Artifact Rate:         0.12%
Burst Decision:        ACCEPT_HIGH_INTENSITY

Physiological Score:   100 (clean velocity OK)
Skeleton Score:        100 (excellent)
Continuity Score:      100 (legitimate high intensity)
→ Biomechanics Score:  100.0 ✅
```

### Scenario 3: Poor Calibration
```
Raw Max Velocity:      1234 deg/s
Clean Max Velocity:    1234 deg/s
Velocity Source:       clean
Velocity Assessment:   PLAUSIBLE
Bone CV:               2.34% ← PROBLEM
Artifact Rate:         0.08%
Burst Decision:        PASS

Physiological Score:   100 (velocity OK)
Skeleton Score:        50 (poor CV, -50 penalty)
Continuity Score:      100 (minimal artifacts)
→ Biomechanics Score:  85.0 (100×0.4 + 50×0.3 + 100×0.3)
```

### Scenario 4: Excessive Artifacts
```
Raw Max Velocity:      3124 deg/s
Clean Max Velocity:    0 deg/s (all high velocity excluded)
Velocity Source:       raw (no valid clean data)
Velocity Assessment:   SEVERE_EXCESS
Bone CV:               1.87%
Artifact Rate:         1.87% ← PROBLEM
Burst Decision:        REJECT

Physiological Score:   60 (-40 penalty)
Skeleton Score:        70 (-30 penalty)
Continuity Score:      25 (-50 REJECT, -25 high artifact rate)
→ Biomechanics Score:  48.5 ❌
```

---

## Validation Checklist

After re-running notebooks, verify:

- [ ] `Biomech_Velocity_Source` = "clean" for runs with artifacts
- [ ] `Clean_Max_Vel_deg_s` < `Max_Ang_Vel_deg_s` when artifacts present
- [ ] `Artifact_Rate_%` matches expected artifact density
- [ ] `Biomech_Burst_Assessment` = "HIGH_INTENSITY_LEGITIMATE" for Gaga
- [ ] Component scores sum correctly: `(Phys×0.4 + Skel×0.3 + Cont×0.3)`

---

**Last Updated**: 2026-01-23  
**Implementation**: src/utils_nb07.py, src/burst_classification.py
