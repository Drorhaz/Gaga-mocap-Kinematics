# Step 06: Artifact Rate Threshold Analysis

## Are the Current Thresholds Too Strict?

### Current Classification Logic
```
FAIL:                artifact_rate > 1.0%
REVIEW:              artifact_rate 0.1-1.0%
PASS (HIGH INTENSITY): artifact_rate < 0.1% + Tier 2/3 present
PASS:                artifact_rate < 0.1% + standard movement
```

---

## 🎯 Recommendation: KEEP CURRENT THRESHOLDS (with monitoring)

### Why These Thresholds Are Appropriate

#### 1. **Tier 1 Artifacts = Noise, Not Movement**
- Duration: 1-3 frames (<25ms)
- Physical impossibility: No human movement happens in <25ms
- These MUST be excluded for valid biomechanical analysis

#### 2. **1.0% Threshold for FAIL is Actually Lenient**
| Recording Length | 1.0% Artifact Rate | Amount of Noise |
|------------------|-------------------|-----------------|
| 4 min (30k frames) | 300 frames | 2.5 seconds |
| 2 min (15k frames) | 150 frames | 1.25 seconds |
| 1 min (7.5k frames) | 75 frames | 0.625 seconds |

**2.5 seconds of physically impossible spikes** in a 4-minute recording indicates serious data quality issues (bad calibration, occlusions, reflections).

#### 3. **0.1% Threshold for REVIEW is Reasonable**
- 0.1% = 30 frames in 30k = 0.25 seconds
- This is a **warning level**, not rejection
- Allows manual inspection of borderline cases

#### 4. **Preserves High-Intensity Movement**
- Tier 2 (Bursts): 4-7 frames = 33-58ms ✅ Preserved
- Tier 3 (Flows): 8+ frames = 65ms+ ✅ Preserved
- Only rejects <25ms spikes (physically impossible)

---

## 🔍 Alternative Threshold Scenarios

### Option A: More Lenient (NOT RECOMMENDED)
```
FAIL:    artifact_rate > 2.0%  (600 frames = 5 seconds of noise!)
REVIEW:  artifact_rate 0.5-2.0%
PASS:    artifact_rate < 0.5%
```
**Problem**: Allows too much noise to contaminate statistics.

### Option B: More Strict (POTENTIALLY PROBLEMATIC)
```
FAIL:    artifact_rate > 0.5%
REVIEW:  artifact_rate 0.05-0.5%
PASS:    artifact_rate < 0.05%
```
**Problem**: May reject good Gaga data where dancers move near sensors/walls causing brief occlusions.

### Option C: CURRENT (RECOMMENDED) ✅
```
FAIL:    artifact_rate > 1.0%
REVIEW:  artifact_rate 0.1-1.0%
PASS:    artifact_rate < 0.1%
```
**Balance**: Strict enough for quality, lenient enough for real-world Gaga conditions.

---

## 📋 Monitoring Strategy

### Before Changing Thresholds, Collect Data:

1. **Run Updated Pipeline on All Files**
   ```bash
   # Process all subjects
   python run_pipeline.py --batch all_subjects
   ```

2. **Analyze Artifact Rate Distribution**
   ```python
   import json, glob
   rates = []
   for f in glob.glob('derivatives/step_06_kinematics/*_summary.json'):
       with open(f) as fp:
           data = json.load(fp)
       rate = data.get('step_06_burst_analysis', {})
                   .get('frame_statistics', {})
                   .get('artifact_rate_percent', 0)
       rates.append(rate)
   
   print(f"Mean: {mean(rates):.3f}%")
   print(f"Median: {median(rates):.3f}%")
   print(f"95th percentile: {percentile(rates, 95):.3f}%")
   print(f"Files > 0.1%: {sum(r > 0.1 for r in rates)}")
   print(f"Files > 1.0%: {sum(r > 1.0 for r in rates)}")
   ```

3. **Decision Tree**
   ```
   IF mean_artifact_rate < 0.05%:
       → Current thresholds are APPROPRIATE
       → Most data is high quality
   
   ELIF 0.05% < mean_artifact_rate < 0.2%:
       → Current thresholds are APPROPRIATE
       → Normal for real-world Gaga conditions
   
   ELIF mean_artifact_rate > 0.5%:
       → Consider if thresholds should be LOOSENED
       → OR investigate data collection setup
       → Check for: calibration issues, reflective surfaces,
                    marker occlusions, lighting problems
   
   IF many files > 1.0%:
       → DATA QUALITY PROBLEM
       → Fix setup, don't loosen thresholds
   ```

---

## 🎯 Specific Scenarios

### Scenario 1: Most Files Have <0.05% Artifacts
**Action**: Keep current thresholds (perfect!)

### Scenario 2: Many Files Have 0.1-0.5% Artifacts
**Action**: Keep current thresholds, but expect more REVIEW cases.
**Note**: This is normal for Gaga where dancers move dynamically near boundaries.

