import os

# 1. Update i18n.js
with open('i18n.js', 'r', encoding='utf-8') as f:
    i18n_code = f.read()

# Vietnamese keys
vi_target = '                viewMyFullCheck: "Xem full-check",'
vi_replacement = """                viewMyFullCheck: "Xem full-check",
                yourFullCheck: "Full-check",
                monthlyOverview: "Tổng quan tháng",
                backToCalendar: "Quay lại lịch",
                currentMonthPill: "Tháng hiện tại",
                fullCheckMon: "T2",
                fullCheckTue: "T3",
                fullCheckWed: "T4",
                fullCheckThu: "T5",
                fullCheckFri: "T6",
                fullCheckSat: "T7",
                fullCheckSun: "CN","""

assert vi_target in i18n_code, "vi_target not found in i18n.js"
i18n_code = i18n_code.replace(vi_target, vi_replacement, 1)

# English keys
en_target = '                viewMyFullCheck: "View my full check",'
en_replacement = """                viewMyFullCheck: "View my full check",
                yourFullCheck: "Your full check",
                monthlyOverview: "Monthly Overview",
                backToCalendar: "Back to calendar",
                currentMonthPill: "Current month",
                fullCheckMon: "Mon",
                fullCheckTue: "Tue",
                fullCheckWed: "Wed",
                fullCheckThu: "Thurs",
                fullCheckFri: "Fri",
                fullCheckSat: "Sat",
                fullCheckSun: "Sun","""

assert en_target in i18n_code, "en_target not found in i18n.js"
i18n_code = i18n_code.replace(en_target, en_replacement, 1)

i18n_code = i18n_code.replace('\r\n', '\n')
assert '\r' not in i18n_code, "CRLF found in i18n.js"

