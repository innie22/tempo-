import re

with open('urmodeFlow.js', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.findall(r'.{0,40}(?:STEP 3|adjust_propose|Proposal).{0,40}', text)
for m in matches[:10]:
    print(m.strip())
