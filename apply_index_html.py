# -*- coding: utf-8 -*-

def update_index_html():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    old_block = """                <a id="nav-link-what-is-tempo" href="#about" onclick="window.TempoApp.navigateTo('about'); return false;" class="text-[#736F68] hover:text-[#FF6B2C] transition whitespace-nowrap">
                    Giới thiệu
                </a>
                <a id="nav-link-check" href="#stress-check" onclick="if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('open'); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('stress-check'); } else { window.location.hash = '#stress-check'; } return false;" class="text-[#736F68] hover:text-[#FF6B2C] transition whitespace-nowrap">
                    Check
                </a>
                <a id="nav-link-plan" href="#plan-workspace" onclick="if (window.TempoMode && typeof window.TempoMode.openPlanWorkspace === 'function') { window.TempoMode.openPlanWorkspace(); } else if (window.TempoApp) { window.TempoApp.navigateTo('plan-workspace'); } return false;" class="text-[#736F68] hover:text-[#FF6B2C] transition whitespace-nowrap">
                    Plan
                </a>"""

    new_block = """                <a id="nav-link-what-is-tempo" data-nav="about" href="#about" onclick="window.TempoApp.navigateTo('about'); return false;" class="text-[#736F68] hover:text-[#FF6B2C] transition whitespace-nowrap">
                    Giới thiệu
                </a>
                <a id="nav-link-check" data-nav="stress-check" href="#stress-check" onclick="if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('open'); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('stress-check'); } else { window.location.hash = '#stress-check'; } return false;" class="text-[#736F68] hover:text-[#FF6B2C] transition whitespace-nowrap">
                    Check
                </a>
                <a id="nav-link-plan" data-nav="plan-workspace" href="#plan-workspace" onclick="if (window.TempoMode && typeof window.TempoMode.openPlanWorkspace === 'function') { window.TempoMode.openPlanWorkspace(); } else if (window.TempoApp) { window.TempoApp.navigateTo('plan-workspace'); } return false;" class="text-[#736F68] hover:text-[#FF6B2C] transition whitespace-nowrap">
                    Plan
                </a>"""

    assert old_block in content, "old_block not found in index.html"
    content = content.replace(old_block, new_block, 1)

    with open('index.html', 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print("index.html updated successfully with LF.")

if __name__ == '__main__':
    update_index_html()
