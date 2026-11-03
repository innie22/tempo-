import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'r', encoding='utf-8', newline='') as f:
    text = f.read()

assert '\r\n' in text, "i18n.js missing CRLF!"

# Target for vi.workspace
vi_target = '                nextAdjustAddTasks: "Tiếp theo: Điều chỉnh & thêm task →",\r\n'
vi_replacement = """                nextAdjustAddTasks: "Tiếp theo: Điều chỉnh & thêm task →",\r\n                adjustPlanStep2: "BƯỚC 2/3 · ĐIỀU CHỈNH PLAN",\r\n                adjustEstimatesAndAddTasks: "Điều chỉnh thời lượng & thêm task mới",\r\n                retainedTasksCount: "CÁC TASK ĐƯỢC GIỮ LẠI ({count}):",\r\n                duePrefixLabel: "Deadline:",\r\n                addNewTaskUpper: "+ THÊM TASK MỚI:",\r\n                taskNamePlaceholderEllipsis: "Tên task...",\r\n                nextProposePlan: "Tiếp theo: Đề xuất plan →",\r\n"""

assert vi_target in text, "vi_target not found in i18n.js"
text = text.replace(vi_target, vi_replacement, 1)

# Target for en.workspace
en_target = '                nextAdjustAddTasks: "Next: Adjust & add tasks →",\r\n'
en_replacement = """                nextAdjustAddTasks: "Next: Adjust & add tasks →",\r\n                adjustPlanStep2: "STEP 2 OF 3 · ADJUST PLAN",\r\n                adjustEstimatesAndAddTasks: "Adjust estimates & add new tasks",\r\n                retainedTasksCount: "RETAINED TASKS ({count}):",\r\n                duePrefixLabel: "Due:",\r\n                addNewTaskUpper: "+ ADD NEW TASK:",\r\n                taskNamePlaceholderEllipsis: "Task name...",\r\n                nextProposePlan: "Next: Propose plan →",\r\n"""

assert en_target in text, "en_target not found in i18n.js"
text = text.replace(en_target, en_replacement, 1)

# Ensure no lone LF
lone_lf = text.replace('\r\n', '').count('\n')
assert lone_lf == 0, f"Found {lone_lf} lone LFs in i18n.js!"

with open('i18n.js', 'wb') as f:
    f.write(text.encode('utf-8'))

print("i18n.js updated successfully with Step 2 keys! (CRLF verified, 0 lone LFs)")
