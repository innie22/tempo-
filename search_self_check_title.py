import glob
import sys

sys.stdout.reconfigure(encoding='utf-8')

terms = ['Tự kiểm tra Tempo', 'selfCheckWorkspace.title', 'Tempo Self-check']
files = ['i18n.js', 'selfCheckWorkspace.js', 'mode.js', 'index.html']

for fpath in files:
    content = open(fpath, encoding='utf-8').read()
    for idx, line in enumerate(content.splitlines()):
        for t in terms:
            if t in line:
                print(f'{fpath}:{idx+1}: {line.strip()[:120]}')
