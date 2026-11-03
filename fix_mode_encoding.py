import sys

with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Verify LF
assert '\r' not in text, "mode.js must have 0 CRLF before edit!"

old_block_1 = """        const isVi = typeof isViLocale === 'function' ? isViLocale() : false;
        const todaysWorkDoneText = (window.t ? window.t('modes.urgent.todaysWorkDone') : null) || (isVi ? '\\xc4\\x90\\xc3\\x83 HO\\xc3\\x80N TH\\xc3\\x80NH C\\xc3\\x94NG VI\\xe1\\xbb\\x86C H\\xc3\\x94M NAY' : "TODAY'S WORK DONE");
        const allDoneTodayHeading = (window.t ? window.t('modes.urgent.allDoneTodayHeading') : null) || (isVi ? 'V\\xe1\\xba\\xady l\\xc3\\xa0 h\\xc3\\xb4m nay b\\xe1\\xba\\xa1n \\xc4\\x91\\xc3\\xa3 ho\\xc3\\xa0n th\\xc3\\xa0nh m\\xe1\\xbb\\x8di vi\\xe1\\xbb\\x87c! \\xf0\\x9f\\x8e\\x89' : "You're all done for today! \\xf0\\x9f\\x8e\\x89");
        const allDoneTodayDesc = (window.t ? window.t('modes.urgent.allDoneTodayDesc') : null) || (isVi ? 'B\\xe1\\xba\\xa1n \\xc4\\x91\\xc3\\xa3 ho\\xc3\\xa0n th\\xc3\\xa0nh c\\xc3\\xa1c c\\xc3\\xb4ng vi\\xe1\\xbb\\x87c h\\xc3\\xb4m nay. B\\xe1\\xba\\xa1n c\\xc3\\xb3 mu\\xe1\\xbb\\x91n b\\xe1\\xba\\xaft \\xc4\\x91\\xe1\\xba\\xa7u tr\\xc6\\xb0\\xe1\\xbb\\x9bc m\\xe1\\xbb\\x99t ch\\xc3\\xbat cho ng\\xc3\\xa0y mai hay ngh\\xe1\\xbb\\x89 ng\\xc6\\xa1i t\\xe1\\xba\\xa1i \\xc4\\x91\\xc3\\xa2y?' : "You've made it through today's tasks. Want to get a head start on tomorrow, or call it a day?");
        const nextPlannedWorkLabel = (window.t ? window.t('modes.urgent.nextPlannedWorkLabel') : null) || (isVi ? 'C\\xc3\\x94NG VI\\xe1\\xbb\\x86C TI\\xe1\\xba\\xbeP THEO:' : 'NEXT PLANNED WORK:');
        const tomorrowLabel = (window.t ? window.t('modes.urgent.tomorrow') : null) || (isVi ? 'Ng\\xc3\\xa0y mai' : 'Tomorrow');
        const previewTomorrowText = (window.t ? window.t('modes.urgent.previewTomorrow') : null) || (isVi ? 'Xem tr\\xc6\\xb0\\xe1\\xbb\\x9bc k\\xe1\\xba\\xbf ho\\xe1\\xba\\xa1ch ng\\xc3\\xa0y mai \\xe2\\x86\\x92' : 'Preview tomorrow \\xe2\\x86\\x92');
        const doTomorrowTaskText = (window.t ? window.t('modes.urgent.doTomorrowTask') : null) || (isVi ? 'B\\xe1\\xba\\xaft \\xc4\\x91\\xe1\\xba\\xa7u c\\xc3\\xb4ng vi\\xe1\\xbb\\x87c ng\\xc3\\xa0y mai \\xe2\\x86\\x92' : "Let's do tomorrow's task \\xe2\\x86\\x92");
        const restForNowText = (window.t ? window.t('modes.urgent.restForNow') : null) || (isVi ? 'T\\xc3\\xb4i s\\xe1\\xba\\xbd ngh\\xe1\\xbb\\x89 ng\\xc6\\xa1i l\\xc3\\xbac n\\xc3\\xa0y' : "I'll rest for now");
        const restingDesc = (window.t ? window.t('modes.urgent.restingDesc') : null) || (isVi ? '\\xc4\\x90\\xc3\\xa3 xong m\\xe1\\xbb\\x8di vi\\xe1\\xbb\\x87c. B\\xe1\\xba\\xa1n x\\xe1\\xbb\\xa9ng \\xc4\\x91\\xc3\\xa1ng \\xc4\\x91\\xc6\\xb0\\xe1\\xbb\\xa3c ngh\\xe1\\xbb\\x89 ng\\xc6\\xa1i. C\\xe1\\xbb\\xa9 th\\xc6\\xb0 gi\\xc3\\xa3n nh\\xc3\\xa9!' : "All done. You've earned some rest. Take it easy!");
        const backToOverviewText = (window.t ? window.t('modes.urgent.backToOverview') : null) || (isVi ? 'Quay l\\xe1\\xba\\xa1i t\\xe1\\xbb\\x95ng quan' : 'Back to overview');"""

