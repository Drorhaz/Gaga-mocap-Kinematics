# Why notebook 06 couldn't read the step 04 parquet

## What actually failed

- **Notebook 06** expected this file to exist:
  `derivatives/step_04_filtering/671_T1_P1_R2_Take 2026-01-06 03.57.12 PM_003__filtered.parquet`
- That file was **missing**, so 06 raised `FileNotFoundError` and the pipeline stopped.

So the failure was: **the step 04 output parquet for that run (P1_R2) was not there when 06 ran.**

---

## What we know from the files on disk

In `derivatives/step_04_filtering/` for subject 671:

- **P1_R1** (first CSV):  
  `*__filtering_summary.json`, `*__winter_residual_data.json`, `*__kinematics_map.json`, `*__qc_excluded_positions.json`  
  → no `*__filtered.parquet`
- **P1_R2** (second CSV, the one 06 was using):  
  same four JSON files  
  → no `*__filtered.parquet`
- **Glob for any step-04 parquet:**  
  `*__filtered.parquet` → **0 files** in the whole folder.

So:

1. Step 04 **did run** for P1_R2: it produced the summary, residuals, kinematics map, and QC JSONs.
2. Step 04 **did not produce any** `__filtered.parquet` for 671 (neither for P1_R1 nor P1_R2).

So **06 couldn’t read the 04 parquet because 04 never wrote it** (for that run, and in fact for any 671 run).

---

## Why might 04 not have written the parquet?

Possible causes:

1. **Different notebook ran for step 04**  
   If there were two notebooks matching `04_*.ipynb`, the runner might have used one that:
   - writes the JSONs (summary, residuals, etc.) in one place, and
   - writes the parquet in a **later** cell that never ran (e.g. timeout, or an earlier cell failed in a way that was swallowed).
   So you’d see the JSONs but no parquet.

2. **Parquet write failed at runtime**  
   The cell that does `df_filtered.to_parquet(out_path, ...)` might have raised (e.g. permission, OneDrive lock, path length on Windows). If that exception wasn’t visible in the pipeline log, it would look like “04 ran” (because 04 started) but the file wouldn’t exist.

3. **Wrong RUN_ID when writing**  
   If 04 used a different `RUN_ID` than 06 (e.g. stale config so 04 thought it was still P1_R1), 04 might have written/overwritten P1_R1’s parquet instead of P1_R2’s. Then 06 would look for P1_R2’s file and not find it.  
   That would still leave the puzzle: we see **no** parquet at all for 671, so either the “wrong” write also failed, or only one 04 notebook ran and it never wrote a parquet.

So the **root cause** is one of: **wrong notebook (parquet in a cell that didn’t run), parquet write failure, or RUN_ID mismatch** (with the “no parquet at all” hint pointing more to 1 or 2).

---

## What the “solution” actually does

The changes we made don’t fix a failed or skipped parquet write directly. They make the pipeline more robust and deterministic:

1. **Injecting `RUN_ID` (and `current_csv`) from the runner into the notebooks**  
   - Ensures 04 and 06 always use the **same** run id for the current CSV.  
   - Removes dependence on config load order or cached config, so a “wrong RUN_ID” in 04 is much less likely.

2. **Preferring a single step-04 notebook (e.g. `04_filtering_output`)**  
   - Ensures the **same** notebook runs every time.  
   - If the chosen notebook is the one where the parquet is written in a cell that always runs, you avoid the “other 04 notebook ran and never reached the parquet cell” case.

So:

- **06 couldn’t read the 04 parquet because 04 never wrote that file** (and in fact wrote no parquet for 671).
- **Why 04 didn’t write it** is likely either: the notebook that ran doesn’t write parquet in the execution path that ran, or the parquet write failed (permissions/sync/path).
- **The fix** makes RUN_ID consistent and step-04 notebook choice deterministic; if the issue was RUN_ID or which notebook ran, re-running the pipeline should fix it. If the issue was a real write failure, you may need to re-run step 04 and check logs/OneDrive/permissions for that run.
