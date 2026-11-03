import os

# 1. Update recoverySetup.js
with open('recoverySetup.js', 'r', encoding='utf-8') as f:
    setup_code = f.read()

# Replace continueLabel in Step 1
setup_code = setup_code.replace(
    "const continueLabel = t('modes.recovery.onboarding.adjustContinueBtn', {}, isVi ? 'Tiếp tục đến Lời nhắn phục hồi →' : 'Continue to Recovery Note →');",
    "const continueLabel = t('modes.recovery.onboarding.adjustContinueBtn', {}, isVi ? 'Tiếp tục đến Lời nhắn phục hồi →' : 'Continue to Recovery Notice →');"
)

# Replace Option B text
setup_code = setup_code.replace(
    "and review your Recovery Note. All past records remain completely safe.",
    "and review your Recovery Notice. All past records remain completely safe."
)

# Replace Step 2 labels in renderStageAdjustNote
setup_code = setup_code.replace(
    "const stepBadge = isVi ? 'BƯỚC 2/3 · LỜI NHẮN PHỤC HỒI' : 'STEP 2 OF 3 · RECOVERY NOTE';",
    "const stepBadge = isVi ? 'BƯỚC 2/3 · LỜI NHẮN PHỤC HỒI' : 'STEP 2 OF 3 · RECOVERY NOTICE';"
)
setup_code = setup_code.replace(
    "const tagLabel = isVi ? 'Xem lại Lời nhắn phục hồi' : 'Review Recovery Note';",
    "const tagLabel = isVi ? 'Xem lại Lời nhắn phục hồi' : 'Review Recovery Notice';"
)
setup_code = setup_code.replace(
    "const title = isVi ? 'Xem lại Lời nhắn phục hồi' : 'Review your Recovery Note';",
    "const title = isVi ? 'Xem lại Lời nhắn phục hồi' : 'Review your Recovery Notice';"
)

# Replace Stage 4 onboarding badge & title
setup_code = setup_code.replace(
    "STEP 3 OF 5 · RECOVERY NOTE (OPTIONAL)",
    "STEP 3 OF 5 · RECOVERY NOTICE (OPTIONAL)"
)
setup_code = setup_code.replace(
    "<h3 class=\"font-heading text-xl sm:text-2xl font-extrabold text-[#202124]\">Create your Recovery Note</h3>",
    "<h3 class=\"font-heading text-xl sm:text-2xl font-extrabold text-[#202124]\">Create your Recovery Notice</h3>"
)

