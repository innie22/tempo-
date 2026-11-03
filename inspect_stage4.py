import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('recoverySetup.js', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.findall(r'(?:stage4|recoveryNote|warningSigns|supportContacts)[\s\S]{0,100}', text, re.I)
print(f"Stage 4 note matches in recoverySetup.js: {len(matches)}")
for m in matches[:10]:
    print("---", m.strip().replace('\n', ' '))
