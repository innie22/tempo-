import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

file_path = 'stressRelief.js'

with open(file_path, 'rb') as f:
    content_bytes = f.read()

# Verify initial CRLF
initial_crlf = content_bytes.count(b'\r\n')
initial_lone_lf = content_bytes.count(b'\n') - initial_crlf
print(f"Initial CRLF: {initial_crlf}, Lone LF: {initial_lone_lf}")

content_str = content_bytes.decode('utf-8')

# 1. Add TEMPO_GAMES and GENTLE_MATCH_SYMBOLS after BREATHING_PHASES
target_phases = """    const BREATHING_PHASES = [
        { label: 'Breathe in gently', count: 4, scale: 1.35 },
        { label: 'Hold softly', count: 4, scale: 1.35 },
        { label: 'Breathe out slowly', count: 4, scale: 0.85 },
        { label: 'Rest before next breath', count: 4, scale: 0.85 }
    ];"""

replacement_phases = """    const BREATHING_PHASES = [
        { label: 'Breathe in gently', count: 4, scale: 1.35 },
        { label: 'Hold softly', count: 4, scale: 1.35 },
        { label: 'Breathe out slowly', count: 4, scale: 0.85 },
        { label: 'Rest before next breath', count: 4, scale: 0.85 }
    ];

    // Tempo Games Catalog (Audited: Gentle Match is the only implemented game in Tempo)
    const TEMPO_GAMES = [
        {
            id: 'gentle-match',
            name: 'Gentle Match',
            category: 'Memory Puzzle',
            duration: 'Untimed • 2–3 min',
            description: 'Find matching pairs of botanical and natural symbols at an unhurried pace. Zero timers, scores, or stress.',
            badgeColor: 'bg-[#ECC9BA] text-[#202124]'
        }
    ];

    // Minimal SVG nature symbols for Gentle Match (Strictly zero emojis)
    const GENTLE_MATCH_SYMBOLS = [
        {
            id: 'leaf',
            label: 'Botanical Leaf',
            svg: '<svg class="w-7 h-7 sm:w-8 sm:h-8 text-[#3B5C43]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6"/></svg>'
        },
        {
            id: 'cloud',
            label: 'Soft Cloud',
            svg: '<svg class="w-7 h-7 sm:w-8 sm:h-8 text-[#4A6A78]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></svg>'
        },
        {
            id: 'sun',
            label: 'Gentle Sun',
            svg: '<svg class="w-7 h-7 sm:w-8 sm:h-8 text-[#8EA28F]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>'
        },
        {
            id: 'moon',
            label: 'Crescent Moon',
            svg: '<svg class="w-7 h-7 sm:w-8 sm:h-8 text-[#4A6A78]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>'
        },
        {
            id: 'droplet',
            label: 'Water Drop',
            svg: '<svg class="w-7 h-7 sm:w-8 sm:h-8 text-[#4A6A78]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/></svg>'
        },
        {
            id: 'wind',
            label: 'Gentle Breeze',
            svg: '<svg class="w-7 h-7 sm:w-8 sm:h-8 text-[#3B5C43]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.7 7.7A2.5 2.5 0 1 1 20 10H2"/><path d="M14.7 17.7A2.5 2.5 0 1 0 17 15H2"/><path d="M9.6 13.7A2 2 0 1 1 11 12H2"/></svg>'
        }
    ];

    let gentleMatchState = {
        cards: [],
        flippedIndices: [],
        isProcessing: false,
        isCompleted: false
    };"""

