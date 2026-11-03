import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = 'mode.js'

with open(file_path, 'rb') as f:
    raw = f.read()

initial_crlf = raw.count(b'\r\n')
initial_lone_lf = raw.count(b'\n') - initial_crlf
print(f"mode.js initial CRLF: {initial_crlf}, lone LF: {initial_lone_lf}")

text = raw.decode('utf-8')

# 1. Quick Relief & Focus Now Cards in Rmode and EntryHome
text = text.replace('aria-label="Quick Relief"', 'aria-label="Giải tỏa nhanh"')
text = text.replace('title="Quick Relief"', 'title="Giải tỏa nhanh"')
text = text.replace('alt="Quick Relief"', 'alt="Giải tỏa nhanh"')
text = text.replace('>Quick Relief<', '>Giải tỏa nhanh<')
text = text.replace('> Quick Relief <', '> Giải tỏa nhanh <')

text = text.replace('aria-label="Focus Now"', 'aria-label="Tập trung ngay"')
text = text.replace('title="Focus Now"', 'title="Tập trung ngay"')
text = text.replace('alt="Focus Now"', 'alt="Tập trung ngay"')
text = text.replace('>Focus Now<', '>Tập trung ngay<')
text = text.replace('> Focus Now <', '> Tập trung ngay <')

# 2. Community Cards & Headers
text = text.replace('From the Tempo Community', 'Từ Cộng đồng Tempo')
text = text.replace('>See all posts<', '>Xem tất cả bài viết<')
text = text.replace('>See all →<', '>Xem tất cả →<')
text = text.replace('>See all<', '>Xem tất cả<')
text = text.replace('<span>See all</span>', '<span>Xem tất cả</span>')

# 3. Your Working Plan Headers & Section Titles
text = text.replace('>Your Working Plan<', '>Kế hoạch Làm việc của bạn<')
text = text.replace('Your Working Plan', 'Kế hoạch Làm việc của bạn')
text = text.replace('>TASKS<', '>CÔNG VIỆC<')
text = text.replace('>TASK DONE<', '>VIỆC ĐÃ XONG<')
text = text.replace('>TASK DONE (', '>VIỆC ĐÃ XONG (')

# 4. Task Detail Popups (Rmode & URmode)
# Close button
text = text.replace('aria-label="Close task details"', 'aria-label="Đóng chi tiết công việc"')
text = text.replace('title="Edit task title"', 'title="Chỉnh sửa tên công việc"')
text = text.replace('title="Completed task"', 'title="Công việc đã hoàn thành"')
text = text.replace('title="Change priority"', 'title="Thay đổi mức ưu tiên"')

# Due date editing
text = text.replace("Due: ${escapeHTML(formatRmodeDeadline", "Hạn chót: ${escapeHTML(formatRmodeDeadline")
text = text.replace("Due: ${escapeHTML(formatUrmodeDeadline", "Hạn chót: ${escapeHTML(formatUrmodeDeadline")
text = text.replace("'Edit due day'", "'Chỉnh sửa hạn chót'")
text = text.replace(">Edit due day<", ">Chỉnh sửa hạn chót<")
text = text.replace(">No fixed deadline<", ">Không có hạn chót cố định<")
text = text.replace(">Save deadline<", ">Lưu hạn chót<")

# Subtasks count and controls
text = text.replace("subtasks</span>", "bước đã xong</span>")
text = text.replace(">+ Add subtask<", ">+ Thêm bước nhỏ<")
text = text.replace('placeholder="Enter new subtask title..."', 'placeholder="Nhập tên bước hành động mới..."')
text = text.replace('title="Toggle subtask"', 'title="Đánh dấu bước nhỏ"')
text = text.replace('title="Edit subtask"', 'title="Chỉnh sửa bước nhỏ"')
text = text.replace('title="Delete subtask"', 'title="Xóa bước nhỏ"')
text = text.replace('>No subtasks yet<', '>Chưa có bước nhỏ nào<')

# Task Note in popup
text = text.replace('>Task Note / Description<', '>Ghi chú Công việc / Mô tả<')
text = text.replace('placeholder="Add details, links, or notes for this task..."', 'placeholder="Thêm chi tiết, liên kết hoặc ghi chú cho công việc này..."')
text = text.replace('>Delete note<', '>Xóa ghi chú<')
text = text.replace('>Save note<', '>Lưu ghi chú<')
text = text.replace('>Note:</strong>', '>Ghi chú:</strong>')
text = text.replace('>Edit note</span>', '>Chỉnh sửa ghi chú</span>')
text = text.replace('title="Edit note"', 'title="Chỉnh sửa ghi chú"')
text = text.replace('>+ Create a note<', '>+ Tạo ghi chú<')

# Action buttons in task popup
text = text.replace("${isDone ? 'Mark as active' : 'Mark as done'}", "${isDone ? 'Mở lại công việc' : 'Đánh dấu hoàn thành'}")
text = text.replace(">▶ Focus now<", ">▶ Tập trung ngay<")
text = text.replace(">Reschedule<", ">Xếp lại lịch<")
text = text.replace(">Clear this task<", ">Xóa công việc này<")

# 5. Greetings & Home banners
text = text.replace("'Good morning'", "'Chào buổi sáng'")
text = text.replace("'Good afternoon'", "'Chào buổi chiều'")
text = text.replace("'Good evening'", "'Chào buổi tối'")
text = text.replace("'Welcome back'", "'Chào mừng trở lại'")
text = text.replace("What do you need right now?", "Lúc này bạn cần gì?")
text = text.replace("You haven't set up your working plan yet", "Bạn chưa thiết lập kế hoạch làm việc")
text = text.replace("You're still setting up your plan.", "Bạn vẫn đang thiết lập kế hoạch.")

# Ensure pure LF line endings
text_lf = text.replace('\r\n', '\n')

with open(file_path, 'wb') as f:
    f.write(text_lf.encode('utf-8'))

with open(file_path, 'rb') as f:
    final_bytes = f.read()

final_crlf = final_bytes.count(b'\r\n')
final_lone_lf = final_bytes.count(b'\n') - final_crlf
print(f"mode.js updated. Final CRLF: {final_crlf}, lone LF: {final_lone_lf}")
