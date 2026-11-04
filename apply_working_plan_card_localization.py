# -*- coding: utf-8 -*-

# 1. Update i18n.js
with open('i18n.js', 'r', encoding='utf-8') as f:
    i18n_text = f.read()

assert '\r\n' not in i18n_text, 'i18n.js has CRLF!'

old_vi_block = """                    workingPlanTitle: "Working Plan",
                    workingPlanFull: "Kế hoạch làm việc của bạn",
                    createNewTask: "Tạo task mới","""

new_vi_block = """                    workingPlanTitle: "Working Plan",
                    workingPlanFull: "Kế hoạch làm việc của bạn",
                    yourWorkingPlanUpper: "YOUR WORKING PLAN",
                    notSetUpYet: "Bạn chưa thiết lập kế hoạch làm việc",
                    notSetUpYetDesc: "Thiết lập kế hoạch làm việc để sắp xếp ngày của bạn hoặc thực hiện ngay một task khẩn cấp.",
                    setupMyPlan: "Setup my plan",
                    switchModeBtn: "Switch Mode",
                    statePlanIncomplete: "Bạn vẫn đang thiết lập kế hoạch.",
                    statePlanIncompleteDesc: "Kế hoạch khẩn cấp của bạn đang được thiết lập ở bước:",
                    createNewTask: "Tạo task mới","""

assert old_vi_block in i18n_text, "old_vi_block not found in i18n.js"
i18n_text = i18n_text.replace(old_vi_block, new_vi_block)

old_en_block = """                    workingPlanTitle: "Working Plan",
                    createNewTask: "Create a new task","""

new_en_block = """                    workingPlanTitle: "Working Plan",
                    yourWorkingPlanUpper: "YOUR WORKING PLAN",
                    notSetUpYet: "You haven't set up your working plan yet",
                    notSetUpYetDesc: "Set up your working plan to organize your day, or execute an urgent task immediately.",
                    setupMyPlan: "Setup my plan",
                    switchModeBtn: "Switch Mode",
                    statePlanIncomplete: "You are still setting up your plan.",
                    statePlanIncompleteDesc: "Your urgent plan setup is in progress at step:",
                    createNewTask: "Create a new task","""

assert old_en_block in i18n_text, "old_en_block not found in i18n.js"
i18n_text = i18n_text.replace(old_en_block, new_en_block)

