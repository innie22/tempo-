import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'yourUrgentPlanUpper', text)]
for idx, m in enumerate(matches):
    print(f"=== OCCURRENCE {idx+1} ===")
    print(text[m-300:m+500])
