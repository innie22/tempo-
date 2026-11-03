import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update tips search input placeholder
old_tips_input = '''                            <input type="text" id="tips-search-input" 
                                   oninput="window.TempoCommunity.handleTipsSearch(this.value)"
                                   placeholder="Search..." 
                                   class="w-full bg-transparent border-none text-[13px] text-[#2D2A26] placeholder-[#8E8A85] focus:outline-none p-0 leading-normal">'''

new_tips_input = '''                            <input type="text" id="tips-search-input" 
                                   oninput="window.TempoCommunity.handleTipsSearch(this.value)"
                                   placeholder="Tìm kiếm..." 
                                   class="w-full bg-transparent border-none text-[13px] text-[#2D2A26] placeholder-[#8E8A85] focus:outline-none p-0 leading-normal">'''

# 2. Update script versions
old_scripts = '''    <script src="i18n.js?v=20261101.25"></script>
    <script src="auth.js?v=20261031.1"></script>
    <script src="volunteer.js"></script>

    <!-- Core App Controllers -->
    <script src="data.js"></script>
    <script src="triage.js"></script>
    <script src="stress.js"></script>
    <script src="routine.js"></script>
    <script src="knowledge.js"></script>
    <script src="support.js"></script>
    <script src="admin.js"></script>
    <script src="emergencySupport.js"></script>
    <script src="communityPosts.js?v=20261101.5"></script>'''

new_scripts = '''    <script src="i18n.js?v=20261101.26"></script>
    <script src="auth.js?v=20261031.1"></script>
    <script src="volunteer.js"></script>

    <!-- Core App Controllers -->
    <script src="data.js"></script>
    <script src="triage.js"></script>
    <script src="stress.js"></script>
    <script src="routine.js"></script>
    <script src="knowledge.js"></script>
    <script src="support.js"></script>
    <script src="admin.js"></script>
    <script src="emergencySupport.js"></script>
    <script src="communityPosts.js?v=20261101.6"></script>'''

assert old_tips_input in content, "old_tips_input not found"
assert old_scripts in content, "old_scripts not found"

content = content.replace(old_tips_input, new_tips_input)
content = content.replace(old_scripts, new_scripts)

# Strictly preserve LF line endings (0 CRLFs)
content_lf = content.replace('\r\n', '\n')

with open('index.html', 'wb') as f:
    f.write(content_lf.encode('utf-8'))

print("index.html updated successfully with tips search placeholder (strict LF).")
