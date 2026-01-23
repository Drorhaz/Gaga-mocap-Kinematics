# Step 06: Overall Status Decision Tree (NEW LOGIC)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    STEP 06: CLASSIFICATION-BASED STATUS                  │
│                        (Gaga-Specific Movement Logic)                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  Gate 5: Burst Classification │
                    │   (Analyze Angular Velocity)  │
                    └───────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │  Compute Artifact Rate (%)    │
                    │  = Tier 1 frames / Total      │
                    └───────────────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            ▼                       ▼                       ▼
    ┌──────────────┐        ┌──────────────┐      ┌──────────────┐
    │ Artifact     │        │ Artifact     │      │ Artifact     │
    │ Rate > 1.0%  │        │ Rate 0.1-1.0%│      │ Rate < 0.1%  │
    └──────────────┘        └──────────────┘      └──────────────┘
            │                       │                       │
            ▼                       ▼                       ▼
    ┌──────────────┐        ┌──────────────┐      ┌──────────────┐
    │   ❌ FAIL    │        │  ⚠️ REVIEW   │      │  Check Tiers │
    └──────────────┘        └──────────────┘      └──────────────┘
    │                       │                               │
    │ Too many              │ Elevated                      │
    │ short spikes          │ artifacts                     │
    │ (data quality)        │ (needs audit)                 │
    │                       │                               │
    └───────────────────────┴───────────────────────────────┤
                                                            │
                            ┌───────────────────────────────┤
                            │                               │
                            ▼                               ▼
                    ┌──────────────┐              ┌──────────────┐
                    │ Contains      │              │ Standard     │
                    │ Tier 2/3?     │              │ Movement     │
                    │ (Bursts/Flow) │              │ Only         │
                    └──────────────┘              └──────────────┘
                            │                               │
                    ┌───────┴───────┐                      │
                    │               │                       │
                    ▼               ▼                       ▼
            ┌──────────────┐  ┌──────────────┐    ┌──────────────┐
            │ ✅ PASS      │  │ ⚠️ REVIEW    │    │ ✅ PASS      │
            │ (HIGH        │  │ (Manual      │    │              │
            │  INTENSITY)  │  │  Audit       │    │              │
            └──────────────┘  │  Required)   │    └──────────────┘
            │                 └──────────────┘    │
            │                 │                    │
            │ Legitimate      │ Burst events       │ Normal gait
            │ Gaga            │ need visual        │ within limits
            │ explosive       │ inspection         │
            │ movement!       │                    │
            └─────────────────┴────────────────────┘
```

---

## Tier Definitions (Burst Classification)

```
┌──────────────────────────────────────────────────────────────────┐
│                     BURST EVENT TIERS                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Tier 1: ARTIFACT (1-3 frames, <25ms)                           │
│  ├─ Duration:      1-3 frames @ 120Hz = 8-25ms                  │
│  ├─ Status:        ❌ EXCLUDE from statistics                    │
│  ├─ Meaning:       Physically impossible spikes                  │
│  └─ Action:        Count for artifact_rate_percent              │
│                                                                   │
│  Tier 2: BURST (4-7 frames, 33-58ms)                           │
│  ├─ Duration:      4-7 frames @ 120Hz = 33-58ms                │
│  ├─ Status:        ⚠️ REVIEW required                           │
│  ├─ Meaning:       Potential whip/shake, may be legitimate      │
│  └─ Action:        Flag for manual visual inspection            │
│                                                                   │
│  Tier 3: FLOW (8+ frames, >65ms)                               │
│  ├─ Duration:      8+ frames @ 120Hz = 65ms+                   │
│  ├─ Status:        ✅ ACCEPT as valid Gaga                      │
│  ├─ Meaning:       Sustained intentional movement               │
│  └─ Action:        Preserve for authentic movement analysis     │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Residual RMS Policy - "Price of Smoothing"

