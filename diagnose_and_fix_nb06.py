"""
Complete diagnostic and fix for Notebook 06 Euler cell placement
"""

import json
from pathlib import Path

NOTEBOOK_PATH = Path("notebooks/06_ultimate_kinematics.ipynb")

print("="*80)
print("NOTEBOOK 06 DIAGNOSTIC & FIX")
print("="*80)

# Load notebook
with open(NOTEBOOK_PATH, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"\nTotal cells: {len(nb['cells'])}")

# Find all Euler-related cells
euler_cells = []
df_master_cell_idx = None

for idx, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        
        # Find Euler conversion cells
        if 'EULER ANGLE CONVERSION' in source:
            has_output = len(cell.get('outputs', [])) > 0
            output_text = str(cell.get('outputs', []))
            
            euler_cells.append({
                'index': idx,
                'source_preview': source[:150].replace('\n', ' '),
                'has_output': has_output,
                'finds_zero_joints': 'added for 0 joints' in output_text or '0 columns' in output_text
            })
        
        # Find where df_master is created
        if 'df_master = pd.DataFrame(result)' in source:
            df_master_cell_idx = idx

print(f"\n--- EULER CONVERSION CELLS ---")
print(f"Found {len(euler_cells)} Euler cell(s):")
for i, cell_info in enumerate(euler_cells, 1):
    print(f"\n  Euler Cell {i}:")
    print(f"    Index: {cell_info['index']}")
    print(f"    Preview: {cell_info['source_preview']}")
    print(f"    Has output: {cell_info['has_output']}")
    if cell_info['finds_zero_joints']:
        print(f"    [WARNING] PROBLEM: Runs too early, finds 0 joints - SHOULD BE DELETED")
    else:
        print(f"    [OK] Would run in correct position")

print(f"\n--- DF_MASTER CREATION ---")
print(f"df_master creation at index: {df_master_cell_idx}")

# Determine what needs to be fixed
cells_to_remove = [c['index'] for c in euler_cells if c['finds_zero_joints']]
good_euler_cells = [c for c in euler_cells if not c['finds_zero_joints']]

print(f"\n--- REQUIRED ACTIONS ---")
if cells_to_remove:
    print(f"[X] Need to remove {len(cells_to_remove)} bad Euler cell(s) at indices: {cells_to_remove}")
else:
    print(f"[OK] No bad Euler cells found")

if not good_euler_cells:
    print(f"[X] No good Euler cell found - need to add one!")
elif df_master_cell_idx and good_euler_cells:
    good_cell_idx = good_euler_cells[0]['index']
    if good_cell_idx >= df_master_cell_idx:
        print(f"[X] PROBLEM: Good Euler cell at index {good_cell_idx} runs AFTER df_master at {df_master_cell_idx}")
        print(f"   The Euler columns won't be saved!")
    else:
        print(f"[OK] Good Euler cell at index {good_cell_idx} runs BEFORE df_master at {df_master_cell_idx}")

# Apply fixes
print(f"\n" + "="*80)
print("APPLYING FIXES")
print("="*80)

if cells_to_remove:
    # Remove bad cells (in reverse order)
    for idx in sorted(cells_to_remove, reverse=True):
        print(f"\nRemoving bad Euler cell at index {idx}...")
        del nb['cells'][idx]
    
    # Save
    backup_path = NOTEBOOK_PATH.parent / f"{NOTEBOOK_PATH.stem}_pre_euler_fix.ipynb"
    print(f"\nCreating backup: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    
    print(f"Saving fixed notebook: {NOTEBOOK_PATH}")
    with open(NOTEBOOK_PATH, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    
    print("\n[X] Fixes applied!")
    print("\nNEXT STEPS:")
    print("  1. Reload notebook in Jupyter")
    print("  2. Kernel [X] Restart & Run All")
    print("  3. Look for output: '[OK] Euler angles added for 19 joints'")
    print("  4. Run verification cell to confirm 57 Euler columns")
else:
    print("\n[X] No fixes needed - notebook structure looks correct!")
    print("\nIf Euler columns are still 0:")
    print("  - Make sure you ran 'Restart & Run All' (not just 'Run All')")
    print("  - Check that the Euler cell output shows '19 joints' not '0 joints'")

