import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()

for i, l in enumerate(lines, 1):
    if 'id="screen-community"' in l:
        print(f"screen-community found at line {i}")
        for j in range(i-1, i+150):
            print(f"{j+1}: {lines[j]}", end='')
        break
