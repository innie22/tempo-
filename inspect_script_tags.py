import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines, 1):
    if any(k in l for k in ['i18n.js', 'communityPosts.js']):
        print(f"{i}: {l.strip()}")
