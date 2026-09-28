/**
 * Tempo Application Core Controller
 * Single-page router, role switcher, toast notifications, confetti celebrations.
 */

window.TempoApp = (function() {
    let currentRole = 'student'; // 'student' | 'admin'
    let currentTab = 'today';

    function init() {
        bindNavigation();
        bindRoleSwitcher();
        initConfettiCanvas();

        // Initialize sub-modules
        if (window.TempoTriage) window.TempoTriage.init();
        if (window.TempoStress) window.TempoStress.init();
        if (window.TempoRoutine) window.TempoRoutine.init();
        if (window.TempoKnowledge) window.TempoKnowledge.init();
        if (window.TempoSupport) window.TempoSupport.init();
        if (window.TempoAdmin) window.TempoAdmin.init();
        if (window.TempoEmergencySupport) window.TempoEmergencySupport.init();
        if (window.TempoAuth) window.TempoAuth.init();
        if (window.TempoVolunteer) window.TempoVolunteer.init();

        // Handle hash navigation
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

    function navigateTo(tabId) {
        currentTab = tabId;
        window.location.hash = `#${tabId}`;

        // Hide all screens
        document.querySelectorAll('.screen-container').forEach(screen => {
            screen.classList.add('hidden');
        });

        // Show active screen
        const targetScreen = document.getElementById(`screen-${tabId}`);
        if (targetScreen) {
            targetScreen.classList.remove('hidden');
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

        // Scroll top gently
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function handleHashChange() {
        const hash = window.location.hash.replace('#', '');
        if (hash) {
            navigateTo(hash);
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

    return {
        init,
        navigateTo,
        setRole,
        showToast,
        triggerConfetti
    };
})();

window.addEventListener('DOMContentLoaded', () => {
    window.TempoApp.init();
});
