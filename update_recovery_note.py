import os

with open('recoveryNote.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update renderHomeCard
target_home_card = """                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-[#FF6B2C] inline-block"></span>
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#FF6B2C]">
                                RECOVERY NOTE
                            </span>
                        </div>
                        <span class="text-[11px] font-semibold text-stone-400">${count} ${count === 1 ? 'item' : 'items'} saved</span>
                    </div>

                    <div class="space-y-1">
                        <h4 class="font-heading text-sm sm:text-base font-bold text-[#202124]">A note to myself</h4>
                        <p class="text-xs sm:text-sm text-stone-600 italic font-medium leading-relaxed bg-[#FFFBF7] p-3 rounded-2xl border border-[#FFD2BA]/50">
                            ${escapeHTML(previewText)}
                        </p>
                    </div>

                    <div class="pt-1 flex items-center justify-between">
                        <button type="button" onclick="window.TempoRecoveryNote.openViewModal()"
                                class="text-xs font-bold text-[#166545] hover:text-[#0E4A32] transition cursor-pointer flex items-center space-x-1">
                            <span>View Recovery Note</span>
                            <span>→</span>
                        </button>"""

refined_home_card = """                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-[#8EA28F] inline-block"></span>
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#4F6851]">
                                RECOVERY NOTE
                            </span>
                        </div>
                        <span class="text-[11px] font-semibold text-[#6F6B68]">${count} ${count === 1 ? 'item' : 'items'} saved</span>
                    </div>

                    <div class="space-y-1">
                        <h4 class="font-heading text-sm sm:text-base font-bold text-[#202124]">A note to myself</h4>
                        <p class="text-xs sm:text-sm text-[#484541] italic font-medium leading-relaxed bg-[#FFF9F4] p-3.5 rounded-2xl border border-[#ECC9BA]/60">
                            ${escapeHTML(previewText)}
                        </p>
                    </div>

                    <div class="pt-1 flex items-center justify-between">
                        <button type="button" onclick="window.TempoRecoveryNote.openViewModal()"
                                class="text-xs font-bold text-[#4F6851] hover:text-[#2E4630] transition cursor-pointer flex items-center space-x-1">
                            <span>View Recovery Note</span>
                            <span>→</span>
                        </button>"""

assert target_home_card in content, "target_home_card not found"
content = content.replace(target_home_card, refined_home_card, 1)

# Empty home card link color
content = content.replace(
    'class="text-xs font-bold text-[#166545] hover:text-[#0E4A32] transition cursor-pointer flex items-center space-x-1">',
    'class="text-xs font-bold text-[#4F6851] hover:text-[#2E4630] transition cursor-pointer flex items-center space-x-1">'
)

# 2. Update ensureModalsMounted
target_modals = """            <!-- MODAL: VIEW RECOVERY NOTE -->
            <div id="modal-recovery-note-view" class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-4 hidden" role="dialog" aria-modal="true">
                <div class="tempo-card max-w-lg w-full p-6 sm:p-8 space-y-6 bg-white rounded-3xl shadow-2xl relative border border-[#EAE4DF] max-h-[90vh] overflow-y-auto">
                    <button type="button" onclick="window.TempoRecoveryNote.closeViewModal()" class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer" title="Close">✕</button>

                    <div class="space-y-1">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-[#FF6B2C] inline-block"></span>
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#FF6B2C]">RECOVERY NOTE</span>
                        </div>
                        <h3 class="font-heading text-2xl font-extrabold text-[#202124]">My Recovery Note</h3>
                        <p class="text-xs text-[#6F6B68]">Things you wanted to remember when things feel heavy.</p>
                    </div>

                    <div id="recovery-note-view-content" class="space-y-5"></div>

                    <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                        <button type="button" onclick="window.TempoRecoveryNote.openEditModal()"
                                class="btn-primary px-4 py-2 rounded-xl text-xs sm:text-sm font-bold shadow-xs transition cursor-pointer">
                            Edit note
                        </button>
                        <button type="button" onclick="window.TempoRecoveryNote.closeViewModal()"
                                class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                            Close
                        </button>
                    </div>
                </div>
            </div>

            <!-- MODAL: EDIT RECOVERY NOTE -->
            <div id="modal-recovery-note-edit" class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-4 hidden" role="dialog" aria-modal="true">
                <div class="tempo-card max-w-xl w-full p-6 sm:p-8 space-y-6 bg-white rounded-3xl shadow-2xl relative border border-[#EAE4DF] max-h-[92vh] overflow-y-auto">
                    <button type="button" onclick="window.TempoRecoveryNote.closeEditModal()" class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer" title="Close">✕</button>

                    <div class="space-y-1">
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#FF6B2C]">EDIT RECOVERY NOTE</span>
                        <h3 class="font-heading text-2xl font-extrabold text-[#202124]">Update your note</h3>
                        <p class="text-xs text-[#6F6B68]">Keep what's useful. All sections are completely optional.</p>
                    </div>

                    <div class="space-y-6">
                        <!-- SECTION 1: WARNING SIGNS -->
                        <div class="space-y-2.5 p-4 rounded-2xl bg-stone-50 border border-stone-200">
                            <h4 class="text-xs font-extrabold uppercase tracking-wider text-[#B83D08] flex items-center space-x-1.5">
                                <span>🔴</span>
                                <span>When I start getting overwhelmed...</span>
                            </h4>
                            <div id="edit-section-warning_sign" class="space-y-2"></div>
                            <div class="flex items-center space-x-2 pt-1">
                                <input type="text" id="input-add-warning_sign" placeholder="Add an early sign..."
                                       class="flex-1 px-3 py-1.5 rounded-xl border border-stone-300 text-xs text-[#202124] focus:outline-none focus:border-[#B83D08]">
                                <button type="button" onclick="window.TempoRecoveryNote.handleAddFromInput('warning_sign')"
                                        class="px-3 py-1.5 rounded-xl bg-white border border-stone-300 hover:border-stone-400 text-xs font-bold text-stone-700 transition cursor-pointer">
                                    + Add
                                </button>
                            </div>
                        </div>

                        <!-- SECTION 2: HELPERS -->
                        <div class="space-y-2.5 p-4 rounded-2xl bg-stone-50 border border-stone-200">
                            <h4 class="text-xs font-extrabold uppercase tracking-wider text-[#166545] flex items-center space-x-1.5">
                                <span>🟢</span>
                                <span>Things that seem to help...</span>
                            </h4>
                            <div id="edit-section-helper" class="space-y-2"></div>
                            <div class="flex items-center space-x-2 pt-1">
                                <input type="text" id="input-add-helper" placeholder="Add something that helps..."
                                       class="flex-1 px-3 py-1.5 rounded-xl border border-stone-300 text-xs text-[#202124] focus:outline-none focus:border-[#166545]">
                                <button type="button" onclick="window.TempoRecoveryNote.handleAddFromInput('helper')"
                                        class="px-3 py-1.5 rounded-xl bg-white border border-stone-300 hover:border-stone-400 text-xs font-bold text-stone-700 transition cursor-pointer">
                                    + Add
                                </button>
                            </div>
                        </div>

                        <!-- SECTION 3: REMINDERS -->
                        <div class="space-y-2.5 p-4 rounded-2xl bg-stone-50 border border-stone-200">
                            <h4 class="text-xs font-extrabold uppercase tracking-wider text-[#1E40AF] flex items-center space-x-1.5">
                                <span>🔵</span>
                                <span>What I want to remind myself...</span>
                            </h4>
                            <div id="edit-section-reminder" class="space-y-2"></div>
                            <div class="flex items-center space-x-2 pt-1">
                                <input type="text" id="input-add-reminder" placeholder="Add a gentle reminder..."
                                       class="flex-1 px-3 py-1.5 rounded-xl border border-stone-300 text-xs text-[#202124] focus:outline-none focus:border-[#1E40AF]">
                                <button type="button" onclick="window.TempoRecoveryNote.handleAddFromInput('reminder')"
                                        class="px-3 py-1.5 rounded-xl bg-white border border-stone-300 hover:border-stone-400 text-xs font-bold text-stone-700 transition cursor-pointer">
                                    + Add
                                </button>
                            </div>
                        </div>

                        <!-- SECTION 4: SUPPORT PEOPLE -->
                        <div class="space-y-2.5 p-4 rounded-2xl bg-stone-50 border border-stone-200">
                            <h4 class="text-xs font-extrabold uppercase tracking-wider text-[#7C3AED] flex items-center space-x-1.5">
                                <span>💜</span>
                                <span>People I can reach out to...</span>
                            </h4>
                            <div id="edit-section-support_person" class="space-y-2"></div>
                            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                                <input type="text" id="input-add-person-name" placeholder="Name (e.g. Nhung)"
                                       class="px-3 py-1.5 rounded-xl border border-stone-300 text-xs text-[#202124] focus:outline-none focus:border-[#7C3AED]">
                                <div class="flex items-center space-x-2">
                                    <input type="text" id="input-add-person-rel" placeholder="Relationship (e.g. Friend)"
                                           class="flex-1 px-3 py-1.5 rounded-xl border border-stone-300 text-xs text-[#202124] focus:outline-none focus:border-[#7C3AED]">
                                    <button type="button" onclick="window.TempoRecoveryNote.handleAddPerson()"
                                            class="px-3 py-1.5 rounded-xl bg-white border border-stone-300 hover:border-stone-400 text-xs font-bold text-stone-700 transition cursor-pointer">
                                        + Add
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                        <button type="button" onclick="window.TempoRecoveryNote.closeEditModal()"
                                class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                            Done
                        </button>
                        <button type="button" onclick="window.TempoRecoveryNote.openViewModal()"
                                class="text-xs font-bold text-[#166545] hover:text-[#0E4A32] transition cursor-pointer">
                            View full note →
                        </button>
                    </div>
                </div>
            </div>"""

refined_modals = """            <!-- MODAL: VIEW RECOVERY NOTE -->
            <div id="modal-recovery-note-view" class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-4 hidden" role="dialog" aria-modal="true">
                <div class="tempo-card max-w-lg w-full p-6 sm:p-8 space-y-6 bg-[#FAF4F0] rounded-3xl shadow-2xl relative border border-[#ECC9BA] max-h-[90vh] overflow-y-auto recovery-note-scroll">
                    <button type="button" onclick="window.TempoRecoveryNote.closeViewModal()" class="absolute top-5 right-5 text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/40 p-2 rounded-xl text-lg transition cursor-pointer" title="Close">✕</button>

                    <div class="space-y-1">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-[#8EA28F] inline-block"></span>
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#4F6851]">RECOVERY NOTE</span>
                        </div>
                        <h3 class="font-heading text-2xl font-extrabold text-[#202124]">My Recovery Note</h3>
                        <p class="text-xs text-[#6F6B68]">Things you wanted to remember when things feel heavy.</p>
                    </div>

                    <div id="recovery-note-view-content" class="space-y-4"></div>

                    <div class="pt-4 border-t border-[#ECC9BA]/60 flex items-center justify-between">
                        <button type="button" onclick="window.TempoRecoveryNote.openEditModal()"
                                class="btn-primary bg-[#8EA28F] hover:bg-[#7D937E] text-white px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold shadow-xs transition cursor-pointer">
                            Edit note
                        </button>
                        <button type="button" onclick="window.TempoRecoveryNote.closeViewModal()"
                                class="px-4 py-2.5 rounded-xl text-xs font-bold text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/20 transition cursor-pointer">
                            Close
                        </button>
                    </div>
                </div>
            </div>

            <!-- MODAL: EDIT RECOVERY NOTE -->
            <div id="modal-recovery-note-edit" class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-4 hidden" role="dialog" aria-modal="true">
                <div class="tempo-card max-w-xl w-full p-6 sm:p-8 space-y-6 bg-[#FAF4F0] rounded-3xl shadow-2xl relative border border-[#ECC9BA] max-h-[92vh] overflow-y-auto recovery-note-scroll">
                    <button type="button" onclick="window.TempoRecoveryNote.closeEditModal()" class="absolute top-5 right-5 text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/40 p-2 rounded-xl text-lg transition cursor-pointer" title="Close">✕</button>

                    <div class="space-y-1">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-[#8EA28F] inline-block"></span>
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#4F6851]">EDIT RECOVERY NOTE</span>
                        </div>
                        <h3 class="font-heading text-2xl font-extrabold text-[#202124]">Update your note</h3>
                        <p class="text-xs text-[#6F6B68]">Keep what's useful. All sections are completely optional.</p>
                    </div>

                    <div class="space-y-4">
                        <!-- SECTION 1: WARNING SIGNS (Warm Blush Accent) -->
                        <div class="space-y-3 p-4 rounded-2xl bg-[#FFF9F4] border border-[#ECC9BA]/80 shadow-2xs transition">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#ECC9BA] shrink-0"></span>
                                <h4 class="text-xs font-bold uppercase tracking-wider text-[#202124]">
                                    When I start getting overwhelmed...
                                </h4>
                            </div>
                            <div id="edit-section-warning_sign" class="space-y-2"></div>
                            <div class="flex items-center space-x-2 pt-0.5">
                                <input type="text" id="input-add-warning_sign" placeholder="Add an early sign..."
                                       class="flex-1 px-3.5 py-2 rounded-xl border border-[#EAE4DF] text-xs text-[#202124] bg-white placeholder-[#6F6B68]/60 focus:outline-none focus:border-[#8EA28F] focus:ring-1 focus:ring-[#8EA28F]/30 transition shadow-2xs">
                                <button type="button" onclick="window.TempoRecoveryNote.handleAddFromInput('warning_sign')"
                                        class="px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] hover:border-[#8EA28F] text-xs font-bold text-[#202124] hover:bg-[#8EA28F]/10 transition cursor-pointer shadow-2xs flex items-center space-x-1 shrink-0">
                                    <span>+ Add</span>
                                </button>
                            </div>
                        </div>

                        <!-- SECTION 2: HELPERS (Sage Green Accent) -->
                        <div class="space-y-3 p-4 rounded-2xl bg-[#FFF9F4] border border-[#8EA28F]/40 shadow-2xs transition">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#8EA28F] shrink-0"></span>
                                <h4 class="text-xs font-bold uppercase tracking-wider text-[#202124]">
                                    Things that seem to help...
                                </h4>
                            </div>
                            <div id="edit-section-helper" class="space-y-2"></div>
                            <div class="flex items-center space-x-2 pt-0.5">
                                <input type="text" id="input-add-helper" placeholder="Add something that helps..."
                                       class="flex-1 px-3.5 py-2 rounded-xl border border-[#EAE4DF] text-xs text-[#202124] bg-white placeholder-[#6F6B68]/60 focus:outline-none focus:border-[#8EA28F] focus:ring-1 focus:ring-[#8EA28F]/30 transition shadow-2xs">
                                <button type="button" onclick="window.TempoRecoveryNote.handleAddFromInput('helper')"
                                        class="px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] hover:border-[#8EA28F] text-xs font-bold text-[#202124] hover:bg-[#8EA28F]/10 transition cursor-pointer shadow-2xs flex items-center space-x-1 shrink-0">
                                    <span>+ Add</span>
                                </button>
                            </div>
                        </div>

                        <!-- SECTION 3: REMINDERS (Dusty Blue Accent) -->
                        <div class="space-y-3 p-4 rounded-2xl bg-[#FFF9F4] border border-[#93AFBC]/50 shadow-2xs transition">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#93AFBC] shrink-0"></span>
                                <h4 class="text-xs font-bold uppercase tracking-wider text-[#202124]">
                                    What I want to remind myself...
                                </h4>
                            </div>
                            <div id="edit-section-reminder" class="space-y-2"></div>
                            <div class="flex items-center space-x-2 pt-0.5">
                                <input type="text" id="input-add-reminder" placeholder="Add a gentle reminder..."
                                       class="flex-1 px-3.5 py-2 rounded-xl border border-[#EAE4DF] text-xs text-[#202124] bg-white placeholder-[#6F6B68]/60 focus:outline-none focus:border-[#8EA28F] focus:ring-1 focus:ring-[#8EA28F]/30 transition shadow-2xs">
                                <button type="button" onclick="window.TempoRecoveryNote.handleAddFromInput('reminder')"
                                        class="px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] hover:border-[#8EA28F] text-xs font-bold text-[#202124] hover:bg-[#8EA28F]/10 transition cursor-pointer shadow-2xs flex items-center space-x-1 shrink-0">
                                    <span>+ Add</span>
                                </button>
                            </div>
                        </div>

                        <!-- SECTION 4: SUPPORT PEOPLE (Warm Blush Accent) -->
                        <div class="space-y-3 p-4 rounded-2xl bg-[#FFF9F4] border border-[#ECC9BA]/60 shadow-2xs transition">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#ECC9BA] shrink-0"></span>
                                <h4 class="text-xs font-bold uppercase tracking-wider text-[#202124]">
                                    People I can reach out to...
                                </h4>
                            </div>
                            <div id="edit-section-support_person" class="space-y-2"></div>
                            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-0.5">
                                <input type="text" id="input-add-person-name" placeholder="Name (e.g. Nhung)"
                                       class="px-3.5 py-2 rounded-xl border border-[#EAE4DF] text-xs text-[#202124] bg-white placeholder-[#6F6B68]/60 focus:outline-none focus:border-[#8EA28F] focus:ring-1 focus:ring-[#8EA28F]/30 transition shadow-2xs">
                                <div class="flex items-center space-x-2">
                                    <input type="text" id="input-add-person-rel" placeholder="Relationship (e.g. Friend)"
                                           class="flex-1 px-3.5 py-2 rounded-xl border border-[#EAE4DF] text-xs text-[#202124] bg-white placeholder-[#6F6B68]/60 focus:outline-none focus:border-[#8EA28F] focus:ring-1 focus:ring-[#8EA28F]/30 transition shadow-2xs">
                                    <button type="button" onclick="window.TempoRecoveryNote.handleAddPerson()"
                                            class="px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] hover:border-[#8EA28F] text-xs font-bold text-[#202124] hover:bg-[#8EA28F]/10 transition cursor-pointer shadow-2xs flex items-center space-x-1 shrink-0">
                                        <span>+ Add</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="pt-4 border-t border-[#ECC9BA]/60 flex items-center justify-between">
                        <button type="button" onclick="window.TempoRecoveryNote.closeEditModal()"
                                class="btn-primary bg-[#8EA28F] hover:bg-[#7D937E] text-white px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer">
                            Done
                        </button>
                        <button type="button" onclick="window.TempoRecoveryNote.openViewModal()"
                                class="px-4 py-2.5 rounded-xl text-xs font-bold text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/20 transition cursor-pointer flex items-center space-x-1">
                            <span>View full note</span>
                            <span>→</span>
                        </button>
                    </div>
                </div>
            </div>"""

assert target_modals in content, "target_modals not found"
content = content.replace(target_modals, refined_modals, 1)

# 3. Update renderViewContent
target_view_content = """        const sections = [
            { type: ITEM_TYPES.WARNING_SIGN, icon: '🔴', title: SECTION_TITLES.warning_sign, color: '#B83D08' },
            { type: ITEM_TYPES.HELPER, icon: '🟢', title: SECTION_TITLES.helper, color: '#166545' },
            { type: ITEM_TYPES.REMINDER, icon: '🔵', title: SECTION_TITLES.reminder, color: '#1E40AF' },
            { type: ITEM_TYPES.SUPPORT_PERSON, icon: '💜', title: SECTION_TITLES.support_person, color: '#7C3AED' }
        ];

        let html = '';
        sections.forEach(sec => {
            const secItems = items.filter(it => it.type === sec.type);
            if (secItems.length === 0) return; // Only show sections with actual content!

            html += `
                <div class="space-y-2 p-4 rounded-2xl bg-stone-50/70 border border-stone-200/80">
                    <h4 class="text-xs font-extrabold uppercase tracking-wider text-[#202124] flex items-center space-x-1.5">
                        <span>${sec.icon}</span>
                        <span>${escapeHTML(sec.title)}</span>
                    </h4>
                    <ul class="space-y-1.5 pl-2">
                        ${secItems.map(it => {
                            if (sec.type === ITEM_TYPES.SUPPORT_PERSON) {
                                const rel = it.metadata?.relationship ? ` <span class="text-stone-400 font-normal">(${escapeHTML(it.metadata.relationship)})</span>` : '';
                                return `<li class="text-xs font-bold text-[#202124] flex items-center space-x-2"><span>•</span><span>${escapeHTML(it.text)}${rel}</span></li>`;
                            }
                            if (sec.type === ITEM_TYPES.REMINDER) {
                                return `<li class="text-xs text-stone-700 italic flex items-start space-x-2"><span>•</span><span>"${escapeHTML(it.text)}"</span></li>`;
                            }
                            return `<li class="text-xs text-stone-700 flex items-start space-x-2"><span>•</span><span>${escapeHTML(it.text)}</span></li>`;
                        }).join('')}
                    </ul>
                </div>
            `;
        });"""

refined_view_content = """        const sections = [
            { type: ITEM_TYPES.WARNING_SIGN, title: SECTION_TITLES.warning_sign, color: '#ECC9BA' },
            { type: ITEM_TYPES.HELPER, title: SECTION_TITLES.helper, color: '#8EA28F' },
            { type: ITEM_TYPES.REMINDER, title: SECTION_TITLES.reminder, color: '#93AFBC' },
            { type: ITEM_TYPES.SUPPORT_PERSON, title: SECTION_TITLES.support_person, color: '#ECC9BA' }
        ];

        let html = '';
        sections.forEach(sec => {
            const secItems = items.filter(it => it.type === sec.type);
            if (secItems.length === 0) return; // Only show sections with actual content!

            html += `
                <div class="space-y-2.5 p-4 rounded-2xl bg-[#FFF9F4] border border-[#EAE4DF] shadow-2xs">
                    <div class="flex items-center space-x-2">
                        <span class="w-2.5 h-2.5 rounded-full inline-block shrink-0" style="background-color: ${sec.color};"></span>
                        <h4 class="text-xs font-bold uppercase tracking-wider text-[#202124]">
                            ${escapeHTML(sec.title)}
                        </h4>
                    </div>
                    <ul class="space-y-1.5 pl-3.5">
                        ${secItems.map(it => {
                            if (sec.type === ITEM_TYPES.SUPPORT_PERSON) {
                                const rel = it.metadata?.relationship ? ` <span class="text-[#6F6B68] font-normal">(${escapeHTML(it.metadata.relationship)})</span>` : '';
                                return `<li class="text-xs font-bold text-[#202124] flex items-center space-x-2"><span class="text-[#8EA28F]">•</span><span>${escapeHTML(it.text)}${rel}</span></li>`;
                            }
                            if (sec.type === ITEM_TYPES.REMINDER) {
                                return `<li class="text-xs text-[#484541] italic flex items-start space-x-2"><span class="text-[#93AFBC]">•</span><span>"${escapeHTML(it.text)}"</span></li>`;
                            }
                            return `<li class="text-xs text-[#484541] flex items-start space-x-2"><span class="text-[#8EA28F]">•</span><span>${escapeHTML(it.text)}</span></li>`;
                        }).join('')}
                    </ul>
                </div>
            `;
        });"""

assert target_view_content in content, "target_view_content not found"
content = content.replace(target_view_content, refined_view_content, 1)

# 4. Update renderEditSections item card styling
target_edit_item = """                return `
                    <div class="flex items-center justify-between p-2 rounded-xl bg-white border border-stone-200 text-xs">
                        <span class="font-medium text-[#202124]">${label}</span>
                        <button type="button" onclick="window.TempoRecoveryNote.handleRemoveItem('${it.id}')"
                                class="text-stone-400 hover:text-red-600 transition cursor-pointer px-1.5 py-0.5 text-xs font-bold" title="Remove">
                            ✕
                        </button>
                    </div>
                `;"""

refined_edit_item = """                return `
                    <div class="flex items-center justify-between px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] text-xs text-[#202124] shadow-2xs hover:border-[#ECC9BA] transition">
                        <span class="font-medium text-[#202124]">${label}</span>
                        <button type="button" onclick="window.TempoRecoveryNote.handleRemoveItem('${it.id}')"
                                class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/30 p-1 rounded-lg text-xs transition cursor-pointer ml-2" title="Remove">
                            ✕
                        </button>
                    </div>
                `;"""

assert target_edit_item in content, "target_edit_item not found"
content = content.replace(target_edit_item, refined_edit_item, 1)

# Strict lone-LF
content = content.replace('\r\n', '\n')
assert '\r' not in content, "Carriage returns found"

with open('recoveryNote.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)

print("recoveryNote.js updated successfully with LF line endings")
