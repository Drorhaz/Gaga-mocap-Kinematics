"""
Deep analysis of Master Audit Log XLSX output
"""
import pandas as pd
import json
from pathlib import Path

# Read the latest audit XLSX
xlsx_path = Path("reports/Master_Audit_Log_20260123_182319.xlsx")
xl = pd.ExcelFile(xlsx_path)

print("=" * 80)
print("MASTER AUDIT LOG DEEP REVIEW")
print("=" * 80)

# List all sheets
print(f"\nSheets found: {xl.sheet_names}")

# Read the main audit sheet
df = pd.read_excel(xl, sheet_name='Parameter_Audit')

print(f"\nDimensions: {df.shape[0]} rows x {df.shape[1]} columns")
print(f"\nTotal Columns: {len(df.columns)}")

# Show all columns
print("\n" + "=" * 80)
print("ALL COLUMNS IN AUDIT")
print("=" * 80)
for i, col in enumerate(df.columns, 1):
    print(f"{i:3d}. {col}")

# Analyze missing/null values
print("\n" + "=" * 80)
print("MISSING/NULL VALUE ANALYSIS")
print("=" * 80)

missing_stats = []
for col in df.columns:
    null_count = df[col].isna().sum()
    null_pct = (null_count / len(df)) * 100
    # Count empty strings as well
    if df[col].dtype == 'object':
        empty_count = (df[col] == '').sum()
        empty_pct = (empty_count / len(df)) * 100
    else:
        empty_count = 0
        empty_pct = 0
    
    total_missing = null_count + empty_count
    total_missing_pct = (total_missing / len(df)) * 100
    
    missing_stats.append({
        'column': col,
        'null_count': null_count,
        'null_pct': null_pct,
        'empty_count': empty_count,
        'empty_pct': empty_pct,
        'total_missing': total_missing,
        'total_missing_pct': total_missing_pct
    })

missing_df = pd.DataFrame(missing_stats)
missing_df = missing_df.sort_values('total_missing_pct', ascending=False)

# Show columns with any missing data
print("\nWARNING - COLUMNS WITH MISSING/EMPTY VALUES:")
problematic = missing_df[missing_df['total_missing'] > 0]
if len(problematic) > 0:
    for _, row in problematic.iterrows():
        print(f"\n  - {row['column']}")
        print(f"    Null: {row['null_count']} ({row['null_pct']:.1f}%)")
        if row['empty_count'] > 0:
            print(f"    Empty: {row['empty_count']} ({row['empty_pct']:.1f}%)")
        print(f"    Total Missing: {row['total_missing']} ({row['total_missing_pct']:.1f}%)")
else:
    print("  [OK] No missing values found!")

# Compare with schema
print("\n" + "=" * 80)
print("SCHEMA COMPLIANCE CHECK")
print("=" * 80)

schema_path = Path("config/report_schema.json")
with open(schema_path) as f:
    schema = json.load(f)

# Extract all expected parameters from schema
expected_params = set()
for step_name, step_info in schema['steps'].items():
    for param_name in step_info['parameters'].keys():
        # Convert nested keys to column names (e.g., "identity.run_id" -> "S0_identity.run_id")
        expected_params.add(param_name)

# Get actual columns (strip section prefixes)
actual_columns = set(df.columns)

# Try to match parameters with actual columns
print("\nSCHEMA PARAMETERS vs ACTUAL COLUMNS:")

# Group by step
for step_name, step_info in schema['steps'].items():
    print(f"\n{step_name.upper()} ({step_info['description']})")
    print("-" * 60)
    
    for param_name, param_info in step_info['parameters'].items():
        # Look for this parameter in columns
        matching_cols = [col for col in actual_columns if param_name in col or col.endswith(param_name)]
        
        section = param_info.get('section', 'N/A')
        
        if matching_cols:
            status = "[OK] FOUND"
            col_name = matching_cols[0]
            # Check if it has data
            if col_name in df.columns:
                missing = df[col_name].isna().sum()
                if missing == len(df):
                    status = "[WARN] FOUND BUT ALL NULL"
                elif missing > 0:
                    status = f"[WARN] FOUND BUT {missing}/{len(df)} NULL"
        else:
            status = "[MISSING]"
        
        print(f"  {status:30s} [{section}] {param_name}")

# Show sample data from first row
print("\n" + "=" * 80)
print("SAMPLE DATA (First Recording)")
print("=" * 80)

if len(df) > 0:
    print(f"\nRun ID: {df['S0_identity.run_id'].iloc[0] if 'S0_identity.run_id' in df.columns else 'N/A'}")
    
    # Show key metrics by section
    sections = {
        'S0': 'Data Lineage & Provenance',
        'S1': 'Rácz Calibration Layer',
        'S2': 'Temporal Quality & Sampling',
        'S3': 'Gap & Interpolation',
        'S4': "Winter's Residual Validation",
        'S5': 'Reference Detection',
        'S6': 'Biomechanics & Outliers',
        'S7': 'Signal-to-Noise',
        'S8': 'Decision Matrix'
    }
    
    for section_code, section_name in sections.items():
        section_cols = [col for col in df.columns if col.startswith(f"{section_code}_")]
        if section_cols:
            print(f"\n[{section_code}] {section_name}:")
            for col in section_cols[:5]:  # Show first 5 columns from each section
                val = df[col].iloc[0]
                print(f"  {col}: {val}")
            if len(section_cols) > 5:
                print(f"  ... and {len(section_cols) - 5} more columns")

# Statistical summary for numeric columns
print("\n" + "=" * 80)
print("NUMERIC COLUMNS SUMMARY")
print("=" * 80)

numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
print(f"\nTotal numeric columns: {len(numeric_cols)}")

for col in numeric_cols:
    non_null = df[col].dropna()
    if len(non_null) > 0:
        print(f"\n{col}:")
        print(f"  Count: {len(non_null)}/{len(df)}")
        print(f"  Range: [{non_null.min():.2f}, {non_null.max():.2f}]")
        print(f"  Mean: {non_null.mean():.2f}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