with open('i18n.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(i18n_text)

print("Updated i18n.js successfully!")

# 2. Update mode.js
with open('mode.js', 'r', encoding='utf-8') as f:
    mode_text = f.read()

assert '\r\n' not in mode_text, 'mode.js has CRLF!'

old_mode_block = """                    <!-- Title Block -->
                    <div class="space-y-1">
                        <h3 class="font-heading text-2xl sm:text-[34px] font-extrabold text-[#484541] tracking-tight leading-snug">
                            ${isEntryStage
                                ? (window.t ? window.t('modes.urgent.notSetUpYet', {}, "Bạn chưa thiết lập kế hoạch làm việc") : "Bạn chưa thiết lập kế hoạch làm việc")
                                : (window.t ? window.t('modes.urgent.statePlanIncomplete', {}, "Bạn vẫn đang thiết lập kế hoạch.") : "Bạn vẫn đang thiết lập kế hoạch.")
                            }
                        </h3>
                        <span class="sr-only">Bạn vẫn đang thiết lập kế hoạch.</span>
                    </div>

                    <!-- Subtask / Step Row -->
                    <div class="flex items-center space-x-2.5 my-3">
                        <div class="w-4 h-4 rounded border-2 border-[#8C6C63]/60 bg-transparent flex items-center justify-center shrink-0"></div>
                        <p class="italic text-sm sm:text-base font-medium text-[#5D5954]">
                            ${isEntryStage
                                ? (window.t ? window.t('modes.urgent.notSetUpYetDesc', {}, 'Set up your working plan to organize your day, or execute an urgent task immediately.') : 'Set up your working plan to organize your day, or execute an urgent task immediately.')
                                : `${window.t ? window.t('modes.urgent.statePlanIncompleteDesc', {}, 'Your urgent plan setup is in progress at step:') : 'Your urgent plan setup is in progress at step:'} <strong class="font-semibold text-[#484541]">${escapeHTML(currentStageTitle)}</strong>.`
                            }
                        </p>
                    </div>
                </div>

                <!-- Action Buttons Row -->
                <div class="relative z-10 pt-4 border-t border-[#E8D9C5] flex flex-wrap items-center gap-3">
                    ${isEntryStage ? `
                        <button onclick="if (window.TempoUrmodeFlow && window.TempoUrmodeFlow.startSetupFlow) { window.TempoUrmodeFlow.startSetupFlow(); } else { window.TempoApp.navigateTo('emergency'); window.TempoEmergencyFlow.goToStage('reality-check'); }"
                                class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center space-x-2 transition cursor-pointer">
                            <span>Setup my plan</span>
                            <span>→</span>
                        </button>
                        <button id="btn-working-plan-create-task" onclick="if (window.TempoUrmodeFlow && window.TempoUrmodeFlow.openQuickTaskModal) { window.TempoUrmodeFlow.openQuickTaskModal(); }"
                                class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#B83D08] border border-[#FFD2BA] shadow-2xs inline-flex items-center space-x-1.5 transition cursor-pointer">
                            <span>⚡</span>
                            <span>${window.t ? window.t('modes.urgent.createNewTask', {}, isViLocale() ? 'Tạo task mới' : 'Create a new task') : (isViLocale() ? 'Tạo task mới' : 'Create a new task')}</span>
                        </button>
                    ` : `
                        <button onclick="window.TempoApp.navigateTo('emergency'); window.TempoEmergencyFlow.goToStage('${currentStage}');"
                                class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center space-x-2 transition cursor-pointer">
                            <span>${window.t ? window.t('modes.urgent.continueBuilding', {}, 'Continue building my plan') : 'Continue building my plan'}</span>
                            <span>→</span>
                        </button>
                        <button id="btn-working-plan-create-task" onclick="if (window.TempoUrmodeFlow && window.TempoUrmodeFlow.openQuickTaskModal) { window.TempoUrmodeFlow.openQuickTaskModal(); }"
                                class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#B83D08] border border-[#FFD2BA] shadow-2xs inline-flex items-center space-x-1.5 transition cursor-pointer">
                            <span>⚡</span>
                            <span>${window.t ? window.t('modes.urgent.createNewTask', {}, isViLocale() ? 'Tạo task mới' : 'Create a new task') : (isViLocale() ? 'Tạo task mới' : 'Create a new task')}</span>
                        </button>
                    `}
                    <button onclick="window.TempoMode.openChangeModeModal()" 
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center transition cursor-pointer">
                        ${window.t ? window.t('modes.selector.switchMode', {}, 'Switch mode') : 'Switch mode'}
                    </button>"""

new_mode_block = """                    <!-- Title Block -->
                    <div class="space-y-1">
                        <h3 class="font-heading text-2xl sm:text-[34px] font-extrabold text-[#484541] tracking-tight leading-snug">
                            ${isEntryStage
                                ? (window.t ? window.t('modes.urgent.notSetUpYet', {}, isViLocale() ? "Bạn chưa thiết lập kế hoạch làm việc" : "You haven't set up your working plan yet") : (isViLocale() ? "Bạn chưa thiết lập kế hoạch làm việc" : "You haven't set up your working plan yet"))
                                : (window.t ? window.t('modes.urgent.statePlanIncomplete', {}, isViLocale() ? "Bạn vẫn đang thiết lập kế hoạch." : "You are still setting up your plan.") : (isViLocale() ? "Bạn vẫn đang thiết lập kế hoạch." : "You are still setting up your plan."))
                            }
                        </h3>
                        <span class="sr-only">${isViLocale() ? (isEntryStage ? 'Bạn chưa thiết lập kế hoạch làm việc.' : 'Bạn vẫn đang thiết lập kế hoạch.') : (isEntryStage ? "You haven't set up your working plan yet." : 'Your plan setup is in progress.')}</span>
                    </div>

                    <!-- Subtask / Step Row -->
                    <div class="flex items-center space-x-2.5 my-3">
                        <div class="w-4 h-4 rounded border-2 border-[#8C6C63]/60 bg-transparent flex items-center justify-center shrink-0"></div>
                        <p class="italic text-sm sm:text-base font-medium text-[#5D5954]">
                            ${isEntryStage
                                ? (window.t ? window.t('modes.urgent.notSetUpYetDesc', {}, isViLocale() ? 'Thiết lập kế hoạch làm việc để sắp xếp ngày của bạn hoặc thực hiện ngay một task khẩn cấp.' : 'Set up your working plan to organize your day, or execute an urgent task immediately.') : (isViLocale() ? 'Thiết lập kế hoạch làm việc để sắp xếp ngày của bạn hoặc thực hiện ngay một task khẩn cấp.' : 'Set up your working plan to organize your day, or execute an urgent task immediately.'))
                                : `${window.t ? window.t('modes.urgent.statePlanIncompleteDesc', {}, isViLocale() ? 'Kế hoạch khẩn cấp của bạn đang được thiết lập ở bước:' : 'Your urgent plan setup is in progress at step:') : (isViLocale() ? 'Kế hoạch khẩn cấp của bạn đang được thiết lập ở bước:' : 'Your urgent plan setup is in progress at step:')} <strong class="font-semibold text-[#484541]">${escapeHTML(currentStageTitle)}</strong>.`
                            }
                        </p>
                    </div>
                </div>

                <!-- Action Buttons Row -->
                <div class="relative z-10 pt-4 border-t border-[#E8D9C5] flex flex-wrap items-center gap-3">
                    ${isEntryStage ? `
                        <button onclick="if (window.TempoUrmodeFlow && window.TempoUrmodeFlow.startSetupFlow) { window.TempoUrmodeFlow.startSetupFlow(); } else { window.TempoApp.navigateTo('emergency'); window.TempoEmergencyFlow.goToStage('reality-check'); }"
                                class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center space-x-2 transition cursor-pointer">
                            <span>${window.t ? window.t('modes.urgent.setupMyPlan', {}, 'Setup my plan') : 'Setup my plan'}</span>
                            <span>→</span>
                        </button>
                        <button id="btn-working-plan-create-task" onclick="if (window.TempoUrmodeFlow && window.TempoUrmodeFlow.openQuickTaskModal) { window.TempoUrmodeFlow.openQuickTaskModal(); }"
                                class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#B83D08] border border-[#FFD2BA] shadow-2xs inline-flex items-center space-x-1.5 transition cursor-pointer">
                            <span>⚡</span>
                            <span>${window.t ? window.t('modes.urgent.createNewTask', {}, isViLocale() ? 'Tạo task mới' : 'Create a new task') : (isViLocale() ? 'Tạo task mới' : 'Create a new task')}</span>
                        </button>
                    ` : `
                        <button onclick="window.TempoApp.navigateTo('emergency'); window.TempoEmergencyFlow.goToStage('${currentStage}');"
                                class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center space-x-2 transition cursor-pointer">
                            <span>${window.t ? window.t('modes.urgent.continueBuilding', {}, isViLocale() ? 'Tiếp tục thiết lập kế hoạch' : 'Continue building my plan') : (isViLocale() ? 'Tiếp tục thiết lập kế hoạch' : 'Continue building my plan')}</span>
                            <span>→</span>
                        </button>
                        <button id="btn-working-plan-create-task" onclick="if (window.TempoUrmodeFlow && window.TempoUrmodeFlow.openQuickTaskModal) { window.TempoUrmodeFlow.openQuickTaskModal(); }"
                                class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#B83D08] border border-[#FFD2BA] shadow-2xs inline-flex items-center space-x-1.5 transition cursor-pointer">
                            <span>⚡</span>
                            <span>${window.t ? window.t('modes.urgent.createNewTask', {}, isViLocale() ? 'Tạo task mới' : 'Create a new task') : (isViLocale() ? 'Tạo task mới' : 'Create a new task')}</span>
                        </button>
                    `}
                    <button onclick="window.TempoMode.openChangeModeModal()" 
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center transition cursor-pointer">
                        ${window.t ? window.t('modes.urgent.switchModeBtn', {}, 'Switch Mode') : 'Switch Mode'}
                    </button>"""

assert old_mode_block in mode_text, "old_mode_block not found in mode.js"
mode_text = mode_text.replace(old_mode_block, new_mode_block)

with open('mode.js', 'w', encoding='utf-8', newline='\n') as f:
    f.write(mode_text)

print("Updated mode.js successfully!")
