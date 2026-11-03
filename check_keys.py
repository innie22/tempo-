import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

for lang in ['vi', 'en']:
    pos = text.find(f'{lang}: {{')
    ws_pos = text.find('workspace: {', pos)
    end_ws = text.find('sos: {', ws_pos)
    block = text[ws_pos:end_ws]
    print(f'=== {lang} ===')
    for line in block.splitlines():
        if any(k in line for k in ['yourTaskForNow', 'taskForNow', 'doThisFirst', 'focusNow', 'laterBtn', 'duePrefix']):
            print(line.strip())
