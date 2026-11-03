import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'MODES.RECOVERY' in line:
        print(f"Line {i+1}: {line.strip()}")
