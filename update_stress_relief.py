import os

path = "stressRelief.js"
with open(path, "rb") as f:
    raw = f.read().decode("utf-8")

# Let's inspect the exact lines to replace
print("Length of stressRelief.js:", len(raw))

# 1. Add isRecoveryMode helper right above init()
t_init = "    function init() {"
rep_init = """    function isRecoveryMode() {
        if (activeContext === 'recovery') return true;
        if (window.TempoMode && typeof window.TempoMode.getMode === 'function') {
            return window.TempoMode.getMode() === 'recovery';
        }
        return false;
    }

    function init() {"""

# 2. openModal wrapper & closeModal
t_openModal = """    function openModal(defaultFilter = 'all') {
        currentFilter = defaultFilter;
        openLibrary({ context: 'home' });
    }

    function openModalWrapper() {
        const modal = document.getElementById('modal-quick-stress-relief');
        if (!modal) return;
        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    function closeModal() {
        stopAllTimers();
        const ctx = activeContext;
        const onClose = onCloseCallback;
        onReadyCallback = null;
        onCloseCallback = null;
        activeContext = 'home';
        const modal = document.getElementById('modal-quick-stress-relief');
        if (modal) {
            modal.classList.add('hidden');
        }
        document.body.classList.remove('overflow-hidden');
        if (typeof onClose === 'function') {
            onClose();
        } else if (ctx === 'emergency_reset' && window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.showResetPopup === 'function') {
            window.TempoUrmodeFlow.showResetPopup();
        }
    }"""

rep_openModal = """    function openModal(defaultFilter = 'all', options = {}) {
        currentFilter = defaultFilter;
        const ctx = options.context || (isRecoveryMode() ? 'recovery' : 'home');
        openLibrary({ context: ctx });
    }

    function openModalWrapper() {
        const modal = document.getElementById('modal-quick-stress-relief');
        if (!modal) return;
        
        const isRec = isRecoveryMode();
        const card = modal.querySelector('.tempo-card');
        const badge = modal.querySelector('span.uppercase.tracking-wider');
        
        if (card) {
            if (isRec) {
                card.className = 'tempo-card max-w-2xl w-full my-auto max-h-[92vh] overflow-y-auto bg-[#FFF9F4] rounded-2xl sm:rounded-[28px] p-5 sm:p-8 space-y-4 relative shadow-xl border border-[#EAE4DF]';
            } else {
                card.className = 'tempo-card max-w-2xl w-full my-auto max-h-[92vh] overflow-y-auto bg-white rounded-2xl sm:rounded-[24px] p-5 sm:p-8 space-y-4 relative shadow-xl border border-[#EAE4DF]';
            }
        }
        
        if (badge) {
            if (isRec) {
                badge.className = 'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-[#FFE9DC] text-[#FF6B2C]';
                badge.textContent = 'Grounded Pause';
            } else {
                badge.className = 'text-[11px] font-bold uppercase tracking-wider text-[#B83D08]';
                badge.textContent = 'Grounded Pause';
            }
        }

        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    function closeModal() {
        stopAllTimers();
        const ctx = activeContext;
        const onClose = onCloseCallback;
        onReadyCallback = null;
        onCloseCallback = null;
        activeContext = 'home';
        const modal = document.getElementById('modal-quick-stress-relief');
        if (modal) {
            modal.classList.add('hidden');
            const card = modal.querySelector('.tempo-card');
            const badge = modal.querySelector('span.uppercase.tracking-wider');
            if (card) card.className = 'tempo-card max-w-2xl w-full my-auto max-h-[92vh] overflow-y-auto bg-white rounded-2xl sm:rounded-[24px] p-5 sm:p-8 space-y-4 relative shadow-xl border border-[#EAE4DF]';
            if (badge) badge.className = 'text-[11px] font-bold uppercase tracking-wider text-[#B83D08]';
        }
        document.body.classList.remove('overflow-hidden');
        if (typeof onClose === 'function') {
            onClose();
        } else if (ctx === 'emergency_reset' && window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.showResetPopup === 'function') {
            window.TempoUrmodeFlow.showResetPopup();
        }
    }"""

