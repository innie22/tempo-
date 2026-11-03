with open('index.html', 'r', encoding='utf-8', newline='') as f:
    text = f.read()

assert '\r\n' not in text, "index.html has CRLF!"

assert 'i18n.js?v=20261101.14' in text
assert 'urmodeFlow.js?v=20261101.4' in text

text = text.replace('i18n.js?v=20261101.14', 'i18n.js?v=20261101.15')
text = text.replace('urmodeFlow.js?v=20261101.4', 'urmodeFlow.js?v=20261101.5')

assert '\r\n' not in text, "index.html has CRLF after replace!"

with open('index.html', 'w', encoding='utf-8', newline='\n') as f:
    f.write(text)

print("index.html cache versions bumped successfully to v15 / v5!")
