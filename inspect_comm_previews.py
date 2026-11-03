import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('communityPosts.js', 'r', encoding='utf-8') as f:
    text = f.read()

for fn in ['renderPreviewEmptyStateHTML', 'renderPreviewPostCardHTML', 'getPostTimeAgoDisplay']:
    idx = text.find(f'function {fn}')
    if idx != -1:
        print(f"\n--- {fn} ---")
        print(text[idx:idx+800])