# 3. renderLibrary
t_renderLib = """    function renderLibrary() {
        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        const filters = [
            { key: 'all', label: 'All Durations' },
            { key: '1', label: '⚡ 1 min' },
            { key: '3', label: '🌿 3 min' },
            { key: '5', label: '🚶 5 min' }
        ];

        const filtered = currentFilter === 'all'
            ? METHODS
            : METHODS.filter(m => String(m.filterDuration) === currentFilter);

        container.innerHTML = `
            <div class="space-y-6">
                <!-- Header -->
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">QUICK STRESS RELIEF</span>
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Choose a grounding method</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">Pick something small to try. A few minutes is enough to signal your nervous system.</p>
                </div>

                <!-- Duration Filter Pills -->
                <div class="flex flex-wrap items-center gap-2">
                    ${filters.map(f => `
                        <button onclick="window.TempoStressRelief.setFilter('${f.key}')" 
                                class="px-3.5 py-1.5 rounded-full text-xs font-semibold transition ${
                                    currentFilter === f.key 
                                        ? 'bg-[#FF6B2C] text-white shadow-sm' 
                                        : 'bg-[#F3F1EF] text-[#6F6B68] hover:text-[#202124] hover:bg-stone-200'
                                }">
                            ${f.label}
                        </button>
                    `).join('')}
                </div>

                <!-- Cards Grid -->
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-1">
                    ${filtered.map(m => `
                        <div onclick="window.TempoStressRelief.selectMethod('${m.id}')"
                             tabindex="0"
                             role="button"
                             onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();window.TempoStressRelief.selectMethod('${m.id}');}"
                             class="p-4 bg-white border border-[#EAE4DF] hover:border-[#FF6B2C] rounded-2xl cursor-pointer transition hover:shadow-sm space-y-2 group flex flex-col justify-between">
                            <div class="space-y-2">
                                <div class="flex items-center justify-between">
                                    <span class="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FFE9DC] text-[#B83D08]">
                                        <span>${m.durationLabel}</span>
                                    </span>
                                    <span class="text-lg">${m.icon}</span>
                                </div>
                                <h4 class="font-heading text-sm font-bold text-[#202124] group-hover:text-[#FF6B2C] transition">
                                    ${m.title}
                                </h4>
                                <p class="text-xs text-[#6F6B68] leading-relaxed line-clamp-2">
                                    ${m.summary}
                                </p>
                            </div>
                            <div class="pt-2 flex items-center justify-between text-xs text-[#FF6B2C] font-bold border-t border-stone-100">
                                <span>Start this action</span>
                                <span class="group-hover:translate-x-1 transition-transform">→</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }"""

rep_renderLib = """    function renderLibrary() {
        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        const isRec = isRecoveryMode();

        const filters = isRec ? [
            { key: 'all', label: 'All Durations' },
            { key: '1', label: '1 min' },
            { key: '3', label: '3 min' },
            { key: '5', label: '5 min' }
        ] : [
            { key: 'all', label: 'All Durations' },
            { key: '1', label: '⚡ 1 min' },
            { key: '3', label: '🌿 3 min' },
            { key: '5', label: '🚶 5 min' }
        ];

        const filtered = currentFilter === 'all'
            ? METHODS
            : METHODS.filter(m => String(m.filterDuration) === currentFilter);

        if (isRec) {
            container.innerHTML = `
                <div class="space-y-6">
                    <!-- Header -->
                    <div class="space-y-1">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">Quick Stress Relief</span>
                        <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Choose a grounding method</h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">Pick something small to try. A few minutes is enough to signal your nervous system.</p>
                    </div>

                    <!-- Duration Filter Pills (No Emojis!) -->
                    <div class="flex flex-wrap items-center gap-2">
                        ${filters.map(f => `
                            <button onclick="window.TempoStressRelief.setFilter('${f.key}')" 
                                    class="px-4 py-1.5 rounded-full text-xs transition cursor-pointer ${
                                        currentFilter === f.key 
                                            ? 'bg-[#FF6B2C] text-white shadow-xs font-bold' 
                                            : 'bg-[#F3F1EF] text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF] font-semibold'
                                    }">
                                ${f.label}
                            </button>
                        `).join('')}
                    </div>

                    <!-- Cards Grid (2-column on desktop, responsive stack, No Emojis!) -->
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-1">
                        ${filtered.map(m => `
                            <div onclick="window.TempoStressRelief.selectMethod('${m.id}')"
                                 tabindex="0"
                                 role="button"
                                 onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();window.TempoStressRelief.selectMethod('${m.id}');}"
                                 class="p-4 sm:p-5 bg-white border border-[#EAE4DF] hover:border-[#FF6B2C] rounded-2xl cursor-pointer transition hover:shadow-xs space-y-3 group flex flex-col justify-between">
                                <div class="space-y-2">
                                    <div class="flex items-center justify-between">
                                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FFE9DC] text-[#FF6B2C]">
                                            ${m.durationLabel}
                                        </span>
                                    </div>
                                    <h4 class="font-heading text-sm sm:text-[15px] font-bold text-[#202124] group-hover:text-[#FF6B2C] transition leading-snug">
                                        ${m.title}
                                    </h4>
                                    <p class="text-xs text-[#6F6B68] leading-relaxed line-clamp-2">
                                        ${m.summary}
                                    </p>
                                </div>
                                <div class="pt-2.5 flex items-center justify-between text-xs text-[#FF6B2C] font-bold border-t border-[#F3F1EF]">
                                    <span>Start this action</span>
                                    <span class="group-hover:translate-x-1 transition-transform">→</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="space-y-6">
                <!-- Header -->
                <div class="space-y-1">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">QUICK STRESS RELIEF</span>
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Choose a grounding method</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">Pick something small to try. A few minutes is enough to signal your nervous system.</p>
                </div>

                <!-- Duration Filter Pills -->
                <div class="flex flex-wrap items-center gap-2">
                    ${filters.map(f => `
                        <button onclick="window.TempoStressRelief.setFilter('${f.key}')" 
                                class="px-3.5 py-1.5 rounded-full text-xs font-semibold transition ${
                                    currentFilter === f.key 
                                        ? 'bg-[#FF6B2C] text-white shadow-sm' 
                                        : 'bg-[#F3F1EF] text-[#6F6B68] hover:text-[#202124] hover:bg-stone-200'
                                }">
                            ${f.label}
                        </button>
                    `).join('')}
                </div>

                <!-- Cards Grid -->
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-1">
                    ${filtered.map(m => `
                        <div onclick="window.TempoStressRelief.selectMethod('${m.id}')"
                             tabindex="0"
                             role="button"
                             onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();window.TempoStressRelief.selectMethod('${m.id}');}"
                             class="p-4 bg-white border border-[#EAE4DF] hover:border-[#FF6B2C] rounded-2xl cursor-pointer transition hover:shadow-sm space-y-2 group flex flex-col justify-between">
                            <div class="space-y-2">
                                <div class="flex items-center justify-between">
                                    <span class="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FFE9DC] text-[#B83D08]">
                                        <span>${m.durationLabel}</span>
                                    </span>
                                    <span class="text-lg">${m.icon}</span>
                                </div>
                                <h4 class="font-heading text-sm font-bold text-[#202124] group-hover:text-[#FF6B2C] transition">
                                    ${m.title}
                                </h4>
                                <p class="text-xs text-[#6F6B68] leading-relaxed line-clamp-2">
                                    ${m.summary}
                                </p>
                            </div>
                            <div class="pt-2 flex items-center justify-between text-xs text-[#FF6B2C] font-bold border-t border-stone-100">
                                <span>Start this action</span>
                                <span class="group-hover:translate-x-1 transition-transform">→</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }"""

