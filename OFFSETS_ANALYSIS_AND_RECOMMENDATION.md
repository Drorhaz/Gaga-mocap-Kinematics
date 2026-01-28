# BVH Offsets: Current State, Problems, and Recommendations

## Current State ❌

### How It Works Now:

1. **ONE shared schema file**: `config/skeleton_schema.json`
2. **Tied to ONE specific BVH file**: `"763_T2_P2_R2_Take_2025-12-25 10.51.23 AM_005_763.bvh"`
3. **Used for ALL sessions**: Every session uses the same offsets

### The Problem:

```
Session 1 (Subject 763): Uses offsets from Subject 763's BVH ✅
Session 2 (Subject 764): Uses offsets from Subject 763's BVH ❌ WRONG!
Session 3 (Subject 765): Uses offsets from Subject 763's BVH ❌ WRONG!
```

**Result**: 
- QC comparison is **only accurate for the one subject** whose BVH was used
- Other subjects will show incorrect ratios (e.g., ratio = 0.95 or 1.05) even if their data is perfect
- This creates **false warnings/alerts** for other subjects

---

## Is It Taking Offsets Per File? ❌ NO

**Answer: NO** - It's using a **shared schema file** for all sessions.

**Current Flow:**
```
1. Load config/skeleton_schema.json (ONE file, shared)
   └─> Contains offsets from ONE specific BVH file

2. Process Session 1
   └─> Uses shared schema offsets

3. Process Session 2 (different subject)
   └─> Uses SAME shared schema offsets ❌ WRONG!
```

---

## Optimal Methods (3 Options)

### Option 1: Per-Session Offsets ✅ RECOMMENDED (if BVH available)

**How it works:**
- Extract offsets from each session's BVH file
- Store per-session: `derivatives/step_01_parse/{RUN_ID}__schema.json`
- Use session-specific offsets for QC

**Pros:**
- ✅ Accurate comparison for each subject
- ✅ Detects scaling issues (meters vs cm)
- ✅ Detects tracking errors vs expected bone lengths

**Cons:**
- ❌ Requires BVH file per session
- ❌ More complex (need BVH parser)
- ❌ Extra storage per session

**Implementation:**
```python
# Per-session schema extraction
def extract_schema_from_bvh(bvh_path, run_id):
    # Parse BVH file
    offsets = parse_bvh_offsets(bvh_path)
    
    # Save per-session
    schema_path = f"derivatives/step_01_parse/{run_id}__schema.json"
    save_schema(schema_path, offsets)
    
    return schema_path

# In pipeline
schema_path = extract_schema_from_bvh(session_bvh_path, run_id)
schema = load_schema(schema_path)  # Per-session!
```

---

### Option 2: Skip BVH Comparison, Use Consistency Only ✅ SIMPLER (Recommended)

**How it works:**
- **Don't compare to BVH offsets**
- **Only check consistency** (CV% - coefficient of variation)
- This is what `notebooks/02_preprocess.ipynb` already does!

**Pros:**
- ✅ Works for all subjects (no per-session extraction needed)
- ✅ Simpler implementation
- ✅ Detects tracking errors (bone length variation)
- ✅ Already implemented in notebook 02

**Cons:**
- ❌ Can't detect scaling issues (meters vs cm) - but you can check manually
- ❌ Can't compare to "expected" bone lengths

**Current Implementation (Notebook 02):**
```python
# Already does this - just checks consistency!
lengths = np.linalg.norm(child_pos - parent_pos, axis=1)
mean_l = np.nanmean(lengths)
std_l = np.nanstd(lengths)
cv = std_l / mean_l  # Coefficient of variation

# If CV > 5%, bone length is inconsistent = tracking error
```

---

### Option 3: Make BVH Comparison Optional ⚠️ COMPROMISE

**How it works:**
- If BVH file exists for session → use per-session offsets
- If no BVH file → skip comparison, only check consistency

**Pros:**
- ✅ Flexible (works with or without BVH)
- ✅ Accurate when BVH available

**Cons:**
- ❌ More complex logic
- ❌ Inconsistent QC across sessions

---

## Is It Even Necessary? 🤔

### My Recommendation: **Probably NOT necessary**

**Reasons:**

1. **Consistency check is sufficient**: 
   - If bone lengths are consistent (low CV%), tracking is good
   - If bone lengths vary (high CV%), tracking has errors
   - **You don't need to compare to "expected" values**

2. **Scaling detection is rare**:
   - Meters vs cm issues are usually obvious and caught early
   - Not worth the complexity of per-session BVH extraction

3. **Notebook 02 already works**:
   - Your existing QC in `02_preprocess.ipynb` only checks consistency
   - It works perfectly for all subjects
   - No need for BVH comparison

4. **Multi-subject problem**:
   - Using shared offsets causes false warnings for other subjects
   - Better to skip the comparison entirely

---

## Recommendation Summary

### ✅ **RECOMMENDED: Option 2 - Skip BVH Comparison**

**Action:**
1. **Remove or make optional** the BVH offset comparison in `src/qc.py`
2. **Keep only consistency check** (CV% - what notebook 02 does)
3. **Remove offsets from schema** (or mark as optional/informational only)

**Why:**
- Simpler
- Works for all subjects
- Already implemented correctly in notebook 02
- Avoids false warnings for different subjects

### Alternative: Option 1 (if you have BVH files)

If you **always have BVH files per session** and want scaling detection:
- Extract offsets per-session from BVH
- Use per-session schema for QC
- More complex but more complete

---

## Current Code Issue

**Problem in `src/qc.py`:**
```python
# Line 39-41: Compares to shared schema offsets
off = offsets.get(c_name, [np.nan, np.nan, np.nan])
L_bvh = float(np.linalg.norm(off))  # From ONE subject's BVH
ratio = float(median_L / L_bvh)     # Wrong for other subjects!
```

**This will show incorrect ratios for subjects other than the one whose BVH was used.**

---

## Conclusion

**Current state**: ❌ Using shared offsets (wrong for multi-subject)

**Optimal method**: ✅ **Skip BVH comparison, use consistency only** (Option 2)

**Is it necessary?**: ❌ **No** - consistency check is sufficient

**Action**: Remove or make optional the BVH offset comparison in QC
