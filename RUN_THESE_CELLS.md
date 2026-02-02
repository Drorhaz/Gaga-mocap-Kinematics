# 🎯 NOTEBOOK 06 - CELLS TO RUN

## Current Status:
- ✅ Cell 9 (Artifact flags) - ALREADY RUN (partial)
- ❌ Cell 6 (Euler conversion) - NOT RUN YET
- ❌ Cell 10 (Save parquet) - NEEDS RE-RUN

---

## Step-by-Step Instructions:

### STEP 1: Find Cell 6 (Euler Conversion)
**How to find it:** Use Ctrl+F (Find) and search for this exact text:
```
E. EULER ANGLE CONVERSION
```

**What the cell does:** Converts quaternions to Euler angles (euler_x, euler_y, euler_z)

**Action:** Click on the cell and press `Shift+Enter` to run it

**Expected Output:**
```
Converting quaternions to Euler angles (ISB Standard)...
✓ Euler angles (XYZ, degrees) added for 19 joints
```

---

### STEP 2: Find Cell 10 (Save Parquet)
**How to find it:** Search for:
```
df_master = pd.DataFrame(result)
```

**What the cell does:** Creates the DataFrame and saves it to parquet file

**Action:** Click on the cell and press `Shift+Enter` to run it

**Expected Output:**
```
✓ Saved: c:\Users\drorh\OneDrive - Mobileye\Desktop\gaga\derivatives\step_06_kinematics\734_T3_P2_R1_Take 2025-12-30 04.12.54 PM_002__kinematics_master.parquet
```

---

### STEP 3: Re-run Your Verification Cell
**The cell you just created with:**
```python
out_parquet = Path(OUT_DIR) / f"{RUN_ID}__kinematics_master.parquet"
df = pd.read_parquet(out_parquet)
```

**Expected Output AFTER running Steps 1-2:**
```
Euler columns: 57 (expected: 57) ✓
Artifact columns: 38 (expected: 38) ✓
Hampel columns: 38 (expected: 38) ✓
```

---

## Why Manual Execution is Required:

The cells exist in the notebook, but Jupyter notebooks require **manual execution** of each cell. The cells I added are just code - they won't run automatically. You need to:

1. Click on Cell 6
2. Press `Shift+Enter` 
3. Wait for output
4. Click on Cell 10
5. Press `Shift+Enter`
6. Re-run verification

---

## Quick Visual Guide:

```
[ Cell 5 ] ← Some previous cell
    ↓
[ Cell 6 ] ← THIS ONE! "E. EULER ANGLE CONVERSION" - RUN ME!
    ↓
[ Cell 7, 8, 9 ] ← Other cells
    ↓
[ Cell 10 ] ← THIS ONE! "df_master = pd.DataFrame(result)" - RUN ME AFTER CELL 6!
```

---

## ⚠️ IMPORTANT:
You MUST run Cell 6 BEFORE Cell 10, because:
- Cell 6 adds the data to the `result` dictionary
- Cell 10 converts `result` to DataFrame and saves it
- If you skip Cell 6, the Euler data won't be in the saved file!

---

## Need Help?
If you're unsure which cell is which:
1. Look for the cell that starts with `# E. EULER ANGLE CONVERSION`
2. That's Cell 6 - run it first!
3. Then find the cell with `df_master.to_parquet` 
4. That's Cell 10 - run it second!
