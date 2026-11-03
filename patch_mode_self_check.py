with open('mode.js', 'r', encoding='utf-8', newline='') as f:
    c = f.read()

assert '\r' not in c, "mode.js must be strictly LF"

target1 = """        // Rerender active mode dashboard when language changes
        if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
            window.TempoI18n.onLanguageChange(() => {
                renderActiveModeHome();
            });
        }"""

replace1 = """        // Rerender active mode dashboard when language changes
        if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
            window.TempoI18n.onLanguageChange(() => {
                renderActiveModeHome();
                const stressCheckScreen = document.getElementById('screen-stress-check');
                if (stressCheckScreen && !stressCheckScreen.classList.contains('hidden')) {
                    if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.render === 'function') {
                        window.TempoSelfCheckWorkspace.render();
                    }
                }
            });
        }"""

assert target1 in c, "target1 not found in mode.js"
c = c.replace(target1, replace1, 1)

target2 = """        const scHomeText = document.getElementById('selfcheck-return-home-text');
        if (scHomeText) {
            if (sourceContext === 'recovery') scHomeText.textContent = 'Return to Recovery Mode';
            else if (sourceContext === 'emergency') scHomeText.textContent = 'Return to Urgent Mode';
            else if (sourceContext === 'unclear') scHomeText.textContent = 'Return to Unclear Mode';
            else scHomeText.textContent = 'Return Home';
        }"""

replace2 = """        const scHomeText = document.getElementById('selfcheck-return-home-text');
        if (scHomeText) {
            const isVi = (window.TempoI18n && typeof window.TempoI18n.getLanguage === 'function') ? (window.TempoI18n.getLanguage() === 'vi') : false;
            if (sourceContext === 'recovery') scHomeText.textContent = isVi ? 'Quay lại Chế độ phục hồi' : 'Return to Recovery Mode';
            else if (sourceContext === 'emergency') scHomeText.textContent = isVi ? 'Quay lại Chế độ khẩn cấp' : 'Return to Urgent Mode';
            else if (sourceContext === 'unclear') scHomeText.textContent = isVi ? 'Quay lại Chế độ mơ hồ' : 'Return to Unclear Mode';
            else scHomeText.textContent = isVi ? 'Quay lại trang chủ' : 'Return Home';
        }"""

assert target2 in c, "target2 not found in mode.js"
c = c.replace(target2, replace2, 1)

assert '\r' not in c, "mode.js must retain strictly LF line endings"

with open('mode.js', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

print("mode.js patched successfully!")
