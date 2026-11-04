# -*- coding: utf-8 -*-
import sys

def update_plan_workspace():
    with open('planWorkspace.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Guard weekday in applyRecurringRulesToPlan
    old_rule = """        rules.forEach(rule => {
            if (!rule.startDate) return;"""
    new_rule = """        rules.forEach(rule => {
            if (!rule.startDate || typeof rule.weekday !== 'number') return;"""
    assert old_rule in content, "old_rule not found"
    content = content.replace(old_rule, new_rule, 1)

    # 2. Update getActivePlan ownership assignment
    old_owner = """        if (plan) {
            if (isAuthenticated) {
                if (plan.userId && plan.userId !== currentUserId) return null;
                if (plan.user_id && plan.user_id !== currentUserId) return null;
                if (!plan.userId && !plan.user_id) return null;
            }"""
    new_owner = """        if (plan) {
            if (isAuthenticated) {
                if (plan.userId && plan.userId !== currentUserId) return null;
                if (plan.user_id && plan.user_id !== currentUserId) return null;
                // If plan exists in current in-memory flow/session without stamped id, associate it with current user
                if (!plan.userId && !plan.user_id) {
                    plan.userId = currentUserId;
                    plan.user_id = currentUserId;
                }
            } else {
                if (plan.userId && plan.userId !== 'guest') return null;
                if (plan.user_id && plan.user_id !== 'guest') return null;
            }"""
    assert old_owner in content, "old_owner not found"
    content = content.replace(old_owner, new_owner, 1)

    # 3. Update open() to explicitly ensure screen container is unhidden
    old_open = """    function open() {
        resetWorkspaceState();
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('plan-workspace');
        } else {
            window.location.hash = '#plan-workspace';
        }
        const plan = getActivePlan();
        if (plan) {
            const changed = cleanupExpiredAvailability(plan);
            if (changed) {
                persistPlan(plan);
            }
        }
        render();
    }"""
    new_open = """    function open() {
        resetWorkspaceState();
        const wsScreen = document.getElementById('screen-plan-workspace');
        if (wsScreen) {
            document.querySelectorAll('.screen-container').forEach(s => s.classList.add('hidden'));
            wsScreen.classList.remove('hidden');
        }
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('plan-workspace');
        } else {
            window.location.hash = '#plan-workspace';
        }
        const plan = getActivePlan();
        if (plan) {
            const changed = cleanupExpiredAvailability(plan);
            if (changed) {
                persistPlan(plan);
            }
        }
        render();
    }"""
    assert old_open in content, "old_open not found"
    content = content.replace(old_open, new_open, 1)

    # 4. Update render() to only enforce background when viewing the actual Plan Workspace
    old_render_start = """    function render() {
        const root = document.getElementById('plan-workspace-root');
        if (!root) return;

        // Ensure light blue background on body and main
        document.body.style.backgroundColor = '#EFFAFF';
        const mainEl = document.querySelector('main');
        if (mainEl) mainEl.style.backgroundColor = '#EFFAFF';"""
    new_render_start = """    function render() {
        const root = document.getElementById('plan-workspace-root');
        if (!root) return;

        const wsScreen = document.getElementById('screen-plan-workspace');
        const isPlanRoute = window.location.hash.includes('plan-workspace') || window.location.hash.includes('workplan');
        const isScreenVisible = wsScreen && !wsScreen.classList.contains('hidden');

        // Only enforce blue background when viewing the actual Plan Workspace
        if (isPlanRoute || isScreenVisible) {
            if (wsScreen && wsScreen.classList.contains('hidden')) {
                document.querySelectorAll('.screen-container').forEach(s => s.classList.add('hidden'));
                wsScreen.classList.remove('hidden');
            }
            document.body.style.backgroundColor = '#EFFAFF';
            const mainEl = document.querySelector('main');
            if (mainEl) mainEl.style.backgroundColor = '#EFFAFF';
        }"""
    assert old_render_start in content, "old_render_start not found"
    content = content.replace(old_render_start, new_render_start, 1)

    # 5. Contextual Return Home Button
    old_back_btn = """                <!-- Top-Left Navigation Control -->
                <div class="flex items-center justify-between">
                    <button id="plan-workspace-back-home"
                            type="button"
                            onclick="window.TempoPlanWorkspace.navigateHome()" 
                            class="text-xs sm:text-sm font-semibold text-[#6F6B68] hover:text-[#202124] flex items-center space-x-1.5 transition py-1 cursor-pointer group"
                            title="${isViLocale() ? '← Về trang chủ' : 'Return Home'}">
                        <span class="group-hover:-translate-x-0.5 transition-transform">←</span>
                        <span>${isViLocale() ? 'Về trang chủ' : 'Return Home'}</span>
                    </button>
                </div>"""
    new_back_btn = """                <!-- Top-Left Navigation Control -->
                <div class="flex items-center justify-between">
                    <button id="plan-workspace-back-home"
                            type="button"
                            onclick="window.TempoPlanWorkspace.navigateHome()" 
                            class="text-xs sm:text-sm font-semibold text-[#6F6B68] hover:text-[#202124] flex items-center space-x-1.5 transition py-1 cursor-pointer group"
                            title="${(window.TempoMode && window.TempoMode.getMode() === 'emergency') ? (isViLocale() ? 'Quay lại URmode' : 'Return to URmode') : (isViLocale() ? 'Về trang chủ' : 'Return Home')}">
                        <span class="group-hover:-translate-x-0.5 transition-transform">←</span>
                        <span>${(window.TempoMode && window.TempoMode.getMode() === 'emergency') ? (isViLocale() ? 'Quay lại URmode' : 'Return to URmode') : (isViLocale() ? 'Về trang chủ' : 'Return Home')}</span>
                    </button>
                </div>"""
    assert old_back_btn in content, "old_back_btn not found"
    content = content.replace(old_back_btn, new_back_btn, 1)

    with open('planWorkspace.js', 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print("planWorkspace.js updated successfully with LF.")

if __name__ == '__main__':
    update_plan_workspace()
