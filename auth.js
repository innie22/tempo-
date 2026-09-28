/**
 * Tempo Authentication Controller
 * Integrates real Supabase Auth with role-based permissions (Student, Volunteer, Admin).
 * Enforces server-side database verification for roles and volunteer application status.
 */

window.TempoAuth = (function() {
    let currentUser = null;
    let currentProfile = null;
    let currentVolunteerProfile = null;

    async function init() {
        bindEvents();
        updateUserGreeting(null);
        // Initialize Supabase Client
        if (window.TempoSupabase) {
            await window.TempoSupabase.init();
        }
        checkSession();
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
            renderHeaderUI(null);
            return;
        }

        try {
            const { data: { session }, error } = await supabase.auth.getSession();
            if (session && session.user) {
                currentUser = session.user;
                await loadUserProfile(session.user.id);
            } else {
                currentUser = null;
                currentProfile = null;
                currentVolunteerProfile = null;
                renderHeaderUI(null);
            }

            // Listen for auth state changes
            supabase.auth.onAuthStateChange(async (event, newSession) => {
                if (newSession && newSession.user) {
                    currentUser = newSession.user;
                    await loadUserProfile(newSession.user.id);
                } else {
                    currentUser = null;
                    currentProfile = null;
                    currentVolunteerProfile = null;
                    renderHeaderUI(null);
                }
            });
        } catch (err) {
            console.warn("Session check error:", err);
            renderHeaderUI(null);
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
                let badgeClass = 'bg-emerald-100 text-emerald-800';

                if (profile.role === 'admin') {
                    badgeText = 'Administrator';
                    badgeClass = 'bg-purple-100 text-purple-800';
                } else if (profile.role === 'volunteer') {
                    const status = currentVolunteerProfile?.application_status || 'PENDING';
                    badgeText = status === 'APPROVED' ? 'Peer Volunteer' : `Volunteer (${status})`;
                    badgeClass = status === 'APPROVED' ? 'bg-sky-100 text-sky-800' : 'bg-amber-100 text-amber-800';
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
            window.TempoApp.showToast("Authentication backend is not configured. Please ensure environment variables are set.");
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
                await loadUserProfile(data.user.id);
            } else {
                window.TempoApp.showToast("Please check your email to confirm your account!");
            }
            window.TempoApp.navigateTo('today');

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
    async function handleSignIn(e) {
        e.preventDefault();
        const email = document.getElementById('signin-email').value.trim();
        const password = document.getElementById('signin-password').value;

        if (!email || !password) {
            window.TempoApp.showToast("Please enter both email and password.");
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
        submitBtn.textContent = "Signing In...";

        try {
            const { data, error } = await supabase.auth.signInWithPassword({
                email,
                password
            });

            if (error) {
                window.TempoApp.showToast(`Sign in failed: ${error.message}`);
                return;
            }

            closeAllAuthModals();
            currentUser = data.user;
            await loadUserProfile(data.user.id);
            window.TempoApp.showToast(`Welcome back, ${currentProfile?.full_name || email}!`);

            if (currentProfile?.role === 'volunteer') {
                window.TempoApp.navigateTo('volunteer-dashboard');
            } else if (currentProfile?.role === 'admin') {
                window.TempoApp.navigateTo('admin');
            } else {
                window.TempoApp.navigateTo('today');
            }

        } catch (err) {
            console.error("Sign in error:", err);
            window.TempoApp.showToast("Error signing in. Please check credentials.");
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    // =========================================================================
    // SIGN OUT
    // =========================================================================
    async function handleSignOut() {
        const supabase = window.TempoSupabase ? window.TempoSupabase.getClient() : null;
        if (supabase) {
            await supabase.auth.signOut();
        }
        currentUser = null;
        currentProfile = null;
        currentVolunteerProfile = null;
        renderHeaderUI(null);
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
        getCurrentUser: () => currentUser,
        getCurrentProfile: () => currentProfile,
        getCurrentVolunteerProfile: () => currentVolunteerProfile,
        openRoleSelectModal,
        openSignInModal,
        handleSignOut,
        loadUserProfile,
        extractGreetingName,
        updateUserGreeting
    };
})();
