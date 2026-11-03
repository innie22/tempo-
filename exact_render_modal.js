    function renderAdjustModal() {
        const container = document.getElementById('selfcheck-adjust-modal-card');
        if (!container || !adjustDraftState) return;
        const draft = adjustDraftState;

        const customTypes = getCustomTypes();
        const customTypesHTML = customTypes.map(t => {
            const isSelected = draft.typeId === t.id;
            const style = isSelected 
                ? `background-color: ${t.color}; color: #ffffff;` 
                : `background-color: ${t.color}25; color: ${t.color}; border: 1px solid ${t.color}50;`;
            return `
                <button type="button" 
                        onclick="window.TempoSelfCheckWorkspace.setAdjustType('${t.id}', '${escapeHTML(t.name)}', '${t.color}')"
                        class="px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer shadow-2xs"
                        style="${style}">
                    ${escapeHTML(t.name)}
                </button>
            `;
        }).join('');

        // Preset colors for new type form
        const presetColors = ['#C34D2E', '#859B8B', '#2563EB', '#7C3AED', '#D97706', '#0D9488', '#EC4899', '#4B5563'];
        const colorButtonsHTML = presetColors.map(c => `
            <button type="button" 
                    onclick="window.TempoSelfCheckWorkspace.setNewTypeColor('${c}')"
                    class="w-6 h-6 rounded-full cursor-pointer transition transform ${draft.selectedNewColor === c ? 'scale-110 ring-2 ring-offset-1 ring-stone-600' : 'hover:scale-105'}"
                    style="background-color: ${c};" 
                    title="${c}">
            </button>
        `).join('');

        const newTypeFormHTML = draft.showNewTypeForm ? `
            <div class="mt-2.5 p-3.5 bg-white rounded-2xl border border-stone-200/80 space-y-2.5 shadow-2xs">
                <span class="text-[11px] font-bold text-[#5B5550] block">Create new type</span>
                <input type="text" id="adjust-new-type-input" placeholder="Type label (e.g. Physical, Habit)..." 
                       value="${escapeHTML(draft.newTypeName || '')}"
                       oninput="if(window.TempoSelfCheckWorkspace.setDraftNewTypeName) window.TempoSelfCheckWorkspace.setDraftNewTypeName(this.value)"
                       class="w-full px-3 py-1.5 text-xs rounded-xl border border-stone-300 focus:outline-none focus:border-[#4A6B53]">
                <div class="space-y-1">
                    <span class="text-[10px] text-stone-500 font-semibold block">Choose color:</span>
                    <div class="flex items-center space-x-2">
                        <div class="flex items-center space-x-1.5">${colorButtonsHTML}</div>
                        <input type="color" value="${draft.selectedNewColor}" 
                               onchange="window.TempoSelfCheckWorkspace.setNewTypeColor(this.value)"
                               class="w-6 h-6 rounded cursor-pointer border-0 p-0" title="Custom color picker">
                    </div>
                </div>
                ${draft.newTypeError ? `<p class="text-[11px] text-red-600 font-semibold">${escapeHTML(draft.newTypeError)}</p>` : ''}
                <div class="flex items-center space-x-2 pt-1">
                    <button type="button" onclick="window.TempoSelfCheckWorkspace.saveNewType()" 
                            class="px-3.5 py-1 rounded-xl text-xs font-bold bg-[#859B8B] hover:bg-[#748A7A] text-white transition">
                        Save type
                    </button>
                    <button type="button" onclick="window.TempoSelfCheckWorkspace.toggleCreateNewTypeForm(false)" 
                            class="px-2 py-1 text-xs text-stone-500 hover:text-stone-800 transition">
                        Cancel
                    </button>
                </div>
            </div>
        ` : '';

        // Method sub-config (options tag editor, scale selector, or quantity unit)
        let methodConfigHTML = '';
        if (draft.checkMethod === 'options') {
            methodConfigHTML = `
                <div class="p-2.5 bg-stone-100/70 rounded-xl space-y-1.5 mt-2 border border-stone-200/60">
                    <div class="flex items-center justify-between">
                        <span class="text-[11px] font-bold text-[#5B5550]">Configured options:</span>
                        <span class="text-[10px] text-stone-400">Click ✕ to remove</span>
                    </div>
                    <div class="flex flex-wrap gap-1.5 items-center">
                        ${draft.options.map(opt => `
                            <span class="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-lg text-xs font-semibold bg-white border border-stone-300 text-[#284132]">
                                <span>${escapeHTML(opt)}</span>
                                ${draft.options.length > 2 ? `<button type="button" onclick="window.TempoSelfCheckWorkspace.removeAdjustOption('${escapeHTML(opt)}')" class="text-stone-400 hover:text-red-500 ml-1">✕</button>` : ''}
                            </span>
                        `).join('')}
                    </div>
                    <div class="flex items-center space-x-2 pt-1">
                        <input type="text" id="adjust-new-option-input" placeholder="Add custom option (e.g. Maybe)..." 
                               class="px-2.5 py-1 rounded-lg border border-stone-300 text-xs w-48 bg-white focus:outline-none">
                        <button type="button" onclick="window.TempoSelfCheckWorkspace.addAdjustOption()" 
                                class="px-3 py-1 rounded-lg text-xs font-bold bg-[#859B8B] text-white hover:bg-[#748A7A] transition">
                            Add
                        </button>
                    </div>
                </div>
            `;
        } else if (draft.checkMethod === 'scale') {
            methodConfigHTML = `
                <div class="p-2.5 bg-stone-100/70 rounded-xl flex items-center space-x-3 mt-2 border border-stone-200/60">
                    <span class="text-[11px] font-bold text-[#5B5550]">Scale range:</span>
                    <button type="button" onclick="window.TempoSelfCheckWorkspace.setAdjustScaleRange('1-5')"
                            class="px-3 py-1 rounded-lg text-xs font-bold transition ${draft.scaleRange === '1-5' ? 'bg-[#859B8B] text-white shadow-2xs' : 'bg-white text-stone-700 border border-stone-300'}">
                        1 to 5
                    </button>
                    <button type="button" onclick="window.TempoSelfCheckWorkspace.setAdjustScaleRange('1-10')"
                            class="px-3 py-1 rounded-lg text-xs font-bold transition ${draft.scaleRange === '1-10' ? 'bg-[#859B8B] text-white shadow-2xs' : 'bg-white text-stone-700 border border-stone-300'}">
                        1 to 10
                    </button>
                </div>
            `;
        } else if (draft.checkMethod === 'quantity') {
            methodConfigHTML = `
                <div class="p-2.5 bg-stone-100/70 rounded-xl space-y-1.5 mt-2 border border-stone-200/60">
                    <span class="text-[11px] font-bold text-[#5B5550]">Measurement unit:</span>
                    <div class="flex flex-wrap gap-1.5 items-center">
                        ${['minutes', 'steps', 'times', 'hours', 'glasses', 'pages'].map(u => `
                            <button type="button" onclick="window.TempoSelfCheckWorkspace.setAdjustQuantityUnit('${u}')"
                                    class="px-2.5 py-0.5 rounded-lg text-xs font-semibold transition ${draft.quantityUnit === u ? 'bg-[#859B8B] text-white shadow-2xs' : 'bg-white text-stone-700 border border-stone-300 hover:bg-stone-50'}">
                                ${u}
                            </button>
                        `).join('')}
                    </div>
                    <div class="flex items-center space-x-2 pt-1">
                        <input type="text" id="adjust-custom-unit-input" placeholder="Custom unit (e.g. km, laps)..." 
                               value="${!['minutes', 'steps', 'times', 'hours', 'glasses', 'pages'].includes(draft.quantityUnit) ? draft.quantityUnit : ''}"
                               class="px-2.5 py-1 rounded-lg border border-stone-300 text-xs w-44 bg-white focus:outline-none"
                               oninput="window.TempoSelfCheckWorkspace.setAdjustQuantityUnit(this.value)">
                    </div>
                </div>
            `;
        }

        const alertTypeSelectorHTML = `
            <div class="flex items-center space-x-2 pt-1 pb-1.5">
                <span class="text-xs font-semibold text-[#5B5550]">Alert type:</span>
                <select id="adjust-alert-type" onchange="if(window.TempoSelfCheckWorkspace.readCurrentAlertInputs) window.TempoSelfCheckWorkspace.readCurrentAlertInputs()" class="px-2.5 py-1 text-xs rounded-xl border border-stone-300 bg-white font-bold text-[#284132] focus:outline-none">
                    <option value="stress_sign" ${draft.alertType === 'stress_sign' ? 'selected' : ''}>Sign of Stress</option>
                    <option value="supportive_reminder" ${draft.alertType === 'supportive_reminder' ? 'selected' : ''}>Supportive Reminder</option>
                </select>
            </div>
        `;

        // Method-specific Alert Controls matching screenshot design
        let alertControlsHTML = '';
        if (draft.checkMethod === 'percentage') {
            alertControlsHTML = `
                <div class="flex flex-wrap items-center gap-1.5 text-xs sm:text-sm text-[#284132] font-medium pt-1">
                    <select id="adjust-alert-operator" class="px-2.5 py-1.5 rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                        <option value="more_than" ${draft.alertOperator === 'more_than' ? 'selected' : ''}>More than</option>
                        <option value="less_than" ${draft.alertOperator === 'less_than' ? 'selected' : ''}>Less than</option>
                    </select>
                    <input type="number" id="adjust-alert-threshold" value="${draft.alertThreshold}" min="0" max="100" 
                           class="w-12 px-1.5 py-1.5 text-center rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                    <span>% for</span>
                    <input type="number" id="adjust-alert-days" value="${draft.alertDays}" min="1" max="30" 
                           class="w-10 px-1 py-1.5 text-center rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                    <span>days in a row.</span>
                </div>
            `;
        } else if (draft.checkMethod === 'options') {
            alertControlsHTML = `
                <div class="flex flex-wrap items-center gap-1.5 text-xs sm:text-sm text-[#284132] font-medium pt-1">
                    <span>Alert me when I select</span>
                    <select id="adjust-alert-option-target" class="px-2.5 py-1.5 rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                        ${draft.options.map(opt => `<option value="${escapeHTML(opt)}" ${opt === draft.alertTargetOption ? 'selected' : ''}>${escapeHTML(opt)}</option>`).join('')}
                    </select>
                    <span>for</span>
                    <input type="number" id="adjust-alert-days" value="${draft.alertDays}" min="1" max="30" 
                           class="w-10 px-1 py-1.5 text-center rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                    <span>days in a row.</span>
                </div>
            `;
        } else if (draft.checkMethod === 'scale') {
            const scaleMax = draft.scaleRange === '1-10' ? 10 : 5;
            const scaleNumbers = [];
            for (let i = 1; i <= scaleMax; i++) scaleNumbers.push(i);

            alertControlsHTML = `
                <div class="flex flex-wrap items-center gap-1.5 text-xs sm:text-sm text-[#284132] font-medium pt-1">
                    <select id="adjust-alert-operator" class="px-2.5 py-1.5 rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                        <option value="more_than" ${draft.alertOperator === 'more_than' ? 'selected' : ''}>More than</option>
                        <option value="less_than" ${draft.alertOperator === 'less_than' ? 'selected' : ''}>Less than</option>
                    </select>
                    <select id="adjust-alert-threshold" class="px-2 py-1.5 rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                        ${scaleNumbers.map(n => `<option value="${n}" ${n == draft.alertThreshold ? 'selected' : ''}>${n}</option>`).join('')}
                    </select>
                    <span>on a scale of ${draft.scaleRange} for</span>
                    <input type="number" id="adjust-alert-days" value="${draft.alertDays}" min="1" max="30" 
                           class="w-10 px-1 py-1.5 text-center rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                    <span>days in a row.</span>
                </div>
            `;
        } else if (draft.checkMethod === 'quantity') {
            const isDidntDo = draft.alertOperator === 'didnt_do';
            alertControlsHTML = `
                <div class="flex flex-wrap items-center gap-1.5 text-xs sm:text-sm text-[#284132] font-medium pt-1">
                    <select id="adjust-alert-operator" onchange="if(window.TempoSelfCheckWorkspace.onAlertOperatorChanged) window.TempoSelfCheckWorkspace.onAlertOperatorChanged(this.value)" class="px-2.5 py-1.5 rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                        <option value="more_than" ${draft.alertOperator === 'more_than' ? 'selected' : ''}>More than</option>
                        <option value="less_than" ${draft.alertOperator === 'less_than' ? 'selected' : ''}>Less than</option>
                        <option value="didnt_do" ${draft.alertOperator === 'didnt_do' ? 'selected' : ''}>Didn't do</option>
                    </select>
                    ${!isDidntDo ? `
                        <input type="number" id="adjust-alert-threshold" value="${draft.alertThreshold}" min="0" step="any" 
                               class="w-14 px-1.5 py-1.5 text-center rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                        <span id="adjust-alert-unit-label">${escapeHTML(draft.quantityUnit)}</span>
                    ` : ''}
                    <span>for</span>
                    <input type="number" id="adjust-alert-days" value="${draft.alertDays}" min="1" max="30" 
                           class="w-10 px-1 py-1.5 text-center rounded-xl border border-stone-400 bg-white font-bold text-[#284132] focus:outline-none">
                    <span>days in a row.</span>
                </div>
            `;
        }

        container.innerHTML = `
            <!-- Close Button -->
            <button type="button" 
                    onclick="window.TempoSelfCheckWorkspace.closeAdjustModal()" 
                    class="absolute top-4 right-4 text-[#9E9893] hover:text-[#37352F] text-base sm:text-lg transition cursor-pointer p-1 rounded-full hover:bg-stone-200/50" 
                    title="Close">
                ✕
            </button>

            <!-- 1. Heading & Editable Tracking Item Name -->
            <div class="space-y-1">
                <span class="text-xs sm:text-sm font-bold text-[#3B5441] tracking-tight block">Your Tracking Item</span>
                <div class="relative pt-0.5">
                    <input type="text" 
                           id="adjust-tracker-name-input" 
                           value="${escapeHTML(draft.trackerName || '')}" 
                           placeholder="Enter tracking name" 
                           maxlength="50"
                           class="w-full font-heading text-2xl sm:text-3xl font-extrabold text-[#284132] tracking-tight bg-white/70 hover:bg-white focus:bg-white rounded-2xl px-3.5 py-1.5 border ${draft.nameError ? 'border-red-400 focus:border-red-500 ring-1 ring-red-400' : 'border-stone-300/80 focus:border-[#4A6B53]'} focus:outline-none placeholder:text-stone-400 placeholder:font-normal placeholder:text-lg sm:placeholder:text-xl shadow-2xs transition"
                           oninput="if(window.TempoSelfCheckWorkspace.setDraftTrackerName) window.TempoSelfCheckWorkspace.setDraftTrackerName(this.value)" />
                    ${draft.nameError ? `<p id="adjust-name-error-msg" class="text-[11px] text-red-600 font-semibold mt-1 pl-1">${escapeHTML(draft.nameError)}</p>` : ''}
                </div>
            </div>

            <!-- 2. Type Section -->
            <div class="space-y-1.5 pt-2">
                <span class="text-xs sm:text-sm font-bold text-[#5B5550] block">Type:</span>
                <div class="flex flex-wrap items-center gap-2">
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.setAdjustType('stress_sign', 'Sign of stress', '#C34D2E')"
                            class="px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer shadow-2xs"
                            style="${draft.typeId === 'stress_sign' ? 'background-color: #C34D2E; color: #ffffff; box-shadow: 0 0 0 2px rgba(195,77,46,0.35);' : 'background-color: rgba(195,77,46,0.78); color: #ffffff;'}">
                        Sign of stress
                    </button>
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.setAdjustType('supportive', 'Supportive', '#859B8B')"
                            class="px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer shadow-2xs"
                            style="${draft.typeId === 'supportive' ? 'background-color: #859B8B; color: #ffffff; box-shadow: 0 0 0 2px rgba(133,155,139,0.35);' : 'background-color: rgba(133,155,139,0.78); color: #ffffff;'}">
                        Supportive
                    </button>
                    ${customTypesHTML}
                </div>
                <button type="button" 
                        onclick="window.TempoSelfCheckWorkspace.toggleCreateNewTypeForm()"
                        class="text-xs font-bold text-[#D48366] hover:underline transition cursor-pointer pt-0.5 block">
                    Create new type
                </button>
                ${newTypeFormHTML}
            </div>

            <!-- 3. Tracking Method Section -->
            <div class="space-y-1.5 pt-2">
                <span class="text-xs sm:text-sm font-bold text-[#5B5550] block">Tracking method:</span>
                <div class="grid grid-cols-4 gap-2 w-full">
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.setAdjustMethod('percentage')"
                            class="py-1.5 px-1 rounded-xl text-center text-xs sm:text-sm font-bold transition cursor-pointer shadow-2xs ${draft.checkMethod === 'percentage' ? 'bg-[#E2EAE4] border border-[#6B8B73] text-[#284132]' : 'bg-white border border-stone-300/80 text-[#3B5441] hover:bg-stone-50'}">
                        %
                    </button>
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.setAdjustMethod('options')"
                            class="py-1.5 px-1 rounded-xl text-center text-xs sm:text-sm font-bold transition cursor-pointer shadow-2xs ${draft.checkMethod === 'options' ? 'bg-[#E2EAE4] border border-[#6B8B73] text-[#284132]' : 'bg-white border border-stone-300/80 text-[#3B5441] hover:bg-stone-50'}">
                        Options
                    </button>
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.setAdjustMethod('scale')"
                            class="py-1.5 px-1 rounded-xl text-center text-xs sm:text-sm font-bold transition cursor-pointer shadow-2xs ${draft.checkMethod === 'scale' ? 'bg-[#E2EAE4] border border-[#6B8B73] text-[#284132]' : 'bg-white border border-stone-300/80 text-[#3B5441] hover:bg-stone-50'}">
                        Scale
                    </button>
                    <button type="button" 
                            onclick="window.TempoSelfCheckWorkspace.setAdjustMethod('quantity')"
                            class="py-1.5 px-1 rounded-xl text-center text-xs sm:text-sm font-bold transition cursor-pointer shadow-2xs ${draft.checkMethod === 'quantity' ? 'bg-[#E2EAE4] border border-[#6B8B73] text-[#284132]' : 'bg-white border border-stone-300/80 text-[#3B5441] hover:bg-stone-50'}">
                        Quantity
                    </button>
                </div>
                ${methodConfigHTML}
            </div>

            <!-- 4. Alert System Section -->
            <div class="space-y-1.5 pt-2.5">
                <div class="flex items-center justify-between">
                    <span class="text-xs sm:text-sm font-bold text-[#5B5550]">Alert system</span>
                    <div class="flex items-center space-x-2">
                        <span class="text-xs font-semibold ${draft.alertEnabled ? 'text-[#37352F]' : 'text-stone-400'}">On</span>
                        <button type="button" 
                                onclick="window.TempoSelfCheckWorkspace.toggleAdjustAlertSystem()"
                                class="w-11 h-6 flex items-center rounded-full p-1 cursor-pointer transition ${draft.alertEnabled ? 'bg-[#859B8B] justify-end' : 'bg-stone-300 justify-start'}"
                                title="Toggle alert system">
                            <div class="bg-white w-4 h-4 rounded-full shadow-md"></div>
                        </button>
                        <span class="text-xs font-semibold ${!draft.alertEnabled ? 'text-[#37352F]' : 'text-stone-400'}">Off</span>
                    </div>
                </div>
                <p class="text-xs text-[#6F6B68]">Notice me if my checks are</p>
                <div id="adjust-alert-controls-container" class="${draft.alertEnabled ? '' : 'opacity-40 pointer-events-none'} transition">
                    ${alertTypeSelectorHTML}
                    ${alertControlsHTML}
                </div>
            </div>

            <!-- Bottom Actions -->
            <div class="flex items-center justify-end space-x-3 pt-4 border-t border-stone-200/60 mt-2">
                <button type="button" 
                        onclick="window.TempoSelfCheckWorkspace.closeAdjustModal()" 
                        class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-600 hover:text-stone-900 transition cursor-pointer">
                    Cancel
                </button>
                <button type="button" 
                        id="adjust-save-submit-btn"
                        onclick="window.TempoSelfCheckWorkspace.saveAdjustTracker()" 
                        class="px-5 py-2 rounded-xl text-xs font-bold bg-[#859B8B] hover:bg-[#728878] text-white transition cursor-pointer shadow-xs">
                    ${draft.mode === 'create' ? 'Add tracking' : 'Save changes'}
                </button>
            </div>
        `;
    }