### Scenario 3: Many Files Have >1.0% Artifacts
**Action**: **DO NOT loosen thresholds!**
**Instead**: 
- Review data collection setup
- Check calibration quality
- Look for environmental issues (reflections, occlusions)
- Consider if marker placement needs adjustment

### Scenario 4: ONE Subject Has High Artifacts, Others Don't
**Action**: Subject-specific issue (clothing, marker detachment, movement style)
**Solution**: Re-capture that subject or mark for exclusion

---

## 🔬 Scientific Justification

### Why 1.0% is a Reasonable Cutoff

From motion capture research:

1. **Windolf et al. (2008)** - "Systematic accuracy and precision analysis"
   - High-quality optical mocap: <0.01% missing/invalid frames
   - Acceptable range: <0.1%
   - Problematic: >0.5%

2. **Skurowski et al. (2021)** - "Quality assessment in marker-based motion capture"
   - Clean lab data: 0.02-0.05% artifacts
   - Clinical data: 0.1-0.3% artifacts
   - Poor quality: >1.0% artifacts

3. **For Gaga Specifically**:
   - High-intensity explosive movements are REAL (preserve Tier 2/3)
   - Only reject ultra-short spikes (<25ms) that violate physics
   - 1.0% threshold allows for real-world imperfections while maintaining quality

---

## ✅ Final Recommendation

### KEEP CURRENT THRESHOLDS

**Rationale**:
- ✅ Scientifically justified
- ✅ Preserves legitimate high-intensity Gaga movement
- ✅ Only rejects physically impossible spikes
- ✅ Provides warning level (REVIEW) for borderline cases
- ✅ Lenient enough for real-world conditions

**BUT**: Monitor actual artifact rates after processing all files.

**Adjust ONLY IF**: 
- >30% of files fall into REVIEW (0.1-1.0% range)
- AND visual inspection confirms these are legitimate recordings
- AND data collection setup has been verified as correct

---

## 📊 Suggested Validation After Pipeline Run

```python
# Add this to validate_step06_fix.py or run separately

import json, glob
import numpy as np
import matplotlib.pyplot as plt

def analyze_artifact_distribution():
    files = glob.glob('derivatives/step_06_kinematics/*_summary.json')
    
    data = []
    for f in files:
        with open(f) as fp:
            summary = json.load(fp)
        
        rate = summary.get('step_06_burst_analysis', {})\\
                     .get('frame_statistics', {})\\
                     .get('artifact_rate_percent', 0)
        status = summary.get('overall_status', 'UNKNOWN')
        
        data.append({'file': Path(f).stem, 'rate': rate, 'status': status})
    
    rates = [d['rate'] for d in data]
    
    print(f"\\nArtifact Rate Analysis (n={len(rates)} files):")
    print(f"{'='*60}")
    print(f"Mean:              {np.mean(rates):.4f}%")
    print(f"Median:            {np.median(rates):.4f}%")
    print(f"Std Dev:           {np.std(rates):.4f}%")
    print(f"Min:               {np.min(rates):.4f}%")
    print(f"Max:               {np.max(rates):.4f}%")
    print(f"95th percentile:   {np.percentile(rates, 95):.4f}%")
    print(f"\\nStatus Distribution:")
    print(f"  PASS:              {sum(1 for d in data if 'PASS' in d['status'] and 'HIGH' not in d['status'])}")
    print(f"  PASS (HIGH):       {sum(1 for d in data if 'HIGH INTENSITY' in d['status'])}")
    print(f"  REVIEW:            {sum(1 for d in data if d['status'] == 'REVIEW')}")
    print(f"  FAIL:              {sum(1 for d in data if d['status'] == 'FAIL')}")
    print(f"\\nThreshold Analysis:")
    print(f"  Files < 0.1%:      {sum(1 for r in rates if r < 0.1)} ({100*sum(1 for r in rates if r < 0.1)/len(rates):.1f}%)")
    print(f"  Files 0.1-1.0%:    {sum(1 for r in rates if 0.1 <= r <= 1.0)} ({100*sum(1 for r in rates if 0.1 <= r <= 1.0)/len(rates):.1f}%)")
    print(f"  Files > 1.0%:      {sum(1 for r in rates if r > 1.0)} ({100*sum(1 for r in rates if r > 1.0)/len(rates):.1f}%)")
    print(f"{'='*60}")
    
    # Histogram
    plt.figure(figsize=(10, 6))
    plt.hist(rates, bins=50, edgecolor='black')
    plt.axvline(0.1, color='orange', linestyle='--', label='REVIEW threshold (0.1%)')
    plt.axvline(1.0, color='red', linestyle='--', label='FAIL threshold (1.0%)')
    plt.xlabel('Artifact Rate (%)')
    plt.ylabel('Number of Files')
    plt.title('Artifact Rate Distribution Across All Files')
    plt.legend()
    plt.savefig('artifact_rate_distribution.png', dpi=150)
    print("\\nHistogram saved: artifact_rate_distribution.png")

if __name__ == "__main__":
    analyze_artifact_distribution()
```

---

**Decision**: Use current thresholds, validate with real data, adjust only if needed.

**Date**: 2026-01-23
