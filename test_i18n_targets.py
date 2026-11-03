import sys

with open('i18n.js', 'r', encoding='utf-8') as f:
    content = f.read()

target_vi = '                    viewAll: "Xem tất cả"\n                },'
if target_vi not in content:
    target_vi = '                    viewAll: "Xem tất cả"\r\n                },'

print("target_vi in content:", target_vi in content)

target_en = '                    viewAll: "View all"\n                },'
if target_en not in content:
    target_en = '                    viewAll: "View all"\r\n                },'

print("target_en in content:", target_en in content)
