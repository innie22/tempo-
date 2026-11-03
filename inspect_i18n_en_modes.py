import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()

for t in [895, 973, 1074]:
    print(f"\n--- Target line {t} ---")
    for j in range(max(0, t-3), min(len(lines), t+4)):
        print(f"{j+1}: {repr(lines[j])}")
