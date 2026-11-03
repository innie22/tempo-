import sys

def main():
    with open('i18n.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add skip to vi.common
    target_common_vi = """                save: "Lưu",
                cancel: "Hủy","""
    repl_common_vi = """                save: "Lưu",
                skip: "Bỏ qua",
                cancel: "Hủy","""

    # 2. Add skip to en.common
    target_common_en = """                save: "Save",
                cancel: "Cancel","""
    repl_common_en = """                save: "Save",
                skip: "Skip",
                cancel: "Cancel","""

    # 3. Add streak keys to vi.modes.urgent
    target_urg_vi = """                    transitionQuestion: "Mọi thứ đã đỡ gấp gáp hơn?",
                    changeMyMode: "Chuyển chế độ","""
    repl_urg_vi = """                    transitionQuestion: "Mọi thứ đã đỡ gấp gáp hơn?",
                    changeMyMode: "Chuyển chế độ",
                    streakHeading: "Chuỗi Self-check 🔥",
                    skip: "Bỏ qua",
                    save: "Lưu",
                    checkinSummary: "Bạn đã check {completed}/{total} mục hôm nay.",
                    viewTodayCheckin: "Xem check-in hôm nay",
                    editTrackingSystem: "Sửa tracking",
                    fromCommunity: "Cộng đồng Tempo","""

    # 4. Add streak keys to en.modes.urgent
    target_urg_en = """                    transitionQuestion: "Are things feeling less urgent now?",
                    changeMyMode: "Change my mode","""
    repl_urg_en = """                    transitionQuestion: "Are things feeling less urgent now?",
                    changeMyMode: "Change my mode",
                    streakHeading: "Your Self-check Streak 🔥",
                    skip: "Skip",
                    save: "Save",
                    checkinSummary: "You checked in on {completed} of {total} things.",
                    viewTodayCheckin: "View today's checkin",
                    editTrackingSystem: "Edit tracking system",
                    fromCommunity: "From the Tempo Community","""

    # 5. Add streak keys to vi.modes.recovery
    target_rec_vi = """                    transitionQuestion: "Bạn đang cảm thấy quá tải hơn?",
                    changeMyMode: "Chuyển chế độ\""""
    repl_rec_vi = """                    transitionQuestion: "Bạn đang cảm thấy quá tải hơn?",
                    changeMyMode: "Chuyển chế độ",
                    streakHeading: "Chuỗi Self-check 🔥",
                    skip: "Bỏ qua",
                    save: "Lưu",
                    checkinSummary: "Bạn đã check {completed}/{total} mục hôm nay.",
                    viewTodayCheckin: "Xem check-in hôm nay",
                    editTrackingSystem: "Sửa tracking",
                    fromCommunity: "Cộng đồng Tempo\""""

    # 6. Add streak keys to en.modes.recovery
    target_rec_en = """                    transitionQuestion: "Are things feeling more overwhelming now?",
                    changeMyMode: "Change my mode\""""
    repl_rec_en = """                    transitionQuestion: "Are things feeling more overwhelming now?",
                    changeMyMode: "Change my mode",
                    streakHeading: "Your Self-check Streak 🔥",
                    skip: "Skip",
                    save: "Save",
                    checkinSummary: "You checked in on {completed} of {total} things.",
                    viewTodayCheckin: "View today's checkin",
                    editTrackingSystem: "Edit tracking system",
                    fromCommunity: "From the Tempo Community\""""

    # 7. Add formatTimeAgo function implementation before updateNavbarSwitcher
    target_fn = """    // -------------------------------------------------------------------------
    // NAVBAR SWITCHER & STATIC HTML UPDATER
    // -------------------------------------------------------------------------"""
    repl_fn = """    function formatTimeAgo(timeInput, lang) {
        const targetLang = (lang && SUPPORTED_LANGS.includes(lang)) ? lang : currentLang;
        const isVi = targetLang === 'vi';

        if (!timeInput) return isVi ? 'Gần đây' : 'Recent';

        if (typeof timeInput === 'string') {
            const str = timeInput.trim();
            if (/^(just now|vừa xong)$/i.test(str)) {
                return isVi ? 'Vừa xong' : 'Just now';
            }
            if (/^(recent|gần đây)$/i.test(str)) {
                return isVi ? 'Gần đây' : 'Recent';
            }

            const match = str.match(/^(\\d+)\\s*(hour|hr|minute|min|day|month|year|giờ|phút|ngày|tháng|năm)s?\\s*(ago|trước)?$/i);
            if (match) {
                const count = parseInt(match[1], 10);
                const unit = match[2].toLowerCase();

                if (unit.startsWith('h') || unit.startsWith('giờ')) {
                    const s = count === 1 ? '' : 's';
                    return isVi ? `${count} giờ trước` : `${count} hour${s} ago`;
                }
                if (unit.startsWith('m') || unit.startsWith('phút')) {
                    const s = count === 1 ? '' : 's';
                    return isVi ? `${count} phút trước` : `${count} minute${s} ago`;
                }
                if (unit.startsWith('d') || unit.startsWith('ngày')) {
                    const s = count === 1 ? '' : 's';
                    return isVi ? `${count} ngày trước` : `${count} day${s} ago`;
                }
                if (unit.startsWith('tháng') || unit.startsWith('month')) {
                    const s = count === 1 ? '' : 's';
                    return isVi ? `${count} tháng trước` : `${count} month${s} ago`;
                }
                if (unit.startsWith('y') || unit.startsWith('năm')) {
                    const s = count === 1 ? '' : 's';
                    return isVi ? `${count} năm trước` : `${count} year${s} ago`;
                }
            }
        }

        let dateObj = null;
        if (timeInput instanceof Date) {
            dateObj = timeInput;
        } else if (typeof timeInput === 'number' && !isNaN(timeInput)) {
            dateObj = new Date(timeInput);
        } else if (typeof timeInput === 'string' && /^\\d{4}-\\d{2}-\\d{2}/.test(timeInput)) {
            const parsed = new Date(timeInput);
            if (!isNaN(parsed.getTime())) {
                dateObj = parsed;
            }
        }

        if (dateObj && !isNaN(dateObj.getTime())) {
            const diffSeconds = Math.max(0, Math.floor((Date.now() - dateObj.getTime()) / 1000));
            if (diffSeconds < 60) {
                return isVi ? 'Vừa xong' : 'Just now';
            }
            const diffMinutes = Math.floor(diffSeconds / 60);
            if (diffMinutes < 60) {
                const s = diffMinutes === 1 ? '' : 's';
                return isVi ? `${diffMinutes} phút trước` : `${diffMinutes} minute${s} ago`;
            }
            const diffHours = Math.floor(diffMinutes / 60);
            if (diffHours < 24) {
                const s = diffHours === 1 ? '' : 's';
                return isVi ? `${diffHours} giờ trước` : `${diffHours} hour${s} ago`;
            }
            const diffDays = Math.floor(diffHours / 24);
            if (diffDays < 30) {
                const s = diffDays === 1 ? '' : 's';
                return isVi ? `${diffDays} ngày trước` : `${diffDays} day${s} ago`;
            }
            const diffMonths = Math.floor(diffDays / 30);
            if (diffMonths < 12) {
                const s = diffMonths === 1 ? '' : 's';
                return isVi ? `${diffMonths} tháng trước` : `${diffMonths} month${s} ago`;
            }
            const diffYears = Math.floor(diffDays / 365);
            const s = diffYears === 1 ? '' : 's';
            return isVi ? `${diffYears} năm trước` : `${diffYears} year${s} ago`;
        }

        return String(timeInput);
    }

    // -------------------------------------------------------------------------
    // NAVBAR SWITCHER & STATIC HTML UPDATER
    // -------------------------------------------------------------------------"""

    # 8. Add formatTimeAgo to exports
    target_exp = """        formatDeadline,
        toggleNavbarDropdown,"""
    repl_exp = """        formatDeadline,
        formatTimeAgo,
        toggleNavbarDropdown,"""

    c_lf = content.replace('\r\n', '\n')
    assert target_common_vi in c_lf, 'target_common_vi not found'
    assert target_common_en in c_lf, 'target_common_en not found'
    assert target_urg_vi in c_lf, 'target_urg_vi not found'
    assert target_urg_en in c_lf, 'target_urg_en not found'
    assert target_rec_vi in c_lf, 'target_rec_vi not found'
    assert target_rec_en in c_lf, 'target_rec_en not found'
    assert target_fn in c_lf, 'target_fn not found'
    assert target_exp in c_lf, 'target_exp not found'

    c_lf = c_lf.replace(target_common_vi, repl_common_vi, 1)
    c_lf = c_lf.replace(target_common_en, repl_common_en, 1)
    c_lf = c_lf.replace(target_urg_vi, repl_urg_vi, 1)
    c_lf = c_lf.replace(target_urg_en, repl_urg_en, 1)
    c_lf = c_lf.replace(target_rec_vi, repl_rec_vi, 1)
    c_lf = c_lf.replace(target_rec_en, repl_rec_en, 1)
    c_lf = c_lf.replace(target_fn, repl_fn, 1)
    c_lf = c_lf.replace(target_exp, repl_exp, 1)

    final_content = c_lf.replace('\n', '\r\n')
    with open('i18n.js', 'wb') as f:
        f.write(final_content.encode('utf-8'))
    print('Successfully updated i18n.js with CRLF!')

if __name__ == '__main__':
    main()
