import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('focusZone.js', 'r', encoding='utf-8') as f:
    text = f.read()

print("Length of focusZone.js:", len(text))
matches = re.findall(r'(?:exit|close|return|navigateTo|TempoMode)[\s\S]{0,100}', text, re.I)
print("FocusZone exit/return matches:")
for m in matches[:10]:
    print("---", m.strip().replace('\n', ' '))
