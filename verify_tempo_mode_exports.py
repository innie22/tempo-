import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('mode.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Find the return block of window.TempoMode
return_idx = text.rfind('return {')
export_block = text[return_idx:]

handlers_to_check = [
    'closeRmodeTaskDetailModal',
    'dismissRecoveryIntro',
    'handleAddTrackingDirectClick',
    'handleRecoveryIntroSetupClick',
    'openChangeModeModal',
    'openHelpSelectionModal',
    'openRmodeTaskDetailModal',
    'openStrack',
    'saveRmodeDetailDeadlineEdit',
    'saveRmodeDetailTitleEdit',
    'setRmodeDetailTaskLabel',
    'skipRmodeCurrentSelfCheck',
    'submitRmodeQuantityValue',
    'submitRmodeSelfCheckValue',
    'toggleModeDropdown',
    'toggleRmodeDetailAddSubtask',
    'toggleRmodeDetailDeadlineEdit',
    'toggleRmodeDetailLabelMenu',
    'toggleRmodeDetailTitleEdit',
    'resetRmodeSkippedTrackers',
    'handleSelfCheckAction',
    'handleRmodeTaskFocus',
    'handleRmodeTaskReschedule',
    'promptClearRmodeTask',
    'toggleRmodeDetailTaskComplete',
    'deleteRmodeDetailNote',
    'saveRmodeDetailNote',
    'toggleRmodeDetailNoteEdit',
    'removeRmodeDetailSubtask',
    'saveRmodeDetailSubtaskTitle',
    'toggleRmodeDetailSubtask',
    'toggleRmodeDetailSubtaskEdit'
]

print("Checking export of Rmode handlers in TempoMode:")
missing_exports = []
missing_defs = []
for h in handlers_to_check:
    has_def = f'function {h}(' in text or f'{h} =' in text
    has_export = f'{h},' in export_block or f'{h}:' in export_block or f'{h}\n' in export_block
    if not has_def:
        missing_defs.append(h)
    if not has_export:
        missing_exports.append(h)
    print(f"  {h:32s}: Defined={has_def} | Exported={has_export}")

print("\nMissing definitions:", missing_defs)
print("Missing exports:", missing_exports)
