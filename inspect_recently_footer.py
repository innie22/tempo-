import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Lines 7050 to 7100 of mode.js ---")
print("".join(lines[7050:7100]))
