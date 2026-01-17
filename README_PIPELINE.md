# 🎬 Motion Capture Pipeline - Quick Start

## 🚀 Automated Batch Processing

### 1. Install Dependencies
```bash
pip install -r pipeline_requirements.txt
```

### 2. Test Your Setup
```bash
python test_pipeline_setup.py
```

### 3. Run the Pipeline

**Auto-discover all CSV files:**
```bash
python run_pipeline.py --auto-discover
```

**Process specific files:**
```bash
python run_pipeline.py --csv-list csv_files_example.txt
```

**Process single file:**
```bash
python run_pipeline.py --single "data/734/T1/734_T1_P2_R1_Take 2025-12-01 02.28.24 PM.csv"
```

## 📖 Full Documentation

See [PIPELINE_USAGE.md](PIPELINE_USAGE.md) for complete documentation.

## 📁 Project Structure

```
gaga/
├── run_pipeline.py              # Main automation script
├── test_pipeline_setup.py       # Setup verification script
├── pipeline_requirements.txt    # Dependencies
├── csv_files_example.txt        # Example file list
├── PIPELINE_USAGE.md           # Complete documentation
├── config/
│   └── config_v1.yaml          # Single source of truth
├── notebooks/
│   ├── 00_setup.ipynb
│   ├── 01_Load_Inspect.ipynb
│   ├── 02_preprocess.ipynb
│   ├── 03_resample.ipynb
│   ├── 04_filtering.ipynb
│   ├── 05_reference_detection.ipynb
│   ├── 06_rotvec_omega.ipynb
│   ├── 07_master_quality_report.ipynb
│   └── 08_visualization_and_analysis.ipynb
├── data/
│   └── [subject]/[session]/[csv files]
├── derivatives/          # Processed data outputs
├── logs/                # Execution logs
└── reports/             # Quality reports
```

## ✅ Quick Check

- [ ] Install dependencies: `pip install -r pipeline_requirements.txt`
- [ ] Test setup: `python test_pipeline_setup.py`
- [ ] Place CSV files in `data/` directory
- [ ] Run pipeline: `python run_pipeline.py --auto-discover`
- [ ] Check logs: `logs/pipeline_run_*.log`
- [ ] Review results: `reports/Master_Audit_Log_*.xlsx`

## 🎯 Manual Processing (Per File)

If you prefer manual control, run notebooks in order:

1. Edit `config/config_v1.yaml` → set `current_csv`
2. Run notebooks: 01 → 02 → 03 → 04 → 05 → 06
3. Run 07 to generate master report
4. Run 08 for visualizations

## 📊 Outputs

- **Logs:** `logs/pipeline_run_YYYYMMDD_HHMMSS.log`
- **Batch Summary:** `reports/batch_summary_YYYYMMDD_HHMMSS.json`
- **Master Report:** `reports/Master_Audit_Log_YYYYMMDD_HHMMSS.xlsx`
- **Derivatives:** `derivatives/step_XX/[run_id]__*.parquet`

## 🆘 Help

```bash
python run_pipeline.py --help
```

For detailed documentation, see [PIPELINE_USAGE.md](PIPELINE_USAGE.md).
