import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('communityPosts.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

target1 = """                    <p class="text-xs font-bold text-[#5A5550]">No community posts yet</p>\r\n                    <p class="text-[10.5px] text-[#8E8A85] leading-relaxed">Be the first to share with your peers in the community.</p>"""
repl1 = """                    <p class="text-xs font-bold text-[#5A5550]">${isViLocale() ? 'Chưa có bài viết cộng đồng nào' : 'No community posts yet'}</p>\r\n                    <p class="text-[10.5px] text-[#8E8A85] leading-relaxed">${isViLocale() ? 'Hãy là người đầu tiên chia sẻ với bạn bè trong cộng đồng.' : 'Be the first to share with your peers in the community.'}</p>"""
assert target1 in content, "target1 not found in communityPosts.js"
content = content.replace(target1, repl1, 1)

target2 = """                <p class="text-xs font-bold text-[#5A5550]">No community posts yet</p>\r\n                <p class="text-[11px] text-[#8E8A85] leading-relaxed">Be the first to share with your peers in the community.</p>"""
repl2 = """                <p class="text-xs font-bold text-[#5A5550]">${isViLocale() ? 'Chưa có bài viết cộng đồng nào' : 'No community posts yet'}</p>\r\n                <p class="text-[11px] text-[#8E8A85] leading-relaxed">${isViLocale() ? 'Hãy là người đầu tiên chia sẻ với bạn bè trong cộng đồng.' : 'Be the first to share with your peers in the community.'}</p>"""
assert target2 in content, "target2 not found in communityPosts.js"
content = content.replace(target2, repl2, 1)

with open('communityPosts.js', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print("communityPosts.js updated successfully.")
