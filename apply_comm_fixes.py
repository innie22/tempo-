import sys
sys.stdout.reconfigure(encoding='utf-8')

# 1. Update communityPosts.js
with open('communityPosts.js', 'r', encoding='utf-8', newline='') as f:
    comm_content = f.read()

# Replace updateReturnButton & handleReturnNavigation
old_comm_return = """    function updateReturnButton() {
        const backLabel = document.getElementById('community-back-label');
        if (!backLabel) return;

        const sourceContext = (window.TempoMode && typeof window.TempoMode.getSourceContext === 'function')
            ? window.TempoMode.getSourceContext()
            : null;
        const currentMode = (window.TempoMode && typeof window.TempoMode.getActiveContext === 'function' && window.TempoMode.getActiveContext())
            || (window.TempoMode && typeof window.TempoMode.getMode === 'function' ? window.TempoMode.getMode() : null);

        if (sourceContext === 'recovery' || (!sourceContext && currentMode === 'recovery')) {
            backLabel.textContent = 'Return to Recovery Mode';
        } else if (sourceContext === 'emergency' || (!sourceContext && currentMode === 'emergency')) {
            backLabel.textContent = 'Return to Emergency Support';
        } else {
            backLabel.textContent = 'Return Home';
        }
    }

    function handleReturnNavigation() {
        const sourceContext = (window.TempoMode && typeof window.TempoMode.getSourceContext === 'function')
            ? window.TempoMode.getSourceContext()
            : null;
        const currentMode = (window.TempoMode && typeof window.TempoMode.getActiveContext === 'function' && window.TempoMode.getActiveContext())
            || (window.TempoMode && typeof window.TempoMode.getMode === 'function' ? window.TempoMode.getMode() : null);

        if (sourceContext === 'recovery' || (!sourceContext && currentMode === 'recovery')) {
            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
                window.TempoMode.setMode('recovery');
            }
            if (window.TempoMode && typeof window.TempoMode.navigateToActiveDashboard === 'function') {
                window.TempoMode.navigateToActiveDashboard();
            } else if (window.TempoApp) {
                window.TempoApp.navigateTo('recovery-mode');
            }
        } else if (sourceContext === 'emergency' || (!sourceContext && currentMode === 'emergency')) {
            if (window.TempoApp) window.TempoApp.navigateTo('emergency');
        } else {
            if (window.TempoApp) window.TempoApp.navigateTo('today');
        }
    }"""

new_comm_return = """    function updateReturnButton() {
        const backBtn = document.getElementById('btn-community-back');
        const backLabel = document.getElementById('community-back-label');
        if (!backLabel) return;

        const isVi = isViLocale();
        const textLabel = isVi ? 'Về Dashboard' : 'Return to Dashboard';
        const fullLabel = isVi ? '← Về Dashboard' : '← Return to Dashboard';

        backLabel.textContent = textLabel;

        if (backBtn) {
            backBtn.setAttribute('title', fullLabel);
            backBtn.setAttribute('aria-label', fullLabel);
        }
    }

    function handleReturnNavigation() {
        if (window.TempoCommunity && typeof window.TempoCommunity.closeCommunityModal === 'function') {
            window.TempoCommunity.closeCommunityModal();
        }
        if (window.TempoMode && typeof window.TempoMode.navigateToActiveDashboard === 'function') {
            window.TempoMode.navigateToActiveDashboard();
        } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('today');
        } else {
            window.location.hash = '#today';
        }
    }"""

# Check CRLF matching
old_comm_return_crlf = old_comm_return.replace('\n', '\r\n')
new_comm_return_crlf = new_comm_return.replace('\n', '\r\n')

assert old_comm_return_crlf in comm_content, "old_comm_return_crlf not found in communityPosts.js"
comm_content = comm_content.replace(old_comm_return_crlf, new_comm_return_crlf, 1)

# In init() add updateReturnButton()
old_init_target = """        renderRecoveryPreview();\r\n        bindEvents();"""
new_init_target = """        renderRecoveryPreview();\r\n        updateReturnButton();\r\n        bindEvents();"""
assert old_init_target in comm_content, "old_init_target not found in communityPosts.js"
comm_content = comm_content.replace(old_init_target, new_init_target, 1)

# In onLanguageChange add updateReturnButton()
old_on_lang = """        window.TempoI18n.onLanguageChange(() => {\r\n            renderUrgentPreview();"""
new_on_lang = """        window.TempoI18n.onLanguageChange(() => {\r\n            updateReturnButton();\r\n            renderUrgentPreview();"""
assert old_on_lang in comm_content, "old_on_lang not found in communityPosts.js"
comm_content = comm_content.replace(old_on_lang, new_on_lang, 1)

# In public API add updateReturnButton
old_public_api = """        selectTab,\r\n        handleReturnNavigation,"""
new_public_api = """        selectTab,\r\n        handleReturnNavigation,\r\n        updateReturnButton,"""
assert old_public_api in comm_content, "old_public_api not found in communityPosts.js"
comm_content = comm_content.replace(old_public_api, new_public_api, 1)

with open('communityPosts.js', 'w', encoding='utf-8', newline='') as f:
    f.write(comm_content)

print("communityPosts.js updated successfully.")
