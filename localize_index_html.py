import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = 'index.html'

with open(file_path, 'rb') as f:
    raw = f.read()

initial_crlf = raw.count(b'\r\n')
initial_lone_lf = raw.count(b'\n') - initial_crlf
print(f"index.html initial CRLF: {initial_crlf}, lone LF: {initial_lone_lf}")

text = raw.decode('utf-8')

# 1. Update Title and Brand Logo Alt/Title
text = text.replace(
    "<title>Tempo — A calmer you, one step at a time.</title>",
    "<title>Tempo — Một bạn bình tâm hơn, từng bước một.</title>"
)
text = text.replace(
    'title="Tempo — A calmer you, one step at a time."',
    'title="Tempo — Một bạn bình tâm hơn, từng bước một."'
)
text = text.replace(
    'alt="Tempo — A calmer you, one step at a time."',
    'alt="Tempo — Một bạn bình tâm hơn, từng bước một."'
)

# 2. Update Nav Links
text = text.replace(
    """>
                    About
                </a>""",
    """>
                    Giới thiệu
                </a>"""
)
text = text.replace(
    """>
                    Check
                </a>""",
    """>
                    Tự kiểm tra
                </a>"""
)
text = text.replace(
    """>
                    Plan
                </a>""",
    """>
                    Kế hoạch
                </a>"""
)
text = text.replace(
    """>
                    Community
                </a>""",
    """>
                    Cộng đồng
                </a>"""
)

# 3. Update Search button & placeholder
text = text.replace('title="Search Tempo"', 'title="Tìm kiếm trên Tempo"')
text = text.replace('placeholder="Search Tempo..."', 'placeholder="Tìm kiếm trên Tempo..."')

# 4. Hide Language Switcher per Requirement 9
text = text.replace(
    '<div class="relative" id="nav-language-wrapper">',
    '<div class="relative hidden" id="nav-language-wrapper" style="display: none !important;">'
)

# 5. Update SOS title & labels
text = text.replace(
    'title="Safety Emergency Support (24/7 Lifelines & Grounding)"',
    'title="Hỗ trợ khẩn cấp (Đường dây nóng 24/7 & Điểm tựa tĩnh tâm)"'
)
text = text.replace('title="Safety Crisis Support"', 'title="Hỗ trợ khẩn cấp"')
text = text.replace('>SOS Support<', '>Hỗ trợ SOS<')
text = text.replace('SOS  Immediate Support', 'SOS · Hỗ trợ khẩn cấp')
text = text.replace('SOS — Immediate Support', 'SOS · Hỗ trợ khẩn cấp')

# 6. Update Log in & Sign up header buttons
text = text.replace(
    """>
                        Log in
                    </button>""",
    """>
                        Đăng nhập
                    </button>"""
)
text = text.replace(
    """>
                        Sign up
                    </button>""",
    """>
                        Đăng ký
                    </button>"""
)

# 7. Avatar Dropdown Menu Items
text = text.replace('<span id="label-menu-messages">Direct Messages</span>', '<span id="label-menu-messages">Tin nhắn trực tiếp</span>')
text = text.replace('<span id="label-menu-saved">Saved</span>', '<span id="label-menu-saved">Đã lưu</span>')
text = text.replace('<span id="label-menu-library">My Library</span>', '<span id="label-menu-library">Thư viện của tôi</span>')
text = text.replace('<span id="label-menu-account">Account</span>', '<span id="label-menu-account">Tài khoản</span>')
text = text.replace('<span id="label-menu-settings">Settings</span>', '<span id="label-menu-settings">Cài đặt</span>')

# 8. Hide pre-auth language toggles in modals
text = text.replace(
    '<div id="auth-lang-switch-reg" class="flex items-center space-x-1.5 text-xs text-stone-500 bg-stone-100 px-2.5 py-1 rounded-full">',
    '<div id="auth-lang-switch-reg" class="hidden" style="display: none !important;">'
)
text = text.replace(
    '<div id="auth-lang-switch-signin" class="flex items-center space-x-1.5 text-xs text-stone-500 bg-stone-100 px-2.5 py-1 rounded-full">',
    '<div id="auth-lang-switch-signin" class="hidden" style="display: none !important;">'
)

