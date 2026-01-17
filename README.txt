# Motion Pipeline – Jupyter + Cursor Project Template

This project provides a fully modular motion-processing pipeline based on:
- NumPy
- Pandas
- SciPy (Slerp, Rotation, CubicSpline, SavGol)
- Matplotlib
- Jupyter Notebook
- Local or Cursor execution

## Structure

motion_pipeline/
│
├── src/                 # All reusable pipeline modules
├── notebooks/           # Step-by-step notebooks for analysis
├── data/                # Place your input CSV here
├── run_pipeline.py      # CLI runner (end-to-end)
├── requirements.txt
└── environment.yml

## Quick Start

1. Create conda env:
   conda env create -f environment.yml
   conda activate motion-pipeline

2. Open Jupyter:
   jupyter lab

3. OR open the project in Cursor and run cells interactively.

4. Add your input CSV to the `data/` folder.

## End-to-end run:

python run_pipeline.py --csv data/your_input.csv

## Notebooks:
- 00_setup.ipynb
- 01_load_and_inspect.ipynb
- 02_preprocess.ipynb
- 03_resample.ipynb
- 04_reference_detection.ipynb
- 05_rotvec_omega.ipynb
- 06_qc.ipynb
- 07_export.ipynb
- 08_full_pipeline_runner.ipynb