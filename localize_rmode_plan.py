import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = 'mode.js'

with open(file_path, 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8')

# 1. Update Rmode working plan headers
text = text.replace(
    '<span>Tasks</span>',
    '<span>CÔNG VIỆC</span>'
)
text = text.replace(
    '<span>Task Done</span>',
    '<span>VIỆC ĐÃ XONG</span>'
)
text = text.replace(
    '>Adjust Plan<',
    '>Điều chỉnh Kế hoạch<'
)
text = text.replace(
    '${completedCount}/${totalCount} Tasks',
    '${completedCount}/${totalCount} công việc'
)
text = text.replace(
    'No tasks pending',
    'Không có công việc nào đang chờ'
)
text = text.replace(
    'Completed tasks will appear here',
    'Công việc đã hoàn thành sẽ xuất hiện tại đây'
)

# 2. Update default Rmode mock tasks labels
text = text.replace("dayLabel: 'Today'", "dayLabel: 'Hôm nay'")
text = text.replace("dayLabel: 'Tomorrow'", "dayLabel: 'Ngày mai'")
text = text.replace("timeHeader: 'Today, 2:00 PM to 4:00 PM'", "timeHeader: 'Hôm nay, 14:00 đến 16:00'")
text = text.replace("timeHeader: 'Today, 5:00 PM to 7:00 PM'", "timeHeader: 'Hôm nay, 17:00 đến 19:00'")
text = text.replace("tag: 'Now'", "tag: 'Làm ngay'")
text = text.replace("tag: 'Then'", "tag: 'Sau đó'")
text = text.replace("tag: 'Later'", "tag: 'Sau nữa'")
text = text.replace("dueDate: 'Due: Oct 17, 2026 - 9:00 PM'", "dueDate: 'Hạn chót: 17 thg 10, 2026 - 21:00'")
text = text.replace("dueDate: 'Due: Oct 18, 2026 - 10:00 AM'", "dueDate: 'Hạn chót: 18 thg 10, 2026 - 10:00'")
text = text.replace("dueDate: 'Due: Oct 20, 2026 - 10:00 PM'", "dueDate: 'Hạn chót: 20 thg 10, 2026 - 22:00'")
text = text.replace("subtasksText: '0/6 subtasks'", "subtasksText: '0/6 bước nhỏ'")
text = text.replace("subtasksText: '0/3 subtasks'", "subtasksText: '0/3 bước nhỏ'")
text = text.replace("subtasksText: '0/3 subtasks'", "subtasksText: '0/3 bước nhỏ'")
text = text.replace("title=\"${isDone ? 'Mark incomplete' : 'Mark complete'}\"", "title=\"${isDone ? 'Đánh dấu chưa xong' : 'Đánh dấu hoàn thành'}\"")
text = text.replace("${isDone ? 'Done' : escapeHTML(item.tag)}", "${isDone ? 'Đã xong' : escapeHTML(item.tag)}")

text_lf = text.replace('\r\n', '\n')

with open(file_path, 'wb') as f:
    f.write(text_lf.encode('utf-8'))

with open(file_path, 'rb') as f:
    final_bytes = f.read()

final_crlf = final_bytes.count(b'\r\n')
final_lone_lf = final_bytes.count(b'\n') - final_crlf
print(f"mode.js rmode plan updated. Final CRLF: {final_crlf}, lone LF: {final_lone_lf}")
