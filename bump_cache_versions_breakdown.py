with open('index.html', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

assert '\r' not in content, "index.html must be strictly LF"

assert 'i18n.js?v=20261101.19' in content, "i18n.js?v=20261101.19 not found"
assert 'urmodeFlow.js?v=20261101.9' in content, "urmodeFlow.js?v=20261101.9 not found"

content = content.replace('i18n.js?v=20261101.19', 'i18n.js?v=20261101.20', 1)
content = content.replace('urmodeFlow.js?v=20261101.9', 'urmodeFlow.js?v=20261101.10', 1)

assert '\r' not in content, "index.html must retain strictly LF line endings"

with open('index.html', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print("index.html cache versions bumped successfully to .20 and .10!")
