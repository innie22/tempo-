import os

with open('recoverySetup.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update isWarmStage
target1 = "const isWarmStage = (stageNum === 'case2_welcome' || stageNum === 'returning_welcome' || stageNum === 'case2_review' || stageNum === 'review_system' || stageNum === 'adjust_trackers');"
replacement1 = "const isWarmStage = (stageNum === 'case2_welcome' || stageNum === 'returning_welcome' || stageNum === 'case2_review' || stageNum === 'review_system' || stageNum === 'adjust_trackers' || stageNum === 'adjust_note' || stageNum === 'adjust_review');"

assert target1 in content, "target1 not found"
content = content.replace(target1, replacement1, 1)

# 2. Refine renderStageAdjustNote
target_note = """    function renderStageAdjustNote(container) {
        const warningSigns = adjustmentDraft.noteItems.filter(i => i.type === 'warning_sign');
        const helpers = adjustmentDraft.noteItems.filter(i => i.type === 'helper');
        const reminders = adjustmentDraft.noteItems.filter(i => i.type === 'reminder');
        const people = adjustmentDraft.noteItems.filter(i => i.type === 'support_person');

        container.innerHTML = `
            <div class="space-y-5">
                <div class="flex items-center justify-between text-xs text-[#6F6B68]">
                    <span class="font-bold uppercase tracking-wider text-[#166545]">STEP 2 OF 3 · RECOVERY NOTE</span>
                    <span>Review Recovery Note</span>
                </div>

                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                        Review your Recovery Note
                    </h3>
                    <p class="text-xs text-[#6F6B68]">
                        Review warning signs, things that help, reminders, and support contacts.
                    </p>
                </div>

                <div class="space-y-4 max-h-[46vh] overflow-y-auto pr-1">
                    <!-- Warning Signs -->
                    <div class="p-3.5 rounded-2xl bg-stone-50 border border-stone-200 space-y-2">
                        <span class="text-xs font-extrabold uppercase tracking-wider text-[#B83D08]">
                            1. When I start getting overwhelmed (${warningSigns.length})
                        </span>
                        <div class="space-y-1">
                            ${warningSigns.map((w, idx) => `
                                <div class="flex items-center justify-between p-1.5 rounded-lg bg-white border border-stone-200 text-xs">
                                    <span>${escapeHTML(w.text)}</span>
                                    <button type="button" onclick="window.TempoRecoverySetup.removeAdjustmentNoteItem('warning_sign', ${idx})"
                                            class="text-stone-400 hover:text-red-500 font-bold ml-2">✕</button>
                                </div>
                            `).join('')}
                        </div>
                        <div class="flex items-center space-x-2 pt-1">
                            <input type="text" id="input-adjust-custom-sign" placeholder="+ Add warning sign..."
                                   class="flex-1 px-3 py-1.5 rounded-xl border border-stone-200 text-xs bg-white">
                            <button type="button" onclick="window.TempoRecoverySetup.addAdjustmentNoteItem('warning_sign')"
                                    class="px-3 py-1.5 rounded-xl bg-white border border-stone-300 text-xs font-bold text-stone-700">Add</button>
                        </div>
                    </div>

                    <!-- Helpers -->
                    <div class="p-3.5 rounded-2xl bg-stone-50 border border-stone-200 space-y-2">
                        <span class="text-xs font-extrabold uppercase tracking-wider text-[#166545]">
                            2. Things that seem to help (${helpers.length})
                        </span>
                        <div class="space-y-1">
                            ${helpers.map((h, idx) => `
                                <div class="flex items-center justify-between p-1.5 rounded-lg bg-white border border-stone-200 text-xs">
                                    <span>${escapeHTML(h.text)}</span>
                                    <button type="button" onclick="window.TempoRecoverySetup.removeAdjustmentNoteItem('helper', ${idx})"
                                            class="text-stone-400 hover:text-red-500 font-bold ml-2">✕</button>
                                </div>
                            `).join('')}
                        </div>
                        <div class="flex items-center space-x-2 pt-1">
                            <input type="text" id="input-adjust-custom-helper" placeholder="+ Add helpful thing..."
                                   class="flex-1 px-3 py-1.5 rounded-xl border border-stone-200 text-xs bg-white">
                            <button type="button" onclick="window.TempoRecoverySetup.addAdjustmentNoteItem('helper')"
                                    class="px-3 py-1.5 rounded-xl bg-white border border-stone-300 text-xs font-bold text-stone-700">Add</button>
                        </div>
                    </div>

                    <!-- Reminders -->
                    <div class="p-3.5 rounded-2xl bg-stone-50 border border-stone-200 space-y-2">
                        <span class="text-xs font-extrabold uppercase tracking-wider text-[#1E40AF]">
                            3. Gentle reminders (${reminders.length})
                        </span>
                        <div class="space-y-1">
                            ${reminders.map((r, idx) => `
                                <div class="flex items-center justify-between p-1.5 rounded-lg bg-white border border-stone-200 text-xs">
                                    <span>"${escapeHTML(r.text)}"</span>
                                    <button type="button" onclick="window.TempoRecoverySetup.removeAdjustmentNoteItem('reminder', ${idx})"
                                            class="text-stone-400 hover:text-red-500 font-bold ml-2">✕</button>
                                </div>
                            `).join('')}
                        </div>
                        <div class="flex items-center space-x-2 pt-1">
                            <input type="text" id="input-adjust-custom-reminder" placeholder="+ Add reminder..."
                                   class="flex-1 px-3 py-1.5 rounded-xl border border-stone-200 text-xs bg-white">
                            <button type="button" onclick="window.TempoRecoverySetup.addAdjustmentNoteItem('reminder')"
                                    class="px-3 py-1.5 rounded-xl bg-white border border-stone-300 text-xs font-bold text-stone-700">Add</button>
                        </div>
                    </div>

                    <!-- Support People -->
                    <div class="p-3.5 rounded-2xl bg-stone-50 border border-stone-200 space-y-2">
                        <span class="text-xs font-extrabold uppercase tracking-wider text-[#7C3AED]">
                            4. People I can reach out to (${people.length})
                        </span>
                        <div class="space-y-1">
                            ${people.map((p, idx) => `
                                <div class="flex items-center justify-between p-1.5 rounded-lg bg-white border border-stone-200 text-xs">
                                    <span><strong>${escapeHTML(p.text)}</strong> ${p.metadata && p.metadata.relationship ? `<span class="text-stone-400">(${escapeHTML(p.metadata.relationship)})</span>` : ''}</span>
                                    <button type="button" onclick="window.TempoRecoverySetup.removeAdjustmentNoteItem('support_person', ${idx})"
                                            class="text-stone-400 hover:text-red-500 font-bold ml-2">✕</button>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <!-- Nav footer -->
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage('adjust_trackers')"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ← Back to Trackers
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage('adjust_review')"
                            class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer">
                        <span>Review Proposed Changes</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }"""

refined_note = """    function renderStageAdjustNote(container) {
        const isVi = isViLocale();
        updateRecoveryCardTheme(true);

        const warningSigns = adjustmentDraft.noteItems.filter(i => i.type === 'warning_sign');
        const helpers = adjustmentDraft.noteItems.filter(i => i.type === 'helper');
        const reminders = adjustmentDraft.noteItems.filter(i => i.type === 'reminder');
        const people = adjustmentDraft.noteItems.filter(i => i.type === 'support_person');

        const stepBadge = isVi ? 'BƯỚC 2/3 · LỜI NHẮN PHỤC HỒI' : 'STEP 2 OF 3 · RECOVERY NOTE';
        const tagLabel = isVi ? 'Xem lại Lời nhắn phục hồi' : 'Review Recovery Note';
        const title = isVi ? 'Xem lại Lời nhắn phục hồi' : 'Review your Recovery Note';
        const desc = isVi
            ? 'Xem lại dấu hiệu cảnh báo, những điều giúp ích, lời nhắc và liên hệ hỗ trợ.'
            : 'Review warning signs, things that help, reminders, and support contacts.';

        const sec1Title = isVi ? 'Khi tôi bắt đầu quá tải' : 'When I start getting overwhelmed';
        const sec2Title = isVi ? 'Những điều giúp ích' : 'Things that seem to help';
        const sec3Title = isVi ? 'Lời nhắc nhở nhẹ nhàng' : 'Gentle reminders';
        const sec4Title = isVi ? 'Người tôi có thể liên hệ' : 'People I can reach out to';

        const addLabel = isVi ? 'Thêm' : 'Add';
        const backBtnLabel = isVi ? 'Quay lại mục tracking' : 'Back to Trackers';
        const reviewBtnLabel = isVi ? 'Xem lại các thay đổi' : 'Review Proposed Changes';

        container.innerHTML = `
            <div class="space-y-5" data-tempo-ui="adjust-recovery-note">
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

                <div class="space-y-4 max-h-[46vh] overflow-y-auto pr-1.5 recovery-note-scroll">
                    <!-- SECTION 1: Warning Signs (Warm Blush Accent) -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#ECC9BA]/80 space-y-3 shadow-2xs transition">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#ECC9BA] shrink-0"></span>
                                <h4 class="text-xs font-bold uppercase tracking-wide text-[#202124]">
                                    1. ${escapeHTML(sec1Title)}
                                </h4>
                            </div>
                            <span class="text-[11px] font-semibold text-[#6F6B68]">(${warningSigns.length})</span>
                        </div>
                        <div class="space-y-1.5">
                            ${warningSigns.length === 0 ? `<p class="text-[11px] text-[#6F6B68] italic py-0.5">${isVi ? 'Chưa có mục nào được lưu.' : 'No items added yet.'}</p>` : ''}
                            ${warningSigns.map((w, idx) => `
                                <div class="flex items-center justify-between px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] text-xs text-[#202124] shadow-2xs hover:border-[#ECC9BA] transition">
                                    <span class="font-medium">${escapeHTML(w.text)}</span>
                                    <button type="button" onclick="window.TempoRecoverySetup.removeAdjustmentNoteItem('warning_sign', ${idx})"
                                            class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/30 p-1 rounded-lg text-xs transition cursor-pointer ml-2" title="${isVi ? 'Xóa' : 'Remove'}">✕</button>
                                </div>
                            `).join('')}
                        </div>
                        <div class="flex items-center space-x-2 pt-0.5">
                            <input type="text" id="input-adjust-custom-sign" placeholder="${isVi ? '+ Thêm dấu hiệu cảnh báo...' : '+ Add warning sign...'}"
                                   class="flex-1 px-3.5 py-2 rounded-xl border border-[#EAE4DF] text-xs text-[#202124] bg-white placeholder-[#6F6B68]/60 focus:outline-none focus:border-[#8EA28F] focus:ring-1 focus:ring-[#8EA28F]/30 transition shadow-2xs">
                            <button type="button" onclick="window.TempoRecoverySetup.addAdjustmentNoteItem('warning_sign')"
                                    class="px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] hover:border-[#8EA28F] text-xs font-bold text-[#202124] hover:bg-[#8EA28F]/10 transition cursor-pointer shadow-2xs flex items-center space-x-1 shrink-0">
                                <span>+</span>
                                <span>${escapeHTML(addLabel)}</span>
                            </button>
                        </div>
                    </div>

                    <!-- SECTION 2: Helpers (Sage Green Accent) -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#8EA28F]/40 space-y-3 shadow-2xs transition">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#8EA28F] shrink-0"></span>
                                <h4 class="text-xs font-bold uppercase tracking-wide text-[#202124]">
                                    2. ${escapeHTML(sec2Title)}
                                </h4>
                            </div>
                            <span class="text-[11px] font-semibold text-[#6F6B68]">(${helpers.length})</span>
                        </div>
                        <div class="space-y-1.5">
                            ${helpers.length === 0 ? `<p class="text-[11px] text-[#6F6B68] italic py-0.5">${isVi ? 'Chưa có mục nào được lưu.' : 'No items added yet.'}</p>` : ''}
                            ${helpers.map((h, idx) => `
                                <div class="flex items-center justify-between px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] text-xs text-[#202124] shadow-2xs hover:border-[#8EA28F]/60 transition">
                                    <span class="font-medium">${escapeHTML(h.text)}</span>
                                    <button type="button" onclick="window.TempoRecoverySetup.removeAdjustmentNoteItem('helper', ${idx})"
                                            class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#8EA28F]/20 p-1 rounded-lg text-xs transition cursor-pointer ml-2" title="${isVi ? 'Xóa' : 'Remove'}">✕</button>
                                </div>
                            `).join('')}
                        </div>
                        <div class="flex items-center space-x-2 pt-0.5">
                            <input type="text" id="input-adjust-custom-helper" placeholder="${isVi ? '+ Thêm điều giúp ích...' : '+ Add helpful thing...'}"
                                   class="flex-1 px-3.5 py-2 rounded-xl border border-[#EAE4DF] text-xs text-[#202124] bg-white placeholder-[#6F6B68]/60 focus:outline-none focus:border-[#8EA28F] focus:ring-1 focus:ring-[#8EA28F]/30 transition shadow-2xs">
                            <button type="button" onclick="window.TempoRecoverySetup.addAdjustmentNoteItem('helper')"
                                    class="px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] hover:border-[#8EA28F] text-xs font-bold text-[#202124] hover:bg-[#8EA28F]/10 transition cursor-pointer shadow-2xs flex items-center space-x-1 shrink-0">
                                <span>+</span>
                                <span>${escapeHTML(addLabel)}</span>
                            </button>
                        </div>
                    </div>

                    <!-- SECTION 3: Reminders (Dusty Blue Accent) -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#93AFBC]/50 space-y-3 shadow-2xs transition">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#93AFBC] shrink-0"></span>
                                <h4 class="text-xs font-bold uppercase tracking-wide text-[#202124]">
                                    3. ${escapeHTML(sec3Title)}
                                </h4>
                            </div>
                            <span class="text-[11px] font-semibold text-[#6F6B68]">(${reminders.length})</span>
                        </div>
                        <div class="space-y-1.5">
                            ${reminders.length === 0 ? `<p class="text-[11px] text-[#6F6B68] italic py-0.5">${isVi ? 'Chưa có mục nào được lưu.' : 'No items added yet.'}</p>` : ''}
                            ${reminders.map((r, idx) => `
                                <div class="flex items-center justify-between px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] text-xs text-[#202124] shadow-2xs hover:border-[#93AFBC]/60 transition">
                                    <span class="font-medium italic">"${escapeHTML(r.text)}"</span>
                                    <button type="button" onclick="window.TempoRecoverySetup.removeAdjustmentNoteItem('reminder', ${idx})"
                                            class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#93AFBC]/20 p-1 rounded-lg text-xs transition cursor-pointer ml-2" title="${isVi ? 'Xóa' : 'Remove'}">✕</button>
                                </div>
                            `).join('')}
                        </div>
                        <div class="flex items-center space-x-2 pt-0.5">
                            <input type="text" id="input-adjust-custom-reminder" placeholder="${isVi ? '+ Thêm lời nhắc...' : '+ Add reminder...'}"
                                   class="flex-1 px-3.5 py-2 rounded-xl border border-[#EAE4DF] text-xs text-[#202124] bg-white placeholder-[#6F6B68]/60 focus:outline-none focus:border-[#8EA28F] focus:ring-1 focus:ring-[#8EA28F]/30 transition shadow-2xs">
                            <button type="button" onclick="window.TempoRecoverySetup.addAdjustmentNoteItem('reminder')"
                                    class="px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] hover:border-[#8EA28F] text-xs font-bold text-[#202124] hover:bg-[#8EA28F]/10 transition cursor-pointer shadow-2xs flex items-center space-x-1 shrink-0">
                                <span>+</span>
                                <span>${escapeHTML(addLabel)}</span>
                            </button>
                        </div>
                    </div>

                    <!-- SECTION 4: Support People -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#ECC9BA]/60 space-y-3 shadow-2xs transition">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#ECC9BA] shrink-0"></span>
                                <h4 class="text-xs font-bold uppercase tracking-wide text-[#202124]">
                                    4. ${escapeHTML(sec4Title)}
                                </h4>
                            </div>
                            <span class="text-[11px] font-semibold text-[#6F6B68]">(${people.length})</span>
                        </div>
                        <div class="space-y-1.5">
                            ${people.length === 0 ? `<p class="text-[11px] text-[#6F6B68] italic py-0.5">${isVi ? 'Chưa có người liên hệ nào.' : 'None added yet.'}</p>` : ''}
                            ${people.map((p, idx) => `
                                <div class="flex items-center justify-between px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] text-xs text-[#202124] shadow-2xs hover:border-[#ECC9BA] transition">
                                    <span><strong>${escapeHTML(p.text)}</strong> ${p.metadata && p.metadata.relationship ? `<span class="text-[#6F6B68]">(${escapeHTML(p.metadata.relationship)})</span>` : ''}</span>
                                    <button type="button" onclick="window.TempoRecoverySetup.removeAdjustmentNoteItem('support_person', ${idx})"
                                            class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/30 p-1 rounded-lg text-xs transition cursor-pointer ml-2" title="${isVi ? 'Xóa' : 'Remove'}">✕</button>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <!-- Nav footer -->
                <div class="pt-4 border-t border-[#ECC9BA]/60 flex items-center justify-between">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage('adjust_trackers')"
                            class="px-4 py-2.5 rounded-xl text-xs font-bold text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/20 transition cursor-pointer flex items-center space-x-1.5">
                        <span>←</span>
                        <span>${escapeHTML(backBtnLabel)}</span>
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage('adjust_review')"
                            class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer bg-[#8EA28F] hover:bg-[#7D937E] text-white">
                        <span>${escapeHTML(reviewBtnLabel)}</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }"""

assert target_note in content, "target_note not found"
content = content.replace(target_note, refined_note, 1)

# 3. Refine Stage 4 (onboarding Recovery Note)
target_stage4_sec1 = """                    <!-- SECTION 1: WARNING SIGNS -->
                    <div class="p-4 rounded-2xl bg-stone-50 border border-stone-200 space-y-2.5">
                        <span class="text-xs font-extrabold uppercase tracking-wider text-[#B83D08]">
                            1. When I start getting overwhelmed...
                        </span>"""

refined_stage4_sec1 = """                    <!-- SECTION 1: WARNING SIGNS (Warm Blush Accent) -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#ECC9BA]/80 space-y-3 shadow-2xs">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#ECC9BA] shrink-0"></span>
                            <span class="text-xs font-bold uppercase tracking-wider text-[#202124]">
                                1. When I start getting overwhelmed...
                            </span>
                        </div>"""

assert target_stage4_sec1 in content, "target_stage4_sec1 not found"
content = content.replace(target_stage4_sec1, refined_stage4_sec1, 1)

target_stage4_sec2 = """                    <!-- SECTION 2: HELPERS -->
                    <div class="p-4 rounded-2xl bg-stone-50 border border-stone-200 space-y-2.5">
                        <span class="text-xs font-extrabold uppercase tracking-wider text-[#166545]">
                            2. Things that seem to help...
                        </span>"""

refined_stage4_sec2 = """                    <!-- SECTION 2: HELPERS (Sage Green Accent) -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#8EA28F]/40 space-y-3 shadow-2xs">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#8EA28F] shrink-0"></span>
                            <span class="text-xs font-bold uppercase tracking-wider text-[#202124]">
                                2. Things that seem to help...
                            </span>
                        </div>"""

assert target_stage4_sec2 in content, "target_stage4_sec2 not found"
content = content.replace(target_stage4_sec2, refined_stage4_sec2, 1)

target_stage4_sec3 = """                    <!-- SECTION 3: REMINDERS -->
                    <div class="p-4 rounded-2xl bg-stone-50 border border-stone-200 space-y-2.5">
                        <span class="text-xs font-extrabold uppercase tracking-wider text-[#1E40AF]">
                            3. What I want to remind myself...
                        </span>"""

refined_stage4_sec3 = """                    <!-- SECTION 3: REMINDERS (Dusty Blue Accent) -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#93AFBC]/50 space-y-3 shadow-2xs">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#93AFBC] shrink-0"></span>
                            <span class="text-xs font-bold uppercase tracking-wider text-[#202124]">
                                3. What I want to remind myself...
                            </span>
                        </div>"""

assert target_stage4_sec3 in content, "target_stage4_sec3 not found"
content = content.replace(target_stage4_sec3, refined_stage4_sec3, 1)

target_stage4_sec4 = """                    <!-- SECTION 4: SUPPORT PEOPLE -->
                    <div class="p-4 rounded-2xl bg-stone-50 border border-stone-200 space-y-2.5">
                        <span class="text-xs font-extrabold uppercase tracking-wider text-[#7C3AED]">
                            4. People I can reach out to...
                        </span>"""

refined_stage4_sec4 = """                    <!-- SECTION 4: SUPPORT PEOPLE (Warm Blush Accent) -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#ECC9BA]/60 space-y-3 shadow-2xs">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#ECC9BA] shrink-0"></span>
                            <span class="text-xs font-bold uppercase tracking-wider text-[#202124]">
                                4. People I can reach out to...
                            </span>
                        </div>"""

assert target_stage4_sec4 in content, "target_stage4_sec4 not found"
content = content.replace(target_stage4_sec4, refined_stage4_sec4, 1)

# Stage 4 checkboxes and inputs focus colors
content = content.replace('class="rounded text-[#B83D08] focus:ring-[#B83D08]"', 'class="rounded text-[#8EA28F] focus:ring-[#8EA28F]"')
content = content.replace('class="rounded text-[#166545] focus:ring-[#166545]"', 'class="rounded text-[#8EA28F] focus:ring-[#8EA28F]"')
content = content.replace('class="rounded text-[#1E40AF] focus:ring-[#1E40AF]"', 'class="rounded text-[#8EA28F] focus:ring-[#8EA28F]"')
content = content.replace("focus:border-[#B83D08]", "focus:border-[#8EA28F]")
content = content.replace("focus:border-[#166545]", "focus:border-[#8EA28F]")
content = content.replace("focus:border-[#1E40AF]", "focus:border-[#8EA28F]")
content = content.replace("focus:border-[#7C3AED]", "focus:border-[#8EA28F]")

# Stage 4 custom add buttons
content = content.replace(
    'class="px-3 py-1.5 rounded-xl bg-white border border-stone-300 text-xs font-bold text-stone-700 transition cursor-pointer">\n                                Add',
    'class="px-3.5 py-1.5 rounded-xl bg-white border border-[#EAE4DF] hover:border-[#8EA28F] text-xs font-bold text-[#202124] hover:bg-[#8EA28F]/10 transition cursor-pointer shadow-2xs">\n                                + Add'
)

# Enforce lone-LF
content = content.replace('\r\n', '\n')
assert '\r' not in content, "Carriage returns found"

with open('recoverySetup.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("recoverySetup.js updated successfully with LF line endings")
