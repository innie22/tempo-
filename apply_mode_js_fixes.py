import sys

with open('mode.js', 'rb') as f:
    content = f.read().decode('utf-8')

# Ensure LF line endings for mode.js
content = content.replace('\r\n', '\n')

# 1. Update getRmodeTodayDateStr
old_rmode_date = """    function getRmodeTodayDateStr() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }"""

new_rmode_date = """    function getRmodeTodayDateStr() {
        return getLocalTodayISO();
    }"""

if old_rmode_date in content:
    content = content.replace(old_rmode_date, new_rmode_date)
    print("1. Replaced getRmodeTodayDateStr")
else:
    print("WARNING: old_rmode_date not found")

# 2. In line 2178:
content = content.replace("const tomorrowStr = tomorrowObj.toISOString().split('T')[0];", "const tomorrowStr = getLocalTomorrowISO();")

# 3. Replace all remaining new Date().toISOString().split('T')[0] in mode.js
content = content.replace("new Date().toISOString().split('T')[0]", "getLocalTodayISO()")

# 4. Replace tmrw.toISOString().split('T')[0] in mode.js
content = content.replace("const tmrwStr = tmrw.toISOString().split('T')[0];", "const tmrwStr = getLocalTomorrowISO();")

with open('mode.js', 'wb') as f:
    f.write(content.encode('utf-8'))
print("mode.js successfully written with LF line endings!")
