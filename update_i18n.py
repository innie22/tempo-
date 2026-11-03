import sys

with open('i18n.js', 'rb') as f:
    raw_content = f.read()

# Make sure we use \r\n
crlf = raw_content.count(b'\r\n')
lf = raw_content.count(b'\n') - crlf
print(f"Original i18n.js line endings: CRLF={crlf}, lone-LF={lf}")

content = raw_content.decode('utf-8')

vi_insertion = """                    viewAll: "Xem tất cả",
                    onboarding: {
                        badge: "CHẾ ĐỘ HỒI PHỤC",
                        badgeReturning: "CHẾ ĐỘ HỒI PHỤC · CHÀO MỪNG QUAY LẠI",
                        badgeReview: "CHẾ ĐỘ HỒI PHỤC · XEM LẠI HỆ THỐNG THEO DÕI",
                        case1Title: "Chào mừng bạn đến với Chế độ Hồi phục",
                        case1Purpose: "Dành cho bản thân không gian để xả hơi và phục hồi.",
                        case1Benefits: "Chế độ Hồi phục giúp bạn giảm bớt áp lực, nhận diện những điều hữu ích và tái tạo lại nhịp điệu sinh hoạt bền vững.",
                        case1Question: "Bạn đã sẵn sàng thiết lập Hệ thống Theo dõi của mình chưa?",
                        case1QuestionSub: "Chọn một vài điều bạn muốn quan sát mỗi ngày. Bạn có thể thay đổi bất cứ lúc nào.",
                        case1Yes: "Có, hãy thiết lập ngay →",
                        case1Later: "Để sau",
                        case2Title: "Chào mừng bạn quay lại!",
                        case2Question: "Bạn có muốn xem lại Hệ thống Theo dõi của mình không?",
                        case2Summary: "Bạn hiện có {count} mục đang theo dõi hoạt động.",
                        case2SummaryEmpty: "Bạn hiện không có mục theo dõi hoạt động nào. Lịch sử theo dõi trước đây được lưu trữ an toàn trong kho lưu trữ.",
                        case2Yes: "Có, xem lại hệ thống →",
                        case2No: "Không, về Dashboard",
                        reviewTitle: "Hệ thống Theo dõi của bạn",
                        reviewSubtitle: "Xem lại các mục theo dõi hiện tại của bạn bên dưới. Bạn có thể giữ nguyên hệ thống hoặc điều chỉnh từng mục.",
                        reviewActiveItems: "Các mục theo dõi đang hoạt động ({count})",
                        reviewNoActive: "Hiện chưa có mục theo dõi nào đang hoạt động.",
                        reviewHistoricalPreserved: "Lịch sử điểm danh và các mục đã lưu trữ vẫn được bảo toàn an toàn trong kho lưu trữ.",
                        optionATitle: "Lựa chọn A – Giữ nguyên hệ thống hiện tại",
                        optionADesc: "Giữ nguyên tất cả các mục theo dõi và cấu hình hiện có. Không ghi đè hay đặt lại lịch sử. Tiếp tục vào Tự kiểm tra.",
                        optionABtn: "Giữ nguyên hệ thống →",
                        optionBTitle: "Lựa chọn B – Điều chỉnh hệ thống",
                        optionBDesc: "Giữ hoặc bỏ bớt mục, thay đổi cách theo dõi hoặc thêm mục mới. Dữ liệu lịch sử của các mục không đổi được giữ nguyên an toàn.",
                        optionBBtn: "Điều chỉnh hệ thống →",
                        backToDashboard: "Quay lại Dashboard",
                        back: "← Quay lại",
                        toastKeepSuccess: "Đã giữ nguyên hệ thống theo dõi.",
                        toastSaveSuccess: "Đã lưu thay đổi hệ thống theo dõi."
                    }
                },""".replace('\n', '\r\n')

en_insertion = """                    viewAll: "View all",
                    onboarding: {
                        badge: "RECOVERY MODE",
                        badgeReturning: "RECOVERY MODE · WELCOME BACK",
                        badgeReview: "RECOVERY MODE · TRACKING SYSTEM REVIEW",
                        case1Title: "Welcome to Rmode",
                        case1Purpose: "Give yourself some space to decompress and recover.",
                        case1Benefits: "Rmode helps you slow down, notice what supports your nervous system, and rebuild a sustainable daily rhythm.",
                        case1Question: "Are you ready to set up your Tracking System?",
                        case1QuestionSub: "Choose a few things that feel useful to observe. You can adjust them anytime.",
                        case1Yes: "Yes, let's set it up →",
                        case1Later: "Later",
                        case2Title: "Welcome back!",
                        case2Question: "Would you like to review your Tracking System?",
                        case2Summary: "You currently have {count} active tracking item{s}.",
                        case2SummaryEmpty: "You currently have 0 active items. Your past tracking records are safely preserved in archive.",
                        case2Yes: "Yes, review my system →",
                        case2No: "No, go to dashboard",
                        reviewTitle: "Your Tracking System",
                        reviewSubtitle: "Review your active tracking items below. You can keep your system as is, or adjust individual items.",
                        reviewActiveItems: "Active Tracking Items ({count})",
                        reviewNoActive: "No tracking items are currently active.",
                        reviewHistoricalPreserved: "Past check-in records and archived items remain safe in your archive.",
                        optionATitle: "Option A – Keep current system",
                        optionADesc: "Keep all existing tracking items and configurations. Does not overwrite or reset history. Continue to Self-check tool.",
                        optionABtn: "Keep current system →",
                        optionBTitle: "Option B – Adjust my system",
                        optionBDesc: "Keep or remove items, update tracking methods, or add new items. Historical records for unchanged items are safely preserved.",
                        optionBBtn: "Adjust my system →",
                        backToDashboard: "Return to Dashboard",
                        back: "← Back",
                        toastKeepSuccess: "Current tracking system preserved.",
                        toastSaveSuccess: "Tracking system updated successfully."
                    }
                },""".replace('\n', '\r\n')

target_vi = '                    viewAll: "Xem tất cả"\r\n                },'
target_en = '                    viewAll: "View all"\r\n                },'

if target_vi not in content or target_en not in content:
    print("ERROR: Target patterns not found in content!")
    sys.exit(1)

content = content.replace(target_vi, vi_insertion, 1)
content = content.replace(target_en, en_insertion, 1)

with open('i18n.js', 'wb') as f:
    f.write(content.encode('utf-8'))

with open('i18n.js', 'rb') as f:
    new_raw = f.read()

new_crlf = new_raw.count(b'\r\n')
new_lf = new_raw.count(b'\n') - new_crlf
print(f"Updated i18n.js line endings: CRLF={new_crlf}, lone-LF={new_lf}")
print("Successfully updated i18n.js")
