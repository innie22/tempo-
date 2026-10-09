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
    let isRegistrationInProgress = false;
    let isExplicitSignInInProgress = false;
    const authReadyPromise = new Promise(resolve => {
        resolveAuthReady = resolve;
    });

    // Pre-auth localization state & dictionary (Vietnamese-first)
    let currentAuthLang = (window.TempoI18n && window.TempoI18n.getLanguage) ? window.TempoI18n.getLanguage() : 'vi';

    const AUTH_I18N = {
        en: {
            regHeading: "CREATE YOUR TEMPO ACCOUNT",
            regTitle: "Welcome to Tempo",
            regSubtitle: "Manage academic stress, organize deadlines, and find your rhythm.",
            regNameLabel: 'Display name <span class="text-rose-500">*</span>',
            regNamePlaceholder: "e.g. Alex or Nguyễn Yến Nhi",
            regEmailLabel: 'Email <span class="text-rose-500">*</span>',
            regEmailPlaceholder: "you@example.com",
            regPasswordLabel: 'Password <span class="text-rose-500">*</span>',
            regPasswordPlaceholder: "Min. 6 characters",
            regSubmitBtn: "Create account",
            regFooterText: 'Already have an account? <button type="button" onclick="window.TempoAuth.openSignInModal()" class="text-[#FF6B2C] font-bold hover:underline ml-1 cursor-pointer">Log in</button>',
            
            loginHeading: "WELCOME BACK",
            loginTitle: "Welcome Back",
            loginSubtitle: "Sign in to your Tempo account.",
            loginEmailLabel: "Email",
            loginPasswordLabel: "Password",
            loginForgotLink: "Forgot password?",
            loginSubmitBtn: "Log in",
            loginFooterText: 'Don\'t have an account? <button type="button" onclick="window.TempoAuth.openRegisterModal()" class="text-[#FF6B2C] font-bold hover:underline ml-1 cursor-pointer">Create account</button>',
            
            forgotPrompt: "Enter your registered email address to receive password reset instructions:",
            forgotSent: "Password reset link has been sent to your email.",
            fillRequired: "Please fill in all required fields.",
            passTooShort: "Password must be at least 6 characters long.",
            emailAlreadyRegistered: "This email is already registered. Please log in instead.",
            errorNotice: "Notice",
            loginWithEmailBtn: "Log in with this email →",
            genericRegError: "Registration failed. Please verify your information and try again.",
            invalidCredentials: "Email or password is incorrect."
        },
        vi: {
            regHeading: "TẠO TÀI KHOẢN TEMPO",
            regTitle: "Chào mừng đến với Tempo",
            regSubtitle: "Quản lý căng thẳng học tập, sắp xếp hạn chót và tìm lại nhịp điệu của bạn.",
            regNameLabel: 'Tên hiển thị <span class="text-rose-500">*</span>',
            regNamePlaceholder: "VD: Alex hoặc Nguyễn Yến Nhi",
            regEmailLabel: 'Email <span class="text-rose-500">*</span>',
            regEmailPlaceholder: "ban@example.com",
            regPasswordLabel: 'Mật khẩu <span class="text-rose-500">*</span>',
            regPasswordPlaceholder: "Tối thiểu 6 ký tự",
            regSubmitBtn: "Tạo tài khoản",
            regFooterText: 'Đã có tài khoản? <button type="button" onclick="window.TempoAuth.openSignInModal()" class="text-[#FF6B2C] font-bold hover:underline ml-1 cursor-pointer">Đăng nhập</button>',
            
            loginHeading: "CHÀO MỪNG TRỞ LẠI",
            loginTitle: "Chào mừng trở lại",
            loginSubtitle: "Đăng nhập vào tài khoản Tempo của bạn.",
            loginEmailLabel: "Email",
            loginPasswordLabel: "Mật khẩu",
            loginForgotLink: "Quên mật khẩu?",
            loginSubmitBtn: "Đăng nhập",
            loginFooterText: 'Chưa có tài khoản? <button type="button" onclick="window.TempoAuth.openRegisterModal()" class="text-[#FF6B2C] font-bold hover:underline ml-1 cursor-pointer">Tạo tài khoản</button>',
            
            forgotPrompt: "Nhập địa chỉ email đã đăng ký để nhận hướng dẫn đặt lại mật khẩu:",
            forgotSent: "Liên kết đặt lại mật khẩu đã được gửi đến email của bạn.",
            fillRequired: "Vui lòng điền đầy đủ các thông tin bắt buộc.",
            passTooShort: "Mật khẩu phải có ít nhất 6 ký tự.",
            emailAlreadyRegistered: "Email này đã được đăng ký. Vui lòng đăng nhập.",
            errorNotice: "Thông báo",
            loginWithEmailBtn: "Đăng nhập với email này →",
            genericRegError: "Đăng ký thất bại. Vui lòng kiểm tra lại thông tin và thử lại.",
            invalidCredentials: "Email hoặc mật khẩu không chính xác."
        }
    };

    function setAuthLanguage(lang, syncGlobal = true) {
        if (!['en', 'vi'].includes(lang)) return;
        currentAuthLang = lang;
        try {
            localStorage.setItem('tempo_auth_lang', lang);
            localStorage.setItem('tempo_language', lang);
        } catch (e) {}

        if (syncGlobal && window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
            if (window.TempoI18n.getLanguage() !== lang) {
                window.TempoI18n.setLanguage(lang);
            }
        }

        const dict = AUTH_I18N[lang];
        if (!dict) return;

        // Update registration modal elements
        const regHeading = document.getElementById('auth-reg-heading');
        if (regHeading) regHeading.textContent = dict.regHeading;
        const regTitle = document.getElementById('auth-reg-title');
        if (regTitle) regTitle.textContent = dict.regTitle;
        const regSubtitle = document.getElementById('auth-reg-subtitle');
        if (regSubtitle) regSubtitle.textContent = dict.regSubtitle;
        const regNameLabel = document.getElementById('auth-reg-name-label');
        if (regNameLabel) regNameLabel.innerHTML = dict.regNameLabel;
        const regNameInput = document.getElementById('reg-display-name');
        if (regNameInput) regNameInput.placeholder = dict.regNamePlaceholder;
        const regEmailLabel = document.getElementById('auth-reg-email-label');
        if (regEmailLabel) regEmailLabel.innerHTML = dict.regEmailLabel;
        const regEmailInput = document.getElementById('reg-email');
        if (regEmailInput) regEmailInput.placeholder = dict.regEmailPlaceholder;
        const regPassLabel = document.getElementById('auth-reg-password-label');
        if (regPassLabel) regPassLabel.innerHTML = dict.regPasswordLabel;
        const regPassInput = document.getElementById('reg-password');
        if (regPassInput) regPassInput.placeholder = dict.regPasswordPlaceholder;
        const btnSubmitReg = document.getElementById('btn-submit-register');
        if (btnSubmitReg) btnSubmitReg.textContent = dict.regSubmitBtn;
        const regFooter = document.getElementById('auth-reg-footer-text');
        if (regFooter) regFooter.innerHTML = dict.regFooterText;

        // Update sign-in modal elements
        const loginHeading = document.getElementById('auth-login-heading');
        if (loginHeading) loginHeading.textContent = dict.loginHeading;
        const loginTitle = document.getElementById('auth-login-title');
        if (loginTitle) loginTitle.textContent = dict.loginTitle;
        const loginSubtitle = document.getElementById('auth-login-subtitle');
        if (loginSubtitle) loginSubtitle.textContent = dict.loginSubtitle;
        const loginEmailLabel = document.getElementById('auth-login-email-label');
        if (loginEmailLabel) loginEmailLabel.textContent = dict.loginEmailLabel;
        const loginPassLabel = document.getElementById('auth-login-password-label');
        if (loginPassLabel) loginPassLabel.textContent = dict.loginPasswordLabel;
        const loginForgotLink = document.getElementById('auth-login-forgot-link');
        if (loginForgotLink) loginForgotLink.textContent = dict.loginForgotLink;
        const btnSubmitSignin = document.getElementById('btn-submit-signin');
        if (btnSubmitSignin) btnSubmitSignin.textContent = dict.loginSubmitBtn;
        const loginFooter = document.getElementById('auth-login-footer-text');
        if (loginFooter) loginFooter.innerHTML = dict.loginFooterText;

        // Update registration error box elements if present
        const regErrTitle = document.getElementById('auth-reg-error-title');
        if (regErrTitle) regErrTitle.textContent = dict.errorNotice || "Notice";
        const regErrBtn = document.getElementById('auth-reg-error-btn-text');
        if (regErrBtn) regErrBtn.textContent = dict.loginWithEmailBtn || "Log in with this email →";
        const regErrDesc = document.getElementById('auth-reg-error-desc');
        const regErrBox = document.getElementById('auth-reg-error-box');
        if (regErrDesc && regErrBox && !regErrBox.classList.contains('hidden')) {
            if (regErrDesc.textContent === AUTH_I18N.en.emailAlreadyRegistered || regErrDesc.textContent === AUTH_I18N.vi.emailAlreadyRegistered) {
                regErrDesc.textContent = dict.emailAlreadyRegistered;
            }
        }

        // Update sign-in error box elements if present
        const loginErrTitle = document.getElementById('auth-login-error-title');
        if (loginErrTitle) loginErrTitle.textContent = dict.errorNotice || "Notice";
        const loginErrDesc = document.getElementById('auth-login-error-desc');
        const loginErrBox = document.getElementById('auth-login-error-box');
        if (loginErrDesc && loginErrBox && !loginErrBox.classList.contains('hidden')) {
            if (loginErrDesc.textContent === AUTH_I18N.en.invalidCredentials || loginErrDesc.textContent === AUTH_I18N.vi.invalidCredentials) {
                loginErrDesc.textContent = dict.invalidCredentials;
            }
        }

        // Update active switch button styles
        document.querySelectorAll('.auth-lang-btn').forEach(btn => {
            const btnLang = btn.getAttribute('data-lang');
            if (btnLang === lang) {
                btn.className = 'auth-lang-btn font-bold text-[#FF6B2C] cursor-pointer';
            } else {
                btn.className = 'auth-lang-btn text-stone-400 hover:text-stone-700 cursor-pointer';
            }
        });

        // Update navbar auth buttons
        const btnHeaderSignin = document.getElementById('btn-header-signin');
        if (btnHeaderSignin) btnHeaderSignin.textContent = lang === 'vi' ? 'Đăng nhập' : 'Sign In';
        const btnHeaderRegister = document.getElementById('btn-header-register');
        if (btnHeaderRegister) btnHeaderRegister.textContent = lang === 'vi' ? 'Đăng ký' : 'Register';
        const btnHeaderSignout = document.getElementById('btn-header-signout');
        if (btnHeaderSignout) btnHeaderSignout.textContent = lang === 'vi' ? 'Đăng xuất' : 'Sign Out';
    }

    /**
     * Computes circular initials fallback from a display name or email.
     * Rules:
     * - Single word: first letter uppercase (e.g. "Alex" -> "A")
     * - Multiple words: first letters of the first two words uppercase (e.g. "Nguyễn Yến Nhi" -> "NY", "Alex Morgan" -> "AM")
     */
    function getInitials(name) {
        if (!name || typeof name !== 'string') return 'U';
        const trimmed = name.trim();
        if (!trimmed) return 'U';
        const cleanName = trimmed.includes('@') ? trimmed.split('@')[0] : trimmed;
        const parts = cleanName.split(/\s+/).filter(Boolean);
        if (parts.length === 0) return 'U';
        if (parts.length === 1) {
            return parts[0].charAt(0).toUpperCase();
        }
        return (parts[0].charAt(0) + parts[1].charAt(0)).toUpperCase();
    }

    function escapeHTML(str) {
        if (!str || typeof str !== 'string') return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function isLocalEnvironment() {
        return ['localhost', '127.0.0.1', '0.0.0.0', ''].includes(window.location.hostname);
    }

    async function syncPlanForUser(userId) {
        if (!userId) return false;
        if (window.TempoPlanStore && typeof window.TempoPlanStore.init === 'function') {
            await window.TempoPlanStore.init(userId);
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.restorePlanState === 'function') {
            await window.TempoEmergencyFlow.restorePlanState();
        }
        if (window.TempoMode && typeof window.TempoMode.handleAuthSuccess === 'function') {
            return window.TempoMode.handleAuthSuccess();
        }
        return false;
    }

    function syncPlanForSignOut() {
        if (window.TempoPlanStore && typeof window.TempoPlanStore.clearInMemoryCache === 'function') {
            window.TempoPlanStore.clearInMemoryCache();
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.resetFlowState === 'function') {
            window.TempoEmergencyFlow.resetFlowState();
        }
        if (window.TempoMode) {
            if (typeof window.TempoMode.handleSignOut === 'function') {
                window.TempoMode.handleSignOut();
            } else if (typeof window.TempoMode.transitionContext === 'function') {
                window.TempoMode.transitionContext(null, { silent: true });
            } else {
                window.TempoMode.setMode('default', { silent: true });
            }
        }
    }

    async function init() {
        bindEvents();
        try {
            const initialLang = (window.TempoI18n && typeof window.TempoI18n.getLanguage === 'function')
                ? window.TempoI18n.getLanguage()
                : (localStorage.getItem('tempo_language') || localStorage.getItem('tempo_auth_lang') || 'vi');
            setAuthLanguage(initialLang, false);

            if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
                window.TempoI18n.onLanguageChange((lang) => {
                    setAuthLanguage(lang, false);
                });
            }
        } catch (e) {}
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

        // Direct Registration Modal trigger (Single Standard Tempo Account)
        const btnOpenRegister = document.getElementById('btn-header-register');
        if (btnOpenRegister) {
            btnOpenRegister.addEventListener('click', openRegisterModal);
        }

        const btnSignOut = document.getElementById('btn-header-signout');
        if (btnSignOut) {
            btnSignOut.addEventListener('click', handleSignOut);
        }

        // Role Selection Modal Choices (Preserved dormant)
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
        const formRegister = document.getElementById('form-register');
        if (formRegister) {
            formRegister.addEventListener('submit', handleRegister);
        }

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

        // Clear registration error on input
        ['reg-display-name', 'reg-email', 'reg-password'].forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('input', () => {
                    clearRegisterError();
                });
            }
        });

        // Clear sign-in error on input
        ['signin-email', 'signin-password'].forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('input', () => {
                    clearSignInError();
                });
            }
        });

        // Modal Close Buttons
        document.querySelectorAll('.btn-close-auth-modal').forEach(btn => {
            btn.addEventListener('click', cancelAuthModal);
        });

        document.querySelectorAll('.auth-modal-overlay').forEach(overlay => {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    cancelAuthModal();
                }
            });
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const openOverlay = document.querySelector('.auth-modal-overlay:not(.hidden)');
                if (openOverlay) {
                    cancelAuthModal();
                }
            }
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
                        if (parsed && parsed.id && parsed.email) {
                            const normEmail = parsed.email.trim().toLowerCase();
                            const registeredMock = localStorage.getItem('tempo_mock_account_' + normEmail) ||
                                                   localStorage.getItem('tempo_mock_account_' + parsed.email);
                            if (registeredMock) {
                                currentUser = parsed;
                                const name = parsed.user_metadata?.display_name || parsed.user_metadata?.full_name || normEmail.split('@')[0];
                                currentProfile = {
                                    id: parsed.id,
                                    email: normEmail,
                                    full_name: name,
                                    display_name: name,
                                    role: parsed.user_metadata?.role || 'student'
                                };
                                authState = 'authenticated';
                                renderHeaderUI(currentProfile);
                                if (resolveAuthReady) resolveAuthReady();
                                return;
                            } else {
                                localStorage.removeItem('tempo_local_dev_user');
                            }
                        }
                    }
                } catch (e) {}
            }
            currentUser = null;
            currentProfile = null;
            currentVolunteerProfile = null;
            authState = 'anonymous';
            renderHeaderUI(null);
            if (resolveAuthReady) resolveAuthReady();
            return;
        }

        try {
            const { data: { session }, error } = await supabase.auth.getSession();
            if (session && session.user) {
                currentUser = session.user;
                authState = 'authenticated';
                await loadUserProfile(session.user.id);
            } else {
                currentUser = null;
                currentProfile = null;
                currentVolunteerProfile = null;
                authState = 'anonymous';
                renderHeaderUI(null);
            }
        } catch (err) {
            console.warn("[TempoAuth] Session check error:", err);
            const isNetworkError = !navigator.onLine || 
                (err && (err.name === 'FetchError' || 
                         err.name === 'TypeError' ||
                         (typeof err.message === 'string' && (
                             err.message.toLowerCase().includes('failed to fetch') ||
                             err.message.toLowerCase().includes('network') ||
                             err.message.toLowerCase().includes('timeout') ||
                             err.message.toLowerCase().includes('offline')
                         ))));
            if (isNetworkError && currentUser) {
                console.info("[TempoAuth] Network error detected; retaining active session per contract.");
            } else {
                currentUser = null;
                currentProfile = null;
                currentVolunteerProfile = null;
                authState = 'anonymous';
                renderHeaderUI(null);
            }
        } finally {
            if (resolveAuthReady) resolveAuthReady();
        }

        // Listen for subsequent auth state changes (attached once)
        if (!authListenerAttached) {
            authListenerAttached = true;
            supabase.auth.onAuthStateChange(async (event, newSession) => {
                if (isRegistrationInProgress) {
                    // Registration cleanup or auto-session from signUp:
                    // MUST NOT treat as authentication success!
                    // MUST NOT clear pendingIntent via handleSignOut!
                    // MUST NOT fulfill pending intents or open protected views!
                    console.info("[TempoAuth] onAuthStateChange event ignored during registration:", event);
                    return;
                }
                if (event === 'SIGNED_OUT' || (!newSession && event !== 'INITIAL_SESSION')) {
                    currentUser = null;
                    currentProfile = null;
                    currentVolunteerProfile = null;
                    authState = 'anonymous';
                    renderHeaderUI(null);
                    syncPlanForSignOut();
                } else if (newSession && newSession.user) {
                    const isNewUser = !currentUser || currentUser.id !== newSession.user.id;
                    currentUser = newSession.user;
                    authState = 'authenticated';
                    await loadUserProfile(newSession.user.id);
                    // Only resume intent via onAuthStateChange if this is NOT an explicit signInWithCredentials call (which handles it directly)
                    if (isNewUser && !isExplicitSignInInProgress && (event === 'SIGNED_IN' || event === 'USER_UPDATED')) {
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
                const metaName = currentUser?.user_metadata?.display_name || currentUser?.user_metadata?.full_name || '';
                currentProfile = {
                    id: userId,
                    email: currentUser?.email || '',
                    full_name: metaName,
                    display_name: metaName,
                    role: currentUser?.user_metadata?.role || 'student'
                };
            } else {
                currentProfile = {
                    ...profile,
                    display_name: profile.display_name || profile.full_name || currentUser?.user_metadata?.display_name || ''
                };
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

        const greetingName = extractGreetingName(profile.display_name || profile.full_name);
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
        const avatarEl = document.getElementById('header-user-avatar');

        if (!profile) {
            if (unauthBox) unauthBox.classList.remove('hidden');
            if (authBox) authBox.classList.add('hidden');
            applyRolePermissions('guest');
        } else {
            if (unauthBox) unauthBox.classList.add('hidden');
            if (authBox) authBox.classList.remove('hidden');

            const displayName = profile.display_name || profile.full_name || profile.email || 'User';
            if (nameLabel) nameLabel.textContent = displayName;

            if (avatarEl) {
                avatarEl.setAttribute('title', displayName);
                if (profile.avatar_url) {
                    avatarEl.innerHTML = `<img src="${escapeHTML(profile.avatar_url)}" alt="${escapeHTML(displayName)}" class="w-full h-full rounded-full object-cover">`;
                } else {
                    avatarEl.textContent = getInitials(displayName);
                }
            }

            if (rolePill) {
                if (profile.role === 'admin') {
                    rolePill.textContent = 'Administrator';
                    rolePill.className = 'px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#F3F1EF] text-[#202124] border border-[#E8E4E1]';
                    rolePill.classList.remove('hidden');
                } else if (profile.role === 'volunteer') {
                    const status = currentVolunteerProfile?.application_status || 'PENDING';
                    rolePill.textContent = status === 'APPROVED' ? 'Peer Volunteer' : `Volunteer (${status})`;
                    rolePill.className = status === 'APPROVED' ? 'px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FFE9DC] text-[#B83D08]' : 'px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800';
                    rolePill.classList.remove('hidden');
                } else {
                    // Standard user account: NEVER display "Student" as part of the user's visible account identity
                    rolePill.classList.add('hidden');
                    rolePill.textContent = '';
                }
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
    // REGISTRATION ERROR & DUPLICATE ACCOUNT HANDLING
    // =========================================================================
    function isDuplicateEmailError(error, data) {
        if (error) {
            const msg = (error.message || '').toLowerCase();
            const code = (error.code || '').toLowerCase();
            if (
                msg.includes('already registered') ||
                msg.includes('already exists') ||
                msg.includes('already in use') ||
                msg.includes('duplicate') ||
                code === 'user_already_exists' ||
                code === 'email_exists'
            ) {
                return true;
            }
        }
        // Supabase GoTrue privacy feature: when email confirmation is enabled,
        // signUp for an existing email returns status 200 with an empty identities array: data.user.identities = []
        if (data && data.user) {
            if (Array.isArray(data.user.identities) && data.user.identities.length === 0) {
                return true;
            }
        }
        return false;
    }

    function showRegisterError(msg, isDuplicate = false) {
        const dict = AUTH_I18N[currentAuthLang] || AUTH_I18N.en;
        const box = document.getElementById('auth-reg-error-box');
        const title = document.getElementById('auth-reg-error-title');
        const desc = document.getElementById('auth-reg-error-desc');
        const action = document.getElementById('auth-reg-error-action');
        const btnText = document.getElementById('auth-reg-error-btn-text');

        if (title) title.textContent = dict.errorNotice || "Notice";
        if (desc) desc.textContent = msg;

        if (action) {
            if (isDuplicate) {
                action.classList.remove('hidden');
                if (btnText) btnText.textContent = dict.loginWithEmailBtn || "Log in with this email →";
            } else {
                action.classList.add('hidden');
            }
        }

        if (box) {
            box.classList.remove('hidden');
        }

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(msg);
        }
    }

    function clearRegisterError() {
        const box = document.getElementById('auth-reg-error-box');
        if (box) box.classList.add('hidden');
        const desc = document.getElementById('auth-reg-error-desc');
        if (desc) desc.textContent = '';
        const action = document.getElementById('auth-reg-error-action');
        if (action) action.classList.add('hidden');
    }

    function showSignInError(msg) {
        const dict = AUTH_I18N[currentAuthLang] || AUTH_I18N.en;
        const box = document.getElementById('auth-login-error-box');
        const title = document.getElementById('auth-login-error-title');
        const desc = document.getElementById('auth-login-error-desc');

        if (title) title.textContent = dict.errorNotice || "Notice";
        if (desc) desc.textContent = msg;

        if (box) {
            box.classList.remove('hidden');
        }

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(msg);
        }
    }

    function clearSignInError() {
        const box = document.getElementById('auth-login-error-box');
        if (box) box.classList.add('hidden');
        const desc = document.getElementById('auth-login-error-desc');
        if (desc) desc.textContent = '';
    }

    // =========================================================================
    // STANDARD TEMPO REGISTRATION (PHASE 1)
    // =========================================================================
    async function registerWithCredentials(displayName, email, password) {
        clearRegisterError();
        const dict = AUTH_I18N[currentAuthLang] || AUTH_I18N.en;

        // Support both register(email, password) and register(displayName, email, password)
        if (displayName && email && !password) {
            password = email;
            email = displayName;
            displayName = (email || '').split('@')[0] || 'Tempo User';
        }

        if (!displayName || !email || !password) {
            showRegisterError(dict.fillRequired, false);
            return false;
        }

        if (password.length < 6) {
            showRegisterError(dict.passTooShort, false);
            return false;
        }

        const normalizedEmail = (email || '').trim().toLowerCase();

        const supabase = window.TempoSupabase ? window.TempoSupabase.getClient() : null;
        if (!supabase) {
            if (!isLocalEnvironment()) {
                showRegisterError("Authentication backend is not configured. Please ensure environment variables are set.", false);
                return false;
            }

            // Check if mock account already exists for this email
            const existingMock = localStorage.getItem('tempo_mock_account_' + normalizedEmail) ||
                                 localStorage.getItem('tempo_mock_account_' + email.trim());
            let devUserEmail = null;
            try {
                const rawDev = localStorage.getItem('tempo_local_dev_user');
                if (rawDev) {
                    const parsedDev = JSON.parse(rawDev);
                    if (parsedDev && parsedDev.email) {
                        devUserEmail = parsedDev.email.trim().toLowerCase();
                    }
                }
            } catch (e) {}

            if (existingMock || (devUserEmail && devUserEmail === normalizedEmail)) {
                showRegisterError(dict.emailAlreadyRegistered, true);
                return false;
            }

            const userId = 'local_user_' + btoa(normalizedEmail).replace(/[^a-zA-Z0-9]/g, '');
            const mockAccount = {
                id: userId,
                email: normalizedEmail,
                raw_email: email.trim(),
                password: password,
                user_metadata: {
                    full_name: displayName.trim(),
                    display_name: displayName.trim(),
                    role: 'student'
                }
            };
            try {
                localStorage.setItem('tempo_mock_account_' + normalizedEmail, JSON.stringify(mockAccount));
                if (normalizedEmail !== email.trim()) {
                    localStorage.setItem('tempo_mock_account_' + email.trim(), JSON.stringify(mockAccount));
                }
            } catch (e) {}

            // TASK 2 CONTRACT (Invariant 14): Register Success does NOT authenticate and does NOT resume intent.
            // Pending Intent is preserved. Transition to Sign In modal to require explicit login.
            closeAllAuthModals();
            openSignInModal(normalizedEmail);

            if (window.TempoApp && typeof window.TempoApp.triggerConfetti === 'function') {
                window.TempoApp.triggerConfetti();
            }
            window.TempoApp.showToast(`Account created for ${displayName.trim()}! Please sign in to continue.`);
            return true;
        }

        try {
            isRegistrationInProgress = true;
            const { data, error } = await supabase.auth.signUp({
                email: normalizedEmail,
                password,
                options: {
                    data: {
                        full_name: displayName.trim(),
                        display_name: displayName.trim(),
                        role: 'student'
                    }
                }
            });

            if (isDuplicateEmailError(error, data)) {
                showRegisterError(dict.emailAlreadyRegistered, true);
                return false;
            }

            if (error) {
                console.error("Supabase registration error:", error);
                showRegisterError(dict.genericRegError || "Registration failed. Please verify your information and try again.", false);
                return false;
            }

            // TASK 2 CONTRACT (Invariant 14): Register Success does NOT authenticate and does NOT resume intent.
            // If Supabase automatically creates an active session on signUp, immediately sign it out
            // so the user MUST explicitly log in. Pending Intent is preserved.
            if (data && data.session) {
                try {
                    await supabase.auth.signOut();
                } catch (e) {}
            }
            try {
                const { data: sData } = await supabase.auth.getSession();
                if (sData && sData.session) {
                    await supabase.auth.signOut({ scope: 'local' });
                }
            } catch (e) {}

            currentUser = null;
            currentProfile = null;
            currentVolunteerProfile = null;
            authState = 'anonymous';
            renderHeaderUI(null);

            closeAllAuthModals();
            openSignInModal(normalizedEmail);

            if (window.TempoApp && typeof window.TempoApp.triggerConfetti === 'function') {
                window.TempoApp.triggerConfetti();
            }
            window.TempoApp.showToast(`Account created for ${displayName.trim()}! Please sign in to continue.`);
            return true;

        } catch (err) {
            console.error("Register unexpected error:", err);
            showRegisterError(dict.genericRegError || "An unexpected error occurred. Please try again.", false);
            return false;
        } finally {
            isRegistrationInProgress = false;
        }
    }

    async function handleRegister(e) {
        if (e && e.preventDefault) e.preventDefault();
        const nameInput = document.getElementById('reg-display-name');
        const emailInput = document.getElementById('reg-email');
        const passInput = document.getElementById('reg-password');

        const displayName = nameInput ? nameInput.value.trim() : '';
        const email = emailInput ? emailInput.value.trim() : '';
        const password = passInput ? passInput.value : '';

        const submitBtn = e && e.target ? e.target.querySelector('button[type="submit"]') : document.getElementById('btn-submit-register');
        const originalText = submitBtn ? submitBtn.textContent : '';
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = currentAuthLang === 'vi' ? "Đang tạo tài khoản..." : "Creating account...";
        }

        try {
            await registerWithCredentials(displayName, email, password);
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        }
    }

    // =========================================================================
    // DORMANT LEGACY STUDENT REGISTRATION (US02) - PRESERVED FOR COMPATIBILITY
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
        const normalizedEmail = (email || '').trim().toLowerCase();
        const dict = AUTH_I18N[currentAuthLang] || AUTH_I18N.en;

        if (!supabase) {
            if (!isLocalEnvironment()) {
                window.TempoApp.showToast("Authentication backend is not configured. Please ensure environment variables are set.", 5000);
                return;
            }

            const existingMock = localStorage.getItem('tempo_mock_account_' + normalizedEmail) || localStorage.getItem('tempo_mock_account_' + email);
            if (existingMock) {
                window.TempoApp.showToast(dict.emailAlreadyRegistered);
                return;
            }

            const userId = 'local_student_' + btoa(normalizedEmail).replace(/[^a-zA-Z0-9]/g, '');
            const mockAccount = {
                id: userId,
                email: normalizedEmail,
                password: password,
                full_name: fullName,
                role: 'student',
                university: university || 'Not specified',
                year_of_study: yearOfStudy || 'Not specified'
            };
            try { localStorage.setItem('tempo_mock_account_' + normalizedEmail, JSON.stringify(mockAccount)); } catch (e) {}

            closeAllAuthModals();
            openSignInModal(normalizedEmail);

            window.TempoApp.triggerConfetti();
            window.TempoApp.showToast(`Account created for ${fullName}! Please sign in to continue.`);
            return;
        }

        const submitBtn = e.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = "Creating Student Account...";

        try {
            isRegistrationInProgress = true;
            const { data, error } = await supabase.auth.signUp({
                email: normalizedEmail,
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

            if (isDuplicateEmailError(error, data)) {
                window.TempoApp.showToast(dict.emailAlreadyRegistered);
                return;
            }

            if (error) {
                window.TempoApp.showToast(dict.genericRegError || `Registration failed: ${error.message}`);
                return;
            }

            if (data && data.session) {
                try { await supabase.auth.signOut(); } catch (e) {}
            }
            try {
                const { data: sData } = await supabase.auth.getSession();
                if (sData && sData.session) {
                    await supabase.auth.signOut({ scope: 'local' });
                }
            } catch (e) {}

            currentUser = null;
            currentProfile = null;
            currentVolunteerProfile = null;
            authState = 'anonymous';
            renderHeaderUI(null);

            closeAllAuthModals();
            openSignInModal(normalizedEmail);
            const signinEmailInput = document.getElementById('signin-email');
            if (signinEmailInput) signinEmailInput.value = email;

            window.TempoApp.triggerConfetti();
            window.TempoApp.showToast(`Account created for ${fullName}! Please sign in to continue.`);

        } catch (err) {
            console.error("Student register error:", err);
            window.TempoApp.showToast("An unexpected error occurred. Please try again.");
        } finally {
            isRegistrationInProgress = false;
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
            isRegistrationInProgress = true;
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

            if (isDuplicateEmailError(error, data)) {
                const dict = AUTH_I18N[currentAuthLang] || AUTH_I18N.en;
                window.TempoApp.showToast(dict.emailAlreadyRegistered);
                return;
            }

            if (error) {
                window.TempoApp.showToast("Application failed. Please verify your information and try again.");
                return;
            }

            if (data && data.session) {
                try { await supabase.auth.signOut(); } catch (e) {}
            }
            try {
                const { data: sData } = await supabase.auth.getSession();
                if (sData && sData.session) {
                    await supabase.auth.signOut({ scope: 'local' });
                }
            } catch (e) {}

            currentUser = null;
            currentProfile = null;
            currentVolunteerProfile = null;
            authState = 'anonymous';
            renderHeaderUI(null);

            closeAllAuthModals();
            // Open Application Submitted Notice Screen
            openVolunteerSubmittedModal(fullName);

        } catch (err) {
            console.error("Volunteer apply error:", err);
            window.TempoApp.showToast("Failed to submit application. Please try again.");
        } finally {
            isRegistrationInProgress = false;
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }

    // =========================================================================
    // SIGN IN
    // =========================================================================
    async function signInWithCredentials(email, password) {
        clearSignInError();
        const dict = AUTH_I18N[currentAuthLang] || AUTH_I18N.en;

        if (!email || !password) {
            showSignInError(dict.fillRequired || "Please enter both email and password.");
            return false;
        }

        const normalizedEmail = (email || '').trim().toLowerCase();

        const supabase = window.TempoSupabase ? window.TempoSupabase.getClient() : null;
        isExplicitSignInInProgress = true;
        try {
            if (!supabase) {
                if (!isLocalEnvironment()) {
                    showSignInError("Authentication backend is not configured. Please ensure SUPABASE_URL and publishable key are set in environment variables.");
                    return false;
                }

                // In local development fallback:
                // An email that has NEVER been registered MUST NOT be able to log in.
                const storedMock = localStorage.getItem('tempo_mock_account_' + normalizedEmail) ||
                                     localStorage.getItem('tempo_mock_account_' + email.trim());
                
                if (!storedMock) {
                    showSignInError(dict.invalidCredentials || "Email or password is incorrect.");
                    return false;
                }

                let parsed = null;
                try {
                    parsed = JSON.parse(storedMock);
                } catch (e) {
                    showSignInError(dict.invalidCredentials || "Email or password is incorrect.");
                    return false;
                }

                if (!parsed || parsed.password !== password) {
                    showSignInError(dict.invalidCredentials || "Email or password is incorrect.");
                    return false;
                }

                let name = parsed.user_metadata?.full_name || parsed.user_metadata?.display_name || parsed.full_name || normalizedEmail.split('@')[0];
                let role = parsed.user_metadata?.role || parsed.role || 'student';
                const userId = parsed.id || ('local_user_' + btoa(normalizedEmail).replace(/[^a-zA-Z0-9]/g, ''));

                currentUser = { 
                    id: userId, 
                    email: normalizedEmail,
                    user_metadata: { full_name: name, display_name: name, role: role }
                };
                try { localStorage.setItem('tempo_local_dev_user', JSON.stringify(currentUser)); } catch (e) {}
                currentProfile = {
                    id: currentUser.id,
                    email: normalizedEmail,
                    full_name: name,
                    display_name: name,
                    role: role
                };
                authState = 'authenticated';
                renderHeaderUI(currentProfile);
                closeAllAuthModals();
                window.TempoApp.showToast(`Welcome back, ${name}!`);

                const intentHandled = await syncPlanForUser(currentUser.id);
                if (!intentHandled) {
                    window.TempoApp.navigateTo('today');
                }
                return true;
            }

            try {
                const { data, error } = await supabase.auth.signInWithPassword({
                    email: normalizedEmail,
                    password
                });

                // Guard against login rejection or missing session/user
                if (error || !data || !data.session || !data.user) {
                    showSignInError(dict.invalidCredentials || "Email or password is incorrect.");
                    return false;
                }

                closeAllAuthModals();
                currentUser = data.user;
                authState = 'authenticated';
                await loadUserProfile(data.user.id);
                const intentHandled = await syncPlanForUser(data.user.id);
                const welcomeName = currentProfile?.display_name || currentProfile?.full_name || email;
                window.TempoApp.showToast(`Welcome back, ${welcomeName}!`);

                if (!intentHandled) {
                    if (currentProfile?.role === 'volunteer') {
                        window.TempoApp.navigateTo('volunteer-dashboard');
                    } else if (currentProfile?.role === 'admin') {
                        window.TempoApp.navigateTo('admin');
                    } else {
                        window.TempoApp.navigateTo('today');
                    }
                }
                return true;

            } catch (err) {
                console.error("Sign in error:", err);
                showSignInError(dict.invalidCredentials || "Email or password is incorrect.");
                return false;
            }
        } finally {
            isExplicitSignInInProgress = false;
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
    // FORGOT PASSWORD
    // =========================================================================
    async function handleForgotPassword() {
        const emailInput = document.getElementById('signin-email');
        const defaultEmail = emailInput ? emailInput.value.trim() : '';
        const dict = AUTH_I18N[currentAuthLang] || AUTH_I18N.en;

        const email = prompt(dict.forgotPrompt, defaultEmail);
        if (!email || !email.trim()) return;

        const supabase = window.TempoSupabase ? window.TempoSupabase.getClient() : null;
        if (!supabase) {
            window.TempoApp.showToast(dict.forgotSent + " (Dev Mode)");
            return;
        }

        try {
            const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
                redirectTo: window.location.origin
            });
            if (error) {
                window.TempoApp.showToast(`Error: ${error.message}`);
            } else {
                window.TempoApp.showToast(dict.forgotSent);
            }
        } catch (err) {
            console.error("Forgot password error:", err);
            window.TempoApp.showToast("Could not send reset email. Please try again.");
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
        authState = 'anonymous';
        renderHeaderUI(null);

        syncPlanForSignOut();

        window.TempoApp.showToast("You have been signed out.");
        window.TempoApp.navigateTo('today');
    }

    // =========================================================================
    // MODAL CONTROLLERS
    // =========================================================================
    function openRegisterModal() {
        closeAllAuthModals();
        clearRegisterError();
        clearSignInError();
        const modal = document.getElementById('modal-register');
        if (modal) {
            modal.classList.remove('hidden');
            const nameInput = document.getElementById('reg-display-name');
            if (nameInput) setTimeout(() => nameInput.focus(), 50);
        }
    }

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

    function openSignInModal(prefillEmail) {
        closeAllAuthModals();
        clearSignInError();
        const modal = document.getElementById('modal-signin');
        if (modal) {
            modal.classList.remove('hidden');
            const emailInput = document.getElementById('signin-email');
            const passInput = document.getElementById('signin-password');
            if (emailInput) {
                if (typeof prefillEmail === 'string' && prefillEmail.trim()) {
                    emailInput.value = prefillEmail.trim();
                } else if (!emailInput.value) {
                    const regEmailInput = document.getElementById('reg-email');
                    if (regEmailInput && regEmailInput.value) {
                        emailInput.value = regEmailInput.value.trim();
                    }
                }
                if (emailInput.value && passInput) {
                    setTimeout(() => passInput.focus(), 50);
                } else {
                    setTimeout(() => emailInput.focus(), 50);
                }
            }
        }
    }

    function openVolunteerSubmittedModal(name) {
        closeAllAuthModals();
        const modal = document.getElementById('modal-volunteer-submitted');
        if (modal) {
            const nameEl = document.getElementById('vol-submitted-name');
            if (nameEl) nameEl.textContent = name;
            modal.classList.remove('hidden');
        }
    }

    function closeAllAuthModals() {
        document.querySelectorAll('.auth-modal-overlay').forEach(modal => {
            modal.classList.add('hidden');
        });
    }

    function cancelAuthModal() {
        closeAllAuthModals();
        if (window.TempoMode && typeof window.TempoMode.handleAuthCancel === 'function') {
            window.TempoMode.handleAuthCancel();
        }
    }

    return {
        init,
        checkSession,
        waitForAuthResolution: () => authReadyPromise,
        getAuthState: () => (currentUser ? 'authenticated' : (authState === 'AUTH_LOADING' ? 'AUTH_LOADING' : 'anonymous')),
        getCurrentUser: () => currentUser,
        getCurrentUserId: () => currentUser ? currentUser.id : null,
        getCurrentProfile: () => currentProfile,
        getCurrentVolunteerProfile: () => currentVolunteerProfile,
        openRegisterModal,
        openRoleSelectModal,
        openStudentRegisterModal,
        openVolunteerApplyModal,
        openSignInModal,
        closeModal: cancelAuthModal,
        closeAllAuthModals,
        cancelAuthModal,
        closeRegisterModal: cancelAuthModal,
        closeSignInModal: cancelAuthModal,
        register: registerWithCredentials,
        signUp: registerWithCredentials,
        signIn: signInWithCredentials,
        handleSignOut,
        signOut: handleSignOut,
        handleForgotPassword,
        setAuthLanguage,
        getAuthLanguage: () => currentAuthLang,
        getInitials,
        loadUserProfile,
        extractGreetingName,
        updateUserGreeting,
        syncPlanForUser,
        syncPlanForSignOut,
        isDuplicateEmailError,
        showRegisterError,
        clearRegisterError,
        showSignInError,
        clearSignInError,
        isRegistrationInProgress: () => isRegistrationInProgress
    };
})();
