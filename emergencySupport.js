/**
 * Tempo Progressive Emergency & Crisis Support Engine
 * Implements a progressive crisis-support flow where AI provides immediate grounding
 * and emotional stabilization while human/emergency support options remain accessible at all times.
 * STRICT POLICY: No medical/mental-health diagnoses. AI is never a replacement for professional help.
 */

window.TempoEmergencySupport = (function() {
    // State
    let currentStep = 'checkin'; // 'checkin' | 'grounding' | 'safety_checkin' | 'still_unsafe' | 'calmer_options' | 'understand_problem' | 'problem_solving'
    let selectedNeed = null;     // 'overwhelmed' | 'crisis' | 'selfharm' | 'notsure'
    let isSafetyMode = false;
    let currentGroundingIndex = 0; // 0: surroundings, 1: slow breathing, 2: move toward safety
    let breathingInterval = null;

    function isVi() {
        return window.TempoI18n && typeof window.TempoI18n.getLanguage === 'function' && window.TempoI18n.getLanguage() === 'vi';
    }

    // Configurable Support Information (Centralized per Tempo Handbook)
    const supportConfig = {
        emergencyMedical: {
            title_vi: 'Hỗ trợ Y tế Khẩn cấp',
            title_en: 'Emergency Medical Support',
            phone: '115',
            callHref: 'tel:115',
            details_vi: "Nếu bạn có nguy cơ tự làm hại bản thân ngay lập tức hoặc đang trong tình huống nguy hiểm.",
            details_en: "If you're at immediate risk of hurting yourself or you're in immediate danger."
        },
        crisisHotline: {
            title_vi: 'Đường dây nóng Khủng hoảng & Hỗ trợ Tâm lý HOPE',
            title_en: 'HOPE — Suicide Prevention Hotline',
            phone: '0865 044 400',
            callHref: 'tel:0865044400',
            details_vi: "Nếu bạn đang trong cơn khủng hoảng, có suy nghĩ tự hại hoặc cần người lắng nghe ngay bây giờ.",
            details_en: "If you're in crisis, having thoughts of hurting yourself, or need someone to support you right now."
        },
        ngayMaiHotline: {
            title_vi: 'ĐƯỜNG DÂY NÓNG NGÀY MAI',
            title_en: 'NGÀY MAI SUPPORT HOTLINE',
            badge_vi: 'Hỗ trợ tâm lý',
            badge_en: 'Mental Health Support',
            phone: '096 306 1414',
            callHref: 'tel:0963061414',
            details_vi: "Hỗ trợ tâm lý miễn phí qua điện thoại cho người đang gặp khủng hoảng tâm lý, trầm cảm và người thân của họ. Lắng nghe không phán xét, bảo mật thông tin.",
            details_en: "Free psychological first aid by phone for people experiencing emotional distress or depression, and their loved ones. Confidential and non-judgmental support.",
            hours_vi: "13:00 – 20:30, Thứ Tư – Chủ Nhật",
            hours_en: "1:00 PM – 8:30 PM, Wednesday – Sunday",
            cta_vi: "Gọi 096 306 1414",
            cta_en: "Call 096 306 1414"
        },
        fptCounseling: {
            title_vi: 'Phòng Tư vấn tâm lý – Đại học FPT',
            title_en: 'FPT University Psychological Counseling Office',
            email: 'tuvansinhvien@fpt.edu.vn',
            emailHref: 'mailto:tuvansinhvien@fpt.edu.vn',
            details_vi: 'Dịch vụ tư vấn tâm lý miễn phí và bảo mật dành cho sinh viên Đại học FPT.',
            details_en: 'Free and confidential psychological counseling services for FPT University students.',
            cta_vi: 'Gửi email tư vấn',
            cta_en: 'Send counseling email'
        },
        waitingGuidance_vi: [
            'Ở cùng một người bạn tin tưởng.',
            'Di chuyển đến một nơi an toàn hơn.',
            'Tạo khoảng cách với những vật có thể gây tổn thương cho bạn.'
        ],
        waitingGuidance_en: [
            'Stay with someone you trust.',
            'Move somewhere safer.',
            'Create distance from anything that could hurt you.'
        ],
        closingReassurance_vi: "Bạn không cần giải quyết mọi thứ ngay lúc này. Lúc này, chỉ cần tập trung giữ an toàn cho bản thân.",
        closingReassurance_en: "You don't need to solve everything right now. For now, just focus on staying safe.",
        trustedPersonTemplate_vi: "Chào bạn, mình đang trải qua một khoảng thời gian rất khó khăn và cảm thấy quá tải. Bạn có thể trò chuyện hoặc ngồi cùng mình một lúc được không?",
        trustedPersonTemplate_en: "Hey, I'm having a really difficult time right now and feeling overwhelmed. Are you free to talk or sit with me for a few minutes?"
    };

    function init() {
        bindEvents();
        if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
            window.TempoI18n.onLanguageChange(() => {
                const modal = document.getElementById('progressive-emergency-modal');
                if (modal && !modal.classList.contains('hidden')) {
                    if (currentStep === 'grounding') {
                        renderGroundingActivity(currentGroundingIndex);
                    }
                }
            });
        }
    }

    function bindEvents() {
        // Universal trigger buttons
        document.querySelectorAll('.btn-open-emergency-support, .btn-urgent, .btn-open-crisis-helpline').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                openModal();
            });
        });

        // Close Modal
        const closeBtn = document.getElementById('btn-close-emergency-flow');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => closeModal(false));
        }

        // Persistent Human Support Drawer Toggle
        const toggleHumanBtn = document.getElementById('btn-toggle-human-drawer');
        if (toggleHumanBtn) {
            toggleHumanBtn.addEventListener('click', toggleHumanDrawer);
        }
        const closeDrawerBtn = document.getElementById('btn-close-human-drawer');
        if (closeDrawerBtn) {
            closeDrawerBtn.addEventListener('click', closeHumanDrawer);
        }

        // Copy trusted contact message
        const copyTrustedBtn = document.getElementById('btn-copy-trusted-msg');
        if (copyTrustedBtn) {
            copyTrustedBtn.addEventListener('click', copyTrustedMessage);
        }
    }

    function copyTrustedMessage() {
        const text = isVi() ? supportConfig.trustedPersonTemplate_vi : supportConfig.trustedPersonTemplate_en;
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text);
        }
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(isVi() 
                ? "Đã sao chép tin nhắn! Bạn có thể dán và gửi cho bạn bè hoặc người thân." 
                : "Message copied to clipboard! You can paste and send it to a friend or family member.");
        }
    }

    function submitOfflineMessage(source = 'drawer') {
        const contactInput = document.getElementById(source === 'drawer' ? 'drawer-offline-contact' : 'step5a-offline-contact');
        const msgInput = document.getElementById(source === 'drawer' ? 'drawer-offline-message' : 'step5a-offline-message');
        const successEl = document.getElementById(source === 'drawer' ? 'drawer-offline-success' : 'step5a-offline-success');

        const message = msgInput ? msgInput.value.trim() : '';
        const contact = contactInput ? contactInput.value.trim() : 'Anonymous Student';

        if (!message) {
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast(isVi() ? "Vui lòng nhập tin nhắn trước khi gửi." : "Please enter a message before sending.");
            }
            return;
        }

        const offlineEntry = {
            id: 'offline-' + Date.now(),
            contact: contact || 'Anonymous Student',
            message: message,
            timestamp: new Date().toISOString()
        };

        try {
            const existing = JSON.parse(localStorage.getItem('tempo_offline_messages') || '[]');
            existing.push(offlineEntry);
            localStorage.setItem('tempo_offline_messages', JSON.stringify(existing));
        } catch (e) {
            console.warn("Storage warning:", e);
        }

        if (msgInput) msgInput.value = '';
        if (successEl) successEl.classList.remove('hidden');

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(isVi()
                ? "Đã ghi nhận tin nhắn. Nhân viên hỗ trợ sẽ phản hồi trong giờ làm việc. Nếu cần giúp đỡ ngay, hãy gọi 115 hoặc HOPE (0865 044 400)."
                : "Message received for office hours. For immediate help, call 115 or HOPE (0865 044 400).");
        }
    }

    function openModal() {
        const modal = document.getElementById('progressive-emergency-modal');
        if (!modal) return;

        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');

        // Always close human drawer when opening modal fresh
        closeHumanDrawer();

        // Reset to Step 1: Initial Check-In
        isSafetyMode = false;
        goToStep('checkin');
    }

    function closeModal(force = false) {
        if (!force && isSafetyMode) {
            const confirmMsg = isVi() 
                ? "Bạn đang ở trong Chế độ Hỗ trợ An toàn. Bạn có chắc chắn muốn thoát không? Hãy nhớ rằng 115 và HOPE (0865 044 400) luôn sẵn sàng hỗ trợ."
                : "You are currently in Safety Support. Are you sure you want to exit? Remember, 115 and HOPE (0865 044 400) are available.";
            if (typeof window.confirm === 'function' && !window.confirm(confirmMsg)) {
                return;
            }
        }
        stopBreathing();
        const modal = document.getElementById('progressive-emergency-modal');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
        closeHumanDrawer();
    }

    function goToStep(step) {
        currentStep = step;
        stopBreathing();

        // Hide all step panels
        document.querySelectorAll('.emergency-flow-step').forEach(panel => {
            panel.classList.add('hidden');
        });

        const activePanel = document.getElementById(`emergency-step-${step}`);
        if (activePanel) {
            activePanel.classList.remove('hidden');
        }

        // Update Safety Mode banner & header
        const safetyBanner = document.getElementById('emergency-safety-banner');
        if (safetyBanner) {
            if (isSafetyMode) {
                safetyBanner.classList.remove('hidden');
            } else {
                safetyBanner.classList.add('hidden');
            }
        }

        // Trigger specific step initializers
        if (step === 'grounding') {
            renderGroundingActivity(currentGroundingIndex);
        }
    }

    // STEP 1: INITIAL CHECK-IN HANDLERS
    function handleInitialCheckin(choice) {
        selectedNeed = choice;

        if (choice === 'crisis' || choice === 'selfharm') {
            // Immediate Safety Mode
            isSafetyMode = true;
            if (choice === 'selfharm') {
                currentGroundingIndex = 2; // Move toward safety grounding
            } else {
                currentGroundingIndex = 0;
            }
            goToStep('grounding');
        } else if (choice === 'notsure') {
            isSafetyMode = false;
            currentGroundingIndex = 0;
            goToStep('grounding');
        } else {
            // Overwhelmed or panicking
            isSafetyMode = false;
            currentGroundingIndex = 0;
            goToStep('grounding');
        }
    }

    // STEP 3: GROUNDING ACTIVITIES (ONE ACTIVITY AT A TIME)
    function renderGroundingActivity(index) {
        currentGroundingIndex = index;
        const container = document.getElementById('grounding-activity-content');
        if (!container) return;

        if (index === 0) {
            // Grounding Activity 1: Notice your surroundings
            container.innerHTML = `
                <div class="space-y-4">
                    <div class="p-5 sm:p-6 bg-[#8EA28F]/10 border border-[#8EA28F]/30 rounded-2xl sm:rounded-3xl space-y-3 shadow-2xs">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#8EA28F]/20 text-[#3B5C43]">
                            ${isVi() ? 'Bước 1 / 3 • Quan sát Xung quanh' : 'Grounding 1 of 3 • Notice Your Surroundings'}
                        </span>
                        <h4 class="font-heading text-lg font-bold text-[#202124]">${isVi() ? 'Quan sát Xung quanh bạn' : 'Notice Your Surroundings'}</h4>
                        <div class="space-y-1.5 text-xs sm:text-sm text-[#202124] leading-relaxed">
                            <p class="font-medium">${isVi() ? '"Đặt cả hai bàn chân trên sàn nếu có thể."' : '"Put both feet on the floor if you can."'}</p>
                            <p class="text-[#6F6B68]">${isVi() ? '"Nhìn quanh và gọi tên 3 đồ vật bạn nhìn thấy."' : '"Look around and name 3 things you can see."'}</p>
                        </div>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-2">
                            <input type="text" placeholder="${isVi() ? '1. Đồ vật tôi nhìn thấy...' : '1. Item I see...'}" class="p-2.5 text-xs bg-[#FFF9F4] border border-[#EAE4DF] rounded-xl text-[#202124] focus:outline-none focus:border-[#8EA28F]">
                            <input type="text" placeholder="${isVi() ? '2. Đồ vật tôi nhìn thấy...' : '2. Item I see...'}" class="p-2.5 text-xs bg-[#FFF9F4] border border-[#EAE4DF] rounded-xl text-[#202124] focus:outline-none focus:border-[#8EA28F]">
                            <input type="text" placeholder="${isVi() ? '3. Đồ vật tôi nhìn thấy...' : '3. Item I see...'}" class="p-2.5 text-xs bg-[#FFF9F4] border border-[#EAE4DF] rounded-xl text-[#202124] focus:outline-none focus:border-[#8EA28F]">
                        </div>
                    </div>

                    <div class="flex items-center justify-between pt-2">
                        <button type="button" onclick="window.TempoEmergencySupport.nextGrounding()" class="px-4 py-2.5 rounded-xl border border-[#93AFBC]/60 text-xs font-bold text-[#202124] bg-white hover:bg-[#F3F1EF] transition cursor-pointer">
                            ${isVi() ? 'Thử phương pháp khác' : 'Try something else'}
                        </button>
                        <button type="button" onclick="window.TempoEmergencySupport.goToStep('safety_checkin')" class="px-6 py-2.5 rounded-xl text-xs font-bold bg-[#8EA28F] hover:bg-[#7D917E] text-white shadow-xs cursor-pointer transition">
                            ${isVi() ? 'Xong →' : 'Done →'}
                        </button>
                    </div>
                </div>
            `;
        } else if (index === 1) {
            // Grounding Activity 2: Slow down (Visually paced respiration)
            container.innerHTML = `
                <div class="space-y-5 text-center">
                    <div class="space-y-1">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#8EA28F]/20 text-[#3B5C43]">
                            ${isVi() ? 'Bước 2 / 3 • Thở Chậm lại' : 'Grounding 2 of 3 • Slow Down'}
                        </span>
                        <h4 class="font-heading text-lg font-bold text-[#202124]">${isVi() ? 'Thở Chậm lại' : 'Slow Down'}</h4>
                        <p class="text-xs text-[#6F6B68] max-w-md mx-auto leading-relaxed">
                            ${isVi() ? 'Hãy thở theo vòng tròn chuyển động. Hít vào nhẹ nhàng bằng mũi, giữ hơi, và thở ra từ từ.' : 'Follow the expanding circle. Inhale gently through your nose, pause, and exhale slowly.'}
                        </p>
                    </div>

                    <div class="h-44 flex items-center justify-center">
                        <div id="grounding-breathing-circle" class="w-32 h-32 rounded-full bg-[#ECC9BA]/35 border-2 border-[#8EA28F] flex flex-col items-center justify-center transition-all duration-1000 shadow-xs">
                            <span id="grounding-breath-phase" class="text-xs font-bold text-[#202124] px-3 text-center leading-snug">${isVi() ? 'Hít vào nhẹ nhàng' : 'Inhale gently'}</span>
                            <span id="grounding-breath-count" class="text-sm font-extrabold text-[#3B5C43] mt-1">4s</span>
                        </div>
                    </div>

                    <div class="flex items-center justify-between pt-2">
                        <button type="button" onclick="window.TempoEmergencySupport.nextGrounding()" class="px-4 py-2.5 rounded-xl border border-[#93AFBC]/60 text-xs font-bold text-[#202124] bg-white hover:bg-[#F3F1EF] transition cursor-pointer">
                            ${isVi() ? 'Thử phương pháp khác' : 'Try something else'}
                        </button>
                        <button type="button" onclick="window.TempoEmergencySupport.goToStep('safety_checkin')" class="px-6 py-2.5 rounded-xl text-xs font-bold bg-[#8EA28F] hover:bg-[#7D917E] text-white shadow-xs cursor-pointer transition">
                            ${isVi() ? 'Xong →' : 'Done →'}
                        </button>
                    </div>
                </div>
            `;
            startGroundingBreathing();
        } else {
            // Grounding Activity 3: Move toward safety
            container.innerHTML = `
                <div class="space-y-4">
                    <div class="p-5 sm:p-6 bg-[#8EA28F]/10 border border-[#8EA28F]/30 rounded-2xl sm:rounded-3xl space-y-3">
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#8EA28F] text-white">
                            ${isVi() ? 'Bước 3 / 3 • Di chuyển đến Nơi An toàn' : 'Grounding 3 of 3 • Move Toward Safety'}
                        </span>
                        <h4 class="font-heading text-lg font-bold text-[#202124]">${isVi() ? 'Di chuyển đến Không gian An toàn' : 'Move Toward Safety'}</h4>
                        <p class="text-xs font-bold text-[#202124]">
                            ${isVi() ? 'Khi bạn đang chờ được hỗ trợ:' : "While you're waiting for support:"}
                        </p>
                        <ul class="text-xs text-[#202124] space-y-1.5 list-disc list-inside font-medium">
                            <li>${isVi() ? 'Ở cùng một người bạn tin tưởng.' : 'Stay with someone you trust.'}</li>
                            <li>${isVi() ? 'Di chuyển đến một nơi an toàn hơn.' : 'Move somewhere safer.'}</li>
                            <li>${isVi() ? 'Tạo khoảng cách với những vật có thể gây tổn thương cho bạn.' : 'Create distance from anything that could hurt you.'}</li>
                        </ul>
                        <div class="pt-2 border-t border-[#ECC9BA]/80 text-xs text-[#202124] space-y-0.5">
                            <p class="font-bold">${isVi() ? 'Bạn không cần giải quyết mọi thứ ngay lúc này.' : "You don't need to solve everything right now."}</p>
                            <p class="text-[#6F6B68]">${isVi() ? 'Lúc này, chỉ cần tập trung giữ an toàn cho bản thân.' : 'For now, just focus on staying safe.'}</p>
                        </div>
                    </div>

                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                        <button type="button" onclick="window.TempoEmergencySupport.copyTrustedMessage()" class="p-3 bg-[#93AFBC]/15 hover:bg-[#93AFBC]/25 text-[#2C4957] border border-[#93AFBC]/40 rounded-xl text-xs font-bold text-center transition flex items-center justify-center space-x-1.5 cursor-pointer shadow-2xs">
                            <svg class="w-4 h-4 text-[#8EA28F]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                            </svg>
                            <span>${isVi() ? 'Liên hệ người bạn tin tưởng' : 'Contact someone I trust'}</span>
                        </button>
                        <button type="button" onclick="window.TempoEmergencySupport.openHumanDrawer()" class="p-3 bg-[#D92D20] hover:bg-[#B42318] text-white rounded-xl text-xs font-bold text-center transition flex items-center justify-center space-x-1.5 shadow-xs cursor-pointer" title="Get immediate help">
                            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                            </svg>
                            <span>${isVi() ? 'Nhận hỗ trợ ngay →' : 'Get support now →'}</span>
                        </button>
                    </div>

                    <div class="flex items-center justify-between pt-2">
                        <button type="button" onclick="window.TempoEmergencySupport.nextGrounding()" class="px-4 py-2.5 rounded-xl border border-[#93AFBC]/60 text-xs font-bold text-[#202124] bg-white hover:bg-[#F3F1EF] transition cursor-pointer">
                            ${isVi() ? 'Tiếp tục tĩnh tâm' : 'Continue grounding'}
                        </button>
                        <button type="button" onclick="window.TempoEmergencySupport.goToStep('safety_checkin')" class="px-6 py-2.5 rounded-xl text-xs font-bold bg-[#8EA28F] hover:bg-[#7D917E] text-white shadow-xs cursor-pointer transition">
                            ${isVi() ? 'Xong →' : 'Done →'}
                        </button>
                    </div>
                </div>
            `;
        }
    }

    function nextGrounding() {
        stopBreathing();
        currentGroundingIndex = (currentGroundingIndex + 1) % 3;
        renderGroundingActivity(currentGroundingIndex);
    }

    function startGroundingBreathing() {
        const circle = document.getElementById('grounding-breathing-circle');
        const phaseText = document.getElementById('grounding-breath-phase');
        const countText = document.getElementById('grounding-breath-count');

        if (circle) circle.classList.add('breathing-circle-active');

        const phases = isVi() ? [
            { label: 'Hít vào nhẹ nhàng', sec: 4 },
            { label: 'Giữ hơi êm dịu', sec: 4 },
            { label: 'Thở ra từ từ', sec: 4 },
            { label: 'Nghỉ ngơi', sec: 4 }
        ] : [
            { label: 'Inhale gently', sec: 4 },
            { label: 'Hold softly', sec: 4 },
            { label: 'Exhale slowly', sec: 4 },
            { label: 'Rest', sec: 4 }
        ];

        let pIdx = 0;
        let s = 4;

        breathingInterval = setInterval(() => {
            if (s > 1) {
                s--;
            } else {
                pIdx = (pIdx + 1) % phases.length;
                s = phases[pIdx].sec;
            }
            if (phaseText) phaseText.textContent = phases[pIdx].label;
            if (countText) countText.textContent = `${s}s`;
        }, 1000);
    }

    function stopBreathing() {
        if (breathingInterval) {
            clearInterval(breathingInterval);
            breathingInterval = null;
        }
    }

    // STEP 4: QUICK SAFETY CHECK-IN (NO NUMERICAL SCORE)
    function handleSafetyCheckin(feeling) {
        if (feeling === 'unsafe') {
            // STEP 5A: User still does not feel safe
            isSafetyMode = true;
            goToStep('still_unsafe');
        } else if (feeling === 'distressed_calmer') {
            // STEP 5B: Still distressed but a little calmer
            isSafetyMode = false;
            goToStep('calmer_options');
        } else {
            // STEP 5B: Feels calmer now
            isSafetyMode = false;
            goToStep('calmer_options');
        }
    }

    // STEP 6: UNDERSTAND THE PROBLEM (NATURAL LANGUAGE - NO MEDICAL DIAGNOSIS)
    function handleAnalyzeProblem() {
        const input = document.getElementById('emergency-problem-text');
        const text = input ? input.value.trim() : '';

        if (!text) {
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast(isVi() ? "Vui lòng mô tả ngắn gọn điều đang khiến bạn cảm thấy khó khăn." : "Please briefly describe what feels most difficult right now.");
            }
            return;
        }

        // Extract practical, non-clinical stressors
        const lower = text.toLowerCase();
        const detectedFactors = [];

        if (lower.includes('deadline') || lower.includes('due') || lower.includes('tomorrow') || lower.includes('report') || lower.includes('exam') || lower.includes('paper')) {
            detectedFactors.push({ 
                title: isVi() ? 'Áp lực Deadline & Khối lượng Bài vở' : 'Deadline Overload & Academic Workload', 
                tip: isVi() ? 'Nhiều nhiệm vụ dồn dập đang cạnh tranh sự tập trung của bạn.' : 'Multiple impending tasks competing for active cognitive bandwidth.' 
            });
        }
        if (lower.includes('sleep') || lower.includes('tired') || lower.includes('exhaust') || lower.includes('night') || lower.includes('drained') || lower.includes('ngủ') || lower.includes('mệt')) {
            detectedFactors.push({ 
                title: isVi() ? 'Thiếu ngủ & Kiệt sức Thể chất' : 'Physical Sleep Debt', 
                tip: isVi() ? 'Sự mệt mỏi thể chất làm tăng đáng kể cảm giác áp lực và cản trở suy nghĩ.' : 'Physical depletion significantly increases perceived difficulty and cognitive friction.' 
            });
        }
        if (lower.includes('start') || lower.includes('freeze') || lower.includes('stuck') || lower.includes('blank') || lower.includes('bắt đầu') || lower.includes('tê liệt')) {
            detectedFactors.push({ 
                title: isVi() ? 'Khó khăn khi Bắt đầu' : 'Task Initiation Freeze', 
                tip: isVi() ? 'Sự trì hoãn ban đầu tạo vòng lặp tránh né. Hành động siêu nhỏ sẽ giúp vượt qua.' : 'Initial friction creates an avoidance loop. Breaking the activation threshold is key.' 
            });
        }
        if (lower.includes('alone') || lower.includes('isolate') || lower.includes('nobody') || lower.includes('secret') || lower.includes('một mình') || lower.includes('cô đơn')) {
            detectedFactors.push({ 
                title: isVi() ? 'Gánh vác Áp lực Một mình' : 'Carrying Stress Alone', 
                tip: isVi() ? 'Chịu đựng áp lực trong cô lập làm tăng cảm giác khủng hoảng.' : 'Carrying academic panic in isolation magnifies emotional distress.' 
            });
        }
        if (lower.includes('fight') || lower.includes('roommate') || lower.includes('argue') || lower.includes('friend') || lower.includes('family') || lower.includes('conflict') || lower.includes('cãi') || lower.includes('bạn')) {
            detectedFactors.push({ 
                title: isVi() ? 'Xung đột Mối quan hệ' : 'Interpersonal Conflict', 
                tip: isVi() ? 'Căng thẳng giao tiếp làm phân tán tâm trí khỏi việc học.' : 'Relational tension drawing attention away from study focus.' 
            });
        }

        if (detectedFactors.length === 0) {
            detectedFactors.push({ 
                title: isVi() ? 'Áp lực Công việc Cấp bách' : 'Immediate Task Pressure', 
                tip: isVi() ? 'Nhiều trách nhiệm đang chờ giải quyết gây quá tải nhận thức.' : 'High concentration of pending obligations creating cognitive overload.' 
            });
        }

        renderProblemAnalysis(text, detectedFactors);
        goToStep('problem_solving');
    }

    function renderProblemAnalysis(rawText, factors) {
        const container = document.getElementById('problem-factors-list');
        if (container) {
            container.innerHTML = factors.map(f => `
                <div class="p-3 bg-[#FFF9F4] border border-[#ECC9BA]/70 rounded-xl space-y-1">
                    <span class="text-xs font-bold text-[#202124]">${f.title}</span>
                    <p class="text-[11px] text-[#6F6B68] leading-relaxed">${f.tip}</p>
                </div>
            `).join('');
        }

        // Bridge to ONE Next Action
        let oneAction = isVi() 
            ? "Mở bài báo cáo và liệt kê 3 mục bạn vẫn cần hoàn thành."
            : "Open your Marketing report and list the three sections you still need to complete.";
        let estimatedTime = isVi() ? "5 phút" : "5 minutes";

        const lower = rawText.toLowerCase();
        if (lower.includes('slide') || lower.includes('presentation') || lower.includes('thuyết trình')) {
            oneAction = isVi()
                ? "Mở phần mềm trình chiếu và đặt tiêu đề cho Slide 1, 2, 3 bằng các gạch đầu dòng thô."
                : "Open your presentation software and title Slide 1, Slide 2, and Slide 3 with rough bullet headers.";
            estimatedTime = isVi() ? "4 phút" : "4 minutes";
        } else if (lower.includes('math') || lower.includes('problem') || lower.includes('toán') || lower.includes('bài tập')) {
            oneAction = isVi()
                ? "Chỉ đọc Bài 1 và ghi lại hai dữ kiện đã cho trong đề bài."
                : "Read Problem 1 only and write down the two known variables given in the prompt.";
            estimatedTime = isVi() ? "5 phút" : "5 minutes";
        } else if (lower.includes('email') || lower.includes('giảng viên') || lower.includes('thầy') || lower.includes('cô') || lower.includes('extension')) {
            oneAction = isVi()
                ? "Soạn một email 2 câu xin gia hạn thêm 24 giờ cho bài nộp sắp tới của bạn."
                : "Draft a 2-sentence email to request a 24-hour extension on your upcoming submission.";
            estimatedTime = isVi() ? "3 phút" : "3 minutes";
        } else if (lower.includes('read') || lower.includes('chapter') || lower.includes('đọc') || lower.includes('sách')) {
            oneAction = isVi()
                ? "Mở bài đọc được giao và chỉ đọc lướt các tiêu đề mục cùng đoạn kết luận."
                : "Open the assigned reading and read just the section headers and conclusion paragraph.";
            estimatedTime = isVi() ? "5 phút" : "5 minutes";
        }

        const actionEl = document.getElementById('emergency-solved-action');
        const timeEl = document.getElementById('emergency-solved-time');
        if (actionEl) actionEl.textContent = oneAction;
        if (timeEl) timeEl.textContent = isVi() ? `Thời lượng ước tính: ${estimatedTime} • Không áp lực` : `Estimated time: ${estimatedTime} • Low pressure`;
    }

    function launchImmediateMicroAction() {
        const actionEl = document.getElementById('emergency-solved-action');
        const defaultAction = isVi() ? "Mở tài liệu của bạn và liệt kê 3 đề mục đơn giản." : "Open your document and list 3 rough section headers.";
        const actionText = actionEl ? actionEl.textContent : defaultAction;

        closeModal(true);

        // Connect directly into Focus Zone
        if (window.TempoFocusZone) {
            window.TempoFocusZone.open({
                taskName: isVi() ? 'Bước Vi mô Ngay lúc này' : 'Immediate Micro Step',
                nextAction: actionText
            });
        } else if (window.TempoTriage) {
            window.TempoTriage.launchFocusMode();
        }

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(isVi() ? "Bắt đầu với hành động nhỏ 5 phút của bạn. Bạn làm được mà." : "Start with your 5-minute micro step. You've got this.");
        }
    }

    // HUMAN SUPPORT DRAWER CONTROLS
    function openHumanDrawer() {
        const drawer = document.getElementById('human-support-drawer');
        if (drawer) {
            drawer.classList.remove('hidden');
        }
    }

    function closeHumanDrawer() {
        const drawer = document.getElementById('human-support-drawer');
        if (drawer) {
            drawer.classList.add('hidden');
        }
    }

    function toggleHumanDrawer() {
        const drawer = document.getElementById('human-support-drawer');
        if (drawer) {
            if (drawer.classList.contains('hidden')) {
                openHumanDrawer();
            } else {
                closeHumanDrawer();
            }
        }
    }

    // Entry point when clicking SOS in top nav or headers
    // CRITICAL: Opens calm Step 1 Initial Check-In (does NOT auto-pop hotline drawer)
    function openSOS() {
        openModal();
        isSafetyMode = true; // Sets safety mode header/banner ready
        goToStep('checkin');
        // Do NOT call openHumanDrawer()!
    }

    return {
        init,
        openModal,
        closeModal,
        openSOS,
        goToStep,
        handleInitialCheckin,
        nextGrounding,
        handleSafetyCheckin,
        handleAnalyzeProblem,
        launchImmediateMicroAction,
        openHumanDrawer,
        closeHumanDrawer,
        toggleHumanDrawer,
        copyTrustedMessage,
        submitOfflineMessage
    };
})();
