import sys
sys.stdout.reconfigure(encoding='utf-8')

for fname in ['recoverySelfCheck.js', 'mode.js']:
    with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f, 1):
            if any(k in line for k in ['YOUR DAILY CHECK-IN', "Today’s self-check", "Today's self-check", "how are you today", "You checked on"]):
                print(f'{fname}:{idx}: {line.strip()[:120]}')
