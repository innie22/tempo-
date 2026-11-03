import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = 'mode.js'

with open(file_path, 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8')

old_block = """        // Link 2: Check (Entry Home & Urmode) vs Plan (Recovery Mode)
        if (checkLink) {
            if (mode === MODES.RECOVERY) {
                checkLink.textContent = 'Plan';
                checkLink.setAttribute('href', '#recovery-working-plan');
                checkLink.setAttribute('title', 'Plan');
                checkLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoApp && typeof window.TempoApp.scrollToRecoveryPlan === 'function') {
                        window.TempoApp.scrollToRecoveryPlan();
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('plan');
                    }
                    return false;
                };
            } else {
                checkLink.textContent = 'Check';
                checkLink.setAttribute('href', '#stress-check');
                checkLink.setAttribute('title', 'Check');
                checkLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                        window.TempoMode.openStrack('open', { sourceContext: mode === MODES.EMERGENCY ? 'emergency' : (mode === MODES.RECOVERY ? 'recovery' : 'entry') });
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('stress-check');
                    }
                    return false;
                };
            }
        }

        // Link 3: Plan (Entry Home) vs Assessment (Urmode & Recovery Mode)
        if (planLink) {
            if (mode === MODES.DEFAULT || !mode || mode === 'default') {
                planLink.textContent = 'Plan';
                planLink.setAttribute('href', '#plan-workspace');
                planLink.setAttribute('title', 'Plan');
                planLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoMode && typeof window.TempoMode.openPlanWorkspace === 'function') {
                        window.TempoMode.openPlanWorkspace();
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('plan-workspace');
                    }
                    return false;
                };
            } else if (mode === MODES.EMERGENCY) {
                planLink.textContent = 'Assessment';
                planLink.setAttribute('href', '#ucheck');
                planLink.setAttribute('title', 'Assessment');
                planLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoMode && typeof window.TempoMode.openUcheck === 'function') {
                        window.TempoMode.openUcheck({ sourceContext: 'emergency' });
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('ucheck');
                    } else {
                        window.location.hash = '#ucheck';
                    }
                    return false;
                };
            } else if (mode === MODES.RECOVERY) {
                planLink.textContent = 'Assessment';
                planLink.setAttribute('href', '#ucheck');
                planLink.setAttribute('title', 'Assessment');
                planLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoMode && typeof window.TempoMode.openUcheck === 'function') {
                        window.TempoMode.openUcheck({ sourceContext: 'recovery' });
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('ucheck');
                    } else {
                        window.location.hash = '#ucheck';
                    }
                    return false;
                };
            } else {
                planLink.textContent = 'Tool';
                planLink.setAttribute('href', '#enjoy-tempo-tools');
                planLink.setAttribute('title', 'Tool');"""

new_block = """        // Link 2: Check (Entry Home & Urmode) vs Plan (Recovery Mode)
        if (checkLink) {
            if (mode === MODES.RECOVERY) {
                checkLink.textContent = 'Kế hoạch';
                checkLink.setAttribute('href', '#recovery-working-plan');
                checkLink.setAttribute('title', 'Kế hoạch');
                checkLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoApp && typeof window.TempoApp.scrollToRecoveryPlan === 'function') {
                        window.TempoApp.scrollToRecoveryPlan();
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('plan');
                    }
                    return false;
                };
            } else {
                checkLink.textContent = 'Tự kiểm tra';
                checkLink.setAttribute('href', '#stress-check');
                checkLink.setAttribute('title', 'Tự kiểm tra');
                checkLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                        window.TempoMode.openStrack('open', { sourceContext: mode === MODES.EMERGENCY ? 'emergency' : (mode === MODES.RECOVERY ? 'recovery' : 'entry') });
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('stress-check');
                    }
                    return false;
                };
            }
        }

        // Link 3: Plan (Entry Home) vs Assessment (Urmode & Recovery Mode)
        if (planLink) {
            if (mode === MODES.DEFAULT || !mode || mode === 'default') {
                planLink.textContent = 'Kế hoạch';
                planLink.setAttribute('href', '#plan-workspace');
                planLink.setAttribute('title', 'Kế hoạch');
                planLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoMode && typeof window.TempoMode.openPlanWorkspace === 'function') {
                        window.TempoMode.openPlanWorkspace();
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('plan-workspace');
                    }
                    return false;
                };
            } else if (mode === MODES.EMERGENCY) {
                planLink.textContent = 'Đánh giá';
                planLink.setAttribute('href', '#ucheck');
                planLink.setAttribute('title', 'Đánh giá');
                planLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoMode && typeof window.TempoMode.openUcheck === 'function') {
                        window.TempoMode.openUcheck({ sourceContext: 'emergency' });
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('ucheck');
                    } else {
                        window.location.hash = '#ucheck';
                    }
                    return false;
                };
            } else if (mode === MODES.RECOVERY) {
                planLink.textContent = 'Đánh giá';
                planLink.setAttribute('href', '#ucheck');
                planLink.setAttribute('title', 'Đánh giá');
                planLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoMode && typeof window.TempoMode.openUcheck === 'function') {
                        window.TempoMode.openUcheck({ sourceContext: 'recovery' });
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('ucheck');
                    } else {
                        window.location.hash = '#ucheck';
                    }
                    return false;
                };
            } else {
                planLink.textContent = 'Công cụ';
                planLink.setAttribute('href', '#enjoy-tempo-tools');
                planLink.setAttribute('title', 'Công cụ');"""

text_norm = text.replace('\r\n', '\n')
assert old_block.replace('\r\n', '\n') in text_norm, "old_block not found in mode.js"
text_norm = text_norm.replace(old_block.replace('\r\n', '\n'), new_block.replace('\r\n', '\n'), 1)

with open(file_path, 'wb') as f:
    f.write(text_norm.encode('utf-8'))

with open(file_path, 'rb') as f:
    final_bytes = f.read()

final_crlf = final_bytes.count(b'\r\n')
final_lone_lf = final_bytes.count(b'\n') - final_crlf
print(f"mode.js updateNavbarForMode updated. Final CRLF: {final_crlf}, lone LF: {final_lone_lf}")
