with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    c = f.read()

assert '\r\n' in c and '\n' not in c.replace('\r\n', ''), "CRLF integrity violated before patch"

if 'planConfirmedAndSavedUpper:' not in c:
    target_vi = 'saveUpdatedPlan: "L\u01b0u Plan m\u1edbi \u2192",'
    replace_vi = """saveUpdatedPlan: "L\u01b0u Plan m\u1edbi \u2192",
                planConfirmedAndSavedUpper: "PLAN \u0110\u00c3 \u0110\u01af\u1ee2C X\u00c1C NH\u1eacN & L\u01afU",
                yourTaskForNow: "Task ti\u1ebfp theo c\u1ee7a b\u1ea1n",
                doThisFirstPriority: "\u01afU TI\u00caN L\u00c0M TR\u01af\u1edaC",
                dueNoFixedDeadline: "Deadline: Ch\u01b0a c\u00f3 deadline",
                dueWithDeadlinePrefix: "Deadline:",
                breakDownQuestion: "B\u1ea1n c\u00f3 mu\u1ed1n chia nh\u1ecf task n\u00e0y th\u00e0nh c\u00e1c b\u01b0\u1edbc d\u1ec5 th\u1ef1c hi\u1ec7n h\u01a1n kh\u00f4ng?",
                breakDownDesc: "Chia task l\u1edbn th\u00e0nh nh\u1eefng b\u01b0\u1edbc nh\u1ecf t\u1eeb 10\u201315 ph\u00fat gi\u00fap b\u1ea1n d\u1ec5 b\u1eaft \u0111\u1ea7u h\u01a1n v\u00e0 tr\u00e1nh c\u1ea3m gi\u00e1c qu\u00e1 t\u1ea3i.",
                noStartWorking: "Kh\u00f4ng, b\u1eaft \u0111\u1ea7u l\u00e0m",
                breakDownTaskBtn: "Chia nh\u1ecf task \u2192\",""".replace('\n', '\r\n')
    assert target_vi in c, "target_vi not found"
    c = c.replace(target_vi, replace_vi, 1)

    target_en = 'saveUpdatedPlan: "Save updated plan \u2192",'
    replace_en = """saveUpdatedPlan: "Save updated plan \u2192",
                planConfirmedAndSavedUpper: "PLAN CONFIRMED & SAVED",
                yourTaskForNow: "Your task for now",
                doThisFirstPriority: "DO THIS FIRST",
                dueNoFixedDeadline: "Due: No fixed deadline",
                dueWithDeadlinePrefix: "Due:",
                breakDownQuestion: "Would you like to break down this task into smaller steps?",
                breakDownDesc: "Breaking big tasks into 10\u201315 min steps prevents freeze and makes starting effortless.",
                noStartWorking: "No, start working",
                breakDownTaskBtn: "Break down task \u2192\",""".replace('\n', '\r\n')
    assert target_en in c, "target_en not found"
    c = c.replace(target_en, replace_en, 1)

    assert '\r\n' in c and '\n' not in c.replace('\r\n', ''), "CRLF integrity violated after patch"
    with open('i18n.js', 'w', encoding='utf-8', newline='') as f:
        f.write(c)
    print("Post-save modal keys added successfully to i18n.js!")
else:
    print("planConfirmedAndSavedUpper already in i18n.js")
