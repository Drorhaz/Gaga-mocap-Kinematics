import json
from pathlib import Path

NOTEBOOK_PATH = Path("notebooks/06_ultimate_kinematics.ipynb")

print("Moving Euler cell to correct position...")

with open(NOTEBOOK_PATH, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find indices
euler_idx = None
first_df_master_idx = None

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        
        if 'EULER ANGLE CONVERSION' in source and euler_idx is None:
            euler_idx = i
        
        if 'df_master = pd.DataFrame(result)' in source and first_df_master_idx is None:
            first_df_master_idx = i

print(f"Current Euler cell: index {euler_idx}")
print(f"First df_master cell: index {first_df_master_idx}")

if euler_idx and first_df_master_idx:
    if euler_idx >= first_df_master_idx:
        print(f"\n[PROBLEM] Euler at {euler_idx} is AFTER df_master at {first_df_master_idx}")
        print("Moving Euler cell to just before df_master...")
        
        # Remove Euler cell from current position
        euler_cell = nb['cells'].pop(euler_idx)
        
        # Insert before first df_master (adjust index since we removed one)
        new_idx = first_df_master_idx if first_df_master_idx < euler_idx else first_df_master_idx - 1
        nb['cells'].insert(new_idx, euler_cell)
        
        # Save
        backup = NOTEBOOK_PATH.parent / f"{NOTEBOOK_PATH.stem}_before_move.ipynb"
        print(f"\nBackup: {backup}")
        with open(backup, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        
        print(f"Saving: {NOTEBOOK_PATH}")
        with open(NOTEBOOK_PATH, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        
        print(f"\n[OK] Moved Euler cell from index {euler_idx} to {new_idx}")
        print("    Now it runs BEFORE df_master creation")
    else:
        print(f"\n[OK] Cell order is already correct")
else:
    print("\n[ERROR] Could not find required cells")

print("\nNEXT: Reload notebook and Restart & Run All")
