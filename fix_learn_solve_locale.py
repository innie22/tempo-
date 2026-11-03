import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('learnSolve.js', 'r', encoding='utf-8') as f:
    text = f.read()

old_func = '''    function isViLocale() {
        if (window.TempoI18n && typeof window.TempoI18n.getCurrentLanguage === 'function') {
            return window.TempoI18n.getCurrentLanguage() === 'vi';
        }
        return (localStorage.getItem('tempo_locale') || 'vi') === 'vi';
    }'''

new_func = '''    function isViLocale() {
        if (window.TempoI18n && typeof window.TempoI18n.getLanguage === 'function') {
            return window.TempoI18n.getLanguage() === 'vi';
        }
        if (window.TempoI18n && typeof window.TempoI18n.getCurrentLanguage === 'function') {
            return window.TempoI18n.getCurrentLanguage() === 'vi';
        }
        return (localStorage.getItem('tempo_language') || localStorage.getItem('tempo_locale') || 'vi') === 'vi';
    }'''

norm = text.replace('\r\n', '\n')
assert old_func in norm, "old_func not found"
norm = norm.replace(old_func, new_func, 1)

content_crlf = norm.replace('\n', '\r\n')
with open('learnSolve.js', 'wb') as f:
    f.write(content_crlf.encode('utf-8'))

print("Updated isViLocale in learnSolve.js (CRLF).")
