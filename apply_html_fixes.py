import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

# 1. Update Return Button
old_btn = """                        <button type="button" id="btn-community-back" onclick="window.TempoCommunity.handleReturnNavigation()" \n                                class="inline-flex items-center space-x-1.5 text-[12px] sm:text-[13px] font-bold text-[#5A5550] hover:text-[#DE8662] transition cursor-pointer">\n                            <span class="text-base">←</span>\n                            <span id="community-back-label">Return Home</span>\n                        </button>"""
new_btn = """                        <button type="button" id="btn-community-back" onclick="window.TempoCommunity.handleReturnNavigation()" \n                                class="inline-flex items-center space-x-1.5 text-[12px] sm:text-[13px] font-bold text-[#5A5550] hover:text-[#DE8662] transition cursor-pointer"\n                                aria-label="← Về Dashboard" title="← Về Dashboard">\n                            <span class="text-base">←</span>\n                            <span id="community-back-label">Về Dashboard</span>\n                        </button>"""

assert old_btn in content, "old_btn not found in index.html"
content = content.replace(old_btn, new_btn, 1)

# 2. Bump script versions
assert 'i18n.js?v=20261101.21' in content, "i18n.js?v=20261101.21 not found"
content = content.replace('i18n.js?v=20261101.21', 'i18n.js?v=20261101.22', 1)

assert 'communityPosts.js?v=20261101.1' in content, "communityPosts.js?v=20261101.1 not found"
content = content.replace('communityPosts.js?v=20261101.1', 'communityPosts.js?v=20261101.2', 1)

with open('index.html', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print("index.html updated successfully.")
