# -*- coding: utf-8 -*-
import sys

def update_emergency_support_js():
    with open('emergencySupport.js', 'r', encoding='utf-8') as f:
        content = f.read()

    target = '''        crisisHotline: {
            title_vi: 'Đường dây nóng Khủng hoảng & Hỗ trợ Tâm lý HOPE',
            title_en: 'HOPE — Suicide Prevention Hotline',
            phone: '0865 044 400',
            callHref: 'tel:0865044400',
            details_vi: "Nếu bạn đang trong cơn khủng hoảng, có suy nghĩ tự hại hoặc cần người lắng nghe ngay bây giờ.",
            details_en: "If you're in crisis, having thoughts of hurting yourself, or need someone to support you right now."
        },'''

    replacement = '''        crisisHotline: {
            title_vi: 'Đường dây nóng Khủng hoảng & Hỗ trợ Tâm lý HOPE',
            title_en: 'HOPE — Suicide Prevention Hotline',
            phone: '0865 044 400',
            callHref: 'tel:0865044400',
            details_vi: "Nếu bạn đang trong cơn khủng hoảng, có suy nghĩ tự hại hoặc cần người lắng nghe ngay bây giờ.",
            details_en: "If you're in crisis, having thoughts of hurting yourself, or need someone to support you right now."
        },
        ngayMaiHotline: {
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

    content_norm = content.replace('\r\n', '\n')
    target_norm = target.replace('\r\n', '\n')
    replacement_norm = replacement.replace('\r\n', '\n')

    assert target_norm in content_norm, "crisisHotline target not found in emergencySupport.js"
    content_norm = content_norm.replace(target_norm, replacement_norm)

    # Pure CRLF for emergencySupport.js
    content_crlf = content_norm.replace('\n', '\r\n')
    with open('emergencySupport.js', 'wb') as f:
        f.write(content_crlf.encode('utf-8'))
    print("emergencySupport.js updated successfully.")

def update_i18n_js():
    with open('i18n.js', 'r', encoding='utf-8') as f:
        content = f.read()

    content_norm = content.replace('\r\n', '\n')

    # 1. Add to vi.sos
    target_vi = '''                hotlineTitle: "Đường dây nóng Khủng hoảng & Hỗ trợ Tâm lý HOPE",
                hotlineDesc: "Nếu bạn đang trong cơn khủng hoảng, có suy nghĩ tự hại hoặc cần người lắng nghe ngay bây giờ.",
                hotlineCall: "Gọi 0865 044 400",'''

    replacement_vi = '''                hotlineTitle: "Đường dây nóng Khủng hoảng & Hỗ trợ Tâm lý HOPE",
                hotlineDesc: "Nếu bạn đang trong cơn khủng hoảng, có suy nghĩ tự hại hoặc cần người lắng nghe ngay bây giờ.",
                hotlineCall: "Gọi 0865 044 400",
                ngayMaiTitle: "ĐƯỜNG DÂY NÓNG NGÀY MAI",
                ngayMaiBadge: "Hỗ trợ tâm lý",
                ngayMaiPhone: "096 306 1414",
                ngayMaiDesc: "Hỗ trợ tâm lý miễn phí qua điện thoại cho người đang gặp khủng hoảng tâm lý, trầm cảm và người thân của họ. Lắng nghe không phán xét, bảo mật thông tin.",
                ngayMaiHours: "13:00 – 20:30, Thứ Tư – Chủ Nhật",
                ngayMaiCall: "Gọi 096 306 1414",'''

    assert target_vi in content_norm, "vi hotline target not found in i18n.js"
    content_norm = content_norm.replace(target_vi, replacement_vi)

    # 2. Add to en.sos
    target_en = '''                hotlineTitle: "HOPE — Suicide Prevention Hotline",
                hotlineDesc: "If you're in crisis, having thoughts of hurting yourself, or need someone to support you right now.",
                hotlineCall: "Call 0865 044 400",'''

    replacement_en = '''                hotlineTitle: "HOPE — Suicide Prevention Hotline",
                hotlineDesc: "If you're in crisis, having thoughts of hurting yourself, or need someone to support you right now.",
                hotlineCall: "Call 0865 044 400",
                ngayMaiTitle: "NGÀY MAI SUPPORT HOTLINE",
                ngayMaiBadge: "Mental Health Support",
                ngayMaiPhone: "096 306 1414",
                ngayMaiDesc: "Free psychological first aid by phone for people experiencing emotional distress or depression, and their loved ones. Confidential and non-judgmental support.",
                ngayMaiHours: "1:00 PM – 8:30 PM, Wednesday – Sunday",
                ngayMaiCall: "Call 096 306 1414",'''

    assert target_en in content_norm, "en hotline target not found in i18n.js"
    content_norm = content_norm.replace(target_en, replacement_en)

    # 3. Add to applyLanguageToDOM
    target_dom = '''        const drawerHotlineTitle = document.getElementById('drawer-hotline-title');
        if (drawerHotlineTitle) drawerHotlineTitle.textContent = t('sos.hotlineTitle');
        const drawerHotlineDesc = document.getElementById('drawer-hotline-desc');
        if (drawerHotlineDesc) drawerHotlineDesc.textContent = t('sos.hotlineDesc');
        const drawerHotlineCall = document.getElementById('drawer-hotline-call');
        if (drawerHotlineCall) drawerHotlineCall.textContent = t('sos.hotlineCall');'''

    replacement_dom = '''        const drawerHotlineTitle = document.getElementById('drawer-hotline-title');
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
        if (step5aNgayMaiCall) step5aNgayMaiCall.textContent = t('sos.ngayMaiCall');'''

    assert target_dom in content_norm, "applyLanguageToDOM hotline target not found in i18n.js"
    content_norm = content_norm.replace(target_dom, replacement_dom)

    # Pure CRLF for i18n.js
    content_crlf = content_norm.replace('\n', '\r\n')
    with open('i18n.js', 'wb') as f:
        f.write(content_crlf.encode('utf-8'))
    print("i18n.js updated successfully.")

def update_index_html():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    content_norm = content.replace('\r\n', '\n')

    # 1. Add Ngày Mai card to #emergency-step-still_unsafe (Step 5A)
    target_step5a = '''                    <!-- HOPE — Suicide Prevention Hotline (Dusty Blue Accent) -->
                    <div class="p-4 sm:p-5 bg-white border border-[#93AFBC]/40 rounded-2xl flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 shadow-2xs">
                        <div class="space-y-0.5">
                            <div class="flex items-center space-x-2">
                                <h5 class="text-sm font-bold text-[#202124]">HOPE — Suicide Prevention Hotline</h5>
                                <span class="px-2.5 py-0.5 bg-[#93AFBC]/25 text-[#2C4957] text-[10px] font-bold rounded-full">Crisis Support</span>
                            </div>
                            <div class="text-lg font-extrabold text-[#202124]">0865 044 400</div>
                            <p class="text-xs text-[#6F6B68]">If you're in crisis, having thoughts of hurting yourself, or need someone to support you right now.</p>
                        </div>
                        <a href="tel:0865044400" class="px-5 py-2.5 bg-[#202124] hover:bg-black text-white rounded-xl text-xs font-bold transition shadow-xs shrink-0 text-center">Call 0865 044 400</a>
                    </div>

                    <!-- While Waiting For Support Guidance (Pale Sage Green Tint) -->'''

    replacement_step5a = '''                    <!-- HOPE — Suicide Prevention Hotline (Dusty Blue Accent) -->
                    <div class="p-4 sm:p-5 bg-white border border-[#93AFBC]/40 rounded-2xl flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 shadow-2xs">
                        <div class="space-y-0.5">
                            <div class="flex items-center space-x-2">
                                <h5 class="text-sm font-bold text-[#202124]">HOPE — Suicide Prevention Hotline</h5>
                                <span class="px-2.5 py-0.5 bg-[#93AFBC]/25 text-[#2C4957] text-[10px] font-bold rounded-full">Crisis Support</span>
                            </div>
                            <div class="text-lg font-extrabold text-[#202124]">0865 044 400</div>
                            <p class="text-xs text-[#6F6B68]">If you're in crisis, having thoughts of hurting yourself, or need someone to support you right now.</p>
                        </div>
                        <a href="tel:0865044400" class="px-5 py-2.5 bg-[#202124] hover:bg-black text-white rounded-xl text-xs font-bold transition shadow-xs shrink-0 text-center">Call 0865 044 400</a>
                    </div>

                    <!-- Ngày Mai Support Hotline (Dusty Blue & Sage Green Accent) -->
                    <div id="step5a-card-ngaymai" class="p-4 sm:p-5 bg-white border border-[#8EA28F]/40 rounded-2xl flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 shadow-2xs">
                        <div class="space-y-1">
                            <div class="flex items-center space-x-2">
                                <h5 id="step5a-ngaymai-title" class="text-sm font-bold text-[#202124]">ĐƯỜNG DÂY NÓNG NGÀY MAI</h5>
                                <span id="step5a-ngaymai-badge" class="px-2.5 py-0.5 bg-[#8EA28F]/20 text-[#3B5C43] text-[10px] font-bold rounded-full">Hỗ trợ tâm lý</span>
                            </div>
                            <div class="text-lg font-extrabold text-[#202124]">096 306 1414</div>
                            <p id="step5a-ngaymai-desc" class="text-xs text-[#6F6B68]">Hỗ trợ tâm lý miễn phí qua điện thoại cho người đang gặp khủng hoảng tâm lý, trầm cảm và người thân của họ. Lắng nghe không phán xét, bảo mật thông tin.</p>
                            <div class="flex items-center space-x-1.5 text-[11px] font-semibold text-[#4A6A78] bg-[#93AFBC]/15 px-2.5 py-1 rounded-lg w-fit">
                                <svg class="w-3.5 h-3.5 text-[#4A6A78] shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                                </svg>
                                <span id="step5a-ngaymai-hours">13:00 – 20:30, Thứ Tư – Chủ Nhật</span>
                            </div>
                        </div>
                        <a id="step5a-ngaymai-call" href="tel:0963061414" class="px-5 py-2.5 bg-[#8EA28F] hover:bg-[#7D917E] text-white rounded-xl text-xs font-bold transition shadow-xs shrink-0 text-center">Gọi 096 306 1414</a>
                    </div>

                    <!-- While Waiting For Support Guidance (Pale Sage Green Tint) -->'''

    assert target_step5a in content_norm, "target_step5a not found in index.html"
    content_norm = content_norm.replace(target_step5a, replacement_step5a)

    # 2. Add Ngày Mai card to #human-support-drawer
    target_drawer = '''                    <!-- HOPE — Suicide Prevention Hotline (Dusty Blue Accent) -->
                    <div class="p-4 bg-white border border-[#93AFBC]/40 rounded-2xl space-y-2 shadow-2xs">
                        <div class="flex items-center justify-between">
                            <span id="drawer-hotline-title" class="text-xs font-bold text-[#202124] uppercase tracking-wider">HOPE — Suicide Prevention Hotline</span>
                            <span class="px-2 py-0.5 bg-[#93AFBC]/25 text-[#2C4957] text-[10px] font-bold rounded-full">Crisis Support</span>
                        </div>
                        <div class="text-lg font-extrabold text-[#202124] tracking-tight">0865 044 400</div>
                        <p id="drawer-hotline-desc" class="text-xs text-[#6F6B68]">If you're in crisis, having thoughts of hurting yourself, or need someone to support you right now.</p>
                        <a id="drawer-hotline-call" href="tel:0865044400" class="inline-block mt-1 px-4 py-2 bg-[#202124] hover:bg-black text-white rounded-xl text-xs font-bold transition shadow-xs">Call 0865 044 400</a>
                    </div>

                    <!-- While Waiting For Support Guidance (Pale Sage Green Tint) -->'''

    replacement_drawer = '''                    <!-- HOPE — Suicide Prevention Hotline (Dusty Blue Accent) -->
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

                    <!-- While Waiting For Support Guidance (Pale Sage Green Tint) -->'''

    assert target_drawer in content_norm, "target_drawer not found in index.html"
    content_norm = content_norm.replace(target_drawer, replacement_drawer)

    # Pure LF for index.html
    with open('index.html', 'wb') as f:
        f.write(content_norm.encode('utf-8'))
    print("index.html updated successfully.")

if __name__ == '__main__':
    update_emergency_support_js()
    update_i18n_js()
    update_index_html()
