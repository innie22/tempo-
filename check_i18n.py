import sys
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8') as f:
    text = f.read()

for m in re.finditer(r'priorityReview', text):
    start = max(0, m.start() - 50)
    end = min(len(text), m.end() + 200)
    print("--- MATCH ---")
    print(text[start:end])
