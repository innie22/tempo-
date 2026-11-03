import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Lines 2610 to 2660 of mode.js ---")
print("".join(lines[2610:2660]))

print("--- Lines 6920 to 6975 of mode.js ---")
print("".join(lines[6920:6975]))
