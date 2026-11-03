import re

with open('app.js', 'rb') as f:
    content = f.read().decode('utf-8')

# Ensure LF
content = content.replace('\r\n', '\n')

# 1. Update navigateTo redirects and add community handler
old_community_section = r'''        // Direct Messages route alias
        if \(tabId === 'direct-messages'\) \{
            navigateTo\('posts', 'messages'\);
            return;
        \}

        // Tempo Posts / Direct Messages \(Community modal experience\)
        if \(tabId === 'posts'\) \{
[\s\S]*?            window\.location\.hash = section === 'messages' \? '#posts\?section=messages' : '#posts';
            return;
        \}'''

new_community_section = '''        // Learn & Solve / Hub aliases migrated to Community
        if (tabId === 'hub' || tabId === 'learn-solve' || tabId === 'learn') {
            navigateTo('community', 'learn');
            return;
        }
        if (tabId === 'solve' || tabId === 'tips') {
            navigateTo('community', 'tips');
            return;
        }

        // Direct Messages route alias
        if (tabId === 'direct-messages') {
            navigateTo('community', 'messages');
            return;
        }

        // Legacy posts route alias
        if (tabId === 'posts') {
            const targetTab = (subTab === 'messages') ? 'messages' : 'posts';
            navigateTo('community', targetTab);
            return;
        }

        // Tempo Community Unified Screen
        if (tabId === 'community') {
            const targetTab = subTab || 'announcement';
            currentTab = 'community';
            window.location.hash = (targetTab === 'announcement') ? '#community' : `#community?tab=${targetTab}`;

            // Hide all screen containers
            document.querySelectorAll('.screen-container').forEach(screen => {
                screen.classList.add('hidden');
            });

            // Show community screen
            const targetScreen = document.getElementById('screen-community');
            if (targetScreen) targetScreen.classList.remove('hidden');

            // Select active category in TempoCommunity controller
            if (window.TempoCommunity && typeof window.TempoCommunity.selectTab === 'function') {
                window.TempoCommunity.selectTab(targetTab, false);
            }

            // Reset background color
            document.body.style.backgroundColor = '';
            const mainEl = document.querySelector('main');
            if (mainEl) mainEl.style.backgroundColor = '';

            // Update desktop nav
            document.querySelectorAll('header nav a[data-nav]').forEach(el => {
                const isMatch = el.dataset.nav === 'community';
                if (isMatch) {
                    el.classList.add('text-[#FF6B2C]', 'font-semibold', 'bg-[#FFE9DC]');
                    el.classList.remove('text-[#6F6B68]', 'hover:text-[#202124]', 'hover:bg-[#F3F1EF]', 'text-gray-600', 'hover:text-gray-900', 'text-emerald-800', 'bg-emerald-50');
                } else {
                    el.classList.remove('text-[#FF6B2C]', 'font-semibold', 'bg-[#FFE9DC]', 'text-emerald-800', 'bg-emerald-50');
                    el.classList.add('text-[#6F6B68]', 'hover:text-[#202124]', 'hover:bg-[#F3F1EF]');
                }
            });

            // Update mobile bottom nav
            document.querySelectorAll('nav.md\\:hidden a[data-nav]').forEach(el => {
                const isMatch = el.dataset.nav === 'community';
                if (isMatch) {
                    el.classList.add('text-[#FF6B2C]', 'font-semibold');
                    el.classList.remove('text-gray-500');
                } else {
                    el.classList.remove('text-[#FF6B2C]', 'font-semibold');
                    el.classList.add('text-gray-500');
                }
            });

            window.scrollTo({ top: 0, behavior: 'smooth' });
            return;
        }'''

if re.search(old_community_section, content):
    content = re.sub(old_community_section, new_community_section, content, count=1)
    print("Successfully patched navigateTo in app.js")
else:
    print("Warning: old_community_section regex not found, checking alternatives...")

# 2. Update handleHashChange
old_hash_section = r'''        if \(rawHash\.startsWith\('personal-space'\)\) \{
            const queryPart = rawHash\.includes\('\?'\) \? rawHash\.split\('\?'\)\[1\] : '';
            const params = new URLSearchParams\(queryPart\);
            const subTab = params\.get\('tab'\) \|\| 'saved';
            navigateTo\('personal-space', subTab\);
        \} else if \(rawHash\.startsWith\('posts'\)\) \{
            const queryPart = rawHash\.includes\('\?'\) \? rawHash\.split\('\?'\)\[1\] : '';
            const params = new URLSearchParams\(queryPart\);
            const section = params\.get\('section'\) \|\| 'feed';
            navigateTo\('posts', section\);
        \} else if \(rawHash\.startsWith\('direct-messages'\)\) \{
            navigateTo\('posts', 'messages'\);'''

new_hash_section = '''        if (rawHash.startsWith('community')) {
            const queryPart = rawHash.includes('?') ? rawHash.split('?')[1] : '';
            const params = new URLSearchParams(queryPart);
            const subTab = params.get('tab') || 'announcement';
            navigateTo('community', subTab);
        } else if (rawHash.startsWith('personal-space')) {
            const queryPart = rawHash.includes('?') ? rawHash.split('?')[1] : '';
            const params = new URLSearchParams(queryPart);
            const subTab = params.get('tab') || 'saved';
            navigateTo('personal-space', subTab);
        } else if (rawHash.startsWith('posts')) {
            const queryPart = rawHash.includes('?') ? rawHash.split('?')[1] : '';
            const params = new URLSearchParams(queryPart);
            const section = params.get('section') || 'feed';
            const targetTab = (section === 'messages') ? 'messages' : 'posts';
            navigateTo('community', targetTab);
        } else if (rawHash.startsWith('direct-messages')) {
            navigateTo('community', 'messages');
        } else if (rawHash === 'learn' || rawHash.startsWith('learn?') || rawHash === 'learn-solve' || rawHash === 'hub') {
            navigateTo('community', 'learn');
        } else if (rawHash === 'solve' || rawHash.startsWith('solve?') || rawHash === 'tips') {
            navigateTo('community', 'tips');'''

if re.search(old_hash_section, content):
    content = re.sub(old_hash_section, new_hash_section, content, count=1)
    print("Successfully patched handleHashChange in app.js")
else:
    print("Warning: old_hash_section regex not found, checking alternatives...")

# 3. Add getCurrentRole to return object
old_return = '        getCurrentTab: () => currentTab,'
new_return = '''        getCurrentTab: () => currentTab,
        getCurrentRole: () => currentRole,'''

if old_return in content:
    content = content.replace(old_return, new_return, 1)
    print("Successfully added getCurrentRole to TempoApp return object.")

# Write back with LF
with open('app.js', 'wb') as f:
    f.write(content.encode('utf-8'))

print("Completed updating app.js with LF line endings.")
