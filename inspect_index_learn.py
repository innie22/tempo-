import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's inspect data-community-tab="learn"
import re
for m in re.finditer(r'data-community-tab="learn"[^>]*>([\s\S]*?)<\/button>', text):
    print("Match learn tab button:\n", m.group(0))

for m in re.finditer(r'id="learn-search-input"[^>]*>', text):
    print("Match learn search input:\n", m.group(0))

for m in re.finditer(r'<script\s+src="[^"]*(?:i18n|communityPosts|learnSolve)[^"]*"', text):
    print("Match script tag:\n", m.group(0))
