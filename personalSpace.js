/**
 * Tempo - Personal Space Controller
 * Manages the single shared Personal Space page with 4 sections:
 * 1. Saved (Đã lưu)
 * 2. My Library (Thư viện của tôi)
 * 3. Account (Tài khoản)
 * 4. Settings (Cài đặt)
 */

window.TempoPersonalSpace = (function() {
    let activeTab = 'saved';
    let activeLibrarySubtab = 'avatars';
    let activeSavedFilter = 'all';

    const VALID_TABS = ['saved', 'library', 'account', 'settings'];
    const VALID_LIBRARY_SUBTABS = ['avatars', 'backgrounds', 'sounds'];
    const VALID_SAVED_FILTERS = ['all', 'posts', 'learn'];

    function init() {
        bindSidebarNavigation();
        bindMobileTabs();
        bindSavedFilters();
        bindLibrarySubtabs();
        bindInlineNameEdit();
        bindAccountInteractions();
        bindSettingsControls();
        bindPolicyModals();

        // Sync initial profile if auth is already loaded
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentProfile === 'function') {
            const profile = window.TempoAuth.getCurrentProfile();
            if (profile) syncProfile(profile);
        }
    }

    /**
     * Bind desktop left sidebar buttons
     */
    function bindSidebarNavigation() {
        document.querySelectorAll('[data-ps-tab]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const tab = btn.getAttribute('data-ps-tab');
                selectTab(tab);
            });
        });
    }

    /**
     * Bind mobile horizontal tab strip
     */
    function bindMobileTabs() {
        document.querySelectorAll('[data-ps-mobile-tab]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const tab = btn.getAttribute('data-ps-mobile-tab');
                selectTab(tab);
            });
        });
    }

    /**
     * Switch active section within Personal Space
     * @param {string} tabId - 'saved' | 'library' | 'account' | 'settings'
     * @param {boolean} updateUrl - whether to update location hash
     */
    function selectTab(tabId, updateUrl = true) {
        if (!VALID_TABS.includes(tabId)) {
            tabId = 'saved';
        }
        activeTab = tabId;

        // 1. Update Desktop Sidebar active styling
        document.querySelectorAll('[data-ps-tab]').forEach(btn => {
            const target = btn.getAttribute('data-ps-tab');
            const icon = btn.querySelector('.ps-nav-icon');
            if (target === tabId) {
                btn.className = 'w-full flex items-center space-x-3 px-4 py-3 rounded-2xl text-xs sm:text-sm font-bold bg-[#FFE9DC] text-[#FF6B2C] border-l-4 border-[#FF6B2C] shadow-xs transition-all cursor-pointer';
                if (icon) {
                    icon.classList.remove('text-[#6F6B68]');
                    icon.classList.add('text-[#FF6B2C]');
                }
            } else {
                btn.className = 'w-full flex items-center space-x-3 px-4 py-3 rounded-2xl text-xs sm:text-sm font-medium text-[#6F6B68] hover:text-[#202124] hover:bg-[#F3F1EF] transition-all cursor-pointer';
                if (icon) {
                    icon.classList.remove('text-[#FF6B2C]');
                    icon.classList.add('text-[#6F6B68]');
                }
            }
        });

        // 2. Update Mobile Tab strip active styling
        document.querySelectorAll('[data-ps-mobile-tab]').forEach(btn => {
            const target = btn.getAttribute('data-ps-mobile-tab');
            if (target === tabId) {
                btn.className = 'px-4 py-2 rounded-xl text-xs font-bold whitespace-nowrap bg-[#FFE9DC] text-[#FF6B2C] border border-[#FF6B2C]/30 shadow-xs cursor-pointer';
            } else {
                btn.className = 'px-4 py-2 rounded-xl text-xs font-medium whitespace-nowrap bg-white text-[#6F6B68] border border-[#E8E4E1] hover:bg-[#F8F6F4] hover:text-[#202124] cursor-pointer';
            }
        });

        // 3. Show target section container, hide others
        VALID_TABS.forEach(t => {
            const section = document.getElementById(`personal-tab-${t}`);
            if (section) {
                if (t === tabId) {
                    section.classList.remove('hidden');
                } else {
                    section.classList.add('hidden');
                }
            }
        });

        // 4. Preserve in URL hash if requested (e.g. #personal-space?tab=account)
        if (updateUrl) {
            window.location.hash = `#personal-space?tab=${tabId}`;
        }

        // 5. Re-sync current profile details if viewing account
        if (tabId === 'account' && window.TempoAuth && typeof window.TempoAuth.getCurrentProfile === 'function') {
            syncProfile(window.TempoAuth.getCurrentProfile());
        }
    }

    /**
     * Sync profile information to Account section UI
     */
    function syncProfile(profile) {
        if (!profile) return;
        const displayName = profile.display_name || profile.full_name || profile.email || 'Tempo User';
        const email = profile.email || '';

        // Display Name text
        const nameTextEl = document.getElementById('account-display-name-text');
        if (nameTextEl) nameTextEl.textContent = displayName;

        // Display Name input
        const nameInputEl = document.getElementById('account-display-name-input');
        if (nameInputEl) nameInputEl.value = displayName;

        // Email text
        const emailTextEl = document.getElementById('account-email-text');
        if (emailTextEl) emailTextEl.textContent = email;

        // Avatar circles
        const avatarEl = document.getElementById('account-avatar-preview');
        if (avatarEl) {
            if (profile.avatar_url) {
                avatarEl.innerHTML = `<img src="${escapeHTML(profile.avatar_url)}" alt="${escapeHTML(displayName)}" class="w-full h-full rounded-full object-cover">`;
            } else {
                const initials = getInitials(displayName);
                avatarEl.textContent = initials;
            }
        }

        // Mini preview in dropdown
        const dropAvatar = document.getElementById('header-dropdown-avatar');
        if (dropAvatar) {
            if (profile.avatar_url) {
                dropAvatar.innerHTML = `<img src="${escapeHTML(profile.avatar_url)}" alt="${escapeHTML(displayName)}" class="w-full h-full rounded-full object-cover">`;
            } else {
                dropAvatar.textContent = getInitials(displayName);
            }
        }
    }

    /**
     * Inline Display Name Edit
     */
    function bindInlineNameEdit() {
        const btnEdit = document.getElementById('btn-edit-display-name');
        const btnCancel = document.getElementById('btn-cancel-edit-name');
        const btnSave = document.getElementById('btn-save-edit-name');
        const viewRow = document.getElementById('account-name-view-row');
        const editRow = document.getElementById('account-name-edit-row');
        const input = document.getElementById('account-display-name-input');

        if (btnEdit && viewRow && editRow && input) {
            btnEdit.addEventListener('click', () => {
                viewRow.classList.add('hidden');
                editRow.classList.remove('hidden');
                input.focus();
                input.select();
            });
        }

        if (btnCancel && viewRow && editRow) {
            btnCancel.addEventListener('click', () => {
                editRow.classList.add('hidden');
                viewRow.classList.remove('hidden');
            });
        }

        if (btnSave && viewRow && editRow && input) {
            btnSave.addEventListener('click', () => {
                const newName = input.value.trim();
                if (!newName) {
                    if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                        window.TempoApp.showToast("Display name cannot be empty.");
                    }
                    return;
                }

                // Update current user profile in auth
                if (window.TempoAuth && typeof window.TempoAuth.getCurrentProfile === 'function') {
                    const profile = window.TempoAuth.getCurrentProfile();
                    if (profile) {
                        profile.display_name = newName;
                        profile.full_name = newName;
                        try {
                            // Update local storage mock if present
                            const devUser = localStorage.getItem('tempo_local_dev_user');
                            if (devUser) {
                                const parsed = JSON.parse(devUser);
                                parsed.user_metadata = parsed.user_metadata || {};
                                parsed.user_metadata.full_name = newName;
                                parsed.user_metadata.display_name = newName;
                                localStorage.setItem('tempo_local_dev_user', JSON.stringify(parsed));
                            }
                        } catch (e) {}
                        
                        // Update UI throughout app
                        syncProfile(profile);
                        if (typeof window.TempoAuth.renderHeaderUI === 'function') {
                            window.TempoAuth.renderHeaderUI(profile);
                        }
                    }
                }

                editRow.classList.add('hidden');
                viewRow.classList.remove('hidden');

                if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                    window.TempoApp.showToast("Display name updated successfully.");
                }
            });

            // Enter key submits inline edit
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    btnSave.click();
                } else if (e.key === 'Escape') {
                    e.preventDefault();
                    if (btnCancel) btnCancel.click();
                }
            });
        }
    }

    /**
     * Account section triggers (Avatar change, change password, danger zone)
     */
    function bindAccountInteractions() {
        // Change avatar -> takes user to My Library (Avatars tab)
        const btnChangeAvatar = document.getElementById('btn-account-change-avatar');
        if (btnChangeAvatar) {
            btnChangeAvatar.addEventListener('click', () => {
                selectTab('library');
                selectLibrarySubtab('avatars');
            });
        }

        // Change password trigger entry point
        const btnChangePass = document.getElementById('btn-account-change-password');
        if (btnChangePass) {
            btnChangePass.addEventListener('click', () => {
                if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                    window.TempoApp.showToast("Password reset link will be sent to your primary email address.");
                }
            });
        }

        // Danger zone DELETE confirmation input
        const deleteInput = document.getElementById('account-delete-confirm-input');
        const deleteBtn = document.getElementById('btn-account-delete-confirm');
        if (deleteInput && deleteBtn) {
            deleteInput.addEventListener('input', () => {
                const val = deleteInput.value.trim();
                if (val === 'DELETE') {
                    deleteBtn.disabled = false;
                    deleteBtn.className = 'px-4 py-2 rounded-xl text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 shadow-xs cursor-pointer transition';
                } else {
                    deleteBtn.disabled = true;
                    deleteBtn.className = 'px-4 py-2 rounded-xl text-xs font-bold text-rose-300 bg-rose-100 cursor-not-allowed opacity-60 transition';
                }
            });

            deleteBtn.addEventListener('click', () => {
                if (deleteInput.value.trim() === 'DELETE') {
                    if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                        window.TempoApp.showToast("Account deletion confirmation placeholder. Permanent deletion requires backend support.");
                    }
                }
            });
        }
    }

    /**
     * Saved Filters (All, Posts, Learn)
     */
    function bindSavedFilters() {
        document.querySelectorAll('[data-saved-filter]').forEach(btn => {
            btn.addEventListener('click', () => {
                const filter = btn.getAttribute('data-saved-filter');
                selectSavedFilter(filter);
            });
        });
    }

    function selectSavedFilter(filter) {
        if (!VALID_SAVED_FILTERS.includes(filter)) filter = 'all';
        activeSavedFilter = filter;

        document.querySelectorAll('[data-saved-filter]').forEach(btn => {
            const f = btn.getAttribute('data-saved-filter');
            if (f === filter) {
                btn.className = 'px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#FFE9DC] text-[#FF6B2C] border border-[#FF6B2C]/40 shadow-xs cursor-pointer';
            } else {
                btn.className = 'px-3.5 py-1.5 rounded-full text-xs font-medium bg-[#F3F1EF] text-[#6F6B68] hover:text-[#202124] hover:bg-[#EAE4DF] cursor-pointer';
            }
        });
    }

    /**
     * My Library Subtabs (Avatars, Backgrounds, Sounds)
     */
    function bindLibrarySubtabs() {
        document.querySelectorAll('[data-library-subtab]').forEach(btn => {
            btn.addEventListener('click', () => {
                const subtab = btn.getAttribute('data-library-subtab');
                selectLibrarySubtab(subtab);
            });
        });

        // Upload entry point triggers
        const btnUpload = document.getElementById('btn-library-upload');
        if (btnUpload) {
            btnUpload.addEventListener('click', () => {
                if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                    const label = activeLibrarySubtab === 'avatars' ? 'avatar' : (activeLibrarySubtab === 'backgrounds' ? 'background image' : 'sound track');
                    window.TempoApp.showToast(`Upload entry point for ${label}. File storage integration will be connected in next phase.`);
                }
            });
        }
    }

    function selectLibrarySubtab(subtab) {
        if (!VALID_LIBRARY_SUBTABS.includes(subtab)) subtab = 'avatars';
        activeLibrarySubtab = subtab;

        // Update button styles
        document.querySelectorAll('[data-library-subtab]').forEach(btn => {
            const s = btn.getAttribute('data-library-subtab');
            if (s === subtab) {
                btn.className = 'px-4 py-2 rounded-xl text-xs font-bold bg-[#202124] text-white shadow-xs cursor-pointer transition';
            } else {
                btn.className = 'px-4 py-2 rounded-xl text-xs font-medium text-[#6F6B68] hover:text-[#202124] hover:bg-[#F3F1EF] cursor-pointer transition';
            }
        });

        // Show corresponding subtab view
        VALID_LIBRARY_SUBTABS.forEach(s => {
            const view = document.getElementById(`library-view-${s}`);
            if (view) {
                if (s === subtab) {
                    view.classList.remove('hidden');
                } else {
                    view.classList.add('hidden');
                }
            }
        });
    }

    /**
     * Settings controls: Language selector, notifications toggles
     */
    function bindSettingsControls() {
        // Language Selector in Settings
        document.querySelectorAll('.settings-lang-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const lang = btn.getAttribute('data-lang');
                if (lang && ['vi', 'en'].includes(lang)) {
                    if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                        window.TempoI18n.setLanguage(lang);
                    } else if (window.TempoAuth && typeof window.TempoAuth.setAuthLanguage === 'function') {
                        window.TempoAuth.setAuthLanguage(lang);
                    }
                    updateSettingsLanguageUI(lang);
                    if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                        window.TempoApp.showToast(lang === 'vi' ? 'Đã đổi ngôn ngữ sang Tiếng Việt' : 'Language switched to English');
                    }
                }
            });
        });

        // Notifications toggles
        const overallToggle = document.getElementById('settings-toggle-browser-push');
        if (overallToggle) {
            overallToggle.addEventListener('change', (e) => {
                const isChecked = e.target.checked;
                if (isChecked && 'Notification' in window) {
                    if (Notification.permission === 'default') {
                        Notification.requestPermission().then(permission => {
                            if (permission !== 'granted') {
                                e.target.checked = false;
                                if (window.TempoApp) window.TempoApp.showToast("Browser notification permission was not granted.");
                            } else {
                                if (window.TempoApp) window.TempoApp.showToast("Browser push notifications enabled.");
                            }
                        });
                        return;
                    } else if (Notification.permission === 'denied') {
                        e.target.checked = false;
                        if (window.TempoApp) window.TempoApp.showToast("Browser notifications are blocked in your browser settings.");
                        return;
                    }
                }
                if (window.TempoApp) {
                    window.TempoApp.showToast(isChecked ? "Browser push notifications enabled." : "Browser push notifications disabled.");
                }
            });
        }

        // Subcategory reminder toggles
        ['settings-toggle-selfcheck', 'settings-toggle-plan', 'settings-toggle-weekly'].forEach(id => {
            const toggle = document.getElementById(id);
            if (toggle) {
                toggle.addEventListener('change', (e) => {
                    if (window.TempoApp) {
                        window.TempoApp.showToast("Notification preference updated.");
                    }
                });
            }
        });
    }

    function updateSettingsLanguageUI(lang) {
        document.querySelectorAll('.settings-lang-btn').forEach(btn => {
            const btnLang = btn.getAttribute('data-lang');
            if (btnLang === lang) {
                btn.className = 'settings-lang-btn px-4 py-2 rounded-xl text-xs font-bold bg-[#FF6B2C] text-white shadow-xs cursor-pointer';
            } else {
                btn.className = 'settings-lang-btn px-4 py-2 rounded-xl text-xs font-medium text-[#6F6B68] hover:text-[#202124] hover:bg-[#F3F1EF] cursor-pointer';
            }
        });
    }

    /**
     * Terms of Service & Privacy Policy Modals
     */
    function bindPolicyModals() {
        // Terms of Service modal triggers
        document.querySelectorAll('a[href="#terms"]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                openPolicyModal('terms');
            });
        });

        // Privacy Policy modal triggers
        document.querySelectorAll('a[href="#privacy"]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                openPolicyModal('privacy');
            });
        });

        // Close buttons on policy modals
        document.querySelectorAll('.btn-close-policy-modal').forEach(btn => {
            btn.addEventListener('click', () => {
                closePolicyModals();
            });
        });

        document.querySelectorAll('.policy-modal-overlay').forEach(overlay => {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) closePolicyModals();
            });
        });
    }

    function openPolicyModal(type) {
        closePolicyModals();
        const modal = document.getElementById(type === 'terms' ? 'modal-terms-policy' : 'modal-privacy-policy');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }

    function closePolicyModals() {
        const termsModal = document.getElementById('modal-terms-policy');
        if (termsModal) termsModal.classList.add('hidden');
        const privacyModal = document.getElementById('modal-privacy-policy');
        if (privacyModal) privacyModal.classList.add('hidden');
    }

    // Helpers
    function getInitials(name) {
        if (!name || typeof name !== 'string') return 'U';
        const trimmed = name.trim();
        if (!trimmed) return 'U';
        const cleanName = trimmed.includes('@') ? trimmed.split('@')[0] : trimmed;
        const parts = cleanName.split(/\s+/).filter(Boolean);
        if (parts.length === 0) return 'U';
        if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
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

    return {
        init,
        selectTab,
        syncProfile,
        selectLibrarySubtab,
        selectSavedFilter,
        openPolicyModal,
        closePolicyModals,
        getActiveTab: () => activeTab
    };
})();
