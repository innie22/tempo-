import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('communityPosts.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines, 1):
    if 'isViLocale' in l or 'onLanguageChange' in l:
        print(f"{i}: {l.strip()}")
