import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function renderCommunityPreviewsHTML')
print(text[idx+1200:idx+2500])
