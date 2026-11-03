with open('unclearMode.js', 'rb') as f:
    content = f.read().decode('utf-8')

# Target 1: Remove duplicate top navigation row
target_nav = """                <!-- Top Navigation Row: Return Home + Unclear Pill + ((SOS)) I don't feel safe -->
                <div class="flex items-center justify-between gap-4 pb-1">
                    <!-- Left: Return Home & Unclear Mode pill -->
                    <div class="flex items-center space-x-3">
                        <button type="button" 
                                onclick="window.TempoUnclearMode.returnToHome()"
                                class="px-5 py-2 rounded-full text-xs sm:text-sm font-bold text-[#5B5550] hover:text-[#202124] bg-white/90 hover:bg-white border border-[#E8D9CF] transition shadow-2xs flex items-center space-x-1.5 cursor-pointer"
                                title="Return Home">
                            <span>←</span>
                            <span>Return Home</span>
                        </button>

                        <div id="home-mode-selector-wrapper" class="relative inline-block text-left">
                            <button id="btn-home-mode-selector" 
                                    type="button" 
                                    onclick="window.TempoMode.toggleModeDropdown(event)" 
                                    class="px-7 py-2 rounded-full text-xs sm:text-sm font-extrabold bg-[#FFF6EF] text-[#C2785C] hover:bg-[#FDEBD0] border border-[#E2B7A0] transition flex items-center space-x-1 shadow-2xs cursor-pointer"
                                    aria-haspopup="true"
                                    aria-expanded="false"
                                    title="Switch Tempo Mode">
                                <span>Unclear</span>
                            </button>
                            <div id="home-mode-selector-dropdown" class="hidden absolute left-0 mt-2 w-72 sm:w-80 bg-white rounded-2xl shadow-xl border border-[#EAE4DF] z-50 overflow-hidden" role="menu"></div>
                        </div>
                    </div>

                    <!-- Right: ((SOS)) I don't feel safe -->
                    <button type="button"
                            onclick="window.TempoEmergencySupport.openSOS()"
                            class="px-5 sm:px-6 py-2 rounded-full text-xs sm:text-sm font-extrabold text-white bg-[#BD3022] hover:bg-[#A9271A] transition shadow-xs flex items-center space-x-2 cursor-pointer"
                            title="I don't feel safe">
                        <span class="tracking-widest font-black">((sos))</span>
                        <span>I don’t feel safe</span>
                    </button>
                </div>

"""

# Target 2: Remove bottom 3 cards
target_bottom_cards = """
                <!-- Bottom Tool Cards: Quick Relief, Learn & Solve, Tempo break -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
                    <!-- 1. Quick Relief -->
                    <div data-card="quick-relief"
                         onclick="if (window.TempoStressRelief && window.TempoStressRelief.openModal) { window.TempoStressRelief.openModal('unclear'); } else if (window.TempoTriage && window.TempoTriage.openQuickReliefModal) { window.TempoTriage.openQuickReliefModal(); }"
                         class="bg-[#D9E7E0] border border-[#BACAD0] rounded-[24px] overflow-hidden p-5 sm:p-6 flex items-center justify-between min-h-[160px] shadow-[0_4px_10px_-2px_rgba(75,55,40,0.05),0_10px_20px_-4px_rgba(75,55,40,0.08)] hover:shadow-md transition cursor-pointer group select-none relative"
                         title="Quick Relief">
                        <div class="flex-1 min-w-0 pr-2">
                            <h3 class="text-xl sm:text-2xl font-extrabold text-[#4A6356] mb-1 group-hover:text-[#384F43] transition">
                                Quick Relief
                            </h3>
                            <p class="text-xs sm:text-sm text-[#5C7568] leading-snug">
                                Quick ways to ease stress and feel better.
                            </p>
                        </div>
                        <img src="assets/quick-relief-mascot-transparent.png" alt="Quick Relief Mascot" class="h-20 sm:h-24 w-auto object-contain shrink-0 select-none pointer-events-none group-hover:scale-105 transition-transform" />
                    </div>

                    <!-- 2. Learn & Solve -->
                    <div data-card="learn-solve"
                         onclick="if (window.TempoApp) { window.TempoApp.navigateTo('learn'); } else { window.location.hash = '#learn'; }"
                         class="bg-[#FBEDD9] border border-[#DFCFC0] rounded-[24px] overflow-hidden p-5 sm:p-6 flex items-center justify-between min-h-[160px] shadow-[0_4px_10px_-2px_rgba(75,55,40,0.05),0_10px_20px_-4px_rgba(75,55,40,0.08)] hover:shadow-md transition cursor-pointer group select-none relative"
                         title="Learn & Solve">
                        <div class="flex-1 min-w-0 pr-2">
                            <h3 class="text-xl sm:text-2xl font-extrabold text-[#6D583F] mb-1 group-hover:text-[#5B4833] transition">
                                Learn &amp; Solve
                            </h3>
                            <p class="text-xs sm:text-sm text-[#7D6B54] leading-snug">
                                Tips and tools to help you cope.
                            </p>
                        </div>
                        <img src="assets/learn-solve-mascot.png" alt="Learn & Solve Mascot" class="h-20 sm:h-24 w-auto object-contain shrink-0 select-none pointer-events-none group-hover:scale-105 transition-transform" />
                    </div>

                    <!-- 3. Tempo break -->
                    <div data-card="tempo-break"
                         onclick="if (window.TempoTools && typeof window.TempoTools.openBreak === 'function') { window.TempoTools.openBreak(); } else if (window.TempoFocusZone) { window.TempoFocusZone.openQuickEntry(); }"
                         class="bg-[#D3DFE4] border border-[#BACAD0] rounded-[24px] overflow-hidden p-5 sm:p-6 flex items-center justify-between min-h-[160px] shadow-[0_4px_10px_-2px_rgba(75,55,40,0.05),0_10px_20px_-4px_rgba(75,55,40,0.08)] hover:shadow-md transition cursor-pointer group select-none relative"
                         title="Tempo break">
                        <div class="flex-1 min-w-0 pr-2">
                            <h3 class="text-xl sm:text-2xl font-extrabold text-[#3D4E56] mb-1 group-hover:text-[#2A373E] transition">
                                Tempo break
                            </h3>
                            <p class="text-xs sm:text-sm text-[#5B6C74] leading-snug">
                                Take a break with fun activities to unwind.
                            </p>
                        </div>
                        <img src="assets/tempo-break-mascot.png" alt="Tempo break Mascot" class="h-20 sm:h-24 w-auto object-contain shrink-0 select-none pointer-events-none group-hover:scale-105 transition-transform" />
                    </div>
                </div>"""

# Normalize target strings to match CRLF
target_nav_crlf = target_nav.replace('\r\n', '\n').replace('\n', '\r\n')
target_bottom_cards_crlf = target_bottom_cards.replace('\r\n', '\n').replace('\n', '\r\n')

print("target_nav in content:", target_nav_crlf in content)
print("target_bottom_cards in content:", target_bottom_cards_crlf in content)

if target_nav_crlf in content and target_bottom_cards_crlf in content:
    content = content.replace(target_nav_crlf, "")
    content = content.replace(target_bottom_cards_crlf, "")
    with open('unclearMode.js', 'wb') as f:
        f.write(content.encode('utf-8'))
    print("Successfully updated unclearMode.js")
else:
    print("Failed to find targets")
