import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- VI posts (lines 585-610) ---")
for i in range(585, 605):
    print(f"{i+1}: {lines[i]}", end='')

print("\n--- EN posts (lines 1365-1390) ---")
for i in range(1365, 1385):
    print(f"{i+1}: {lines[i]}", end='')
