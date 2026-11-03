# -*- coding: utf-8 -*-
import sys

def update_i18n():
    with open('i18n.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # Old Vietnamese sos block
    old_vi_sos = '''            sos: {
                title: "SOS · Hỗ trợ khẩn cấp",
                subtitle: "Sự an toàn của bạn là ưu tiên hàng đầu",
                pillSupport: "Nhận hỗ trợ ngay →",
                safetyBannerHeading: "Chế độ An toàn đang Bật — Hỗ trợ trực tiếp từ con người luôn sẵn sàng.",
                safetyBannerDesc: "Bạn không cần hoàn thành bất kỳ bài tập nào để trò chuyện với chuyên viên hỗ trợ. Bạn có thể nhấn \\"Nhận hỗ trợ ngay →\\" bất kỳ lúc nào.",
                eyebrow: "SOS · HỖ TRỢ KHẨN CẤP",
                mainHeading: "Lúc này tôi cảm thấy không an toàn",
                situationIntro: "Nếu lúc này bạn đang:",
                situation1: "hoảng loạn và cảm thấy mất kiểm soát",
                situation2: "có suy nghĩ hoặc thôi thúc muốn làm tổn thương bản thân",
                situation3: "cảm thấy không an toàn khi ở một mình",
                reassuranceTitle: "Sự an toàn của bạn là ưu tiên hàng đầu.",
                reassuranceBody: "Bạn không phải vượt qua mọi thứ một mình ngay lúc này.",
                getSupportNow: "Nhận hỗ trợ ngay →",
                altOptionsHeading: "Hoặc chọn điều bạn cần ngay lúc này",
                optionABadge: "LỰA CHỌN A",
                optionATitle: "Tôi đang quá tải hoặc hoảng loạn",
                optionADesc: "Tôi cảm thấy căng thẳng, quá tải hoặc không thể suy nghĩ rõ ràng.",
                optionBBadge: "LỰA CHỌN B • HỖ TRỢ KHẨN CẤP",
                optionBTitle: "Tôi đang khủng hoảng cảm xúc hoặc thấy không an toàn",
                optionBDesc: "Tôi đang trải qua nỗi đau tâm lý dữ dội và cần hỗ trợ ngay.",
                optionCBadge: "LỰA CHỌN C • CHĂM SÓC ĐẶC BIỆT",
                optionCTitle: "Tôi đang nghĩ đến việc tự hại hoặc tự tử",
                optionCDesc: "Tôi đang có suy nghĩ muốn làm tổn thương bản thân hoặc kết thúc cuộc sống.",
                optionDLabel: "Tôi không chắc — tâm trí tôi đang hỗn loạn và tôi chỉ cần giúp bình tĩnh lại",
                drawerTitle: "Nhận hỗ trợ ngay",
                drawerSubtitle: "Nếu bạn cảm thấy không an toàn, đừng ở một mình. Hãy ở cùng người bạn tin cậy và tìm kiếm sự hỗ trợ ngay bây giờ.",
                medicalTitle: "Hỗ trợ Y tế Khẩn cấp",
                medicalDesc: "Nếu bạn có nguy cơ tự làm hại bản thân ngay lập tức hoặc đang trong tình huống nguy hiểm.",
                medicalCall: "Gọi 115 ngay",
                hotlineTitle: "Đường dây nóng Khủng hoảng & Hỗ trợ Tâm lý HOPE",
                hotlineDesc: "Nếu bạn đang trong cơn khủng hoảng, có suy nghĩ tự hại hoặc cần người lắng nghe ngay bây giờ.",
                hotlineCall: "Gọi 0865 044 400",
                waitingHeader: "Khi bạn đang chờ được hỗ trợ",
                action1: "Ở cùng một người bạn tin tưởng.",
                action2: "Di chuyển đến một nơi an toàn hơn.",
                action3: "Tạo khoảng cách với những vật có thể gây tổn thương cho bạn.",
                reassurance: "Bạn không cần giải quyết mọi thứ ngay lúc này. Lúc này, chỉ cần tập trung giữ an toàn cho bản thân.",
                copyTrustedBtn: "Sao chép tin nhắn",
                closeSOS: "Đóng cửa sổ hỗ trợ"
            },'''

    new_vi_sos = '''            sos: {
                title: "SOS · Hỗ trợ khẩn cấp",
                subtitle: "An toàn của bạn là ưu tiên hàng đầu",
                pillSupport: "Nhận hỗ trợ ngay →",
                safetyBannerHeading: "Chế độ an toàn đang bật",
                safetyBannerDesc: "Bạn không cần phải trải qua điều này một mình. Hãy để chúng tôi giúp bạn.",
                eyebrow: "SOS · Hỗ trợ khẩn cấp",
                mainHeading: "Tôi không cảm thấy an toàn lúc này",
                situationIntro: "Nếu ngay lúc này bạn đang:",
                situation1: "Hoảng loạn và cảm thấy mất kiểm soát",
                situation2: "Có suy nghĩ hoặc thôi thúc làm tổn thương bản thân",
                situation3: "Cảm thấy không an toàn khi ở một mình",
                reassuranceTitle: "An toàn của bạn là ưu tiên hàng đầu.",
                reassuranceBody: "Bạn không cần phải tự mình vượt qua tất cả.",
                getSupportNow: "Nhận hỗ trợ ngay →",
                altOptionsHeading: "Hoặc chọn điều bạn cần lúc này",
                optionABadge: "Lựa chọn A",
                optionATitle: "Lựa chọn A · Quá tải hoặc hoảng loạn",
                optionADesc: "Tôi cảm thấy căng thẳng, quá tải hoặc không thể suy nghĩ rõ ràng.",
                optionBBadge: "Lựa chọn B",
                optionBTitle: "Lựa chọn B · Khủng hoảng cảm xúc",
                optionBDesc: "Tôi đang trải qua trạng thái cảm xúc rất tiêu cực và cần được hỗ trợ ngay.",
                optionCBadge: "Lựa chọn C",
                optionCTitle: "Lựa chọn C · Cần hỗ trợ khẩn cấp",
                optionCDesc: "Tôi đang nghĩ đến việc làm tổn thương bản thân hoặc tự tử.",
                optionDLabel: "Tôi không chắc — đầu óc tôi đang rối bời và tôi chỉ muốn được giúp bình tĩnh lại.",
                drawerTitle: "Nhận hỗ trợ ngay",
                drawerSubtitle: "Nếu bạn cảm thấy không an toàn, đừng ở một mình. Hãy ở cùng người bạn tin cậy và tìm kiếm sự hỗ trợ ngay bây giờ.",
                medicalTitle: "Hỗ trợ Y tế Khẩn cấp",
                medicalDesc: "Nếu bạn có nguy cơ tự làm hại bản thân ngay lập tức hoặc đang trong tình huống nguy hiểm.",
                medicalCall: "Gọi 115 ngay",
                hotlineTitle: "Đường dây nóng Khủng hoảng & Hỗ trợ Tâm lý HOPE",
                hotlineDesc: "Nếu bạn đang trong cơn khủng hoảng, có suy nghĩ tự hại hoặc cần người lắng nghe ngay bây giờ.",
                hotlineCall: "Gọi 0865 044 400",
                waitingHeader: "Khi bạn đang chờ được hỗ trợ",
                action1: "Ở cùng một người bạn tin tưởng.",
                action2: "Di chuyển đến một nơi an toàn hơn.",
                action3: "Tạo khoảng cách với những vật có thể gây tổn thương cho bạn.",
                reassurance: "Bạn không cần giải quyết mọi thứ ngay lúc này. Lúc này, chỉ cần tập trung giữ an toàn cho bản thân.",
                copyTrustedBtn: "Sao chép tin nhắn",
                closeSOS: "Đóng cửa sổ hỗ trợ",
                copySuccessToast: "Đã sao chép tin nhắn! Bạn có thể dán và gửi cho bạn bè hoặc người thân."
            },'''

    # Ensure line endings match
    old_vi_sos_norm = old_vi_sos.replace('\r\n', '\n')
    content_norm = content.replace('\r\n', '\n')
    assert old_vi_sos_norm in content_norm, "Old vi sos block not found in i18n.js!"
    content_norm = content_norm.replace(old_vi_sos_norm, new_vi_sos.replace('\r\n', '\n'))

    # Update applyLanguageToDOM for SOS options badge handling and drawer quote
    old_dom_sos_options = '''        const sosAltHeading = document.getElementById('sos-alt-options-heading');
        if (sosAltHeading) sosAltHeading.textContent = t('sos.altOptionsHeading');

        const sosOptABadge = document.getElementById('sos-option-a-badge');
        if (sosOptABadge) sosOptABadge.textContent = t('sos.optionABadge');
        const sosOptATitle = document.getElementById('sos-option-a-title');
        if (sosOptATitle) sosOptATitle.textContent = t('sos.optionATitle');
        const sosOptADesc = document.getElementById('sos-option-a-desc');
        if (sosOptADesc) sosOptADesc.textContent = t('sos.optionADesc');

        const sosOptBBadge = document.getElementById('sos-option-b-badge');
        if (sosOptBBadge) sosOptBBadge.textContent = t('sos.optionBBadge');
        const sosOptBTitle = document.getElementById('sos-option-b-title');
        if (sosOptBTitle) sosOptBTitle.textContent = t('sos.optionBTitle');
        const sosOptBDesc = document.getElementById('sos-option-b-desc');
        if (sosOptBDesc) sosOptBDesc.textContent = t('sos.optionBDesc');

        const sosOptCBadge = document.getElementById('sos-option-c-badge');
        if (sosOptCBadge) sosOptCBadge.textContent = t('sos.optionCBadge');
        const sosOptCTitle = document.getElementById('sos-option-c-title');
        if (sosOptCTitle) sosOptCTitle.textContent = t('sos.optionCTitle');
        const sosOptCDesc = document.getElementById('sos-option-c-desc');
        if (sosOptCDesc) sosOptCDesc.textContent = t('sos.optionCDesc');

        const sosOptDLabel = document.getElementById('sos-option-d-label');
        if (sosOptDLabel) sosOptDLabel.textContent = t('sos.optionDLabel');'''

    new_dom_sos_options = '''        const sosAltHeading = document.getElementById('sos-alt-options-heading');
        if (sosAltHeading) sosAltHeading.textContent = t('sos.altOptionsHeading');

        const sosOptABadge = document.getElementById('sos-option-a-badge');
        if (sosOptABadge) {
            if (currentLang === 'vi') {
                sosOptABadge.textContent = '';
                sosOptABadge.style.display = 'none';
            } else {
                sosOptABadge.style.display = '';
                sosOptABadge.textContent = t('sos.optionABadge');
            }
        }
        const sosOptATitle = document.getElementById('sos-option-a-title');
        if (sosOptATitle) sosOptATitle.textContent = t('sos.optionATitle');
        const sosOptADesc = document.getElementById('sos-option-a-desc');
        if (sosOptADesc) sosOptADesc.textContent = t('sos.optionADesc');

        const sosOptBBadge = document.getElementById('sos-option-b-badge');
        if (sosOptBBadge) {
            if (currentLang === 'vi') {
                sosOptBBadge.textContent = '';
                sosOptBBadge.style.display = 'none';
            } else {
                sosOptBBadge.style.display = '';
                sosOptBBadge.textContent = t('sos.optionBBadge');
            }
        }
        const sosOptBTitle = document.getElementById('sos-option-b-title');
        if (sosOptBTitle) sosOptBTitle.textContent = t('sos.optionBTitle');
        const sosOptBDesc = document.getElementById('sos-option-b-desc');
        if (sosOptBDesc) sosOptBDesc.textContent = t('sos.optionBDesc');

        const sosOptCBadge = document.getElementById('sos-option-c-badge');
        if (sosOptCBadge) {
            if (currentLang === 'vi') {
                sosOptCBadge.textContent = '';
                sosOptCBadge.style.display = 'none';
            } else {
                sosOptCBadge.style.display = '';
                sosOptCBadge.textContent = t('sos.optionCBadge');
            }
        }
        const sosOptCTitle = document.getElementById('sos-option-c-title');
        if (sosOptCTitle) sosOptCTitle.textContent = t('sos.optionCTitle');
        const sosOptCDesc = document.getElementById('sos-option-c-desc');
        if (sosOptCDesc) sosOptCDesc.textContent = t('sos.optionCDesc');

        const sosOptDLabel = document.getElementById('sos-option-d-label');
        if (sosOptDLabel) sosOptDLabel.textContent = t('sos.optionDLabel');'''

    old_dom_sos_options_norm = old_dom_sos_options.replace('\r\n', '\n')
    assert old_dom_sos_options_norm in content_norm, "Old dom sos options not found in i18n.js!"
    content_norm = content_norm.replace(old_dom_sos_options_norm, new_dom_sos_options.replace('\r\n', '\n'))

    # Update drawer trusted quote in applyLanguageToDOM if present
    old_drawer_copy = '''        const drawerCopyBtn = document.getElementById('drawer-copy-btn-text');
        if (drawerCopyBtn) drawerCopyBtn.textContent = t('sos.copyTrustedBtn');'''
    new_drawer_copy = '''        const drawerCopyBtn = document.getElementById('drawer-copy-btn-text');
        if (drawerCopyBtn) drawerCopyBtn.textContent = t('sos.copyTrustedBtn');
        const drawerQuote = document.getElementById('drawer-trusted-quote');
        if (drawerQuote) {
            drawerQuote.textContent = currentLang === 'vi'
                ? '"Chào bạn, mình đang trải qua một khoảng thời gian rất khó khăn và cảm thấy quá tải. Bạn có thể trò chuyện hoặc ngồi cùng mình một lúc được không?"'
                : '"Hey, I\\'m having a really difficult time right now and feeling overwhelmed. Are you free to talk or sit with me for a few minutes?"';
        }'''
    old_drawer_copy_norm = old_drawer_copy.replace('\r\n', '\n')
    assert old_drawer_copy_norm in content_norm, "Old drawer copy not found in i18n.js!"
    content_norm = content_norm.replace(old_drawer_copy_norm, new_drawer_copy.replace('\r\n', '\n'))

    # Convert back to pure CRLF for i18n.js
    content_crlf = content_norm.replace('\n', '\r\n')
    with open('i18n.js', 'wb') as f:
        f.write(content_crlf.encode('utf-8'))
    print("i18n.js updated successfully with CRLF line endings.")

def update_index_html():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Normalize to LF
    content_norm = content.replace('\r\n', '\n')

    # Replace initial static strings in progressive-emergency-modal to match default vi
    old_header = '''                    <div>
                        <h3 id="sos-header-title" class="font-heading text-sm sm:text-base font-bold text-[#202124] leading-tight">SOS · Immediate Support</h3>
                        <p id="sos-header-subtitle" class="text-[11px] text-[#6F6B68]">Your safety comes first</p>
                    </div>'''

    new_header = '''                    <div>
                        <h3 id="sos-header-title" class="font-heading text-sm sm:text-base font-bold text-[#202124] leading-tight">SOS · Hỗ trợ khẩn cấp</h3>
                        <p id="sos-header-subtitle" class="text-[11px] text-[#6F6B68]">An toàn của bạn là ưu tiên hàng đầu</p>
                    </div>'''
    assert old_header in content_norm, "Old header not found in index.html!"
    content_norm = content_norm.replace(old_header, new_header)

    old_pill = '''<span id="sos-pill-get-support">Get support now →</span>'''
    new_pill = '''<span id="sos-pill-get-support">Nhận hỗ trợ ngay →</span>'''
    assert old_pill in content_norm, "Old pill not found in index.html!"
    content_norm = content_norm.replace(old_pill, new_pill)

    old_banner = '''                <div class="flex-1 space-y-0.5">
                    <p id="sos-safety-mode-active-heading" class="font-bold text-[#202124]">Safety Mode Active — Immediate human support is right here.</p>
                    <p id="sos-safety-mode-active-desc" class="text-[11px] text-[#6F6B68] leading-relaxed">You don't need to finish any exercises to speak with someone. You can tap "Get support now →" at any second.</p>
                </div>'''

    new_banner = '''                <div class="flex-1 space-y-0.5">
                    <p id="sos-safety-mode-active-heading" class="font-bold text-[#202124]">Chế độ an toàn đang bật</p>
                    <p id="sos-safety-mode-active-desc" class="text-[11px] text-[#6F6B68] leading-relaxed">Bạn không cần phải trải qua điều này một mình. Hãy để chúng tôi giúp bạn.</p>
                </div>'''
    assert old_banner in content_norm, "Old banner not found in index.html!"
    content_norm = content_norm.replace(old_banner, new_banner)

    old_checkin = '''                    <div class="text-center space-y-1.5 max-w-lg mx-auto">
                        <span id="sos-eyebrow" class="px-3 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider bg-[#93AFBC]/20 text-[#2C4957] inline-block">
                            SOS · Immediate Support
                        </span>
                        <h4 id="sos-main-heading" class="font-heading text-2xl sm:text-3xl font-bold text-[#202124] tracking-tight">
                            I don't feel safe right now
                        </h4>
                    </div>

                    <!-- Emergency Information Card (Pale Warm Blush surface, Deep Ink text, Minimal Red) -->
                    <div class="p-5 sm:p-6 bg-[#ECC9BA]/20 border border-[#ECC9BA]/70 rounded-2xl sm:rounded-3xl space-y-4">
                        <p id="sos-card-situation-intro" class="text-xs font-bold text-[#202124] uppercase tracking-wider">
                            If right now you're:
                        </p>
                        
                        <div class="space-y-2.5">
                            <div class="flex items-start space-x-2.5 p-3 bg-white border border-[#EAE4DF] rounded-xl text-xs sm:text-sm text-[#202124]">
                                <span class="w-2 h-2 rounded-full bg-[#93AFBC] shrink-0 mt-1.5"></span>
                                <span id="sos-situation-1" class="leading-relaxed font-medium">panicking and feel out of control</span>
                            </div>
                            <div class="flex items-start space-x-2.5 p-3 bg-white border border-[#EAE4DF] rounded-xl text-xs sm:text-sm text-[#202124]">
                                <span class="w-2 h-2 rounded-full bg-[#D92D20] shrink-0 mt-1.5"></span>
                                <span id="sos-situation-2" class="leading-relaxed font-medium">having thoughts or urges to hurt yourself</span>
                            </div>
                            <div class="flex items-start space-x-2.5 p-3 bg-white border border-[#EAE4DF] rounded-xl text-xs sm:text-sm text-[#202124]">
                                <span class="w-2 h-2 rounded-full bg-[#8EA28F] shrink-0 mt-1.5"></span>
                                <span id="sos-situation-3" class="leading-relaxed font-medium">not feeling safe being alone</span>
                            </div>
                        </div>

                        <div class="pt-2 border-t border-[#ECC9BA]/60 text-xs sm:text-sm text-[#202124] space-y-0.5">
                            <p id="sos-reassurance-title" class="font-bold text-[#202124]">Your safety comes first.</p>
                            <p id="sos-reassurance-body" class="text-[#6F6B68]">You don't need to handle everything by yourself right now.</p>
                        </div>

                        <!-- Primary Emergency CTA (Solid Red #D92D20 with White Text - Single Red Focal Point) -->
                        <div class="pt-1">
                            <button id="btn-sos-get-support-now" type="button" onclick="window.TempoEmergencySupport.openHumanDrawer()" 
                                class="w-full py-3.5 px-5 bg-[#D92D20] hover:bg-[#B42318] text-white rounded-xl text-sm font-bold shadow-xs hover:shadow-sm transition flex items-center justify-center space-x-2 cursor-pointer">
                                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                                </svg>
                                <span id="sos-cta-label">Get support now →</span>
                            </button>
                        </div>
                    </div>'''

    new_checkin = '''                    <div class="text-center space-y-1.5 max-w-lg mx-auto">
                        <span id="sos-eyebrow" class="px-3 py-0.5 rounded-full text-[11px] font-bold tracking-wider bg-[#93AFBC]/20 text-[#2C4957] inline-block">
                            SOS · Hỗ trợ khẩn cấp
                        </span>
                        <h4 id="sos-main-heading" class="font-heading text-2xl sm:text-3xl font-bold text-[#202124] tracking-tight">
                            Tôi không cảm thấy an toàn lúc này
                        </h4>
                    </div>

                    <!-- Emergency Information Card (Pale Warm Blush surface, Deep Ink text, Minimal Red) -->
                    <div class="p-5 sm:p-6 bg-[#ECC9BA]/20 border border-[#ECC9BA]/70 rounded-2xl sm:rounded-3xl space-y-4">
                        <p id="sos-card-situation-intro" class="text-xs font-bold text-[#202124] tracking-wider">
                            Nếu ngay lúc này bạn đang:
                        </p>
                        
                        <div class="space-y-2.5">
                            <div class="flex items-start space-x-2.5 p-3 bg-white border border-[#EAE4DF] rounded-xl text-xs sm:text-sm text-[#202124]">
                                <span class="w-2 h-2 rounded-full bg-[#93AFBC] shrink-0 mt-1.5"></span>
                                <span id="sos-situation-1" class="leading-relaxed font-medium">Hoảng loạn và cảm thấy mất kiểm soát</span>
                            </div>
                            <div class="flex items-start space-x-2.5 p-3 bg-white border border-[#EAE4DF] rounded-xl text-xs sm:text-sm text-[#202124]">
                                <span class="w-2 h-2 rounded-full bg-[#D92D20] shrink-0 mt-1.5"></span>
                                <span id="sos-situation-2" class="leading-relaxed font-medium">Có suy nghĩ hoặc thôi thúc làm tổn thương bản thân</span>
                            </div>
                            <div class="flex items-start space-x-2.5 p-3 bg-white border border-[#EAE4DF] rounded-xl text-xs sm:text-sm text-[#202124]">
                                <span class="w-2 h-2 rounded-full bg-[#8EA28F] shrink-0 mt-1.5"></span>
                                <span id="sos-situation-3" class="leading-relaxed font-medium">Cảm thấy không an toàn khi ở một mình</span>
                            </div>
                        </div>

                        <div class="pt-2 border-t border-[#ECC9BA]/60 text-xs sm:text-sm text-[#202124] space-y-0.5">
                            <p id="sos-reassurance-title" class="font-bold text-[#202124]">An toàn của bạn là ưu tiên hàng đầu.</p>
                            <p id="sos-reassurance-body" class="text-[#6F6B68]">Bạn không cần phải tự mình vượt qua tất cả.</p>
                        </div>

                        <!-- Primary Emergency CTA (Solid Red #D92D20 with White Text - Single Red Focal Point) -->
                        <div class="pt-1">
                            <button id="btn-sos-get-support-now" type="button" onclick="window.TempoEmergencySupport.openHumanDrawer()" 
                                class="w-full py-3.5 px-5 bg-[#D92D20] hover:bg-[#B42318] text-white rounded-xl text-sm font-bold shadow-xs hover:shadow-sm transition flex items-center justify-center space-x-2 cursor-pointer">
                                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                                </svg>
                                <span id="sos-cta-label">Nhận hỗ trợ ngay →</span>
                            </button>
                        </div>
                    </div>'''
    assert old_checkin in content_norm, "Old checkin block not found in index.html!"
    content_norm = content_norm.replace(old_checkin, new_checkin)

    old_options = '''                    <div class="text-center">
                        <p id="sos-alt-options-heading" class="text-xs font-bold text-[#6F6B68] uppercase tracking-wider">
                            Or choose what you need right now
                        </p>
                    </div>

                    <!-- Option A: Overwhelmed / Panicking (Pale Sage Green Tint & Accent) -->
                    <button type="button" onclick="window.TempoEmergencySupport.handleInitialCheckin('overwhelmed')" 
                        class="w-full p-4 sm:p-5 rounded-2xl border border-[#8EA28F]/35 bg-[#8EA28F]/10 hover:border-[#8EA28F] hover:bg-[#8EA28F]/15 text-left transition group cursor-pointer shadow-2xs">
                        <div class="flex items-start justify-between gap-3">
                            <div class="space-y-1">
                                <span id="sos-option-a-badge" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#8EA28F] text-white">
                                    Option A
                                </span>
                                <h5 id="sos-option-a-title" class="text-sm sm:text-base font-bold text-[#202124] group-hover:text-[#3B5C43] transition">
                                    I'm overwhelmed or panicking
                                </h5>
                                <p id="sos-option-a-desc" class="text-xs text-[#6F6B68] leading-relaxed">
                                    I feel stressed, overwhelmed, or unable to think clearly.
                                </p>
                            </div>
                            <span class="text-[#3B5C43] group-hover:translate-x-1 transition-transform text-lg font-bold shrink-0 mt-1">→</span>
                        </div>
                    </button>

                    <!-- Option B: Emotional Crisis (Pale Dusty Blue Tint & Accent) -->
                    <button type="button" onclick="window.TempoEmergencySupport.handleInitialCheckin('crisis')" 
                        class="w-full p-4 sm:p-5 rounded-2xl border border-[#93AFBC]/40 bg-[#93AFBC]/10 hover:border-[#93AFBC] hover:bg-[#93AFBC]/15 text-left transition group cursor-pointer shadow-2xs">
                        <div class="flex items-start justify-between gap-3">
                            <div class="space-y-1">
                                <span id="sos-option-b-badge" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#93AFBC] text-white">
                                    Option B • Immediate Support
                                </span>
                                <h5 id="sos-option-b-title" class="text-sm sm:text-base font-bold text-[#202124] group-hover:text-[#2C4957] transition">
                                    I'm in an emotional crisis or don't feel safe
                                </h5>
                                <p id="sos-option-b-desc" class="text-xs text-[#6F6B68] leading-relaxed">
                                    I'm experiencing intense emotional distress and need immediate support.
                                </p>
                            </div>
                            <span class="text-[#2C4957] group-hover:translate-x-1 transition-transform text-lg font-bold shrink-0 mt-1">→</span>
                        </div>
                    </button>

                    <!-- Option C: Self Harm / Suicide Risk (White Card, Deep Ink Title, Subtle Red Indicator Badge) -->
                    <button type="button" onclick="window.TempoEmergencySupport.handleInitialCheckin('selfharm')" 
                        class="w-full p-4 sm:p-5 rounded-2xl border border-[#EAE4DF] hover:border-[#D92D20]/50 bg-white hover:bg-[#D92D20]/5 text-left transition group cursor-pointer shadow-2xs">
                        <div class="flex items-start justify-between gap-3">
                            <div class="space-y-1">
                                <span id="sos-option-c-badge" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#D92D20]/15 text-[#D92D20]">
                                    Option C • Urgent Care
                                </span>
                                <h5 id="sos-option-c-title" class="text-sm sm:text-base font-bold text-[#202124] group-hover:text-[#D92D20] transition">
                                    I'm thinking about hurting myself or suicide
                                </h5>
                                <p id="sos-option-c-desc" class="text-xs text-[#6F6B68] leading-relaxed">
                                    I'm having thoughts about harming myself or ending my life.
                                </p>
                            </div>
                            <span class="text-[#D92D20] group-hover:translate-x-1 transition-transform text-lg font-bold shrink-0 mt-1">→</span>
                        </div>
                    </button>

                    <!-- Option D: I'm not sure (Neutral White / Subtle Sage Green Hover) -->
                    <button type="button" onclick="window.TempoEmergencySupport.handleInitialCheckin('notsure')" 
                        class="w-full p-3.5 sm:p-4 rounded-2xl border border-[#EAE4DF] hover:border-[#8EA28F] hover:bg-[#8EA28F]/5 bg-white text-left transition text-center text-xs font-semibold text-[#6F6B68] hover:text-[#202124] cursor-pointer">
                        <span id="sos-option-d-label">I'm not sure — my mind is racing and I just need help slowing down</span>
                    </button>'''

    new_options = '''                    <div class="text-center">
                        <p id="sos-alt-options-heading" class="text-xs font-bold text-[#6F6B68] tracking-wider">
                            Hoặc chọn điều bạn cần lúc này
                        </p>
                    </div>

                    <!-- Option A: Overwhelmed / Panicking (Pale Sage Green Tint & Accent) -->
                    <button type="button" onclick="window.TempoEmergencySupport.handleInitialCheckin('overwhelmed')" 
                        class="w-full p-4 sm:p-5 rounded-2xl border border-[#8EA28F]/35 bg-[#8EA28F]/10 hover:border-[#8EA28F] hover:bg-[#8EA28F]/15 text-left transition group cursor-pointer shadow-2xs">
                        <div class="flex items-start justify-between gap-3">
                            <div class="space-y-1">
                                <span id="sos-option-a-badge" style="display:none;" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#8EA28F] text-white">
                                    Lựa chọn A
                                </span>
                                <h5 id="sos-option-a-title" class="text-sm sm:text-base font-bold text-[#202124] group-hover:text-[#3B5C43] transition">
                                    Lựa chọn A · Quá tải hoặc hoảng loạn
                                </h5>
                                <p id="sos-option-a-desc" class="text-xs text-[#6F6B68] leading-relaxed">
                                    Tôi cảm thấy căng thẳng, quá tải hoặc không thể suy nghĩ rõ ràng.
                                </p>
                            </div>
                            <span class="text-[#3B5C43] group-hover:translate-x-1 transition-transform text-lg font-bold shrink-0 mt-1">→</span>
                        </div>
                    </button>

                    <!-- Option B: Emotional Crisis (Pale Dusty Blue Tint & Accent) -->
                    <button type="button" onclick="window.TempoEmergencySupport.handleInitialCheckin('crisis')" 
                        class="w-full p-4 sm:p-5 rounded-2xl border border-[#93AFBC]/40 bg-[#93AFBC]/10 hover:border-[#93AFBC] hover:bg-[#93AFBC]/15 text-left transition group cursor-pointer shadow-2xs">
                        <div class="flex items-start justify-between gap-3">
                            <div class="space-y-1">
                                <span id="sos-option-b-badge" style="display:none;" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#93AFBC] text-white">
                                    Lựa chọn B
                                </span>
                                <h5 id="sos-option-b-title" class="text-sm sm:text-base font-bold text-[#202124] group-hover:text-[#2C4957] transition">
                                    Lựa chọn B · Khủng hoảng cảm xúc
                                </h5>
                                <p id="sos-option-b-desc" class="text-xs text-[#6F6B68] leading-relaxed">
                                    Tôi đang trải qua trạng thái cảm xúc rất tiêu cực và cần được hỗ trợ ngay.
                                </p>
                            </div>
                            <span class="text-[#2C4957] group-hover:translate-x-1 transition-transform text-lg font-bold shrink-0 mt-1">→</span>
                        </div>
                    </button>

                    <!-- Option C: Self Harm / Suicide Risk (White Card, Deep Ink Title, Subtle Red Indicator Badge) -->
                    <button type="button" onclick="window.TempoEmergencySupport.handleInitialCheckin('selfharm')" 
                        class="w-full p-4 sm:p-5 rounded-2xl border border-[#EAE4DF] hover:border-[#D92D20]/50 bg-white hover:bg-[#D92D20]/5 text-left transition group cursor-pointer shadow-2xs">
                        <div class="flex items-start justify-between gap-3">
                            <div class="space-y-1">
                                <span id="sos-option-c-badge" style="display:none;" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#D92D20]/15 text-[#D92D20]">
                                    Lựa chọn C
                                </span>
                                <h5 id="sos-option-c-title" class="text-sm sm:text-base font-bold text-[#202124] group-hover:text-[#D92D20] transition">
                                    Lựa chọn C · Cần hỗ trợ khẩn cấp
                                </h5>
                                <p id="sos-option-c-desc" class="text-xs text-[#6F6B68] leading-relaxed">
                                    Tôi đang nghĩ đến việc làm tổn thương bản thân hoặc tự tử.
                                </p>
                            </div>
                            <span class="text-[#D92D20] group-hover:translate-x-1 transition-transform text-lg font-bold shrink-0 mt-1">→</span>
                        </div>
                    </button>

                    <!-- Option D: I'm not sure (Neutral White / Subtle Sage Green Hover) -->
                    <button type="button" onclick="window.TempoEmergencySupport.handleInitialCheckin('notsure')" 
                        class="w-full p-3.5 sm:p-4 rounded-2xl border border-[#EAE4DF] hover:border-[#8EA28F] hover:bg-[#8EA28F]/5 bg-white text-left transition text-center text-xs font-semibold text-[#6F6B68] hover:text-[#202124] cursor-pointer">
                        <span id="sos-option-d-label">Tôi không chắc — đầu óc tôi đang rối bời và tôi chỉ muốn được giúp bình tĩnh lại.</span>
                    </button>'''
    assert old_options in content_norm, "Old options block not found in index.html!"
    content_norm = content_norm.replace(old_options, new_options)

    # Pure LF for index.html
    with open('index.html', 'wb') as f:
        f.write(content_norm.encode('utf-8'))
    print("index.html updated successfully with LF line endings.")

if __name__ == '__main__':
    update_i18n()
    update_index_html()
