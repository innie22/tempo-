import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('recoverySetup.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'([^\n]*TempoRecoverySelfCheck[^\n]*)', text)
for m in set(m.group(1).strip() for m in matches):
    print(m)
