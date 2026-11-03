with open('unclearMode.js', 'rb') as f:
    raw = f.read()

# Normalize to \n for replacement
text = raw.decode('utf-8').replace('\r\n', '\n')

target1 = """        const incompleteDrafts = getIncompleteVersions();
        const hasUnfinishedDraft = incompleteDrafts.length > 0;
        const draft = incompleteDrafts[0] || null;
        const history = loadCompletedHistory();
        const lastCheckin = history.length > 0 ? history[0] : null;

        container.innerHTML = `
            <div id="unclear-home-view" class="space-y-6">
                <!-- Main Content Area: Two-Column Layout -->"""

replacement1 = """        const incompleteDrafts = getIncompleteVersions();
        const hasUnfinishedDraft = incompleteDrafts.length > 0;
        const draft = incompleteDrafts[0] || null;
        const history = loadCompletedHistory();
        const lastCheckin = history.length > 0 ? history[0] : null;

        const isVi = (window.TempoI18n && typeof window.TempoI18n.getLanguage === 'function') ? (window.TempoI18n.getLanguage() === 'vi') : false;
        const activeCtx = (window.TempoMode && typeof window.TempoMode.getActiveContext === 'function') ? window.TempoMode.getActiveContext() : null;
        const backBtnText = isVi ? 'Quay lại Dashboard' : 'Back to Dashboard';
        const backBtnTitle = activeCtx === 'recovery'
            ? (isVi ? 'Quay lại Recovery Mode Dashboard' : 'Back to Recovery Mode Dashboard')
            : (activeCtx === 'emergency'
                ? (isVi ? 'Quay lại Urgent Mode Dashboard' : 'Back to Urgent Mode Dashboard')
                : (isVi ? 'Quay lại Dashboard' : 'Back to Dashboard'));

        container.innerHTML = `
            <div id="unclear-home-view" class="space-y-6">
                <!-- Top Utility Bar: Back to Dashboard -->
                <div class="flex items-center justify-between pb-1" data-tempo-ui="ucheck-header-bar">
                    <button type="button" 
                            id="btn-ucheck-back-to-dashboard"
                            data-tempo-action="back-to-dashboard"
                            onclick="if (window.TempoMode && typeof window.TempoMode.navigateToActiveDashboard === 'function') { window.TempoMode.navigateToActiveDashboard(); } else if (window.TempoApp) { window.TempoApp.navigateTo('today'); }"
                            class="inline-flex items-center space-x-1.5 px-4 py-2 rounded-full text-xs sm:text-sm font-bold text-[#5B5550] hover:text-[#202124] bg-white hover:bg-stone-50 border border-[#E8D9CF] transition shadow-xs cursor-pointer"
                            title="${backBtnTitle}">
                        <span>←</span>
                        <span>${backBtnText}</span>
                    </button>
                </div>

                <!-- Main Content Area: Two-Column Layout -->"""

assert target1 in text, "target1 not found in unclearMode.js"
text = text.replace(target1, replacement1, 1)

target2 = """    function returnToHome() {
        const uid = getUserId();
        sessionStorage.removeItem(`tempo_unclear_in_flow_${uid}`);
        if (window.TempoMode && typeof window.TempoMode.returnToSourceContext === 'function') {
            window.TempoMode.returnToSourceContext();
        } else if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
            window.TempoMode.setMode('default');
        } else {
            viewState = 'home';
            renderHome();
        }
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('today');
        }
    }"""

replacement2 = """    function returnToHome() {
        const uid = getUserId();
        sessionStorage.removeItem(`tempo_unclear_in_flow_${uid}`);
        if (window.TempoMode && typeof window.TempoMode.navigateToActiveDashboard === 'function') {
            window.TempoMode.navigateToActiveDashboard();
        } else if (window.TempoMode && typeof window.TempoMode.returnToSourceContext === 'function') {
            window.TempoMode.returnToSourceContext();
        } else if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
            window.TempoMode.setMode('default');
        } else {
            viewState = 'home';
            renderHome();
        }
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('today');
        }
    }"""

assert target2 in text, "target2 not found in unclearMode.js"
text = text.replace(target2, replacement2, 1)

# Ensure strictly CRLF
text_crlf = text.replace('\n', '\r\n')

with open('unclearMode.js', 'wb') as f:
    f.write(text_crlf.encode('utf-8'))

print("Successfully updated unclearMode.js with CRLF")