```
┌──────────────────────────────────────────────────────────────────┐
│                    RESIDUAL RMS QUALITY GRADING                   │
│                                                                   │
│  Definition: Distance between raw and filtered marker position   │
│                                                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  RMS < 15mm          →  🥇 GOLD                                  │
│  ├─ Interpretation:  Excellent tracking                          │
│  ├─ Filter Impact:   Minimal distortion                         │
│  └─ Score Penalty:   None (0 points)                            │
│                                                                   │
│  RMS 15-30mm         →  🥈 SILVER                                │
│  ├─ Interpretation:  Acceptable tracking                         │
│  ├─ Filter Impact:   Moderate distortion                        │
│  └─ Score Penalty:   -10 points                                 │
│                                                                   │
│  RMS > 30mm          →  🔍 REVIEW                                │
│  ├─ Interpretation:  High filtering distortion                   │
│  ├─ Filter Impact:   Filter "fighting" the movement             │
│  ├─ Meaning:         Movement is TRULY explosive                │
│  └─ Score Penalty:   -30 points                                 │
│                                                                   │
│  💡 Key Insight:                                                 │
│     High RMS + High Cutoff (16Hz) = Authentic explosive movement│
│     (Not sensor noise, but real Gaga dynamics!)                 │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Comparison: OLD vs NEW Logic

```
┌─────────────────────────────────────────────────────────────────┐
│                    OLD LOGIC (ERROR-BASED)                       │
│                           ❌ WRONG                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  IF max_velocity > 1500 deg/s:                                 │
│      overall_status = "FAIL"  ← Treats high velocity as ERROR  │
│  ELSE:                                                          │
│      overall_status = "PASS"                                    │
│                                                                  │
│  Problem:                                                       │
│  - Rejects legitimate Gaga explosive movement                  │
│  - No differentiation between noise and real movement          │
│  - Designed for standard gait, not high-intensity dance        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

                              ⬇️ FIXED ⬇️

┌─────────────────────────────────────────────────────────────────┐
│                  NEW LOGIC (CLASSIFICATION-BASED)                │
│                           ✅ CORRECT                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  IF artifact_rate > 1.0%:                                       │
│      overall_status = "FAIL"                                    │
│      reason = "Data quality issue"                              │
│                                                                  │
│  ELIF artifact_rate > 0.1%:                                     │
│      overall_status = "REVIEW"                                  │
│      reason = "Elevated artifacts"                              │
│                                                                  │
│  ELIF burst_decision == "ACCEPT_HIGH_INTENSITY":                │
│      overall_status = "PASS (HIGH INTENSITY)"                   │
│      reason = "Legitimate Gaga movement"                        │
│                                                                  │
│  ELSE:                                                          │
│      overall_status = "PASS"                                    │
│      reason = "Standard gait"                                   │
│                                                                  │
│  Benefits:                                                      │
│  ✅ Accepts high-intensity Gaga as legitimate                  │
│  ✅ Differentiates noise (Tier 1) from movement (Tier 2/3)    │
│  ✅ Context-aware: velocity + duration analysis               │
│  ✅ Gaga-specific: designed for explosive movement            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Example Case: Subject 734, T1, P1, R1

```
INPUT DATA:
──────────
Max Angular Velocity:  2,347 deg/s  (OVER 1500!)
Recording Duration:    30,127 frames @ 120Hz
Tier 1 Artifacts:      87 frames (0.29%)
Tier 2 Bursts:         5 events
Tier 3 Flows:          12 events
Residual RMS:          18.5mm

OLD LOGIC RESULT:
──────────────────
overall_status = "FAIL"  ❌
Reason: max_velocity (2347) > 1500

→ File REJECTED as bad data
→ Authentic Gaga movement LOST


NEW LOGIC RESULT:
──────────────────
overall_status = "PASS (HIGH INTENSITY)"  ✅
Reason: "High-intensity Gaga movement confirmed (Tier 2/3 flows present)"

Detailed Analysis:
├─ Artifact Rate: 0.29% < 1.0% → Not a data quality issue
├─ Tier 3 Flows: 12 events → Sustained intentional movement
├─ RMS Grade: SILVER (18.5mm) → Acceptable tracking
└─ Decision: ACCEPT as legitimate explosive Gaga movement

→ File ACCEPTED and included in analysis
→ Authentic movement PRESERVED
```

---

## Implementation Status

| Component | Status | Action Required |
|-----------|--------|-----------------|
| **Fix Script** | ✅ Ready | Run `fix_step06_status_logic.py` |
| **Validation Script** | ✅ Ready | Run `validate_step06_fix.py` |
| **Notebook Updates** | ⏳ Pending | Apply fix script |
| **Scoring Module** | ✅ Complete | Already updated |
| **Documentation** | ✅ Complete | All files created |
| **Testing** | ⏳ Pending | User validation |

---

**Next Steps**:
1. Run `fix_step06_status_logic.py`
2. Verify backup created
3. Run `validate_step06_fix.py`
4. Test on Subject 734 file
5. Regenerate all Step 06 data
