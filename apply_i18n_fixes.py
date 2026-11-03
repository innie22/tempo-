import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

# 1. In vi.common
target_vi_common = '            common: {\r\n                appName: "Tempo",\r\n'
repl_vi_common = '            common: {\r\n                appName: "Tempo",\r\n                returnToDashboard: "Về Dashboard",\r\n                returnToDashboardWithArrow: "← Về Dashboard",\r\n'
assert target_vi_common in content, "target_vi_common not found"
content = content.replace(target_vi_common, repl_vi_common, 1)

# 2. In vi.posts
target_vi_posts = '            posts: {\r\n                title: "Tempo Posts",\r\n'
repl_vi_posts = '            posts: {\r\n                title: "Tempo Posts",\r\n                returnToDashboard: "Về Dashboard",\r\n                returnToDashboardWithArrow: "← Về Dashboard",\r\n'
assert target_vi_posts in content, "target_vi_posts not found"
content = content.replace(target_vi_posts, repl_vi_posts, 1)

# 3. In en.common
target_en_common = '            common: {\r\n                appName: "Tempo",\r\n'
repl_en_common = '            common: {\r\n                appName: "Tempo",\r\n                returnToDashboard: "Return to Dashboard",\r\n                returnToDashboardWithArrow: "← Return to Dashboard",\r\n'
assert target_en_common in content, "target_en_common not found"
content = content.replace(target_en_common, repl_en_common, 1)

# 4. In en.posts
target_en_posts = '            posts: {\r\n                title: "Tempo Posts",\r\n'
repl_en_posts = '            posts: {\r\n                title: "Tempo Posts",\r\n                returnToDashboard: "Return to Dashboard",\r\n                returnToDashboardWithArrow: "← Return to Dashboard",\r\n'
assert target_en_posts in content, "target_en_posts not found"
content = content.replace(target_en_posts, repl_en_posts, 1)

# 5. In updateStaticHtml
target_static = """        const navLinkCommunity = document.getElementById('nav-link-community');\r\n        if (navLinkCommunity) navLinkCommunity.textContent = t('nav.community', {}, currentLang === 'vi' ? 'Cộng đồng' : 'Community');\r\n"""
repl_static = """        const navLinkCommunity = document.getElementById('nav-link-community');\r\n        if (navLinkCommunity) navLinkCommunity.textContent = t('nav.community', {}, currentLang === 'vi' ? 'Cộng đồng' : 'Community');\r\n        const communityBackBtn = document.getElementById('btn-community-back');\r\n        const communityBackLabel = document.getElementById('community-back-label');\r\n        if (communityBackLabel) {\r\n            communityBackLabel.textContent = currentLang === 'vi' ? 'Về Dashboard' : 'Return to Dashboard';\r\n        }\r\n        if (communityBackBtn) {\r\n            const commBackText = currentLang === 'vi' ? '← Về Dashboard' : '← Return to Dashboard';\r\n            communityBackBtn.setAttribute('title', commBackText);\r\n            communityBackBtn.setAttribute('aria-label', commBackText);\r\n        }\r\n"""
assert target_static in content, "target_static not found"
content = content.replace(target_static, repl_static, 1)

with open('i18n.js', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print("i18n.js updated successfully.")
