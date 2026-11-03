with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    c = f.read()

assert '\r\n' in c and '\n' not in c.replace('\r\n', ''), "CRLF integrity violated before patch"

if 'adjustPlanStep3:' not in c:
    target_vi = 'datePlaceholderStep2: "dd/mm/yyyy",'
    replace_vi = """datePlaceholderStep2: "dd/mm/yyyy",
                adjustPlanStep3: "B\u01af\u1edaC 3/3 \u00b7 X\u00c1C NH\u1eacN PLAN M\u1edaI",
                proposedUpdatedPlan: "Plan m\u1edbi \u0111\u01b0\u1ee3c \u0111\u1ec1 xu\u1ea5t",
                adjustPlanStep3Desc: "\u0110\u00e2y l\u00e0 k\u1ebf ho\u1ea1ch l\u00e0m vi\u1ec7c \u0111\u00e3 \u0111\u01b0\u1ee3c \u0111i\u1ec1u ch\u1ec9nh. K\u1ebf ho\u1ea1ch ban \u0111\u1ea7u s\u1ebd \u0111\u01b0\u1ee3c gi\u1eef nguy\u00ean cho \u0111\u1ebfn khi b\u1ea1n x\u00e1c nh\u1eadn v\u00e0 l\u01b0u thay \u0111\u1ed5i.",
                doThisFirstUpper: "L\u00c0M \u0110\u1ea6U TI\u00caN",
                upNextUpper: "TI\u1ebeP THEO",
                noFixedDeadlineStep3: "Ch\u01b0a c\u00f3 deadline c\u1ed1 \u0111\u1ecbnh",
                saveUpdatedPlan: "L\u01b0u Plan m\u1edbi \u2192\",""".replace('\n', '\r\n')
    assert target_vi in c, "target_vi not found"
    c = c.replace(target_vi, replace_vi, 1)

    target_en = 'datePlaceholderStep2: "MMM DD, YYYY",'
    replace_en = """datePlaceholderStep2: "MMM DD, YYYY",
                adjustPlanStep3: "STEP 3 OF 3 \u00b7 CONFIRM UPDATED PLAN",
                proposedUpdatedPlan: "Proposed Updated Plan",
                adjustPlanStep3Desc: "Here is your updated working plan. Your original plan is preserved until you confirm and save.",
                doThisFirstUpper: "DO THIS FIRST",
                upNextUpper: "UP NEXT",
                noFixedDeadlineStep3: "No fixed deadline",
                saveUpdatedPlan: "Save updated plan \u2192\",""".replace('\n', '\r\n')
    assert target_en in c, "target_en not found"
    c = c.replace(target_en, replace_en, 1)

    assert '\r\n' in c and '\n' not in c.replace('\r\n', ''), "CRLF integrity violated after patch"
    with open('i18n.js', 'w', encoding='utf-8', newline='') as f:
        f.write(c)
    print("Step 3 keys added successfully to i18n.js!")
else:
    print("adjustPlanStep3 already in i18n.js")
