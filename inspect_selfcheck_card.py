import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function renderSelfCheckCard(')
end = text.find('function renderRecoverySupportRowHTML(', idx)
print(f"renderSelfCheckCard length: {end - idx}")

sc_code = text[idx:end]
with open('scratch/rmode_selfcheck_dump.js', 'w', encoding='utf-8') as f_out:
    f_out.write(sc_code)

print("Buttons with onclick in SelfCheckCard:")
for m in re.finditer(r'<button[^>]*onclick="([^"]*)"[^>]*>([\s\S]*?)<\/button>', sc_code):
    onclick = m.group(1)
    text_content = re.sub(r'\s+', ' ', m.group(2)).strip()
    print(f"  - Onclick: {onclick[:70]:70s} | Text: {text_content[:40]}")
