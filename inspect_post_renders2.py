import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('communityPosts.js', 'r', encoding='utf-8', newline='') as f:
    text = f.read()

idx = text.find('function renderTwoColumnPostHTML')
print(text[idx+2500:idx+6000])
