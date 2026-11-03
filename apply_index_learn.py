import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update mobile learn tab button
old_mobile_tab = '''                        <button type="button" role="tab" data-community-tab="learn" onclick="window.TempoCommunity.selectTab('learn')" 
                                class="community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Learn
                        </button>'''

new_mobile_tab = '''                        <button type="button" role="tab" data-community-tab="learn" onclick="window.TempoCommunity.selectTab('learn')" 
                                class="community-mobile-tab-btn px-3.5 py-1.5 rounded-full text-xs font-semibold transition whitespace-nowrap bg-white text-[#5A5550] border border-[#EAE4DF]">
                            Kiến thức
                        </button>'''

# 2. Update desktop learn tab button
old_desktop_tab = '''                        <button type="button" role="tab" data-community-tab="learn" onclick="window.TempoCommunity.selectTab('learn')" 
                                class="community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Learn
                        </button>'''

new_desktop_tab = '''                        <button type="button" role="tab" data-community-tab="learn" onclick="window.TempoCommunity.selectTab('learn')" 
                                class="community-nav-item w-full flex items-center px-4 py-2.5 rounded-2xl text-[14px] sm:text-[15px] font-bold transition text-left cursor-pointer text-[#5A5550] hover:text-[#DE8662]">
                            Kiến thức
                        </button>'''

# 3. Update learn search input placeholder
old_search_input = '''                           <input type="text" id="learn-search-input" 
                                   oninput="window.TempoCommunity.handleLearnSearch(this.value)"
                                   placeholder="Search..." '''

new_search_input = '''                           <input type="text" id="learn-search-input" 
                                   oninput="window.TempoCommunity.handleLearnSearch(this.value)"
                                   placeholder="Tìm kiếm..." '''

# 4. Bump cache versions
old_i18n = '<script src="i18n.js?v=20261101.27"></script>'
new_i18n = '<script src="i18n.js?v=20261101.28"></script>'

old_comm = '<script src="communityPosts.js?v=20261101.7"></script>'
new_comm = '<script src="communityPosts.js?v=20261101.8"></script>'

old_ls = '<script src="learnSolve.js"></script>'
new_ls = '<script src="learnSolve.js?v=20261101.1"></script>'

assert old_mobile_tab in content, "old_mobile_tab not found"
assert old_desktop_tab in content, "old_desktop_tab not found"
assert old_search_input in content, "old_search_input not found"
assert old_i18n in content, "old_i18n not found"
assert old_comm in content, "old_comm not found"
assert old_ls in content, "old_ls not found"

content = content.replace(old_mobile_tab, new_mobile_tab, 1)
content = content.replace(old_desktop_tab, new_desktop_tab, 1)
content = content.replace(old_search_input, new_search_input, 1)
content = content.replace(old_i18n, new_i18n, 1)
content = content.replace(old_comm, new_comm, 1)
content = content.replace(old_ls, new_ls, 1)

# Preserve LF strictly
content_lf = content.replace('\r\n', '\n')
with open('index.html', 'wb') as f:
    f.write(content_lf.encode('utf-8'))

print("Updated index.html successfully with LF line endings.")