# Replace renderStageAdjustReview
target_review = """    function renderStageAdjustReview(container) {
        const keptTrackers = adjustmentDraft.trackers.filter(t => t.isKept !== false);
        const stoppedTrackers = adjustmentDraft.trackers.filter(t => t.isKept === false);
        const newTrackers = adjustmentDraft.newTrackers;

        container.innerHTML = `
            <div class="space-y-5">
                <div class="flex items-center justify-between text-xs text-[#6F6B68]">
                    <span class="font-bold uppercase tracking-wider text-[#166545]">STEP 3 OF 3 · FINAL CONFIRMATION</span>
                    <span>Review & Confirm</span>
                </div>

                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                        Review proposed setup changes
                    </h3>
                    <p class="text-xs text-[#6F6B68]">
                        Please confirm your updates. Changes will be saved only after explicit confirmation.
                    </p>
                </div>

                <div class="space-y-4 max-h-[46vh] overflow-y-auto pr-1 text-xs">
                    <!-- Kept Trackers -->
                    <div class="p-3.5 rounded-2xl bg-white border border-[#CDE9DA] space-y-2">
                        <span class="font-extrabold uppercase tracking-wider text-[#166545] text-[11px] block">
                            Active Tracking Items (${keptTrackers.length + newTrackers.length})
                        </span>
                        <div class="space-y-1.5">
                            ${keptTrackers.map(t => {
                                const methodChanged = t.wasEdited && t.check_method !== t.originalMethod;
                                return `
                                    <div class="flex items-center justify-between p-2 rounded-xl bg-[#F7FCF9] border border-[#CDE9DA]/60">
                                        <div class="flex items-center space-x-2">
                                            <span class="font-bold text-[#202124]">${escapeHTML(t.name)}</span>
                                            <span class="text-stone-500">(${escapeHTML(t.check_method)})</span>
                                        </div>
                                        ${methodChanged ? `
                                            <span class="text-[10px] font-bold text-[#B83D08] bg-[#FFE9DC] px-2 py-0.5 rounded-full border border-[#FFD2BA]">
                                                Method: ${escapeHTML(t.originalMethod)} → ${escapeHTML(t.check_method)} (effective today)
                                            </span>
                                        ` : '<span class="text-[10px] font-bold text-[#166545]">Active</span>'}
                                    </div>
                                `;
                            }).join('')}
                            ${newTrackers.map(t => `
                                <div class="flex items-center justify-between p-2 rounded-xl bg-[#F4F9F6] border border-dashed border-[#166545]/40">
                                    <span class="font-bold text-[#166545]">${escapeHTML(t.name)} (${escapeHTML(t.check_method)})</span>
                                    <span class="text-[10px] font-bold text-[#166545] bg-[#EDF7F1] px-2 py-0.5 rounded-full">New item</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Stopped Trackers -->
                    ${stoppedTrackers.length > 0 ? `
                        <div class="p-3.5 rounded-2xl bg-stone-50 border border-stone-200 space-y-2">
                            <span class="font-extrabold uppercase tracking-wider text-[#B83D08] text-[11px] block">
                                Items to Stop Tracking (${stoppedTrackers.length})
                            </span>
                            <div class="space-y-1.5">
                                ${stoppedTrackers.map(t => `
                                    <div class="p-2 rounded-xl bg-white border border-stone-200 flex items-center justify-between">
                                        <span class="font-medium text-[#202124]">${escapeHTML(t.name)}</span>
                                        <span class="text-[11px] text-stone-500">✓ Past check-in records safely preserved</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- Recovery Note summary -->
                    <div class="p-3.5 rounded-2xl bg-[#FEFAF4] border border-[#F0EBE6] space-y-1">
                        <span class="font-extrabold uppercase tracking-wider text-[#484541] text-[11px] block">
                            Recovery Note
                        </span>
                        <p class="text-stone-600">
                            ${adjustmentDraft.noteItems.length} personal reflection items saved.
                        </p>
                    </div>
                </div>

                <!-- Footer Nav with Explicit Save Confirmation -->
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage('adjust_trackers')"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ← Back to Edit
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.executeAdjustSetupConfirm()"
                            class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer bg-[#166545] hover:bg-[#0E4A32] text-white">
                        <span>Confirm & Save Setup</span>
                        <span>✓</span>
                    </button>
                </div>
            </div>
        `;
    }"""

