/**
 * Tempo Shared Ecosystem — Phase 1 & 3: Shared Tempo Tools Component
 * 
 * Centralized, reusable component providing the core Tempo utilities:
 * 1. 🎯 Focus Zone (with structured 45/15 rhythms and break intervals)
 * 2. 🌿 Quick Relief (micro-actions: 1m, 3m, 5m resets)
 * 3. 🫁 Breathing (2-minute Box Breathing)
 * 4. ☕ Tempo Break (standalone contained recovery pause without focus session)
 * 
 * Single source of truth mounted consistently across:
 * - Default Home
 * - Urgent Home
 * - Recovery Home
 */

window.TempoTools = (function() {
    'use strict';

    function openFocusZone() {
        if (window.TempoFocusZone && typeof window.TempoFocusZone.openQuickEntry === 'function') {
            window.TempoFocusZone.openQuickEntry();
        } else if (window.TempoTriage && typeof window.TempoTriage.launchFocusMode === 'function') {
            window.TempoTriage.launchFocusMode();
        }
    }

    function openQuickRelief() {
        if (window.TempoStressRelief && typeof window.TempoStressRelief.openModal === 'function') {
            window.TempoStressRelief.openModal();
        } else if (window.TempoTriage && typeof window.TempoTriage.openBoxBreathingModal === 'function') {
            window.TempoTriage.openBoxBreathingModal();
        }
    }

    function openBreathing() {
        if (window.TempoStressRelief && typeof window.TempoStressRelief.openBreathing === 'function') {
            window.TempoStressRelief.openBreathing();
        } else if (window.TempoTriage && typeof window.TempoTriage.openBoxBreathingModal === 'function') {
            window.TempoTriage.openBoxBreathingModal();
        }
    }

    function openBreak() {
        if (window.TempoFocusZone && typeof window.TempoFocusZone.openStandaloneBreak === 'function') {
            window.TempoFocusZone.openStandaloneBreak();
        } else if (window.TempoFocusZone && typeof window.TempoFocusZone.startBreakPeriod === 'function') {
            window.TempoFocusZone.startBreakPeriod();
        }
    }

    function renderSectionHTML() {
        return `
            <div class="tempo-tools-section space-y-4 pt-2 text-left">
                <!-- Section Header -->
                <div class="space-y-1">
                    <div class="flex items-center space-x-2">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">TEMPO TOOLS</span>
                    </div>
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124] tracking-tight">
                        Tempo Tools
                    </h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        A few things you can use whenever you need them.
                    </p>
                </div>

                <!-- 4 Tools Grid -->
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <!-- Tool 1: Focus Zone -->
                    <div class="bg-white border border-[#EAE4DF] hover:border-[#FF6B2C] rounded-3xl p-5 space-y-4 shadow-2xs flex flex-col justify-between transition text-left group">
                        <div class="space-y-2.5">
                            <div class="w-10 h-10 rounded-2xl bg-[#FFE9DC] text-[#FF6B2C] flex items-center justify-center text-lg font-bold shadow-xs">
                                🎯
                            </div>
                            <div class="space-y-1">
                                <h4 class="font-heading text-sm sm:text-base font-extrabold text-[#202124] group-hover:text-[#FF6B2C] transition">
                                    Focus Zone
                                </h4>
                                <p class="text-xs text-[#6F6B68] leading-relaxed">
                                    Focus at your own pace with structured intervals and intentional breaks.
                                </p>
                            </div>
                        </div>
                        <div class="pt-2">
                            <button type="button" onclick="window.TempoTools.openFocusZone()"
                                    class="btn-primary w-full py-2.5 px-3 rounded-xl text-xs font-bold shadow-xs transition cursor-pointer text-center">
                                Start Focus →
                            </button>
                        </div>
                    </div>

                    <!-- Tool 2: Quick Relief -->
                    <div class="bg-white border border-[#EAE4DF] hover:border-[#FF6B2C] rounded-3xl p-5 space-y-4 shadow-2xs flex flex-col justify-between transition text-left group">
                        <div class="space-y-2.5">
                            <div class="w-10 h-10 rounded-2xl bg-[#FFE9DC] text-[#B83D08] flex items-center justify-center text-lg font-bold shadow-xs">
                                🌿
                            </div>
                            <div class="space-y-1">
                                <h4 class="font-heading text-sm sm:text-base font-extrabold text-[#202124] group-hover:text-[#FF6B2C] transition">
                                    Quick Relief
                                </h4>
                                <p class="text-xs text-[#6F6B68] leading-relaxed">
                                    Calming micro-actions (1–5 min) to reset physical tension and settle racing thoughts.
                                </p>
                            </div>
                        </div>
                        <div class="pt-2">
                            <button type="button" onclick="window.TempoTools.openQuickRelief()"
                                    class="px-3 py-2.5 rounded-xl border border-[#FFD2BA] bg-[#FFF8F3] hover:bg-[#FFE9DC] text-[#B83D08] text-xs font-bold shadow-xs transition cursor-pointer w-full text-center">
                                Open Quick Relief →
                            </button>
                        </div>
                    </div>

                    <!-- Tool 3: Breathing -->
                    <div class="bg-white border border-[#EAE4DF] hover:border-[#166545] rounded-3xl p-5 space-y-4 shadow-2xs flex flex-col justify-between transition text-left group">
                        <div class="space-y-2.5">
                            <div class="w-10 h-10 rounded-2xl bg-[#EDF7F1] text-[#166545] flex items-center justify-center text-lg font-bold shadow-xs">
                                🫁
                            </div>
                            <div class="space-y-1">
                                <h4 class="font-heading text-sm sm:text-base font-extrabold text-[#202124] group-hover:text-[#166545] transition">
                                    Breathing
                                </h4>
                                <p class="text-xs text-[#6F6B68] leading-relaxed">
                                    A quick 2-minute box breathing reset to down-regulate your nervous system.
                                </p>
                            </div>
                        </div>
                        <div class="pt-2">
                            <button type="button" onclick="window.TempoTools.openBreathing()"
                                    class="px-3 py-2.5 rounded-xl border border-[#CDE9DA] bg-[#F4FAF6] hover:bg-[#EDF7F1] text-[#166545] text-xs font-bold shadow-xs transition cursor-pointer w-full text-center">
                                Start Breathing →
                            </button>
                        </div>
                    </div>

                    <!-- Tool 4: Tempo Break -->
                    <div class="bg-white border border-[#EAE4DF] hover:border-[#7E22CE] rounded-3xl p-5 space-y-4 shadow-2xs flex flex-col justify-between transition text-left group">
                        <div class="space-y-2.5">
                            <div class="w-10 h-10 rounded-2xl bg-[#FAF5FF] text-[#7E22CE] flex items-center justify-center text-lg font-bold shadow-xs">
                                ☕
                            </div>
                            <div class="space-y-1">
                                <h4 class="font-heading text-sm sm:text-base font-extrabold text-[#202124] group-hover:text-[#7E22CE] transition">
                                    Tempo Break
                                </h4>
                                <p class="text-xs text-[#6F6B68] leading-relaxed">
                                    Step away for a standalone recovery pause, gentle game, or light stretch.
                                </p>
                            </div>
                        </div>
                        <div class="pt-2">
                            <button type="button" onclick="window.TempoTools.openBreak()"
                                    class="px-3 py-2.5 rounded-xl border border-[#E9D5FF] bg-[#FAF5FF] hover:bg-[#F3E8FF] text-[#7E22CE] text-xs font-bold shadow-xs transition cursor-pointer w-full text-center">
                                Take a Break →
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    return {
        openFocusZone,
        openQuickRelief,
        openBreathing,
        openBreak,
        renderSectionHTML
    };
})();
