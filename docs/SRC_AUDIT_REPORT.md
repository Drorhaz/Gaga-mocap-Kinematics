# Source Folder Audit & Consolidation Report

**Project:** Gaga Motion Capture Pipeline  
**Scope:** `src/` folder (45 Python modules)  
**Date:** 2026-01-29  
**Instruction:** No files were modified; this is an analysis-only report.

---

## 1. Redundancy & Deletion Candidates

### 1.1 Obsolete or Broken Entry Points

| Filename | Reason |
|----------|--------|
| **`init.py`** | Redundant with `__init__.py`. Contains only a one-line comment ("Marks src as a Python package"). The standard package marker is `__init__.py`; `init.py` is never imported anywhere and can be removed. |
| **`pipeline.py`** | **Broken imports:** (1) `from .config import CONFIG` — there is no `config.py` in `src/` (only `pipeline_config.py`). (2) `from .utils import ... log_event` — `utils.py` does not define `log_event`. The pipeline is not runnable as-is. Either fix these imports or treat as legacy and document. |

### 1.2 Unreferenced or Narrowly Referenced Scripts

| Filename | Status |
|----------|--------|
| **`init.py`** | Never imported. Safe deletion candidate. |
| **`export_tables.py`** | Only referenced by `pipeline.py` (which is broken). No notebooks or tests import it. If the legacy pipeline is retired, this becomes orphaned. |
| **`interpolation_tracking.py`** | Only used by `02_preprocess.ipynb` (`compute_per_joint_interpolation_stats`). Single consumer; consider keeping but note narrow use. |
| **`interactive_viz.py`** | Only self-reference in docstring. No external imports found in codebase search; may be used from notebooks via dynamic path. Verify before deletion. |
| **`lcs_visualization.py`** | No direct imports found from other `src/` modules or tests. Possibly notebook-only; verify usage. |

### 1.3 Cross-Reference Summary: Main Workflow

- **Notebook workflow:** Notebooks add `SRC_PATH` to `sys.path` and import by bare name (e.g. `from pipeline_config import CONFIG`, `from angular_velocity import ...`). They do **not** use `from src.xxx import`.
- **Test/scripts at project root:** `verify_gates.py`, `test_final_push*.py` use `from src.xxx import`. Tests under `tests/` use either `sys.path` + bare imports or `from src.xxx import`.
- **Gate / pipeline core:** `__init__.py` re-exports artifacts, time_alignment, resampling, euler_isb, burst_classification, gate_integration. These are the main “blessed” API surface.

**Suggested deletion list (with reason):**

1. **`init.py`** — Redundant with `__init__.py`; never imported.
2. **`pipeline.py`** — Do **not** delete yet; fix or document as legacy. It references non-existent `config` and missing `log_event` in `utils`. Either: (a) add `config.py` (or alias `pipeline_config` as `config`) and add `log_event` to `utils.py`, or (b) mark as deprecated and redirect to notebook-driven runs.

---

## 2. Consolidation & Merging Opportunities

### 2.1 Quaternion Logic (Fragmented Across Multiple Files)

| File | Responsibility | Overlap |
|------|----------------|---------|
| **`quaternion_ops.py`** | Low-level: `quat_normalize`, `quat_inv`, `quat_mul`, `quat_shortest`, `quat_enforce_continuity`. Used by `pipeline.py`, `resampling.py`, `reference.py`. | Core math; keep as single source. |
| **`quaternions.py`** | DataFrame-level: `renormalize_all_quat_cols`, `renormalize_quat_block`, column helpers. Used by `time_alignment`, `gapfill_quaternions`, tests. | Overlaps conceptually with normalization. |
| **`quaternion_normalization.py`** | Drift detection, safe normalization with warnings, long-sequence handling. | Duplicate idea of “safe normalize” vs `quaternion_ops.quat_normalize` and `quaternions.renormalize_*`. |

**Recommendation:** Merge into a single **`quaternions`** (or `quaternion_utils`) module:

- Keep `quaternion_ops.py` as the low-level numpy API (or move its functions into `quaternions.py` as private/stable helpers).
- Move `quaternion_normalization.py`’s drift detection and “safe” normalization into `quaternions.py` (or a submodule `quaternions.normalization`).
- Re-export from one place so callers use `from src.quaternions import ...` (and optionally `from src.quaternion_ops import ...` if you keep a separate ops file for backward compatibility).

### 2.2 Validation Modules (Similar Patterns)

| File | Purpose |
|------|--------|
| **`filter_validation.py`** | Winter filter PSD/Welch validation, cutoff checks. |
| **`sg_filter_validation.py`** | Savitzky–Golay derivative validation. |
| **`artifact_validation.py`** | Artifact detection validation. |
| **`reference_validation.py`** | Reference frame / quaternion continuity validation. |
| **`bone_length_validation.py`** | Bone length stability from reference/calibration. |
| **`validation.py`** | Generic validation helpers (used by tests). |

**Recommendation:** Group under a package `src/validation/` (or `src/validations/`):

