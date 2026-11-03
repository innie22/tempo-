import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function renderRecoveryCommunityCard(')
end = text.find('function renderRecoveryEnjoyToolsSection(', idx)
if end == -1:
    end = text.find('function renderRecoveryTodaySection(', idx)
if end == -1:
    end = idx + 4000

print(f"renderRecoveryCommunityCard length: {end - idx}")
comm_code = text[idx:end]
with open('scratch/rmode_comm_dump.js', 'w', encoding='utf-8') as f_out:
    f_out.write(comm_code)

print("Buttons with onclick in Community Card:")
for m in re.finditer(r'<button[^>]*onclick="([^"]*)"[^>]*>([\s\S]*?)<\/button>', comm_code):
    onclick = m.group(1)
    text_content = re.sub(r'\s+', ' ', m.group(2)).strip()
    print(f"  - Onclick: {onclick[:70]:70s} | Text: {text_content[:40]}")
