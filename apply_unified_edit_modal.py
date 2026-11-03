import sys

# 1. Update selfCheckWorkspace.js if not already updated
with open('selfCheckWorkspace.js', 'r', encoding='utf-8') as f:
    workspace_code = f.read()

old_open_adjust = '''    function openAdjustTracker(trackerId) {
        ensureAdjustModalMounted();
        let tracker = null;
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerById === 'function') {
            tracker = window.TempoRecoverySelfCheck.getTrackerById(trackerId);
        }
        if (!tracker && window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function') {
            const active = window.TempoRecoverySelfCheck.getActiveTrackers();
            tracker = active.find(t => t.id === trackerId);
        }
        if (!tracker) return;'''

new_open_adjust = '''    function openAdjustTracker(trackerIdOrObj) {
        ensureAdjustModalMounted();
        let tracker = null;
        if (typeof trackerIdOrObj === 'object' && trackerIdOrObj !== null) {
            tracker = trackerIdOrObj;
        } else {
            const trackerId = trackerIdOrObj;
            if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerById === 'function') {
                tracker = window.TempoRecoverySelfCheck.getTrackerById(trackerId);
            }
            if (!tracker && window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function') {
                const active = window.TempoRecoverySelfCheck.getActiveTrackers();
                tracker = active.find(t => t.id === trackerId);
            }
        }
        if (!tracker) return;'''

if old_open_adjust in workspace_code:
    workspace_code = workspace_code.replace(old_open_adjust, new_open_adjust, 1)

old_modal_title = '<span class="text-xs sm:text-sm font-bold text-[#3B5441] tracking-tight block">${isVi ? \'Mục tracking của bạn\' : \'Your Tracking Item\'}</span>'
new_modal_title = '<span class="text-xs sm:text-sm font-bold text-[#3B5441] tracking-tight block">${draft.mode === \'create\' ? (isVi ? \'Mục tracking của bạn\' : \'Your Tracking Item\') : (isVi ? \'Chỉnh sửa mục tracking\' : \'Edit Tracking Item\')}</span>'

if old_modal_title in workspace_code:
    workspace_code = workspace_code.replace(old_modal_title, new_modal_title, 1)

old_linked_notes = '''            alertDays: alertCfg.days || 4,
            alertTargetOption: alertCfg.target_option || defaultOptions[0] || 'Yes','''

new_linked_notes = '''            alertDays: alertCfg.days || 4,
            alertTargetOption: alertCfg.target_option || defaultOptions[0] || 'Yes',
            linkedNoteItemIds: Array.isArray(tracker.linked_note_item_ids) ? [...tracker.linked_note_item_ids] : [],'''

if old_linked_notes in workspace_code:
    workspace_code = workspace_code.replace(old_linked_notes, new_linked_notes, 1)

old_tracker_payload = '''            scale_range: adjustDraftState.scaleRange,
            quantity_unit: adjustDraftState.quantityUnit,
            alert_enabled: adjustDraftState.alertEnabled,
            alert_config: alertConfig
        };'''

new_tracker_payload = '''            scale_range: adjustDraftState.scaleRange,
            quantity_unit: adjustDraftState.quantityUnit,
            alert_enabled: adjustDraftState.alertEnabled,
            alert_config: alertConfig,
            linked_note_item_ids: adjustDraftState.linkedNoteItemIds || []
        };'''

if old_tracker_payload in workspace_code:
    workspace_code = workspace_code.replace(old_tracker_payload, new_tracker_payload, 1)

old_save_else = '''            } else {
                const trackerId = adjustDraftState.trackerId;
                if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.updateTracker === 'function') {
                    window.TempoRecoverySelfCheck.updateTracker(trackerId, trackerPayload);
                }

                closeAdjustModal();
                render();

                if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.onTrackerSaved === 'function') {
                    const updatedTrk = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerById === 'function')
                        ? window.TempoRecoverySelfCheck.getTrackerById(trackerId)
                        : null;
                    if (updatedTrk) window.TempoRecoverySetup.onTrackerSaved(updatedTrk);
                }'''

new_save_else = '''            } else {
                const trackerId = adjustDraftState.trackerId;
                let updatedTrk = null;
                if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.updateTracker === 'function') {
                    try {
                        updatedTrk = window.TempoRecoverySelfCheck.updateTracker(trackerId, trackerPayload);
                    } catch (e) {
                        console.warn('[SelfCheckWorkspace] updateTracker threw:', e);
                    }
                }

                closeAdjustModal();
                render();

                if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.onTrackerSaved === 'function') {
                    if (!updatedTrk && window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerById === 'function') {
                        updatedTrk = window.TempoRecoverySelfCheck.getTrackerById(trackerId);
                    }
                    if (updatedTrk) {
                        window.TempoRecoverySetup.onTrackerSaved(updatedTrk);
                    } else {
                        window.TempoRecoverySetup.onTrackerSaved({ id: trackerId, ...trackerPayload });
                    }
                }'''

if old_save_else in workspace_code:
    workspace_code = workspace_code.replace(old_save_else, new_save_else, 1)

workspace_code = workspace_code.replace('\r\n', '\n')
with open('selfCheckWorkspace.js', 'wb') as f:
    f.write(workspace_code.encode('utf-8'))

print('selfCheckWorkspace.js checked and updated!')

# 2. Update recoverySetup.js
with open('recoverySetup.js', 'r', encoding='utf-8') as f:
    setup_code = f.read()

