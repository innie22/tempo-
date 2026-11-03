import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('communityPosts.js', 'r', encoding='utf-8') as f:
    text = f.read()

assert 'function updateReturnButton()' in text
assert 'function handleReturnNavigation()' in text
print("Found updateReturnButton and handleReturnNavigation in communityPosts.js")

with open('i18n.js', 'r', encoding='utf-8') as f:
    text_i18n = f.read()

assert 'function updateStaticHtml()' in text_i18n
print("Found updateStaticHtml in i18n.js")

with open('index.html', 'r', encoding='utf-8') as f:
    text_html = f.read()

assert 'id="btn-community-back"' in text_html
assert 'id="community-back-label"' in text_html
print("Found btn-community-back in index.html")
