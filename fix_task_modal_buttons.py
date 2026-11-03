import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = 'mode.js'

with open(file_path, 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8')

# Replace Reschedule on its own line
text = re.sub(r'(\n\s*)Reschedule(\s*\n)', r'\1Xếp lại lịch\2', text)

# Replace Clear this task on its own line
text = re.sub(r'(\n\s*)Clear this task(\s*\n)', r'\1Xóa công việc này\2', text)

# Replace priority dropdown buttons in Rmode & URmode detail modals
text = text.replace("<span>${isDone ? 'Done' : priorityBadge}</span>", "<span>${isDone ? 'Đã xong' : (priorityBadge === 'Now' ? 'Làm ngay' : (priorityBadge === 'Then' ? 'Sau đó' : (priorityBadge === 'Later' ? 'Sau nữa' : priorityBadge)))}</span>")
text = text.replace("<span>Now</span>", "<span>Làm ngay</span>")
text = text.replace("<span>Then</span>", "<span>Sau đó</span>")
text = text.replace("<span>Later</span>", "<span>Sau nữa</span>")

# Confirmations
text = text.replace("Are you sure you want to clear this task from your plan?", "Bạn có chắc chắn muốn xóa công việc này khỏi kế hoạch không?")

text_lf = text.replace('\r\n', '\n')

with open(file_path, 'wb') as f:
    f.write(text_lf.encode('utf-8'))

with open(file_path, 'rb') as f:
    final_bytes = f.read()

final_crlf = final_bytes.count(b'\r\n')
final_lone_lf = final_bytes.count(b'\n') - final_crlf
print(f"mode.js task modal buttons updated. Final CRLF: {final_crlf}, lone LF: {final_lone_lf}")
