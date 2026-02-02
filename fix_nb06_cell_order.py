"""
Fix notebook 06: Move feature engineering cell to correct position.
Cell 5 needs to be AFTER Cell 10 (linear velocity computation).
"""
import json
from pathlib import Path
import shutil

nb_path = Path(r'c:\Users\drorh\OneDrive - Mobileye\Desktop\gaga\notebooks\06_ultimate_kinematics.ipynb')

# Backup
backup_path = nb_path.with_suffix('.ipynb.backup')
shutil.copy(nb_path, backup_path)
print(f"[OK] Created backup: {backup_path}")

# Load notebook
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the misplaced feature engineering cell (Cell 5)
feature_cell_idx = None
for i, cell in enumerate(nb['cells']):
    if cell.get('cell_type') == 'code':
        source = ''.join(cell.get('source', []))
        if 'Add magnitude and rotation vector features to result' in source:
            feature_cell_idx = i
            break

if feature_cell_idx is None:
    print("❌ Could not find feature engineering cell")
    exit(1)

print(f"[OK] Found feature engineering cell at index {feature_cell_idx}")

# Find the linear velocity cell (Cell 10 in current structure)
linear_vel_idx = None
for i, cell in enumerate(nb['cells']):
    if cell.get('cell_type') == 'code':
        source = ''.join(cell.get('source', []))
        if 'Linear velocity and acceleration from root-relative positions' in source:
            linear_vel_idx = i
            break

if linear_vel_idx is None:
    print("❌ Could not find linear velocity cell")
    exit(1)

print(f"[OK] Found linear velocity cell at index {linear_vel_idx}")

# Extract the feature cell
feature_cell = nb['cells'].pop(feature_cell_idx)

# Adjust target index (linear_vel_idx may have shifted if feature was before it)
if feature_cell_idx < linear_vel_idx:
    target_idx = linear_vel_idx  # No adjustment needed, already shifted
else:
    target_idx = linear_vel_idx + 1

# Insert after linear velocity cell
nb['cells'].insert(target_idx, feature_cell)

print(f"[OK] Moved feature cell from index {feature_cell_idx} to after index {target_idx}")

# Save
with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print(f"[OK] Saved fixed notebook: {nb_path}")
print("\nNew cell order (first 15):")
print("=" * 80)
for i, cell in enumerate(nb['cells'][:15]):
    cell_type = cell.get('cell_type', 'unknown')
    source = cell.get('source', [''])
    first_line = ''.join(source[:1])[:70] if source else 'empty'
    print(f"Cell {i:2d}: {cell_type:8s} - {first_line}")
