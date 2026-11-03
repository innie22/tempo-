with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    c = f.read()

assert '\r\n' in c and '\n' not in c.replace('\r\n', ''), "CRLF integrity violated before patch"

if 'firstTaskExecutionUpper:' not in c:
    target_vi = 'yesStartWorkingBtn: "C\u00f3, b\u1eaft \u0111\u1ea7u th\u00f4i \u2192",'
    replace_vi = """yesStartWorkingBtn: "C\u00f3, b\u1eaft \u0111\u1ea7u th\u00f4i \u2192",
                firstTaskExecutionUpper: "B\u1eaeT \u0110\u1ea6U TASK \u0110\u1ea6U TI\u00caN",
                yourFirstTaskIs: "Task \u0111\u1ea7u ti\u00ean c\u1ee7a b\u1ea1n l\u00e0\u2026",
                readyNowBadge: "S\u1eb4N S\u00c0NG TH\u1ef0C HI\u1ec6N",
                chooseAnotherTaskBtn: "Ch\u1ecdn task kh\u00e1c",
                doThisTaskBtn: "B\u1eaft \u0111\u1ea7u task n\u00e0y \u2192\",""".replace('\n', '\r\n')
    assert target_vi in c, "target_vi not found"
    c = c.replace(target_vi, replace_vi, 1)

    target_en = 'yesStartWorkingBtn: "Yes, start working \u2192",'
    replace_en = """yesStartWorkingBtn: "Yes, start working \u2192",
                firstTaskExecutionUpper: "FIRST TASK EXECUTION",
                yourFirstTaskIs: "Your first task is\u2026",
                readyNowBadge: "READY NOW",
                chooseAnotherTaskBtn: "Choose another task",
                doThisTaskBtn: "Do this task \u2192\",""".replace('\n', '\r\n')
    assert target_en in c, "target_en not found"
    c = c.replace(target_en, replace_en, 1)

    assert '\r\n' in c and '\n' not in c.replace('\r\n', ''), "CRLF integrity violated after patch"
    with open('i18n.js', 'w', encoding='utf-8', newline='') as f:
        f.write(c)
    print("First task execution keys added successfully to i18n.js!")
else:
    print("firstTaskExecutionUpper already in i18n.js")
