import pandas as pd

xl = pd.ExcelFile('reports/Master_Audit_Log_FINAL.xlsx')
df = pd.read_excel(xl, sheet_name='Parameter_Audit')

print('Step 04 sample values for first recording:')
print(f"  filter_cutoff_hz: {df['step_04_filter_params_filter_cutoff_hz'].iloc[0]}")
print(f"  winter_failed: {df['step_04_filter_params_winter_analysis_failed'].iloc[0]}")
print(f"  residual_rms: {df['step_04_filter_params_residual_rms_mm'].iloc[0]}")
print(f"  residual_slope: {df['step_04_filter_params_residual_slope'].iloc[0]}")
print(f"  decision: {str(df['step_04_filter_params_decision_reason'].iloc[0])[:60]}")
print(f"  height_cm: {df['step_04_subject_metadata_height_cm'].iloc[0]}")

# Count NULLs
null_counts = df.isnull().sum()
null_cols = null_counts[null_counts > 0]
print(f'\nTotal NULL columns: {len(null_cols)}/{len(df.columns)}')
print('\nRemaining NULLs:')
for col, count in null_cols.items():
    print(f'  - {col}: {count}/2 records')
