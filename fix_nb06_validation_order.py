"""
Fix notebook 06: Move validation cell to correct position.
Validation cell needs to be AFTER feature engineering cell.
"""
import json
from pathlib import Path

nb_path = Path(r'c:\Users\drorh\OneDrive - Mobileye\Desktop\gaga\notebooks\06_ultimate_kinematics.ipynb')

# Load notebook
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find the validation cell
validation_cell_idx = None
for i, cell in enumerate(nb['cells']):
    if cell.get('cell_type') == 'code':
        source = ''.join(cell.get('source', []))
        if 'Validate Master Feature Set Completeness' in source:
            validation_cell_idx = i
            break

if validation_cell_idx is None:
    print("[ERROR] Could not find validation cell")
    exit(1)

print(f"[OK] Found validation cell at index {validation_cell_idx}")

# Find the feature engineering cell
feature_cell_idx = None
for i, cell in enumerate(nb['cells']):
    if cell.get('cell_type') == 'code':
        source = ''.join(cell.get('source', []))
        if 'Add magnitude and rotation vector features to result' in source:
            feature_cell_idx = i
            break

if feature_cell_idx is None:
    print("[ERROR] Could not find feature engineering cell")
    exit(1)

print(f"[OK] Found feature engineering cell at index {feature_cell_idx}")

# Check if validation is before feature engineering
if validation_cell_idx < feature_cell_idx:
    print(f"[FIX] Validation cell ({validation_cell_idx}) is before feature cell ({feature_cell_idx}), moving it...")
    
    # Extract the validation cell
    validation_cell = nb['cells'].pop(validation_cell_idx)
    
    # Insert after feature engineering cell (adjust index since we removed one)
    target_idx = feature_cell_idx  # feature_cell_idx already shifted down by 1 after pop
    nb['cells'].insert(target_idx, validation_cell)
    
    print(f"[OK] Moved validation cell to after feature engineering cell (new index: {target_idx})")
    
    # Save
    with open(nb_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
    
    print(f"[OK] Saved fixed notebook: {nb_path}")
else:
    print("[OK] Cell order is already correct, no changes needed")

print("\nNew cell order (cells 8-12):")
print("=" * 80)
for i in range(max(0, validation_cell_idx-2), min(len(nb['cells']), validation_cell_idx+5)):
    cell = nb['cells'][i]
    cell_type = cell.get('cell_type', 'unknown')
    source = cell.get('source', [''])
    first_line = ''.join(source[:1])[:70] if source else 'empty'
    print(f"Cell {i:2d}: {cell_type:8s} - {first_line}")
