import re, sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Find community/posts sections
for m in re.finditer(r'([a-zA-Z0-9_]+)\s*:\s*\{', text):
    sec_name = m.group(1)
    if any(k in sec_name.lower() for k in ['communit', 'post', 'feed']):
        print(f"Section: {sec_name} at pos {m.start()}")
