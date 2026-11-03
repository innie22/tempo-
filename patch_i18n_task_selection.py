with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    c = f.read()

assert '\r\n' in c and '\n' not in c.replace('\r\n', ''), "CRLF integrity violated before patch"

if 'taskSelectionUpper:' not in c:
    target_vi = 'doThisTaskBtn: "B\u1eaft \u0111\u1ea7u task n\u00e0y \u2192",'
    replace_vi = """doThisTaskBtn: "B\u1eaft \u0111\u1ea7u task n\u00e0y \u2192",
                taskSelectionUpper: "CH\u1eccN TASK",
                selectTaskToWorkOn: "Ch\u1ecdn task b\u1ea1n mu\u1ed1n th\u1ef1c hi\u1ec7n",
                selectTaskWithArrow: "Ch\u1ecdn \u2192\",""".replace('\n', '\r\n')
    assert target_vi in c, "target_vi not found"
    c = c.replace(target_vi, replace_vi, 1)

    target_en = 'doThisTaskBtn: "Do this task \u2192",'
    replace_en = """doThisTaskBtn: "Do this task \u2192",
                taskSelectionUpper: "TASK SELECTION",
                selectTaskToWorkOn: "Select a task to work on",
                selectTaskWithArrow: "Select \u2192\",""".replace('\n', '\r\n')
    assert target_en in c, "target_en not found"
    c = c.replace(target_en, replace_en, 1)

    assert '\r\n' in c and '\n' not in c.replace('\r\n', ''), "CRLF integrity violated after patch"
    with open('i18n.js', 'w', encoding='utf-8', newline='') as f:
        f.write(c)
    print("Task selection keys added successfully to i18n.js!")
else:
    print("taskSelectionUpper already in i18n.js")
