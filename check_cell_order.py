import json

with open('notebooks/06_ultimate_kinematics.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

euler_idx = None
df_idx = None

for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source'])
        if 'EULER ANGLE CONVERSION' in source:
            euler_idx = i
            has_output = len(cell.get('outputs', [])) > 0
            if has_output:
                output = str(cell.get('outputs', []))
                if '19 joints' in output:
                    print(f"Euler cell at index {i}: GOOD - shows 19 joints")
                elif '0 joints' in output:
                    print(f"Euler cell at index {i}: BAD - shows 0 joints")
                else:
                    print(f"Euler cell at index {i}: Has output but unclear")
            else:
                print(f"Euler cell at index {i}: No output (not executed)")
        
        if 'df_master = pd.DataFrame(result)' in source:
            df_idx = i
            print(f"df_master creation at index {i}")

if euler_idx and df_idx:
    if euler_idx < df_idx:
        print(f"\n[OK] Cell order is correct: Euler ({euler_idx}) before df_master ({df_idx})")
    else:
        print(f"\n[ERROR] Cell order is WRONG: Euler ({euler_idx}) after df_master ({df_idx})")
elif not euler_idx:
    print("\n[ERROR] No Euler cell found!")
elif not df_idx:
    print("\n[ERROR] No df_master cell found!")
