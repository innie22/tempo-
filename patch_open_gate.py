import sys

with open('recoverySetup.js', 'rb') as f:
    raw = f.read()

crlf = raw.count(b'\r\n')
lf = raw.count(b'\n') - crlf
print(f"recoverySetup.js line endings: CRLF={crlf}, lone-LF={lf}")

content = raw.decode('utf-8')

target = """    function open(stage = null, options = {}) {
        if (!window.TempoAuth || !window.TempoAuth.getCurrentUser()) {
            if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                window.TempoMode.openStrack('setup', { stage });
            }
            return;
        }
        ensureModalMounted();"""

replacement = """    function open(stage = null, options = {}) {
        ensureModalMounted();"""

if target not in content:
    print("ERROR: Target not found in recoverySetup.js!")
    sys.exit(1)

content = content.replace(target, replacement, 1)
content = content.replace('\r\n', '\n')

with open('recoverySetup.js', 'wb') as f:
    f.write(content.encode('utf-8'))

with open('recoverySetup.js', 'rb') as f:
    new_raw = f.read()

new_crlf = new_raw.count(b'\r\n')
new_lf = new_raw.count(b'\n') - new_crlf
print(f"Updated recoverySetup.js line endings: CRLF={new_crlf}, lone-LF={new_lf}")
