with open('index.html', 'rb') as f:
    content = f.read().decode('utf-8')

target1 = """                    <button type="button" 
                            onclick="window.TempoMode.setMode('unclear'); if (window.TempoApp) window.TempoApp.navigateTo('today');"
                            class="inline-flex items-center space-x-1.5 px-4 py-2 rounded-full text-xs sm:text-sm font-bold text-[#5B5550] hover:text-[#202124] bg-white hover:bg-stone-50 border border-[#E8D9CF] transition shadow-xs cursor-pointer">
                        <span>←</span>
                        <span>Back to Unclear Mode</span>
                    </button>"""

replacement1 = """                    <button type="button" 
                            onclick="if (window.TempoMode && typeof window.TempoMode.openUcheck === 'function') { window.TempoMode.openUcheck(); } else if (window.TempoApp) { window.TempoApp.navigateTo('ucheck'); }"
                            class="inline-flex items-center space-x-1.5 px-4 py-2 rounded-full text-xs sm:text-sm font-bold text-[#5B5550] hover:text-[#202124] bg-white hover:bg-stone-50 border border-[#E8D9CF] transition shadow-xs cursor-pointer">
                        <span>←</span>
                        <span>Back to Unclear Mode</span>
                    </button>"""

assert target1 in content, "target1 not found in index.html"
content = content.replace(target1, replacement1, 1)

target2 = """                        <button type="button"
                                onclick="window.TempoMode.setMode('unclear'); if (window.TempoUnclearMode) window.TempoUnclearMode.startNewCheckIn();"
                                class="btn-primary px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold shadow-xs transition cursor-pointer">
                            Take Tempo Test
                        </button>"""

replacement2 = """                        <button type="button"
                                onclick="if (window.TempoMode && typeof window.TempoMode.openUcheck === 'function') { window.TempoMode.openUcheck({ startNew: true }); } else if (window.TempoUnclearMode) { window.TempoUnclearMode.startNewCheckIn(); }"
                                class="btn-primary px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold shadow-xs transition cursor-pointer">
                            Take Tempo Test
                        </button>"""

assert target2 in content, "target2 not found in index.html"
content = content.replace(target2, replacement2, 1)

target3 = """                    <button type="button" 
                            onclick="window.TempoMode.setMode('unclear'); if (window.TempoApp) window.TempoApp.navigateTo('today');"
                            class="inline-flex items-center space-x-1.5 px-4 py-2 rounded-full text-xs sm:text-sm font-bold text-[#5B5550] hover:text-[#202124] bg-white hover:bg-stone-50 border border-[#E8D9CF] transition shadow-xs cursor-pointer">
                        <span>←</span>
                        <span>Back to Unclear Mode</span>
                    </button>"""

replacement3 = """                    <button type="button" 
                            onclick="if (window.TempoMode && typeof window.TempoMode.openUcheck === 'function') { window.TempoMode.openUcheck(); } else if (window.TempoApp) { window.TempoApp.navigateTo('ucheck'); }"
                            class="inline-flex items-center space-x-1.5 px-4 py-2 rounded-full text-xs sm:text-sm font-bold text-[#5B5550] hover:text-[#202124] bg-white hover:bg-stone-50 border border-[#E8D9CF] transition shadow-xs cursor-pointer">
                        <span>←</span>
                        <span>Back to Unclear Mode</span>
                    </button>"""

assert target3 in content, "target3 not found in index.html"
content = content.replace(target3, replacement3, 1)

# Ensure strictly lone-LF
content = content.replace('\r\n', '\n').replace('\r', '\n')

with open('index.html', 'wb') as f:
    f.write(content.encode('utf-8'))

print("Successfully updated index.html with lone-LF")
