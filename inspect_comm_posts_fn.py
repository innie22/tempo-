import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('communityPosts.js', 'r', encoding='utf-8', newline='') as f:
    text = f.read()

idx = text.find('function renderCommunityPosts(')
if idx == -1:
    idx = text.find('renderCommunityPosts')
print("renderCommunityPosts at", idx)
print(text[idx:idx+2500])
