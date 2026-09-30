/**
 * Tempo Authentication Controller
 * Integrates real Supabase Auth with role-based permissions (Student, Volunteer, Admin).
 * Enforces server-side database verification for roles and volunteer application status.
 */

window.TempoAuth = (function() {
    let currentUser = null;
    let currentProfile = null;
    let currentVolunteerProfile = null;

    // Asynchronous auth lifecycle tracking
    let authState = 'AUTH_LOADING'; // 'AUTH_LOADING' | 'AUTHENTICATED' | 'ANONYMOUS'
    let authListenerAttached = false;
    let resolveAuthReady = null;
    const authReadyPromise = new Promise(resolve => {
        resolveAuthReady = resolve;
    });

    function isLocalEnvironment() {
        return ['localhost', '127.0.0.1', '0.0.0.0', ''].includes(window.location.hostname);
    }

    async function syncPlanForUser(userId) {
        if (!userId) return;
        if (window.TempoPlanStore && typeof window.TempoPlanStore.init === 'function') {
            await window.TempoPlanStore.init(userId);
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.restorePlanState === 'function') {
            await window.TempoEmergencyFlow.restorePlanState();
        }
        if (window.TempoMode) {
            const hasActive = window.TempoPlanStore && typeof window.TempoPlanStore.hasActivePlan === 'function' && window.TempoPlanStore.hasActivePlan('emergency');
            if (hasActive) {
                window.TempoMode.setMode('emergency', { silent: true });
            }
        }
    }

    function syncPlanForSignOut() {
        if (window.TempoPlanStore && typeof window.TempoPlanStore.clearInMemoryCache === 'function') {
            window.TempoPlanStore.clearInMemoryCache();
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.resetFlowState === 'function') {
            window.TempoEmergencyFlow.resetFlowState();
        }
        if (window.TempoMode) {
            window.TempoMode.setMode('default', { silent: true });
        }
    }

    async function init() {
        bindEvents();
        updateUserGreeting(null);
        // Initialize Supabase Client
        if (window.TempoSupabase) {
            await window.TempoSupabase.init();
        }
        await checkSession();
    }

    function bindEvents() {
        // Top Bar Auth Buttons
        const btnOpenSignIn = document.getElementById('btn-header-signin');
        if (btnOpenSignIn) {
            btnOpenSignIn.addEventListener('click', openSignInModal);
        }

        const btnOpenRegister = document.getElementById('btn-header-register');
        if (btnOpenRegister) {
            btnOpenRegister.addEventListener('click', openRoleSelectModal);
        }

        const btnSignOut = document.getElementById('btn-header-signout');
        if (btnSignOut) {
            btnSignOut.addEventListener('click', handleSignOut);
        }

        // Role Selection Modal Choices
        const chooseStudentBtn = document.getElementById('btn-choose-role-student');
        if (chooseStudentBtn) {
            chooseStudentBtn.addEventListener('click', () => {
                closeRoleSelectModal();
                openStudentRegisterModal();
            });
        }

        const chooseVolunteerBtn = document.getElementById('btn-choose-role-volunteer');
        if (chooseVolunteerBtn) {
            chooseVolunteerBtn.addEventListener('click', () => {
                closeRoleSelectModal();
                openVolunteerApplyModal();
            });
        }

        // Form Submissions
        const formStudentRegister = document.getElementById('form-student-register');
        if (formStudentRegister) {
            formStudentRegister.addEventListener('submit', handleStudentRegister);
        }

        const formVolunteerApply = document.getElementById('form-volunteer-apply');
        if (formVolunteerApply) {
            formVolunteerApply.addEventListener('submit', handleVolunteerApply);
        }

        const formSignIn = document.getElementById('form-signin');
        if (formSignIn) {
            formSignIn.addEventListener('submit', handleSignIn);
        }

        // Modal Close Buttons
        document.querySelectorAll('.btn-close-auth-modal').forEach(btn => {
            btn.addEventListener('click', closeAllAuthModals);
        });
    }

    async function checkSession() {
        const supabase = window.TempoSupabase ? window.TempoSupabase.getClient() : null;
        if (!supabase) {
            // Check local development persisted fallback session (ONLY on localhost)
            if (isLocalEnvironment()) {
                try {
                    const storedLocal = localStorage.getItem('tempo_local_dev_user');
                    if (storedLocal) {
                        const parsed = JSON.parse(storedLocal);
                        if (parsed && parsed.id) {
                            currentUser = parsed;
                            currentProfile = {
                                id: parsed.id,
                                email: parsed.email || '',
                                full_name: (parsed.email || 'user').split('@')[0],
                                role: 'student'
                            };
                            authState = 'AUTHENTICATED';
                            renderHeaderUI(currentProfile);
                            if (resolveAuthReady) resolveAuthReady();
                            return;
                        }
                    }
                } catch (e) {}
            }
            currentUser = null;
            currentProfile = null;
            currentVolunteerProfile = null;
            authState = 'ANONYMOUS';
            renderHeaderUI(null);
            if (resolveAuthReady) resolveAuthReady();
            return;
        }

        try {
            const { data: { session }, error } = await supabase.auth.getSession();
            if (session && session.user) {
                currentUser = session.user;
                authState = 'AUTHENTICATED';
                await loadUserProfile(session.user.id);
            } else {
                currentUser = null;
                currentProfile = null;
                currentVolunteerProfile = null;
                authState = 'ANONYMOUS';
                renderHeaderUI(null);
            }
        } catch (err) {
            console.warn("[TempoAuth] Session check error:", err);
            currentUser = null;
            currentProfile = null;
            currentVolunteerProfile = null;
            authState = 'ANONYMOUS';
            renderHeaderUI(null);
        } finally {
            if (resolveAuthReady) resolveAuthReady();
        }

        // Listen for subsequent auth state changes (attached once)
        if (!authListenerAttached) {
            authListenerAttached = true;
            supabase.auth.onAuthStateChange(async (event, newSession) => {
                if (event === 'SIGNED_OUT' || (!newSession && event !== 'INITIAL_SESSION')) {
                    currentUser = null;
                    currentProfile = null;
                    currentVolunteerProfile = null;
                    authState = 'ANONYMOUS';
                    renderHeaderUI(null);
                    syncPlanForSignOut();
                } else if (newSession && newSession.user) {
                    const isNewUser = !currentUser || currentUser.id !== newSession.user.id;
                    currentUser = newSession.user;
                    authState = 'AUTHENTICATED';
                    await loadUserProfile(newSession.user.id);
                    if (isNewUser && (event === 'SIGNED_IN' || event === 'USER_UPDATED')) {
                        await syncPlanForUser(newSession.user.id);
                    }
                }
            });
        }
    }

    async function loadUserProfile(userId) {
        const supabase = window.TempoSupabase ? window.TempoSupabase.getClient() : null;
        if (!supabase) return;

        try {
            // Load base profile
            const { data: profile, error } = await supabase
                .from('profiles')
                .select('*')
                .eq('id', userId)
                .single();

            if (error || !profile) {
                console.warn("Profile not yet created or loading:", error);
                // Fallback using user metadata if trigger has latency
                currentProfile = {
                    id: userId,
                    email: currentUser.email,
                    full_name: currentUser.user_metadata?.full_name || '',
                    role: currentUser.user_metadata?.role || 'student'
                };
            } else {
                currentProfile = profile;
            }

            // If role is volunteer, load volunteer profile
            if (currentProfile.role === 'volunteer') {
                const { data: vProfile } = await supabase
                    .from('volunteer_profiles')
                    .select('*')
                    .eq('user_id', userId)
                    .single();
                currentVolunteerProfile = vProfile || {
                    application_status: 'PENDING'
                };
            } else {
                currentVolunteerProfile = null;
            }

            renderHeaderUI(currentProfile);

            // Update app permissions and active tab
            applyRolePermissions(currentProfile.role);

        } catch (e) {
            console.error("Error loading profile:", e);
        }
    }

    /**
     * Extracts the appropriate greeting name from a full name.
     * Supports Vietnamese naming order (given name last) and Western naming order (given name first).
     * e.g. "Đặng Nguyễn Yến Nhi" -> "Nhi"
     * e.g. "John Smith" -> "John"
     */
    function extractGreetingName(fullName) {
        if (!fullName || typeof fullName !== 'string') return null;
        const trimmed = fullName.trim();
        if (!trimmed) return null;
        const parts = trimmed.split(/\s+/).filter(Boolean);
        if (parts.length === 0) return null;
        if (parts.length === 1) return parts[0];

        // Check for Vietnamese diacritics or common Vietnamese family names
        const hasVietnameseDiacritics = /[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđĐ]/i.test(trimmed);
        const commonVnSurnames = /^(nguyen|tran|le|pham|hoang|huynh|phan|vu|vo|dang|bui|do|ho|ngo|duong|ly|dinh|dao|doan|luong|mai|truong|ha|trinh)/i;
        const startsWithVnSurname = commonVnSurnames.test(parts[0]);

        if (hasVietnameseDiacritics || startsWithVnSurname) {
            // In Vietnamese naming order, informal address uses the given name (last token)
            return parts[parts.length - 1];
        }

        // Standard Western convention: given name is first token
        return parts[0];
    }

    /**
     * Updates the home screen heading with a personalized greeting if authenticated,
     * or a neutral greeting if unauthenticated / profile name unavailable.
     */
    function updateUserGreeting(profile) {
        const greetingEl = document.getElementById('home-greeting-heading');
        if (!greetingEl) return;

        if (!profile) {
            greetingEl.textContent = 'Hi there 👋';
            return;
        }

        const greetingName = extractGreetingName(profile.full_name);
        if (greetingName) {
            greetingEl.textContent = `Hi, ${greetingName} 👋`;
        } else {
            greetingEl.textContent = 'Hi there 👋';
        }
    }

    function renderHeaderUI(profile) {
        updateUserGreeting(profile);

        const unauthBox = document.getElementById('header-unauthenticated-box');
        const authBox = document.getElementById('header-authenticated-box');
        const nameLabel = document.getElementById('header-user-name');
        const rolePill = document.getElementById('header-user-role-pill');

        if (!profile) {
            if (unauthBox) unauthBox.classList.remove('hidden');
            if (authBox) authBox.classList.add('hidden');
            applyRolePermissions('guest');
        } else {
            if (unauthBox) unauthBox.classList.add('hidden');
            if (authBox) authBox.classList.remove('hidden');

            if (nameLabel) nameLabel.textContent = profile.full_name || profile.email;
            if (rolePill) {
                let badgeText = 'Student';
                let badgeClass = 'bg-[#FFE9DC] text-[#B83D08]';

                if (profile.role === 'admin') {
                    badgeText = 'Administrator';
                    badgeClass = 'bg-[#F3F1EF] text-[#202124] border border-[#E8E4E1]';
                } else if (profile.role === 'volunteer') {
                    const status = currentVolunteerProfile?.application_status || 'PENDING';
                    badgeText = status === 'APPROVED' ? 'Peer Volunteer' : `Volunteer (${status})`;
                    badgeClass = status === 'APPROVED' ? 'bg-[#FFE9DC] text-[#B83D08]' : 'bg-amber-100 text-amber-800';
                }

                rolePill.textContent = badgeText;
                rolePill.className = `px-2 py-0.5 rounded-full text-[10px] font-bold ${badgeClass}`;
            }
        }
    }

    function applyRolePermissions(role) {
        const adminNav = document.getElementById('nav-tab-admin');
        const volunteerNav = document.getElementById('nav-tab-volunteer');

        if (role === 'admin') {
            if (adminNav) adminNav.classList.remove('hidden');
            if (volunteerNav) volunteerNav.classList.add('hidden');
        } else if (role === 'volunteer') {
            if (adminNav) adminNav.classList.add('hidden');
            if (volunteerNav) volunteerNav.classList.remove('hidden');
            // If user is volunteer, re-render volunteer dashboard
            if (window.TempoVolunteer) window.TempoVolunteer.render();
        } else {
            // Student or Guest
            if (adminNav) adminNav.classList.add('hidden');
            if (volunteerNav) volunteerNav.classList.add('hidden');
        }
    }

    // =========================================================================
    // STUDENT REGISTRATION (US02)
    // =========================================================================
    async function handleStudentRegister(e) {
        e.preventDefault();
        const fullName = document.getElementById('reg-student-name').value.trim();
        const email = document.getElementById('reg-student-email').value.trim();
        const password = document.getElementById('reg-student-password').value;
        const confirmPassword = document.getElementById('reg-student-confirm').value;
        const university = document.getElementById('reg-student-university').value.trim();
        const yearOfStudy = document.getElementById('reg-student-year').value;
        const terms = document.getElementById('reg-student-terms').checked;

        if (!fullName || !email || !password) {
            window.TempoApp.showToast("Please fill in all required fields.");
            return;
        }

        if (password !== confirmPassword) {
            window.TempoApp.showToast("Passwords do not match. Please verify.");
            return;
        }

        if (!terms) {
            window.TempoApp.showToast("Please agree to the Terms of Service and Privacy Policy.");
            return;
        }

        const supabase = window.TempoSupabase ? window.TempoSupabase.getClient() : null;
        if (!supabase) {
            if (!isLocalEnvironment()) {
                window.TempoApp.showToast("Authentication backend is not configured. Please ensure environment variables are set.", 5000);
                return;
            }
            currentUser = { id: 'local_student_' + btoa(email).replace(/[^a-zA-Z0-9]/g, '').slice(0, 16), email: email };
            try { localStorage.setItem('tempo_local_dev_user', JSON.stringify(currentUser)); } catch (e) {}
            currentProfile = {
                id: currentUser.id,
                email: email,
                full_name: fullName,
                role: 'student',
                university: university || 'Not specified',
                year_of_study: yearOfStudy || 'Not specified'
            };
            authState = 'AUTHENTICATED';
            renderHeaderUI(currentProfile);
            closeAllAuthModals();
            window.TempoApp.triggerConfetti();
            window.TempoApp.showToast(`Welcome, ${fullName}! Your account has been created.`);

            await syncPlanForUser(currentUser.id);

            if (window.TempoMode && window.TempoMode.hasPendingMode()) {
                window.TempoMode.handleAuthSuccess();
            } else {
                window.TempoApp.navigateTo('today');
            }
            return;
        }

        const submitBtn = e.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = "Creating Student Account...";

        try {
            const { data, error } = await supabase.auth.signUp({
                email,
                password,
                options: {
                    data: {
                        full_name: fullName,
                        role: 'student',
                        university: university || 'Not specified',
                        year_of_study: yearOfStudy || 'Not specified'
                    }
                }
            });

            if (error) {
                window.TempoApp.showToast(`Registration failed: ${error.message}`);
                return;
            }

            closeAllAuthModals();
            window.TempoApp.triggerConfetti();
            window.TempoApp.showToast(`Welcome, ${fullName}! Your student account has been created.`);

            if (data.session) {
                currentUser = data.user;
                authState = 'AUTHENTICATED';
                await loadUserProfile(data.user.id);
                await syncPlanForUser(data.user.id);
            } else {
                window.TempoApp.showToast("Please check your email to confirm your account!");
            }

            if (window.TempoMode && window.TempoMode.hasPendingMode()) {
                window.TempoMode.handleAuthSuccess();
            } else {
                window.TempoApp.navigateTo('today');
            }

        } catch (err) {
            console.error("Student register error:", err);
            window.TempoApp.showToast("An unexpected error occurred. Please try again.");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    // =========================================================================
    // VOLUNTEER APPLICATION (US03)
    // =========================================================================
    async function handleVolunteerApply(e) {
        e.preventDefault();
        const fullName = document.getElementById('vol-name').value.trim();
        const email = document.getElementById('vol-email').value.trim();
        const password = document.getElementById('vol-password').value;
        const confirmPassword = document.getElementById('vol-confirm').value;
        const universityOrOrg = document.getElementById('vol-organization').value.trim();
        const background = document.getElementById('vol-background').value;
        const studyYear = document.getElementById('vol-studyyear').value.trim();
        const experience = document.getElementById('vol-experience').value.trim();
        const motivation = document.getElementById('vol-motivation').value.trim();
        const availability = document.getElementById('vol-availability').value;
        const ethical = document.getElementById('vol-ethical-acknowledgement').checked;

        if (!fullName || !email || !password || !universityOrOrg || !studyYear || !experience || !motivation) {
            window.TempoApp.showToast("Please fill in all required fields for your application.");
            return;
        }

        if (password !== confirmPassword) {
            window.TempoApp.showToast("Passwords do not match.");
            return;
        }

        if (!ethical) {
            window.TempoApp.showToast("You must acknowledge the peer support ethical agreement.");
            return;
        }

        const supabase = window.TempoSupabase ? window.TempoSupabase.getClient() : null;
        if (!supabase) {
            window.TempoApp.showToast("Authentication backend is not configured. Please ensure environment variables are set.");
            return;
        }

        const submitBtn = e.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = "Submitting Application...";

        try {
            const { data, error } = await supabase.auth.signUp({
                email,
                password,
                options: {
                    data: {
                        full_name: fullName,
                        role: 'volunteer',
                        university_or_organization: universityOrOrg,
                        background,
                        study_year_or_qualification: studyYear,
                        experience,
                        motivation,
                        availability,
                        ethical_acknowledged: true
                    }
                }
            });

            if (error) {
                window.TempoApp.showToast(`Application error: ${error.message}`);
                return;
            }

            closeAllAuthModals();
            // Open Application Submitted Notice Screen
            openVolunteerSubmittedModal(fullName);

            if (data.session) {
                currentUser = data.user;
                await loadUserProfile(data.user.id);
            }

        } catch (err) {
            console.error("Volunteer apply error:", err);
            window.TempoApp.showToast("Failed to submit application. Please try again.");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    // =========================================================================
    // SIGN IN
    // =========================================================================
    async function signInWithCredentials(email, password) {
        if (!email || !password) {
            window.TempoApp.showToast("Please enter both email and password.");
            return false;
        }

        const supabase = window.TempoSupabase ? window.TempoSupabase.getClient() : null;
        if (!supabase) {
            if (!isLocalEnvironment()) {
                window.TempoApp.showToast("Authentication backend is not configured. Please ensure SUPABASE_URL and publishable key are set in environment variables.", 5000);
                return false;
            }
            currentUser = { id: 'local_student_' + btoa(email).replace(/[^a-zA-Z0-9]/g, '').slice(0, 16), email: email };
            try { localStorage.setItem('tempo_local_dev_user', JSON.stringify(currentUser)); } catch (e) {}
            currentProfile = {
                id: currentUser.id,
                email: email,
                full_name: email.split('@')[0],
                role: 'student'
            };
            authState = 'AUTHENTICATED';
            renderHeaderUI(currentProfile);
            closeAllAuthModals();
            window.TempoApp.showToast(`Welcome back, ${currentProfile.full_name}! (Local Dev Mode)`);

            await syncPlanForUser(currentUser.id);

            if (window.TempoMode && window.TempoMode.hasPendingMode()) {
                window.TempoMode.handleAuthSuccess();
            } else {
                window.TempoApp.navigateTo('today');
            }
            return true;
        }

        try {
            const { data, error } = await supabase.auth.signInWithPassword({
                email,
                password
            });

            if (error) {
                window.TempoApp.showToast(`Sign in failed: ${error.message}`);
                return false;
            }

            closeAllAuthModals();
            currentUser = data.user;
            authState = 'AUTHENTICATED';
            await loadUserProfile(data.user.id);
            await syncPlanForUser(data.user.id);
            window.TempoApp.showToast(`Welcome back, ${currentProfile?.full_name || email}!`);

            if (window.TempoMode && window.TempoMode.hasPendingMode()) {
                window.TempoMode.handleAuthSuccess();
            } else if (currentProfile?.role === 'volunteer') {
                window.TempoApp.navigateTo('volunteer-dashboard');
            } else if (currentProfile?.role === 'admin') {
                window.TempoApp.navigateTo('admin');
            } else {
                window.TempoApp.navigateTo('today');
            }
            return true;

        } catch (err) {
            console.error("Sign in error:", err);
            window.TempoApp.showToast("Error signing in. Please check credentials.");
            return false;
        }
    }

    async function handleSignIn(e) {
        e.preventDefault();
        const email = document.getElementById('signin-email').value.trim();
        const password = document.getElementById('signin-password').value;

        const submitBtn = e.target.querySelector('button[type="submit"]');
        const originalText = submitBtn ? submitBtn.textContent : '';
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = "Signing In...";
        }

        try {
            await signInWithCredentials(email, password);
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        }
    }

    // =========================================================================
    // SIGN OUT
    // =========================================================================
    async function handleSignOut() {
        const supabase = window.TempoSupabase ? window.TempoSupabase.getClient() : null;
        if (supabase) {
            try {
                await supabase.auth.signOut();
            } catch (e) {
                console.warn("[TempoAuth] Supabase signOut error:", e);
            }
        }
        try {
            localStorage.removeItem('tempo_local_dev_user');
        } catch (e) {}

        currentUser = null;
        currentProfile = null;
        currentVolunteerProfile = null;
        authState = 'ANONYMOUS';
        renderHeaderUI(null);

        syncPlanForSignOut();

        window.TempoApp.showToast("You have been signed out.");
        window.TempoApp.navigateTo('today');
    }

    // =========================================================================
    // MODAL CONTROLLERS
    // =========================================================================
    function openRoleSelectModal() {
        closeAllAuthModals();
        const modal = document.getElementById('modal-role-select');
        if (modal) modal.classList.remove('hidden');
    }

    function closeRoleSelectModal() {
        const modal = document.getElementById('modal-role-select');
        if (modal) modal.classList.add('hidden');
    }

    function openStudentRegisterModal() {
        closeAllAuthModals();
        const modal = document.getElementById('modal-student-register');
        if (modal) modal.classList.remove('hidden');
    }

    function openVolunteerApplyModal() {
        closeAllAuthModals();
        const modal = document.getElementById('modal-volunteer-apply');
        if (modal) modal.classList.remove('hidden');
    }

    function openSignInModal() {
        closeAllAuthModals();
        const modal = document.getElementById('modal-signin');
        if (modal) modal.classList.remove('hidden');
    }

    function openVolunteerSubmittedModal(name) {
        closeAllAuthModals();
        const modal = document.getElementById('modal-volunteer-submitted');
        if (modal) {
            document.getElementById('vol-submitted-name').textContent = name;
            modal.classList.remove('hidden');
        }
    }

    function closeAllAuthModals() {
        document.querySelectorAll('.auth-modal-overlay').forEach(modal => {
            modal.classList.add('hidden');
        });
    }

    return {
        init,
        checkSession,
        waitForAuthResolution: () => authReadyPromise,
        getAuthState: () => authState,
        getCurrentUser: () => currentUser,
        getCurrentUserId: () => currentUser ? currentUser.id : null,
        getCurrentProfile: () => currentProfile,
        getCurrentVolunteerProfile: () => currentVolunteerProfile,
        openRoleSelectModal,
        openSignInModal,
        signIn: signInWithCredentials,
        handleSignOut,
        loadUserProfile,
        extractGreetingName,
        updateUserGreeting,
        syncPlanForUser,
        syncPlanForSignOut
    };
})();
