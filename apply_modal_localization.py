import re

with open('selfCheckWorkspace.js', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update initialTypeName in openAddTracking
old_init = '''        let initialName = '';
        let initialTypeId = 'stress_sign';
        let initialTypeName = 'Sign of stress';
        let initialTypeColor = '#C34D2E';
        let initialMethod = 'percentage';
        let initialUnit = 'minutes';
        let initialOptions = ['Yes', 'No'];

        if (prefill) {
            if (typeof prefill === 'string') {
                initialName = prefill;
            } else if (typeof prefill === 'object') {
                initialName = prefill.name || '';
                if (prefill.category === 'supportive' || prefill.type_id === 'supportive') {
                    initialTypeId = 'supportive';
                    initialTypeName = 'Supportive';
                    initialTypeColor = '#859B8B';
                }'''

new_init = '''        let initialName = '';
        let initialTypeId = 'stress_sign';
        let initialTypeName = isViLocale() ? 'Dấu hiệu căng thẳng' : 'Sign of stress';
        let initialTypeColor = '#C34D2E';
        let initialMethod = 'percentage';
        let initialUnit = 'minutes';
        let initialOptions = ['Yes', 'No'];

        if (prefill) {
            if (typeof prefill === 'string') {
                initialName = prefill;
            } else if (typeof prefill === 'object') {
                initialName = prefill.name || '';
                if (prefill.category === 'supportive' || prefill.type_id === 'supportive') {
                    initialTypeId = 'supportive';
                    initialTypeName = isViLocale() ? 'Yếu tố hỗ trợ' : 'Supportive';
                    initialTypeColor = '#859B8B';
                }'''

assert old_init in text, 'old_init not found'
text = text.replace(old_init, new_init, 1)

# 2. Update openAdjustTracker default typeName
old_adj_type = '''typeName: tracker.type_label || (tracker.category === 'supportive' ? 'Supportive' : 'Sign of stress'),'''
new_adj_type = '''typeName: tracker.type_label || (tracker.category === 'supportive' ? (isViLocale() ? 'Yếu tố hỗ trợ' : 'Supportive') : (isViLocale() ? 'Dấu hiệu căng thẳng' : 'Sign of stress')),'''
assert old_adj_type in text, 'old_adj_type not found'
text = text.replace(old_adj_type, new_adj_type, 1)

# 3. Update readCurrentDraftInputs
old_read = '''    function readCurrentDraftInputs() {
        if (!adjustDraftState) return;
        const nameInp = document.getElementById('adjust-tracker-name-input');
        if (nameInp && nameInp.value !== undefined) {
            adjustDraftState.trackerName = nameInp.value;
        }
        readCurrentAlertInputs();
    }'''

new_read = '''    function readCurrentDraftInputs() {
        if (!adjustDraftState) return;
        const nameInp = document.getElementById('adjust-tracker-name-input');
        if (nameInp && nameInp.value !== undefined) {
            adjustDraftState.trackerName = nameInp.value;
        }
        const newTypeInp = document.getElementById('adjust-new-type-input');
        if (newTypeInp && newTypeInp.value !== undefined) {
            adjustDraftState.newTypeName = newTypeInp.value;
        }
        readCurrentAlertInputs();
    }'''

assert old_read in text, 'old_read not found'
text = text.replace(old_read, new_read, 1)

# 4. Update saveAdjustTracker name validation and saving state
old_save_val = '''        // Validate: Require a valid, non-empty tracking name before saving
        if (!cleanName) {
            adjustDraftState.nameError = 'Please enter a tracking name.';
            renderAdjustModal();
            const inp = document.getElementById('adjust-tracker-name-input');
            if (inp) inp.focus();
            return;
        }

        adjustDraftState.trackerName = cleanName;
        adjustDraftState.nameError = '';
        adjustDraftState.isSaving = true;

        const saveBtn = document.getElementById('adjust-save-submit-btn');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.classList.add('opacity-50', 'cursor-not-allowed');
            saveBtn.innerHTML = `
                <span class="inline-flex items-center space-x-1.5">
                    <svg class="animate-spin -ml-0.5 mr-1.5 h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                    </svg>
                    <span>${adjustDraftState.mode === 'create' ? 'Adding tracking...' : 'Saving...'}</span>
                </span>
            `;
        }'''

new_save_val = '''        // Validate: Require a valid, non-empty tracking name before saving
        if (!cleanName) {
            const isVi = isViLocale();
            adjustDraftState.nameError = isVi ? 'Vui lòng nhập tên mục tracking.' : 'Please enter a tracking name.';
            renderAdjustModal();
            const inp = document.getElementById('adjust-tracker-name-input');
            if (inp) inp.focus();
            return;
        }

        adjustDraftState.trackerName = cleanName;
        adjustDraftState.nameError = '';
        adjustDraftState.isSaving = true;

        const isVi = isViLocale();
        const saveBtn = document.getElementById('adjust-save-submit-btn');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.classList.add('opacity-50', 'cursor-not-allowed');
            saveBtn.innerHTML = `
                <span class="inline-flex items-center space-x-1.5">
                    <svg class="animate-spin -ml-0.5 mr-1.5 h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                    </svg>
                    <span>${adjustDraftState.mode === 'create' ? (isVi ? 'Đang thêm...' : 'Adding tracking...') : (isVi ? 'Đang lưu...' : 'Saving...')}</span>
                </span>
            `;
        }'''

assert old_save_val in text, 'old_save_val not found'
text = text.replace(old_save_val, new_save_val, 1)

# 5. Update saveAdjustTracker catch block
old_save_catch = '''        } catch (err) {
            console.error("Error saving tracking configuration:", err);
            adjustDraftState.isSaving = false;
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                saveBtn.textContent = adjustDraftState.mode === 'create' ? 'Add tracking' : 'Save changes';
            }
            adjustDraftState.nameError = err && err.message ? err.message : 'Failed to save tracker. Please try again.';
            renderAdjustModal();
        }'''

new_save_catch = '''        } catch (err) {
            console.error("Error saving tracking configuration:", err);
            adjustDraftState.isSaving = false;
            const isVi = isViLocale();
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                saveBtn.textContent = adjustDraftState.mode === 'create' ? (isVi ? 'Thêm tracking' : 'Add tracking') : (isVi ? 'Lưu thay đổi' : 'Save changes');
            }
            adjustDraftState.nameError = err && err.message ? err.message : (isVi ? 'Không thể lưu mục tracking. Vui lòng thử lại.' : 'Failed to save tracker. Please try again.');
            renderAdjustModal();
        }'''

assert old_save_catch in text, 'old_save_catch not found'
text = text.replace(old_save_catch, new_save_catch, 1)

# 6. Transform renderAdjustModal
start_marker = '    function renderAdjustModal() {'
end_marker = '    function promptClearAll() {'
start_idx = text.index(start_marker)
end_idx = text.index(end_marker)
modal_fn = text[start_idx:end_idx]

# Add isVi and typeName sync
modal_fn = modal_fn.replace(
'''        const draft = adjustDraftState;''',
'''        const draft = adjustDraftState;
        const isVi = isViLocale();

        // Sync standard type name with active locale
        if (draft.typeId === 'stress_sign') {
            draft.typeName = isVi ? 'Dấu hiệu căng thẳng' : 'Sign of stress';
        } else if (draft.typeId === 'supportive') {
            draft.typeName = isVi ? 'Yếu tố hỗ trợ' : 'Supportive';
        }'''
)

# New type form
modal_fn = modal_fn.replace(
    '<span class="text-[11px] font-bold text-[#5B5550] block">Create new type</span>',
    '<span class="text-[11px] font-bold text-[#5B5550] block">${isVi ? \'Tạo loại mới\' : \'Create new type\'}</span>'
)
modal_fn = modal_fn.replace(
    'placeholder="Type label (e.g. Physical, Habit)..."',
    'placeholder="${isVi ? \'Tên loại (vd: Thể chất, Thói quen)...\' : \'Type label (e.g. Physical, Habit)...\'}"'
)
modal_fn = modal_fn.replace(
    '<span class="text-[10px] text-stone-500 font-semibold block">Choose color:</span>',
    '<span class="text-[10px] text-stone-500 font-semibold block">${isVi ? \'Chọn màu:\' : \'Choose color:\'}</span>'
)
modal_fn = modal_fn.replace(
    'Save type\n                    </button>',
    "${isVi ? 'Lưu loại' : 'Save type'}\n                    </button>"
)

# Cancel in new type form:
# <button type="button" onclick="window.TempoSelfCheckWorkspace.toggleCreateNewTypeForm(false)" \n class="px-2 py-1 text-xs text-stone-500 hover:text-stone-800 transition">\n Cancel\n </button>
modal_fn = modal_fn.replace(
    'class="px-2 py-1 text-xs text-stone-500 hover:text-stone-800 transition">\n                        Cancel\n                    </button>',
    'class="px-2 py-1 text-xs text-stone-500 hover:text-stone-800 transition">\n                        ${isVi ? \'Hủy\' : \'Cancel\'}\n                    </button>'
)

# Options method sub-config
modal_fn = modal_fn.replace(
    '<span class="text-[11px] font-bold text-[#5B5550]">Configured options:</span>',
    '<span class="text-[11px] font-bold text-[#5B5550]">${isVi ? \'Các lựa chọn thiết lập:\' : \'Configured options:\'}</span>'
)
modal_fn = modal_fn.replace(
    '<span class="text-[10px] text-stone-400">Click ✕ to remove</span>',
    '<span class="text-[10px] text-stone-400">${isVi ? \'Nhấn ✕ để xóa\' : \'Click ✕ to remove\'}</span>'
)
modal_fn = modal_fn.replace(
    'placeholder="Add custom option (e.g. Maybe)..."',
    'placeholder="${isVi ? \'Thêm lựa chọn (vd: Có thể)...\' : \'Add custom option (e.g. Maybe)...\'}"'
)
modal_fn = modal_fn.replace(
    'class="px-3 py-1 rounded-lg text-xs font-bold bg-[#859B8B] text-white hover:bg-[#748A7A] transition">\n                            Add\n                        </button>',
    'class="px-3 py-1 rounded-lg text-xs font-bold bg-[#859B8B] text-white hover:bg-[#748A7A] transition">\n                            ${isVi ? \'Thêm\' : \'Add\'}\n                        </button>'
)

# Scale method sub-config
modal_fn = modal_fn.replace(
    '<span class="text-[11px] font-bold text-[#5B5550]">Scale range:</span>',
    '<span class="text-[11px] font-bold text-[#5B5550]">${isVi ? \'Khoảng thang đo:\' : \'Scale range:\'}</span>'
)
modal_fn = modal_fn.replace(
    '>\n                        1 to 5\n                    </button>',
    ">\n                        1 ${isVi ? 'đến' : 'to'} 5\n                    </button>"
)
modal_fn = modal_fn.replace(
    '>\n                        1 to 10\n                    </button>',
    ">\n                        1 ${isVi ? 'đến' : 'to'} 10\n                    </button>"
)

# Quantity method sub-config
modal_fn = modal_fn.replace(
    '<span class="text-[11px] font-bold text-[#5B5550]">Measurement unit:</span>',
    '<span class="text-[11px] font-bold text-[#5B5550]">${isVi ? \'Đơn vị đo lường:\' : \'Measurement unit:\'}</span>'
)
modal_fn = modal_fn.replace(
    'placeholder="Custom unit (e.g. km, laps)..."',
    'placeholder="${isVi ? \'Đơn vị tùy chỉnh (vd: km)...\' : \'Custom unit (e.g. km, laps)...\'}"'
)

# Quantity unit buttons map
old_qty_btn = '''                        ${['minutes', 'steps', 'times', 'hours', 'glasses', 'pages'].map(u => `
                            <button type="button" onclick="window.TempoSelfCheckWorkspace.setAdjustQuantityUnit('${u}')"
                                    class="px-2.5 py-0.5 rounded-lg text-xs font-semibold transition ${draft.quantityUnit === u ? 'bg-[#859B8B] text-white shadow-2xs' : 'bg-white text-stone-700 border border-stone-300 hover:bg-stone-50'}">
                                ${u}
                            </button>
                        `).join('')}'''

new_qty_btn = '''                        ${(() => {
                            const unitLabelMapVi = { 'minutes': 'phút', 'steps': 'bước', 'times': 'lần', 'hours': 'giờ', 'glasses': 'ly', 'pages': 'trang' };
                            return ['minutes', 'steps', 'times', 'hours', 'glasses', 'pages'].map(u => `
                                <button type="button" onclick="window.TempoSelfCheckWorkspace.setAdjustQuantityUnit('${u}')"
                                        class="px-2.5 py-0.5 rounded-lg text-xs font-semibold transition ${draft.quantityUnit === u ? 'bg-[#859B8B] text-white shadow-2xs' : 'bg-white text-stone-700 border border-stone-300 hover:bg-stone-50'}">
                                    ${isVi ? (unitLabelMapVi[u] || u) : u}
                                </button>
                            `).join('');
                        })()}'''

assert old_qty_btn in modal_fn, 'old_qty_btn not found'
modal_fn = modal_fn.replace(old_qty_btn, new_qty_btn, 1)

# Alert type selector
modal_fn = modal_fn.replace(
    '<span class="text-xs font-semibold text-[#5B5550]">Alert type:</span>',
    '<span class="text-xs font-semibold text-[#5B5550]">${isVi ? \'Loại cảnh báo\' : \'Alert type\'}:</span>'
)
modal_fn = modal_fn.replace(
    'Sign of Stress</option>',
    "${isVi ? 'Dấu hiệu căng thẳng' : 'Sign of Stress'}</option>"
)
modal_fn = modal_fn.replace(
    'Supportive Reminder</option>',
    "${isVi ? 'Yếu tố hỗ trợ' : 'Supportive Reminder'}</option>"
)

# Alert operators & inline text
modal_fn = modal_fn.replace(
    '>More than</option>',
    ">${isVi ? 'Lớn hơn' : 'More than'}</option>"
)
modal_fn = modal_fn.replace(
    '>Less than</option>',
    ">${isVi ? 'Nhỏ hơn' : 'Less than'}</option>"
)
modal_fn = modal_fn.replace(
    ">Didn't do</option>",
    ">${isVi ? 'Không thực hiện' : \"Didn't do\"}</option>"
)

# Inline text
modal_fn = modal_fn.replace(
    '<span>% for</span>',
    '<span>${isVi ? \'% trong\' : \'% for\'}</span>'
)
modal_fn = modal_fn.replace(
    '<span>days in a row.</span>',
    '<span>${isVi ? \'ngày liên tiếp\' : \'days in a row\'}</span>'
)
modal_fn = modal_fn.replace(
    '<span>Alert me when I select</span>',
    '<span>${isVi ? \'Cảnh báo khi tôi chọn\' : \'Alert me when I select\'}</span>'
)
modal_fn = modal_fn.replace(
    '<span>for</span>',
    '<span>${isVi ? \'trong\' : \'for\'}</span>'
)
modal_fn = modal_fn.replace(
    '<span>on a scale of ${draft.scaleRange} for</span>',
    '<span>${isVi ? `trên thang đo ${draft.scaleRange} trong` : `on a scale of ${draft.scaleRange} for`}</span>'
)

# Modal card header & inputs
modal_fn = modal_fn.replace(
    'title="Close">',
    'title="${isVi ? \'Đóng\' : \'Close\'}">'
)
modal_fn = modal_fn.replace(
    '<span class="text-xs sm:text-sm font-bold text-[#3B5441] tracking-tight block">Your Tracking Item</span>',
    '<span class="text-xs sm:text-sm font-bold text-[#3B5441] tracking-tight block">${isVi ? \'Mục tracking của bạn\' : \'Your Tracking Item\'}</span>'
)
modal_fn = modal_fn.replace(
    'placeholder="Enter tracking name"',
    'placeholder="${isVi ? \'Nhập tên mục tracking\' : \'Enter tracking name\'}"'
)

# Type section
modal_fn = modal_fn.replace(
    '<span class="text-xs sm:text-sm font-bold text-[#5B5550] block">Type:</span>',
    '<span class="text-xs sm:text-sm font-bold text-[#5B5550] block">${isVi ? \'Loại\' : \'Type\'}:</span>'
)
modal_fn = modal_fn.replace(
    "onclick=\"window.TempoSelfCheckWorkspace.setAdjustType('stress_sign', 'Sign of stress', '#C34D2E')\"\n                            class=\"px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer shadow-2xs\"\n                            style=\"${draft.typeId === 'stress_sign' ? 'background-color: #C34D2E; color: #ffffff; box-shadow: 0 0 0 2px rgba(195,77,46,0.35);' : 'background-color: rgba(195,77,46,0.78); color: #ffffff;'}\">\n                        Sign of stress",
    "onclick=\"window.TempoSelfCheckWorkspace.setAdjustType('stress_sign', '${isVi ? 'Dấu hiệu căng thẳng' : 'Sign of stress'}', '#C34D2E')\"\n                            class=\"px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer shadow-2xs\"\n                            style=\"${draft.typeId === 'stress_sign' ? 'background-color: #C34D2E; color: #ffffff; box-shadow: 0 0 0 2px rgba(195,77,46,0.35);' : 'background-color: rgba(195,77,46,0.78); color: #ffffff;'}\">\n                        ${isVi ? 'Dấu hiệu căng thẳng' : 'Sign of stress'}"
)
modal_fn = modal_fn.replace(
    "onclick=\"window.TempoSelfCheckWorkspace.setAdjustType('supportive', 'Supportive', '#859B8B')\"\n                            class=\"px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer shadow-2xs\"\n                            style=\"${draft.typeId === 'supportive' ? 'background-color: #859B8B; color: #ffffff; box-shadow: 0 0 0 2px rgba(133,155,139,0.35);' : 'background-color: rgba(133,155,139,0.78); color: #ffffff;'}\">\n                        Supportive",
    "onclick=\"window.TempoSelfCheckWorkspace.setAdjustType('supportive', '${isVi ? 'Yếu tố hỗ trợ' : 'Supportive'}', '#859B8B')\"\n                            class=\"px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer shadow-2xs\"\n                            style=\"${draft.typeId === 'supportive' ? 'background-color: #859B8B; color: #ffffff; box-shadow: 0 0 0 2px rgba(133,155,139,0.35);' : 'background-color: rgba(133,155,139,0.78); color: #ffffff;'}\">\n                        ${isVi ? 'Yếu tố hỗ trợ' : 'Supportive'}"
)
modal_fn = modal_fn.replace(
    'class="text-xs font-bold text-[#D48366] hover:underline transition cursor-pointer pt-0.5 block">\n                    Create new type\n                </button>',
    'class="text-xs font-bold text-[#D48366] hover:underline transition cursor-pointer pt-0.5 block">\n                    ${isVi ? \'Tạo loại mới\' : \'Create new type\'}\n                </button>'
)

# Tracking method section
modal_fn = modal_fn.replace(
    '<span class="text-xs sm:text-sm font-bold text-[#5B5550] block">Tracking method:</span>',
    '<span class="text-xs sm:text-sm font-bold text-[#5B5550] block">${isVi ? \'Hình thức tracking\' : \'Tracking method\'}:</span>'
)
modal_fn = modal_fn.replace(
    ">\n                        Options\n                    </button>",
    ">\n                        ${isVi ? 'Lựa chọn' : 'Options'}\n                    </button>"
)
modal_fn = modal_fn.replace(
    ">\n                        Scale\n                    </button>",
    ">\n                        ${isVi ? 'Thang đo' : 'Scale'}\n                    </button>"
)
modal_fn = modal_fn.replace(
    ">\n                        Quantity\n                    </button>",
    ">\n                        ${isVi ? 'Số lượng' : 'Quantity'}\n                    </button>"
)

# Alert system section
modal_fn = modal_fn.replace(
    '<span class="text-xs sm:text-sm font-bold text-[#5B5550]">Alert system</span>',
    '<span class="text-xs sm:text-sm font-bold text-[#5B5550]">${isVi ? \'Cơ chế cảnh báo\' : \'Alert system\'}</span>'
)
modal_fn = modal_fn.replace(
    ">${draft.alertEnabled ? 'text-[#37352F]' : 'text-stone-400'}\">On</span>",
    ">${draft.alertEnabled ? 'text-[#37352F]' : 'text-stone-400'}\">${isVi ? 'Bật' : 'On'}</span>"
)
modal_fn = modal_fn.replace(
    ">${!draft.alertEnabled ? 'text-[#37352F]' : 'text-stone-400'}\">Off</span>",
    ">${!draft.alertEnabled ? 'text-[#37352F]' : 'text-stone-400'}\">${isVi ? 'Tắt' : 'Off'}</span>"
)
modal_fn = modal_fn.replace(
    'title="Toggle alert system">',
    'title="${isVi ? \'Bật/tắt cơ chế cảnh báo\' : \'Toggle alert system\'}">'
)
modal_fn = modal_fn.replace(
    '<p class="text-xs text-[#6F6B68]">Notice me if my checks are</p>',
    '<p class="text-xs text-[#6F6B68]">${isVi ? \'Cảnh báo khi kết quả tracking của tôi\' : \'Notice me if my checks are\'}</p>'
)

# Bottom Actions
modal_fn = modal_fn.replace(
    'class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-600 hover:text-stone-900 transition cursor-pointer">\n                    Cancel\n                </button>',
    'class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-600 hover:text-stone-900 transition cursor-pointer">\n                    ${isVi ? \'Hủy\' : \'Cancel\'}\n                </button>'
)
modal_fn = modal_fn.replace(
    "${draft.mode === 'create' ? 'Add tracking' : 'Save changes'}",
    "${draft.mode === 'create' ? (isVi ? 'Thêm tracking' : 'Add tracking') : (isVi ? 'Lưu thay đổi' : 'Save changes')}"
)

# Replace the modal function in text
text = text[:start_idx] + modal_fn + text[end_idx:]

# 7. Update onLanguageChange listener
old_lang_change = '''    if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
        window.TempoI18n.onLanguageChange(() => {
            const screenEl = document.getElementById('screen-stress-check');
            const root = document.getElementById('self-check-workspace-root');
            if (root && screenEl && !screenEl.classList.contains('hidden')) {
                render();
            }
        });
    }'''

new_lang_change = '''    if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
        window.TempoI18n.onLanguageChange(() => {
            const screenEl = document.getElementById('screen-stress-check');
            const root = document.getElementById('self-check-workspace-root');
            if (root && screenEl && !screenEl.classList.contains('hidden')) {
                render();
            }
            const modal = document.getElementById('modal-selfcheck-adjust');
            if (modal && !modal.classList.contains('hidden') && adjustDraftState) {
                const activeId = document.activeElement ? document.activeElement.id : null;
                const selStart = (activeId && document.getElementById(activeId) && typeof document.getElementById(activeId).selectionStart === 'number')
                    ? document.getElementById(activeId).selectionStart
                    : null;
                const selEnd = (activeId && document.getElementById(activeId) && typeof document.getElementById(activeId).selectionEnd === 'number')
                    ? document.getElementById(activeId).selectionEnd
                    : null;

                readCurrentDraftInputs();
                renderAdjustModal();

                if (activeId && document.getElementById(activeId)) {
                    const el = document.getElementById(activeId);
                    el.focus();
                    if (selStart !== null && selEnd !== null && typeof el.setSelectionRange === 'function') {
                        try {
                            el.setSelectionRange(selStart, selEnd);
                        } catch (e) {}
                    }
                }
            }
        });
    }'''

assert old_lang_change in text, 'old_lang_change not found'
text = text.replace(old_lang_change, new_lang_change, 1)

# Strictly write with LF line endings
text = text.replace('\r\n', '\n')
with open('selfCheckWorkspace.js', 'wb') as f:
    f.write(text.encode('utf-8'))

print('Successfully applied all changes to selfCheckWorkspace.js!')