# Replace openEditTrackerInAdjustment and simplify handlers
old_setup_handlers = '''    function openEditTrackerInAdjustment(idx, isNew = false) {
        adjustmentDraft.editingTrackerIndex = idx;
        adjustmentDraft.editingIsNew = isNew;
        renderStageAdjustTrackers(document.getElementById('recovery-setup-stage-container'));
    }

    function closeTrackerEditInAdjustment() {
        adjustmentDraft.editingTrackerIndex = null;
        adjustmentDraft.editingIsNew = false;
        renderStageAdjustTrackers(document.getElementById('recovery-setup-stage-container'));
    }

    function saveTrackerEditInAdjustment(idx, isNew) {
        const nameInput = document.getElementById('adjust-edit-name');
        const methodSelect = document.getElementById('adjust-edit-method');
        const unitInput = document.getElementById('adjust-edit-unit');
        const optionsInput = document.getElementById('adjust-edit-options');
        const scaleRangeSelect = document.getElementById('adjust-edit-scale-range');
        const alertToggle = document.getElementById('adjust-edit-alert-toggle');

        if (!nameInput || !nameInput.value.trim()) {
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Tracking name cannot be empty.");
            }
            return;
        }

        const target = isNew ? adjustmentDraft.newTrackers[idx] : adjustmentDraft.trackers[idx];
        if (!target) return;

        target.name = nameInput.value.trim();
        const newMethod = methodSelect ? methodSelect.value : target.check_method;
        if (newMethod !== target.check_method) {
            target.check_method = newMethod;
            target.wasEdited = true;
        }
        if (unitInput) {
            target.quantity_unit = unitInput.value.trim();
        }
        if (optionsInput && (newMethod === 'options' || newMethod === 'yes_no')) {
            const rawOpts = optionsInput.value.split(',').map(s => s.trim()).filter(Boolean);
            if (rawOpts.length > 0) target.options = rawOpts;
        }
        if (scaleRangeSelect && newMethod === 'scale') {
            target.scale_range = scaleRangeSelect.value;
            target.scale_max = scaleRangeSelect.value === '1-10' ? 10 : 5;
        }
        if (alertToggle) {
            target.alert_enabled = alertToggle.checked;
        }

        target.wasEdited = true;
        closeTrackerEditInAdjustment();
    }'''

new_setup_handlers = '''    function openEditTrackerInAdjustment(idx, isNew = false) {
        const target = isNew ? adjustmentDraft.newTrackers[idx] : adjustmentDraft.trackers[idx];
        if (!target) return;
        if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.openAdjustTracker === 'function') {
            window.TempoSelfCheckWorkspace.openAdjustTracker(target.id ? target.id : target);
        } else if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openTrackerModal === 'function') {
            window.TempoRecoverySelfCheck.openTrackerModal(target.id ? target.id : target);
        }
    }

    function closeTrackerEditInAdjustment() {
        if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.closeAdjustModal === 'function') {
            window.TempoSelfCheckWorkspace.closeAdjustModal();
        }
    }

    function saveTrackerEditInAdjustment(idx, isNew) {
        if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.saveAdjustTracker === 'function') {
            window.TempoSelfCheckWorkspace.saveAdjustTracker();
        }
    }'''

assert old_setup_handlers in setup_code, 'old_setup_handlers not found'
setup_code = setup_code.replace(old_setup_handlers, new_setup_handlers, 1)

# In renderStageAdjustTrackers, remove editingIdx, editingIsNew, editingTracker
old_stage_editing_vars = '''    function renderStageAdjustTrackers(container) {
        const isVi = isViLocale();
        updateRecoveryCardTheme(true);

        const editingIdx = adjustmentDraft.editingTrackerIndex;
        const editingIsNew = adjustmentDraft.editingIsNew;
        const editingTracker = editingIdx !== null
            ? (editingIsNew ? adjustmentDraft.newTrackers[editingIdx] : adjustmentDraft.trackers[editingIdx])
            : null;'''

new_stage_editing_vars = '''    function renderStageAdjustTrackers(container) {
        const isVi = isViLocale();
        updateRecoveryCardTheme(true);'''

assert old_stage_editing_vars in setup_code, 'old_stage_editing_vars not found'
setup_code = setup_code.replace(old_stage_editing_vars, new_stage_editing_vars, 1)

# Remove the duplicate edit modal HTML block
start_marker = "        // Modal for editing tracker\n        let editModalHTML = '';\n        if (editingTracker) {"
end_marker = "        container.innerHTML = `\n            <div class=\"space-y-5\" data-tempo-ui=\"rmode-adjust-trackers\">"

start_idx = setup_code.index(start_marker)
end_idx = setup_code.index(end_marker)

setup_code = setup_code[:start_idx] + setup_code[end_idx:]

# Remove ${editModalHTML} at the end of renderStageAdjustTrackers
old_end_modal = '''                ${editModalHTML}
            </div>
        `;
    }'''

new_end_modal = '''            </div>
        `;
    }'''

assert old_end_modal in setup_code, 'old_end_modal not found'
setup_code = setup_code.replace(old_end_modal, new_end_modal, 1)

setup_code = setup_code.replace('\r\n', '\n')
with open('recoverySetup.js', 'wb') as f:
    f.write(setup_code.encode('utf-8'))

print('recoverySetup.js successfully updated!')
