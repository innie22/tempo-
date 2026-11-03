import glob, sys
sys.stdout.reconfigure(encoding='utf-8')

keywords = ['YOUR DAILY CHECK-IN', "Today's self-check", "how are you today", "streak", "Select level:", "You checked on"]
for fname in sorted(glob.glob('*.js') + glob.glob('*.html')):
    with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    for idx, line in enumerate(lines, 1):
        for kw in keywords:
            if kw.lower() in line.lower():
                print(f'{fname}:{idx}: [{kw}] {line.strip()[:110]}')
