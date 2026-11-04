# -*- coding: utf-8 -*-

def fix_mode_js():
    with open('mode.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # The issue was:
    #             planLink.onclick = ...;
    #         }
    #     }
    #
    #
    #         // Shared navigation rendering condition:
    #         ...
    #     }
    # Notice the duplicate } } before // Shared navigation rendering condition

    old_snippet = """            planLink.onclick = function(e) {
                if (e && e.preventDefault) e.preventDefault();
                if (window.TempoMode && typeof window.TempoMode.openPlanWorkspace === 'function') {
                    window.TempoMode.openPlanWorkspace();
                } else if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.open === 'function') {
                    window.TempoPlanWorkspace.open();
                } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                    window.TempoApp.navigateTo('plan-workspace');
                } else {
                    window.location.hash = '#plan-workspace';
                }
                return false;
            };
        }
    }


        // Shared navigation rendering condition:"""

    new_snippet = """            planLink.onclick = function(e) {
                if (e && e.preventDefault) e.preventDefault();
                if (window.TempoMode && typeof window.TempoMode.openPlanWorkspace === 'function') {
                    window.TempoMode.openPlanWorkspace();
                } else if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.open === 'function') {
                    window.TempoPlanWorkspace.open();
                } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                    window.TempoApp.navigateTo('plan-workspace');
                } else {
                    window.location.hash = '#plan-workspace';
                }
                return false;
            };
        }

        // Shared navigation rendering condition:"""

    assert old_snippet in content, "old_snippet not found"
    content = content.replace(old_snippet, new_snippet, 1)

    with open('mode.js', 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print("Fixed extra closing brace in mode.js")

if __name__ == '__main__':
    fix_mode_js()
