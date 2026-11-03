import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = 'planWorkspace.js'

with open(file_path, 'rb') as f:
    raw = f.read()

initial_crlf = raw.count(b'\r\n')
initial_lone_lf = raw.count(b'\n') - initial_crlf
print(f"planWorkspace.js initial CRLF: {initial_crlf}, lone LF: {initial_lone_lf}")

text = raw.decode('utf-8')

replacements = [
    ('>Tempo Working Plan<', '>Kế hoạch Làm việc Tempo<'),
    ('>Flexible / Unscheduled<', '>Linh hoạt / Chưa lên lịch<'),
    ('>Clear this task?<', '>Xóa công việc này?<'),
    ('>Delete your plan?<', '>Xóa kế hoạch của bạn?<'),
    ('>Update your plan?<', '>Cập nhật kế hoạch của bạn?<'),
    ('>Add a task<', '>Thêm công việc<'),
    ('>Task added<', '>Đã thêm công việc<'),
    ('>Reschedule task<', '>Xếp lại lịch công việc<'),
    ('>Your available time<', '>Thời gian rảnh của bạn<'),
    ('Edit Task Note', 'Chỉnh sửa Ghi chú Công việc'),
    ('Create Task Note', 'Tạo Ghi chú Công việc'),
    ('>Start focus now<', '>Bắt đầu tập trung ngay<'),
    ('>Start Focus Now<', '>Bắt đầu tập trung ngay<')
]

for src, rep in replacements:
    text = text.replace(src, rep)

text_lf = text.replace('\r\n', '\n')

with open(file_path, 'wb') as f:
    f.write(text_lf.encode('utf-8'))

with open(file_path, 'rb') as f:
    final_bytes = f.read()

final_crlf = final_bytes.count(b'\r\n')
final_lone_lf = final_bytes.count(b'\n') - final_crlf
print(f"planWorkspace.js updated. Final CRLF: {final_crlf}, lone LF: {final_lone_lf}")
