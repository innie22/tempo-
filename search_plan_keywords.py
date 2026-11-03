import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('planWorkspace.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

search_words = [
    "Return Home", "Về trang chủ",
    "Add task", "Thêm task",
    "Add availability", "Thêm thời gian",
    "Adjust Plan", "Điều chỉnh plan",
    "Delete my plan", "Xóa plan",
    "Tasks",
    "Tomorrow", "Ngày mai",
    "Completed", "Đã hoàn thành",
    "Deadline",
    "No deadline", "Chưa có deadline",
    "Subtasks", "subtask",
    "Do now", "Làm ngay",
    "Done", "Hoàn thành",
    "Edit deadline", "Sửa deadline",
    "Break down task", "Chia nhỏ",
    "Add note", "Thêm ghi chú",
    "Mark as done",
    "Focus now", "Làm task",
    "Reschedule", "Đổi lịch",
    "Clear this task", "Xóa task"
]

results = {}
for i, line in enumerate(lines):
    for w in search_words:
        if w.lower() in line.lower():
            results.setdefault(w, []).append((i + 1, line.strip()))

for w, occurrences in results.items():
    print(f"=== Keyword: '{w}' (Count: {len(occurrences)}) ===")
    for line_num, l_str in occurrences[:4]:
        print(f"  Line {line_num}: {l_str}")
