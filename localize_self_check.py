import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

for file_path in ['recoverySelfCheck.js', 'selfCheckWorkspace.js']:
    with open(file_path, 'rb') as f:
        raw = f.read()

    initial_crlf = raw.count(b'\r\n')
    initial_lone_lf = raw.count(b'\n') - initial_crlf
    print(f"{file_path} initial CRLF: {initial_crlf}, lone LF: {initial_lone_lf}")

    text = raw.decode('utf-8')

    replacements = [
        ("Things I'm keeping track of", "Những điều mình đang theo dõi"),
        ("Add something to track", "Thêm điều cần theo dõi"),
        ("How have things been today?", "Hôm nay của bạn thế nào?"),
        ("Today's check-in", "Điểm danh hôm nay"),
        ("Today’s check-in", "Điểm danh hôm nay"),
        ("Today's self-check", "Điểm danh hôm nay"),
        ("Today’s self-check", "Điểm danh hôm nay"),
        ("Signs of stress", "Dấu hiệu căng thẳng"),
        ("Supportive habits", "Thói quen hỗ trợ"),
        ("Save check-in", "Lưu điểm danh"),
        ("Save Check-in", "Lưu điểm danh"),
        ("-day check-in streak", " ngày điểm danh liên tiếp"),
        ("Tracker Summary for this week", "Tổng kết theo dõi tuần này"),
        ("No tracking items yet", "Chưa có mục theo dõi nào"),
        ("Tempo Self-check", "Tự kiểm tra Tempo"),
        ("Your Tracking System", "Hệ thống Theo dõi của bạn"),
        ("Clear all tracking items?", "Xóa tất cả mục theo dõi?"),
        ("My Weekly Report", "Báo cáo Tuần của tôi")
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
    print(f"{file_path} updated. Final CRLF: {final_crlf}, lone LF: {final_lone_lf}")
