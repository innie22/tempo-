import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

assert '\r\n' not in content, "CRLF found in index.html!"

t_i18n = '<script src="i18n.js?v=20261101.7"></script>'
r_i18n = '<script src="i18n.js?v=20261101.8"></script>'

t_notes = '<script src="toolNotes.js?v=20261101.2"></script>'
r_notes = '<script src="toolNotes.js?v=20261101.3"></script>'

t_mode = '<script src="mode.js?v=20261101.7"></script>'
r_mode = '<script src="mode.js?v=20261101.8"></script>'

assert t_i18n in content, "t_i18n not found!"
assert t_notes in content, "t_notes not found!"
assert t_mode in content, "t_mode not found!"

content = content.replace(t_i18n, r_i18n, 1)
content = content.replace(t_notes, r_notes, 1)
content = content.replace(t_mode, r_mode, 1)

assert '\r' not in content, "CRLF introduced into index.html!"

with open('index.html', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print(f"Updated index.html successfully! Total LF lines: {content.count(chr(10))}")