- `validation/__init__.py` — re-export public APIs.
- `validation/filter_validation.py` — current `filter_validation` + `sg_filter_validation` (or keep two files under the package).
- `validation/artifact_validation.py`, `reference_validation.py`, `bone_length_validation.py` — move as-is.
- Keep top-level `validation.py` only if it is generic; otherwise merge into one of these or into a small `validation/common.py`.

This reduces top-level clutter and makes “validation” a single concept for discovery.

### 2.3 File I/O and Config Loading

| File | Responsibility |
|------|----------------|
| **`utils.py`** | `ensure_dirs`, `sha256_file`, `fingerprint_file`, `write_json`, `normalize_joint_name`. No JSON loading. |
| **`utils_nb07.py`** | JSON loading, `safe_get_path`, `safe_float`, `safe_int`, scoring, Excel export, large `PARAMETER_SCHEMA`. |
| **`pipeline_config.py`** | YAML load, `CONFIG`, `PROJECT_ROOT`, uppercase aliases. |

**Recommendation:**

- **Config:** Keep a single entry point for pipeline config. Either:
  - Rename or alias so `pipeline.py` can do `from .pipeline_config import CONFIG` (and remove the non-existent `config` module), or
  - Add a thin `config.py` that does `from .pipeline_config import CONFIG` (and anything else the pipeline expects).
- **Utils:** Keep `utils.py` for generic file/path helpers. Consider moving `safe_get_path`, `safe_float`, `safe_int` from `utils_nb07.py` into `utils.py` so other modules can use them without depending on the notebook-07 schema. Leave `utils_nb07.py` for report-specific logic (scoring, schema, Excel) that imports from `utils`.

### 2.4 Resampling vs Time Alignment

| File | Responsibility |
|------|----------------|
| **`time_alignment.py`** | Perfect time grid, artifact-aware resampling, monotonicity checks, position/quat resampling. Uses `artifacts`, `quaternions`. |
| **`resampling.py`** | Gate 2 jitter metrics, `estimate_fs`, and (in pipeline) `resample_time_grid`, `resample_pos`, `resample_quat_slerp`. Uses `quaternion_ops`. |

**Recommendation:** The split is partly historical (Gate 2 metrics vs temporal grid logic). Options:

- **Option A:** Keep both; document that `resampling.py` = “Gate 2 metrics + legacy resample API” and `time_alignment.py` = “precise grid and artifact-aware resampling” used by notebooks.
- **Option B:** Move `estimate_fs` and jitter from `resampling.py` into `time_alignment.py` and make `resampling.py` a thin wrapper that imports from `time_alignment` for consistency. Then Gate 2 can still import from `resampling` for API stability.

### 2.5 Gap Filling

- **`gapfill_positions.py`** — Uses `from artifacts import ...` (absolute). Should use `from .artifacts import ...` for package consistency.
- **`gapfill_quaternions.py`** — Uses `from .quaternions import ...` correctly.

**Recommendation:** Fix `gapfill_positions.py` to use relative import. Consider a single `gapfill.py` that exposes `gapfill_positions` and `gapfill_quaternions` subroutines if you want one entry point; otherwise keep two files and fix the import.

### 2.6 Export and Filter Export

- **`filter_export.py`** (537 lines) — Exports filter summaries and optionally calls `winter_export.export_winter_residual_data` via a bare `from winter_export import ...` inside a function.
- **`winter_export.py`** — Winter-specific residual export.

**Recommendation:** Use relative import in `filter_export.py`: `from .winter_export import export_winter_residual_data`. Optionally group `filter_export.py` and `winter_export.py` under an `export/` package (e.g. `export/filter_export.py`, `export/winter_export.py`) if more export types appear.

---

## 3. Architectural Optimization Suggestions

### 3.1 Folder Structure (Modular Layout)

Current `src/` is flat (45 files). Suggested high-level structure:

```
src/
├── __init__.py          # Re-export gate/public API only
├── config.py            # Thin wrapper: from .pipeline_config import CONFIG (or alias)
├── utils.py             # Generic file/path/JSON helpers; add safe_get_path, safe_float, safe_int here
├── pipeline_config.py   # Keep as-is (YAML, CONFIG, aliases)
├── pipeline.py          # Fix imports to use pipeline_config and utils (add log_event or remove use)
│
├── quaternions/         # Optional: package for all quaternion logic
│   ├── __init__.py
│   ├── ops.py           # current quaternion_ops.py
│   ├── normalize.py    # current quaternion_normalization + quaternions renormalize
│   └── ...
│
├── validation/          # All validation modules
│   ├── __init__.py
│   ├── filter_validation.py
│   ├── sg_filter_validation.py
│   ├── artifact_validation.py
│   ├── reference_validation.py
│   ├── bone_length_validation.py
│   └── common.py        # shared helpers from current validation.py
│
├── gates/               # Optional: Gate 2–5 + integration
│   ├── __init__.py
│   ├── resampling.py    # Gate 2
│   ├── filtering.py     # Gate 3
│   ├── euler_isb.py     # Gate 4
│   ├── burst_classification.py  # Gate 5
│   └── gate_integration.py
│
├── preprocessing.py     # Keep; fix to use from .utils or from src.utils
├── time_alignment.py
├── artifacts.py
├── reference.py
├── calibration.py
├── kinematics_alignment.py
├── angular_velocity.py
├── kinematic_repair.py
├── gapfill_positions.py
├── gapfill_quaternions.py
├── export_tables.py
├── filter_export.py
├── winter_export.py
├── qc.py
├── qc_columns.py
├── units.py
├── skeleton_defs.py
├── preprocessing.py
├── interpolation_logger.py
├── interpolation_tracking.py
├── snr_analysis.py
├── joint_statistics.py
├── subject_validation.py
├── utils_nb07.py        # Report-specific; keep in src or move to notebooks/support
├── interactive_viz.py
├── lcs_visualization.py
├── coordinate_systems.py
└── validation.py        # If not merged into validation/
```