# 4. renderBreathingSetup
t_breathing = """    function renderBreathingSetup() {
        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        selectedDuration = 3;

        container.innerHTML = `
            <div class="space-y-6 max-w-lg mx-auto py-2">
                <!-- Header -->
                <div class="text-center space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">BREATHING</span>
                    <h3 class="font-heading text-2xl font-bold text-[#202124]">Box Breathing Reset</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">Take a few minutes and follow the rhythm.</p>
                </div>

                <!-- Explanation Box -->
                <div class="p-4 bg-[#FFF8F2] border border-[#FFD2BA]/60 rounded-2xl text-xs text-[#6F6B68] leading-relaxed space-y-2">
                    <p class="font-semibold text-[#202124]">How it works:</p>
                    <p>Inhale (4s) • Hold (4s) • Exhale (4s) • Rest (4s). This equal cadence helps your heart rate and nervous system downshift naturally.</p>
                </div>

                <!-- Duration Picker -->
                <div class="space-y-3 pt-1">
                    <label class="block text-xs font-bold uppercase tracking-wider text-[#202124] text-center">
                        Select Duration:
                    </label>
                    <div class="flex items-center justify-center gap-2.5">
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(1)" id="dur-btn-1" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50">
                            1 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(3)" id="dur-btn-3" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition bg-[#FF6B2C] text-white border border-[#FF6B2C] shadow-sm">
                            3 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(5)" id="dur-btn-5" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50">
                            5 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice('custom')" id="dur-btn-custom" 
                                class="px-3.5 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50">
                            Custom
                        </button>
                    </div>

                    <!-- Custom Duration Input (hidden by default) -->
                    <div id="custom-duration-box" class="hidden text-center pt-2">
                        <label for="custom-duration-input" class="text-xs text-[#6F6B68] mr-2">Minutes:</label>
                        <input id="custom-duration-input" type="number" min="1" max="20" value="4" 
                               onchange="window.TempoStressRelief.handleCustomDurationChange(this.value)"
                               class="w-16 px-2.5 py-1 text-xs border border-gray-300 rounded-lg text-center font-bold">
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
                    <button onclick="window.TempoStressRelief.startBreathingSession()" 
                            class="btn-primary w-full sm:w-auto px-8 py-3 rounded-xl font-bold text-sm shadow-md flex items-center justify-center space-x-2">
                        <span>Start Breathing →</span>
                    </button>
                    <button onclick="window.TempoStressRelief.renderLibrary()" 
                            class="w-full sm:w-auto px-5 py-3 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                        View Other Methods
                    </button>
                </div>
            </div>
        `;
    }"""

