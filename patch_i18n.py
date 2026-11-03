import sys

with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    c = f.read()

if 'addPlain:' not in c:
    target_vi = 'taskNamePlaceholderEllipsis: "T\u00ean task...",'
    replace_vi = 'taskNamePlaceholderEllipsis: "T\u00ean task...",\r\n                addPlain: "Th\u00eam",'
    assert target_vi in c, "target_vi not found"
    c = c.replace(target_vi, replace_vi, 1)

    target_en = 'taskNamePlaceholderEllipsis: "Task name...",'
    replace_en = 'taskNamePlaceholderEllipsis: "Task name...",\r\n                addPlain: "Add",'
    assert target_en in c, "target_en not found"
    c = c.replace(target_en, replace_en, 1)

    assert '\r\n' in c and '\n' not in c.replace('\r\n', ''), "CRLF integrity violated"
    with open('i18n.js', 'w', encoding='utf-8', newline='') as f:
        f.write(c)
    print("addPlain added successfully!")
else:
    print("addPlain already in i18n.js")
