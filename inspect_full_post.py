import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('communityPosts.js', 'r', encoding='utf-8', newline='') as f:
    text = f.read()

idx = text.find('function renderFullWidthPostHTML')
print(text[idx:idx+2500])
