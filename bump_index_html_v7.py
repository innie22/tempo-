import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

assert '\r\n' not in content, "CRLF found in index.html!"

target_i18n = '<script src="i18n.js?v=20261101.6"></script>'
replacement_i18n = '<script src="i18n.js?v=20261101.7"></script>'

target_notes = '<script src="toolNotes.js?v=20261101.1"></script>'
replacement_notes = '<script src="toolNotes.js?v=20261101.2"></script>'

assert target_i18n in content, "target_i18n not found!"
assert target_notes in content, "target_notes not found!"

content = content.replace(target_i18n, replacement_i18n, 1)
content = content.replace(target_notes, replacement_notes, 1)

assert '\r' not in content, "CRLF introduced into index.html!"

with open('index.html', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print(f"Successfully bumped index.html scripts! Total LF lines: {content.count(chr(10))}")
