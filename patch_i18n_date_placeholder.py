with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    c = f.read()

assert '\r\n' in c and '\n' not in c.replace('\r\n', ''), "CRLF integrity violated before patch"

if 'datePlaceholderStep2:' not in c:
    target_vi = 'addPlain: "Th\u00eam",'
    replace_vi = 'addPlain: "Th\u00eam",\r\n                datePlaceholderStep2: "dd/mm/yyyy",'
    assert target_vi in c, "target_vi not found"
    c = c.replace(target_vi, replace_vi, 1)

    target_en = 'addPlain: "Add",'
    replace_en = 'addPlain: "Add",\r\n                datePlaceholderStep2: "MMM DD, YYYY",'
    assert target_en in c, "target_en not found"
    c = c.replace(target_en, replace_en, 1)

    assert '\r\n' in c and '\n' not in c.replace('\r\n', ''), "CRLF integrity violated after patch"
    with open('i18n.js', 'w', encoding='utf-8', newline='') as f:
        f.write(c)
    print("datePlaceholderStep2 added successfully to i18n.js!")
else:
    print("datePlaceholderStep2 already in i18n.js")
