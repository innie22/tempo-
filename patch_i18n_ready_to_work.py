with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    c = f.read()

assert '\r\n' in c and '\n' not in c.replace('\r\n', ''), "CRLF integrity violated before patch"

if 'readyToWorkUpper:' not in c:
    target_vi = 'breakDownTaskBtn: "Chia nh\u1ecf task \u2192",'
    replace_vi = """breakDownTaskBtn: "Chia nh\u1ecf task \u2192",
                readyToWorkUpper: "S\u1eb4N S\u00c0NG B\u1eaeT \u0110\u1ea6U",
                startWorkingOnPlanTitle: "B\u1eaft \u0111\u1ea7u l\u00e0m vi\u1ec7c nh\u00e9?",
                startWorkingOnPlanDesc: "K\u1ebf ho\u1ea1ch l\u00e0m vi\u1ec7c c\u1ee7a b\u1ea1n \u0111\u00e3 s\u1eb5n s\u00e0ng. B\u1ea1n mu\u1ed1n b\u1eaft \u0111\u1ea7u v\u1edbi task \u0111\u1ea7u ti\u00ean ngay b\u00e2y gi\u1edd kh\u00f4ng?",
                firstTaskPrefix: "Task \u0111\u1ea7u ti\u00ean:",
                laterBtn: "\u0110\u1ec3 sau",
                breakMoreTasksBtn: "Chia nh\u1ecf th\u00eam task",
                yesStartWorkingBtn: "C\u00f3, b\u1eaft \u0111\u1ea7u th\u00f4i \u2192\",""".replace('\n', '\r\n')
    assert target_vi in c, "target_vi not found"
    c = c.replace(target_vi, replace_vi, 1)

    target_en = 'breakDownTaskBtn: "Break down task \u2192",'
    replace_en = """breakDownTaskBtn: "Break down task \u2192",
                readyToWorkUpper: "READY TO WORK",
                startWorkingOnPlanTitle: "Start working on your plan?",
                startWorkingOnPlanDesc: "Your working plan is ready. Would you like to start right away on your first task?",
                firstTaskPrefix: "First task:",
                laterBtn: "Later",
                breakMoreTasksBtn: "Break more tasks",
                yesStartWorkingBtn: "Yes, start working \u2192\",""".replace('\n', '\r\n')
    assert target_en in c, "target_en not found"
    c = c.replace(target_en, replace_en, 1)

    assert '\r\n' in c and '\n' not in c.replace('\r\n', ''), "CRLF integrity violated after patch"
    with open('i18n.js', 'w', encoding='utf-8', newline='') as f:
        f.write(c)
    print("Ready to work keys added successfully to i18n.js!")
else:
    print("readyToWorkUpper already in i18n.js")
