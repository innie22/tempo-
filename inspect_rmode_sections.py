import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

funcs = [
    'renderRmodeHeader',
    'renderSelfCheckCard',
    'renderRecoverySupportRowHTML',
    'renderRecoveryNoteCard',
    'renderRecentlyCard',
    'renderRecoveryWorkingPlanSection',
    'renderRecoveryCommunityCard',
    'renderRmodeTaskDetailModalHTML',
    'openChangeModeModal'
]

for fn in funcs:
    idx = text.find(f'function {fn}(')
    if idx == -1:
        print(f"Function {fn} NOT FOUND")
        continue
    # grab first 30 lines
    lines = text[idx:].splitlines()[:35]
    print(f"=== {fn} ===")
    print("\n".join(lines[:20]))
    print("...")
