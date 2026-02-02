"""
Script to clean up duplicate Euler conversion cell in Notebook 06
Removes the misplaced cell that runs before quaternions are created
"""

import json
from pathlib import Path

NOTEBOOK_PATH = Path("notebooks/06_ultimate_kinematics.ipynb")

print("Cleaning up Notebook 06...")
print(f"Reading: {NOTEBOOK_PATH}")

# Load notebook
with open(NOTEBOOK_PATH, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find cells with Euler conversion
euler_cells = []
for idx, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'E. EULER ANGLE CONVERSION' in source and 'Converting quaternions to Euler' in source:
            euler_cells.append({
                'index': idx,
                'has_output': len(cell.get('outputs', [])) > 0,
                'output_text': str(cell.get('outputs', [])),
                'source_start': source[:100]
            })

print(f"\nFound {len(euler_cells)} Euler conversion cells:")
for i, cell_info in enumerate(euler_cells, 1):
    print(f"\n  Cell {i} at index {cell_info['index']}:")
    print(f"    Has output: {cell_info['has_output']}")
    if 'added for 0 joints' in cell_info['output_text']:
        print(f"    Status: WRONG POSITION (runs too early, finds 0 joints) - WILL DELETE")
    else:
        print(f"    Status: CORRECT POSITION (after quaternions created) - KEEP")

# Remove the cell that shows "0 joints" (the one running too early)
cells_to_remove = []
for cell_info in euler_cells:
    if 'added for 0 joints' in cell_info['output_text']:
        cells_to_remove.append(cell_info['index'])

if cells_to_remove:
    print(f"\nRemoving {len(cells_to_remove)} misplaced cell(s)...")
    # Remove in reverse order to maintain indices
    for idx in sorted(cells_to_remove, reverse=True):
        print(f"  Removing cell at index {idx}")
        del nb['cells'][idx]
    
    # Save cleaned notebook
    backup_path = NOTEBOOK_PATH.parent / f"{NOTEBOOK_PATH.stem}_backup.ipynb"
    print(f"\nCreating backup: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    
    print(f"Saving cleaned notebook: {NOTEBOOK_PATH}")
    with open(NOTEBOOK_PATH, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    
    print("\n[OK] Notebook cleaned successfully!")
    print("     The misplaced Euler cell has been removed.")
    print("     The correct Euler cell (after quaternions) remains.")
    print("\nNext steps:")
    print("  1. Reload the notebook in Jupyter")
    print("  2. Kernel -> Restart & Run All")
    print("  3. Verify Euler columns appear in output")
else:
    print("\n[OK] No misplaced cells found. Notebook is already correct.")

