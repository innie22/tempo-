import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('recoverySetup.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'shouldShowFirstTimeWelcome' in line or 'open(' in line:
        start = max(0, i - 10)
        end = min(len(lines), i + 25)
        print(f"--- Line {i+1} ---")
        print(''.join(lines[start:end]))
