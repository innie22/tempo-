import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Search for profile or settings in index.html
print("Matches in index.html for profile / settings / user:")
for m in re.finditer(r'(?:profile|settings|account|user-menu)[\w-]*', text, re.I):
    start = max(0, m.start() - 30)
    end = min(len(text), m.end() + 60)
    print("---", text[start:end].replace('\n', ' '))
