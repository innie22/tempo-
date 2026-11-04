import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'yourWorkingPlan', text)]
for m in matches:
    print(text[m-50:m+150])
    print("-"*40)
