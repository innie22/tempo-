/**
 * Tempo Application Core Controller
 * Single-page router, role switcher, toast notifications, confetti celebrations.
 */

window.TempoApp = (function() {
    let currentRole = 'student'; // 'student' | 'admin'
    let currentTab = 'today';

    async function init() {
        bindNavigation();
        bindRoleSwitcher();
        initConfettiCanvas();

        // 1. Initialize standalone sub-modules
        if (window.TempoTriage) window.TempoTriage.init();
        if (window.TempoStress) window.TempoStress.init();
        if (window.TempoRoutine) window.TempoRoutine.init();
        if (window.TempoKnowledge) window.TempoKnowledge.init();
        if (window.TempoSupport) window.TempoSupport.init();
        if (window.TempoAdmin) window.TempoAdmin.init();
        if (window.TempoEmergencySupport) window.TempoEmergencySupport.init();
        if (window.TempoVolunteer) window.TempoVolunteer.init();
        if (window.TempoCommunity) window.TempoCommunity.init();
        if (window.TempoStressRelief) window.TempoStressRelief.init();

        // 2. Initialize Supabase Auth and await session resolution (AUTH_LOADING -> AUTHENTICATED / ANONYMOUS)
        if (window.TempoAuth) {
            await window.TempoAuth.init();
            if (typeof window.TempoAuth.waitForAuthResolution === 'function') {
                await window.TempoAuth.waitForAuthResolution();
            }
        }

        // 3. Initialize centralized Plan Store with resolved identity (authenticated user or guest)
        if (window.TempoPlanStore) {
            await window.TempoPlanStore.init();
        }

        // 4. Hydrate Emergency Flow with active plan or draft for resolved user
        if (window.TempoEmergencyFlow) {
            await window.TempoEmergencyFlow.init();
        }

        if (window.TempoFocusZone) window.TempoFocusZone.init();
        if (window.TempoPersonalSpace) window.TempoPersonalSpace.init();

        // 5. Initialize Mode system with hydrated plan and auth state
        if (window.TempoMode) {
            window.TempoMode.init();
        }

        // UI Interactions
        initGlobalSearch();
        initQuickToolsDropdown();
        initMainRoutingFlow();
        initWhatIsTempoModal();

        // Handle hash navigation with resolved user & plan state
        window.addEventListener('hashchange', handleHashChange);
        if (window.location.hash) {
            handleHashChange();
        } else {
            navigateTo('today');
        }
    }

    function bindNavigation() {
        document.querySelectorAll('[data-nav]').forEach(el => {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                const target = e.currentTarget.dataset.nav;
                navigateTo(target);
            });
        });
    }

    function bindRoleSwitcher() {
        const roleBtn = document.getElementById('btn-toggle-role');
        if (roleBtn) {
            roleBtn.addEventListener('click', () => {
                currentRole = currentRole === 'student' ? 'admin' : 'student';
                updateRoleUI();
            });
        }
    }

    function updateRoleUI() {
        const label = document.getElementById('current-role-label');
        const adminTab = document.getElementById('nav-tab-admin');
        const roleBanner = document.getElementById('role-indicator-banner');

        if (currentRole === 'admin') {
            if (label) label.textContent = 'Advisor: Dr. Elena Vance';
            if (adminTab) adminTab.classList.remove('hidden');
            if (roleBanner) {
                roleBanner.classList.remove('hidden');
                roleBanner.innerHTML = `
                    <div class="max-w-6xl mx-auto flex items-center justify-between">
                        <span>👩‍🏫 You are viewing as <strong>Dr. Elena Vance (Campus Wellbeing Advisor)</strong>. You can answer student tickets and publish tips.</span>
                        <button onclick="window.TempoApp.setRole('student')" class="underline text-xs font-semibold ml-4">Switch to Student View</button>
                    </div>
                `;
            }
            navigateTo('admin');
            showToast("Switched to Advisor View. You can now triage student tickets and publish tips.");
        } else {
            const profile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
            if (label) label.textContent = profile?.full_name ? `Student: ${profile.full_name}` : 'Student View';
            if (adminTab) adminTab.classList.add('hidden');
            if (roleBanner) roleBanner.classList.add('hidden');
            navigateTo('today');
            showToast("Switched to Student View.");
        }
    }

    function setRole(role) {
        currentRole = role;
        updateRoleUI();
    }

    function navigateTo(tabId, subTab) {
        if (tabId === 'what-is-tempo') {
            tabId = 'about';
        }
        if (tabId === 'hub' || tabId === 'learn-solve') {
            tabId = 'learn';
        }
        if (tabId === 'notes') {
            tabId = 'tool-notes';
        }
        if (tabId === 'tools' || tabId === 'enjoy-tempo-tools') {
            scrollToEnjoyTempoTools();
            return;
        }

        // Shared Authenticated Tool: Strack (Self-check)
        if (tabId === 'strack' || tabId === 'stress-check') {
            if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                window.TempoMode.openStrack('open');
                return;
            }
        }

        // Shared Authenticated Tool: Wplan (Working Plan)
        const isWplan = (tabId === 'plan-workspace');
        if (isWplan && (!window.TempoAuth || !window.TempoAuth.getCurrentUser())) {
            const src = window.TempoMode && window.TempoMode.getSourceContext ? window.TempoMode.getSourceContext() : 'entry';
            if (window.TempoMode && typeof window.TempoMode.setPendingIntent === 'function') {
                window.TempoMode.setPendingIntent({
                    destination: 'plan-workspace',
                    action: 'navigate',
                    source: src,
                    requiredParams: {},
                    type: 'tool',
                    tool: 'plan-workspace',
                    sourceContext: src
                });
            }
            if (window.TempoAuth && typeof window.TempoAuth.openSignInModal === 'function') {
                window.TempoAuth.openSignInModal();
            }
            if (typeof showToast === 'function') {
                showToast("Please sign in or create an account to access Working Plan.");
            }
            return;
        }

        // Shared Authenticated Area: Personal Space (Saved, Library, Account, Settings)
        if (tabId === 'personal-space') {
            if (!window.TempoAuth || !window.TempoAuth.getCurrentUser()) {
                const src = window.TempoMode && window.TempoMode.getSourceContext ? window.TempoMode.getSourceContext() : 'entry';
                if (window.TempoMode && typeof window.TempoMode.setPendingIntent === 'function') {
                    window.TempoMode.setPendingIntent({
                        destination: 'personal-space',
                        action: 'navigate',
                        source: src,
                        requiredParams: { tab: subTab || 'saved' },
                        type: 'tool',
                        tool: 'personal-space',
                        sourceContext: src
                    });
                }
                if (window.TempoAuth && typeof window.TempoAuth.openSignInModal === 'function') {
                    window.TempoAuth.openSignInModal();
                }
                if (typeof showToast === 'function') {
                    showToast("Please sign in or create an account to access Personal Space.");
                }
                return;
            }
        }

        // Direct Messages route alias
        if (tabId === 'direct-messages') {
            navigateTo('posts', 'messages');
            return;
        }

        // Tempo Posts / Direct Messages (Community modal experience)
        if (tabId === 'posts') {
            const section = subTab === 'messages' ? 'messages' : 'feed';
            if (section === 'messages' && (!window.TempoAuth || !window.TempoAuth.getCurrentUser())) {
                const src = window.TempoMode && window.TempoMode.getSourceContext ? window.TempoMode.getSourceContext() : 'entry';
                if (window.TempoMode && typeof window.TempoMode.setPendingIntent === 'function') {
                    window.TempoMode.setPendingIntent({
                        destination: 'posts',
                        action: 'navigate',
                        source: src,
                        requiredParams: { section: 'messages' },
                        type: 'tool',
                        tool: 'posts',
                        sourceContext: src
                    });
                }
                if (window.TempoAuth && typeof window.TempoAuth.openSignInModal === 'function') {
                    window.TempoAuth.openSignInModal();
                }
                if (typeof showToast === 'function') {
                    showToast("Please sign in or create an account to view Direct Messages.");
                }
                return;
            }

            if (window.TempoCommunity && typeof window.TempoCommunity.openCommunityModal === 'function') {
                window.TempoCommunity.openCommunityModal(section);
            }
            window.location.hash = section === 'messages' ? '#posts?section=messages' : '#posts';
            return;
        }

        // Shared Assessment Tool: Ucheck
        if (tabId === 'unclear-mode') {
            if (window.TempoMode && typeof window.TempoMode.openUcheck === 'function') {
                window.TempoMode.openUcheck({ sourceContext: window.TempoMode.getSourceContext ? window.TempoMode.getSourceContext() : 'entry' });
                return;
            }
        }

        // Active Contexts: emergency & recovery
        if ((tabId === 'emergency' || tabId === 'recovery-mode') && (!window.TempoAuth || !window.TempoAuth.getCurrentUser())) {
            const targetContext = tabId === 'emergency' ? 'emergency' : 'recovery';
            if (window.TempoMode && typeof window.TempoMode.requestContext === 'function') {
                window.TempoMode.requestContext(targetContext, 'navigation');
                return;
            } else if (window.TempoMode) {
                window.TempoMode.requestMode(targetContext);
                return;
            }
        }

        currentTab = tabId;
        if (tabId === 'personal-space') {
            const activeSub = subTab || (window.TempoPersonalSpace && window.TempoPersonalSpace.getActiveTab()) || 'saved';
            window.location.hash = `#personal-space?tab=${activeSub}`;
        } else {
            window.location.hash = `#${tabId}`;
        }

        // Hide all screens
        document.querySelectorAll('.screen-container').forEach(screen => {
            screen.classList.add('hidden');
        });

        // Show active screen
        const targetScreen = document.getElementById(`screen-${tabId}`) || (tabId === 'learn' ? document.getElementById('screen-hub') : null);
        if (targetScreen) {
            targetScreen.classList.remove('hidden');
        }

        // If on today tab, synchronize active mode dashboard with strict mutual exclusivity
        if (tabId === 'today') {
            if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
                window.TempoMode.renderActiveModeHome();
            } else if (window.TempoMode) {
                const mode = window.TempoMode.getMode();
                if (mode === 'emergency') window.TempoMode.renderEmodeHome();
                else if (mode === 'recovery') window.TempoMode.renderRmodeHome();
                else window.TempoMode.restoreDefaultHome();
            }
        }

        // If entering Recovery Mode via route, activate recovery mode and route to today
        if (tabId === 'recovery-mode') {
            const curContext = window.TempoMode && window.TempoMode.getActiveContext ? window.TempoMode.getActiveContext() : null;
            if (curContext !== 'recovery' && curContext !== null) {
                // Prevent browser back from flipping away from emergency to recovery
                navigateTo('today');
                return;
            }
            if (window.TempoMode && window.TempoMode.transitionContext && curContext !== 'recovery') {
                window.TempoMode.transitionContext('recovery', { silent: true });
            }
            navigateTo('today');
            return;
        }

        // If entering Emergency Mode, guard against accidental mode flip from recovery
        if (tabId === 'emergency') {
            const curContext = window.TempoMode && window.TempoMode.getActiveContext ? window.TempoMode.getActiveContext() : null;
            if (curContext === 'recovery') {
                // Invariant 26: Browser Back must not flip activeContext from recovery to emergency
                navigateTo('today');
                return;
            }
            if (curContext !== 'emergency' && window.TempoMode && window.TempoMode.transitionContext) {
                window.TempoMode.transitionContext('emergency', { silent: true });
            }
            if (window.TempoEmergencyFlow) {
                const stage = window.TempoEmergencyFlow.getCurrentStage();
                window.TempoEmergencyFlow.goToStage(stage || 'entry');
            }
        }

        // If entering Plan Workspace, render workspace
        if (tabId === 'plan-workspace') {
            if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
                window.TempoPlanWorkspace.render();
            }
        }

        // Update desktop nav item active states
        document.querySelectorAll('header nav a[data-nav]').forEach(el => {
            const isMatch = el.dataset.nav === tabId;
            if (isMatch) {
                el.classList.add('text-[#FF6B2C]', 'font-semibold', 'bg-[#FFE9DC]');
                el.classList.remove('text-[#6F6B68]', 'hover:text-[#202124]', 'hover:bg-[#F3F1EF]', 'text-gray-600', 'hover:text-gray-900', 'text-emerald-800', 'bg-emerald-50');
            } else {
                el.classList.remove('text-[#FF6B2C]', 'font-semibold', 'bg-[#FFE9DC]', 'text-emerald-800', 'bg-emerald-50');
                el.classList.add('text-[#6F6B68]', 'hover:text-[#202124]', 'hover:bg-[#F3F1EF]');
            }
        });

        // Update mobile bottom nav items
        document.querySelectorAll('nav.md\\:hidden a[data-nav]').forEach(el => {
            const isMatch = el.dataset.nav === tabId;
            if (isMatch) {
                el.classList.add('text-[#FF6B2C]', 'font-semibold');
                el.classList.remove('text-gray-500');
            } else {
                el.classList.remove('text-[#FF6B2C]', 'font-semibold');
                el.classList.add('text-gray-500');
            }
        });

        // Screen-specific activations
        if (tabId === 'admin' && window.TempoAdmin) {
            window.TempoAdmin.loadVolunteerApplications();
        }
        if (tabId === 'volunteer-dashboard' && window.TempoVolunteer) {
            window.TempoVolunteer.render();
        }
        if (tabId === 'about') {
            initAboutStackedCards();
        }
        if (tabId === 'learn') {
            if (window.TempoKnowledge && typeof window.TempoKnowledge.init === 'function') {
                window.TempoKnowledge.init();
            }
        }
        if (tabId === 'personal-space' && window.TempoPersonalSpace) {
            window.TempoPersonalSpace.selectTab(subTab || 'saved', false);
        }

        // Scroll top gently
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function scrollToEnjoyTempoTools() {
        const doScroll = () => {
            const el = document.getElementById('enjoy-tempo-tools')
                || document.querySelector('[data-tempo-ui="urgent-lower-section"]')
                || Array.from(document.querySelectorAll('h2')).find(h => (h.textContent || '').includes('Enjoy Tempo Tools'));
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        };

        const todayScreen = document.getElementById('screen-today');
        const isTodayVisible = todayScreen && !todayScreen.classList.contains('hidden');

        if (isTodayVisible) {
            doScroll();
        } else {
            navigateTo('today');
            setTimeout(doScroll, 100);
        }
    }

    function handleHashChange() {
        const rawHash = window.location.hash.replace('#', '');
        if (!rawHash) return;

        if (rawHash.startsWith('personal-space')) {
            const queryPart = rawHash.includes('?') ? rawHash.split('?')[1] : '';
            const params = new URLSearchParams(queryPart);
            const subTab = params.get('tab') || 'saved';
            navigateTo('personal-space', subTab);
        } else if (rawHash.startsWith('posts')) {
            const queryPart = rawHash.includes('?') ? rawHash.split('?')[1] : '';
            const params = new URLSearchParams(queryPart);
            const section = params.get('section') || 'feed';
            navigateTo('posts', section);
        } else if (rawHash.startsWith('direct-messages')) {
            navigateTo('posts', 'messages');
        } else if (rawHash === 'hub' || rawHash === 'learn-solve' || rawHash === 'learn') {
            navigateTo('learn');
        } else {
            navigateTo(rawHash);
        }
    }

    function showToast(message, duration = 3500) {
        const toast = document.getElementById('app-toast');
        if (!toast) return;

        toast.textContent = message;
        toast.classList.remove('opacity-0', 'translate-y-4', 'pointer-events-none');
        toast.classList.add('opacity-100', 'translate-y-0');

        setTimeout(() => {
            toast.classList.remove('opacity-100', 'translate-y-0');
            toast.classList.add('opacity-0', 'translate-y-4', 'pointer-events-none');
        }, duration);
    }

    // Gentle Canvas Confetti
    function initConfettiCanvas() {
        const canvas = document.createElement('canvas');
        canvas.id = 'confetti-canvas';
        document.body.appendChild(canvas);
    }

    function triggerConfetti() {
        const canvas = document.getElementById('confetti-canvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        const particles = [];
        const colors = ['#2D6A4F', '#52B788', '#D97706', '#3D5A80', '#A7D7C5'];

        for (let i = 0; i < 45; i++) {
            particles.push({
                x: canvas.width / 2 + (Math.random() - 0.5) * 200,
                y: canvas.height * 0.45,
                vx: (Math.random() - 0.5) * 8,
                vy: -(Math.random() * 8 + 4),
                size: Math.random() * 7 + 4,
                color: colors[Math.floor(Math.random() * colors.length)],
                alpha: 1
            });
        }

        let animationFrame;
        function update() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            let active = false;

            particles.forEach(p => {
                p.x += p.vx;
                p.y += p.vy;
                p.vy += 0.25; // gravity
                p.alpha -= 0.015;

                if (p.alpha > 0) {
                    active = true;
                    ctx.save();
                    ctx.globalAlpha = p.alpha;
                    ctx.fillStyle = p.color;
                    ctx.fillRect(p.x, p.y, p.size, p.size);
                    ctx.restore();
                }
            });

            if (active) {
                animationFrame = requestAnimationFrame(update);
            } else {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
            }
        }
        update();
    }

    // =========================================================================
    // GLOBAL SEARCH IMPLEMENTATION
    // =========================================================================
    function initGlobalSearch() {
        const searchInput = document.getElementById('global-search-input');
        const searchDropdown = document.getElementById('global-search-results-dropdown');
        if (!searchInput || !searchDropdown) return;

        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim().toLowerCase();
            if (!query) {
                searchDropdown.classList.add('hidden');
                return;
            }
            renderSearchResults(query, searchDropdown);
        });

        // Close search on click outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
                searchDropdown.classList.add('hidden');
            }
        });

        searchInput.addEventListener('focus', () => {
            if (searchInput.value.trim()) {
                searchDropdown.classList.remove('hidden');
            }
        });
    }

    function renderSearchResults(query, dropdown) {
        const results = [];

        // 1. Searchable Tools
        const tools = [
            { name: 'Focus Zone', category: 'Tool', desc: 'Focus with intentional breaks. Default 45 min focus / 15 min rest.', action: () => { if (window.TempoFocusZone) window.TempoFocusZone.openQuickEntry(); else window.TempoTriage.launchFocusMode(); } },
            { name: 'Breathing (Box Breathing)', category: 'Tool', desc: 'A quick 4-4-4-4 breathing exercise to calm your mind.', action: () => { window.TempoStressRelief.openBreathing({ context: 'home' }); } },
            { name: 'Quick Stress Relief', category: 'Tool', desc: 'Simple micro-actions (1m, 3m, 5m) to ease stress in minutes.', action: () => { window.TempoStressRelief.openLibrary({ context: 'home' }); } },
            { name: 'Self-check', category: 'Tool', desc: 'Track your stress signals and wellbeing habits across 6 dimensions.', action: () => { navigateTo('strack'); } },
            { name: 'Urgent Mode (Deadline Triage)', category: 'Tool', desc: 'Academic triage: unfreeze panic and extract the ONE next action.', action: () => { navigateTo('emergency'); } },
            { name: 'Routine & Habit Tracker', category: 'Tool', desc: 'Build gentle, non-punitive habits and daily routine blocks.', action: () => { navigateTo('routine'); } },
            { name: 'SOS Safety Support', category: 'Safety', desc: 'Emergency Medical Support (115), HOPE Suicide Prevention Hotline (0865 044 400), and urgent safety help.', action: () => { window.TempoEmergencySupport.openSOS(); } }
        ];

        tools.forEach(t => {
            if (t.name.toLowerCase().includes(query) || t.desc.toLowerCase().includes(query)) {
                results.push(t);
            }
        });

        // 2. Tempo Posts
        if (window.TempoCommunity) {
            const posts = window.TempoCommunity.getAllPosts();
            posts.forEach(p => {
                if (p.content.toLowerCase().includes(query) || p.tag.toLowerCase().includes(query) || p.authorName.toLowerCase().includes(query)) {
                    results.push({
                        name: `${p.tag} • ${p.authorName}`,
                        category: 'Tempo Post',
                        desc: p.content.slice(0, 80) + '...',
                        action: () => { window.TempoCommunity.openCommunityModal(); }
                    });
                }
            });
        }

        // 3. Knowledge Guides
        if (window.TEMPO_DATA && window.TEMPO_DATA.articles) {
            window.TEMPO_DATA.articles.forEach(art => {
                if (art.title.toLowerCase().includes(query) || art.summary.toLowerCase().includes(query) || art.category.toLowerCase().includes(query)) {
                    results.push({
                        name: art.title,
                        category: 'Guide',
                        desc: art.summary.slice(0, 80) + '...',
                        action: () => { 
                            navigateTo('learn');
                            if (window.TempoKnowledge) window.TempoKnowledge.openArticle(art.id);
                        }
                    });
                }
            });
        }

        // 4. Topic Hashtags
        const topics = ['#Deadline', '#MentalHealth', '#Focus', '#Recovery', '#ExamSeason', '#Sleep'];
        topics.forEach(tag => {
            if (tag.toLowerCase().includes(query)) {
                results.push({
                    name: `Topic: ${tag}`,
                    category: 'Hashtag',
                    desc: `View student conversations and experiences about ${tag}`,
                    action: () => { window.TempoCommunity.openCommunityModal(); }
                });
            }
        });

        dropdown.classList.remove('hidden');

        if (results.length === 0) {
            dropdown.innerHTML = `
                <div class="p-5 text-center space-y-1.5">
                    <p class="text-xs font-bold text-[#202124]">No matches found for "${escapeHtml(query)}"</p>
                    <p class="text-[11px] text-[#6F6B68]">Try searching for <strong>Focus Zone</strong>, <strong>Breathing</strong>, <strong>#Deadline</strong>, or <strong>Self-check</strong>.</p>
                </div>
            `;
            return;
        }

        dropdown.innerHTML = `
            <div class="p-2 space-y-1 max-h-72 overflow-y-auto">
                ${results.slice(0, 5).map((res, i) => `
                    <div id="search-item-${i}" class="p-2.5 hover:bg-[#FFF4EC] rounded-xl cursor-pointer transition flex items-start justify-between group">
                        <div class="space-y-0.5 max-w-[85%]">
                            <div class="flex items-center space-x-1.5">
                                <span class="text-xs font-bold text-[#202124] group-hover:text-[#FF6B2C] transition">${res.name}</span>
                                <span class="text-[9px] uppercase tracking-wider font-semibold px-1.5 py-0.5 bg-stone-100 text-stone-600 rounded">${res.category}</span>
                            </div>
                            <p class="text-[11px] text-[#6F6B68] truncate">${res.desc}</p>
                        </div>
                        <span class="text-xs text-[#FF6B2C] opacity-0 group-hover:opacity-100 transition-opacity font-bold mt-1">→</span>
                    </div>
                `).join('')}
            </div>
        `;

        results.slice(0, 5).forEach((res, i) => {
            const el = document.getElementById(`search-item-${i}`);
            if (el) {
                el.addEventListener('click', () => {
                    dropdown.classList.add('hidden');
                    const searchInput = document.getElementById('global-search-input');
                    if (searchInput) searchInput.value = '';
                    res.action();
                });
            }
        });
    }

    // =========================================================================
    // QUICK TOOLS NAVIGATION DROPDOWN
    // =========================================================================
    function initQuickToolsDropdown() {
        const btn = document.getElementById('nav-btn-quick-tools');
        const dropdown = document.getElementById('nav-quick-tools-dropdown');
        if (!btn || !dropdown) return;

        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('hidden');
        });

        document.addEventListener('click', (e) => {
            if (!dropdown.contains(e.target) && !btn.contains(e.target)) {
                dropdown.classList.add('hidden');
            }
        });
    }

    // =========================================================================
    // MAIN ROUTING STATE SELECTION
    // =========================================================================
    // MAIN ROUTING STATE SELECTION (Find Your Next Step)
    // =========================================================================
    function initMainRoutingFlow() {
        const ctaBtn = document.getElementById('btn-hero-figure-start');
        const modal = document.getElementById('modal-routing-selection');
        const closeBtn = document.getElementById('btn-close-routing-modal');

        function openModal() {
            const m = document.getElementById('modal-routing-selection');
            if (!m) return;
            m.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
            // Accessibility focus on first card or close button
            const firstCard = m.querySelector('.state-choice-card');
            if (firstCard) {
                firstCard.focus();
            }
        }

        function closeModal() {
            const m = document.getElementById('modal-routing-selection');
            if (!m) return;
            m.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
            const cta = document.getElementById('btn-hero-figure-start');
            if (cta) {
                cta.focus();
            }
        }

        if (ctaBtn) {
            ctaBtn.addEventListener('click', openModal);
        }

        document.addEventListener('click', (e) => {
            const target = e.target && e.target.closest ? e.target.closest('#btn-hero-figure-start') : null;
            if (target) {
                e.preventDefault();
                openModal();
            }
        });

        if (closeBtn) {
            closeBtn.addEventListener('click', closeModal);
        }

        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    closeModal();
                }
            });
        }

        window.addEventListener('keydown', (e) => {
            const m = document.getElementById('modal-routing-selection');
            if (e.key === 'Escape' && m && !m.classList.contains('hidden')) {
                closeModal();
            }
        });
    }

    function selectRoutingState(state) {
        const modal = document.getElementById('modal-routing-selection');
        if (modal) {
            modal.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        }

        if (state === 'urgent') {
            if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.queueResetPopup === 'function') {
                window.TempoUrmodeFlow.queueResetPopup();
            }
            if (window.TempoMode && typeof window.TempoMode.requestContext === 'function') {
                window.TempoMode.requestContext('emergency', 'entry');
            } else if (window.TempoMode) {
                window.TempoMode.requestMode('emergency');
            } else {
                navigateTo('emergency');
            }
        } else if (state === 'recovering') {
            if (window.TempoMode && typeof window.TempoMode.requestContext === 'function') {
                window.TempoMode.requestContext('recovery', 'entry');
            } else if (window.TempoMode) {
                window.TempoMode.requestMode('recovery');
            } else {
                navigateTo('recovery-mode');
            }
        } else if (state === 'unclear') {
            if (window.TempoMode && typeof window.TempoMode.openUcheck === 'function') {
                window.TempoMode.openUcheck({ sourceContext: 'entry' });
            } else if (window.TempoMode) {
                window.TempoMode.requestMode('unclear');
            } else {
                navigateTo('unclear-mode');
            }
        } else if (state === 'unsafe') {
            if (window.TempoEmergencySupport) {
                window.TempoEmergencySupport.openSOS();
            }
        }
    }

    // =========================================================================
    // ABOUT TEMPO PAGE INTERACTIONS
    // =========================================================================
    function initWhatIsTempoModal() {
        const navBtn = document.getElementById('nav-link-what-is-tempo');
        if (navBtn) {
            navBtn.addEventListener('click', (e) => {
                e.preventDefault();
                navigateTo('about');
            });
        }
        const closeBtn = document.getElementById('btn-close-what-is-tempo');
        const modal = document.getElementById('modal-what-is-tempo');
        if (closeBtn && modal) {
            closeBtn.addEventListener('click', () => {
                modal.classList.add('hidden');
                document.body.classList.remove('overflow-hidden');
            });
        }
    }

    let stackedCardsObserverInitialized = false;
    function initAboutStackedCards() {
        const container = document.querySelector('.about-stacked-cards-container');
        if (!container) return;

        // Skip scroll transforms if reduced motion is preferred
        if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            return;
        }

        const wrappers = Array.from(container.querySelectorAll('.about-stacked-card-wrapper'));
        if (wrappers.length === 0) return;

        function updateStackedCards() {
            if (window.innerWidth < 640) {
                wrappers.forEach(w => {
                    const card = w.querySelector('.about-stacked-card');
                    if (card) {
                        card.style.transform = '';
                        card.style.filter = '';
                    }
                });
                return;
            }

            wrappers.forEach((wrapper, index) => {
                const card = wrapper.querySelector('.about-stacked-card');
                if (!card) return;

                if (index < wrappers.length - 1) {
                    const nextWrapper = wrappers[index + 1];
                    const nextRect = nextWrapper.getBoundingClientRect();
                    const currentRect = wrapper.getBoundingClientRect();

                    const overlapDistance = currentRect.top - nextRect.top;
                    if (overlapDistance <= 0) {
                        card.style.transform = 'scale(1)';
                        card.style.filter = 'brightness(1)';
                    } else {
                        const progress = Math.min(1, Math.max(0, overlapDistance / (currentRect.height || 260)));
                        const scale = 1 - progress * 0.04;
                        const brightness = 1 - progress * 0.03;
                        card.style.transform = `scale(${scale.toFixed(4)})`;
                        card.style.filter = `brightness(${brightness.toFixed(4)})`;
                    }
                } else {
                    card.style.transform = 'scale(1)';
                    card.style.filter = 'brightness(1)';
                }
            });
        }

        if (!stackedCardsObserverInitialized) {
            stackedCardsObserverInitialized = true;
            let ticking = false;
            window.addEventListener('scroll', () => {
                if (!ticking) {
                    window.requestAnimationFrame(() => {
                        updateStackedCards();
                        ticking = false;
                    });
                    ticking = true;
                }
            }, { passive: true });

            window.addEventListener('resize', updateStackedCards, { passive: true });
        }

        updateStackedCards();
    }

    function escapeHtml(str) {
        return (str || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    return {
        init,
        navigateTo,
        scrollToEnjoyTempoTools,
        setRole,
        showToast,
        triggerConfetti,
        selectRoutingState,
        initAboutStackedCards,
        openRoutingModal: () => {
            const m = document.getElementById('modal-routing-selection');
            if (!m) return;
            m.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
            const firstCard = m.querySelector('.state-choice-card');
            if (firstCard) firstCard.focus();
        },
        getCurrentTab: () => currentTab
    };
})();

window.addEventListener('DOMContentLoaded', () => {
    window.TempoApp.init();
});