new_block_1 = """        const isVi = typeof isViLocale === 'function' ? isViLocale() : false;
        const todaysWorkDoneText = (window.t ? window.t('modes.urgent.todaysWorkDone') : null) || (isVi ? 'ĐÃ HOÀN THÀNH CÔNG VIỆC HÔM NAY' : "TODAY'S WORK DONE");
        const allDoneTodayHeading = (window.t ? window.t('modes.urgent.allDoneTodayHeading') : null) || (isVi ? 'Vậy là hôm nay bạn đã hoàn thành mọi việc! 🎉' : "You're all done for today! 🎉");
        const allDoneTodayDesc = (window.t ? window.t('modes.urgent.allDoneTodayDesc') : null) || (isVi ? 'Bạn đã hoàn thành các công việc hôm nay. Bạn có muốn bắt đầu trước một chút cho ngày mai hay nghỉ ngơi tại đây?' : "You've made it through today's tasks. Want to get a head start on tomorrow, or call it a day?");
        const nextPlannedWorkLabel = (window.t ? window.t('modes.urgent.nextPlannedWorkLabel') : null) || (isVi ? 'CÔNG VIỆC TIẾP THEO:' : 'NEXT PLANNED WORK:');
        const tomorrowLabel = (window.t ? window.t('modes.urgent.tomorrow') : null) || (isVi ? 'Ngày mai' : 'Tomorrow');
        const previewTomorrowText = (window.t ? window.t('modes.urgent.previewTomorrow') : null) || (isVi ? 'Xem trước kế hoạch ngày mai →' : 'Preview tomorrow →');
        const doTomorrowTaskText = (window.t ? window.t('modes.urgent.doTomorrowTask') : null) || (isVi ? 'Bắt đầu công việc ngày mai →' : "Let's do tomorrow's task →");
        const restForNowText = (window.t ? window.t('modes.urgent.restForNow') : null) || (isVi ? 'Tôi sẽ nghỉ ngơi lúc này' : "I'll rest for now");
        const restingDesc = (window.t ? window.t('modes.urgent.restingDesc') : null) || (isVi ? 'Đã xong mọi việc. Bạn xứng đáng được nghỉ ngơi. Cứ thư giãn nhé!' : "All done. You've earned some rest. Take it easy!");
        const backToOverviewText = (window.t ? window.t('modes.urgent.backToOverview') : null) || (isVi ? 'Quay lại tổng quan' : 'Back to overview');"""

assert old_block_1 in text, "old_block_1 not found!"
text = text.replace(old_block_1, new_block_1, 1)

old_block_2 = """        let nextScheduleText = tomorrowLabel;
        if (nextItem) {
            const isTomorrow = (nextItem.dayDate === tomorrowStr) ||
                               (typeof nextItem.dayLabel === 'string' && (nextItem.dayLabel.trim().toLowerCase() === 'tomorrow' || nextItem.dayLabel.trim().toLowerCase() === 'ng\\xc3\\xa0y mai'));
            if (isTomorrow) {
                nextScheduleText = tomorrowLabel;
            } else if (nextItem.dayDate) {
                nextScheduleText = (window.TempoI18n && typeof window.TempoI18n.formatScheduledDateLabel === 'function')
                    ? window.TempoI18n.formatScheduledDateLabel(nextItem.dayDate, isVi ? 'vi' : 'en')
                    : (nextItem.dayLabel || nextItem.dayDate);
            } else {
                nextScheduleText = nextItem.dayLabel || tomorrowLabel;
            }
            if (nextItem.startTime) {
                nextScheduleText += ` \\xc2\\xb7 ${nextItem.startTime}`;
            }
        }"""

new_block_2 = """        let nextScheduleText = tomorrowLabel;
        if (nextItem) {
            const isTomorrow = (nextItem.dayDate === tomorrowStr) ||
                               (typeof nextItem.dayLabel === 'string' && (nextItem.dayLabel.trim().toLowerCase() === 'tomorrow' || nextItem.dayLabel.trim().toLowerCase() === 'ngày mai'));
            if (isTomorrow) {
                nextScheduleText = tomorrowLabel;
            } else if (nextItem.dayDate) {
                nextScheduleText = (window.TempoI18n && typeof window.TempoI18n.formatScheduledDateLabel === 'function')
                    ? window.TempoI18n.formatScheduledDateLabel(nextItem.dayDate, isVi ? 'vi' : 'en')
                    : (nextItem.dayLabel || nextItem.dayDate);
            } else {
                nextScheduleText = nextItem.dayLabel || tomorrowLabel;
            }
            if (nextItem.startTime) {
                nextScheduleText += ` · ${nextItem.startTime}`;
            }
        }"""

assert old_block_2 in text, "old_block_2 not found!"
text = text.replace(old_block_2, new_block_2, 1)

# Ensure strictly LF
text = text.replace('\r\n', '\n').replace('\r', '\n')
raw_out = text.encode('utf-8')

with open('mode.js', 'wb') as f:
    f.write(raw_out)

crlf_after = raw_out.count(b'\r\n')
lf_after = raw_out.count(b'\n') - crlf_after
print(f"mode.js updated! CRLF={crlf_after}, lone LF={lf_after}")
assert crlf_after == 0, "mode.js must have 0 CRLF!"
