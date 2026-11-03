import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
for m in re.finditer(r'data-community-tab="learn"[^>]*>[\s\S]*?<\/button>', text):
    start = max(0, m.start() - 40)
    end = min(len(text), m.end() + 20)
    print("MATCH TAB:\n" + repr(text[start:end]))

for m in re.finditer(r'i18n\.js\?v=[^\n]+', text):
    start = max(0, m.start() - 20)
    end = min(len(text), m.end() + 100)
    print("MATCH SCRIPTS:\n" + repr(text[start:end]))
