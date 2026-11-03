import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('toolNotes.js', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.findall(r'(?:TempoApp\.navigateTo|TempoMode\.navigateToActiveDashboard|TempoMode\.returnToSourceContext|Quay lại|Return)[\s\S]{0,100}', text)
print(f"Matches in toolNotes.js: {len(matches)}")
for m in matches[:10]:
    print("---", m.strip().replace('\n', ' '))
