import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

assert '\r\n' in content, "CRLF missing from i18n.js!"
assert content.count('\n') == content.count('\r\n'), "Lone LF found before updating!"

vi_target = """                viewDetails: "Xem chi tiết →",
                clickToExpand: "Nhấn để mở rộng","""

vi_replacement = """                viewDetails: "Xem chi tiết →",
                clickToExpand: "Nhấn để mở rộng",
                viewTask: "Xem task",
                taskUnavailable: "Task này hiện không còn tồn tại.","""

en_target = """                viewDetails: "View details →",
                clickToExpand: "Click to expand","""

en_replacement = """                viewDetails: "View details →",
                clickToExpand: "Click to expand",
                viewTask: "View Task",
                taskUnavailable: "This task is no longer available.","""

vi_target_crlf = vi_target.replace('\n', '\r\n')
vi_replacement_crlf = vi_replacement.replace('\n', '\r\n')
en_target_crlf = en_target.replace('\n', '\r\n')
en_replacement_crlf = en_replacement.replace('\n', '\r\n')

assert vi_target_crlf in content, "vi_target_crlf not found!"
assert en_target_crlf in content, "en_target_crlf not found!"

content = content.replace(vi_target_crlf, vi_replacement_crlf, 1)
content = content.replace(en_target_crlf, en_replacement_crlf, 1)

assert content.count('\n') == content.count('\r\n'), "Lone LF created!"

with open('i18n.js', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print(f"Updated i18n.js successfully! CRLF lines: {content.count(chr(10))}")
