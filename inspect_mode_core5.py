import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Lines 1050 to 1350 of mode.js ---")
print("".join(lines[1050:1350]))
