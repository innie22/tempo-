import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Lines 550 to 850 of mode.js ---")
print("".join(lines[550:850]))