# 2. Update renderLibrary() in Rmode
target_library_rec = """        if (isRec) {
            container.innerHTML = `
                <div class="space-y-6">
                    <!-- Header -->
                    <div class="space-y-1">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-[#4A6A78]">Quick Stress Relief</span>
                        <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Choose a grounding method</h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">Pick something small to try. A few minutes is enough to signal your nervous system.</p>
                    </div>

                    <!-- Duration Filter Pills (No Emojis!) -->
                    <div class="flex flex-wrap items-center gap-2">
                        ${filters.map(f => `
                            <button onclick="window.TempoStressRelief.setFilter('${f.key}')" 
                                    class="px-4 py-1.5 rounded-full text-xs transition cursor-pointer ${
                                        currentFilter === f.key 
                                            ? 'bg-[#8EA28F] text-white shadow-xs font-bold' 
                                            : 'bg-[#F3F1EF] text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/30 font-semibold'
                                    }">
                                ${f.label}
                            </button>
                        `).join('')}
                    </div>

                    <!-- Cards Grid (2-column on desktop, responsive stack, No Emojis!) -->
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-1">"""

replacement_library_rec = """        if (isRec) {
            container.innerHTML = `
                <div class="space-y-6">
                    <!-- Header -->
                    <div class="space-y-1">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-[#4A6A78]">Quick Stress Relief</span>
                        <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Choose a grounding method</h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">Pick something small to try. A few minutes is enough to signal your nervous system.</p>
                    </div>

                    <!-- Duration Filter Pills & Tempo Games Entry Pill (No Emojis!) -->
                    <div class="flex flex-wrap items-center gap-2">
                        ${filters.map(f => `
                            <button onclick="window.TempoStressRelief.setFilter('${f.key}')" 
                                    class="px-4 py-1.5 rounded-full text-xs transition cursor-pointer ${
                                        currentFilter === f.key 
                                            ? 'bg-[#8EA28F] text-white shadow-xs font-bold' 
                                            : 'bg-[#F3F1EF] text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/30 font-semibold'
                                    }">
                                ${f.label}
                            </button>
                        `).join('')}
                        <button type="button"
                                onclick="window.TempoStressRelief.openGamesHub()"
                                class="px-4 py-1.5 rounded-full text-xs transition cursor-pointer bg-[#ECC9BA] text-[#202124] hover:bg-[#E5BDB0] font-bold flex items-center space-x-1 shadow-xs ml-auto">
                            <span>Tempo Games</span>
                            <span>→</span>
                        </button>
                    </div>

                    <!-- Featured Tempo Games Activity Card (Visible on All Durations) -->
                    ${currentFilter === 'all' ? `
                        <div onclick="window.TempoStressRelief.openGamesHub()"
                             tabindex="0"
                             role="button"
                             onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();window.TempoStressRelief.openGamesHub();}"
                             class="p-4 sm:p-5 bg-[#ECC9BA]/25 border border-[#ECC9BA]/90 hover:border-[#8EA28F] rounded-2xl cursor-pointer transition hover:shadow-xs space-y-3 group flex flex-col sm:flex-row sm:items-center sm:justify-between">
                            <div class="space-y-1 sm:max-w-md">
                                <div class="flex items-center space-x-2">
                                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#93AFBC]/25 text-[#4A6A78]">
                                        Tempo Games
                                    </span>
                                    <span class="text-[10px] font-medium text-[#6F6B68]">Untimed • Mindful Pause</span>
                                </div>
                                <h4 class="font-heading text-base font-bold text-[#202124] group-hover:text-[#3B5C43] transition">
                                    Tempo Games
                                </h4>
                                <p class="text-xs text-[#6F6B68] leading-relaxed">
                                    Calm, low-pressure games designed to gently ground attention and ease mental fatigue.
                                </p>
                            </div>
                            <div class="pt-2 sm:pt-0 sm:pl-4 shrink-0 flex items-center">
                                <span class="px-4 py-2 bg-[#8EA28F] group-hover:bg-[#7D917E] text-white rounded-xl text-xs font-bold transition shadow-xs flex items-center space-x-1.5">
                                    <span>Explore Games</span>
                                    <span class="group-hover:translate-x-1 transition-transform">→</span>
                                </span>
                            </div>
                        </div>
                    ` : ''}

                    <!-- Cards Grid (2-column on desktop, responsive stack, No Emojis!) -->
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-1">"""

