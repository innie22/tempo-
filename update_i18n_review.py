import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

target_vi = '                yesTakeQuickResetBtn: "Có, tôi muốn lấy lại bình tĩnh một chút →",\r\n'
replacement_vi = (
    '                yesTakeQuickResetBtn: "Có, tôi muốn lấy lại bình tĩnh một chút →",\r\n'
    '                workingPlanReviewBadge: "XEM LẠI PLAN",\r\n'
    '                workingPlanSummaryTitle: "Tổng quan kế hoạch làm việc",\r\n'
    '                tasksOverdueCount: "{count} task đã quá hạn:",\r\n'
    '                overdueWarningDesc: "Một số task đã quá ngày lên lịch hoặc deadline. Bạn có thể giữ lại hoặc điều chỉnh lịch trình.",\r\n'
    '                badgeOverdue: "QUÁ HẠN",\r\n'
    '                badgeUpNext: "TIẾP THEO",\r\n'
    '                badgeThen: "SAU ĐÓ",\r\n'
    '                badgeLater: "ĐỂ SAU",\r\n'
    '                noFixedDeadlineLabel: "Chưa có deadline",\r\n'
    '                adjustMyPlanBtn: "Điều chỉnh plan",\r\n'
    '                keepThePlanBtn: "Giữ nguyên plan →",\r\n'
)

target_en = '                yesTakeQuickResetBtn: "Yes, take a quick reset →",\r\n'
replacement_en = (
    '                yesTakeQuickResetBtn: "Yes, take a quick reset →",\r\n'
    '                workingPlanReviewBadge: "WORKING PLAN REVIEW",\r\n'
    '                workingPlanSummaryTitle: "Your Working Plan Summary",\r\n'
    '                tasksOverdueCount: "{count} tasks overdue:",\r\n'
    '                taskOverdueSingleCount: "{count} task overdue:",\r\n'
    '                overdueWarningDesc: "Some tasks passed their planned date or deadline. You can keep them or adjust your schedule.",\r\n'
    '                badgeOverdue: "OVERDUE",\r\n'
    '                badgeUpNext: "UP NEXT",\r\n'
    '                badgeThen: "THEN",\r\n'
    '                badgeLater: "LATER",\r\n'
    '                noFixedDeadlineLabel: "No fixed deadline",\r\n'
    '                adjustMyPlanBtn: "Adjust my plan",\r\n'
    '                keepThePlanBtn: "Keep the plan →",\r\n'
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

print('Successfully updated i18n.js with review modal keys')
