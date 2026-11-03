import os

# 1. Update i18n.js
with open('i18n.js', 'r', encoding='utf-8') as f:
    i18n_code = f.read()

# Update Vietnamese selfCheckWorkspace
vi_target = """            selfCheckWorkspace: {
                title: "Tự kiểm tra Tempo",
                returnUrgent: "Quay lại Chế độ khẩn cấp",
                returnRecovery: "Quay lại Chế độ phục hồi",
                returnUnclear: "Quay lại Chế độ mơ hồ",
                returnHome: "Quay lại trang chủ",
                returnUrgentWithArrow: "← Quay lại Chế độ khẩn cấp",
                dailyCheckinUpper: "CHECK-IN HẰNG NGÀY",
                todaysCheckin: "Check-in hôm nay",
                streakDays: "Chuỗi {count} ngày",
                sleepQuestion: "Bạn ngủ thế nào vào tối qua?",
                good: "Tốt",
                notGood: "Chưa tốt",
                walkQuestion: "Hôm nay bạn có đi bộ không?",
                yes: "Có",
                noIdidnt: "Không",
                createNoteForToday: "Tạo ghi chú hôm nay",
                checkedInCount: "Bạn đã check-in {completed}/{total} mục hôm nay.",
                yourTrackingSystem: "Hệ thống tracking của bạn",
                addTracking: "Thêm tracking",
                clearAll: "Xóa tất cả",
                adjust: "Chỉnh sửa",
                tension: "Căng thẳng",
                sleep: "Giấc ngủ",
                walk: "Đi bộ",
                avgTensionLevel: "Mức độ căng thẳng trung bình của bạn là",
                nightsQualitySleep: "Số đêm ngủ ngon","""

vi_replacement = """            selfCheckWorkspace: {
                title: "Tự kiểm tra Tempo",
                returnUrgent: "Quay lại Chế độ khẩn cấp",
                returnRecovery: "Quay lại Dashboard",
                returnUnclear: "Quay lại Chế độ mơ hồ",
                returnHome: "Quay lại trang chủ",
                returnUrgentWithArrow: "← Quay lại Chế độ khẩn cấp",
                returnRecoveryWithArrow: "← Quay lại Dashboard",
                dailyCheckinUpper: "CHECK-IN HẰNG NGÀY",
                todaysCheckin: "Check-in hôm nay",
                streakDays: "Chuỗi {count} ngày",
                sleepQuestion: "Bạn ngủ thế nào vào tối qua?",
                good: "Tốt",
                notGood: "Chưa tốt",
                walkQuestion: "Hôm nay bạn có đi bộ không?",
                yes: "Có",
                noIdidnt: "Không",
                createNoteForToday: "Tạo ghi chú hôm nay",
                checkedInCount: "Bạn đã check-in {completed}/{total} mục hôm nay.",
                yourTrackingSystem: "Các mục tracking của bạn",
                addTracking: "Thêm mục tracking",
                clearAll: "Xóa tất cả",
                adjust: "Chỉnh sửa",
                tension: "Căng thẳng",
                sleep: "Giấc ngủ",
                walk: "Đi bộ",
                avgTensionLevel: "Mức căng thẳng trung bình",
                nightsQualitySleep: "Số đêm có giấc ngủ tốt","""

assert vi_target in i18n_code, "vi_target not found in i18n.js"
i18n_code = i18n_code.replace(vi_target, vi_replacement, 1)

# English section: add returnRecoveryWithArrow for symmetry
en_target = """                returnHome: "Return Home",
                returnUrgentWithArrow: "Return to Urgent Mode","""

en_replacement = """                returnHome: "Return Home",
                returnUrgentWithArrow: "Return to Urgent Mode",
                returnRecoveryWithArrow: "Return to Recovery Mode","""

if en_target in i18n_code:
    i18n_code = i18n_code.replace(en_target, en_replacement, 1)

