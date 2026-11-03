import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines in mode.js: {len(lines)}")
print("--- Lines 1 to 250 of mode.js ---")
print("".join(lines[:250]))
