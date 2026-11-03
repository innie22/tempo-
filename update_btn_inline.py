import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('index.html', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

target = """                        <button type="button" id="btn-community-back" onclick="window.TempoCommunity.handleReturnNavigation()" \n                                class="inline-flex items-center space-x-1.5 text-[12px] sm:text-[13px] font-bold text-[#5A5550] hover:text-[#DE8662] transition cursor-pointer"\n                                aria-label="← Về Dashboard" title="← Về Dashboard">\n                            <span class="text-base">←</span>\n                            <span id="community-back-label">Về Dashboard</span>\n                        </button>"""

replacement = """                        <button type="button" id="btn-community-back" onclick="window.TempoCommunity.handleReturnNavigation()" \n                                class="inline-flex items-center space-x-1.5 text-[12px] sm:text-[13px] font-bold text-[#5A5550] hover:text-[#DE8662] transition cursor-pointer"\n                                aria-label="← Về Dashboard" title="← Về Dashboard">\n                            <span class="text-base leading-none">←</span> <span id="community-back-label">Về Dashboard</span>\n                        </button>"""

assert target in content, "target not found in index.html"
content = content.replace(target, replacement, 1)

with open('index.html', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print("index.html updated successfully with single-line spans.")
