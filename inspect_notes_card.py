import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function renderEmodeCreateNotesCard(')
end = text.find('function renderRecoveryNoteCard(', idx)
if end == -1:
    end = idx + 4000
print(f"renderEmodeCreateNotesCard length: {end - idx}")

note_code = text[idx:end]
with open('scratch/rmode_note_dump.js', 'w', encoding='utf-8') as f_out:
    f_out.write(note_code)

print("Buttons with onclick in Notes Card:")
for m in re.finditer(r'<button[^>]*onclick="([^"]*)"[^>]*>([\s\S]*?)<\/button>', note_code):
    onclick = m.group(1)
    text_content = re.sub(r'\s+', ' ', m.group(2)).strip()
    print(f"  - Onclick: {onclick[:70]:70s} | Text: {text_content[:40]}")
