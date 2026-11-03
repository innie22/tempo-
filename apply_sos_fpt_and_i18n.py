# -*- coding: utf-8 -*-
import sys

def update_emergency_support_js():
    with open('emergencySupport.js', 'r', encoding='utf-8') as f:
        content = f.read()

    content_norm = content.replace('\r\n', '\n')

    # Add fptCounseling to supportConfig
    old_config = '''        ngayMaiHotline: {
            title_vi: 'ĐƯỜNG DÂY NÓNG NGÀY MAI',
            title_en: 'NGÀY MAI SUPPORT HOTLINE',
            badge_vi: 'Hỗ trợ tâm lý',
            badge_en: 'Mental Health Support',
            phone: '096 306 1414',
            callHref: 'tel:0963061414',
            details_vi: "Hỗ trợ tâm lý miễn phí qua điện thoại cho người đang gặp khủng hoảng tâm lý, trầm cảm và người thân của họ. Lắng nghe không phán xét, bảo mật thông tin.",
            details_en: "Free psychological first aid by phone for people experiencing emotional distress or depression, and their loved ones. Confidential and non-judgmental support.",
            hours_vi: "13:00 – 20:30, Thứ Tư – Chủ Nhật",
            hours_en: "1:00 PM – 8:30 PM, Wednesday – Sunday",
            cta_vi: "Gọi 096 306 1414",
            cta_en: "Call 096 306 1414"
        },'''

    new_config = '''        ngayMaiHotline: {
            title_vi: 'ĐƯỜNG DÂY NÓNG NGÀY MAI',
            title_en: 'NGÀY MAI SUPPORT HOTLINE',
            badge_vi: 'Hỗ trợ tâm lý',
            badge_en: 'Mental Health Support',
            phone: '096 306 1414',
            callHref: 'tel:0963061414',
            details_vi: "Hỗ trợ tâm lý miễn phí qua điện thoại cho người đang gặp khủng hoảng tâm lý, trầm cảm và người thân của họ. Lắng nghe không phán xét, bảo mật thông tin.",
            details_en: "Free psychological first aid by phone for people experiencing emotional distress or depression, and their loved ones. Confidential and non-judgmental support.",
            hours_vi: "13:00 – 20:30, Thứ Tư – Chủ Nhật",
            hours_en: "1:00 PM – 8:30 PM, Wednesday – Sunday",
            cta_vi: "Gọi 096 306 1414",
            cta_en: "Call 096 306 1414"
        },
        fptCounseling: {
            title_vi: 'Phòng Tư vấn tâm lý – Đại học FPT',
            title_en: 'FPT University Psychological Counseling Office',
            email: 'tuvansinhvien@fpt.edu.vn',
            emailHref: 'mailto:tuvansinhvien@fpt.edu.vn',
            details_vi: 'Dịch vụ tư vấn tâm lý miễn phí và bảo mật dành cho sinh viên Đại học FPT.',
            details_en: 'Free and confidential psychological counseling services for FPT University students.',
            cta_vi: 'Gửi email tư vấn',
            cta_en: 'Send counseling email'
        },'''

    assert old_config in content_norm, "old_config not found in emergencySupport.js"
    content_norm = content_norm.replace(old_config, new_config)

    # Update closingReassurance_vi
    old_reass = 'closingReassurance_vi: "Bạn không cần giải quyết mọi thứ ngay lúc này. Lúc này, chỉ cần ưu tiên giữ an toàn cho bản thân.",'
    new_reass = 'closingReassurance_vi: "Bạn không cần giải quyết mọi thứ ngay lúc này. Lúc này, chỉ cần tập trung giữ an toàn cho bản thân.",'
    if old_reass in content_norm:
        content_norm = content_norm.replace(old_reass, new_reass)

    old_act3_reass = '<p class="text-[#6F6B68]">${isVi() ? \'Lúc này, chỉ cần ưu tiên giữ an toàn cho bản thân.\' : \'For now, just focus on staying safe.\'}</p>'
    new_act3_reass = '<p class="text-[#6F6B68]">${isVi() ? \'Lúc này, chỉ cần tập trung giữ an toàn cho bản thân.\' : \'For now, just focus on staying safe.\'}</p>'
    if old_act3_reass in content_norm:
        content_norm = content_norm.replace(old_act3_reass, new_act3_reass)

    content_crlf = content_norm.replace('\n', '\r\n')
    with open('emergencySupport.js', 'wb') as f:
        f.write(content_crlf.encode('utf-8'))
    print("emergencySupport.js updated successfully.")

