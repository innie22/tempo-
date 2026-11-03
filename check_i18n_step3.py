import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.findall(r'.{0,40}(?:adjustPlan|Step 3|doThisFirst|upNext|noFixedDeadline).{0,40}', text, re.IGNORECASE)
for m in matches[:10]:
    print(m.strip())