refined_review = """    function renderStageAdjustReview(container) {
        const isVi = isViLocale();
        updateRecoveryCardTheme(true);

        const keptTrackers = adjustmentDraft.trackers.filter(t => t.isKept !== false);
        const stoppedTrackers = adjustmentDraft.trackers.filter(t => t.isKept === false);
        const newTrackers = adjustmentDraft.newTrackers;
        const noteItemsCount = adjustmentDraft.noteItems.length;

        const stepBadge = isVi ? 'BƯỚC 3/3 · XÁC NHẬN CUỐI CÙNG' : 'STEP 3 OF 3 · FINAL CONFIRMATION';
        const tagLabel = isVi ? 'Xem lại & xác nhận' : 'Review & Confirm';
        const title = isVi ? 'Xem lại các thay đổi thiết lập' : 'Review proposed setup changes';
        const desc = isVi
            ? 'Vui lòng kiểm tra và xác nhận các thay đổi. Thiết lập chỉ được lưu sau khi bạn xác nhận.'
            : 'Please confirm your updates. Changes will be saved only after explicit confirmation.';

        const activeTrackersHeader = isVi
            ? `CÁC MỤC TRACKING ĐANG HOẠT ĐỘNG (${keptTrackers.length + newTrackers.length})`
            : `ACTIVE TRACKING ITEMS (${keptTrackers.length + newTrackers.length})`;

        const activeLabel = isVi ? 'Đang tracking' : 'Active';
        const newLabel = isVi ? 'Mục mới' : 'New item';
        const stoppedTrackersHeader = isVi
            ? `CÁC MỤC NGỪNG TRACKING (${stoppedTrackers.length})`
            : `ITEMS TO STOP TRACKING (${stoppedTrackers.length})`;
        const stoppedPreservedNote = isVi
            ? '✓ Dữ liệu tracking trước đó vẫn được giữ nguyên an toàn'
            : '✓ Past check-in records safely preserved';

        const recoveryNoticeHeader = isVi ? 'LỜI NHẮN PHỤC HỒI' : 'RECOVERY NOTICE';
        const recoveryNoticeText = noteItemsCount === 0
            ? (isVi ? 'Chưa có nội dung chia sẻ cá nhân nào được lưu.' : '0 personal reflection items saved.')
            : (isVi ? `${noteItemsCount} nội dung chia sẻ cá nhân đã lưu.` : `${noteItemsCount} personal reflection ${noteItemsCount === 1 ? 'item' : 'items'} saved.`);

        const backBtnLabel = isVi ? 'Quay lại chỉnh sửa' : 'Back to Edit';
        const confirmBtnLabel = isVi ? 'Xác nhận & lưu thiết lập ✓' : 'Confirm & Save Setup ✓';

        function getMethodDesc(method, t) {
            if (method === 'percentage') return isVi ? 'Phần trăm (%)' : 'Percentage (%)';
            if (method === 'scale') return isVi ? `Thang đo 1–${t.scale_max || 5}` : `Scale 1–${t.scale_max || 5}`;
            if (method === 'quantity') {
                const unit = t.quantity_unit || (isVi ? 'phút' : 'minutes');
                return isVi ? `Số lượng (${unit})` : `Quantity (${unit})`;
            }
            if (method === 'options' || method === 'yes_no') return isVi ? 'Lựa chọn' : 'Options';
            return method;
        }

        container.innerHTML = `
            <div class="space-y-5" data-tempo-ui="adjust-review-confirm">
                <div class="flex items-center justify-between text-xs">
                    <span class="font-extrabold uppercase tracking-wider text-[#4F6851] text-[11px]">${escapeHTML(stepBadge)}</span>
                    <span class="text-[#6F6B68] font-medium">${escapeHTML(tagLabel)}</span>
                </div>

                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                        ${escapeHTML(title)}
                    </h3>
                    <p class="text-xs text-[#6F6B68]">
                        ${escapeHTML(desc)}
                    </p>
                </div>

                <div class="space-y-4 max-h-[46vh] overflow-y-auto pr-1.5 recovery-note-scroll text-xs">
                    <!-- Kept Trackers -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#ECC9BA]/80 space-y-3 shadow-2xs transition">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#8EA28F] shrink-0"></span>
                            <span class="font-extrabold uppercase tracking-wider text-[#202124] text-[11px] block">
                                ${escapeHTML(activeTrackersHeader)}
                            </span>
                        </div>
                        <div class="space-y-1.5">
                            ${keptTrackers.map(t => {
                                const methodChanged = t.wasEdited && t.check_method !== t.originalMethod;
                                const curMethodLabel = getMethodDesc(t.check_method, t);
                                return `
                                    <div class="flex items-center justify-between p-2.5 rounded-xl bg-white border border-[#EAE4DF] text-xs shadow-2xs">
                                        <div class="flex items-center space-x-2">
                                            <span class="font-bold text-[#202124]">${escapeHTML(t.name)}</span>
                                            <span class="text-[#6F6B68]">(${escapeHTML(curMethodLabel)})</span>
                                        </div>
                                        ${methodChanged ? `
                                            <span class="text-[10px] font-bold text-[#8EA28F] bg-[#8EA28F]/10 px-2.5 py-0.5 rounded-full border border-[#8EA28F]/30">
                                                ${isVi
                                                    ? `Hình thức: ${escapeHTML(getMethodDesc(t.originalMethod, t))} → ${escapeHTML(curMethodLabel)} (áp dụng từ hôm nay)`
                                                    : `Method: ${escapeHTML(t.originalMethod)} → ${escapeHTML(t.check_method)} (effective today)`}
                                            </span>
                                        ` : `<span class="text-[10px] font-bold text-[#25422D] bg-[#8EA28F]/15 border border-[#8EA28F]/40 px-2 py-0.5 rounded-full">${escapeHTML(activeLabel)}</span>`}
                                    </div>
                                `;
                            }).join('')}
                            ${newTrackers.map(t => `
                                <div class="flex items-center justify-between p-2.5 rounded-xl bg-[#FFF9F4] border border-dashed border-[#8EA28F]/60 text-xs shadow-2xs">
                                    <span class="font-bold text-[#4F6851]">${escapeHTML(t.name)} (${escapeHTML(getMethodDesc(t.check_method, t))})</span>
                                    <span class="text-[10px] font-bold text-[#25422D] bg-[#8EA28F]/15 border border-[#8EA28F]/40 px-2 py-0.5 rounded-full">${escapeHTML(newLabel)}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Stopped Trackers -->
                    ${stoppedTrackers.length > 0 ? `
                        <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#ECC9BA]/60 space-y-3 shadow-2xs transition">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#ECC9BA] shrink-0"></span>
                                <span class="font-extrabold uppercase tracking-wider text-[#6F6B68] text-[11px] block">
                                    ${escapeHTML(stoppedTrackersHeader)}
                                </span>
                            </div>
                            <div class="space-y-1.5">
                                ${stoppedTrackers.map(t => `
                                    <div class="p-2.5 rounded-xl bg-white/80 border border-[#EAE4DF] flex items-center justify-between text-xs shadow-2xs">
                                        <span class="font-medium text-[#202124]">${escapeHTML(t.name)}</span>
                                        <span class="text-[11px] text-[#6F6B68]">${escapeHTML(stoppedPreservedNote)}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- Recovery Notice summary -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#ECC9BA]/80 space-y-1.5 shadow-2xs transition">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#93AFBC] shrink-0"></span>
                            <span class="font-extrabold uppercase tracking-wider text-[#202124] text-[11px] block">
                                ${escapeHTML(recoveryNoticeHeader)}
                            </span>
                        </div>
                        <p class="text-xs text-[#6F6B68] pl-4.5">
                            ${escapeHTML(recoveryNoticeText)}
                        </p>
                    </div>
                </div>

                <!-- Footer Nav with Explicit Save Confirmation -->
                <div class="pt-4 border-t border-[#ECC9BA]/60 flex items-center justify-between">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage('adjust_trackers')"
                            class="px-4 py-2.5 rounded-xl text-xs font-bold text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/20 transition cursor-pointer flex items-center space-x-1.5">
                        <span>←</span>
                        <span>${escapeHTML(backBtnLabel)}</span>
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.executeAdjustSetupConfirm()"
                            class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer bg-[#8EA28F] hover:bg-[#7D937E] text-white">
                        <span>${escapeHTML(confirmBtnLabel)}</span>
                    </button>
                </div>
            </div>
        `;
    }"""

