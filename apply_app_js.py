# -*- coding: utf-8 -*-
import sys

def update_app_js():
    with open('app.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update Wplan navigation in navigateTo
    old_wplan_block = """        // Shared Authenticated Tool: Wplan (Working Plan)
        const isWplan = (tabId === 'plan-workspace' || tabId === 'tool-workplan' || tabId === 'workplan');
        if (isWplan && (!window.TempoAuth || !window.TempoAuth.getCurrentUser())) {
            const src = window.TempoMode && window.TempoMode.getSourceContext ? window.TempoMode.getSourceContext() : 'entry';
            if (window.TempoMode && typeof window.TempoMode.setPendingIntent === 'function') {
                window.TempoMode.setPendingIntent({
                    destination: 'tool-workplan',
                    action: 'navigate',
                    source: src,
                    requiredParams: subTab ? { taskId: subTab } : {},
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
        }"""

    new_wplan_block = """        // Shared Authenticated Tool: Wplan (Working Plan)
        const isWplan = (tabId === 'plan-workspace' || tabId === 'tool-workplan' || tabId === 'workplan');
        if (isWplan) {
            // Allow navigation to standalone Working Plan tool for both authenticated and guest users.
            // If user is guest/unauthenticated, preserve pending intent for seamless sign-in later if desired,
            // but DO NOT block the tool view. The tool itself displays the clean empty state or user's active session tasks.
            const currentUser = window.TempoAuth ? window.TempoAuth.getCurrentUser() : null;
            if (!currentUser) {
                const src = window.TempoMode && window.TempoMode.getSourceContext ? window.TempoMode.getSourceContext() : 'entry';
                if (window.TempoMode && typeof window.TempoMode.setPendingIntent === 'function') {
                    window.TempoMode.setPendingIntent({
                        destination: 'tool-workplan',
                        action: 'navigate',
                        source: src,
                        requiredParams: subTab ? { taskId: subTab } : {},
                        type: 'tool',
                        tool: 'plan-workspace',
                        sourceContext: src
                    });
                }
            }
        }"""

    assert old_wplan_block in content, "old_wplan_block not found in app.js"
    content = content.replace(old_wplan_block, new_wplan_block)

    # 2. Update desktop nav active state matching
    old_nav_active = """        // Update desktop nav item active states
        document.querySelectorAll('header nav a[data-nav]').forEach(el => {
            const isMatch = el.dataset.nav === tabId;"""

    new_nav_active = """        // Update desktop nav item active states
        document.querySelectorAll('header nav a[data-nav]').forEach(el => {
            const isMatch = el.dataset.nav === tabId ||
                            (el.dataset.nav === 'plan-workspace' && (tabId === 'plan-workspace' || tabId === 'tool-workplan' || tabId === 'workplan')) ||
                            (el.dataset.nav === 'stress-check' && (tabId === 'stress-check' || tabId === 'strack'));"""

    assert old_nav_active in content, "old_nav_active not found in app.js"
    content = content.replace(old_nav_active, new_nav_active)

    # 3. Update scrollToRecoveryPlan to only target recovery-working-plan
    old_scroll_rec = """    function scrollToRecoveryPlan() {
        const doScroll = () => {
            const el = document.getElementById('recovery-working-plan')
                || document.querySelector('[data-tempo-ui="recovery-working-plan"]')
                || Array.from(document.querySelectorAll('h3, h2')).find(h => (h.textContent || '').includes('Your Working Plan'));
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        };"""

    new_scroll_rec = """    function scrollToRecoveryPlan() {
        const doScroll = () => {
            const el = document.getElementById('recovery-working-plan')
                || document.querySelector('[data-tempo-ui="recovery-working-plan"]');
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        };"""

    assert old_scroll_rec in content, "old_scroll_rec not found in app.js"
    content = content.replace(old_scroll_rec, new_scroll_rec)

    with open('app.js', 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print("app.js updated successfully with LF.")

if __name__ == '__main__':
    update_app_js()