def update_i18n_js():
    with open('i18n.js', 'r', encoding='utf-8') as f:
        content = f.read()

    content_norm = content.replace('\r\n', '\n')

    # 1. Update vi.sos
    old_vi_sos_block = '''                drawerTitle: "Nhận hỗ trợ ngay",
                drawerSubtitle: "Nếu bạn cảm thấy không an toàn, đừng ở một mình. Hãy ở cùng người bạn tin cậy và tìm kiếm sự hỗ trợ ngay bây giờ.",
                medicalTitle: "Hỗ trợ Y tế Khẩn cấp",
                medicalDesc: "Nếu bạn có nguy cơ tự làm hại bản thân ngay lập tức hoặc đang trong tình huống nguy hiểm.",
                medicalCall: "Gọi 115 ngay",
                hotlineTitle: "Đường dây nóng Khủng hoảng & Hỗ trợ Tâm lý HOPE",
                hotlineDesc: "Nếu bạn đang trong cơn khủng hoảng, có suy nghĩ tự hại hoặc cần người lắng nghe ngay bây giờ.",
                hotlineCall: "Gọi 0865 044 400",
                ngayMaiTitle: "ĐƯỜNG DÂY NÓNG NGÀY MAI",
                ngayMaiBadge: "Hỗ trợ tâm lý",
                ngayMaiPhone: "096 306 1414",
                ngayMaiDesc: "Hỗ trợ tâm lý miễn phí qua điện thoại cho người đang gặp khủng hoảng tâm lý, trầm cảm và người thân của họ. Lắng nghe không phán xét, bảo mật thông tin.",
                ngayMaiHours: "13:00 – 20:30, Thứ Tư – Chủ Nhật",
                ngayMaiCall: "Gọi 096 306 1414",
                waitingHeader: "Khi bạn đang chờ được hỗ trợ",
                action1: "Ở cùng một người bạn tin tưởng.",
                action2: "Di chuyển đến một nơi an toàn hơn.",
                action3: "Tạo khoảng cách với những vật có thể gây tổn thương cho bạn.",
                reassurance: "Bạn không cần giải quyết mọi thứ ngay lúc này. Lúc này, chỉ cần tập trung giữ an toàn cho bản thân.",
                copyTrustedBtn: "Sao chép tin nhắn",
                closeSOS: "Đóng cửa sổ hỗ trợ",
                copySuccessToast: "Đã sao chép tin nhắn! Bạn có thể dán và gửi cho bạn bè hoặc người thân."'''

    new_vi_sos_block = '''                drawerTitle: "Nhận hỗ trợ ngay",
                drawerSubtitle: "Nếu bạn cảm thấy không an toàn, đừng ở một mình.",
                drawerSubtitleDesc: "Hãy ở cùng người bạn tin cậy và tìm kiếm sự hỗ trợ ngay bây giờ.",
                medicalTitle: "Hỗ trợ Y tế Khẩn cấp",
                medicalBadge: "Khẩn cấp",
                medicalDesc: "Nếu bạn có nguy cơ tự làm hại bản thân ngay lập tức hoặc đang trong tình huống nguy hiểm.",
                medicalCall: "Gọi 115 ngay",
                hotlineTitle: "Đường dây nóng Khủng hoảng & Hỗ trợ Tâm lý HOPE",
                hotlineBadge: "Hỗ trợ khủng hoảng",
                hotlineDesc: "Nếu bạn đang trong cơn khủng hoảng, có suy nghĩ tự hại hoặc cần người lắng nghe ngay bây giờ.",
                hotlineCall: "Gọi 0865 044 400",
                ngayMaiTitle: "ĐƯỜNG DÂY NÓNG NGÀY MAI",
                ngayMaiBadge: "Hỗ trợ tâm lý",
                ngayMaiPhone: "096 306 1414",
                ngayMaiDesc: "Hỗ trợ tâm lý miễn phí qua điện thoại cho người đang gặp khủng hoảng tâm lý, trầm cảm và người thân của họ. Lắng nghe không phán xét, bảo mật thông tin.",
                ngayMaiHours: "13:00 – 20:30, Thứ Tư – Chủ Nhật",
                ngayMaiCall: "Gọi 096 306 1414",
                waitingHeader: "KHI BẠN ĐANG CHỜ ĐƯỢC HỖ TRỢ",
                action1: "Ở cùng một người bạn tin tưởng.",
                action2: "Di chuyển đến một nơi an toàn hơn.",
                action3: "Tạo khoảng cách với những vật có thể gây tổn thương cho bạn.",
                waitingReassTitle: "Bạn không cần giải quyết mọi thứ ngay lúc này.",
                reassurance: "Lúc này, chỉ cần tập trung giữ an toàn cho bản thân.",
                trustedTitle: "Liên hệ với người bạn tin tưởng",
                trustedDesc: "Bạn có thể sao chép tin nhắn này để gửi cho bạn bè hoặc người thân:",
                trustedQuote: "Chào bạn, mình đang trải qua một khoảng thời gian rất khó khăn và cảm thấy quá tải. Bạn có thể trò chuyện hoặc ngồi cùng mình một lúc được không?",
                copyTrustedBtn: "Sao chép tin nhắn",
                campusTitle: "HỖ TRỢ SỨC KHỎE TINH THẦN SINH VIÊN",
                campusBadge: "Hỗ trợ trong giờ làm việc",
                campusDesc: "Trong trường hợp khẩn cấp hoặc nguy hiểm tức thời, hãy gọi 115 hoặc 0865 044 400. Nếu bạn cần trao đổi về các vấn đề tâm lý không khẩn cấp, bạn có thể liên hệ với bộ phận hỗ trợ sinh viên trong giờ làm việc.",
                fptTitle: "Phòng Tư vấn tâm lý – Đại học FPT",
                fptDesc: "Dịch vụ tư vấn tâm lý miễn phí và bảo mật dành cho sinh viên Đại học FPT.",
                fptEmail: "tuvansinhvien@fpt.edu.vn",
                fptCta: "Gửi email tư vấn",
                offlineContactPlaceholder: "Họ tên hoặc email sinh viên (không bắt buộc)",
                offlineMsgPlaceholder: "Mô tả vấn đề hoặc nội dung bạn muốn gửi đến phòng tư vấn",
                offlineSubmitBtn: "Gửi tin nhắn cho bộ phận hỗ trợ",
                offlineSuccessMsg: "Tin nhắn đã được lưu. Bộ phận hỗ trợ sẽ phản hồi trong giờ làm việc. Nếu cần giúp đỡ ngay lập tức, hãy gọi 115 hoặc 0865 044 400.",
                closeSOS: "Đóng cửa sổ hỗ trợ",
                copySuccessToast: "Đã sao chép tin nhắn! Bạn có thể dán và gửi cho bạn bè hoặc người thân."'''

    assert old_vi_sos_block in content_norm, "old_vi_sos_block not found in i18n.js"
    content_norm = content_norm.replace(old_vi_sos_block, new_vi_sos_block)

    # 2. Update en.sos
    old_en_sos_block = '''                drawerTitle: "Get Support Now",
                drawerSubtitle: "If you don't feel safe, don't stay alone. Stay with someone you trust and reach out for support now.",
                medicalTitle: "Emergency Medical Support",
                medicalDesc: "If you're at immediate risk of hurting yourself or you're in immediate danger.",
                medicalCall: "Call 115 Now",
                hotlineTitle: "HOPE — Suicide Prevention Hotline",
                hotlineDesc: "If you're in crisis, having thoughts of hurting yourself, or need someone to support you right now.",
                hotlineCall: "Call 0865 044 400",
                ngayMaiTitle: "NGÀY MAI SUPPORT HOTLINE",
                ngayMaiBadge: "Mental Health Support",
                ngayMaiPhone: "096 306 1414",
                ngayMaiDesc: "Free psychological first aid by phone for people experiencing emotional distress or depression, and their loved ones. Confidential and non-judgmental support.",
                ngayMaiHours: "1:00 PM – 8:30 PM, Wednesday – Sunday",
                ngayMaiCall: "Call 096 306 1414",
                waitingHeader: "While you're waiting for support",
                action1: "Stay with someone you trust.",
                action2: "Move somewhere safer.",
                action3: "Create distance from anything that could hurt you.",
                reassurance: "You don't need to solve everything right now. For now, just focus on staying safe.",
                copyTrustedBtn: "Copy Message",
                closeSOS: "Close Support Drawer"'''

    new_en_sos_block = '''                drawerTitle: "Get Support Now",
                drawerSubtitle: "If you don't feel safe, don't stay alone.",
                drawerSubtitleDesc: "Stay with someone you trust and reach out for support now.",
                medicalTitle: "Emergency Medical Support",
                medicalBadge: "Emergency",
                medicalDesc: "If you're at immediate risk of hurting yourself or you're in immediate danger.",
                medicalCall: "Call 115 Now",
                hotlineTitle: "HOPE — Suicide Prevention Hotline",
                hotlineBadge: "Crisis Support",
                hotlineDesc: "If you're in crisis, having thoughts of hurting yourself, or need someone to support you right now.",
                hotlineCall: "Call 0865 044 400",
                ngayMaiTitle: "NGÀY MAI SUPPORT HOTLINE",
                ngayMaiBadge: "Mental Health Support",
                ngayMaiPhone: "096 306 1414",
                ngayMaiDesc: "Free psychological first aid by phone for people experiencing emotional distress or depression, and their loved ones. Confidential and non-judgmental support.",
                ngayMaiHours: "1:00 PM – 8:30 PM, Wednesday – Sunday",
                ngayMaiCall: "Call 096 306 1414",
                waitingHeader: "While you're waiting for support",
                action1: "Stay with someone you trust.",
                action2: "Move somewhere safer.",
                action3: "Create distance from anything that could hurt you.",
                waitingReassTitle: "You don't need to solve everything right now.",
                reassurance: "For now, just focus on staying safe.",
                trustedTitle: "Reach Out to Someone You Trust:",
                trustedDesc: "Copy this simple message to reach out to a friend or family member:",
                trustedQuote: "Hey, I'm having a really difficult time right now and feeling overwhelmed. Are you free to talk or sit with me for a few minutes?",
                copyTrustedBtn: "Copy Message",
                campusTitle: "Campus Student Wellbeing",
                campusBadge: "Office Hours Support",
                campusDesc: "For immediate crisis or danger, call 115 or 0865 044 400. For non-urgent campus advising questions during office hours:",
                fptTitle: "FPT University Psychological Counseling Office",
                fptDesc: "Free and confidential psychological counseling services for FPT University students.",
                fptEmail: "tuvansinhvien@fpt.edu.vn",
                fptCta: "Send counseling email",
                offlineContactPlaceholder: "Your name or student email (optional)",
                offlineMsgPlaceholder: "Describe your question or message for office hours...",
                offlineSubmitBtn: "Leave Message for Campus Staff",
                offlineSuccessMsg: "Message saved. Staff will respond during normal hours. For immediate help, call 115 or 0865 044 400.",
                closeSOS: "Close Support Drawer"'''

    assert old_en_sos_block in content_norm, "old_en_sos_block not found in i18n.js"
    content_norm = content_norm.replace(old_en_sos_block, new_en_sos_block)

    # 3. Update applyLanguageToDOM
    old_dom_block = '''        // Support Drawer Reactive Texts
        const drawerTitle = document.getElementById('drawer-title');
        if (drawerTitle) drawerTitle.textContent = t('sos.drawerTitle');
        const drawerSubtitle = document.getElementById('drawer-subtitle');
        if (drawerSubtitle) drawerSubtitle.textContent = t('sos.drawerSubtitle');

        const drawerMedTitle = document.getElementById('drawer-medical-title');
        if (drawerMedTitle) drawerMedTitle.textContent = t('sos.medicalTitle');
        const drawerMedDesc = document.getElementById('drawer-medical-desc');
        if (drawerMedDesc) drawerMedDesc.textContent = t('sos.medicalDesc');
        const drawerMedCall = document.getElementById('drawer-medical-call');
        if (drawerMedCall) drawerMedCall.textContent = t('sos.medicalCall');

        const drawerHotlineTitle = document.getElementById('drawer-hotline-title');
        if (drawerHotlineTitle) drawerHotlineTitle.textContent = t('sos.hotlineTitle');
        const drawerHotlineDesc = document.getElementById('drawer-hotline-desc');
        if (drawerHotlineDesc) drawerHotlineDesc.textContent = t('sos.hotlineDesc');
        const drawerHotlineCall = document.getElementById('drawer-hotline-call');
        if (drawerHotlineCall) drawerHotlineCall.textContent = t('sos.hotlineCall');

        const drawerNgayMaiTitle = document.getElementById('drawer-ngaymai-title');
        if (drawerNgayMaiTitle) drawerNgayMaiTitle.textContent = t('sos.ngayMaiTitle');
        const drawerNgayMaiBadge = document.getElementById('drawer-ngaymai-badge');
        if (drawerNgayMaiBadge) drawerNgayMaiBadge.textContent = t('sos.ngayMaiBadge');
        const drawerNgayMaiDesc = document.getElementById('drawer-ngaymai-desc');
        if (drawerNgayMaiDesc) drawerNgayMaiDesc.textContent = t('sos.ngayMaiDesc');
        const drawerNgayMaiHours = document.getElementById('drawer-ngaymai-hours');
        if (drawerNgayMaiHours) drawerNgayMaiHours.textContent = t('sos.ngayMaiHours');
        const drawerNgayMaiCall = document.getElementById('drawer-ngaymai-call');
        if (drawerNgayMaiCall) drawerNgayMaiCall.textContent = t('sos.ngayMaiCall');

        const step5aNgayMaiTitle = document.getElementById('step5a-ngaymai-title');
        if (step5aNgayMaiTitle) step5aNgayMaiTitle.textContent = t('sos.ngayMaiTitle');
        const step5aNgayMaiBadge = document.getElementById('step5a-ngaymai-badge');
        if (step5aNgayMaiBadge) step5aNgayMaiBadge.textContent = t('sos.ngayMaiBadge');
        const step5aNgayMaiDesc = document.getElementById('step5a-ngaymai-desc');
        if (step5aNgayMaiDesc) step5aNgayMaiDesc.textContent = t('sos.ngayMaiDesc');
        const step5aNgayMaiHours = document.getElementById('step5a-ngaymai-hours');
        if (step5aNgayMaiHours) step5aNgayMaiHours.textContent = t('sos.ngayMaiHours');
        const step5aNgayMaiCall = document.getElementById('step5a-ngaymai-call');
        if (step5aNgayMaiCall) step5aNgayMaiCall.textContent = t('sos.ngayMaiCall');

        const drawerWaitHeader = document.getElementById('drawer-waiting-header');
        if (drawerWaitHeader) drawerWaitHeader.textContent = t('sos.waitingHeader');
        const drawerWait1 = document.getElementById('drawer-waiting-action-1');
        if (drawerWait1) drawerWait1.textContent = t('sos.action1');
        const drawerWait2 = document.getElementById('drawer-waiting-action-2');
        if (drawerWait2) drawerWait2.textContent = t('sos.action2');
        const drawerWait3 = document.getElementById('drawer-waiting-action-3');
        if (drawerWait3) drawerWait3.textContent = t('sos.action3');
        const drawerWaitReass = document.getElementById('drawer-waiting-reassurance');
        if (drawerWaitReass) drawerWaitReass.textContent = t('sos.reassurance');

        const drawerCopyBtn = document.getElementById('drawer-copy-btn-text');
        if (drawerCopyBtn) drawerCopyBtn.textContent = t('sos.copyTrustedBtn');
        const drawerQuote = document.getElementById('drawer-trusted-quote');
        if (drawerQuote) {
            drawerQuote.textContent = currentLang === 'vi'
                ? '"Chào bạn, mình đang trải qua một khoảng thời gian rất khó khăn và cảm thấy quá tải. Bạn có thể trò chuyện hoặc ngồi cùng mình một lúc được không?"'
                : '"Hey, I\\'m having a really difficult time right now and feeling overwhelmed. Are you free to talk or sit with me for a few minutes?"';
        }
        const drawerCloseBtn = document.getElementById('drawer-close-btn-text');
        if (drawerCloseBtn) drawerCloseBtn.textContent = t('sos.closeSOS');'''

    new_dom_block = '''        // Support Drawer Reactive Texts
        const drawerTitle = document.getElementById('drawer-title');
        if (drawerTitle) drawerTitle.textContent = t('sos.drawerTitle');
        const drawerSubtitle = document.getElementById('drawer-subtitle');
        if (drawerSubtitle) drawerSubtitle.textContent = t('sos.drawerSubtitle');
        const drawerSubtitleDesc = document.getElementById('drawer-subtitle-desc');
        if (drawerSubtitleDesc) drawerSubtitleDesc.textContent = t('sos.drawerSubtitleDesc');

        const drawerMedTitle = document.getElementById('drawer-medical-title');
        if (drawerMedTitle) drawerMedTitle.textContent = t('sos.medicalTitle');
        const drawerMedBadge = document.getElementById('drawer-medical-badge');
        if (drawerMedBadge) drawerMedBadge.textContent = t('sos.medicalBadge');
        const drawerMedDesc = document.getElementById('drawer-medical-desc');
        if (drawerMedDesc) drawerMedDesc.textContent = t('sos.medicalDesc');
        const drawerMedCall = document.getElementById('drawer-medical-call');
        if (drawerMedCall) drawerMedCall.textContent = t('sos.medicalCall');

        const drawerHotlineTitle = document.getElementById('drawer-hotline-title');
        if (drawerHotlineTitle) drawerHotlineTitle.textContent = t('sos.hotlineTitle');
        const drawerHotlineBadge = document.getElementById('drawer-hotline-badge');
        if (drawerHotlineBadge) drawerHotlineBadge.textContent = t('sos.hotlineBadge');
        const drawerHotlineDesc = document.getElementById('drawer-hotline-desc');
        if (drawerHotlineDesc) drawerHotlineDesc.textContent = t('sos.hotlineDesc');
        const drawerHotlineCall = document.getElementById('drawer-hotline-call');
        if (drawerHotlineCall) drawerHotlineCall.textContent = t('sos.hotlineCall');

        const drawerNgayMaiTitle = document.getElementById('drawer-ngaymai-title');
        if (drawerNgayMaiTitle) drawerNgayMaiTitle.textContent = t('sos.ngayMaiTitle');
        const drawerNgayMaiBadge = document.getElementById('drawer-ngaymai-badge');
        if (drawerNgayMaiBadge) drawerNgayMaiBadge.textContent = t('sos.ngayMaiBadge');
        const drawerNgayMaiDesc = document.getElementById('drawer-ngaymai-desc');
        if (drawerNgayMaiDesc) drawerNgayMaiDesc.textContent = t('sos.ngayMaiDesc');
        const drawerNgayMaiHours = document.getElementById('drawer-ngaymai-hours');
        if (drawerNgayMaiHours) drawerNgayMaiHours.textContent = t('sos.ngayMaiHours');
        const drawerNgayMaiCall = document.getElementById('drawer-ngaymai-call');
        if (drawerNgayMaiCall) drawerNgayMaiCall.textContent = t('sos.ngayMaiCall');

        const step5aNgayMaiTitle = document.getElementById('step5a-ngaymai-title');
        if (step5aNgayMaiTitle) step5aNgayMaiTitle.textContent = t('sos.ngayMaiTitle');
        const step5aNgayMaiBadge = document.getElementById('step5a-ngaymai-badge');
        if (step5aNgayMaiBadge) step5aNgayMaiBadge.textContent = t('sos.ngayMaiBadge');
        const step5aNgayMaiDesc = document.getElementById('step5a-ngaymai-desc');
        if (step5aNgayMaiDesc) step5aNgayMaiDesc.textContent = t('sos.ngayMaiDesc');
        const step5aNgayMaiHours = document.getElementById('step5a-ngaymai-hours');
        if (step5aNgayMaiHours) step5aNgayMaiHours.textContent = t('sos.ngayMaiHours');
        const step5aNgayMaiCall = document.getElementById('step5a-ngaymai-call');
        if (step5aNgayMaiCall) step5aNgayMaiCall.textContent = t('sos.ngayMaiCall');

        const drawerWaitHeader = document.getElementById('drawer-waiting-header');
        if (drawerWaitHeader) drawerWaitHeader.textContent = t('sos.waitingHeader');
        const drawerWait1 = document.getElementById('drawer-waiting-action-1');
        if (drawerWait1) drawerWait1.textContent = t('sos.action1');
        const drawerWait2 = document.getElementById('drawer-waiting-action-2');
        if (drawerWait2) drawerWait2.textContent = t('sos.action2');
        const drawerWait3 = document.getElementById('drawer-waiting-action-3');
        if (drawerWait3) drawerWait3.textContent = t('sos.action3');
        const drawerWaitReassTitle = document.getElementById('drawer-waiting-reass-title');
        if (drawerWaitReassTitle) drawerWaitReassTitle.textContent = t('sos.waitingReassTitle');
        const drawerWaitReass = document.getElementById('drawer-waiting-reassurance');
        if (drawerWaitReass) drawerWaitReass.textContent = t('sos.reassurance');

        // Step 5A waiting guidance
        const step5aWaitHeader = document.getElementById('step5a-waiting-header');
        if (step5aWaitHeader) step5aWaitHeader.textContent = t('sos.waitingHeader');
        const step5aWait1 = document.getElementById('step5a-waiting-action-1');
        if (step5aWait1) step5aWait1.textContent = t('sos.action1');
        const step5aWait2 = document.getElementById('step5a-waiting-action-2');
        if (step5aWait2) step5aWait2.textContent = t('sos.action2');
        const step5aWait3 = document.getElementById('step5a-waiting-action-3');
        if (step5aWait3) step5aWait3.textContent = t('sos.action3');
        const step5aWaitReassTitle = document.getElementById('step5a-waiting-reass-title');
        if (step5aWaitReassTitle) step5aWaitReassTitle.textContent = t('sos.waitingReassTitle');
        const step5aWaitReass = document.getElementById('step5a-waiting-reassurance');
        if (step5aWaitReass) step5aWaitReass.textContent = t('sos.reassurance');

        // Trusted Contact Card
        const drawerTrustedTitle = document.getElementById('drawer-trusted-title');
        if (drawerTrustedTitle) drawerTrustedTitle.textContent = t('sos.trustedTitle');
        const drawerTrustedDesc = document.getElementById('drawer-trusted-desc');
        if (drawerTrustedDesc) drawerTrustedDesc.textContent = t('sos.trustedDesc');
        const drawerCopyBtn = document.getElementById('drawer-copy-btn-text');
        if (drawerCopyBtn) drawerCopyBtn.textContent = t('sos.copyTrustedBtn');
        const drawerQuote = document.getElementById('drawer-trusted-quote');
        if (drawerQuote) {
            drawerQuote.textContent = '"' + t('sos.trustedQuote') + '"';
        }

        // Campus Student Wellbeing Card & FPT Counseling Office
        const drawerCampusTitle = document.getElementById('drawer-campus-title');
        if (drawerCampusTitle) drawerCampusTitle.textContent = t('sos.campusTitle');
        const drawerCampusBadge = document.getElementById('drawer-campus-badge');
        if (drawerCampusBadge) drawerCampusBadge.textContent = t('sos.campusBadge');
        const drawerCampusDesc = document.getElementById('drawer-campus-desc');
        if (drawerCampusDesc) {
            drawerCampusDesc.innerHTML = currentLang === 'vi'
                ? 'Trong trường hợp khẩn cấp hoặc nguy hiểm tức thời, hãy gọi <strong>115</strong> hoặc <strong>0865 044 400</strong>. Nếu bạn cần trao đổi về các vấn đề tâm lý không khẩn cấp, bạn có thể liên hệ với bộ phận hỗ trợ sinh viên trong giờ làm việc.'
                : 'For immediate crisis or danger, call <strong>115</strong> or <strong>0865 044 400</strong>. For non-urgent campus advising questions during office hours:';
        }

        const drawerFptTitle = document.getElementById('drawer-fpt-title');
        if (drawerFptTitle) drawerFptTitle.textContent = t('sos.fptTitle');
        const drawerFptDesc = document.getElementById('drawer-fpt-desc');
        if (drawerFptDesc) drawerFptDesc.textContent = t('sos.fptDesc');
        const drawerFptCtaText = document.getElementById('drawer-fpt-cta-text');
        if (drawerFptCtaText) drawerFptCtaText.textContent = t('sos.fptCta');

        const drawerOfflineContact = document.getElementById('drawer-offline-contact');
        if (drawerOfflineContact) drawerOfflineContact.setAttribute('placeholder', t('sos.offlineContactPlaceholder'));
        const drawerOfflineMessage = document.getElementById('drawer-offline-message');
        if (drawerOfflineMessage) drawerOfflineMessage.setAttribute('placeholder', t('sos.offlineMsgPlaceholder'));
        const drawerOfflineBtnText = document.getElementById('drawer-offline-btn-text');
        if (drawerOfflineBtnText) drawerOfflineBtnText.textContent = t('sos.offlineSubmitBtn');
        const drawerOfflineSuccess = document.getElementById('drawer-offline-success');
        if (drawerOfflineSuccess) drawerOfflineSuccess.textContent = t('sos.offlineSuccessMsg');

        // Step 5A Campus & FPT
        const step5aCampusTitle = document.getElementById('step5a-campus-title');
        if (step5aCampusTitle) step5aCampusTitle.textContent = t('sos.campusTitle');
        const step5aCampusBadge = document.getElementById('step5a-campus-badge');
        if (step5aCampusBadge) step5aCampusBadge.textContent = t('sos.campusBadge');
        const step5aCampusDesc = document.getElementById('step5a-campus-desc');
        if (step5aCampusDesc) {
            step5aCampusDesc.innerHTML = currentLang === 'vi'
                ? 'Trong trường hợp khẩn cấp hoặc nguy hiểm tức thời, hãy gọi <strong>115</strong> hoặc <strong>0865 044 400</strong>. Nếu bạn cần trao đổi về các vấn đề tâm lý không khẩn cấp, bạn có thể liên hệ với bộ phận hỗ trợ sinh viên trong giờ làm việc.'
                : 'For immediate crisis or danger, call <strong>115</strong> or <strong>0865 044 400</strong>. For non-urgent campus advising questions during office hours:';
        }

        const step5aFptTitle = document.getElementById('step5a-fpt-title');
        if (step5aFptTitle) step5aFptTitle.textContent = t('sos.fptTitle');
        const step5aFptDesc = document.getElementById('step5a-fpt-desc');
        if (step5aFptDesc) step5aFptDesc.textContent = t('sos.fptDesc');
        const step5aFptCtaText = document.getElementById('step5a-fpt-cta-text');
        if (step5aFptCtaText) step5aFptCtaText.textContent = t('sos.fptCta');

        const step5aOfflineContact = document.getElementById('step5a-offline-contact');
        if (step5aOfflineContact) step5aOfflineContact.setAttribute('placeholder', t('sos.offlineContactPlaceholder'));
        const step5aOfflineMessage = document.getElementById('step5a-offline-message');
        if (step5aOfflineMessage) step5aOfflineMessage.setAttribute('placeholder', t('sos.offlineMsgPlaceholder'));
        const step5aOfflineBtnText = document.getElementById('step5a-offline-btn-text');
        if (step5aOfflineBtnText) step5aOfflineBtnText.textContent = t('sos.offlineSubmitBtn');
        const step5aOfflineSuccess = document.getElementById('step5a-offline-success');
        if (step5aOfflineSuccess) step5aOfflineSuccess.textContent = t('sos.offlineSuccessMsg');

        const drawerCloseBtn = document.getElementById('drawer-close-btn-text');
        if (drawerCloseBtn) drawerCloseBtn.textContent = t('sos.closeSOS');'''

    assert old_dom_block in content_norm, "old_dom_block not found in i18n.js"
    content_norm = content_norm.replace(old_dom_block, new_dom_block)

    content_crlf = content_norm.replace('\n', '\r\n')
    with open('i18n.js', 'wb') as f:
        f.write(content_crlf.encode('utf-8'))
    print("i18n.js updated successfully.")

