import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

for m in re.finditer(r'.{0,40}\blater\b.{0,40}', text, re.IGNORECASE):
    print(m.group(0).strip())
