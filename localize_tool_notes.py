import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = 'toolNotes.js'

with open(file_path, 'rb') as f:
    raw = f.read()

initial_crlf = raw.count(b'\r\n')
initial_lone_lf = raw.count(b'\n') - initial_crlf
print(f"toolNotes.js initial CRLF: {initial_crlf}, lone LF: {initial_lone_lf}")

text = raw.decode('utf-8')

replacements = [
    ('>Create a Note<', '>Tạo Ghi chú<'),
    ('>Edit Note<', '>Chỉnh sửa Ghi chú<'),
    ('>Tool Notes<', '>Ghi chú Công cụ<'),
    ('>Day Notes<', '>Ghi chú theo ngày<'),
    ('>Task Notes<', '>Ghi chú công việc<'),
    ('No day notes yet.', 'Chưa có ghi chú theo ngày nào.'),
    ('No task notes yet.', 'Chưa có ghi chú công việc nào.'),
    ('No notes saved yet.', 'Chưa có ghi chú nào được lưu.'),
    ('>Save Note<', '>Lưu ghi chú<'),
    ('>Save changes<', '>Lưu thay đổi<'),
    ('>Delete Note<', '>Xóa ghi chú<'),
    ('>Delete note<', '>Xóa ghi chú<'),
    ('Note saved successfully.', 'Đã lưu ghi chú thành công.'),
    ('Note deleted successfully.', 'Đã xóa ghi chú thành công.'),
    ('Note deleted.', 'Đã xóa ghi chú.'),
    ('placeholder="Title (Optional)"', 'placeholder="Tiêu đề (Tùy chọn)"'),
    ('placeholder="Write your note here..."', 'placeholder="Viết ghi chú của bạn tại đây..."'),
    ('placeholder="Add details, thoughts, or next steps..."', 'placeholder="Thêm chi tiết, suy nghĩ hoặc bước tiếp theo..."'),
    ('Academic Task', 'Công việc Học tập'),
    ('No task selected', 'Chưa chọn công việc'),
    ('>All Notes<', '>Tất cả ghi chú<'),
    ('>Recent<', '>Gần đây<'),
    ('>Cancel<', '>Hủy<'),
    ('>Close<', '>Đóng<')
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
print(f"toolNotes.js updated. Final CRLF: {final_crlf}, lone LF: {final_lone_lf}")
