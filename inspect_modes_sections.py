import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line_no in [108, 187, 289, 896, 974, 1075]:
    print(f"\n--- Around line {line_no} ---")
    for j in range(max(0, line_no-10), min(len(lines), line_no+5)):
        print(f"{j+1}: {lines[j]}", end='')
