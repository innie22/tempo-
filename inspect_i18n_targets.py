import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()

targets = [108, 187, 289, 900, 978, 1079]
for t in targets:
    print(f"\n--- Target line {t} ---")
    for j in range(max(0, t-3), min(len(lines), t+3)):
        print(f"{j+1}: {repr(lines[j])}")