rep_breathing = """    function renderBreathingSetup() {
        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        selectedDuration = 3;
        const isRec = isRecoveryMode();

        if (isRec) {
            container.innerHTML = `
                <div class="space-y-6 max-w-lg mx-auto py-2">
                    <!-- Header -->
                    <div class="text-center space-y-1.5">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">Breathing</span>
                        <h3 class="font-heading text-2xl font-bold text-[#202124]">Box Breathing Reset</h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68]">Take a few minutes and follow the rhythm.</p>
                    </div>

                    <!-- Explanation Box -->
                    <div class="p-4 bg-[#FFF9F4] border border-[#FFE9DC] rounded-2xl text-xs text-[#6F6B68] leading-relaxed space-y-2">
                        <p class="font-bold text-[#202124]">How it works:</p>
                        <p>Inhale (4s) • Hold (4s) • Exhale (4s) • Rest (4s). This equal cadence helps your heart rate and nervous system downshift naturally.</p>
                    </div>

                    <!-- Duration Picker -->
                    <div class="space-y-3 pt-1">
                        <label class="block text-xs font-bold uppercase tracking-wider text-[#202124] text-center">
                            Select Duration:
                        </label>
                        <div class="flex items-center justify-center gap-2.5">
                            <button type="button" onclick="window.TempoStressRelief.setDurationChoice(1)" id="dur-btn-1" 
                                    class="px-4 py-2 rounded-xl text-xs font-bold transition border border-[#EAE4DF] text-[#202124] hover:bg-[#F3F1EF]">
                                1 min
                            </button>
                            <button type="button" onclick="window.TempoStressRelief.setDurationChoice(3)" id="dur-btn-3" 
                                    class="px-4 py-2 rounded-xl text-xs font-bold transition bg-[#FF6B2C] text-white border border-[#FF6B2C] shadow-xs">
                                3 min
                            </button>
                            <button type="button" onclick="window.TempoStressRelief.setDurationChoice(5)" id="dur-btn-5" 
                                    class="px-4 py-2 rounded-xl text-xs font-bold transition border border-[#EAE4DF] text-[#202124] hover:bg-[#F3F1EF]">
                                5 min
                            </button>
                            <button type="button" onclick="window.TempoStressRelief.setDurationChoice('custom')" id="dur-btn-custom" 
                                    class="px-3.5 py-2 rounded-xl text-xs font-bold transition border border-[#EAE4DF] text-[#202124] hover:bg-[#F3F1EF]">
                                Custom
                            </button>
                        </div>

                        <!-- Custom Duration Input (hidden by default) -->
                        <div id="custom-duration-box" class="hidden text-center pt-2">
                            <label for="custom-duration-input" class="text-xs text-[#6F6B68] mr-2">Minutes:</label>
                            <input id="custom-duration-input" type="number" min="1" max="20" value="4" 
                                   onchange="window.TempoStressRelief.handleCustomDurationChange(this.value)"
                                   class="w-16 px-2.5 py-1 text-xs border border-[#EAE4DF] rounded-lg text-center font-bold text-[#202124]">
                        </div>
                    </div>

                    <!-- Action Buttons -->
                    <div class="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
                        <button onclick="window.TempoStressRelief.startBreathingSession()" 
                                class="btn-primary w-full sm:w-auto px-8 py-3 rounded-xl font-bold text-sm shadow-xs flex items-center justify-center space-x-2 bg-[#FF6B2C] hover:bg-[#E8591C] text-white transition cursor-pointer">
                            <span>Start Breathing →</span>
                        </button>
                        <button onclick="window.TempoStressRelief.renderLibrary()" 
                                class="w-full sm:w-auto px-5 py-3 rounded-xl border border-[#EAE4DF] text-xs font-bold text-[#202124] bg-white hover:bg-[#F3F1EF] transition cursor-pointer">
                            View Other Methods
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="space-y-6 max-w-lg mx-auto py-2">
                <!-- Header -->
                <div class="text-center space-y-1.5">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">BREATHING</span>
                    <h3 class="font-heading text-2xl font-bold text-[#202124]">Box Breathing Reset</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">Take a few minutes and follow the rhythm.</p>
                </div>

                <!-- Explanation Box -->
                <div class="p-4 bg-[#FFF8F2] border border-[#FFD2BA]/60 rounded-2xl text-xs text-[#6F6B68] leading-relaxed space-y-2">
                    <p class="font-semibold text-[#202124]">How it works:</p>
                    <p>Inhale (4s) • Hold (4s) • Exhale (4s) • Rest (4s). This equal cadence helps your heart rate and nervous system downshift naturally.</p>
                </div>

                <!-- Duration Picker -->
                <div class="space-y-3 pt-1">
                    <label class="block text-xs font-bold uppercase tracking-wider text-[#202124] text-center">
                        Select Duration:
                    </label>
                    <div class="flex items-center justify-center gap-2.5">
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(1)" id="dur-btn-1" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50">
                            1 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(3)" id="dur-btn-3" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition bg-[#FF6B2C] text-white border border-[#FF6B2C] shadow-sm">
                            3 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(5)" id="dur-btn-5" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50">
                            5 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice('custom')" id="dur-btn-custom" 
                                class="px-3.5 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50">
                            Custom
                        </button>
                    </div>

                    <!-- Custom Duration Input (hidden by default) -->
                    <div id="custom-duration-box" class="hidden text-center pt-2">
                        <label for="custom-duration-input" class="text-xs text-[#6F6B68] mr-2">Minutes:</label>
                        <input id="custom-duration-input" type="number" min="1" max="20" value="4" 
                               onchange="window.TempoStressRelief.handleCustomDurationChange(this.value)"
                               class="w-16 px-2.5 py-1 text-xs border border-gray-300 rounded-lg text-center font-bold">
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
                    <button onclick="window.TempoStressRelief.startBreathingSession()" 
                            class="btn-primary w-full sm:w-auto px-8 py-3 rounded-xl font-bold text-sm shadow-md flex items-center justify-center space-x-2">
                        <span>Start Breathing →</span>
                    </button>
                    <button onclick="window.TempoStressRelief.renderLibrary()" 
                            class="w-full sm:w-auto px-5 py-3 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                        View Other Methods
                    </button>
                </div>
            </div>
        `;
    }"""