assert target_review in setup_code, "target_review not found in recoverySetup.js"
setup_code = setup_code.replace(target_review, refined_review, 1)

# Enforce strict lone-LF
setup_code = setup_code.replace('\r\n', '\n')
assert '\r' not in setup_code, "Carriage returns found in recoverySetup.js"

with open('recoverySetup.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(setup_code)
print("recoverySetup.js updated successfully")

# 2. Update i18n.js
with open('i18n.js', 'r', encoding='utf-8') as f:
    i18n_code = f.read()

i18n_code = i18n_code.replace('recoveryNote: "GHI CHU H?I PH?C"', 'recoveryNote: "LỜI NHẮN PHỤC HỒI"')
i18n_code = i18n_code.replace('recoveryNote: "GHI CHÚ HỒI PHỤC"', 'recoveryNote: "LỜI NHẮN PHỤC HỒI"')
i18n_code = i18n_code.replace('recoveryNote: "RECOVERY NOTE"', 'recoveryNote: "RECOVERY NOTICE"')
i18n_code = i18n_code.replace('viewNote: "View Recovery Note"', 'viewNote: "View Recovery Notice"')
i18n_code = i18n_code.replace('adjustContinueBtn: "Continue to Recovery Note  "', 'adjustContinueBtn: "Continue to Recovery Notice →"')
i18n_code = i18n_code.replace('adjustContinueBtn: "Continue to Recovery Note →"', 'adjustContinueBtn: "Continue to Recovery Notice →"')

with open('i18n.js', 'w', encoding='utf-8', newline='') as f:
    f.write(i18n_code)
print("i18n.js updated successfully")

# 3. Update recoveryNote.js user-facing text
with open('recoveryNote.js', 'r', encoding='utf-8') as f:
    note_code = f.read()

note_code = note_code.replace('>RECOVERY NOTE<', '>RECOVERY NOTICE<')
note_code = note_code.replace('>View Recovery Note<', '>View Recovery Notice<')
note_code = note_code.replace('>My Recovery Note<', '>My Recovery Notice<')
note_code = note_code.replace('>EDIT RECOVERY NOTE<', '>EDIT RECOVERY NOTICE<')
note_code = note_code.replace('>Update your note<', '>Update your notice<')
note_code = note_code.replace('>View full note<', '>View full notice<')

note_code = note_code.replace('\r\n', '\n')
assert '\r' not in note_code, "Carriage returns in recoveryNote.js"

with open('recoveryNote.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(note_code)
print("recoveryNote.js updated successfully")
