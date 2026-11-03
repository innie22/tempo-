import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Lines 6970 to 7050 of mode.js ---")
print("".join(lines[6970:7050]))
