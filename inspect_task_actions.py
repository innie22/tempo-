import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

for fn in ['handleRmodeTaskReschedule', 'promptClearRmodeTask', 'handleRmodeTaskFocus']:
    idx = text.find(f'function {fn}(')
    if idx != -1:
        print(f"=== {fn} ===")
        print(text[idx:idx+800])
    else:
        print(f"{fn} NOT FOUND")
