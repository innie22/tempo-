import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Lines 850 to 1050 of mode.js ---")
print("".join(lines[850:1050]))
