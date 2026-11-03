import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

assert 'i18n.js?v=20261101.22' in content
content = content.replace('i18n.js?v=20261101.22', 'i18n.js?v=20261101.23', 1)

assert 'communityPosts.js?v=20261101.2' in content
content = content.replace('communityPosts.js?v=20261101.2', 'communityPosts.js?v=20261101.3', 1)

assert 'mode.js?v=20261101.9' in content
content = content.replace('mode.js?v=20261101.9', 'mode.js?v=20261101.10', 1)

with open('index.html', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print("index.html versions bumped successfully.")
