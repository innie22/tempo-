import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('i18n.js', 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8')
assert '\r\n' in text

vi_target = '                addAvailabilityBtn: "+ Thêm thời gian làm việc",\r\n'
vi_insert = (
    '                addAvailabilityBtn: "+ Thêm thời gian làm việc",\r\n'
    '                copyToTomorrow: "Sao chép sang ngày mai",\r\n'
    '                repeatWeekly: "Lặp lại hàng tuần",\r\n'
    '                repeatEveryWeek: "Lặp lại mỗi tuần",\r\n'
    '                startDate: "Ngày bắt đầu",\r\n'
    '                endDate: "Ngày kết thúc (không bắt buộc)",\r\n'
    '                confirm: "Xác nhận",\r\n'
    '                cancel: "Hủy",\r\n'
    '                copiedSuccessfully: "Đã sao chép thời gian làm việc thành công.",\r\n'
    '                noWorkingHours: "Không có thời gian làm việc để sao chép.",\r\n'
)

en_target = '                addAvailabilityBtn: "+ Add availability",\r\n'
en_insert = (
    '                addAvailabilityBtn: "+ Add availability",\r\n'
    '                copyToTomorrow: "Copy to Tomorrow",\r\n'
    '                repeatWeekly: "Repeat Weekly",\r\n'
    '                repeatEveryWeek: "Repeat every week",\r\n'
    '                startDate: "Start date",\r\n'
    '                endDate: "End date (optional)",\r\n'
    '                confirm: "Confirm",\r\n'
    '                cancel: "Cancel",\r\n'
    '                copiedSuccessfully: "Working hours copied successfully.",\r\n'
    '                noWorkingHours: "No working hours available to copy.",\r\n'
)

assert vi_target in text, "vi_target not found!"
assert en_target in text, "en_target not found!"

text = text.replace(vi_target, vi_insert, 1)
text = text.replace(en_target, en_insert, 1)

raw_out = text.encode('utf-8')
crlf_cnt = raw_out.count(b'\r\n')
lf_cnt = raw_out.count(b'\n') - crlf_cnt
assert lf_cnt == 0, f"Found {lf_cnt} lone LFs in i18n.js"

with open('i18n.js', 'wb') as f:
    f.write(raw_out)

print(f"i18n.js updated successfully! (CRLF={crlf_cnt}, LF=0)")
