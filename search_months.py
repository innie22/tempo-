import glob
import sys

sys.stdout.reconfigure(encoding='utf-8')

for f in glob.glob('*.js'):
    content = open(f, encoding='utf-8').read()
    for idx, line in enumerate(content.splitlines()):
        if 'January' in line or 'tháng 1' in line.lower():
            print(f'{f}:{idx+1}: {line.strip()[:100]}')
