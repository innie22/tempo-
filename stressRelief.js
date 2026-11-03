/**
 * Tempo Quick Stress Relief & Breathing Reusable System
 * 
 * Reusable system callable from:
 * - Homepage Quick Tools (Breathing & Quick Stress Relief)
 * - Emergency Mode Reset Flow
 * - Future Focus Zone stress pauses
 * 
 * Flow:
 * Library / Direct Entry -> Method Detail -> Timed Session -> Checkpoint Panel
 * Checkpoint actions:
 * - I'm ready -> return to caller context (Emergency Reality Check or Home)
 * - Do this again / Keep breathing -> repeat method
 * - ${isVi() ? 'Thử phương pháp khác' : 'Try another method'} -> return to Method Library
 */

window.TempoStressRelief = (function() {
    function isVi() {
        return !window.TempoI18n || typeof window.TempoI18n.getLanguage !== 'function' || window.TempoI18n.getLanguage() === 'vi';
    }

    // 8 Core Stress-Relief Methods (Bilingual: vi + en)
    const METHODS = [
        {
            id: 'breathing',
            icon: '🫁',
            title_vi: 'Thở 4 nhịp (Box Breathing)',
            title_en: 'Box Breathing',
            summary_vi: 'Thực hiện theo nhịp 4 giây đều đặn để làm dịu hệ thần kinh.',
            summary_en: 'Follow a steady 4-second rhythm to calm your nervous system.',
            durationLabel_vi: '3 phút',
            durationLabel_en: '3 min',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: true,
            steps_vi: [
                'Hít vào nhẹ nhàng bằng mũi trong 4 giây.',
                'Giữ không khí êm ái trong phổi trong 4 giây.',
                'Thở ra từ từ và trọn vẹn qua miệng trong 4 giây.',
                'Nghỉ ngơi thả lỏng trong 4 giây trước nhịp thở tiếp theo.'
            ],
            steps_en: [
                'Inhale gently through your nose for 4 seconds.',
                'Hold breath smoothly for 4 seconds.',
                'Exhale slowly and completely through your mouth for 4 seconds.',
                'Rest and relax for 4 seconds before the next breath.'
            ]
        },
        {
            id: 'release-tension',
            icon: '💆',
            title_vi: 'Thả lỏng Cơ thể',
            title_en: 'Release Tension',
            summary_vi: 'Thư giãn cơ hàm, thả lỏng vai và hai bàn tay.',
            summary_en: 'Unclench your jaw, drop your shoulders, and relax your hands.',
            durationLabel_vi: '2–3 phút',
            durationLabel_en: '2–3 min',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: false,
            steps_vi: [
                'Chú ý đến hàm và răng. Hé nhẹ miệng và để lưỡi thả lỏng tự nhiên.',
                'Nhẹ nhàng nâng vai về phía tai khi hít vào chậm.',
                'Thở ra dứt khoát, để đôi vai buông thõng hoàn toàn.',
                'Mở rộng các ngón tay và thả lỏng, để hai bàn tay buông nghỉ êm ái.'
            ],
            steps_en: [
                'Notice your jaw and teeth. Slightly open your mouth and let your tongue rest.',
                'Gently lift your shoulders towards your ears with a slow inhale.',
                'Exhale firmly, letting your shoulders drop completely.',
                'Spread your fingers wide, then let your hands rest comfortably.'
            ]
        },
        {
            id: 'short-stretch',
            icon: '🧘',
            title_vi: 'Vận động Nhẹ',
            title_en: 'Short Stretch',
            summary_vi: 'Nhẹ nhàng giải tỏa căng cứng ở vùng cổ, cột sống và ngực.',
            summary_en: 'Gently relieve tension in your neck, spine, and chest.',
            durationLabel_vi: '3 phút',
            durationLabel_en: '3 min',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: false,
            steps_vi: [
                'Ngồi thẳng lưng. Nghiêng tai phải về vai phải trong 3 nhịp thở.',
                'Đổi bên và nghiêng tai trái về vai trái trong 3 nhịp thở.',
                'Đan các ngón tay sau đầu và nhẹ nhàng ngả ra sau để mở rộng lồng ngực.',
                'Thở ra và khom nhẹ lưng trên, cúi cằm về phía ngực.'
            ],
            steps_en: [
                'Sit tall. Tilt your right ear to your right shoulder for 3 breaths.',
                'Switch sides and tilt your left ear to your left shoulder for 3 breaths.',
                'Interlace fingers behind your head and gently lean back to open your chest.',
                'Exhale and round your upper back slightly, bringing chin towards chest.'
            ]
        },
        {
            id: 'sensory-grounding',
            icon: '👁️',
            title_vi: 'Định tâm 5 Giác quan',
            title_en: '5-Sense Grounding',
            summary_vi: 'Neo giữ sự chú ý với phương pháp quan sát xung quanh 5-4-3-2-1.',
            summary_en: 'Anchor your attention with the 5-4-3-2-1 sensory awareness technique.',
            durationLabel_vi: '3 phút',
            durationLabel_en: '3 min',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: false,
            steps_vi: [
                'Nhìn xung quanh: Gọi tên 5 điều bạn có thể nhìn thấy ngay lúc này.',
                'Cảm nhận cơ thể: Gọi tên 4 cảm giác tiếp xúc (chân chạm sàn, áo chạm tay).',
                'Lắng nghe: Gọi tên 3 âm thanh nhỏ xung quanh bạn.',
                'Cảm nhận 2 mùi hương hoặc bề mặt gần bạn, rồi hít 1 hơi thở sâu.'
            ],
            steps_en: [
                'Look around: Name 5 things you can see right now.',
                'Feel your body: Name 4 physical sensations (feet on floor, sleeve on skin).',
                'Listen closely: Name 3 subtle sounds around you.',
                'Notice 2 textures or scents near you, then take 1 slow deep breath.'
            ]
        },
        {
            id: 'step-away',
            icon: '🚪',
            title_vi: 'Rời xa Màn hình',
            title_en: 'Step Away',
            summary_vi: 'Cho đôi mắt nghỉ ngơi và bước hoàn toàn ra khỏi các thiết bị điện tử.',
            summary_en: 'Rest your eyes and step completely away from digital screens.',
            durationLabel_vi: '5 phút',
            durationLabel_en: '5 min',
            defaultDuration: 5,
            filterDuration: 5,
            isBreathing: false,
            steps_vi: [
                'Gập màn hình laptop lại và úp điện thoại xuống.',
                'Đứng dậy và bước ra khỏi góc làm việc của bạn.',
                'Nhìn ra ngoài cửa sổ hoặc điểm xa nhất trong phòng.',
                'Để ánh nhìn nghỉ ngơi êm dịu ở phía xa mà không tập trung vào chi tiết nhỏ.'
            ],
            steps_en: [
                'Close your laptop lid and turn your phone face-down.',
                'Stand up and walk away from your desk.',
                'Look out a window or at the furthest point in the room.',
                'Rest your gaze gently in the distance without focusing on any detail.'
            ]
        },
        {
            id: 'short-walk',
            icon: '🚶',
            title_vi: 'Đi dạo Ngắn',
            title_en: 'Short Walk',
            summary_vi: 'Đi bộ dọc hành lang để giải tỏa căng thẳng tích tụ trong cơ thể.',
            summary_en: 'Take a gentle walk down the hallway to shake off built-up stress.',
            durationLabel_vi: '5 phút',
            durationLabel_en: '5 min',
            defaultDuration: 5,
            filterDuration: 5,
            isBreathing: false,
            steps_vi: [
                'Rời khỏi phòng hiện tại mà không mang theo điện thoại.',
                'Đi dọc hành lang hoặc khuôn viên với tốc độ vừa phải, thoải mái.',
                'Chú ý cảm giác nhịp nhàng khi gót chân và bàn chân chạm đất.',
                'Để hai tay đung đưa tự nhiên và giữ nhịp thở thong thả.'
            ],
            steps_en: [
                'Step away from your room without taking your phone.',
                'Walk down the hallway or courtyard at an easy, comfortable pace.',
                'Notice the steady rhythm of your heels and feet meeting the floor.',
                'Let your arms swing naturally and keep your breathing easy.'
            ]
        },
        {
            id: 'write-worries',
            icon: '📝',
            title_vi: 'Viết ra Nỗi lo',
            title_en: 'Write Your Worries',
            summary_vi: 'Trút bỏ một nỗi bận tâm cụ thể lên một mẩu giấy.',
            summary_en: 'Release a specific worry onto a piece of scratch paper.',
            durationLabel_vi: '3 phút',
            durationLabel_en: '3 min',
            defaultDuration: 3,
            filterDuration: 3,
            isBreathing: false,
            steps_vi: [
                'Lấy một mẩu giấy nhỏ hoặc giấy ghi chú.',
                'Viết ra một câu: "Điều duy nhất đang khiến mình lo lắng nhất lúc này là gì?"',
                'Tự hỏi: "Mình có thể giải quyết việc này trong 15 phút tới không?"',
                'Nếu không, hãy viết: "Mình sẽ tạm gác việc này lại sau." Gấp mẩu giấy và để sang bên.'
            ],
            steps_en: [
                'Grab a small scrap of paper or sticky note.',
                'Write down one sentence: "What is the single thing worrying me most right now?"',
                'Ask yourself: "Can I resolve this in the next 15 minutes?"',
                'If not, write: "I will return to this later." Fold the note and set it aside.'
            ]
        },
        {
            id: 'get-water',
            icon: '💧',
            title_vi: 'Uống một Ly nước',
            title_en: 'Drink Water',
            summary_vi: 'Uống một ly nước mát thật chậm rãi và tỉnh thức.',
            summary_en: 'Drink a cool glass of water slowly and mindfully.',
            durationLabel_vi: '1–2 phút',
            durationLabel_en: '1–2 min',
            defaultDuration: 1,
            filterDuration: 1,
            isBreathing: false,
            steps_vi: [
                'Đi đến bồn rửa, vòi nước hoặc bình nước gần nhất.',
                'Rót một ly nước mát hoặc nước ở nhiệt độ phòng.',
                'Uống 3 ngụm nhỏ, cảm nhận dòng nước mát lành qua cổ họng.',
                'Thở ra một hơi thật dài trước khi quay trở lại bàn học.'
            ],
            steps_en: [
                'Walk over to the nearest sink, fountain, or water pitcher.',
                'Pour a cool or room-temperature glass of water.',
                'Take 3 slow sips, feeling the cool water soothing your throat.',
                'Take a long, slow exhale before heading back to your desk.'
            ]
        }
    ];

    // Define dynamic bilingual accessors on METHODS
    METHODS.forEach(m => {
        Object.defineProperties(m, {
            title: {
                get() { return isVi() ? (this.title_vi || 'Thở 4 nhịp') : (this.title_en || 'Box Breathing'); },
                configurable: true
            },
            summary: {
                get() { return isVi() ? (this.summary_vi || '') : (this.summary_en || ''); },
                configurable: true
            },
            durationLabel: {
                get() { return isVi() ? (this.durationLabel_vi || '') : (this.durationLabel_en || ''); },
                configurable: true
            },
            steps: {
                get() { return isVi() ? (this.steps_vi || []) : (this.steps_en || []); },
                configurable: true
            }
        });
    });

    // State Variables
    let activeContext = 'home'; // 'home' | 'emergency'
    let onReadyCallback = null;
    let onCloseCallback = null;
    let activeMethod = METHODS[0]; // defaults to Breathing
    let selectedDuration = 3; // minutes
    let currentFilter = 'all'; // 'all' | '1' | '3' | '5' | '10'

    // Timer and Interval References
    let sessionTimer = null;
    let sessionRemainingSeconds = 180;
    let sessionIsPaused = false;
    let breathingInterval = null;
    let breathingPhaseIndex = 0;
    let breathingPhaseSeconds = 4;

    let currentView = 'library'; // 'library' | 'breathing' | 'detail' | 'checkpoint' | 'games_hub' | 'gentle_match'

    const BREATHING_PHASES = [
        { label_vi: 'Hít vào nhẹ nhàng', label_en: 'Inhale gently', count: 4, scale: 1.35 },
        { label_vi: 'Giữ hơi thở êm dịu', label_en: 'Hold breath gently', count: 4, scale: 1.35 },
        { label_vi: 'Thở ra từ từ', label_en: 'Exhale slowly', count: 4, scale: 0.85 },
        { label_vi: 'Nghỉ trước nhịp thở tiếp theo', label_en: 'Rest before next breath', count: 4, scale: 0.85 }
    ];
    BREATHING_PHASES.forEach(p => {
        Object.defineProperty(p, 'label', {
            get() { return isVi() ? this.label_vi : this.label_en; },
            configurable: true
        });
    });

    // Tempo Games Catalog (Audited: Gentle Match is the only implemented game in Tempo)
    const TEMPO_GAMES = [
        {
            id: 'gentle-match',
            name_vi: 'Ghép cặp Nhẹ nhàng',
            name_en: 'Gentle Match',
            category_vi: 'Giải đố Trí nhớ',
            category_en: 'Memory Puzzle',
            duration_vi: 'Không giới hạn • 2–3 phút',
            duration_en: 'Untimed • 2–3 min',
            description_vi: 'Tìm các cặp biểu tượng tự nhiên và cây cỏ theo nhịp độ của riêng bạn. Không tính giờ, không điểm số, không áp lực.',
            description_en: 'Match nature and plant symbols at your own pace. No timers, no scoring, zero pressure.',
            badgeColor: 'bg-[#ECC9BA] text-[#202124]'
        }
    ];
    TEMPO_GAMES.forEach(g => {
        Object.defineProperties(g, {
            name: { get() { return isVi() ? this.name_vi : this.name_en; }, configurable: true },
            category: { get() { return isVi() ? this.category_vi : this.category_en; }, configurable: true },
            duration: { get() { return isVi() ? this.duration_vi : this.duration_en; }, configurable: true },
            description: { get() { return isVi() ? this.description_vi : this.description_en; }, configurable: true }
        });
    });

    // Minimal SVG nature symbols for Gentle Match (Strictly zero emojis)
    const GENTLE_MATCH_SYMBOLS = [
        {
            id: 'leaf',
            label_vi: 'Lá cây',
            label_en: 'Leaf',
            svg: '<svg class="w-7 h-7 sm:w-8 sm:h-8 text-[#3B5C43]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/><path d="M2 21c0-3 1.85-5.36 5.08-6"/></svg>'
        },
        {
            id: 'cloud',
            label_vi: 'Đám mây',
            label_en: 'Cloud',
            svg: '<svg class="w-7 h-7 sm:w-8 sm:h-8 text-[#4A6A78]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/></svg>'
        },
        {
            id: 'sun',
            label_vi: 'Mặt trời',
            label_en: 'Sun',
            svg: '<svg class="w-7 h-7 sm:w-8 sm:h-8 text-[#8EA28F]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>'
        },
        {
            id: 'moon',
            label_vi: 'Mặt trăng',
            label_en: 'Moon',
            svg: '<svg class="w-7 h-7 sm:w-8 sm:h-8 text-[#4A6A78]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>'
        },
        {
            id: 'droplet',
            label_vi: 'Giọt nước',
            label_en: 'Droplet',
            svg: '<svg class="w-7 h-7 sm:w-8 sm:h-8 text-[#4A6A78]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/></svg>'
        },
        {
            id: 'wind',
            label_vi: 'Gió nhẹ',
            label_en: 'Breeze',
            svg: '<svg class="w-7 h-7 sm:w-8 sm:h-8 text-[#3B5C43]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.7 7.7A2.5 2.5 0 1 1 20 10H2"/><path d="M14.7 17.7A2.5 2.5 0 1 0 17 15H2"/><path d="M9.6 13.7A2 2 0 1 1 11 12H2"/></svg>'
        }
    ];
    GENTLE_MATCH_SYMBOLS.forEach(s => {
        Object.defineProperty(s, 'label', {
            get() { return isVi() ? this.label_vi : this.label_en; },
            configurable: true
        });
    });

    let gentleMatchState = {
        cards: [],
        flippedIndices: [],
        isProcessing: false,
        isCompleted: false
    };

    function isRecoveryMode() {
        return true;
    }

    function init() {
        bindEvents();
        if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
            window.TempoI18n.onLanguageChange(() => {
                const modal = document.getElementById('modal-quick-stress-relief');
                if (modal && !modal.classList.contains('hidden')) {
                    if (currentView === 'games_hub') {
                        openGamesHub();
                    } else if (currentView === 'gentle_match') {
                        renderGentleMatchGame();
                    } else if (currentView === 'detail' && activeMethod) {
                        renderMethodDetail(activeMethod);
                    } else if (currentView === 'breathing') {
                        renderBreathingSetup();
                    } else if (currentView === 'checkpoint') {
                        renderCheckpoint();
                    } else {
                        renderLibrary();
                    }
                }
            });
        }
    }

    function bindEvents() {
        const closeBtn = document.getElementById('btn-close-stress-relief');
        if (closeBtn) {
            closeBtn.addEventListener('click', closeModal);
        }

        // Close on backdrop click
        const modal = document.getElementById('modal-quick-stress-relief');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    closeModal();
                }
            });
        }

        // Close on Escape key
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal && !modal.classList.contains('hidden')) {
                closeModal();
            }
        });
    }

    /**
     * Open Breathing directly (used by Emergency Mode Reset & Quick Tools Breathing)
     */
    function openBreathing(options = {}) {
        let ctx = options.context;
        if (!ctx) {
            if (window.TempoMode && typeof window.TempoMode.getMode === 'function') {
                const mode = window.TempoMode.getMode();
                ctx = mode === 'emergency' ? 'emergency' : (mode === 'recovery' ? 'recovery' : 'home');
            } else {
                ctx = 'home';
            }
        }
        activeContext = ctx;
        onReadyCallback = options.onReady || null;
        onCloseCallback = options.onClose || null;
        activeMethod = METHODS.find(m => m.id === 'breathing') || METHODS[0];
        selectedDuration = 3;

        stopAllTimers();
        openModalWrapper();
        renderBreathingSetup();
    }

    /**
     * Open Method Library (used by Homepage Quick Tools & "${isVi() ? 'Thử phương pháp khác' : 'Try another method'}")
     */
    function openLibrary(options = {}) {
        let ctx = options.context;
        if (!ctx) {
            if (activeContext && activeContext !== 'home') {
                ctx = activeContext;
            } else if (window.TempoMode && typeof window.TempoMode.getMode === 'function') {
                const mode = window.TempoMode.getMode();
                ctx = mode === 'emergency' ? 'emergency' : (mode === 'recovery' ? 'recovery' : 'home');
            } else {
                ctx = 'home';
            }
        }
        activeContext = ctx;
        if (options.onReady) {
            onReadyCallback = options.onReady;
        }
        if (options.onClose) {
            onCloseCallback = options.onClose;
        }

        stopAllTimers();
        openModalWrapper();
        renderLibrary();
    }

    /**
     * Backwards-compatible alias for Quick Tools
     */
    function openModal(defaultFilter = 'all', options = {}) {
        currentFilter = defaultFilter;
        let ctx = options.context;
        if (!ctx) {
            if (window.TempoMode && typeof window.TempoMode.getMode === 'function') {
                const mode = window.TempoMode.getMode();
                ctx = mode === 'emergency' ? 'emergency' : (mode === 'recovery' ? 'recovery' : 'home');
            } else {
                ctx = 'home';
            }
        }
        openLibrary({ context: ctx });
    }

    function openModalWrapper() {
        const modal = document.getElementById('modal-quick-stress-relief');
        if (!modal) return;
        
        const card = modal.querySelector('.tempo-card');
        const badge = modal.querySelector('span.uppercase.tracking-wider');
        
        if (card) {
            card.className = 'tempo-card max-w-2xl w-full my-auto max-h-[92vh] overflow-y-auto bg-[#FFF9F4] rounded-2xl sm:rounded-[28px] p-5 sm:p-8 space-y-4 relative shadow-xl border border-[#ECC9BA]/60';
        }
        
        if (badge) {
            badge.className = 'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-[#ECC9BA] text-[#202124]';
            badge.textContent = 'Grounded Pause';
        }

        const closeBtn = document.getElementById('btn-close-stress-relief');
        if (closeBtn) {
            closeBtn.className = 'text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/30 p-2 rounded-xl text-lg transition shrink-0';
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
            const closeBtn = document.getElementById('btn-close-stress-relief');
            if (card) card.className = 'tempo-card max-w-2xl w-full my-auto max-h-[92vh] overflow-y-auto bg-[#FFF9F4] rounded-2xl sm:rounded-[28px] p-5 sm:p-8 space-y-4 relative shadow-xl border border-[#ECC9BA]/60';
            if (badge) {
                badge.className = 'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-[#ECC9BA] text-[#202124]';
                badge.textContent = 'Grounded Pause';
            }
            if (closeBtn) closeBtn.className = 'text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/30 p-2 rounded-xl text-lg transition shrink-0';
        }
        document.body.classList.remove('overflow-hidden');
        if (typeof onClose === 'function') {
            onClose();
        } else if (ctx === 'emergency_reset' && window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.showResetPopup === 'function') {
            window.TempoUrmodeFlow.showResetPopup();
        }
    }

    function stopAllTimers() {
        if (sessionTimer) {
            clearInterval(sessionTimer);
            sessionTimer = null;
        }
        if (breathingInterval) {
            clearInterval(breathingInterval);
            breathingInterval = null;
        }
        sessionIsPaused = false;
    }

    // =========================================================================
    // VIEW 1: METHOD LIBRARY VIEW
    // =========================================================================
    function renderLibrary() {
        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        const isRec = isRecoveryMode();

                currentView = 'library';
        const filters = isRec ? [
            { key: 'all', label: isVi() ? 'Tất cả thời lượng' : 'All durations' },
            { key: '1', label: isVi() ? '1 phút' : '1 min' },
            { key: '3', label: isVi() ? '3 phút' : '3 min' },
            { key: '5', label: isVi() ? '5 phút' : '5 min' }
        ] : [
            { key: 'all', label: isVi() ? 'Tất cả thời lượng' : 'All durations' },
            { key: '1', label: isVi() ? '⚡ 1 phút' : '⚡ 1 min' },
            { key: '3', label: isVi() ? '🌿 3 phút' : '🌿 3 min' },
            { key: '5', label: isVi() ? '🚶 5 phút' : '🚶 5 min' }
        ];

        const filtered = currentFilter === 'all'
            ? METHODS
            : METHODS.filter(m => String(m.filterDuration) === currentFilter);

        if (isRec) {
            container.innerHTML = `
                <div class="space-y-6">
                    <!-- Header -->
                    <div class="space-y-1">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-[#4A6A78]">${isVi() ? 'Giải tỏa Căng thẳng Nhanh' : 'Quick Stress Relief'}</span>
                        <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">${isVi() ? 'Chọn phương pháp tĩnh tâm' : 'Choose a Grounding Method'}</h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">${isVi() ? 'Chọn một hành động nhỏ để thử. Chỉ vài phút là đủ để xoa dịu hệ thần kinh của bạn.' : 'Pick one small reset action. Even a few minutes can help calm your nervous system.'}</p>
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
                            <span>${isVi() ? 'Trò chơi Tempo' : 'Tempo Games'}</span>
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
                                    <span class="text-[10px] font-medium text-[#6F6B68]">${isVi() ? 'Không giới hạn • Khoảng dừng thư thái' : 'Untimed • Gentle break'}</span>
                                </div>
                                <h4 class="font-heading text-base font-bold text-[#202124] group-hover:text-[#3B5C43] transition">
                                    Tempo Games
                                </h4>
                                <p class="text-xs text-[#6F6B68] leading-relaxed">
                                    ${isVi() ? 'Các trò chơi nhẹ nhàng, không áp lực giúp bạn định tâm và giảm mệt mỏi tinh thần.' : 'Gentle, low-pressure games designed to ground you and reduce mental fatigue.'}
                                </p>
                            </div>
                            <div class="pt-2 sm:pt-0 sm:pl-4 shrink-0 flex items-center">
                                <span class="px-4 py-2 bg-[#8EA28F] group-hover:bg-[#7D917E] text-white rounded-xl text-xs font-bold transition shadow-xs flex items-center space-x-1.5">
                                    <span>${isVi() ? 'Khám phá Trò chơi' : 'Explore Games'}</span>
                                    <span class="group-hover:translate-x-1 transition-transform">→</span>
                                </span>
                            </div>
                        </div>
                    ` : ''}

                    <!-- Cards Grid (2-column on desktop, responsive stack, No Emojis!) -->
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-1">
                        ${filtered.map(m => `
                            <div onclick="window.TempoStressRelief.selectMethod('${m.id}')"
                                 tabindex="0"
                                 role="button"
                                 onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();window.TempoStressRelief.selectMethod('${m.id}');}"
                                 class="p-4 sm:p-5 bg-white border border-[#EAE4DF] hover:border-[#8EA28F] rounded-2xl cursor-pointer transition hover:shadow-xs space-y-3 group flex flex-col justify-between">
                                <div class="space-y-2">
                                    <div class="flex items-center justify-between">
                                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#ECC9BA] text-[#202124]">
                                            ${m.durationLabel}
                                        </span>
                                    </div>
                                    <h4 class="font-heading text-sm sm:text-[15px] font-bold text-[#202124] group-hover:text-[#3B5C43] transition leading-snug">
                                        ${m.title}
                                    </h4>
                                    <p class="text-xs text-[#6F6B68] leading-relaxed line-clamp-2">
                                        ${m.summary}
                                    </p>
                                </div>
                                <div class="pt-2.5 flex items-center justify-between text-xs font-bold border-t border-[#F3F1EF] text-[#3B5C43]">
                                    <span>${isVi() ? 'Bắt đầu hành động này' : 'Start this action'}</span>
                                    <span class="text-[#8EA28F] group-hover:translate-x-1 transition-transform">→</span>
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
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">${isVi() ? 'Chọn phương pháp tĩnh tâm' : 'Choose a Grounding Method'}</h3>
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
                                <span>${isVi() ? 'Bắt đầu hành động này' : 'Start this action'}</span>
                                <span class="group-hover:translate-x-1 transition-transform">→</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    function setFilter(filterKey) {
        currentFilter = filterKey;
        renderLibrary();
    }

    function selectMethod(methodId) {
        const method = METHODS.find(m => m.id === methodId);
        if (!method) return;
        activeMethod = method;

        if (method.isBreathing) {
            renderBreathingSetup();
        } else {
            renderMethodDetail(method);
        }
    }

    // =========================================================================
    // VIEW 2: BREATHING SETUP VIEW (Default for Reset)
    // =========================================================================
    function renderBreathingSetup() {
        currentView = 'breathing';
        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        selectedDuration = 3;
        const isRec = isRecoveryMode();

        if (isRec) {
            container.innerHTML = `
                <div class="space-y-6 max-w-lg mx-auto py-2">
                    <!-- Header -->
                    <div class="text-center space-y-1.5">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-[#4A6A78]">${isVi() ? 'Bài tập thở' : 'Breathing Exercise'}</span>
                        <h3 class="font-heading text-2xl font-bold text-[#202124]">${isVi() ? 'Lấy lại Nhịp điệu với Box Breathing' : 'Regain Calm with Box Breathing'}</h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68]">${isVi() ? 'Dành vài phút và thở theo nhịp điệu êm dịu.' : 'Take a few minutes and follow the rhythm.'}</p>
                    </div>

                    <!-- Explanation Box -->
                    <div class="p-4 bg-[#ECC9BA]/25 border border-[#ECC9BA]/70 rounded-2xl text-xs text-[#6F6B68] leading-relaxed space-y-2">
                        <p class="font-bold text-[#202124]">${isVi() ? 'Cách thức hoạt động:' : 'How it works:'}</p>
                        <p>${isVi() ? 'Hít vào (4s) • Giữ hơi (4s) • Thở ra (4s) • Nghỉ (4s). Nhịp thở đều đặn này giúp nhịp tim và hệ thần kinh tự nhiên lắng dịu.' : 'Inhale (4s) • Hold (4s) • Exhale (4s) • Rest (4s). This equal cadence helps your heart rate and nervous system downshift naturally.'}</p>
                    </div>

                    <!-- Duration Picker -->
                    <div class="space-y-3 pt-1">
                        <label class="block text-xs font-bold uppercase tracking-wider text-[#202124] text-center">
                            ${isVi() ? 'Chọn thời lượng:' : 'Select Duration:'}
                        </label>
                        <div class="flex items-center justify-center gap-2.5">
                            <button type="button" onclick="window.TempoStressRelief.setDurationChoice(1)" id="dur-btn-1" 
                                    class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 1 ? 'bg-[#8EA28F] text-white border border-[#8EA28F] shadow-xs' : 'border border-[#EAE4DF] text-[#202124] bg-white hover:bg-[#F3F1EF]'}">
                                ${isVi() ? '1 phút' : '1 min'}
                            </button>
                            <button type="button" onclick="window.TempoStressRelief.setDurationChoice(3)" id="dur-btn-3" 
                                    class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 3 ? 'bg-[#8EA28F] text-white border border-[#8EA28F] shadow-xs' : 'border border-[#EAE4DF] text-[#202124] bg-white hover:bg-[#F3F1EF]'}">
                                ${isVi() ? '3 phút' : '3 min'}
                            </button>
                            <button type="button" onclick="window.TempoStressRelief.setDurationChoice(5)" id="dur-btn-5" 
                                    class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 5 ? 'bg-[#8EA28F] text-white border border-[#8EA28F] shadow-xs' : 'border border-[#EAE4DF] text-[#202124] bg-white hover:bg-[#F3F1EF]'}">
                                ${isVi() ? '5 phút' : '5 min'}
                            </button>
                            <button type="button" onclick="window.TempoStressRelief.setDurationChoice('custom')" id="dur-btn-custom" 
                                    class="px-3.5 py-2 rounded-xl text-xs font-bold transition border border-[#EAE4DF] text-[#202124] bg-white hover:bg-[#F3F1EF]">
                                ${isVi() ? 'Tùy chỉnh' : 'Custom'}
                            </button>
                        </div>

                        <!-- ${isVi() ? 'Tùy chỉnh' : 'Custom'} Duration Input (hidden by default) -->
                        <div id="custom-duration-box" class="hidden text-center pt-2">
                            <label for="custom-duration-input" class="text-xs text-[#6F6B68] mr-2">${isVi() ? 'Số phút:' : 'Minutes:'}</label>
                            <input id="custom-duration-input" type="number" min="1" max="20" value="4" 
                                   onchange="window.TempoStressRelief.handleCustomDurationChange(this.value)"
                                   class="w-16 px-2.5 py-1 text-xs border border-[#EAE4DF] rounded-lg text-center font-bold text-[#202124] focus:border-[#8EA28F] focus:outline-hidden">
                        </div>
                    </div>

                    <!-- Action Buttons -->
                    <div class="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
                        <button onclick="window.TempoStressRelief.startBreathingSession()" 
                                class="btn-primary w-full sm:w-auto px-8 py-3 rounded-xl font-bold text-sm shadow-xs flex items-center justify-center space-x-2 bg-[#8EA28F] hover:bg-[#7D917E] text-white transition cursor-pointer">
                            <span>${isVi() ? 'Bắt đầu bài tập thở →' : 'Start Breathing →'}</span>
                        </button>
                        <button onclick="window.TempoStressRelief.renderLibrary()" 
                                class="w-full sm:w-auto px-5 py-3 rounded-xl border border-[#93AFBC]/60 text-xs font-bold text-[#202124] bg-white hover:bg-[#F3F1EF] transition cursor-pointer">
                            ${isVi() ? 'Xem phương pháp khác' : 'View Other Methods'}
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
                    <h3 class="font-heading text-2xl font-bold text-[#202124]">${isVi() ? 'Lấy lại Nhịp điệu với Box Breathing' : 'Regain Calm with Box Breathing'}</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">${isVi() ? 'Dành vài phút và thở theo nhịp điệu êm dịu.' : 'Take a few minutes and follow the rhythm.'}</p>
                </div>

                <!-- Explanation Box -->
                <div class="p-4 bg-[#FFF8F2] border border-[#FFD2BA]/60 rounded-2xl text-xs text-[#6F6B68] leading-relaxed space-y-2">
                    <p class="font-semibold text-[#202124]">How it works:</p>
                    <p>${isVi() ? 'Hít vào (4s) • Giữ hơi (4s) • Thở ra (4s) • Nghỉ (4s). Nhịp thở đều đặn này giúp nhịp tim và hệ thần kinh tự nhiên lắng dịu.' : 'Inhale (4s) • Hold (4s) • Exhale (4s) • Rest (4s). This equal cadence helps your heart rate and nervous system downshift naturally.'}</p>
                </div>

                <!-- Duration Picker -->
                <div class="space-y-3 pt-1">
                    <label class="block text-xs font-bold uppercase tracking-wider text-[#202124] text-center">
                        ${isVi() ? 'Chọn thời lượng:' : 'Select Duration:'}
                    </label>
                    <div class="flex items-center justify-center gap-2.5">
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(1)" id="dur-btn-1" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50">
                            ${isVi() ? '1 phút' : '1 min'}
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(3)" id="dur-btn-3" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition bg-[#FF6B2C] text-white border border-[#FF6B2C] shadow-sm">
                            ${isVi() ? '3 phút' : '3 min'}
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(5)" id="dur-btn-5" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50">
                            ${isVi() ? '5 phút' : '5 min'}
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice('custom')" id="dur-btn-custom" 
                                class="px-3.5 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50">
                            ${isVi() ? 'Tùy chỉnh' : 'Custom'}
                        </button>
                    </div>

                    <!-- ${isVi() ? 'Tùy chỉnh' : 'Custom'} Duration Input (hidden by default) -->
                    <div id="custom-duration-box" class="hidden text-center pt-2">
                        <label for="custom-duration-input" class="text-xs text-[#6F6B68] mr-2">${isVi() ? 'Số phút:' : 'Minutes:'}</label>
                        <input id="custom-duration-input" type="number" min="1" max="20" value="4" 
                               onchange="window.TempoStressRelief.handleCustomDurationChange(this.value)"
                               class="w-16 px-2.5 py-1 text-xs border border-gray-300 rounded-lg text-center font-bold">
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
                    <button onclick="window.TempoStressRelief.startBreathingSession()" 
                            class="btn-primary w-full sm:w-auto px-8 py-3 rounded-xl font-bold text-sm shadow-md flex items-center justify-center space-x-2">
                        <span>${isVi() ? 'Bắt đầu bài tập thở →' : 'Start Breathing →'}</span>
                    </button>
                    <button onclick="window.TempoStressRelief.renderLibrary()" 
                            class="w-full sm:w-auto px-5 py-3 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                        ${isVi() ? 'Xem phương pháp khác' : 'View Other Methods'}
                    </button>
                </div>
            </div>
        `;
    }

    function setDurationChoice(val) {
        const customBox = document.getElementById('custom-duration-box');
        const isRec = isRecoveryMode();
        ['1', '3', '5', 'custom'].forEach(k => {
            const btn = document.getElementById(`dur-btn-${k}`);
            if (btn) {
                if (String(val) === k) {
                    if (isRec) {
                        btn.className = 'px-4 py-2 rounded-xl text-xs font-bold transition bg-[#8EA28F] text-white border border-[#8EA28F] shadow-xs';
                    } else {
                        btn.className = 'px-4 py-2 rounded-xl text-xs font-bold transition bg-[#FF6B2C] text-white border border-[#FF6B2C] shadow-sm';
                    }
                } else {
                    if (isRec) {
                        btn.className = 'px-4 py-2 rounded-xl text-xs font-bold transition border border-[#EAE4DF] text-[#202124] bg-white hover:bg-[#F3F1EF]';
                    } else {
                        btn.className = 'px-4 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50';
                    }
                }
            }
        });

        if (val === 'custom') {
            if (customBox) customBox.classList.remove('hidden');
            const customInput = document.getElementById('custom-duration-input');
            selectedDuration = customInput ? parseInt(customInput.value, 10) || 4 : 4;
        } else {
            if (customBox) customBox.classList.add('hidden');
            selectedDuration = parseInt(val, 10);
        }
    }

    function handleCustomDurationChange(val) {
        const parsed = parseInt(val, 10);
        if (parsed && parsed >= 1 && parsed <= 30) {
            selectedDuration = parsed;
        }
    }

    // =========================================================================
    // VIEW 3: ACTIVE BREATHING SESSION
    // =========================================================================
    function startBreathingSession() {
        stopAllTimers();
        sessionRemainingSeconds = selectedDuration * 60;
        sessionIsPaused = false;
        breathingPhaseIndex = 0;
        breathingPhaseSeconds = 4;

        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        const isRec = isRecoveryMode();
        if (isRec) {
            container.innerHTML = `
                <div class="space-y-6 max-w-sm mx-auto text-center py-2">
                    <!-- Header -->
                    <div class="space-y-1">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-[#4A6A78]">${isVi() ? 'Bài tập thở' : 'Breathing Exercise'}</span>
                        <h3 class="font-heading text-xl font-bold text-[#202124]">Lấy lại Nhịp điệu với Box Breathing</h3>
                        <p id="breathing-time-remaining" class="text-xs font-bold text-[#6F6B68]">
                            ${formatMinutesSeconds(sessionRemainingSeconds)} remaining
                        </p>
                    </div>

                    <!-- Animated Breathing Circle -->
                    <div class="h-48 flex items-center justify-center relative">
                        <div id="active-breathing-circle" 
                             class="w-32 h-32 rounded-full bg-[#ECC9BA]/35 border-2 border-[#8EA28F] flex flex-col items-center justify-center transition-all duration-1000 ease-in-out shadow-xs">
                            <span id="active-breathing-phase" class="text-xs font-bold text-[#202124] px-4 text-center leading-snug">
                                Breathe in gently
                            </span>
                            <span id="active-breathing-count" class="text-sm font-extrabold text-[#3B5C43] mt-1">
                                4s
                            </span>
                        </div>
                    </div>

                    <!-- Session Controls -->
                    <div class="space-y-3 pt-2">
                        <div class="flex items-center justify-center gap-3">
                            <button id="btn-breathing-pause" onclick="window.TempoStressRelief.togglePauseResume()" 
                                    class="px-5 py-2.5 rounded-xl border border-[#93AFBC]/60 hover:border-[#93AFBC] text-xs font-bold text-[#202124] bg-white hover:bg-[#F3F1EF] transition shadow-xs cursor-pointer">
                                ${isVi() ? '⏸ Tạm dừng' : '⏸ Pause'}
                            </button>
                            <button onclick="window.TempoStressRelief.endSessionEarly()" 
                                    class="px-5 py-2.5 rounded-xl border border-transparent text-xs font-medium text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/20 transition cursor-pointer">
                                ${isVi() ? 'Kết thúc sớm' : 'Finish Early'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="space-y-6 max-w-sm mx-auto text-center py-2">
                    <!-- Header -->
                    <div class="space-y-1">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-[#FF6B2C]">BREATHING</span>
                        <h3 class="font-heading text-xl font-bold text-[#202124]">Lấy lại Nhịp điệu với Box Breathing</h3>
                        <p id="breathing-time-remaining" class="text-xs font-bold text-[#6F6B68]">
                            ${formatMinutesSeconds(sessionRemainingSeconds)} remaining
                        </p>
                    </div>

                    <!-- Animated Breathing Circle -->
                    <div class="h-48 flex items-center justify-center relative">
                        <div id="active-breathing-circle" 
                             class="w-32 h-32 rounded-full bg-[#FFE9DC]/70 border-2 border-[#FF6B2C]/60 flex flex-col items-center justify-center transition-all duration-1000 ease-in-out shadow-sm">
                            <span id="active-breathing-phase" class="text-xs font-bold text-[#202124] px-4 text-center leading-snug">
                                Breathe in gently
                            </span>
                            <span id="active-breathing-count" class="text-sm font-extrabold text-[#FF6B2C] mt-1">
                                4s
                            </span>
                        </div>
                    </div>

                    <!-- Session Controls -->
                    <div class="space-y-3 pt-2">
                        <div class="flex items-center justify-center gap-3">
                            <button id="btn-breathing-pause" onclick="window.TempoStressRelief.togglePauseResume()" 
                                    class="px-5 py-2.5 rounded-xl border border-gray-300 hover:border-gray-400 text-xs font-bold text-gray-700 bg-white hover:bg-stone-50 transition shadow-sm">
                                ${isVi() ? '⏸ Tạm dừng' : '⏸ Pause'}
                            </button>
                            <button onclick="window.TempoStressRelief.endSessionEarly()" 
                                    class="px-5 py-2.5 rounded-xl border border-transparent text-xs font-medium text-gray-500 hover:text-gray-800 hover:bg-stone-100 transition">
                                ${isVi() ? 'Kết thúc sớm' : 'Finish Early'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        updateBreathingDisplay();

        // 1-second interval driving both the breathing phases and session total countdown
        breathingInterval = setInterval(() => {
            if (sessionIsPaused) return;

            // Decrement session remaining
            if (sessionRemainingSeconds > 0) {
                sessionRemainingSeconds--;
                const timeEl = document.getElementById('breathing-time-remaining');
                if (timeEl) {
                    timeEl.textContent = `${formatMinutesSeconds(sessionRemainingSeconds)} remaining`;
                }
            } else {
                // Session finished!
                stopAllTimers();
                if (activeContext === 'emergency_reset') {
                    handleReady();
                    return;
                }
                renderCheckpoint();
                return;
            }

            // Decrement current breathing phase count
            if (breathingPhaseSeconds > 1) {
                breathingPhaseSeconds--;
            } else {
                breathingPhaseIndex = (breathingPhaseIndex + 1) % BREATHING_PHASES.length;
                breathingPhaseSeconds = BREATHING_PHASES[breathingPhaseIndex].count;
            }

            updateBreathingDisplay();
        }, 1000);
    }

    function updateBreathingDisplay() {
        const circle = document.getElementById('active-breathing-circle');
        const phaseEl = document.getElementById('active-breathing-phase');
        const countEl = document.getElementById('active-breathing-count');

        const currentPhase = BREATHING_PHASES[breathingPhaseIndex];
        if (phaseEl) phaseEl.textContent = currentPhase.label;
        if (countEl) countEl.textContent = `${breathingPhaseSeconds}s`;

        if (circle) {
            circle.style.transform = `scale(${currentPhase.scale})`;
            if (isRecoveryMode()) {
                circle.style.borderColor = breathingPhaseIndex % 2 === 0 ? '#8EA28F' : '#93AFBC';
            } else {
                circle.style.borderColor = breathingPhaseIndex % 2 === 0 ? '#FF6B2C' : '#FF9E79';
            }
        }
    }

    // =========================================================================
    // VIEW 4: METHOD DETAIL VIEW (Non-breathing methods)
    // =========================================================================
    function renderMethodDetail(method) {
        currentView = 'detail';
        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        selectedDuration = method.defaultDuration || 3;
        const isRec = isRecoveryMode();

        if (isRec) {
            container.innerHTML = `
                <div class="space-y-6 max-w-lg mx-auto py-2">
                    <!-- Back Link -->
                    <button onclick="window.TempoStressRelief.renderLibrary()" 
                            class="text-xs font-bold text-[#4A6A78] hover:text-[#202124] flex items-center space-x-1.5 transition cursor-pointer">
                        <span>←</span>
                        <span>${isVi() ? 'Quay lại danh sách' : 'Back to all methods'}</span>
                    </button>

                    <!-- Method Header (No Emojis!) -->
                    <div class="space-y-2 border-b border-[#EAE4DF] pb-4">
                        <div class="flex items-center space-x-2">
                            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#ECC9BA] text-[#202124]">
                                ${method.durationLabel}
                            </span>
                        </div>
                        <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">${method.title}</h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">${method.summary}</p>
                    </div>

                    <!-- Step-by-Step Instructions -->
                    <div class="p-4 bg-[#ECC9BA]/20 border border-[#ECC9BA]/60 rounded-2xl space-y-3">
                        <h4 class="text-xs font-bold uppercase tracking-wider text-[#202124]">${isVi() ? 'Hướng dẫn từng bước:' : 'Simple Instructions:'}</h4>
                        <ol class="space-y-2">
                            ${method.steps.map((s, idx) => `
                                <li class="flex items-start space-x-3 p-3 bg-white border border-[#EAE4DF] rounded-xl text-xs text-[#202124]">
                                    <span class="w-5 h-5 rounded-full bg-[#93AFBC] text-white flex items-center justify-center font-bold text-[11px] shrink-0 mt-0.5">
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
                            ${isVi() ? 'Thời lượng mong muốn?' : 'How long?'}
                        </label>
                        <div class="flex items-center justify-center gap-2.5">
                            <button type="button" onclick="window.TempoStressRelief.setDurationChoice(1)" id="dur-btn-1" 
                                    class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 1 ? 'bg-[#8EA28F] text-white border border-[#8EA28F] shadow-xs' : 'border border-[#EAE4DF] text-[#202124] bg-white hover:bg-[#F3F1EF]'}">
                                ${isVi() ? '1 phút' : '1 min'}
                            </button>
                            <button type="button" onclick="window.TempoStressRelief.setDurationChoice(3)" id="dur-btn-3" 
                                    class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 3 ? 'bg-[#8EA28F] text-white border border-[#8EA28F] shadow-xs' : 'border border-[#EAE4DF] text-[#202124] bg-white hover:bg-[#F3F1EF]'}">
                                ${isVi() ? '3 phút' : '3 min'}
                            </button>
                            <button type="button" onclick="window.TempoStressRelief.setDurationChoice(5)" id="dur-btn-5" 
                                    class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 5 ? 'bg-[#8EA28F] text-white border border-[#8EA28F] shadow-xs' : 'border border-[#EAE4DF] text-[#202124] bg-white hover:bg-[#F3F1EF]'}">
                                ${isVi() ? '5 phút' : '5 min'}
                            </button>
                            <button type="button" onclick="window.TempoStressRelief.setDurationChoice('custom')" id="dur-btn-custom" 
                                    class="px-3.5 py-2 rounded-xl text-xs font-bold transition border border-[#EAE4DF] text-[#202124] bg-white hover:bg-[#F3F1EF]">
                                ${isVi() ? 'Tùy chỉnh' : 'Custom'}
                            </button>
                        </div>

                        <div id="custom-duration-box" class="hidden text-center pt-2">
                            <label for="custom-duration-input" class="text-xs text-[#6F6B68] mr-2">${isVi() ? 'Số phút:' : 'Minutes:'}</label>
                            <input id="custom-duration-input" type="number" min="1" max="20" value="${selectedDuration}" 
                                   onchange="window.TempoStressRelief.handleCustomDurationChange(this.value)"
                                   class="w-16 px-2.5 py-1 text-xs border border-[#EAE4DF] rounded-lg text-center font-bold text-[#202124] focus:border-[#8EA28F] focus:outline-hidden">
                        </div>
                    </div>

                    <!-- Action Button -->
                    <div class="pt-2 flex justify-center">
                        <button onclick="window.TempoStressRelief.startTimedSession()" 
                                class="btn-primary w-full sm:w-auto px-8 py-3 rounded-xl font-bold text-sm shadow-xs flex items-center justify-center space-x-2 bg-[#8EA28F] hover:bg-[#7D917E] text-white transition cursor-pointer">
                            <span>${isVi() ? 'Bắt đầu →' : 'Start →'}</span>
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
                    <span>${isVi() ? 'Quay lại danh sách' : 'Back to all methods'}</span>
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
                    <h4 class="text-xs font-bold uppercase tracking-wider text-[#202124]">${isVi() ? 'Hướng dẫn từng bước:' : 'Simple Instructions:'}</h4>
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
                        ${isVi() ? 'Thời lượng mong muốn?' : 'How long?'}
                    </label>
                    <div class="flex items-center justify-center gap-2.5">
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(1)" id="dur-btn-1" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 1 ? 'bg-[#FF6B2C] text-white border border-[#FF6B2C]' : 'border border-gray-200 text-gray-700 hover:bg-stone-50'}">
                            ${isVi() ? '1 phút' : '1 min'}
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(3)" id="dur-btn-3" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 3 ? 'bg-[#FF6B2C] text-white border border-[#FF6B2C]' : 'border border-gray-200 text-gray-700 hover:bg-stone-50'}">
                            ${isVi() ? '3 phút' : '3 min'}
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice(5)" id="dur-btn-5" 
                                class="px-4 py-2 rounded-xl text-xs font-bold transition ${selectedDuration === 5 ? 'bg-[#FF6B2C] text-white border border-[#FF6B2C]' : 'border border-gray-200 text-gray-700 hover:bg-stone-50'}">
                            ${isVi() ? '5 phút' : '5 min'}
                        </button>
                        <button type="button" onclick="window.TempoStressRelief.setDurationChoice('custom')" id="dur-btn-custom" 
                                class="px-3.5 py-2 rounded-xl text-xs font-bold transition border border-gray-200 text-gray-700 hover:bg-stone-50">
                            ${isVi() ? 'Tùy chỉnh' : 'Custom'}
                        </button>
                    </div>

                    <div id="custom-duration-box" class="hidden text-center pt-2">
                        <label for="custom-duration-input" class="text-xs text-[#6F6B68] mr-2">${isVi() ? 'Số phút:' : 'Minutes:'}</label>
                        <input id="custom-duration-input" type="number" min="1" max="20" value="${selectedDuration}" 
                               onchange="window.TempoStressRelief.handleCustomDurationChange(this.value)"
                               class="w-16 px-2.5 py-1 text-xs border border-gray-300 rounded-lg text-center font-bold">
                    </div>
                </div>

                <!-- Action Button -->
                <div class="pt-2 flex justify-center">
                    <button onclick="window.TempoStressRelief.startTimedSession()" 
                            class="btn-primary w-full sm:w-auto px-8 py-3 rounded-xl font-bold text-sm shadow-md flex items-center justify-center space-x-2">
                        <span>${isVi() ? 'Bắt đầu →' : 'Start →'}</span>
                    </button>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // VIEW 5: ACTIVE TIMED SESSION (Non-breathing methods)
    // =========================================================================
    function startTimedSession() {
        stopAllTimers();
        sessionRemainingSeconds = selectedDuration * 60;
        sessionIsPaused = false;

        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        const isRec = isRecoveryMode();
        if (isRec) {
            container.innerHTML = `
                <div class="space-y-6 max-w-md mx-auto text-center py-2">
                    <!-- Header (No Emojis!) -->
                    <div class="space-y-1">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#ECC9BA] text-[#202124]">${isVi() ? 'Phiên thực hành' : 'Active Session'}</span>
                        <h3 class="font-heading text-xl font-bold text-[#202124]">${activeMethod.title}</h3>
                        <p class="text-xs text-[#6F6B68]">${activeMethod.summary}</p>
                    </div>

                    <!-- Countdown Clock Display -->
                    <div class="py-6 px-8 bg-[#ECC9BA]/25 border border-[#ECC9BA]/80 rounded-3xl inline-block shadow-xs">
                        <span id="timed-session-clock" class="font-heading text-4xl sm:text-5xl font-extrabold text-[#202124] tracking-tight">
                            ${formatMinutesSeconds(sessionRemainingSeconds)}
                        </span>
                        <p class="text-[11px] font-bold text-[#4A6A78] uppercase tracking-wider mt-1">${isVi() ? 'Thời gian còn lại' : 'Remaining Time'}</p>
                    </div>

                    <!-- Steps Quick Reminder -->
                    <div class="text-left bg-white p-4 rounded-2xl border border-[#EAE4DF] text-xs space-y-2">
                        <p class="font-bold text-[#202124] uppercase tracking-wider text-[10px]">${isVi() ? 'Thực hiện theo nhịp độ của bạn:' : 'Follow along at your own pace:'}</p>
                        <ul class="space-y-1.5 text-[#6F6B68]">
                            ${activeMethod.steps.map(s => `<li>• ${s}</li>`).join('')}
                        </ul>
                    </div>

                    <!-- Session Controls -->
                    <div class="flex items-center justify-center gap-3 pt-2">
                        <button id="btn-timed-pause" onclick="window.TempoStressRelief.togglePauseResume()" 
                                class="px-5 py-2.5 rounded-xl border border-[#93AFBC]/60 hover:border-[#93AFBC] text-xs font-bold text-[#202124] bg-white hover:bg-[#F3F1EF] transition shadow-xs cursor-pointer">
                            ${isVi() ? '⏸ Tạm dừng' : '⏸ Pause'}
                        </button>
                        <button onclick="window.TempoStressRelief.endSessionEarly()" 
                                class="px-5 py-2.5 rounded-xl border border-transparent text-xs font-medium text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/20 transition cursor-pointer">
                            ${isVi() ? 'Kết thúc sớm' : 'Finish Early'}
                        </button>
                    </div>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="space-y-6 max-w-md mx-auto text-center py-2">
                    <!-- Header -->
                    <div class="space-y-1">
                        <span class="text-3xl">${activeMethod.icon}</span>
                        <h3 class="font-heading text-xl font-bold text-[#202124]">${activeMethod.title}</h3>
                        <p class="text-xs text-[#6F6B68]">${activeMethod.summary}</p>
                    </div>

                    <!-- Countdown Clock Display -->
                    <div class="py-6 px-8 bg-[#FFF8F2] border border-[#FFD2BA]/60 rounded-3xl inline-block shadow-sm">
                        <span id="timed-session-clock" class="font-heading text-4xl sm:text-5xl font-extrabold text-[#FF6B2C] tracking-tight">
                            ${formatMinutesSeconds(sessionRemainingSeconds)}
                        </span>
                        <p class="text-[11px] font-bold text-[#6F6B68] uppercase tracking-wider mt-1">${isVi() ? 'Thời gian còn lại' : 'Remaining Time'}</p>
                    </div>

                    <!-- Steps Quick Reminder -->
                    <div class="text-left bg-white p-4 rounded-2xl border border-gray-200 text-xs space-y-2">
                        <p class="font-bold text-gray-800 uppercase tracking-wider text-[10px]">${isVi() ? 'Thực hiện theo nhịp độ của bạn:' : 'Follow along at your own pace:'}</p>
                        <ul class="space-y-1.5 text-[#6F6B68]">
                            ${activeMethod.steps.map(s => `<li>• ${s}</li>`).join('')}
                        </ul>
                    </div>

                    <!-- Session Controls -->
                    <div class="flex items-center justify-center gap-3 pt-2">
                        <button id="btn-timed-pause" onclick="window.TempoStressRelief.togglePauseResume()" 
                                class="px-5 py-2.5 rounded-xl border border-gray-300 hover:border-gray-400 text-xs font-bold text-gray-700 bg-white hover:bg-stone-50 transition shadow-sm">
                            ${isVi() ? '⏸ Tạm dừng' : '⏸ Pause'}
                        </button>
                        <button onclick="window.TempoStressRelief.endSessionEarly()" 
                                class="px-5 py-2.5 rounded-xl border border-transparent text-xs font-medium text-gray-500 hover:text-gray-800 hover:bg-stone-100 transition">
                            ${isVi() ? 'Kết thúc sớm' : 'Finish Early'}
                        </button>
                    </div>
                </div>
            `;
        }

        sessionTimer = setInterval(() => {
            if (sessionIsPaused) return;

            if (sessionRemainingSeconds > 0) {
                sessionRemainingSeconds--;
                const clockEl = document.getElementById('timed-session-clock');
                if (clockEl) {
                    clockEl.textContent = formatMinutesSeconds(sessionRemainingSeconds);
                }
            } else {
                stopAllTimers();
                if (activeContext === 'emergency_reset') {
                    handleReady();
                    return;
                }
                renderCheckpoint();
            }
        }, 1000);
    }

    // =========================================================================
    // PAUSE / RESUME CONTROL
    // =========================================================================
    function togglePauseResume() {
        sessionIsPaused = !sessionIsPaused;
        const btnBreathing = document.getElementById('btn-breathing-pause');
        const btnTimed = document.getElementById('btn-timed-pause');
        const circle = document.getElementById('active-breathing-circle');

        const btnText = sessionIsPaused ? (isVi() ? '▶ Tiếp tục' : '▶ Resume') : (isVi() ? '⏸ Tạm dừng' : '⏸ Pause');
        if (btnBreathing) btnBreathing.textContent = btnText;
        if (btnTimed) btnTimed.textContent = btnText;

        if (circle) {
            if (sessionIsPaused) {
                circle.style.transition = 'none';
            } else {
                circle.style.transition = 'all 1000ms ease-in-out';
            }
        }
    }

    function endSessionEarly() {
        stopAllTimers();
        if (activeContext === 'emergency_reset') {
            handleReady();
            return;
        }
        renderCheckpoint();
    }

    // =========================================================================
    // VIEW 6: CHECKPOINT PANEL (Bạn cảm thấy thế nào rồi?)
    // =========================================================================
    function renderCheckpoint() {
        currentView = 'checkpoint';
        if (activeContext === 'emergency_reset') {
            handleReady();
            return;
        }
        const container = document.getElementById('stress-relief-content-body');
        if (!container) return;

        const isBreathing = activeMethod && activeMethod.isBreathing;
        const repeatActionText = isBreathing ? (isVi() ? 'Tiếp tục thở' : 'Keep breathing') : (isVi() ? 'Thực hiện lại' : 'Do this again');

        const isRec = isRecoveryMode();
        if (isRec) {
            container.innerHTML = `
                <div class="space-y-6 max-w-md mx-auto text-center py-4">
                    <div class="w-12 h-12 rounded-full bg-[#8EA28F] text-white flex items-center justify-center mx-auto text-xl font-bold shadow-xs">
                        ✓
                    </div>

                    <div class="space-y-1.5">
                        <h3 class="font-heading text-2xl font-bold text-[#202124]">${isVi() ? 'Bạn cảm thấy thế nào rồi?' : 'How are you feeling?'}</h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68]">${isVi() ? 'Hít một hơi thở sâu và cảm nhận tâm trí, cơ thể của mình.' : 'Take a deep breath and check in with your mind and body.'}</p>
                    </div>

                    <!-- Checkpoint 3 Action Buttons -->
                    <div class="space-y-3 pt-2">
                        <!-- 1. Primary: I'm ready -->
                        <button onclick="window.TempoStressRelief.handleReady()" 
                                class="btn-primary w-full py-3.5 rounded-xl font-bold text-sm shadow-xs flex items-center justify-center space-x-2 bg-[#8EA28F] hover:bg-[#7D917E] text-white transition cursor-pointer">
                            <span>${isVi() ? 'Tôi đã sẵn sàng →' : 'I am ready →'}</span>
                        </button>

                        <!-- 2. Secondary: Repeat -->
                        <button onclick="window.TempoStressRelief.handleRepeat()" 
                                class="w-full py-3 rounded-xl border border-[#93AFBC]/60 text-xs sm:text-sm font-bold text-[#202124] bg-white hover:bg-[#F3F1EF] transition cursor-pointer">
                            ${repeatActionText}
                        </button>

                        <!-- 3. Tertiary: ${isVi() ? 'Thử phương pháp khác' : 'Try another method'} -->
                        <button onclick="window.TempoStressRelief.renderLibrary()" 
                                class="w-full py-2.5 text-xs text-[#3B5C43] hover:text-[#202124] font-bold underline transition cursor-pointer">
                            ${isVi() ? 'Thử phương pháp khác' : 'Try another method'}
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="space-y-6 max-w-md mx-auto text-center py-4">
                <div class="w-12 h-12 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-100 flex items-center justify-center mx-auto text-lg font-bold shadow-xs">
                    ✨
                </div>

                <div class="space-y-1.5">
                    <h3 class="font-heading text-2xl font-bold text-[#202124]">${isVi() ? 'Bạn cảm thấy thế nào rồi?' : 'How are you feeling?'}</h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">${isVi() ? 'Hít một hơi thở sâu và cảm nhận tâm trí, cơ thể của mình.' : 'Take a deep breath and check in with your mind and body.'}</p>
                </div>

                <!-- Checkpoint 3 Action Buttons -->
                <div class="space-y-3 pt-2">
                    <!-- 1. Primary: I'm ready -->
                    <button onclick="window.TempoStressRelief.handleReady()" 
                            class="btn-primary w-full py-3.5 rounded-xl font-bold text-sm shadow-xs flex items-center justify-center space-x-2 bg-[#FF6B2C] hover:bg-[#E8591C] text-white transition cursor-pointer">
                        <span>${isVi() ? 'Tôi đã sẵn sàng →' : 'I am ready →'}</span>
                    </button>

                    <!-- 2. Secondary: Repeat -->
                    <button onclick="window.TempoStressRelief.handleRepeat()" 
                            class="w-full py-3 rounded-xl border border-[#EAE4DF] text-xs sm:text-sm font-bold text-[#202124] bg-white hover:bg-[#F3F1EF] transition cursor-pointer">
                        ${repeatActionText}
                    </button>

                    <!-- 3. Tertiary: ${isVi() ? 'Thử phương pháp khác' : 'Try another method'} -->
                    <button onclick="window.TempoStressRelief.renderLibrary()" 
                            class="w-full py-2.5 text-xs text-[#FF6B2C] hover:text-[#E8591C] font-bold underline transition cursor-pointer">
                        ${isVi() ? 'Thử phương pháp khác' : 'Try another method'}
                    </button>
                </div>
            </div>
        `;
    }

    function handleReady() {
        const cb = onReadyCallback;
        const ctx = activeContext;
        stopAllTimers();
        onReadyCallback = null;
        onCloseCallback = null;
        activeContext = 'home';
        const modal = document.getElementById('modal-quick-stress-relief');
        if (modal) {
            modal.classList.add('hidden');
            const card = modal.querySelector('.tempo-card');
            const badge = modal.querySelector('span.uppercase.tracking-wider');
            const closeBtn = document.getElementById('btn-close-stress-relief');
            if (card) card.className = 'tempo-card max-w-2xl w-full my-auto max-h-[92vh] overflow-y-auto bg-[#FFF9F4] rounded-2xl sm:rounded-[28px] p-5 sm:p-8 space-y-4 relative shadow-xl border border-[#ECC9BA]/60';
            if (badge) {
                badge.className = 'px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-[#ECC9BA] text-[#202124]';
                badge.textContent = 'Grounded Pause';
            }
            if (closeBtn) closeBtn.className = 'text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/30 p-2 rounded-xl text-lg transition shrink-0';
        }
        document.body.classList.remove('overflow-hidden');

        if (ctx === 'emergency') {
            if (window.TempoEmergencyFlow) {
                window.TempoEmergencyFlow.goToStage('reality-check');
            }
        } else if (ctx !== 'emergency_reset') {
            if (window.TempoApp) {
                window.TempoApp.showToast(isVi() ? "Làm tốt lắm. Hãy mang nguồn năng lượng bình tâm này vào bước tiếp theo nhé." : "Well done. Carry this calm momentum into your next step.");
            }
        }

        if (typeof cb === 'function') {
            cb();
        }
    }

    function handleRepeat() {
        if (activeMethod && activeMethod.isBreathing) {
            renderBreathingSetup();
        } else if (activeMethod) {
            renderMethodDetail(activeMethod);
        } else {
            renderBreathingSetup();
        }
    }

    // =========================================================================
    // TEMPO GAMES SYSTEM (RMODE ONLY)
    // =========================================================================
    function openGamesHub() {
        currentView = 'games_hub';
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
                        <span>${isVi() ? 'Quay lại phương pháp tĩnh tâm' : 'Back to grounding methods'}</span>
                    </button>
                    <div class="space-y-1">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-[#4A6A78]">Tempo Games</span>
                        <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">${isVi() ? 'Trò chơi Thư giãn Tinh thần' : 'Calming Mini-Games'}</h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">${isVi() ? 'Những hoạt động nhẹ nhàng, có giới hạn giúp bạn rời xa căng thẳng mà không có áp lực thành tích.' : 'Gentle, bounded activities to help you pause and step away without performance pressure.'}</p>
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
                                    <span class="text-[11px] font-semibold text-[#4A6A78]">${isVi() ? 'Nhịp độ êm dịu có chừng mực' : 'Gentle bounded pace'}</span>
                                    <button type="button"
                                            onclick="window.TempoStressRelief.launchGame('${g.id}')"
                                            class="px-4 py-2 bg-[#8EA28F] hover:bg-[#7D917E] text-white rounded-xl text-xs font-bold transition shadow-xs flex items-center space-x-1.5 cursor-pointer">
                                        <span>${isVi() ? 'Chơi ngay' : 'Play now'}</span>
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
                        <h4 class="font-heading text-base font-bold text-[#202124]">${isVi() ? 'Hiện chưa có trò chơi nào' : 'No games available yet'}</h4>
                        <p class="text-xs text-[#6F6B68] max-w-sm mx-auto">
                            ${isVi() ? 'Thêm nhiều hoạt động thư thái sẽ sớm ra mắt. Trong lúc này, hãy khám phá các phương pháp tĩnh tâm của chúng mình.' : 'More calming activities are coming soon. In the meantime, explore our grounding exercises.'}
                        </p>
                        <div class="pt-2">
                            <button type="button"
                                    onclick="window.TempoStressRelief.renderLibrary()"
                                    class="px-4 py-2 bg-[#8EA28F] hover:bg-[#7D917E] text-white rounded-xl text-xs font-bold transition shadow-xs cursor-pointer">
                                ${isVi() ? 'Quay lại phương pháp tĩnh tâm' : 'Back to grounding methods'}
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
        currentView = 'gentle_match';
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
                        <span>${isVi() ? 'Quay lại Trò chơi Tempo' : 'Back to Tempo Games'}</span>
                    </button>
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#ECC9BA] text-[#202124]">
                        Gentle Match
                    </span>
                </div>

                <!-- Title & Instructions -->
                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">${isVi() ? 'Ghép cặp Nhẹ nhàng' : 'Gentle Match'}</h3>
                    <p class="text-xs text-[#6F6B68]">${isVi() ? 'Tìm tất cả các cặp trùng khớp theo nhịp độ của bạn. Trò chơi bình dị cho một tâm trí an yên.' : 'Find all matching pairs at your own pace. A gentle game for a calm mind.'}</p>
                </div>

                <!-- 4x3 Matching Grid (Zero performance pressure, no timer or score) -->
                <div class="grid grid-cols-4 gap-2.5 sm:gap-3.5 max-w-xs sm:max-w-md mx-auto py-2">
                    ${game.cards.map((card, idx) => `
                        <button type="button"
                                onclick="window.TempoStressRelief.handleGameCardClick(${idx})"
                                aria-label="${card.isFlipped || card.isMatched ? card.label : (isVi() ? 'Thẻ bài ẩn' : 'Hidden card')}"
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
                            <span class="text-xs font-bold text-[#3B5C43] block">${isVi() ? 'Đã tìm thấy tất cả các cặp ghép ✓' : 'All matching pairs found ✓'}</span>
                            <p class="text-xs text-[#6F6B68]">${isVi() ? 'Hãy hít một hơi thật sâu, tĩnh tâm và tận hưởng khoảnh khắc thư thái này.' : 'Take a deep breath, ground yourself, and enjoy this calm moment.'}</p>
                        </div>
                        <div class="flex flex-wrap items-center justify-center gap-2 pt-1">
                            <button type="button"
                                    onclick="window.TempoStressRelief.restartGentleMatch()"
                                    class="px-3.5 py-2 rounded-xl border border-[#93AFBC]/60 bg-white text-[#202124] text-xs font-bold hover:bg-[#F3F1EF] transition cursor-pointer">
                                
                            </button>
                            <button type="button"
                                    onclick="window.TempoStressRelief.openGamesHub()"
                                    class="px-3.5 py-2 rounded-xl border border-[#93AFBC]/60 bg-white text-[#202124] text-xs font-bold hover:bg-[#F3F1EF] transition cursor-pointer">
                                
                            </button>
                            <button type="button"
                                    onclick="window.TempoStressRelief.handleReady()"
                                    class="px-4 py-2 bg-[#8EA28F] hover:bg-[#7D917E] text-white rounded-xl text-xs font-bold transition shadow-xs cursor-pointer">
                                
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

    function formatMinutesSeconds(totalSec) {
        const mins = Math.floor(totalSec / 60);
        const secs = totalSec % 60;
        return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }

    return {
        init,
        openBreathing,
        openLibrary,
        openModal,
        closeModal,
        renderLibrary,
        setFilter,
        selectMethod,
        renderBreathingSetup,
        setDurationChoice,
        handleCustomDurationChange,
        startBreathingSession,
        renderMethodDetail,
        startTimedSession,
        togglePauseResume,
        endSessionEarly,
        renderCheckpoint,
        handleReady,
        handleRepeat,
        openGamesHub,
        launchGame,
        initGentleMatchGame,
        renderGentleMatchGame,
        handleGameCardClick,
        restartGentleMatch
    };
})();
