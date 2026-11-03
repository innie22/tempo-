import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
for m in re.finditer(r'common\s*:\s*\{([^}]+)\}', text):
    print("Match at", m.start())
    print(m.group(0)[:500])
