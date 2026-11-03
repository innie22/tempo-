import glob, os, sys
sys.stdout.reconfigure(encoding='utf-8')

keywords = ['My Recovery Notice', 'Things you wanted to remember', 'Edit note', 'RECOVERY NOTICE', 'Recovery Notice']
for fname in sorted(glob.glob('*.js') + glob.glob('*.html')):
    with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    for idx, line in enumerate(lines, 1):
        for kw in keywords:
            if kw.lower() in line.lower():
                print(f'{fname}:{idx}: [{kw}] {line.strip()[:100]}')
