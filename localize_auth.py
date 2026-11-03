import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = 'auth.js'

with open(file_path, 'rb') as f:
    raw = f.read()

initial_crlf = raw.count(b'\r\n')
initial_lone_lf = raw.count(b'\n') - initial_crlf
print(f"auth.js initial CRLF: {initial_crlf}, lone LF: {initial_lone_lf}")

text = raw.decode('utf-8')
text_norm = text.replace('\r\n', '\n')

replacements = [
    ('Please fill in all required fields.', 'Vui lòng điền đầy đủ các thông tin bắt buộc.'),
    ('Passwords do not match. Please verify.', 'Mật khẩu không khớp. Vui lòng kiểm tra lại.'),
    ('Passwords do not match.', 'Mật khẩu không khớp.'),
    ('Password must be at least 6 characters long.', 'Mật khẩu phải có ít nhất 6 ký tự.'),
    ('Email or password is incorrect.', 'Email hoặc mật khẩu không chính xác.'),
    ('Please enter both email and password.', 'Vui lòng nhập cả email và mật khẩu.'),
    ('You have been signed out.', 'Bạn đã đăng xuất.'),
    ('Welcome back, ${welcomeName}!', 'Chào mừng trở lại, ${welcomeName}!'),
    ('Welcome back, ${name}!', 'Chào mừng trở lại, ${name}!'),
    ('Account created for ${displayName.trim()}! Please sign in to continue.', 'Đã tạo tài khoản cho ${displayName.trim()}! Vui lòng đăng nhập để tiếp tục.'),
    ('Account created for ${fullName}! Please sign in to continue.', 'Đã tạo tài khoản cho ${fullName}! Vui lòng đăng nhập để tiếp tục.'),
    ('Could not send reset email. Please try again.', 'Không thể gửi email đặt lại mật khẩu. Vui lòng thử lại.'),
    ('Password reset link has been sent to your email.', 'Liên kết đặt lại mật khẩu đã được gửi đến email của bạn.'),
    ('An unexpected error occurred. Please try again.', 'Đã xảy ra lỗi không mong muốn. Vui lòng thử lại.'),
    ('Please agree to the Terms of Service and Privacy Policy to create an account.', 'Vui lòng đồng ý với Điều khoản Dịch vụ và Chính sách Quyền riêng tư để tạo tài khoản.'),
    ('Please agree to the Terms of Service and Privacy Policy.', 'Vui lòng đồng ý với Điều khoản Dịch vụ và Chính sách Quyền riêng tư.'),
    ('Failed to submit application. Please try again.', 'Gửi đơn đăng ký không thành công. Vui lòng thử lại.')
]

for src, rep in replacements:
    text_norm = text_norm.replace(src, rep)

new_crlf = text_norm.replace('\n', '\r\n')

with open(file_path, 'wb') as f:
    f.write(new_crlf.encode('utf-8'))

with open(file_path, 'rb') as f:
    final_bytes = f.read()

final_crlf = final_bytes.count(b'\r\n')
final_lone_lf = final_bytes.count(b'\n') - final_crlf
print(f"auth.js updated. Final CRLF: {final_crlf}, lone LF: {final_lone_lf}")
