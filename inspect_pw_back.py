import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('planWorkspace.js', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.findall(r'(?:return|back|navigate)[\s\S]{0,120}', text, re.I)
print(f"Matches for return/back in planWorkspace.js: {len(matches)}")
for m in matches[:10]:
    print("---", m.strip().replace('\n', ' '))