# 5. renderMethodDetail
t_detail = """    function renderMethodDetail(method) {
        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        selectedDuration = method.defaultDuration || 3;

        container.innerHTML = `
            <div class="space-y-6 max-w-lg mx-auto py-2">
                <!-- Back Link -->
                <button onclick="window.TempoStressRelief.renderLibrary()" 
                        class="text-xs font-semibold text-[#6F6B68] hover:text-[#202124] flex items-center space-x-1 transition">
                    <span>←</span>
                    <span>Back to all methods</span>
                </button>

                <!-- Method Header -->
                <div class="space-y-1.5 border-b border-gray-100 pb-4">
                    <div class="flex items-center space-x-2">
                        <span class="text-2xl">${method.icon}</span>
                        <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#FFE9DC] text-[#B83D08]">
                            ${method.durationLabel}
                        </span>
                    </div>
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">${method.title}</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">${method.summary}</p>
                </div>

                <!-- Step-by-Step Instructions -->
                <div class="space-y-2.5">
                    <h4 class="text-xs font-bold uppercase tracking-wider text-[#202124]">Simple Instructions:</h4>
                    <ol class="space-y-2">
                        ${method.steps.map((s, idx) => `
                            <li class="flex items-start space-x-3 p-3 bg-[#FFF8F2] border border-[#FFD2BA]/60 rounded-xl text-xs text-[#202124]">
                                <span class="w-5 h-5 rounded-full bg-[#FF6B2C] text-white flex items-center justify-center font-bold text-[11px] shrink-0 mt-0.5">
                                    ${idx + 1}
                                </span>
                                <span class="leading-relaxed">${s}</span>
                            </li>
                        `).join('')}
                    </ol>
                </div>

                <!-- Duration Picker -->
                <div class="space-y-3 pt-2">
                    <label class="block text-xs font-bold uppercase tracking-wider text-[#202124] text-center">
                        How long?
                    </label>
                    <div class="flex items-center justify-center gap-2.5">
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(1)" id="dur-btn-1" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 1 ? 'bg-[#FF6B2C] text-white border border-[#FF6B2C]' : 'border border-gray-200 text-gray-700 hover:bg-stone-50'}">
                            1 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(3)" id="dur-btn-3" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 3 ? 'bg-[#FF6B2C] text-white border border-[#FF6B2C]' : 'border border-gray-200 text-gray-700 hover:bg-stone-50'}">
                            3 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(5)" id="dur-btn-5" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 5 ? 'bg-[#FF6B2C] text-white border border-[#FF6B2C]' : 'border border-gray-200 text-gray-700 hover:bg-stone-50'}">
                            5 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice('custom')" id="dur-btn-custom" 
                                class="px-3.5 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50">
                            Custom
                        </button>
                    </div>

                    <div id="custom-duration-box" class="hidden text-center pt-2">
                        <label for="custom-duration-input" class="text-xs text-[#6F6B68] mr-2">Minutes:</label>
                        <input id="custom-duration-input" type="number" min="1" max="20" value="${selectedDuration}" 
                               onchange="window.TempoStressRelief.handleCustomDurationChange(this.value)"
                               class="w-16 px-2.5 py-1 text-xs border border-gray-300 rounded-lg text-center font-bold">
                    </div>
                </div>

                <!-- Action Button -->
                <div class="pt-2 flex justify-center">
                    <button onclick="window.TempoStressRelief.startTimedSession()" 
                            class="btn-primary w-full sm:w-auto px-8 py-3 rounded-xl font-bold text-sm shadow-md flex items-center justify-center space-x-2">
                        <span>Start →</span>
                    </button>
                </div>
            </div>
        `;
    }"""

