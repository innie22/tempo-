with open('urmodeFlow.js', 'r', encoding='utf-8', newline='') as f:
    content = f.read()

assert '\r' not in content, "urmodeFlow.js must be strictly LF"

# 1. Update empty state message in renderBreakTaskPopup
target_empty = """                ${subtasks.length === 0 ? `
                    <div class="p-3 bg-stone-50 rounded-xl text-xs text-stone-500 italic text-center">
                        No action steps added yet. Add your first step below or click ✨ AI Help.
                    </div>
                ` : subtasks.map((s, idx) => `"""

replace_empty = """                ${subtasks.length === 0 ? `
                    <div class="p-3 bg-stone-50 rounded-xl text-xs text-stone-500 italic text-center">
                        ${window.t ? window.t('workspace.breakdownEmptyState', {}, (isViLocale() ? 'Chưa có bước thực hiện nào. Hãy thêm bước đầu tiên bên dưới hoặc chọn ✨ AI hỗ trợ.' : 'No action steps added yet. Add your first step below or click ✨ AI Help.')) : (isViLocale() ? 'Chưa có bước thực hiện nào. Hãy thêm bước đầu tiên bên dưới hoặc chọn ✨ AI hỗ trợ.' : 'No action steps added yet. Add your first step below or click ✨ AI Help.')}
                    </div>
                ` : subtasks.map((s, idx) => `"""

assert target_empty in content, "target_empty not found in urmodeFlow.js"
content = content.replace(target_empty, replace_empty, 1)

# 2. Update onLanguageChange
target_lang = """            } else if (activeModalView === 'select_another_task') {
                showTaskSelectionPopup();
            }"""

replace_lang = """            } else if (activeModalView === 'select_another_task') {
                showTaskSelectionPopup();
            } else if (activeModalView === 'breakdown') {
                if (currentBreakdownTaskId) {
                    renderBreakTaskPopup(currentBreakdownTaskId);
                }
            }"""

assert target_lang in content, "target_lang not found in urmodeFlow.js"
content = content.replace(target_lang, replace_lang, 1)

assert '\r' not in content, "urmodeFlow.js must retain strictly LF line endings"

with open('urmodeFlow.js', 'w', encoding='utf-8', newline='') as f:
    f.write(content)

print("urmodeFlow.js successfully patched for breakdown empty state!")