i18n_code = i18n_code.replace('\r\n', '\n')
assert '\r' not in i18n_code, "CRLF found in i18n.js"

with open('i18n.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(i18n_code)
print("i18n.js updated successfully")


# 2. Update selfCheckWorkspace.js
with open('selfCheckWorkspace.js', 'r', encoding='utf-8') as f:
    scw_code = f.read()

# Update metricLabel calculation
target_metrics = """        if (tracker.check_method === 'percentage' || nameLower.includes('tension') || nameLower.includes('căng thẳng')) {
            const avg = countNumeric > 0 ? `${Math.round(sum / countNumeric)}%` : '0%';
            metricLabel = (nameLower.includes('tension') || nameLower.includes('căng thẳng'))
                ? (isVi ? 'Mức độ căng thẳng trung bình của bạn là' : 'Your average tension level is')
                : (isVi ? `Mức độ ${escapeHTML(formatTrackerDisplayName(tracker.name).toLowerCase())} trung bình của bạn là` : `Your average ${escapeHTML(nameLower)} level is`);
            metricValue = avg;
        } else if (tracker.check_method === 'yes_no' || nameLower.includes('sleep') || nameLower.includes('giấc ngủ')) {
            metricLabel = isVi ? 'Số đêm ngủ ngon' : 'Nights of Quality Sleep';
            metricValue = `${goodCount}`;"""

refined_metrics = """        if (tracker.check_method === 'percentage' || nameLower.includes('tension') || nameLower.includes('căng thẳng')) {
            const avg = countNumeric > 0 ? `${Math.round(sum / countNumeric)}%` : '0%';
            metricLabel = (nameLower.includes('tension') || nameLower.includes('căng thẳng'))
                ? (window.t ? window.t('selfCheckWorkspace.avgTensionLevel', {}, isVi ? 'Mức căng thẳng trung bình' : 'Your average tension level is') : (isVi ? 'Mức căng thẳng trung bình' : 'Your average tension level is'))
                : (isVi ? `Mức độ ${escapeHTML(formatTrackerDisplayName(tracker.name).toLowerCase())} trung bình của bạn là` : `Your average ${escapeHTML(nameLower)} level is`);
            metricValue = avg;
        } else if (tracker.check_method === 'yes_no' || nameLower.includes('sleep') || nameLower.includes('giấc ngủ')) {
            metricLabel = window.t ? window.t('selfCheckWorkspace.nightsQualitySleep', {}, isVi ? 'Số đêm có giấc ngủ tốt' : 'Nights of Quality Sleep') : (isVi ? 'Số đêm có giấc ngủ tốt' : 'Nights of Quality Sleep');
            metricValue = `${goodCount}`;"""

assert target_metrics in scw_code, "target_metrics not found in selfCheckWorkspace.js"
scw_code = scw_code.replace(target_metrics, refined_metrics, 1)

# Update empty state button (line 2914)
target_empty_btn = """                    <div class="pt-2">
                        <button type="button" 
                                onclick="window.TempoSelfCheckWorkspace.openAddTracking()"
                                class="px-4 py-2 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shadow-2xs inline-flex items-center space-x-1.5">
                            <span>+ ${isVi ? 'Thêm tracking' : 'Add Tracking'}</span>
                        </button>
                    </div>"""

refined_empty_btn = """                    <div class="pt-2">
                        <button type="button" 
                                onclick="window.TempoSelfCheckWorkspace.openAddTracking()"
                                class="px-4 py-2 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shadow-2xs inline-flex items-center space-x-1.5">
                            <span>+ ${window.t ? window.t('selfCheckWorkspace.addTracking', {}, isVi ? 'Thêm mục tracking' : 'Add Tracking') : (isVi ? 'Thêm mục tracking' : 'Add Tracking')}</span>
                        </button>
                    </div>"""

assert target_empty_btn in scw_code, "target_empty_btn not found in selfCheckWorkspace.js"
scw_code = scw_code.replace(target_empty_btn, refined_empty_btn, 1)

# Update returnLabel logic (line 3065)
target_return_label = """        let returnLabel = isVi ? 'Quay lại trang chủ' : 'Return Home';
        if (originMode === 'emergency') {
            returnLabel = isVi ? 'Quay lại Chế độ khẩn cấp' : 'Return to Urgent Mode';
        } else if (originMode === 'recovery') {
            returnLabel = isVi ? 'Quay lại Chế độ phục hồi' : 'Return to Recovery Mode';
        } else if (originMode === 'unclear') {
            returnLabel = isVi ? 'Quay lại Chế độ mơ hồ' : 'Return to Unclear Mode';
        }
        const returnTitle = isVi ? (originMode === 'emergency' ? '← Quay lại Chế độ khẩn cấp' : `← ${returnLabel}`) : returnLabel;"""

refined_return_label = """        let returnLabel = isVi ? 'Quay lại trang chủ' : 'Return Home';
        if (originMode === 'emergency') {
            returnLabel = isVi ? (window.t ? window.t('selfCheckWorkspace.returnUrgent', {}, 'Quay lại Chế độ khẩn cấp') : 'Quay lại Chế độ khẩn cấp') : 'Return to Urgent Mode';
        } else if (originMode === 'recovery') {
            returnLabel = isVi ? (window.t ? window.t('selfCheckWorkspace.returnRecovery', {}, 'Quay lại Dashboard') : 'Quay lại Dashboard') : 'Return to Recovery Mode';
        } else if (originMode === 'unclear') {
            returnLabel = isVi ? (window.t ? window.t('selfCheckWorkspace.returnUnclear', {}, 'Quay lại Chế độ mơ hồ') : 'Quay lại Chế độ mơ hồ') : 'Return to Unclear Mode';
        }
        const returnTitle = isVi ? (originMode === 'emergency' ? '← Quay lại Chế độ khẩn cấp' : (returnLabel.startsWith('←') ? returnLabel : `← ${returnLabel}`)) : returnLabel;"""

assert target_return_label in scw_code, "target_return_label not found in selfCheckWorkspace.js"
scw_code = scw_code.replace(target_return_label, refined_return_label, 1)

# Update right column title and buttons (line 3220)
target_right_header = """                        <!-- Header: Title + Add Tracking + Clear all -->
                        <div class="flex items-center justify-between gap-3 pb-1">
                            <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#1B4332]">
                                ${isVi ? 'Hệ thống tracking của bạn' : 'Your Tracking System'}
                            </h2>
                            <div class="flex items-center space-x-2">
                                <button type="button" 
                                        onclick="window.TempoSelfCheckWorkspace.openAddTracking()"
                                        class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shadow-2xs">
                                    ${isVi ? 'Thêm tracking' : 'Add Tracking'}
                                </button>
                                <button type="button" 
                                        onclick="window.TempoSelfCheckWorkspace.promptClearAll()"
                                        class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#C8322B] hover:bg-[#B32B25] text-white transition cursor-pointer shadow-2xs">
                                    ${isVi ? 'Xóa tất cả' : 'Clear all'}
                                </button>
                            </div>
                        </div>"""

refined_right_header = """                        <!-- Header: Title + Add Tracking + Clear all -->
                        <div class="flex items-center justify-between gap-3 pb-1">
                            <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#1B4332]">
                                ${window.t ? window.t('selfCheckWorkspace.yourTrackingSystem', {}, isVi ? 'Các mục tracking của bạn' : 'Your Tracking System') : (isVi ? 'Các mục tracking của bạn' : 'Your Tracking System')}
                            </h2>
                            <div class="flex items-center space-x-2">
                                <button type="button" 
                                        onclick="window.TempoSelfCheckWorkspace.openAddTracking()"
                                        class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shadow-2xs">
                                    ${window.t ? window.t('selfCheckWorkspace.addTracking', {}, isVi ? 'Thêm mục tracking' : 'Add Tracking') : (isVi ? 'Thêm mục tracking' : 'Add Tracking')}
                                </button>
                                <button type="button" 
                                        onclick="window.TempoSelfCheckWorkspace.promptClearAll()"
                                        class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#C8322B] hover:bg-[#B32B25] text-white transition cursor-pointer shadow-2xs">
                                    ${window.t ? window.t('selfCheckWorkspace.clearAll', {}, isVi ? 'Xóa tất cả' : 'Clear all') : (isVi ? 'Xóa tất cả' : 'Clear all')}
                                </button>
                            </div>
                        </div>"""

assert target_right_header in scw_code, "target_right_header not found in selfCheckWorkspace.js"
scw_code = scw_code.replace(target_right_header, refined_right_header, 1)

scw_code = scw_code.replace('\r\n', '\n')
assert '\r' not in scw_code, "CRLF found in selfCheckWorkspace.js"

with open('selfCheckWorkspace.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(scw_code)
print("selfCheckWorkspace.js updated successfully")


# 3. Update mode.js
with open('mode.js', 'r', encoding='utf-8') as f:
    mode_code = f.read()

target_mode_sc = """        const scHomeText = document.getElementById('selfcheck-return-home-text');
        if (scHomeText) {
            const isVi = (window.TempoI18n && typeof window.TempoI18n.getLanguage === 'function') ? (window.TempoI18n.getLanguage() === 'vi') : false;
            if (sourceContext === 'recovery') scHomeText.textContent = isVi ? 'Quay lại Chế độ phục hồi' : 'Return to Recovery Mode';
            else if (sourceContext === 'emergency') scHomeText.textContent = isVi ? 'Quay lại Chế độ khẩn cấp' : 'Return to Urgent Mode';
            else if (sourceContext === 'unclear') scHomeText.textContent = isVi ? 'Quay lại Chế độ mơ hồ' : 'Return to Unclear Mode';
            else scHomeText.textContent = isVi ? 'Quay lại trang chủ' : 'Return Home';
        }"""

refined_mode_sc = """        const scHomeText = document.getElementById('selfcheck-return-home-text');
        if (scHomeText) {
            const isVi = (window.TempoI18n && typeof window.TempoI18n.getLanguage === 'function') ? (window.TempoI18n.getLanguage() === 'vi') : false;
            if (sourceContext === 'recovery') scHomeText.textContent = isVi ? (window.t ? window.t('selfCheckWorkspace.returnRecovery', {}, 'Quay lại Dashboard') : 'Quay lại Dashboard') : 'Return to Recovery Mode';
            else if (sourceContext === 'emergency') scHomeText.textContent = isVi ? (window.t ? window.t('selfCheckWorkspace.returnUrgent', {}, 'Quay lại Chế độ khẩn cấp') : 'Quay lại Chế độ khẩn cấp') : 'Return to Urgent Mode';
            else if (sourceContext === 'unclear') scHomeText.textContent = isVi ? (window.t ? window.t('selfCheckWorkspace.returnUnclear', {}, 'Quay lại Chế độ mơ hồ') : 'Quay lại Chế độ mơ hồ') : 'Return to Unclear Mode';
            else scHomeText.textContent = isVi ? (window.t ? window.t('selfCheckWorkspace.returnHome', {}, 'Quay lại trang chủ') : 'Quay lại trang chủ') : 'Return Home';
        }"""

assert target_mode_sc in mode_code, "target_mode_sc not found in mode.js"
mode_code = mode_code.replace(target_mode_sc, refined_mode_sc, 1)

mode_code = mode_code.replace('\r\n', '\n')
assert '\r' not in mode_code, "CRLF found in mode.js"

with open('mode.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(mode_code)
print("mode.js updated successfully")