rep_detail = """    function renderMethodDetail(method) {
        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        selectedDuration = method.defaultDuration || 3;
        const isRec = isRecoveryMode();

        if (isRec) {
            container.innerHTML = `
                <div class="space-y-6 max-w-lg mx-auto py-2">
                    <!-- Back Link -->
                    <button onclick="window.TempoStressRelief.renderLibrary()" 
                            class="text-xs font-bold text-[#6F6B68] hover:text-[#202124] flex items-center space-x-1.5 transition cursor-pointer">
                        <span>←</span>
                        <span>Back to all methods</span>
                    </button>

                    <!-- Method Header (No Emojis!) -->
                    <div class="space-y-2 border-b border-[#F3F1EF] pb-4">
                        <div class="flex items-center space-x-2">
                            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#FFE9DC] text-[#FF6B2C]">
                                ${method.durationLabel}
                            </span>
                        </div>
                        <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">${method.title}</h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">${method.summary}</p>
                    </div>

                    <!-- Step-by-Step Instructions -->
                    <div class="space-y-2.5">
                        <h4 class="text-xs font-bold uppercase tracking-wider text-[#202124]">Simple Instructions:</h4>
                        <ol class="space-y-2">
                            ${method.steps.map((s, idx) => `
                                <li class="flex items-start space-x-3 p-3.5 bg-[#FFF9F4] border border-[#FFE9DC] rounded-xl text-xs text-[#202124]">
                                    <span class="w-5 h-5 rounded-full bg-[#FF6B2C] text-white flex items-center justify-center font-bold text-[11px] shrink-0 mt-0.5">
                                        ${idx + 1}
                                    </span>
                                    <span class="leading-relaxed">${s}</span>
                                </li>
                            `).join('')}
                        </ol>
                    </div>

                    <!-- Duration Picker -->
                    <div class="space-y-3 pt-2">
                        <label class="block text-xs font-bold uppercase tracking-wider text-[#202124] text-center">
                            How long?
                        </label>
                        <div class="flex items-center justify-center gap-2.5">
                            <button type="button" onclick="window.TempoStressRelief.setDurationChoice(1)" id="dur-btn-1" 
                                    class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 1 ? 'bg-[#FF6B2C] text-white border border-[#FF6B2C] shadow-xs' : 'border border-[#EAE4DF] text-[#202124] hover:bg-[#F3F1EF]'}">
                                1 min
                            </button>
                            <button type="button" onclick="window.TempoStressRelief.setDurationChoice(3)" id="dur-btn-3" 
                                    class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 3 ? 'bg-[#FF6B2C] text-white border border-[#FF6B2C] shadow-xs' : 'border border-[#EAE4DF] text-[#202124] hover:bg-[#F3F1EF]'}">
                                3 min
                            </button>
                            <button type="button" onclick="window.TempoStressRelief.setDurationChoice(5)" id="dur-btn-5" 
                                    class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 5 ? 'bg-[#FF6B2C] text-white border border-[#FF6B2C] shadow-xs' : 'border border-[#EAE4DF] text-[#202124] hover:bg-[#F3F1EF]'}">
                                5 min
                            </button>
                            <button type="button" onclick="window.TempoStressRelief.setDurationChoice('custom')" id="dur-btn-custom" 
                                    class="px-3.5 py-2 rounded-xl text-xs font-bold transition border border-[#EAE4DF] text-[#202124] hover:bg-[#F3F1EF]">
                                Custom
                            </button>
                        </div>

                        <div id="custom-duration-box" class="hidden text-center pt-2">
                            <label for="custom-duration-input" class="text-xs text-[#6F6B68] mr-2">Minutes:</label>
                            <input id="custom-duration-input" type="number" min="1" max="20" value="${selectedDuration}" 
                                   onchange="window.TempoStressRelief.handleCustomDurationChange(this.value)"
                                   class="w-16 px-2.5 py-1 text-xs border border-[#EAE4DF] rounded-lg text-center font-bold text-[#202124]">
                        </div>
                    </div>

                    <!-- Action Button -->
                    <div class="pt-2 flex justify-center">
                        <button onclick="window.TempoStressRelief.startTimedSession()" 
                                class="btn-primary w-full sm:w-auto px-8 py-3 rounded-xl font-bold text-sm shadow-xs flex items-center justify-center space-x-2 bg-[#FF6B2C] hover:bg-[#E8591C] text-white transition cursor-pointer">
                            <span>Start →</span>
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="space-y-6 max-w-lg mx-auto py-2">
                <!-- Back Link -->
                <button onclick="window.TempoStressRelief.renderLibrary()" 
                        class="text-xs font-semibold text-[#6F6B68] hover:text-[#202124] flex items-center space-x-1 transition">
                    <span>←</span>
                    <span>Back to all methods</span>
                </button>

                <!-- Method Header -->
                <div class="space-y-1.5 border-b border-gray-100 pb-4">
                    <div class="flex items-center space-x-2">
                        <span class="text-2xl">${method.icon}</span>
                        <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#FFE9DC] text-[#B83D08]">
                            ${method.durationLabel}
                        </span>
                    </div>
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">${method.title}</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">${method.summary}</p>
                </div>

                <!-- Step-by-Step Instructions -->
                <div class="space-y-2.5">
                    <h4 class="text-xs font-bold uppercase tracking-wider text-[#202124]">Simple Instructions:</h4>
                    <ol class="space-y-2">
                        ${method.steps.map((s, idx) => `
                            <li class="flex items-start space-x-3 p-3 bg-[#FFF8F2] border border-[#FFD2BA]/60 rounded-xl text-xs text-[#202124]">
                                <span class="w-5 h-5 rounded-full bg-[#FF6B2C] text-white flex items-center justify-center font-bold text-[11px] shrink-0 mt-0.5">
                                    ${idx + 1}
                                </span>
                                <span class="leading-relaxed">${s}</span>
                            </li>
                        `).join('')}
                    </ol>
                </div>

                <!-- Duration Picker -->
                <div class="space-y-3 pt-2">
                    <label class="block text-xs font-bold uppercase tracking-wider text-[#202124] text-center">
                        How long?
                    </label>
                    <div class="flex items-center justify-center gap-2.5">
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(1)" id="dur-btn-1" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 1 ? 'bg-[#FF6B2C] text-white border border-[#FF6B2C]' : 'border border-gray-200 text-gray-700 hover:bg-stone-50'}">
                            1 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(3)" id="dur-btn-3" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 3 ? 'bg-[#FF6B2C] text-white border border-[#FF6B2C]' : 'border border-gray-200 text-gray-700 hover:bg-stone-50'}">
                            3 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(5)" id="dur-btn-5" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 5 ? 'bg-[#FF6B2C] text-white border border-[#FF6B2C]' : 'border border-gray-200 text-gray-700 hover:bg-stone-50'}">
                            5 min
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice('custom')" id="dur-btn-custom" 
                                class="px-3.5 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50">
                            Custom
                        </button>
                    </div>

                    <div id="custom-duration-box" class="hidden text-center pt-2">
                        <label for="custom-duration-input" class="text-xs text-[#6F6B68] mr-2">Minutes:</label>
                        <input id="custom-duration-input" type="number" min="1" max="20" value="${selectedDuration}" 
                               onchange="window.TempoStressRelief.handleCustomDurationChange(this.value)"
                               class="w-16 px-2.5 py-1 text-xs border border-gray-300 rounded-lg text-center font-bold">
                    </div>
                </div>

                <!-- Action Button -->
                <div class="pt-2 flex justify-center">
                    <button onclick="window.TempoStressRelief.startTimedSession()" 
                            class="btn-primary w-full sm:w-auto px-8 py-3 rounded-xl font-bold text-sm shadow-md flex items-center justify-center space-x-2">
                        <span>Start →</span>
                    </button>
                </div>
            </div>
        `;
    }"""