# 9. Register Modal (#modal-register)
text = text.replace('CREATE YOUR TEMPO ACCOUNT', 'TẠO TÀI KHOẢN TEMPO')
text = text.replace('Welcome to Tempo', 'Chào mừng đến với Tempo')
text = text.replace('Manage academic stress, organize deadlines, and find your rhythm.', 'Quản lý căng thẳng học tập, sắp xếp hạn chót và tìm lại nhịp điệu của bạn.')
text = text.replace('Authentication Required', 'Yêu cầu Đăng nhập')
text = text.replace('Sign in or register below to enter Urgent Mode. Your selection will continue directly after.', 'Đăng nhập hoặc đăng ký bên dưới để tiếp tục. Bạn sẽ được chuyển thẳng đến không gian mong muốn.')
text = text.replace('Display name <span class="text-rose-500">*</span>', 'Tên hiển thị <span class="text-rose-500">*</span>')
text = text.replace('placeholder="e.g. Alex or Nguyễn Yến Nhi"', 'placeholder="VD: Alex hoặc Nguyễn Yến Nhi"')
text = text.replace('Email <span class="text-rose-500">*</span>', 'Email <span class="text-rose-500">*</span>')
text = text.replace('Password <span class="text-rose-500">*</span>', 'Mật khẩu <span class="text-rose-500">*</span>')
text = text.replace('placeholder="At least 6 characters"', 'placeholder="Tối thiểu 6 ký tự"')
text = text.replace('Log in with this email →', 'Đăng nhập bằng email này →')
text = text.replace('Create account', 'Tạo tài khoản')
text = text.replace('Already have an account?', 'Đã có tài khoản?')

# 10. Sign In Modal (#modal-signin)
text = text.replace('WELCOME BACK', 'CHÀO MỪNG TRỞ LẠI')
text = text.replace('Welcome Back', 'Chào mừng trở lại')
text = text.replace('Sign in to your Tempo account.', 'Đăng nhập vào tài khoản Tempo của bạn.')
text = text.replace('Forgot password?', 'Quên mật khẩu?')
text = text.replace('Don\'t have an account?', 'Chưa có tài khoản?')

# 11. Mode Switcher Modal (#modal-change-mode)
text = text.replace('TEMPO MODES', 'CÁC CHẾ ĐỘ TEMPO')
text = text.replace('Change Tempo Mode', 'Chuyển Chế độ Tempo')
text = text.replace(
    'A mode changes what Tempo brings forward first. Your tasks, plans, and progress are always preserved.',
    'Mỗi chế độ sẽ ưu tiên những công cụ phù hợp nhất. Công việc, kế hoạch và tiến độ của bạn luôn được bảo toàn.'
)
text = text.replace('⚡ Urgent Mode', '⚡ Chế độ Khẩn cấp')
text = text.replace('Shift to Urgent Mode →', 'Chuyển sang Chế độ Khẩn cấp →')
text = text.replace('Academic Deadline Triage', 'Xử lý Hạn chót Gấp')
text = text.replace(
    'Acute workload triage, feasibility check, and structured execution when deadlines are urgent.',
    'Phân loại công việc gấp, kiểm tra tính khả thi và hành động từng bước khi hạn chót cận kề.'
)
text = text.replace('🌱 Recovery Mode', '🌱 Chế độ Phục hồi')
text = text.replace('Shift to Recovery →', 'Chuyển sang Chế độ Phục hồi →')
text = text.replace('Rebuild Rhythm & Recharge', 'Tái tạo Năng lượng & Nhịp điệu')
text = text.replace(
    'Shift Tempo toward recovery, rebuilding rhythm, and sustainable pacing after heavy pressure.',
    'Giảm nhịp độ, lắng nghe bản thân và thiết lập nhịp điệu bền vững sau những giai đoạn áp lực.'
)
text = text.replace('🧭 Unclear Mode', '🧭 Chế độ Chưa rõ')
text = text.replace('Shift to Unclear →', 'Chuyển sang Chế độ Chưa rõ →')
text = text.replace('Unpack Confusion', 'Gỡ rối Suy nghĩ')
text = text.replace(
    'Shift Tempo toward understanding what you need right now when things feel foggy.',
    'Cùng Tempo làm rõ cảm xúc và xác định điều bạn cần nhất khi mọi thứ dường như mông lung.'
)
text = text.replace('Stay in Urgent Mode', 'Ở lại Chế độ Hiện tại')

# 12. Mode Badge in Navbar (#mode-indicator-shell)
text = text.replace('title="Switch Tempo Mode"', 'title="Chuyển Chế độ Tempo"')

# Preserve pure LF for index.html
text_lf = text.replace('\r\n', '\n')

with open(file_path, 'wb') as f:
    f.write(text_lf.encode('utf-8'))

with open(file_path, 'rb') as f:
    final_bytes = f.read()

final_crlf = final_bytes.count(b'\r\n')
final_lone_lf = final_bytes.count(b'\n') - final_crlf
print(f"index.html updated. Final CRLF: {final_crlf}, lone LF: {final_lone_lf}")
