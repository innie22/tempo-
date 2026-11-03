import glob
import sys

sys.stdout.reconfigure(encoding='utf-8')

for f in glob.glob('*.js') + glob.glob('*.html'):
    content = open(f, encoding='utf-8').read()
    for idx, line in enumerate(content.splitlines()):
        if 'full check' in line.lower() or 'full-check' in line.lower():
            print(f'{f}:{idx+1}: {line.strip()[:100]}')
