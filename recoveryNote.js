/**
 * TEMPO WELLBEING — RECOVERY MODE: RECOVERY NOTE (PHASE 3)
 * File: recoveryNote.js
 *
 * Architecture:
 * 1. Structured Recovery Note model (warning_sign, helper, reminder, support_person)
 * 2. Synchronous local storage persistence (tempo_recovery_note_${uid}) + additive Supabase sync
 * 3. Recovery Home Card renderer (shows preview when content exists, or subtle empty state)
 * 4. Detail View Modal (#modal-recovery-note-view)
 * 5. Direct Edit Modal (#modal-recovery-note-edit)
 */

(function () {
    'use strict';

    const ITEM_TYPES = {
        WARNING_SIGN: 'warning_sign',
        HELPER: 'helper',
        REMINDER: 'reminder',
        SUPPORT_PERSON: 'support_person'
    };

    const SECTION_TITLES = {
        warning_sign: 'When I start getting overwhelmed',
        helper: 'Things that seem to help',
        reminder: 'What I want to remember',
        support_person: 'People I can reach out to'
    };

    function isViLocale() {
        if (window.TempoI18n && typeof window.TempoI18n.getLanguage === 'function') {
            return window.TempoI18n.getLanguage() === 'vi';
        }
        try {
            const stored = localStorage.getItem('tempo_language') || localStorage.getItem('tempo_lang');
            if (stored === 'vi' || stored === 'en') return stored === 'vi';
        } catch (e) {}
        return false;
    }

    function t(path, params = {}, fallback = '') {
        if (typeof params === 'string') {
            fallback = params;
            params = {};
        }
        if (window.TempoI18n && typeof window.TempoI18n.t === 'function') {
            const val = window.TempoI18n.t(path, params, fallback);
            if (val && val !== path) return val;
        }
        return fallback || path;
    }

    function getNoticeModalTranslations() {
        const isVi = isViLocale();
        return {
            header: t('modes.recovery.noticeModalHeader', {}, t('modes.recovery.recoveryNote', {}, isVi ? 'LỜI NHẮN PHỤC HỒI' : 'RECOVERY NOTICE')),
            title: t('modes.recovery.noticeModalTitle', {}, isVi ? 'Lời nhắn dành cho tôi' : 'My Recovery Notice'),
            subtitle: t('modes.recovery.noticeModalSubtitle', {}, isVi ? 'Những điều bạn muốn nhắc nhở bản thân khi mọi thứ trở nên khó khăn.' : 'Things you wanted to remember when things feel heavy.'),
            editBtn: t('modes.recovery.noticeModalEditBtn', {}, isVi ? 'Chỉnh sửa lời nhắn' : 'Edit note'),
            closeBtn: t('common.close', {}, isVi ? 'Đóng' : 'Close')
        };
    }

    let isLangListenerAttached = false;
    function attachLanguageListener() {
        if (isLangListenerAttached) return;
        if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
            window.TempoI18n.onLanguageChange(() => {
                updateViewModalTexts();
            });
            isLangListenerAttached = true;
        }
    }

    // =========================================================================
    // STORAGE & PERSISTENCE
    // =========================================================================

    function getUserId() {
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') {
            const uid = window.TempoAuth.getCurrentUserId();
            if (uid) return uid;
        }
        return 'local_user';
    }

    function getStorageKey() {
        const uid = getUserId();
        return `tempo_recovery_note_${uid}`;
    }

    function loadNote() {
        try {
            const key = getStorageKey();
            const raw = localStorage.getItem(key);
            if (raw) return JSON.parse(raw);

            // Legacy fallback
            const legacy = localStorage.getItem('tempo_recovery_note');
            if (legacy) return JSON.parse(legacy);
        } catch (e) {
            console.warn("[RecoveryNote] Error loading note:", e);
        }
        return {
            id: 'note_' + Date.now(),
            user_id: getUserId(),
            items: [],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };
    }

    function saveNote(noteData) {
        try {
            noteData.updated_at = new Date().toISOString();
            const key = getStorageKey();
            localStorage.setItem(key, JSON.stringify(noteData));

            // Background Supabase sync if client available
            syncNoteToSupabase(noteData);

            // Refresh Recovery Home if active
            if (window.TempoMode && typeof window.TempoMode.getMode === 'function') {
                if (window.TempoMode.getMode() === 'recovery') {
                    window.TempoMode.renderRmodeHome();
                }
            }
        } catch (e) {
            console.warn("[RecoveryNote] Error saving note:", e);
        }
    }

    async function syncNoteToSupabase(note) {
        if (!window.TempoSupabase || typeof window.TempoSupabase.getClient !== 'function') return;
        const sb = window.TempoSupabase.getClient();
        if (!sb || !window.TempoAuth || !window.TempoAuth.getCurrentUserId()) return;

        try {
            const uid = window.TempoAuth.getCurrentUserId();
            // Upsert recovery note row
            await sb.from('recovery_notes').upsert([{
                id: note.id.startsWith('note_') ? undefined : note.id,
                user_id: uid,
                updated_at: note.updated_at
            }]);

            // Note items can also be synced if table exists
        } catch (e) {
            console.warn("[RecoveryNote] Supabase sync notice (local mirror active):", e);
        }
    }

    // =========================================================================
    // NOTE DATA API
    // =========================================================================

    function getNote() {
        return loadNote();
    }

    function getItems() {
        const note = loadNote();
        return note.items || [];
    }

    function hasNoteContent() {
        const items = getItems();
        return items.length > 0;
    }

    function setNoteItems(items) {
        const note = loadNote();
        note.items = items.map((it, idx) => ({
            id: it.id || ('item_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6)),
            type: it.type || ITEM_TYPES.REMINDER,
            text: it.text ? it.text.trim() : '',
            source: it.source || 'custom',
            source_ref: it.source_ref || null,
            metadata: it.metadata || {},
            order_index: it.order_index !== undefined ? it.order_index : idx,
            created_at: it.created_at || new Date().toISOString(),
            updated_at: new Date().toISOString()
        })).filter(it => it.text.length > 0);

        saveNote(note);
        return note;
    }

    function addItem(type, text, metadata = {}, source = 'custom') {
        if (!text || !text.trim()) return null;
        const note = loadNote();
        const newItem = {
            id: 'item_' + Date.now() + '_' + Math.random().toString(36).substr(2, 6),
            type: type || ITEM_TYPES.REMINDER,
            text: text.trim(),
            source: source,
            metadata: metadata,
            order_index: (note.items || []).length,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };
        note.items = [...(note.items || []), newItem];
        saveNote(note);
        return newItem;
    }

    function removeItem(id) {
        const note = loadNote();
        note.items = (note.items || []).filter(it => it.id !== id);
        saveNote(note);
        return note;
    }

    function updateItem(id, updates) {
        const note = loadNote();
        const idx = (note.items || []).findIndex(it => it.id === id);
        if (idx === -1) return null;

        const patch = typeof updates === 'string' ? { text: updates.trim() } : (updates || {});
        note.items[idx] = {
            ...note.items[idx],
            ...patch,
            updated_at: new Date().toISOString()
        };
        saveNote(note);
        return note.items[idx];
    }

    // =========================================================================
    // RECOVERY HOME CARD RENDERER
    // =========================================================================

    function renderHomeCard() {
        const items = getItems();
        const hasContent = items.length > 0;

        if (hasContent) {
            // Pick a preview item: preferably a reminder, or the first item
            const reminder = items.find(it => it.type === ITEM_TYPES.REMINDER);
            const previewText = reminder ? `"${reminder.text}"` : `"${items[0].text}"`;
            const count = items.length;

            return `
                <div class="recovery-card-note bg-white border border-[#EAE4DF] rounded-3xl p-5 sm:p-6 space-y-3.5 shadow-xs relative overflow-hidden" data-tempo-ui="recovery-note">
                    <div class="flex items-center justify-between">
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
                            <span>View Recovery Notice</span>
                            <span>→</span>
                        </button>
                        <button type="button" onclick="window.TempoRecoveryNote.openEditModal()"
                                class="text-xs font-semibold text-stone-400 hover:text-stone-700 transition cursor-pointer">
                            Edit
                        </button>
                    </div>
                </div>
            `;
        }

        // Empty state: subtle, gentle, unpunitive
        return `
            <div class="recovery-card-note bg-white border border-[#EAE4DF] rounded-3xl p-5 space-y-3 shadow-xs" data-tempo-ui="recovery-note">
                <div class="flex items-center space-x-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-stone-300 inline-block"></span>
                    <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#6F6B68]">
                        RECOVERY NOTE
                    </span>
                </div>
                <div class="space-y-1">
                    <h4 class="font-heading text-sm font-bold text-[#202124]">Keep what helps in one place</h4>
                    <p class="text-xs text-[#6F6B68] leading-relaxed">
                        You haven't added anything here yet. If you notice something you'd like your future self to remember when things feel heavy, you can keep it here.
                    </p>
                </div>
                <div class="pt-1">
                    <button type="button" onclick="window.TempoRecoveryNote.openEditModal()"
                            class="text-xs font-bold text-[#4F6851] hover:text-[#2E4630] transition cursor-pointer flex items-center space-x-1">
                        <span>+ Add something to your note</span>
                    </button>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // MODAL SHELLS & CONTROLLERS (VIEW & EDIT)
    // =========================================================================

    function updateViewModalTexts() {
        const trans = getNoticeModalTranslations();
        const headerEl = document.getElementById('modal-recovery-note-view-header');
        if (headerEl) headerEl.textContent = trans.header;

        const titleEl = document.getElementById('modal-recovery-note-view-title');
        if (titleEl) titleEl.textContent = trans.title;

        const subtitleEl = document.getElementById('modal-recovery-note-view-subtitle');
        if (subtitleEl) subtitleEl.textContent = trans.subtitle;

        const editBtn = document.getElementById('modal-recovery-note-view-edit-btn');
        if (editBtn) editBtn.textContent = trans.editBtn;

        const closeBtn = document.getElementById('modal-recovery-note-view-close-btn');
        if (closeBtn) closeBtn.textContent = trans.closeBtn;

        const closeX = document.getElementById('modal-recovery-note-view-close-x');
        if (closeX) closeX.title = trans.closeBtn;
    }

    function ensureModalsMounted() {
        attachLanguageListener();
        if (document.getElementById('tempo-recovery-note-modals')) {
            updateViewModalTexts();
            return;
        }

        const trans = getNoticeModalTranslations();
        const container = document.createElement('div');
        container.id = 'tempo-recovery-note-modals';
        container.innerHTML = `
            <!-- MODAL: VIEW RECOVERY NOTE -->
            <div id="modal-recovery-note-view" class="fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-4 hidden" role="dialog" aria-modal="true">
                <div class="tempo-card max-w-lg w-full p-6 sm:p-8 space-y-6 bg-[#FAF4F0] rounded-3xl shadow-2xl relative border border-[#ECC9BA] max-h-[90vh] overflow-y-auto recovery-note-scroll">
                    <button type="button" id="modal-recovery-note-view-close-x" onclick="window.TempoRecoveryNote.closeViewModal()" class="absolute top-5 right-5 text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/40 p-2 rounded-xl text-lg transition cursor-pointer" title="${trans.closeBtn}">✕</button>

                    <div class="space-y-1">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-[#8EA28F] inline-block"></span>
                            <span id="modal-recovery-note-view-header" class="text-[11px] font-extrabold uppercase tracking-wider text-[#4F6851]">${trans.header}</span>
                        </div>
                        <h3 id="modal-recovery-note-view-title" class="font-heading text-2xl font-extrabold text-[#202124]">${trans.title}</h3>
                        <p id="modal-recovery-note-view-subtitle" class="text-xs text-[#6F6B68]">${trans.subtitle}</p>
                    </div>

                    <div id="recovery-note-view-content" class="space-y-4"></div>

                    <div class="pt-4 border-t border-[#ECC9BA]/60 flex items-center justify-between">
                        <button type="button" id="modal-recovery-note-view-edit-btn" onclick="window.TempoRecoveryNote.openEditModal()"
                                class="btn-primary bg-[#8EA28F] hover:bg-[#7D937E] text-white px-5 py-2.5 rounded-xl text-xs sm:text-sm font-bold shadow-xs transition cursor-pointer">
                            ${trans.editBtn}
                        </button>
                        <button type="button" id="modal-recovery-note-view-close-btn" onclick="window.TempoRecoveryNote.closeViewModal()"
                                class="px-4 py-2.5 rounded-xl text-xs font-bold text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/20 transition cursor-pointer">
                            ${trans.closeBtn}
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
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#4F6851]">EDIT RECOVERY NOTICE</span>
                        </div>
                        <h3 class="font-heading text-2xl font-extrabold text-[#202124]">Update your notice</h3>
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
                            <span>View full notice</span>
                            <span>→</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(container);
    }

    // =========================================================================
    // VIEW CONTROLLER
    // =========================================================================

    function openViewModal() {
        ensureModalsMounted();
        updateViewModalTexts();
        closeEditModal();
        renderViewContent();

        const modal = document.getElementById('modal-recovery-note-view');
        if (modal) {
            modal.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
        }
    }

    function closeViewModal() {
        const modal = document.getElementById('modal-recovery-note-view');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }

    function renderViewContent() {
        const container = document.getElementById('recovery-note-view-content');
        if (!container) return;

        const items = getItems();
        if (items.length === 0) {
            container.innerHTML = `
                <div class="p-6 text-center rounded-2xl border border-dashed border-stone-200 space-y-2">
                    <p class="text-sm font-semibold text-[#202124]">Your note is empty right now.</p>
                    <p class="text-xs text-[#6F6B68]">You can add early warning signs, things that help, reminders, or support contacts anytime.</p>
                </div>
            `;
            return;
        }

        const sections = [
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
        });

        container.innerHTML = html;
    }

    // =========================================================================
    // EDIT CONTROLLER
    // =========================================================================

    function openEditModal() {
        ensureModalsMounted();
        closeViewModal();
        renderEditSections();

        const modal = document.getElementById('modal-recovery-note-edit');
        if (modal) {
            modal.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
        }
    }

    function closeEditModal() {
        const modal = document.getElementById('modal-recovery-note-edit');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    }

    function renderEditSections() {
        const items = getItems();
        const types = [ITEM_TYPES.WARNING_SIGN, ITEM_TYPES.HELPER, ITEM_TYPES.REMINDER, ITEM_TYPES.SUPPORT_PERSON];

        types.forEach(t => {
            const container = document.getElementById(`edit-section-${t}`);
            if (!container) return;

            const secItems = items.filter(it => it.type === t);
            if (secItems.length === 0) {
                container.innerHTML = `<p class="text-[11px] text-stone-400 italic">None added yet.</p>`;
                return;
            }

            container.innerHTML = secItems.map(it => {
                const label = (t === ITEM_TYPES.SUPPORT_PERSON && it.metadata?.relationship)
                    ? `${escapeHTML(it.text)} <span class="text-stone-400 text-[11px]">(${escapeHTML(it.metadata.relationship)})</span>`
                    : escapeHTML(it.text);

                return `
                    <div class="flex items-center justify-between px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] text-xs text-[#202124] shadow-2xs hover:border-[#ECC9BA] transition">
                        <span class="font-medium text-[#202124]">${label}</span>
                        <button type="button" onclick="window.TempoRecoveryNote.handleRemoveItem('${it.id}')"
                                class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/30 p-1 rounded-lg text-xs transition cursor-pointer ml-2" title="Remove">
                            ✕
                        </button>
                    </div>
                `;
            }).join('');
        });
    }

    function handleAddFromInput(type) {
        const input = document.getElementById(`input-add-${type}`);
        if (!input || !input.value.trim()) return;

        addItem(type, input.value.trim(), {}, 'custom');
        input.value = '';
        renderEditSections();
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast("Added to Recovery Note.");
        }
    }

    function handleAddPerson() {
        const nameInput = document.getElementById('input-add-person-name');
        const relInput = document.getElementById('input-add-person-rel');
        if (!nameInput || !nameInput.value.trim()) return;

        const name = nameInput.value.trim();
        const rel = relInput ? relInput.value.trim() : '';

        addItem(ITEM_TYPES.SUPPORT_PERSON, name, { relationship: rel }, 'custom');
        nameInput.value = '';
        if (relInput) relInput.value = '';

        renderEditSections();
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast("Support person added.");
        }
    }

    function handleRemoveItem(id) {
        removeItem(id);
        renderEditSections();
    }

    function escapeHTML(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function init() {
        ensureModalsMounted();
        attachLanguageListener();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    window.TempoRecoveryNote = {
        init,
        ITEM_TYPES,
        getNote,
        getItems,
        hasNoteContent,
        setNoteItems,
        addItem,
        removeItem,
        updateItem,
        renderHomeCard,
        openViewModal,
        closeViewModal,
        openEditModal,
        closeEditModal,
        updateViewModalTexts,
        handleAddFromInput,
        handleAddPerson,
        handleRemoveItem
    };

})();