# 3. Add Games Hub, Launch, and Gentle Match functions right before formatMinutesSeconds
target_before_format = """    function formatMinutesSeconds(totalSec) {"""

games_functions = """    // =========================================================================
    // TEMPO GAMES SYSTEM (RMODE ONLY)
    // =========================================================================
    function openGamesHub() {
        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        const hasGames = TEMPO_GAMES && TEMPO_GAMES.length > 0;

        container.innerHTML = `
            <div class="space-y-6">
                <!-- Navigation & Header -->
                <div class="space-y-3">
                    <button type="button"
                            onclick="window.TempoStressRelief.renderLibrary()"
                            class="text-xs font-bold text-[#3B5C43] hover:text-[#202124] flex items-center space-x-1.5 transition cursor-pointer">
                        <span>←</span>
                        <span>Back to grounding methods</span>
                    </button>
                    <div class="space-y-1">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-[#4A6A78]">Tempo Games</span>
                        <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Mindful Break Games</h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">Simple, bounded activities to help you step away from stress without performance pressure.</p>
                    </div>
                </div>

                ${hasGames ? `
                    <!-- Games Selection Grid -->
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                        ${TEMPO_GAMES.map(g => `
                            <div class="p-5 bg-white border border-[#EAE4DF] hover:border-[#8EA28F] rounded-2xl transition hover:shadow-xs space-y-4 flex flex-col justify-between">
                                <div class="space-y-2.5">
                                    <div class="flex items-center justify-between">
                                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#ECC9BA] text-[#202124]">
                                            ${g.category}
                                        </span>
                                        <span class="text-[11px] font-medium text-[#6F6B68]">
                                            ${g.duration}
                                        </span>
                                    </div>
                                    <h4 class="font-heading text-base font-bold text-[#202124] leading-snug">
                                       ${g.name}
                                    </h4>
                                    <p class="text-xs text-[#6F6B68] leading-relaxed">
                                        ${g.description}
                                    </p>
                                </div>
                                <div class="pt-3 border-t border-[#F3F1EF] flex items-center justify-between">
                                    <span class="text-[11px] font-semibold text-[#4A6A78]">Bounded gentle pace</span>
                                    <button type="button"
                                            onclick="window.TempoStressRelief.launchGame('${g.id}')"
                                            class="px-4 py-2 bg-[#8EA28F] hover:bg-[#7D917E] text-white rounded-xl text-xs font-bold transition shadow-xs flex items-center space-x-1.5 cursor-pointer">
                                        <span>Play</span>
                                        <span>→</span>
                                    </button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : `
                    <!-- Empty State Fallback -->
                    <div class="p-8 text-center bg-white border border-[#EAE4DF] rounded-2xl space-y-3">
                        <div class="w-10 h-10 rounded-full bg-[#F3F1EF] text-[#6F6B68] flex items-center justify-center mx-auto text-sm font-bold">
                            —
                        </div>
                        <h4 class="font-heading text-base font-bold text-[#202124]">No games currently available</h4>
                        <p class="text-xs text-[#6F6B68] max-w-sm mx-auto">
                            More calm, mindful activities will arrive soon. In the meantime, explore our grounding methods.
                        </p>
                        <div class="pt-2">
                            <button type="button"
                                    onclick="window.TempoStressRelief.renderLibrary()"
                                    class="px-4 py-2 bg-[#8EA28F] hover:bg-[#7D917E] text-white rounded-xl text-xs font-bold transition shadow-xs cursor-pointer">
                                Return to grounding methods
                            </button>
                        </div>
                    </div>
                `}
            </div>
        `;
    }

    function launchGame(gameId) {
        if (gameId === 'gentle-match') {
            initGentleMatchGame();
            renderGentleMatchGame();
        }
    }

    function initGentleMatchGame() {
        const deck = [...GENTLE_MATCH_SYMBOLS, ...GENTLE_MATCH_SYMBOLS];
        for (let i = deck.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [deck[i], deck[j]] = [deck[j], deck[i]];
        }
        gentleMatchState = {
            cards: deck.map((item, index) => ({
                id: index,
                symbolId: item.id,
                label: item.label,
                svg: item.svg,
                isFlipped: false,
                isMatched: false
            })),
            flippedIndices: [],
            isProcessing: false,
            isCompleted: false
        };
    }

    function renderGentleMatchGame() {
        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        const game = gentleMatchState;
        if (!game) return;

        container.innerHTML = `
            <div class="space-y-5 text-center">
                <!-- Navigation Bar -->
                <div class="flex items-center justify-between pb-2 border-b border-[#F3F1EF]">
                    <button type="button"
                            onclick="window.TempoStressRelief.openGamesHub()"
                            class="text-xs font-bold text-[#3B5C43] hover:text-[#202124] flex items-center space-x-1.5 transition cursor-pointer">
                        <span>←</span>
                        <span>Back to Tempo Games</span>
                    </button>
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#ECC9BA] text-[#202124]">
                        Gentle Match
                    </span>
                </div>

                <!-- Title & Instructions -->
                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">Gentle Match</h3>
                    <p class="text-xs text-[#6F6B68]">Find all matching pairs at your own pace. A calm game for a calmer you.</p>
                </div>

                <!-- 4x3 Matching Grid (Zero performance pressure, no timer or score) -->
                <div class="grid grid-cols-4 gap-2.5 sm:gap-3.5 max-w-xs sm:max-w-md mx-auto py-2">
                    ${game.cards.map((card, idx) => `
                        <button type="button"
                                onclick="window.TempoStressRelief.handleGameCardClick(${idx})"
                                aria-label="${card.isFlipped || card.isMatched ? card.label : 'Hidden card'}"
                                class="w-16 h-16 sm:w-20 sm:h-20 rounded-2xl flex items-center justify-center transition-all duration-200 select-none ${
                                    card.isMatched 
                                        ? 'bg-[#8EA28F]/15 border-2 border-[#8EA28F] text-[#3B5C43] opacity-80 cursor-default shadow-xs'
                                        : (card.isFlipped 
                                            ? 'bg-[#ECC9BA]/35 border-2 border-[#8EA28F] text-[#4A6A78] shadow-xs scale-102'
                                            : 'bg-white hover:bg-[#F3F1EF]/60 border-2 border-[#EAE4DF] hover:border-[#93AFBC] cursor-pointer shadow-2xs')
                                }">
                            ${card.isFlipped || card.isMatched 
                                ? card.svg 
                                : '<svg class="w-5 h-5 text-[#93AFBC]/40" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="3"/><circle cx="6" cy="12" r="2"/><circle cx="18" cy="12" r="2"/></svg>'}
                        </button>
                    `).join('')}
                </div>

                <!-- Completion Status -->
                ${game.isCompleted ? `
                    <div class="p-4 sm:p-5 bg-[#8EA28F]/15 border border-[#8EA28F]/60 rounded-2xl space-y-3 max-w-sm mx-auto">
                        <div class="space-y-1">
                            <span class="text-xs font-bold text-[#3B5C43] block">All pairs matched</span>
                            <p class="text-xs text-[#6F6B68]">Take a slow, grounding breath and enjoy this restful moment.</p>
                        </div>
                        <div class="flex flex-wrap items-center justify-center gap-2 pt-1">
                            <button type="button"
                                    onclick="window.TempoStressRelief.restartGentleMatch()"
                                    class="px-3.5 py-2 rounded-xl border border-[#93AFBC]/60 bg-white text-[#202124] text-xs font-bold hover:bg-[#F3F1EF] transition cursor-pointer">
                                Another round
                            </button>
                            <button type="button"
                                    onclick="window.TempoStressRelief.openGamesHub()"
                                    class="px-3.5 py-2 rounded-xl border border-[#93AFBC]/60 bg-white text-[#202124] text-xs font-bold hover:bg-[#F3F1EF] transition cursor-pointer">
                                Back to games
                            </button>
                            <button type="button"
                                    onclick="window.TempoStressRelief.handleReady()"
                                    class="px-4 py-2 bg-[#8EA28F] hover:bg-[#7D917E] text-white rounded-xl text-xs font-bold transition shadow-xs cursor-pointer">
                                Done
                            </button>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    function handleGameCardClick(index) {
        if (!gentleMatchState || gentleMatchState.isProcessing) return;
        const card = gentleMatchState.cards[index];
        if (!card || card.isMatched || card.isFlipped) return;

        card.isFlipped = true;
        gentleMatchState.flippedIndices.push(index);

        if (gentleMatchState.flippedIndices.length === 2) {
            const idx1 = gentleMatchState.flippedIndices[0];
            const idx2 = gentleMatchState.flippedIndices[1];
            const card1 = gentleMatchState.cards[idx1];
            const card2 = gentleMatchState.cards[idx2];

            if (card1.symbolId === card2.symbolId) {
                card1.isMatched = true;
                card2.isMatched = true;
                gentleMatchState.flippedIndices = [];
                const allDone = gentleMatchState.cards.every(c => c.isMatched);
                if (allDone) {
                    gentleMatchState.isCompleted = true;
                }
                renderGentleMatchGame();
            } else {
                gentleMatchState.isProcessing = true;
                renderGentleMatchGame();
                setTimeout(() => {
                    card1.isFlipped = false;
                    card2.isFlipped = false;
                    gentleMatchState.flippedIndices = [];
                    gentleMatchState.isProcessing = false;
                    renderGentleMatchGame();
                }, 750);
            }
        } else {
            renderGentleMatchGame();
        }
    }

    function restartGentleMatch() {
        initGentleMatchGame();
        renderGentleMatchGame();
    }

    function formatMinutesSeconds(totalSec) {"""