Introduce subpackages gradually (e.g. `validation/` first) and keep backward-compatible re-exports in `__init__.py` so notebooks and tests do not break.

### 3.2 “God Files” (Too Many Responsibilities)

| File | Approx. Lines | Suggestion |
|------|----------------|------------|
| **`filtering.py`** | ~1767 | Split: (1) Constants and region definitions (`BODY_REGIONS`, etc.) → `filtering_config.py` or `config/filtering.yaml`. (2) Winter residual analysis → `winter_residual.py`. (3) Apply filter / pipeline step → keep in `filtering.py` and import from (1) and (2). |
| **`utils_nb07.py`** | ~1488 | Split: (1) `PARAMETER_SCHEMA` → JSON or separate `report_schema.py`. (2) `safe_get_path`, `safe_float`, `safe_int` → `utils.py`. (3) Scoring functions → `report_scores.py` or keep in `utils_nb07` and import utils. (4) Excel/build logic → keep in `utils_nb07` or move to `report_excel.py`. |
| **`burst_classification.py`** | ~770 | Consider extracting: (1) Threshold constants to config or `burst_config.py`. (2) Pure classification logic vs I/O and reporting into smaller modules. |
| **`calibration.py`** | ~671 | Extract: (1) V-pose detection and math. (2) Offset computation. (3) Export and file I/O. So that tests can import only the part they need. |
| **`preprocessing.py`** | ~552 | Already large; consider splitting CSV parsing, name mapping, and interpolation into separate modules and keep `preprocessing.py` as the orchestrator. |

### 3.3 Shared Constants and Config

- **Single source of truth:** `config/config_v1.yaml` + `pipeline_config.py` is correct. Ensure no script duplicates these values (e.g. `FS_TARGET`, `BODY_REGIONS`) in code; move any discovered duplicates into config or a single `constants.py` that reads from config.
- **Gate thresholds:** Burst, filter, and validation thresholds appear in multiple places (e.g. `burst_classification`, `verify_gates.py`). Centralize in `config_v1.yaml` or a dedicated `gate_thresholds.json` / module and have code read from there.
- **Where config should live:** Pipeline-wide: `config/config_v1.yaml` and `src/pipeline_config.py`. Feature-specific constants (e.g. filter regions, burst tiers) can live in the same YAML under keys or in small modules under `src/` that are documented as “config” (e.g. `filtering_config.py` that only holds constants and region definitions).

### 3.4 Import Consistency

- **Relative vs absolute:** Prefer relative imports inside `src/` (e.g. `from .artifacts import ...`) so the package works regardless of how the project is run. Fix: `gapfill_positions.py` (use `from .artifacts import ...`), `filter_export.py` (use `from .winter_export import ...`), and `preprocessing.py` (use `from .utils import normalize_joint_name` or `from src.utils import ...` when run as package).
- **Notebooks:** They use `sys.path.insert(0, SRC_PATH)` and bare imports. This is acceptable; ensure `SRC_PATH` points to `src/` and that any new subpackages (e.g. `src.validation`) are importable the same way (e.g. `from filter_validation import ...` if `validation` is not a package, or `from validation.filter_validation import ...` if it is).

---

## Summary Tables

### Deletion Candidates

| File | Action | Reason |
|------|--------|--------|
| `init.py` | Delete | Redundant with `__init__.py`; never imported. |
| `pipeline.py` | Fix or deprecate | Imports non-existent `config` and missing `log_event`. |

### High-Impact Consolidations

| Group | Action |
|-------|--------|
| Quaternion logic | Merge `quaternion_ops`, `quaternions`, `quaternion_normalization` into one module or `quaternions/` package. |
| Validation | Group `*_validation.py` under `validation/` package. |
| Utils | Move `safe_get_path`, `safe_float`, `safe_int` to `utils.py`; keep `utils_nb07` for report-only logic. |
| Config | Add `config.py` that re-exports `CONFIG` from `pipeline_config`, or change `pipeline.py` to import from `pipeline_config`. |

### God Files to Split

| File | Priority | Suggested split |
|------|----------|------------------|
| `filtering.py` | High | Config/constants, winter_residual, main filtering. |
| `utils_nb07.py` | High | Schema (file or module), safe accessors → utils, scoring + Excel. |
| `burst_classification.py` | Medium | Constants vs classification vs I/O. |
| `calibration.py` | Medium | Detection, offsets, export. |

---

*End of report. No files were modified.*