# 6. startTimedSession
t_timed = """        container.innerHTML = `
            <div class="space-y-6 max-w-md mx-auto text-center py-2">
                <!-- Header -->
                <div class="space-y-1">
                    <span class="text-3xl">${activeMethod.icon}</span>
                    <h3 class="font-heading text-xl font-bold text-[#202124]">${activeMethod.title}</h3>
                    <p class="text-xs text-[#6F6B68]">${activeMethod.summary}</p>
                </div>"""

rep_timed = """        const isRec = isRecoveryMode();
        container.innerHTML = `
            <div class="space-y-6 max-w-md mx-auto text-center py-2">
                <!-- Header -->
                <div class="space-y-1">
                    ${isRec ? `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#FFE9DC] text-[#FF6B2C]">Active Session</span>` : `<span class="text-3xl">${activeMethod.icon}</span>`}
                    <h3 class="font-heading text-xl font-bold text-[#202124]">${activeMethod.title}</h3>
                    <p class="text-xs text-[#6F6B68]">${activeMethod.summary}</p>
                </div>"""

# 7. renderCheckpoint
t_checkpoint = """        container.innerHTML = `
            <div class="space-y-6 max-w-md mx-auto text-center py-4">
                <div class="w-14 h-14 rounded-2xl bg-emerald-50 text-emerald-600 border border-emerald-100 flex items-center justify-center mx-auto text-2xl shadow-sm">
                    ✨
                </div>

                <div class="space-y-1.5">
                    <h3 class="font-heading text-2xl font-bold text-[#202124]">How are you feeling now?</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">Take a breath and check in with your mind and body.</p>
                </div>

                <!-- Checkpoint 3 Action Buttons -->
                <div class="space-y-3 pt-2">
                    <!-- 1. Primary: I'm ready -->
                    <button onclick="window.TempoStressRelief.handleReady()" 
                            class="btn-primary w-full py-3.5 rounded-xl font-bold text-sm shadow-md flex items-center justify-center space-x-2 transition">
                        <span>I'm ready →</span>
                    </button>

                    <!-- 2. Secondary: Repeat -->
                    <button onclick="window.TempoStressRelief.handleRepeat()" 
                            class="w-full py-3 rounded-xl border border-gray-200 text-xs sm:text-sm font-semibold text-gray-700 bg-white hover:bg-stone-50 transition">
                        ${repeatActionText}
                    </button>

                    <!-- 3. Tertiary: Try something else -->
                    <button onclick="window.TempoStressRelief.renderLibrary()" 
                            class="w-full py-2.5 text-xs text-[#FF6B2C] hover:text-[#E8591C] font-semibold underline transition">
                        Try something else
                    </button>
                </div>
            </div>
        `;"""

