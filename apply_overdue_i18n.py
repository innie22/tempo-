import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'rb') as f:
    raw = f.read()

assert b'\r\n' in raw and raw.count(b'\n') == raw.count(b'\r\n'), 'i18n.js must be CRLF'

content = raw.decode('utf-8')

# Target 1 in VI modes.urgent (20 spaces)
target_vi = '                    updateSchedule: "Cập nhật lịch trình",\r\n'
replacement_vi = (
    '                    updateSchedule: "Cập nhật lịch trình",\r\n'
    '                    taskOverdue: "TASK TRỄ DEADLINE",\r\n'
    '                    thisTaskIsOverdue: "Task này đã trễ Deadline",\r\n'
    '                    taskOverdueDesc: "Task này đã trễ deadline. Bạn muốn xóa, đánh dấu hoàn thành hay cập nhật lại?",\r\n'
    '                    overdueBadge: "TRỄ DEADLINE",\r\n'
    '                    scheduledLabel: "Ngày lên lịch:",\r\n'
    '                    deadlineLabel: "Deadline:",\r\n'
    '                    clearThisTask: "Xóa task này",\r\n'
    '                    markAsDone: "Hoàn thành",\r\n'
    '                    editTask: "Chỉnh sửa task",\r\n'
)

assert target_vi in content, 'target_vi not found'
content = content.replace(target_vi, replacement_vi, 1)

# Target 2 in VI workspace (16 spaces)
target_vi_ws = '                priorityOverdue: "Quá hạn",\r\n                priorityOverdueUpper: "QUÁ HẠN",'
replacement_vi_ws = '                priorityOverdue: "Trễ Deadline",\r\n                priorityOverdueUpper: "TRỄ DEADLINE",'

assert target_vi_ws in content, 'target_vi_ws not found'
content = content.replace(target_vi_ws, replacement_vi_ws, 1)

# Target 3 in EN modes.urgent (20 spaces)
target_en = '                    updateSchedule: "Update schedule",\r\n'
replacement_en = (
    '                    updateSchedule: "Update schedule",\r\n'
    '                    taskOverdue: "TASK OVERDUE",\r\n'
    '                    thisTaskIsOverdue: "This task is overdue",\r\n'
    '                    taskOverdueDesc: "Looks like this task has passed its due date. Would you like to clear it, mark it as done, or update it?",\r\n'
    '                    overdueBadge: "OVERDUE",\r\n'
    '                    scheduledLabel: "Scheduled:",\r\n'
    '                    deadlineLabel: "Deadline:",\r\n'
    '                    clearThisTask: "Clear this task",\r\n'
    '                    markAsDone: "Mark as done",\r\n'
    '                    editTask: "Edit task",\r\n'
)

assert target_en in content, 'target_en not found'
content = content.replace(target_en, replacement_en, 1)

new_raw = content.encode('utf-8')
assert new_raw.count(b'\r\n') == new_raw.count(b'\n'), 'Resulting i18n.js must be strictly CRLF'

with open('i18n.js', 'wb') as f:
    f.write(new_raw)

print(f'Successfully updated i18n.js! Total lines: {len(new_raw.split(b"\r\n"))}')
