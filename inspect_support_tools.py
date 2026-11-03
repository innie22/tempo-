import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

for fn in ['renderQuickReliefCardHTML', 'renderFocusNowCardHTML']:
    idx = text.find(f'function {fn}(')
    if idx == -1:
        print(f"{fn} NOT FOUND")
        continue
    lines = text[idx:].splitlines()[:35]
    print(f"=== {fn} ===")
    print("\n".join(lines[:25]))
