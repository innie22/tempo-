import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('recoverySetup.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'function renderStageAdjustReview' in line or 'function executeAdjustSetupConfirm' in line:
        print(f"=== Line {i+1} ===")
        print(''.join(lines[i:i+60]))