with open('i18n.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(i18n_code)
print("i18n.js updated successfully")


# 2. Update selfCheckWorkspace.js
with open('selfCheckWorkspace.js', 'r', encoding='utf-8') as f:
    scw_code = f.read()

# Update renderFullCheckModal
old_rfc_months = """        const monthNames = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];
        const monthName = monthNames[month];"""

new_rfc_months = """        const isVi = isViLocale();
        const monthNamesEn = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];
        const monthNamesVi = [
            'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
            'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
        ];
        const monthNames = isVi ? monthNamesVi : monthNamesEn;
        const monthName = monthNames[month];"""

assert old_rfc_months in scw_code, "old_rfc_months not found in selfCheckWorkspace.js"
scw_code = scw_code.replace(old_rfc_months, new_rfc_months, 1)

old_rfc_content = """            <!-- Close Button -->
            <button type="button" 
                    onclick="window.TempoSelfCheckWorkspace.closeFullCheckPlaceholder()" 
                    class="absolute top-4 right-4 text-[#9E9893] hover:text-[#37352F] text-base sm:text-lg transition cursor-pointer p-1 rounded-full hover:bg-stone-200/50" 
                    title="Close">
                ✕
            </button>

            <!-- 1. Small Heading -->
            <span class="text-xs sm:text-sm font-bold text-[#3B5441] tracking-tight block">Your full check</span>

            <!-- 2. Tracking Header: Dot + Name -->
            <div class="flex items-center space-x-2.5 sm:space-x-3 pt-1">
                <span class="w-5 h-5 sm:w-5.5 sm:h-5.5 rounded-full inline-block shrink-0 shadow-2xs" style="background-color: ${dotColor};"></span>
                <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#284132] tracking-tight truncate">${escapeHTML(tracker.name)}</h2>
            </div>

            <!-- 3. Current Month & Year Selector -->
            <div class="flex items-center justify-between pt-1.5 sm:pt-2 flex-wrap gap-2">
                <div class="flex items-center space-x-1.5">
                    <!-- Prev Month Arrow Button -->
                    <button type="button" 
                            id="fullcheck-prev-month-btn"
                            onclick="window.TempoSelfCheckWorkspace.prevMonthFullCheck()"
                            class="w-6 h-6 rounded-lg bg-stone-100 hover:bg-stone-200 text-[#5B5550] flex items-center justify-center transition cursor-pointer text-xs font-bold shadow-2xs" 
                            title="Previous month">
                        ‹
                    </button>

                    <!-- Month and Year Selectors -->
                    <div class="flex items-center space-x-1 bg-stone-50/80 px-2 py-0.5 rounded-lg border border-stone-200/60">
                        <select id="fullcheck-year-select" 
                                onchange="window.TempoSelfCheckWorkspace.onFullCheckYearChange(this.value)"
                                class="bg-transparent font-bold text-xs sm:text-sm text-[#C87D55] cursor-pointer focus:outline-none hover:opacity-80 py-0.5">
                            ${availableYears.map(y => `
                                <option value="${y}" ${y === year ? 'selected' : ''}>${y}</option>
                            `).join('')}
                        </select>
                        <span class="text-xs font-bold text-[#C87D55]">,</span>
                        <select id="fullcheck-month-select" 
                                onchange="window.TempoSelfCheckWorkspace.onFullCheckMonthChange(this.value)"
                                class="bg-transparent font-bold text-xs sm:text-sm text-[#C87D55] cursor-pointer focus:outline-none hover:opacity-80 py-0.5">
                            ${monthNames.map((m, idx) => {
                                const isFuture = (year === now.getFullYear() && idx > now.getMonth());
                                if (isFuture) return '';
                                return `<option value="${idx}" ${idx === month ? 'selected' : ''}>${m}</option>`;
                            }).join('')}
                        </select>
                    </div>

                    <!-- Next Month Arrow Button (Disabled on current month) -->
                    <button type="button" 
                            id="fullcheck-next-month-btn"
                            onclick="window.TempoSelfCheckWorkspace.nextMonthFullCheck()"
                            ${isCurrentMonth ? 'disabled title="Cannot navigate into future months"' : 'title="Next month"'}
                            class="w-6 h-6 rounded-lg flex items-center justify-center transition text-xs font-bold shadow-2xs ${isCurrentMonth ? 'bg-stone-100/50 text-stone-300 cursor-not-allowed' : 'bg-stone-100 hover:bg-stone-200 text-[#5B5550] cursor-pointer'}">
                        ›
                    </button>
                </div>

                <!-- Return to Current Month Pill (Only when not on current month) -->
                ${!isCurrentMonth ? `
                    <button type="button" 
                            id="fullcheck-return-current-btn"
                            onclick="window.TempoSelfCheckWorkspace.jumpToCurrentMonthFullCheck()"
                            class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA] hover:bg-[#DDF0E5] transition cursor-pointer shadow-2xs">
                        Current month
                    </button>
                ` : ''}
            </div>

            <!-- 4. Monthly Calendar with Seven Columns -->
            <div class="pt-2 sm:pt-2.5">
                <!-- Weekday Columns -->
                <div class="grid grid-cols-7 gap-1 text-center pt-2 pb-1.5 w-full">
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">Mon</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">Tue</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">Wed</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">Thus</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">Fri</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">Sat</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">Sun</span>
                </div>

                <!-- Calendar Days Grid -->
                <div class="grid grid-cols-7 gap-x-1 gap-y-1 sm:gap-y-1.5 text-center w-full">
                    ${dayCellsHTML}
                </div>
            </div>

            <!-- 5. Centered Monthly Overview Button -->
            <div class="flex justify-center pt-5 sm:pt-6">
                <button type="button" 
                        onclick="window.TempoSelfCheckWorkspace.onMonthlyOverviewClick('${tracker.id}')"
                        class="px-8 sm:px-10 py-2 sm:py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-[#859B8B] hover:bg-[#748A7A] text-white transition shadow-2xs cursor-pointer tracking-normal">
                    Monthly Overview
                </button>
            </div>"""

new_rfc_content = """            <!-- Close Button -->
            <button type="button" 
                    onclick="window.TempoSelfCheckWorkspace.closeFullCheckPlaceholder()" 
                    class="absolute top-4 right-4 text-[#9E9893] hover:text-[#37352F] text-base sm:text-lg transition cursor-pointer p-1 rounded-full hover:bg-stone-200/50" 
                    title="${window.t ? window.t('common.close', {}, isVi ? 'Đóng' : 'Close') : (isVi ? 'Đóng' : 'Close')}">
                ✕
            </button>

            <!-- 1. Small Heading -->
            <span class="text-xs sm:text-sm font-bold text-[#3B5441] tracking-tight block">${window.t ? window.t('selfCheckWorkspace.yourFullCheck', {}, isVi ? 'Full-check' : 'Your full check') : (isVi ? 'Full-check' : 'Your full check')}</span>

            <!-- 2. Tracking Header: Dot + Name -->
            <div class="flex items-center space-x-2.5 sm:space-x-3 pt-1">
                <span class="w-5 h-5 sm:w-5.5 sm:h-5.5 rounded-full inline-block shrink-0 shadow-2xs" style="background-color: ${dotColor};"></span>
                <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#284132] tracking-tight truncate">${escapeHTML(formatTrackerDisplayName(tracker.name))}</h2>
            </div>

            <!-- 3. Current Month & Year Selector -->
            <div class="flex items-center justify-between pt-1.5 sm:pt-2 flex-wrap gap-2">
                <div class="flex items-center space-x-1.5">
                    <!-- Prev Month Arrow Button -->
                    <button type="button" 
                            id="fullcheck-prev-month-btn"
                            onclick="window.TempoSelfCheckWorkspace.prevMonthFullCheck()"
                            class="w-6 h-6 rounded-lg bg-stone-100 hover:bg-stone-200 text-[#5B5550] flex items-center justify-center transition cursor-pointer text-xs font-bold shadow-2xs" 
                            title="${isVi ? 'Tháng trước' : 'Previous month'}">
                        ‹
                    </button>

                    <!-- Month and Year Selectors -->
                    <div class="flex items-center space-x-1 bg-stone-50/80 px-2 py-0.5 rounded-lg border border-stone-200/60">
                        <select id="fullcheck-year-select" 
                                onchange="window.TempoSelfCheckWorkspace.onFullCheckYearChange(this.value)"
                                class="bg-transparent font-bold text-xs sm:text-sm text-[#C87D55] cursor-pointer focus:outline-none hover:opacity-80 py-0.5">
                            ${availableYears.map(y => `
                                <option value="${y}" ${y === year ? 'selected' : ''}>${y}</option>
                            `).join('')}
                        </select>
                        <span class="text-xs font-bold text-[#C87D55]">,</span>
                        <select id="fullcheck-month-select" 
                                onchange="window.TempoSelfCheckWorkspace.onFullCheckMonthChange(this.value)"
                                class="bg-transparent font-bold text-xs sm:text-sm text-[#C87D55] cursor-pointer focus:outline-none hover:opacity-80 py-0.5">
                            ${monthNames.map((m, idx) => {
                                const isFuture = (year === now.getFullYear() && idx > now.getMonth());
                                if (isFuture) return '';
                                return `<option value="${idx}" ${idx === month ? 'selected' : ''}>${m}</option>`;
                            }).join('')}
                        </select>
                    </div>

                    <!-- Next Month Arrow Button (Disabled on current month) -->
                    <button type="button" 
                            id="fullcheck-next-month-btn"
                            onclick="window.TempoSelfCheckWorkspace.nextMonthFullCheck()"
                            ${isCurrentMonth ? `disabled title="${isVi ? 'Không thể xem các tháng trong tương lai' : 'Cannot navigate into future months'}"` : `title="${isVi ? 'Tháng sau' : 'Next month'}"`}
                            class="w-6 h-6 rounded-lg flex items-center justify-center transition text-xs font-bold shadow-2xs ${isCurrentMonth ? 'bg-stone-100/50 text-stone-300 cursor-not-allowed' : 'bg-stone-100 hover:bg-stone-200 text-[#5B5550] cursor-pointer'}">
                        ›
                    </button>
                </div>

                <!-- Return to Current Month Pill (Only when not on current month) -->
                ${!isCurrentMonth ? `
                    <button type="button" 
                            id="fullcheck-return-current-btn"
                            onclick="window.TempoSelfCheckWorkspace.jumpToCurrentMonthFullCheck()"
                            class="px-2.5 py-1 rounded-full text-[11px] font-bold bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA] hover:bg-[#DDF0E5] transition cursor-pointer shadow-2xs">
                        ${window.t ? window.t('selfCheckWorkspace.currentMonthPill', {}, isVi ? 'Tháng hiện tại' : 'Current month') : (isVi ? 'Tháng hiện tại' : 'Current month')}
                    </button>
                ` : ''}
            </div>

            <!-- 4. Monthly Calendar with Seven Columns -->
            <div class="pt-2 sm:pt-2.5">
                <!-- Weekday Columns -->
                <div class="grid grid-cols-7 gap-1 text-center pt-2 pb-1.5 w-full">
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">${window.t ? window.t('selfCheckWorkspace.fullCheckMon', {}, isVi ? 'T2' : 'Mon') : (isVi ? 'T2' : 'Mon')}</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">${window.t ? window.t('selfCheckWorkspace.fullCheckTue', {}, isVi ? 'T3' : 'Tue') : (isVi ? 'T3' : 'Tue')}</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">${window.t ? window.t('selfCheckWorkspace.fullCheckWed', {}, isVi ? 'T4' : 'Wed') : (isVi ? 'T4' : 'Wed')}</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">${window.t ? window.t('selfCheckWorkspace.fullCheckThu', {}, isVi ? 'T5' : 'Thurs') : (isVi ? 'T5' : 'Thurs')}</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">${window.t ? window.t('selfCheckWorkspace.fullCheckFri', {}, isVi ? 'T6' : 'Fri') : (isVi ? 'T6' : 'Fri')}</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">${window.t ? window.t('selfCheckWorkspace.fullCheckSat', {}, isVi ? 'T7' : 'Sat') : (isVi ? 'T7' : 'Sat')}</span>
                    <span class="text-xs font-bold text-[#6F6B68] select-none text-center">${window.t ? window.t('selfCheckWorkspace.fullCheckSun', {}, isVi ? 'CN' : 'Sun') : (isVi ? 'CN' : 'Sun')}</span>
                </div>

                <!-- Calendar Days Grid -->
                <div class="grid grid-cols-7 gap-x-1 gap-y-1 sm:gap-y-1.5 text-center w-full">
                    ${dayCellsHTML}
                </div>
            </div>

            <!-- 5. Centered Monthly Overview Button -->
            <div class="flex justify-center pt-5 sm:pt-6">
                <button type="button" 
                        onclick="window.TempoSelfCheckWorkspace.onMonthlyOverviewClick('${tracker.id}')"
                        class="px-8 sm:px-10 py-2 sm:py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-[#859B8B] hover:bg-[#748A7A] text-white transition shadow-2xs cursor-pointer tracking-normal">
                    ${window.t ? window.t('selfCheckWorkspace.monthlyOverview', {}, isVi ? 'Tổng quan tháng' : 'Monthly Overview') : (isVi ? 'Tổng quan tháng' : 'Monthly Overview')}
                </button>
            </div>"""

assert old_rfc_content in scw_code, "old_rfc_content not found in selfCheckWorkspace.js"
scw_code = scw_code.replace(old_rfc_content, new_rfc_content, 1)


# Update renderMonthlyOverview
old_rmo_months = """        const monthNames = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];
        const monthName = monthNames[month];"""

new_rmo_months = """        const isVi = isViLocale();
        const monthNamesEn = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];
        const monthNamesVi = [
            'Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5', 'Tháng 6',
            'Tháng 7', 'Tháng 8', 'Tháng 9', 'Tháng 10', 'Tháng 11', 'Tháng 12'
        ];
        const monthNames = isVi ? monthNamesVi : monthNamesEn;
        const monthName = monthNames[month];"""

assert old_rmo_months in scw_code, "old_rmo_months not found in selfCheckWorkspace.js"
scw_code = scw_code.replace(old_rmo_months, new_rmo_months, 1)

old_rmo_top = """            <!-- Top Utility: Back to Calendar & Close -->
            <div class="flex items-center justify-between pb-3 border-b border-stone-200/70">
                <button type="button" 
                        onclick="window.TempoSelfCheckWorkspace.closeMonthlyOverview()" 
                        class="inline-flex items-center space-x-1.5 text-xs sm:text-sm font-bold text-[#4A6B5D] hover:text-[#166545] transition cursor-pointer"
                        title="Back to Calendar">
                    <span class="text-base leading-none">←</span>
                    <span>Back to calendar</span>
                </button>
                <button type="button" 
                        onclick="window.TempoSelfCheckWorkspace.closeMonthlyOverview(true)" 
                        class="text-[#9E9893] hover:text-[#37352F] text-base sm:text-lg transition cursor-pointer p-1 rounded-full hover:bg-stone-200/50" 
                        title="Close">
                    ✕
                </button>
            </div>

            <!-- Tracker Header & Month Navigator -->
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-3">
                <div>
                    <span class="text-xs font-bold text-[#3B5441] tracking-tight block">Monthly Overview</span>
                    <div class="flex items-center space-x-2.5 pt-0.5">
                        <span class="w-3.5 h-3.5 rounded-full inline-block shrink-0 shadow-2xs" style="background-color: ${dotColor};"></span>
                        <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#284132] tracking-tight">${escapeHTML(tracker.name)}</h2>
                        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#E2EAE4] text-[#284132] border border-[#6B8B73]/40">${methodBadge}</span>
                    </div>
                </div>

                <!-- Month Navigation Controls -->
                <div class="flex items-center space-x-1.5 sm:space-x-2">
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.prevMonthOverview()"
                            class="w-8 h-8 rounded-xl bg-white border border-stone-300 hover:bg-stone-50 text-stone-700 font-bold flex items-center justify-center transition cursor-pointer shadow-2xs"
                            title="Previous month">
                        ‹
                    </button>
                    <span class="text-xs sm:text-sm font-extrabold text-[#C87D55] px-2 min-w-[110px] sm:min-w-[130px] text-center select-none">${monthName} ${year}</span>
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.nextMonthOverview()"
                            class="w-8 h-8 rounded-xl bg-white border border-stone-300 hover:bg-stone-50 text-stone-700 font-bold flex items-center justify-center transition cursor-pointer shadow-2xs ${isCurrentMonthAndYear ? 'opacity-35 pointer-events-none' : ''}"
                            title="Next month">
                        ›
                    </button>
                    ${!isCurrentMonthAndYear ? `
                        <button type="button" 
                                onclick="window.TempoSelfCheckWorkspace.jumpToCurrentMonthOverview()"
                                class="px-2.5 py-1 rounded-xl bg-[#859B8B]/15 hover:bg-[#859B8B]/25 text-[#284132] text-[11px] font-bold transition cursor-pointer ml-1">
                            Current
                        </button>
                    ` : ''}
                </div>
            </div>"""

new_rmo_top = """            <!-- Top Utility: Back to Calendar & Close -->
            <div class="flex items-center justify-between pb-3 border-b border-stone-200/70">
                <button type="button" 
                        onclick="window.TempoSelfCheckWorkspace.closeMonthlyOverview()" 
                        class="inline-flex items-center space-x-1.5 text-xs sm:text-sm font-bold text-[#4A6B5D] hover:text-[#166545] transition cursor-pointer"
                        title="${window.t ? window.t('selfCheckWorkspace.backToCalendar', {}, isVi ? 'Quay lại lịch' : 'Back to calendar') : (isVi ? 'Quay lại lịch' : 'Back to calendar')}">
                    <span class="text-base leading-none">←</span>
                    <span>${window.t ? window.t('selfCheckWorkspace.backToCalendar', {}, isVi ? 'Quay lại lịch' : 'Back to calendar') : (isVi ? 'Quay lại lịch' : 'Back to calendar')}</span>
                </button>
                <button type="button" 
                        onclick="window.TempoSelfCheckWorkspace.closeMonthlyOverview(true)" 
                        class="text-[#9E9893] hover:text-[#37352F] text-base sm:text-lg transition cursor-pointer p-1 rounded-full hover:bg-stone-200/50" 
                        title="${window.t ? window.t('common.close', {}, isVi ? 'Đóng' : 'Close') : (isVi ? 'Đóng' : 'Close')}">
                    ✕
                </button>
            </div>

            <!-- Tracker Header & Month Navigator -->
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-3">
                <div>
                    <span class="text-xs font-bold text-[#3B5441] tracking-tight block">${window.t ? window.t('selfCheckWorkspace.monthlyOverview', {}, isVi ? 'Tổng quan tháng' : 'Monthly Overview') : (isVi ? 'Tổng quan tháng' : 'Monthly Overview')}</span>
                    <div class="flex items-center space-x-2.5 pt-0.5">
                        <span class="w-3.5 h-3.5 rounded-full inline-block shrink-0 shadow-2xs" style="background-color: ${dotColor};"></span>
                        <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#284132] tracking-tight">${escapeHTML(formatTrackerDisplayName(tracker.name))}</h2>
                        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#E2EAE4] text-[#284132] border border-[#6B8B73]/40">${methodBadge}</span>
                    </div>
                </div>

                <!-- Month Navigation Controls -->
                <div class="flex items-center space-x-1.5 sm:space-x-2">
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.prevMonthOverview()"
                            class="w-8 h-8 rounded-xl bg-white border border-stone-300 hover:bg-stone-50 text-stone-700 font-bold flex items-center justify-center transition cursor-pointer shadow-2xs"
                            title="${isVi ? 'Tháng trước' : 'Previous month'}">
                        ‹
                    </button>
                    <span class="text-xs sm:text-sm font-extrabold text-[#C87D55] px-2 min-w-[110px] sm:min-w-[130px] text-center select-none">${monthName} ${year}</span>
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.nextMonthOverview()"
                            class="w-8 h-8 rounded-xl bg-white border border-stone-300 hover:bg-stone-50 text-stone-700 font-bold flex items-center justify-center transition cursor-pointer shadow-2xs ${isCurrentMonthAndYear ? 'opacity-35 pointer-events-none' : ''}"
                            title="${isVi ? 'Tháng sau' : 'Next month'}">
                        ›
                    </button>
                    ${!isCurrentMonthAndYear ? `
                        <button type="button" 
                                onclick="window.TempoSelfCheckWorkspace.jumpToCurrentMonthOverview()"
                                class="px-2.5 py-1 rounded-xl bg-[#859B8B]/15 hover:bg-[#859B8B]/25 text-[#284132] text-[11px] font-bold transition cursor-pointer ml-1">
                            ${window.t ? window.t('selfCheckWorkspace.currentMonthPill', {}, isVi ? 'Hiện tại' : 'Current') : (isVi ? 'Hiện tại' : 'Current')}
                        </button>
                    ` : ''}
                </div>
            </div>"""

assert old_rmo_top in scw_code, "old_rmo_top not found in selfCheckWorkspace.js"
scw_code = scw_code.replace(old_rmo_top, new_rmo_top, 1)

# Hook up onLanguageChange for fullcheck & monthly overview modals
old_on_lang = """            const modal = document.getElementById('modal-selfcheck-adjust');
            if (modal && !modal.classList.contains('hidden') && adjustDraftState) {"""

new_on_lang = """            const fullCheckModal = document.getElementById('modal-selfcheck-fullcheck');
            if (fullCheckModal && !fullCheckModal.classList.contains('hidden') && fullCheckTrackerId) {
                renderFullCheckModal(fullCheckTrackerId, fullCheckYear, fullCheckMonth);
            }
            const overviewModal = document.getElementById('modal-selfcheck-monthly-overview');
            if (overviewModal && !overviewModal.classList.contains('hidden') && monthlyOverviewTrackerId) {
                renderMonthlyOverview(monthlyOverviewTrackerId);
            }
            const modal = document.getElementById('modal-selfcheck-adjust');
            if (modal && !modal.classList.contains('hidden') && adjustDraftState) {"""

assert old_on_lang in scw_code, "old_on_lang not found in selfCheckWorkspace.js"
scw_code = scw_code.replace(old_on_lang, new_on_lang, 1)

scw_code = scw_code.replace('\r\n', '\n')
assert '\r' not in scw_code, "CRLF found in selfCheckWorkspace.js"

with open('selfCheckWorkspace.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(scw_code)
print("selfCheckWorkspace.js updated successfully")
