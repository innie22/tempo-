import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 1. emergencySupport.js (CRLF)
es_path = 'emergencySupport.js'
with open(es_path, 'rb') as f:
    raw = f.read()
text = raw.decode('utf-8').replace('\r\n', '\n')

es_reps = [
    ("title: 'Emergency Medical Support'", "title: 'Hỗ trợ Y tế Khẩn cấp'"),
    ("title: 'HOPE — Suicide Prevention Hotline'", "title: 'Đường dây nóng Khủng hoảng & Hỗ trợ Tâm lý HOPE'"),
    ("Stay with someone you trust.", "Ở cùng một người bạn tin tưởng."),
    ("Move somewhere safer.", "Di chuyển đến một nơi an toàn hơn."),
    ("Create distance from anything that could hurt you.", "Tạo khoảng cách với những vật có thể gây tổn thương cho bạn."),
    ("You don't need to solve everything right now. For now, just focus on staying safe.",
     "Bạn không cần giải quyết mọi thứ ngay lúc này. Lúc này, chỉ cần ưu tiên giữ an toàn cho bản thân."),
    ("Hey, I'm having a really difficult time right now and feeling overwhelmed. Are you free to talk or sit with me for a few minutes?",
     "Chào bạn, mình đang trải qua một khoảng thời gian rất khó khăn và cảm thấy quá tải. Bạn có thể trò chuyện hoặc ngồi cùng mình một lúc được không?"),
    ("Message copied! You can paste and send it to a friend or family member.",
     "Đã sao chép tin nhắn! Bạn có thể dán và gửi cho bạn bè hoặc người thân."),
    ("Starting with your 5-minute micro-action. You've got this.",
     "Bắt đầu với hành động nhỏ 5 phút của bạn. Bạn làm được mà."),
    ("Please enter a message before sending.", "Vui lòng nhập tin nhắn trước khi gửi."),
    ("Please describe what is feeling difficult in a few words.", "Vui lòng mô tả ngắn gọn điều đang khiến bạn cảm thấy khó khăn."),
    (">Notice Your Surroundings<", ">Quan sát Xung quanh bạn<"),
    (">Slow Down Your Breathing<", ">Thở Chậm lại<"),
    (">Move Toward Space & Safety<", ">Di chuyển đến Không gian An toàn<")
]
for src, rep in es_reps:
    text = text.replace(src, rep)

with open(es_path, 'wb') as f:
    f.write(text.replace('\n', '\r\n').encode('utf-8'))
print("emergencySupport.js localized (CRLF).")

# 2. urmodeFlow.js (LF)
uf_path = 'urmodeFlow.js'
with open(uf_path, 'rb') as f:
    raw = f.read()
text = raw.decode('utf-8').replace('\r\n', '\n')

uf_reps = [
    ("Working Plan updated and saved successfully.", "Đã cập nhật và lưu Kế hoạch Làm việc thành công."),
    ("Overdue task marked as finished.", "Đã đánh dấu hoàn thành công việc quá hạn."),
    (">Are you ready?<", ">Bạn đã sẵn sàng chưa?<"),
    (">Execute a task now<", ">Thực hiện một việc ngay bây giờ<"),
    (">Your Working Plan Summary<", ">Tóm tắt Kế hoạch Làm việc<"),
    (">Your task for now is…<", ">Công việc bạn cần làm lúc này là…<"),
    (">Your task for now<", ">Việc cần làm ngay của bạn<"),
    (">Would you like to break down this task into smaller steps?<", ">Bạn có muốn chia nhỏ công việc này thành các bước dễ làm hơn không?<"),
    (">Start working on your plan?<", ">Bắt đầu thực hiện kế hoạch của bạn nhé?<")
]
for src, rep in uf_reps:
    text = text.replace(src, rep)

with open(uf_path, 'wb') as f:
    f.write(text.encode('utf-8'))
print("urmodeFlow.js localized (LF).")

# 3. emergencyFlow.js (CRLF)
ef_path = 'emergencyFlow.js'
with open(ef_path, 'rb') as f:
    raw = f.read()
text = raw.decode('utf-8').replace('\r\n', '\n')

ef_reps = [
    ("Working Plan saved successfully.", "Đã lưu Kế hoạch Làm việc thành công."),
    ("Cannot add availability in the past.", "Không thể thêm khung giờ trong quá khứ."),
    ("Please add at least one task to continue.", "Vui lòng thêm ít nhất một công việc để tiếp tục."),
    ("End time must be after start time.", "Thời gian kết thúc phải sau thời gian bắt đầu."),
    ("Please enter a valid estimate duration greater than 0.", "Vui lòng nhập thời lượng dự tính hợp lệ lớn hơn 0."),
    ("All tasks in this Urgent Plan are completed! Great job.", "Tất cả công việc trong Kế hoạch Khẩn cấp đã hoàn thành! Bạn làm rất tốt."),
    ("Please enter a task name.", "Vui lòng nhập tên công việc."),
    (">Pick up where you left off?<", ">Tiếp tục nơi bạn vừa dừng lại nhé?<"),
    (">Reality Check<", ">Thực tế Kiểm tra<"),
    (">Get everything out of your head.<", ">Trút hết mọi suy nghĩ trong đầu ra trang giấy.<"),
    (">Suggested Organization<", ">Gợi ý Sắp xếp<"),
    (">When can you actually work on this?<", ">Khi nào bạn có thể thực sự bắt tay vào làm việc này?<")
]
for src, rep in ef_reps:
    text = text.replace(src, rep)

with open(ef_path, 'wb') as f:
    f.write(text.replace('\n', '\r\n').encode('utf-8'))
print("emergencyFlow.js localized (CRLF).")

# 4. unclearMode.js (CRLF)
uc_path = 'unclearMode.js'
with open(uc_path, 'rb') as f:
    raw = f.read()
text = raw.decode('utf-8').replace('\r\n', '\n')

uc_reps = [
    (">Not sure where to start?<", ">Chưa biết bắt đầu từ đâu?<"),
    (">Let’s figure it out together.<", ">Hãy cùng Tempo tìm cách tháo gỡ nhé.<"),
    (">What's been on your mind lately?<", ">Gần đây điều gì đang quanh quẩn trong tâm trí bạn?<"),
    (">What feels heaviest right now?<", ">Điều gì đang khiến bạn cảm thấy nặng nề nhất lúc này?<"),
    (">What have you noticed lately?<", ">Gần đây bạn nhận thấy cơ thể hoặc tâm trạng mình thế nào?<"),
    (">Overall, how much has this been affecting your everyday life?<", ">Nhìn chung, điều này đang ảnh hưởng đến cuộc sống hằng ngày của bạn nhiều thế nào?<"),
    (">What would help most right now?<", ">Lúc này điều gì sẽ giúp bạn cảm thấy nhẹ nhõm nhất?<"),
    (">Here's what you noticed<", ">Dưới đây là những gì bạn vừa chia sẻ<"),
    (">What feels right from here?<", ">Từ đây, hướng đi nào phù hợp với bạn nhất?<")
]
for src, rep in uc_reps:
    text = text.replace(src, rep)

with open(uc_path, 'wb') as f:
    f.write(text.replace('\n', '\r\n').encode('utf-8'))
print("unclearMode.js localized (CRLF).")