rep_checkpoint = """        const isRec = isRecoveryMode();
        container.innerHTML = `
            <div class="space-y-6 max-w-md mx-auto text-center py-4">
                <div class="w-12 h-12 rounded-full ${isRec ? 'bg-[#FFE9DC] text-[#FF6B2C]' : 'bg-emerald-50 text-emerald-600 border border-emerald-100'} flex items-center justify-center mx-auto text-lg font-bold shadow-xs">
                    ${isRec ? '✓' : '✨'}
                </div>

                <div class="space-y-1.5">
                    <h3 class="font-heading text-2xl font-bold text-[#202124]">How are you feeling now?</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">Take a breath and check in with your mind and body.</p>
                </div>

                <!-- Checkpoint 3 Action Buttons -->
                <div class="space-y-3 pt-2">
                    <!-- 1. Primary: I'm ready -->
                    <button onclick="window.TempoStressRelief.handleReady()" 
                            class="btn-primary w-full py-3.5 rounded-xl font-bold text-sm shadow-xs flex items-center justify-center space-x-2 bg-[#FF6B2C] hover:bg-[#E8591C] text-white transition cursor-pointer">
                        <span>I'm ready →</span>
                    </button>

                    <!-- 2. Secondary: Repeat -->
                    <button onclick="window.TempoStressRelief.handleRepeat()" 
                            class="w-full py-3 rounded-xl border border-[#EAE4DF] text-xs sm:text-sm font-bold text-[#202124] bg-white hover:bg-[#F3F1EF] transition cursor-pointer">
                        ${repeatActionText}
                    </button>

                    <!-- 3. Tertiary: Try something else -->
                    <button onclick="window.TempoStressRelief.renderLibrary()" 
                            class="w-full py-2.5 text-xs text-[#FF6B2C] hover:text-[#E8591C] font-bold underline transition cursor-pointer">
                        Try something else
                    </button>
                </div>
            </div>
        `;"""

# Convert all targets and replacements to CRLF
def to_crlf(s):
    return s.replace("\r\n", "\n").replace("\n", "\r\n")

replacements = [
    (to_crlf(t_init), to_crlf(rep_init)),
    (to_crlf(t_openModal), to_crlf(rep_openModal)),
    (to_crlf(t_renderLib), to_crlf(rep_renderLib)),
    (to_crlf(t_breathing), to_crlf(rep_breathing)),
    (to_crlf(t_detail), to_crlf(rep_detail)),
    (to_crlf(t_timed), to_crlf(rep_timed)),
    (to_crlf(t_checkpoint), to_crlf(rep_checkpoint))
]

content = raw
for idx, (t, r) in enumerate(replacements):
    if t not in content:
        print(f"Error: target {idx + 1} not found!")
        exit(1)
    content = content.replace(t, r, 1)
    print(f"Replacement {idx + 1} succeeded.")

with open(path, "wb") as f:
    f.write(content.encode("utf-8"))

print("stressRelief.js updated successfully!")
