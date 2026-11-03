import glob
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

terms = ['Tự kiểm tra Tempo', 'selfCheckWorkspace.title']

for fpath in glob.glob('*.js') + glob.glob('*.html'):
    try:
        content = open(fpath, encoding='utf-8').read()
        for idx, line in enumerate(content.splitlines()):
            for t in terms:
                if t in line:
                    print(f'{fpath}:{idx+1}: {line.strip()[:120]}')
    except Exception:
        pass
