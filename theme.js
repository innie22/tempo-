/**
 * Tempo Theme & Appearance Controller
 * Manages global background customization with 11 official Tempo palette presets.
 */

(function() {
    'use strict';

    const BACKGROUND_PRESETS = [
        { id: 'sage-green', name: 'Sage Green', hex: '#8EA695' },
        { id: 'dusty-blue', name: 'Dusty Blue', hex: '#94B0BD' },
        { id: 'warm-blush', name: 'Warm Blush', hex: '#ECC9BA' },
        { id: 'soft-sage', name: 'Soft Sage', hex: '#D5E1D8' },
        { id: 'soft-blue', name: 'Soft Blue', hex: '#D1DEE4' },
        { id: 'warm-cream', name: 'Warm Cream', hex: '#F5EDE3' },
        { id: 'pale-pink', name: 'Pale Pink', hex: '#FDDBD8' },
        { id: 'blush-cream', name: 'Blush Cream', hex: '#FCE8E1' },
        { id: 'soft-beige', name: 'Soft Beige', hex: '#FAEDDB' },
        { id: 'cloud-blue', name: 'Cloud Blue', hex: '#E7EDF0' },
        { id: 'mist-green', name: 'Mist Green', hex: '#EAEEE8', isDefault: true }
    ];

    const DEFAULT_BG_HEX = '#EAEEE8';

    // State
    let activeColor = DEFAULT_BG_HEX;
    let selectedColor = DEFAULT_BG_HEX; // Color currently selected in Settings preview
    let isInitialized = false;

    function normalizeHex(hex) {
        if (!hex || typeof hex !== 'string') return DEFAULT_BG_HEX;
        return hex.trim().toUpperCase();
    }

    function isValidPreset(hex) {
        const norm = normalizeHex(hex);
        return BACKGROUND_PRESETS.some(p => p.hex.toUpperCase() === norm);
    }

    function getPresetByHex(hex) {
        const norm = normalizeHex(hex);
        return BACKGROUND_PRESETS.find(p => p.hex.toUpperCase() === norm) || BACKGROUND_PRESETS[10]; // Mist Green
    }

    function getCurrentUserId() {
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentUser === 'function') {
            const user = window.TempoAuth.getCurrentUser();
            return user?.id || null;
        }
        return null;
    }

    function getSavedColorForUser(userId) {
        if (userId) {
            // 1. Check user-specific localStorage key
            try {
                const userSaved = localStorage.getItem(`tempo_background_color_${userId}`);
                if (userSaved && isValidPreset(userSaved)) {
                    return normalizeHex(userSaved);
                }
            } catch (e) {}

            // 2. Check mock dev user metadata
            try {
                const devUser = localStorage.getItem('tempo_local_dev_user');
                if (devUser) {
                    const parsed = JSON.parse(devUser);
                    if (parsed.id === userId && parsed.user_metadata?.background_color) {
                        const bg = parsed.user_metadata.background_color;
                        if (isValidPreset(bg)) return normalizeHex(bg);
                    }
                }
            } catch (e) {}

            // 3. Check mock accounts if present
            try {
                const user = window.TempoAuth && window.TempoAuth.getCurrentUser ? window.TempoAuth.getCurrentUser() : null;
                if (user && user.email) {
                    const normEmail = user.email.trim().toLowerCase();
                    const mockData = localStorage.getItem('tempo_mock_account_' + normEmail);
                    if (mockData) {
                        const parsed = JSON.parse(mockData);
                        if (parsed.background_color && isValidPreset(parsed.background_color)) {
                            return normalizeHex(parsed.background_color);
                        }
                    }
                }
            } catch (e) {}

            // New user without preference -> Default Mist Green
            return DEFAULT_BG_HEX;
        }

        // Anonymous / guest user
        try {
            const anonSaved = localStorage.getItem('tempo_background_color');
            if (anonSaved && isValidPreset(anonSaved)) {
                return normalizeHex(anonSaved);
            }
        } catch (e) {}

        return DEFAULT_BG_HEX;
    }

    async function persistColorForUser(userId, hex) {
        const color = isValidPreset(hex) ? normalizeHex(hex) : DEFAULT_BG_HEX;

        if (userId) {
            try {
                localStorage.setItem(`tempo_background_color_${userId}`, color);
            } catch (e) {}

            // Update local dev user metadata
            try {
                const devUser = localStorage.getItem('tempo_local_dev_user');
                if (devUser) {
                    const parsed = JSON.parse(devUser);
                    if (parsed.id === userId) {
                        parsed.user_metadata = parsed.user_metadata || {};
                        parsed.user_metadata.background_color = color;
                        localStorage.setItem('tempo_local_dev_user', JSON.stringify(parsed));
                    }
                }
            } catch (e) {}

            // Update mock account record
            try {
                const user = window.TempoAuth && window.TempoAuth.getCurrentUser ? window.TempoAuth.getCurrentUser() : null;
                if (user && user.email) {
                    const normEmail = user.email.trim().toLowerCase();
                    const mockKey = 'tempo_mock_account_' + normEmail;
                    const mockData = localStorage.getItem(mockKey);
                    if (mockData) {
                        const parsed = JSON.parse(mockData);
                        parsed.background_color = color;
                        localStorage.setItem(mockKey, JSON.stringify(parsed));
                    }
                }
            } catch (e) {}

            // Supabase auth metadata update if client available
            try {
                const supabase = window.TempoSupabase ? window.TempoSupabase.getClient() : null;
                if (supabase && supabase.auth && typeof supabase.auth.updateUser === 'function') {
                    await supabase.auth.updateUser({
                        data: { background_color: color }
                    });
                }
            } catch (err) {
                console.warn("[TempoTheme] Supabase updateUser sync warning:", err);
            }
        } else {
            // Anonymous fallback
            try {
                localStorage.setItem('tempo_background_color', color);
            } catch (e) {}
        }
    }

    /**
     * Apply color to DOM surfaces cleanly
     */
    function applyThemeToDOM(hex) {
        const color = isValidPreset(hex) ? normalizeHex(hex) : DEFAULT_BG_HEX;

        // 1. CSS Custom Properties
        document.documentElement.style.setProperty('--tempo-bg-color', color);
        document.documentElement.style.setProperty('--bg-app', color);

        // 2. Direct body styling
        if (document.body) {
            document.body.style.backgroundColor = color;
            document.body.setAttribute('data-tempo-custom-bg', color);
            if (color.toUpperCase() !== DEFAULT_BG_HEX.toUpperCase()) {
                document.body.classList.add('has-custom-bg');
            } else {
                document.body.classList.remove('has-custom-bg');
            }
        }

        // 3. Header styling
        const header = document.querySelector('header.entry-header');
        if (header) {
            header.style.backgroundColor = color;
        }

        // 4. Main wrapper
        const mainEl = document.querySelector('main');
        if (mainEl) {
            mainEl.style.backgroundColor = 'transparent';
        }

        activeColor = color;
    }

    /**
     * Ensure current background is active (called on route transitions)
     */
    function ensureCurrentBackground() {
        applyThemeToDOM(activeColor);
    }

    /**
     * Load theme for specific user (e.g. on sign in or sign out)
     */
    function loadUserTheme(userId) {
        const saved = getSavedColorForUser(userId);
        activeColor = saved;
        selectedColor = saved;
        applyThemeToDOM(saved);
        syncSettingsUI();
    }

    /**
     * Render and bind Appearance Settings UI in Settings tab
     */
    function syncSettingsUI() {
        const container = document.getElementById('settings-group-appearance');
        if (!container) return;

        const isVi = (!window.TempoI18n || typeof window.TempoI18n.getLanguage !== 'function') 
            ? true 
            : (window.TempoI18n.getLanguage() === 'vi');

        // 1. Update text labels
        const groupHeading = document.getElementById('appearance-group-heading');
        if (groupHeading) groupHeading.textContent = isVi ? 'GIAO DIỆN' : 'APPEARANCE';

        const titleEl = document.getElementById('appearance-title');
        if (titleEl) titleEl.textContent = isVi ? 'Màu nền' : 'Background Color';

        const descEl = document.getElementById('appearance-description');
        if (descEl) descEl.textContent = isVi 
            ? 'Lựa chọn màu nền phù hợp với trải nghiệm Tempo của bạn.' 
            : 'Choose a background color for your Tempo experience.';

        const activeLabelEl = document.getElementById('appearance-active-label');
        if (activeLabelEl) activeLabelEl.textContent = isVi ? 'Đang dùng:' : 'Active:';

        const previewLabelEl = document.getElementById('appearance-preview-label');
        if (previewLabelEl) previewLabelEl.textContent = isVi ? 'XEM TRƯỚC' : 'PREVIEW';

        const btnReset = document.getElementById('btn-appearance-reset');
        if (btnReset) btnReset.textContent = isVi ? 'Đặt lại mặc định' : 'Reset to default';

        const btnApply = document.getElementById('btn-appearance-apply');
        if (btnApply) {
            const btnSpan = btnApply.querySelector('span');
            if (btnSpan) btnSpan.textContent = isVi ? 'Áp dụng' : 'Apply';
            else btnApply.textContent = isVi ? 'Áp dụng' : 'Apply';
        }

        // Preview mock labels
        const prevTitle = document.getElementById('appearance-preview-card-title');
        if (prevTitle) prevTitle.textContent = isVi ? 'Xem trước giao diện' : 'Tempo Preview';
        const prevBadge = document.getElementById('appearance-preview-card-badge');
        if (prevBadge) prevBadge.textContent = isVi ? 'Mẫu' : 'Sample';
        const prevDesc = document.getElementById('appearance-preview-desc');
        if (prevDesc) prevDesc.textContent = isVi
            ? 'Tông màu nền dịu mắt, giúp giảm căng thẳng và tăng khả năng tập trung.'
            : 'Soft, calming background tones designed to reduce stress and improve focus.';
        const prevSurface = document.getElementById('appearance-preview-surface-label');
        if (prevSurface) prevSurface.textContent = isVi ? 'Thẻ nội dung mẫu' : 'Card Surface';
        const prevBtn = document.getElementById('appearance-preview-sample-btn');
        if (prevBtn) prevBtn.textContent = isVi ? 'Nút bấm mẫu' : 'Sample Button';

        // 2. Active Indicator Badge
        const activePreset = getPresetByHex(activeColor);
        const activeDot = document.getElementById('appearance-active-dot');
        if (activeDot) activeDot.style.backgroundColor = activePreset.hex;
        const activeName = document.getElementById('appearance-active-name');
        if (activeName) activeName.textContent = activePreset.name;

        // 3. Preview Box
        const selectedPreset = getPresetByHex(selectedColor);
        const previewBox = document.getElementById('appearance-preview-box');
        if (previewBox) {
            previewBox.style.backgroundColor = selectedPreset.hex;
        }
        const previewColorLabel = document.getElementById('appearance-preview-color-label');
        if (previewColorLabel) {
            previewColorLabel.textContent = `${selectedPreset.name} (${selectedPreset.hex})`;
        }

        // 4. Render Swatches Grid
        const grid = document.getElementById('appearance-swatches-grid');
        if (grid) {
            grid.innerHTML = '';
            BACKGROUND_PRESETS.forEach(preset => {
                const isSelected = (preset.hex.toUpperCase() === selectedColor.toUpperCase());
                const isDefault = !!preset.isDefault;

                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = `appearance-swatch-btn group relative flex items-center space-x-2.5 p-2.5 rounded-xl border transition cursor-pointer text-left ${
                    isSelected 
                        ? 'border-[#4A6B5D] ring-2 ring-[#4A6B5D]/40 bg-[#F4F7F5] shadow-xs' 
                        : 'border-[#E8E4E1] hover:border-[#4A6B5D]/50 hover:bg-[#FAF9F7] bg-white'
                }`;
                btn.setAttribute('data-bg-hex', preset.hex);
                btn.setAttribute('data-bg-id', preset.id);
                btn.setAttribute('title', `${preset.name} (${preset.hex})${isDefault ? ' - Default' : ''}`);

                btn.innerHTML = `
                    <span class="w-6 h-6 rounded-full shrink-0 border border-black/10 shadow-2xs" style="background-color: ${preset.hex};"></span>
                    <div class="min-w-0 flex-1">
                        <div class="flex items-center space-x-1">
                            <span class="text-xs font-bold text-[#202124] truncate">${preset.name}</span>
                            ${isDefault ? `<span class="text-[9px] font-semibold text-[#6F6B68] bg-[#F0ECE9] px-1 py-0.2 rounded">${isVi ? 'Mặc định' : 'Default'}</span>` : ''}
                        </div>
                        <span class="text-[10px] text-[#8E8A85] font-mono block">${preset.hex}</span>
                    </div>
                    <span class="appearance-swatch-badge ${isSelected ? '' : 'hidden'} absolute -top-1.5 -right-1.5 px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-[#4A6B5D] text-white shadow-2xs">
                        ${isVi ? 'Đang chọn' : 'Selected'}
                    </span>
                `;

                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    selectColorInPreview(preset.hex);
                });

                grid.appendChild(btn);
            });
        }
    }

    /**
     * Select a color swatch (updates preview only, does not commit globally)
     */
    function selectColorInPreview(hex) {
        if (!isValidPreset(hex)) return;
        selectedColor = normalizeHex(hex);
        syncSettingsUI();
    }

    /**
     * Apply the selected preview color globally and persist
     */
    async function applySelectedColor() {
        activeColor = selectedColor;
        applyThemeToDOM(activeColor);
        syncSettingsUI();

        const uid = getCurrentUserId();
        await persistColorForUser(uid, activeColor);

        const isVi = (!window.TempoI18n || typeof window.TempoI18n.getLanguage !== 'function') 
            ? true 
            : (window.TempoI18n.getLanguage() === 'vi');

        const toastMsg = isVi 
            ? 'Đã áp dụng màu nền mới.' 
            : 'Background color applied successfully.';

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(toastMsg);
        }
    }

    /**
     * Reset background to default Mist Green (#EAEEE8)
     */
    async function resetToDefault() {
        selectedColor = DEFAULT_BG_HEX;
        activeColor = DEFAULT_BG_HEX;
        applyThemeToDOM(DEFAULT_BG_HEX);
        syncSettingsUI();

        const uid = getCurrentUserId();
        await persistColorForUser(uid, DEFAULT_BG_HEX);

        const isVi = (!window.TempoI18n || typeof window.TempoI18n.getLanguage !== 'function') 
            ? true 
            : (window.TempoI18n.getLanguage() === 'vi');

        const toastMsg = isVi 
            ? 'Đã đặt lại màu nền mặc định (#EAEEE8).' 
            : 'Reset to default background (#EAEEE8).';

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(toastMsg);
        }
    }

    /**
     * Initialize Theme controller
     */
    function init() {
        if (isInitialized) return;
        isInitialized = true;

        // Initial theme load
        const uid = getCurrentUserId();
        const saved = getSavedColorForUser(uid);
        activeColor = saved;
        selectedColor = saved;
        applyThemeToDOM(activeColor);

        // Bind Apply & Reset buttons
        const btnApply = document.getElementById('btn-appearance-apply');
        if (btnApply) {
            btnApply.addEventListener('click', (e) => {
                e.preventDefault();
                applySelectedColor();
            });
        }

        const btnReset = document.getElementById('btn-appearance-reset');
        if (btnReset) {
            btnReset.addEventListener('click', (e) => {
                e.preventDefault();
                resetToDefault();
            });
        }

        // Subscribe to i18n changes if available
        if (window.TempoI18n && typeof window.TempoI18n.subscribe === 'function') {
            window.TempoI18n.subscribe(() => {
                syncSettingsUI();
            });
        }

        syncSettingsUI();
    }

    // Public API
    window.TempoTheme = {
        init,
        getPresets: () => BACKGROUND_PRESETS.slice(),
        getDefaultColor: () => DEFAULT_BG_HEX,
        getCurrentColor: () => activeColor,
        getSelectedColor: () => selectedColor,
        setSelectedColor: selectColorInPreview,
        applySelectedColor,
        resetToDefault,
        loadUserTheme,
        ensureCurrentBackground,
        syncSettingsUI,
        onLanguageChange: () => syncSettingsUI()
    };

    // Auto-apply background immediately when script evaluates to prevent flashing
    try {
        const uid = (function() {
            try {
                const dev = localStorage.getItem('tempo_local_dev_user');
                if (dev) return JSON.parse(dev)?.id;
            } catch (e) {}
            return null;
        })();
        const initialColor = getSavedColorForUser(uid);
        activeColor = initialColor;
        selectedColor = initialColor;
        // Set CSS property immediately
        document.documentElement.style.setProperty('--tempo-bg-color', initialColor);
        document.documentElement.style.setProperty('--bg-app', initialColor);
    } catch (e) {}

    // Initialize full UI on DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
