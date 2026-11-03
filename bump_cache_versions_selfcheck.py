with open('index.html', 'r', encoding='utf-8', newline='') as f:
    c = f.read()

assert '\r' not in c, "index.html must be strictly LF"

assert 'i18n.js?v=20261101.20' in c, "i18n.js?v=20261101.20 not found"
assert '<script src="selfCheckWorkspace.js"></script>' in c, "selfCheckWorkspace.js not found"
assert 'mode.js?v=20261101.8' in c, "mode.js?v=20261101.8 not found"

c = c.replace('i18n.js?v=20261101.20', 'i18n.js?v=20261101.21', 1)
c = c.replace('<script src="selfCheckWorkspace.js"></script>', '<script src="selfCheckWorkspace.js?v=20261101.1"></script>', 1)
c = c.replace('mode.js?v=20261101.8', 'mode.js?v=20261101.9', 1)

assert '\r' not in c, "index.html must retain strictly LF line endings"

with open('index.html', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

print("index.html cache versions bumped successfully!")
