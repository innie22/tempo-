import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('communityPosts.js', 'r', encoding='utf-8', newline='') as f:
    text = f.read()

idx = text.find('INITIAL_POSTS')
idx2 = text.find('// Reference 2:', idx)
print(text[idx:idx2])
