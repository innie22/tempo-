import re, sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

for m in re.finditer(r'([a-zA-Z0-9_]+)\s*:\s*([\'\"][^\n\r]*?(?:Dashboard|Return|Về|Quay lại)[^\n\r]*?[\'\"])', text, re.IGNORECASE):
    print(f"{m.group(1)}: {m.group(2)}")
