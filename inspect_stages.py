import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('recoverySetup.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.finditer(r'function renderStage([A-Za-z0-9_]+)\(', text)
for m in matches:
    print('Stage:', m.group(1))

# Also search for 'hub', 'review', 'adjust'
for m in re.finditer(r'function ([A-Za-z0-9_]*(?:review|adjust|track|manage)[A-Za-z0-9_]*)\(', text, re.I):
    print('Fn:', m.group(1))
