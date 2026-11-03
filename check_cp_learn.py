import sys, re

sys.stdout.reconfigure(encoding='utf-8')

with open('communityPosts.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update updateCommunitySidebar learn tab
old_sidebar_tab = '''            tips: 'Tips',
            learn: isVi ? 'Bài viết' : 'Posts',''' # wait let's check exact text

# Let's inspect updateCommunitySidebar in communityPosts.js
with open('communityPosts.js', 'r', encoding='utf-8') as f:
    for line in f:
        if 'learn:' in line:
            print("Found in communityPosts.js:", line.strip())