def update_index_html():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    content_norm = content.replace('\r\n', '\n')

    # 1. Update #human-support-drawer in index.html
    old_drawer_section = '''                <div class="space-y-1">
                    <p id="drawer-subtitle" class="text-xs font-bold text-[#202124]">If you don't feel safe, don't stay alone.</p>
                    <p class="text-xs text-[#6F6B68] leading-relaxed">Stay with someone you trust and reach out for support now.</p>
                </div>

                <div class="space-y-3">
                    <!-- Emergency Medical Support (115 - Essential Red CTA) -->
                    <div class="p-4 bg-white border border-[#D92D20]/30 rounded-2xl space-y-2 shadow-2xs">
                        <div class="flex items-center justify-between">
                            <span id="drawer-medical-title" class="text-xs font-bold text-[#202124] uppercase tracking-wider">Emergency Medical Support</span>
                            <span class="px-2 py-0.5 bg-[#D92D20]/15 text-[#D92D20] text-[10px] font-bold rounded-full">Emergency</span>
                        </div>
                        <div class="text-xl font-extrabold text-[#D92D20] tracking-tight">115</div>
                        <p id="drawer-medical-desc" class="text-xs text-[#6F6B68]">If you're at immediate risk of hurting yourself or you're in immediate danger.</p>
                        <a id="drawer-medical-call" href="tel:115" class="inline-block mt-1 px-4 py-2 bg-[#D92D20] hover:bg-[#B42318] text-white rounded-xl text-xs font-bold transition shadow-xs">Call 115 Now</a>
                    </div>

                    <!-- HOPE — Suicide Prevention Hotline (Dusty Blue Accent) -->
                    <div class="p-4 bg-white border border-[#93AFBC]/40 rounded-2xl space-y-2 shadow-2xs">
                        <div class="flex items-center justify-between">
                            <span id="drawer-hotline-title" class="text-xs font-bold text-[#202124] uppercase tracking-wider">HOPE — Suicide Prevention Hotline</span>
                            <span class="px-2 py-0.5 bg-[#93AFBC]/25 text-[#2C4957] text-[10px] font-bold rounded-full">Crisis Support</span>
                        </div>
                        <div class="text-lg font-extrabold text-[#202124] tracking-tight">0865 044 400</div>
                        <p id="drawer-hotline-desc" class="text-xs text-[#6F6B68]">If you're in crisis, having thoughts of hurting yourself, or need someone to support you right now.</p>
                        <a id="drawer-hotline-call" href="tel:0865044400" class="inline-block mt-1 px-4 py-2 bg-[#202124] hover:bg-black text-white rounded-xl text-xs font-bold transition shadow-xs">Call 0865 044 400</a>
                    </div>

                    <!-- Đường dây nóng Ngày Mai (Dusty Blue & Sage Green Accent) -->
                    <div id="drawer-card-ngaymai" class="p-4 bg-white border border-[#8EA28F]/40 rounded-2xl space-y-2 shadow-2xs">
                        <div class="flex items-center justify-between gap-2">
                            <span id="drawer-ngaymai-title" class="text-xs font-bold text-[#202124] uppercase tracking-wider">ĐƯỜNG DÂY NÓNG NGÀY MAI</span>
                            <span id="drawer-ngaymai-badge" class="px-2 py-0.5 bg-[#8EA28F]/20 text-[#3B5C43] text-[10px] font-bold rounded-full shrink-0">Hỗ trợ tâm lý</span>
                        </div>
                        <div class="text-lg font-extrabold text-[#202124] tracking-tight">096 306 1414</div>
                        <p id="drawer-ngaymai-desc" class="text-xs text-[#6F6B68] leading-relaxed">Hỗ trợ tâm lý miễn phí qua điện thoại cho người đang gặp khủng hoảng tâm lý, trầm cảm và người thân của họ. Lắng nghe không phán xét, bảo mật thông tin.</p>
                        <div class="flex items-center space-x-1.5 text-[11px] font-semibold text-[#4A6A78] bg-[#93AFBC]/15 px-2.5 py-1 rounded-lg">
                            <svg class="w-3.5 h-3.5 text-[#4A6A78] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                            </svg>
                            <span id="drawer-ngaymai-hours">13:00 – 20:30, Thứ Tư – Chủ Nhật</span>
                        </div>
                        <a id="drawer-ngaymai-call" href="tel:0963061414" class="inline-block mt-1 px-4 py-2 bg-[#8EA28F] hover:bg-[#7D917E] text-white rounded-xl text-xs font-bold transition shadow-xs">Gọi 096 306 1414</a>
                    </div>

                    <!-- While Waiting For Support Guidance (Pale Sage Green Tint) -->
                    <div class="p-4 bg-[#8EA28F]/10 border border-[#8EA28F]/30 rounded-2xl space-y-2.5">
                        <span id="drawer-waiting-header" class="text-xs font-bold text-[#3B5C43] uppercase tracking-wider">While you're waiting for support</span>
                        <ul class="text-xs text-[#202124] space-y-1.5 list-disc list-inside font-medium">
                            <li id="drawer-waiting-action-1">Stay with someone you trust.</li>
                            <li id="drawer-waiting-action-2">Move somewhere safer.</li>
                            <li id="drawer-waiting-action-3">Create distance from anything that could hurt you.</li>
                        </ul>
                        <div class="pt-2 border-t border-[#8EA28F]/30 text-xs text-[#202124] space-y-0.5">
                            <p class="font-bold">You don't need to solve everything right now.</p>
                            <p id="drawer-waiting-reassurance" class="text-[#6F6B68]">For now, just focus on staying safe.</p>
                        </div>
                    </div>

                    <!-- Reach Out to Someone You Trust Helper (Dusty Blue Button Accent) -->
                    <div class="p-4 bg-white border border-[#EAE4DF] rounded-2xl space-y-2 shadow-2xs">
                        <span class="text-xs font-bold text-[#202124]">Reach Out to Someone You Trust:</span>
                        <p class="text-xs text-[#6F6B68]">Copy this simple message to reach out to a friend or family member:</p>
                        <div id="drawer-trusted-quote" class="p-3 bg-[#FFF9F4] border border-[#93AFBC]/35 rounded-xl text-xs text-[#202124] italic">
                            "Hey, I'm having a really difficult time right now and feeling overwhelmed. Are you free to talk or sit with me for a few minutes?"
                        </div>
                        <button type="button" onclick="window.TempoEmergencySupport.copyTrustedMessage()" 
                            class="w-full py-2.5 px-4 bg-[#93AFBC]/15 hover:bg-[#93AFBC]/25 text-[#2C4957] rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5 cursor-pointer">
                            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
                            </svg>
                            <span id="drawer-copy-btn-text">Copy Message</span>
                        </button>
                    </div>

                    <!-- Campus Support Offline Notice (Sage Green Button Accent) -->
                    <div class="p-4 bg-white border border-[#EAE4DF] rounded-2xl space-y-2 shadow-2xs">
                        <div class="flex items-center justify-between">
                            <span class="text-xs font-bold text-[#202124] uppercase tracking-wider">Campus Student Wellbeing</span>
                            <span class="text-[10px] font-bold text-[#4A6A78] bg-[#93AFBC]/20 px-2 py-0.5 rounded-full">Office Hours Support</span>
                        </div>
                        <p class="text-xs text-[#6F6B68] leading-relaxed">
                            For immediate crisis or danger, call <strong>115</strong> or <strong>0865 044 400</strong>. For non-urgent campus advising questions during office hours:
                        </p>
                        <div class="pt-1 space-y-2">
                            <input id="drawer-offline-contact" type="text" placeholder="Your name or student email (optional)" class="w-full p-2.5 text-xs bg-white border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#8EA28F]">
                            <textarea id="drawer-offline-message" rows="2" placeholder="Describe your question or message for office hours..." class="w-full p-2.5 text-xs bg-white border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#8EA28F]"></textarea>
                            <button id="btn-drawer-send-offline" type="button" onclick="window.TempoEmergencySupport.submitOfflineMessage('drawer')" class="w-full py-2.5 bg-[#8EA28F] hover:bg-[#7D917E] text-white rounded-xl text-xs font-bold transition shadow-xs cursor-pointer">
                                Leave Message for Campus Staff
                            </button>
                            <p id="drawer-offline-success" class="hidden text-[11px] text-[#3B5C43] font-semibold p-2 bg-[#8EA28F]/15 border border-[#8EA28F]/40 rounded-xl">
                                Message saved. Staff will respond during normal hours. For immediate help, call 115 or 0865 044 400.
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="pt-4 border-t border-[#ECC9BA]/40">
                <button onclick="window.TempoEmergencySupport.closeHumanDrawer()" class="w-full py-3 bg-[#202124] hover:bg-black text-white rounded-xl text-xs font-bold transition cursor-pointer shadow-xs">
                    <span id="drawer-close-btn-text">Close Support Drawer</span>
                </button>
            </div>'''

    new_drawer_section = '''                <div class="space-y-1">
                    <p id="drawer-subtitle" class="text-xs font-bold text-[#202124]">Nếu bạn cảm thấy không an toàn, đừng ở một mình.</p>
                    <p id="drawer-subtitle-desc" class="text-xs text-[#6F6B68] leading-relaxed">Hãy ở cùng người bạn tin cậy và tìm kiếm sự hỗ trợ ngay bây giờ.</p>
                </div>

                <div class="space-y-3">
                    <!-- Emergency Medical Support (115 - Essential Red CTA) -->
                    <div class="p-4 bg-white border border-[#D92D20]/30 rounded-2xl space-y-2 shadow-2xs">
                        <div class="flex items-center justify-between">
                            <span id="drawer-medical-title" class="text-xs font-bold text-[#202124] uppercase tracking-wider">Hỗ trợ Y tế Khẩn cấp</span>
                            <span id="drawer-medical-badge" class="px-2 py-0.5 bg-[#D92D20]/15 text-[#D92D20] text-[10px] font-bold rounded-full">Khẩn cấp</span>
                        </div>
                        <div class="text-xl font-extrabold text-[#D92D20] tracking-tight">115</div>
                        <p id="drawer-medical-desc" class="text-xs text-[#6F6B68]">Nếu bạn có nguy cơ tự làm hại bản thân ngay lập tức hoặc đang trong tình huống nguy hiểm.</p>
                        <a id="drawer-medical-call" href="tel:115" class="inline-block mt-1 px-4 py-2 bg-[#D92D20] hover:bg-[#B42318] text-white rounded-xl text-xs font-bold transition shadow-xs">Gọi 115 ngay</a>
                    </div>

                    <!-- HOPE — Suicide Prevention Hotline (Dusty Blue Accent) -->
                    <div class="p-4 bg-white border border-[#93AFBC]/40 rounded-2xl space-y-2 shadow-2xs">
                        <div class="flex items-center justify-between">
                            <span id="drawer-hotline-title" class="text-xs font-bold text-[#202124] uppercase tracking-wider">Đường dây nóng Khủng hoảng & Hỗ trợ Tâm lý HOPE</span>
                            <span id="drawer-hotline-badge" class="px-2 py-0.5 bg-[#93AFBC]/25 text-[#2C4957] text-[10px] font-bold rounded-full">Hỗ trợ khủng hoảng</span>
                        </div>
                        <div class="text-lg font-extrabold text-[#202124] tracking-tight">0865 044 400</div>
                        <p id="drawer-hotline-desc" class="text-xs text-[#6F6B68]">Nếu bạn đang trong cơn khủng hoảng, có suy nghĩ tự hại hoặc cần người lắng nghe ngay bây giờ.</p>
                        <a id="drawer-hotline-call" href="tel:0865044400" class="inline-block mt-1 px-4 py-2 bg-[#202124] hover:bg-black text-white rounded-xl text-xs font-bold transition shadow-xs">Gọi 0865 044 400</a>
                    </div>

                    <!-- Đường dây nóng Ngày Mai (Dusty Blue & Sage Green Accent) -->
                    <div id="drawer-card-ngaymai" class="p-4 bg-white border border-[#8EA28F]/40 rounded-2xl space-y-2 shadow-2xs">
                        <div class="flex items-center justify-between gap-2">
                            <span id="drawer-ngaymai-title" class="text-xs font-bold text-[#202124] uppercase tracking-wider">ĐƯỜNG DÂY NÓNG NGÀY MAI</span>
                            <span id="drawer-ngaymai-badge" class="px-2 py-0.5 bg-[#8EA28F]/20 text-[#3B5C43] text-[10px] font-bold rounded-full shrink-0">Hỗ trợ tâm lý</span>
                        </div>
                        <div class="text-lg font-extrabold text-[#202124] tracking-tight">096 306 1414</div>
                        <p id="drawer-ngaymai-desc" class="text-xs text-[#6F6B68] leading-relaxed">Hỗ trợ tâm lý miễn phí qua điện thoại cho người đang gặp khủng hoảng tâm lý, trầm cảm và người thân của họ. Lắng nghe không phán xét, bảo mật thông tin.</p>
                        <div class="flex items-center space-x-1.5 text-[11px] font-semibold text-[#4A6A78] bg-[#93AFBC]/15 px-2.5 py-1 rounded-lg">
                            <svg class="w-3.5 h-3.5 text-[#4A6A78] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                            </svg>
                            <span id="drawer-ngaymai-hours">13:00 – 20:30, Thứ Tư – Chủ Nhật</span>
                        </div>
                        <a id="drawer-ngaymai-call" href="tel:0963061414" class="inline-block mt-1 px-4 py-2 bg-[#8EA28F] hover:bg-[#7D917E] text-white rounded-xl text-xs font-bold transition shadow-xs">Gọi 096 306 1414</a>
                    </div>

                    <!-- While Waiting For Support Guidance (Pale Sage Green Tint) -->
                    <div class="p-4 bg-[#8EA28F]/10 border border-[#8EA28F]/30 rounded-2xl space-y-2.5">
                        <span id="drawer-waiting-header" class="text-xs font-bold text-[#3B5C43] uppercase tracking-wider">KHI BẠN ĐANG CHỜ ĐƯỢC HỖ TRỢ</span>
                        <ul class="text-xs text-[#202124] space-y-1.5 list-disc list-inside font-medium">
                            <li id="drawer-waiting-action-1">Ở cùng một người bạn tin tưởng.</li>
                            <li id="drawer-waiting-action-2">Di chuyển đến một nơi an toàn hơn.</li>
                            <li id="drawer-waiting-action-3">Tạo khoảng cách với những vật có thể gây tổn thương cho bạn.</li>
                        </ul>
                        <div class="pt-2 border-t border-[#8EA28F]/30 text-xs text-[#202124] space-y-0.5">
                            <p id="drawer-waiting-reass-title" class="font-bold">Bạn không cần giải quyết mọi thứ ngay lúc này.</p>
                            <p id="drawer-waiting-reassurance" class="text-[#6F6B68]">Lúc này, chỉ cần tập trung giữ an toàn cho bản thân.</p>
                        </div>
                    </div>

                    <!-- Reach Out to Someone You Trust Helper (Dusty Blue Button Accent) -->
                    <div class="p-4 bg-white border border-[#EAE4DF] rounded-2xl space-y-2 shadow-2xs">
                        <span id="drawer-trusted-title" class="text-xs font-bold text-[#202124]">Liên hệ với người bạn tin tưởng</span>
                        <p id="drawer-trusted-desc" class="text-xs text-[#6F6B68]">Bạn có thể sao chép tin nhắn này để gửi cho bạn bè hoặc người thân:</p>
                        <div id="drawer-trusted-quote" class="p-3 bg-[#FFF9F4] border border-[#93AFBC]/35 rounded-xl text-xs text-[#202124] italic">
                            "Chào bạn, mình đang trải qua một khoảng thời gian rất khó khăn và cảm thấy quá tải. Bạn có thể trò chuyện hoặc ngồi cùng mình một lúc được không?"
                        </div>
                        <button id="btn-copy-trusted-msg" type="button" onclick="window.TempoEmergencySupport.copyTrustedMessage()" 
                            class="w-full py-2.5 px-4 bg-[#93AFBC]/15 hover:bg-[#93AFBC]/25 text-[#2C4957] rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5 cursor-pointer">
                            <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
                            </svg>
                            <span id="drawer-copy-btn-text">Sao chép tin nhắn</span>
                        </button>
                    </div>

                    <!-- Campus Student Wellbeing Card (Sage Green Button Accent) -->
                    <div class="p-4 bg-white border border-[#EAE4DF] rounded-2xl space-y-3 shadow-2xs">
                        <div class="flex items-center justify-between">
                            <span id="drawer-campus-title" class="text-xs font-bold text-[#202124] uppercase tracking-wider">HỖ TRỢ SỨC KHỎE TINH THẦN SINH VIÊN</span>
                            <span id="drawer-campus-badge" class="text-[10px] font-bold text-[#4A6A78] bg-[#93AFBC]/20 px-2 py-0.5 rounded-full">Hỗ trợ trong giờ làm việc</span>
                        </div>
                        <p id="drawer-campus-desc" class="text-xs text-[#6F6B68] leading-relaxed">
                            Trong trường hợp khẩn cấp hoặc nguy hiểm tức thời, hãy gọi <strong>115</strong> hoặc <strong>0865 044 400</strong>. Nếu bạn cần trao đổi về các vấn đề tâm lý không khẩn cấp, bạn có thể liên hệ với bộ phận hỗ trợ sinh viên trong giờ làm việc.
                        </p>

                        <!-- FPT University Psychological Counseling Office Dedicated Contact -->
                        <div id="drawer-fpt-counseling-card" class="p-3.5 bg-[#FFF9F4] border border-[#93AFBC]/40 rounded-xl space-y-2">
                            <div class="flex items-center space-x-2">
                                <span class="w-6 h-6 rounded-lg bg-[#93AFBC]/20 text-[#2C4957] flex items-center justify-center shrink-0">
                                    <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                                        <polyline points="22,6 12,13 2,6"/>
                                    </svg>
                                </span>
                                <h6 id="drawer-fpt-title" class="text-xs font-bold text-[#202124]">Phòng Tư vấn tâm lý – Đại học FPT</h6>
                            </div>
                            <p id="drawer-fpt-desc" class="text-xs text-[#6F6B68] leading-relaxed">
                                Dịch vụ tư vấn tâm lý miễn phí và bảo mật dành cho sinh viên Đại học FPT.
                            </p>
                            <div class="flex items-center justify-between pt-1 gap-2 flex-wrap">
                                <span class="text-xs font-semibold text-[#2C4957] break-all">tuvansinhvien@fpt.edu.vn</span>
                                <a id="drawer-fpt-cta" href="mailto:tuvansinhvien@fpt.edu.vn" class="px-3.5 py-1.5 bg-[#93AFBC]/25 hover:bg-[#93AFBC]/40 text-[#2C4957] border border-[#93AFBC]/50 rounded-lg text-xs font-bold transition flex items-center space-x-1 cursor-pointer">
                                    <svg class="w-3 h-3 text-[#2C4957]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                                        <polyline points="22,6 12,13 2,6"/>
                                    </svg>
                                    <span id="drawer-fpt-cta-text">Gửi email tư vấn</span>
                                </a>
                            </div>
                        </div>

                        <!-- Direct Form Message for Campus Staff -->
                        <div class="pt-1 space-y-2">
                            <input id="drawer-offline-contact" type="text" placeholder="Họ tên hoặc email sinh viên (không bắt buộc)" class="w-full p-2.5 text-xs bg-white border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#8EA28F]">
                            <textarea id="drawer-offline-message" rows="2" placeholder="Mô tả vấn đề hoặc nội dung bạn muốn gửi đến phòng tư vấn" class="w-full p-2.5 text-xs bg-white border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#8EA28F]"></textarea>
                            <button id="btn-drawer-send-offline" type="button" onclick="window.TempoEmergencySupport.submitOfflineMessage('drawer')" class="w-full py-2.5 bg-[#8EA28F] hover:bg-[#7D917E] text-white rounded-xl text-xs font-bold transition shadow-xs cursor-pointer">
                                <span id="drawer-offline-btn-text">Gửi tin nhắn cho bộ phận hỗ trợ</span>
                            </button>
                            <p id="drawer-offline-success" class="hidden text-[11px] text-[#3B5C43] font-semibold p-2 bg-[#8EA28F]/15 border border-[#8EA28F]/40 rounded-xl">
                                Tin nhắn đã được lưu. Bộ phận hỗ trợ sẽ phản hồi trong giờ làm việc. Nếu cần giúp đỡ ngay lập tức, hãy gọi 115 hoặc 0865 044 400.
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <div class="pt-4 border-t border-[#ECC9BA]/40">
                <button onclick="window.TempoEmergencySupport.closeHumanDrawer()" class="w-full py-3 bg-[#202124] hover:bg-black text-white rounded-xl text-xs font-bold transition cursor-pointer shadow-xs">
                    <span id="drawer-close-btn-text">Đóng cửa sổ hỗ trợ</span>
                </button>
            </div>'''

    assert old_drawer_section in content_norm, "old_drawer_section not found in index.html"
    content_norm = content_norm.replace(old_drawer_section, new_drawer_section)

    # 2. Update Step 5A in index.html
    old_step5a_section = '''                    <!-- While Waiting For Support Guidance (Pale Sage Green Tint) -->
                    <div class="p-4 sm:p-5 bg-[#8EA28F]/10 border border-[#8EA28F]/30 rounded-2xl space-y-2.5 text-xs text-[#202124]">
                        <span class="text-xs font-bold text-[#3B5C43] uppercase tracking-wider">While you're waiting for support</span>
                        <ul class="text-xs text-[#202124] space-y-1.5 list-disc list-inside font-medium">
                            <li>Stay with someone you trust.</li>
                            <li>Move somewhere safer.</li>
                            <li>Create distance from anything that could hurt you.</li>
                        </ul>
                        <div class="pt-2 border-t border-[#8EA28F]/30 text-xs text-[#202124] space-y-0.5">
                            <p class="font-bold">You don't need to solve everything right now.</p>
                            <p class="text-[#6F6B68]">For now, just focus on staying safe.</p>
                        </div>
                    </div>

                    <!-- Campus Support (With Message Form - Sage Green Accent) -->
                    <div class="p-4 sm:p-5 bg-white border border-[#EAE4DF] rounded-2xl space-y-2.5 shadow-2xs">
                        <div class="flex items-center justify-between">
                            <h5 class="text-xs font-bold text-[#202124] uppercase tracking-wider">Campus Student Wellbeing</h5>
                            <span class="text-[10px] font-bold text-[#4A6A78] bg-[#93AFBC]/20 px-2 py-0.5 rounded-full">Office Hours Support</span>
                        </div>
                        <p class="text-xs text-[#6F6B68] leading-relaxed">
                            For immediate crisis or danger, call <strong>115</strong> or <strong>0865 044 400</strong>. For non-urgent campus advising questions during office hours:
                        </p>
                        <div class="pt-2 border-t border-[#EAE4DF] space-y-2">
                            <input id="step5a-offline-contact" type="text" placeholder="Your name or student email (optional)" class="w-full p-2.5 text-xs bg-white border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#8EA28F]">
                            <textarea id="step5a-offline-message" rows="2" placeholder="Describe your question or message for office hours..." class="w-full p-2.5 text-xs bg-white border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#8EA28F]"></textarea>
                            <button id="btn-step5a-send-offline" type="button" onclick="window.TempoEmergencySupport.submitOfflineMessage('step5a')" class="w-full py-2.5 bg-[#8EA28F] hover:bg-[#7D917E] text-white rounded-xl text-xs font-bold transition shadow-xs cursor-pointer">
                                Leave Message for Campus Staff
                            </button>
                            <p id="step5a-offline-success" class="hidden text-[11px] text-[#3B5C43] font-semibold p-2 bg-[#8EA28F]/15 border border-[#8EA28F]/40 rounded-xl">
                                Message saved. Staff will respond during normal hours. For immediate help, call 115 or 0865 044 400.
                            </p>
                        </div>
                    </div>'''

    new_step5a_section = '''                    <!-- While Waiting For Support Guidance (Pale Sage Green Tint) -->
                    <div class="p-4 sm:p-5 bg-[#8EA28F]/10 border border-[#8EA28F]/30 rounded-2xl space-y-2.5 text-xs text-[#202124]">
                        <span id="step5a-waiting-header" class="text-xs font-bold text-[#3B5C43] uppercase tracking-wider">KHI BẠN ĐANG CHỜ ĐƯỢC HỖ TRỢ</span>
                        <ul class="text-xs text-[#202124] space-y-1.5 list-disc list-inside font-medium">
                            <li id="step5a-waiting-action-1">Ở cùng một người bạn tin tưởng.</li>
                            <li id="step5a-waiting-action-2">Di chuyển đến một nơi an toàn hơn.</li>
                            <li id="step5a-waiting-action-3">Tạo khoảng cách với những vật có thể gây tổn thương cho bạn.</li>
                        </ul>
                        <div class="pt-2 border-t border-[#8EA28F]/30 text-xs text-[#202124] space-y-0.5">
                            <p id="step5a-waiting-reass-title" class="font-bold">Bạn không cần giải quyết mọi thứ ngay lúc này.</p>
                            <p id="step5a-waiting-reassurance" class="text-[#6F6B68]">Lúc này, chỉ cần tập trung giữ an toàn cho bản thân.</p>
                        </div>
                    </div>

                    <!-- Campus Support (With Message Form - Sage Green Accent) -->
                    <div class="p-4 sm:p-5 bg-white border border-[#EAE4DF] rounded-2xl space-y-3 shadow-2xs">
                        <div class="flex items-center justify-between">
                            <h5 id="step5a-campus-title" class="text-xs font-bold text-[#202124] uppercase tracking-wider">HỖ TRỢ SỨC KHỎE TINH THẦN SINH VIÊN</h5>
                            <span id="step5a-campus-badge" class="text-[10px] font-bold text-[#4A6A78] bg-[#93AFBC]/20 px-2 py-0.5 rounded-full">Hỗ trợ trong giờ làm việc</span>
                        </div>
                        <p id="step5a-campus-desc" class="text-xs text-[#6F6B68] leading-relaxed">
                            Trong trường hợp khẩn cấp hoặc nguy hiểm tức thời, hãy gọi <strong>115</strong> hoặc <strong>0865 044 400</strong>. Nếu bạn cần trao đổi về các vấn đề tâm lý không khẩn cấp, bạn có thể liên hệ với bộ phận hỗ trợ sinh viên trong giờ làm việc.
                        </p>

                        <!-- FPT University Psychological Counseling Office Dedicated Contact -->
                        <div id="step5a-fpt-counseling-card" class="p-3.5 bg-[#FFF9F4] border border-[#93AFBC]/40 rounded-xl space-y-2">
                            <div class="flex items-center space-x-2">
                                <span class="w-6 h-6 rounded-lg bg-[#93AFBC]/20 text-[#2C4957] flex items-center justify-center shrink-0">
                                    <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                                        <polyline points="22,6 12,13 2,6"/>
                                    </svg>
                                </span>
                                <h6 id="step5a-fpt-title" class="text-xs font-bold text-[#202124]">Phòng Tư vấn tâm lý – Đại học FPT</h6>
                            </div>
                            <p id="step5a-fpt-desc" class="text-xs text-[#6F6B68] leading-relaxed">
                                Dịch vụ tư vấn tâm lý miễn phí và bảo mật dành cho sinh viên Đại học FPT.
                            </p>
                            <div class="flex items-center justify-between pt-1 gap-2 flex-wrap">
                                <span class="text-xs font-semibold text-[#2C4957] break-all">tuvansinhvien@fpt.edu.vn</span>
                                <a id="step5a-fpt-cta" href="mailto:tuvansinhvien@fpt.edu.vn" class="px-3.5 py-1.5 bg-[#93AFBC]/25 hover:bg-[#93AFBC]/40 text-[#2C4957] border border-[#93AFBC]/50 rounded-lg text-xs font-bold transition flex items-center space-x-1 cursor-pointer">
                                    <svg class="w-3 h-3 text-[#2C4957]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                                        <polyline points="22,6 12,13 2,6"/>
                                    </svg>
                                    <span id="step5a-fpt-cta-text">Gửi email tư vấn</span>
                                </a>
                            </div>
                        </div>

                        <div class="pt-2 border-t border-[#EAE4DF] space-y-2">
                            <input id="step5a-offline-contact" type="text" placeholder="Họ tên hoặc email sinh viên (không bắt buộc)" class="w-full p-2.5 text-xs bg-white border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#8EA28F]">
                            <textarea id="step5a-offline-message" rows="2" placeholder="Mô tả vấn đề hoặc nội dung bạn muốn gửi đến phòng tư vấn" class="w-full p-2.5 text-xs bg-white border border-[#EAE4DF] rounded-xl focus:outline-none focus:border-[#8EA28F]"></textarea>
                            <button id="btn-step5a-send-offline" type="button" onclick="window.TempoEmergencySupport.submitOfflineMessage('step5a')" class="w-full py-2.5 bg-[#8EA28F] hover:bg-[#7D917E] text-white rounded-xl text-xs font-bold transition shadow-xs cursor-pointer">
                                <span id="step5a-offline-btn-text">Gửi tin nhắn cho bộ phận hỗ trợ</span>
                            </button>
                            <p id="step5a-offline-success" class="hidden text-[11px] text-[#3B5C43] font-semibold p-2 bg-[#8EA28F]/15 border border-[#8EA28F]/40 rounded-xl">
                                Tin nhắn đã được lưu. Bộ phận hỗ trợ sẽ phản hồi trong giờ làm việc. Nếu cần giúp đỡ ngay lập tức, hãy gọi 115 hoặc 0865 044 400.
                            </p>
                        </div>
                    </div>'''

    assert old_step5a_section in content_norm, "old_step5a_section not found in index.html"
    content_norm = content_norm.replace(old_step5a_section, new_step5a_section)

    with open('index.html', 'wb') as f:
        f.write(content_norm.encode('utf-8'))
    print("index.html updated successfully.")

if __name__ == '__main__':
    update_emergency_support_js()
    update_i18n_js()
    update_index_html()