# 4. Update the exports object
target_exports = """        renderCheckpoint,
        handleReady,
        handleRepeat
    };"""

replacement_exports = """        renderCheckpoint,
        handleReady,
        handleRepeat,
        openGamesHub,
        launchGame,
        initGentleMatchGame,
        renderGentleMatchGame,
        handleGameCardClick,
        restartGentleMatch
    };"""

# Normalize string comparisons by replacing CRLF with LF in python memory
content_lf = content_str.replace('\r\n', '\n')

assert target_phases.replace('\r\n', '\n') in content_lf, "Target 1 not found"
assert target_library_rec.replace('\r\n', '\n') in content_lf, "Target 2 not found"
assert target_before_format.replace('\r\n', '\n') in content_lf, "Target 3 not found"
assert target_exports.replace('\r\n', '\n') in content_lf, "Target 4 not found"

content_lf = content_lf.replace(target_phases.replace('\r\n', '\n'), replacement_phases.replace('\r\n', '\n'), 1)
content_lf = content_lf.replace(target_library_rec.replace('\r\n', '\n'), replacement_library_rec.replace('\r\n', '\n'), 1)
content_lf = content_lf.replace(target_before_format.replace('\r\n', '\n'), games_functions.replace('\r\n', '\n'), 1)
content_lf = content_lf.replace(target_exports.replace('\r\n', '\n'), replacement_exports.replace('\r\n', '\n'), 1)

# Convert all LFs back to pure CRLFs
new_crlf_content = content_lf.replace('\n', '\r\n')

with open(file_path, 'wb') as f:
    f.write(new_crlf_content.encode('utf-8'))

# Final check
with open(file_path, 'rb') as f:
    final_bytes = f.read()

final_crlf = final_bytes.count(b'\r\n')
final_lone_lf = final_bytes.count(b'\n') - final_crlf
print(f"Update successful! Final CRLF: {final_crlf}, Lone LF: {final_lone_lf}")
