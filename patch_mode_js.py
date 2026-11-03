with open('mode.js', 'rb') as f:
    content = f.read().decode('utf-8')

content = content.replace('\r\n', '\n')

# 1. Update renderLearnSolveCardHTML
content = content.replace(
    "onclick=\"if (window.TempoApp) { window.TempoApp.navigateTo('learn'); } else { window.location.hash = '#learn'; }\"",
    "onclick=\"if (window.TempoApp) { window.TempoApp.navigateTo('community', 'tips'); } else { window.location.hash = '#community?tab=tips'; }\""
)

# 2. Update See all posts button in Entry Home
content = content.replace(
    "onclick=\"if (window.TempoCommunity && window.TempoCommunity.openCommunityModal) { window.TempoCommunity.openCommunityModal(); } else if (window.TempoApp) { window.TempoApp.navigateTo('posts'); }\"",
    "onclick=\"if (window.TempoApp) { window.TempoApp.navigateTo('community', 'posts'); } else if (window.TempoCommunity) { window.TempoCommunity.selectTab('posts'); }\""
)

# 3. Update See all posts in emergency mode
content = content.replace(
    "onclick=\"if (window.TempoCommunity && typeof window.TempoCommunity.openCommunityModal === 'function') { window.TempoCommunity.openCommunityModal(); } else if (window.TempoApp) { window.TempoApp.navigateTo('posts'); }\"",
    "onclick=\"if (window.TempoApp) { window.TempoApp.navigateTo('community', 'posts'); } else if (window.TempoCommunity) { window.TempoCommunity.selectTab('posts'); }\""
)

with open('mode.js', 'wb') as f:
    f.write(content.encode('utf-8'))

print("Successfully updated mode.js with LF line endings.")
