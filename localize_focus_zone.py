import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = 'focusZone.js'

with open(file_path, 'rb') as f:
    raw = f.read()

initial_crlf = raw.count(b'\r\n')
initial_lone_lf = raw.count(b'\n') - initial_crlf
print(f"focusZone.js initial CRLF: {initial_crlf}, lone LF: {initial_lone_lf}")

text = raw.decode('utf-8')

replacements = [
    ('>What are you working on?<', '>Bạn đang làm việc gì?<'),
    ('Independent Focus Session', 'Phiên Tập trung Độc lập'),
    ('No task selected', 'Chưa chọn công việc'),
    ('>Focus paused<', '>Đã tạm dừng tập trung<'),
    ('>End this focus session?<', '>Kết thúc phiên tập trung này?<'),
    ('>Did you finish the task?<', '>Bạn đã hoàn thành công việc chưa?<'),
    ('>All action steps are done!<', '>Tất cả các bước hành động đã xong!<'),
    ('>Take a Break<', '>Nghỉ ngơi<'),
    ('>What feels good right now?<', '>Lúc này bạn thấy thoải mái với điều gì?<'),
    ('>Gentle Match<', '>Ghép cặp Nhẹ nhàng<'),
    ('>Move a little<', '>Vận động một chút<'),
    ('>Just resting.<', '>Chỉ cần nghỉ ngơi.<'),
    ('>Break time is up 🌿<', '>Đã hết giờ nghỉ 🌿<'),
    ('>Break complete 🌿<', '>Đã xong giờ nghỉ 🌿<'),
    ('>Today\'s plan is complete ✓<', '>Kế hoạch hôm nay đã hoàn thành ✓<'),
    ('>Tomorrow\'s Plan<', '>Kế hoạch Ngày mai<'),
    ('>Change focus rhythm<', '>Thay đổi nhịp độ tập trung<'),
    ('>Focus rhythm updated ✓<', '>Đã cập nhật nhịp độ tập trung ✓<'),
    ('>Back to break options<', '>Quay lại lựa chọn nghỉ ngơi<'),
    ('>Back to break<', '>Quay lại giờ nghỉ<'),
    ('>Another round<', '>Chơi ván khác<'),
    ('All pairs matched. Take a slow breath.', 'Đã tìm thấy tất cả các cặp ghép. Hãy thở một hơi chậm rãi.'),
    ('>Start focus<', '>Bắt đầu tập trung<'),
    ('>Start Focus<', '>Bắt đầu tập trung<'),
    ('>Pause<', '>Tạm dừng<'),
    ('>Resume<', '>Tiếp tục<'),
    ('>End session<', '>Kết thúc phiên<'),
    ('>End Session<', '>Kết thúc phiên<')
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
print(f"focusZone.js updated. Final CRLF: {final_crlf}, lone LF: {final_lone_lf}")
