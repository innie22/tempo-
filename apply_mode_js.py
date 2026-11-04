# -*- coding: utf-8 -*-
import sys

def update_mode_js():
    with open('mode.js', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    start_idx = None
    end_idx = None
    for i, l in enumerate(lines):
        if 'function updateNavbarForMode(activeMode) {' in l:
            start_idx = i
        if start_idx is not None and i > start_idx and '// Shared navigation rendering condition:' in l:
            end_idx = i - 1
            break

    assert start_idx is not None and end_idx is not None, "Could not locate updateNavbarForMode"

    new_fn = [
        "    function updateNavbarForMode(activeMode) {\n",
        "        let mode = activeMode !== undefined ? activeMode : getMode();\n",
        "        if (isUCheckActiveView()) {\n",
        "            mode = MODES.UNCLEAR;\n",
        "        }\n",
        "\n",
        "        const checkLink = document.getElementById('nav-link-check');\n",
        "        const planLink = document.getElementById('nav-link-plan');\n",
        "        const isVi = isViLocale();\n",
        "\n",
        "        // Link 2: Check (Self-check / Strack) consistently across all modes\n",
        "        if (checkLink) {\n",
        "            const label = window.t ? window.t('nav.check', {}, 'Check') : 'Check';\n",
        "            checkLink.textContent = label;\n",
        "            checkLink.setAttribute('href', '#stress-check');\n",
        "            checkLink.setAttribute('title', label);\n",
        "            checkLink.onclick = function(e) {\n",
        "                if (e && e.preventDefault) e.preventDefault();\n",
        "                const srcCtx = mode === MODES.EMERGENCY ? 'emergency' : (mode === MODES.RECOVERY ? 'recovery' : (sourceContext || 'entry'));\n",
        "                if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {\n",
        "                    window.TempoMode.openStrack('open', { sourceContext: srcCtx });\n",
        "                } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {\n",
        "                    window.TempoApp.navigateTo('stress-check');\n",
        "                } else {\n",
        "                    window.location.hash = '#stress-check';\n",
        "                }\n",
        "                return false;\n",
        "            };\n",
        "        }\n",
        "\n",
        "        // Link 3: Plan (Standalone Working Plan tool view) consistently across ALL modes (including URmode & Recovery Mode)\n",
        "        if (planLink) {\n",
        "            const label = window.t ? window.t('nav.plan', {}, 'Plan') : 'Plan';\n",
        "            planLink.textContent = label;\n",
        "            planLink.setAttribute('href', '#plan-workspace');\n",
        "            planLink.setAttribute('title', label);\n",
        "            planLink.onclick = function(e) {\n",
        "                if (e && e.preventDefault) e.preventDefault();\n",
        "                if (window.TempoMode && typeof window.TempoMode.openPlanWorkspace === 'function') {\n",
        "                    window.TempoMode.openPlanWorkspace();\n",
        "                } else if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.open === 'function') {\n",
        "                    window.TempoPlanWorkspace.open();\n",
        "                } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {\n",
        "                    window.TempoApp.navigateTo('plan-workspace');\n",
        "                } else {\n",
        "                    window.location.hash = '#plan-workspace';\n",
        "                }\n",
        "                return false;\n",
        "            };\n",
        "        }\n",
        "    }\n",
        "\n"
    ]

    lines[start_idx:end_idx] = new_fn

    full_text = "".join(lines)

    # Guard calls to TempoPlanWorkspace.render in mode.js
    # so they don't prematurely render into hidden containers
    old_call = """        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
            window.TempoPlanWorkspace.render();
        }"""
    guarded_call = """        const wsPlanScreen = document.getElementById('screen-plan-workspace');
        if (wsPlanScreen && !wsPlanScreen.classList.contains('hidden') && window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
            window.TempoPlanWorkspace.render();
        }"""

    full_text = full_text.replace(old_call, guarded_call)

    with open('mode.js', 'w', encoding='utf-8', newline='\n') as f:
        f.write(full_text)
    print("mode.js updated successfully with LF.")

if __name__ == '__main__':
    update_mode_js()
