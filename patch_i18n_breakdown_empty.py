with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    c = f.read()

assert '\r\n' in c and '\n' not in c.replace('\r\n', ''), "CRLF integrity violated before patch"

if 'breakdownEmptyState:' not in c:
    target_vi = 'selectTaskWithArrow: "Ch\u1ecdn \u2192",'
    replace_vi = """selectTaskWithArrow: "Ch\u1ecdn \u2192",
                breakdownEmptyState: "Ch\u01b0a c\u00f3 b\u01b0\u1edbc th\u1ef1c hi\u1ec7n n\u00e0o. H\u00e3y th\u00eam b\u01b0\u1edbc \u0111\u1ea7u ti\u00ean b\u00ean d\u01b0\u1edbi ho\u1eb7c ch\u1ecdn \u2728 AI h\u1ed7 tr\u1ee3.",""".replace('\n', '\r\n')
    assert target_vi in c, "target_vi not found"
    c = c.replace(target_vi, replace_vi, 1)

    target_en = 'selectTaskWithArrow: "Select \u2192",'
    replace_en = """selectTaskWithArrow: "Select \u2192",
                breakdownEmptyState: "No action steps added yet. Add your first step below or click \u2728 AI Help.",""".replace('\n', '\r\n')
    assert target_en in c, "target_en not found"
    c = c.replace(target_en, replace_en, 1)

    assert '\r\n' in c and '\n' not in c.replace('\r\n', ''), "CRLF integrity violated after patch"
    with open('i18n.js', 'w', encoding='utf-8', newline='') as f:
        f.write(c)
    print("breakdownEmptyState keys added successfully to i18n.js!")
else:
    print("breakdownEmptyState already in i18n.js")
