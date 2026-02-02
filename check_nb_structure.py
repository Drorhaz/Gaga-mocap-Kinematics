import json
from pathlib import Path

nb_path = Path(r'c:\Users\drorh\OneDrive - Mobileye\Desktop\gaga\notebooks\06_ultimate_kinematics.ipynb')
nb = json.load(open(nb_path, encoding='utf-8'))

print("First 15 cells:")
print("=" * 80)
for i, cell in enumerate(nb['cells'][:15]):
    cell_type = cell.get('cell_type', 'unknown')
    source = cell.get('source', [''])
    first_line = source[0][:70] if source else 'empty'
    print(f"Cell {i:2d}: {cell_type:8s} - {first_line}")
