import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/topics_raw.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re

for line in text.splitlines():
    if 'relatedTool' in line or 'relatedMode' in line:
        print(line.strip())
