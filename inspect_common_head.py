import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    lines = f.readlines()

print("--- VI common ---")
for i in range(25, 45):
    print(f"{i+1}: {repr(lines[i])}")

print("\n--- EN common ---")
for i in range(809, 830):
    print(f"{i+1}: {repr(lines[i])}")
