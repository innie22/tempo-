import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

target_vi = '                keepThePlanBtn: "Giữ nguyên plan →",\r\n'
replacement_vi = (
    '                keepThePlanBtn: "Giữ nguyên plan →",\r\n'
    '                yourTaskForNowBadge: "TASK HIỆN TẠI CỦA BẠN",\r\n'
    '                yourTaskForNowHeading: "Task bạn nên thực hiện lúc này là…",\r\n'
    '                focusNowBtn: "Tập trung ngay →",\r\n'
)

target_en = '                keepThePlanBtn: "Keep the plan →",\r\n'
replacement_en = (
    '                keepThePlanBtn: "Keep the plan →",\r\n'
    '                yourTaskForNowBadge: "YOUR TASK FOR NOW",\r\n'
    '                yourTaskForNowHeading: "Your task for now is…",\r\n'
    '                focusNowBtn: "Focus now →",\r\n'
)

if target_vi not in content:
    print('ERROR: target_vi not found!')
    sys.exit(1)

if target_en not in content:
    print('ERROR: target_en not found!')
    sys.exit(1)

content = content.replace(target_vi, replacement_vi, 1)
content = content.replace(target_en, replacement_en, 1)

with open('i18n.js', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print('Successfully updated i18n.js with Your Task for Now modal keys')
