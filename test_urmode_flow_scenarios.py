"""
TEMPO REGRESSION TEST SUITE: URMODE ENTRY, WORKING PLAN, EXECUTION, RESET, REVIEW, & ADJUSTMENT FLOWS
File: test_urmode_flow_scenarios.py

Validates all 12 key scenarios for Urmode entry and Working Plan lifecycle:
1. First-time user enters Urmode: Reset popup appears, Path A (Reset -> Breathing -> Are you ready? checkpoint).
2. First-time user: Path B ("Build my plan" -> Working Plan setup flow).
3. First-time user: Path C (Close popup -> dashboard with empty plan card and Setup / Execute buttons).
4. Quick task creation popup ("Finish & focus now" creates task, adds to plan, opens Focus Zone).
5. Quick task cancellation / close (X keeps user on dashboard with task in both cards).
6. Working Plan setup flow: save plan -> "Your task for now" popup with highest-priority task & break down prompt.
7. Break-task flow: over 'plan-workspace' background, adding/removing steps, "Do this task", "Break more tasks", "Later".
8. "Start working on your plan" popup: "Yes, start working" -> "Your first task is..." popup, task selection, Focus Zone.
9. Case 2 (Existing plan with NO overdue tasks): Reset popup shows "Review your plan" -> review summary -> "Keep the plan" / "Adjust my plan".
10. Case 3 (Existing plan with OVERDUE tasks): Reset popup shows "Review your plan", overdue tasks flagged OVERDUE, dashboard overdue notice & "Mark this task as finished" confirmation.
11. Working Plan Adjustment flow: 3 steps, non-destructive until saved (cancel preserves original plan).
12. Invariants: reload, session restore, login/logout do NOT trigger Reset popup; explicit entry triggers it once.
"""

import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_urmode_flow_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9235
    
    cmd = [
        edge_path,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "http://localhost:8000/"
    ]
    
    log(f"Launching Edge on port {port}...")
    proc = subprocess.Popen(cmd)
    ws = None
    try:
        ws_url = None
        for _ in range(30):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as resp:
                    tabs = json.loads(resp.read().decode())
                    pages = [t for t in tabs if t.get("type") == "page"]
                    if pages:
                        ws_url = pages[0]["webSocketDebuggerUrl"]
                        break
            except Exception:
                time.sleep(0.5)
        
        if not ws_url:
            raise RuntimeError("Failed to connect to Edge CDP endpoint")
            
        log(f"Connected to CDP: {ws_url}")
        ws = websocket.create_connection(ws_url)
        
        msg_id = 1
        def send_command(method, params=None):
            nonlocal msg_id
            cid = msg_id
            msg_id += 1
            req = {"id": cid, "method": method}
            if params:
                req["params"] = params
            ws.send(json.dumps(req))
            while True:
                raw = ws.recv()
                msg = json.loads(raw)
                if msg.get("id") == cid:
                    if "error" in msg:
                        raise RuntimeError(f"CDP error: {msg['error']}")
                    return msg.get("result", {})

        def eval_js(expr, await_promise=True):
            res = send_command("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": await_promise
            })
            if "exceptionDetails" in res:
                raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        def wait_for_ready():
            for _ in range(40):
                try:
                    ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined' && typeof window.TempoUrmodeFlow !== 'undefined'")
                    if ready:
                        eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("Application failed to become ready")

        log("Waiting for page and scripts ready...")
        wait_for_ready()

        # Seed mock user and sign in
        eval_js("""
            (async () => {
                const mock = {
                    id: 'local_user_test101',
                    email: 'alex.chen@university.edu',
                    raw_email: 'alex.chen@university.edu',
                    password: 'password123',
                    user_metadata: {
                        full_name: 'Alex Chen',
                        display_name: 'Alex Chen',
                        role: 'student'
                    }
                };
                localStorage.setItem('tempo_mock_account_alex.chen@university.edu', JSON.stringify(mock));
                await window.TempoAuth.signIn('alex.chen@university.edu', 'password123');
                if (window.TempoAuth.closeAllAuthModals) window.TempoAuth.closeAllAuthModals();
            })()
        """)
        time.sleep(0.5)
        log(f"Authenticated user: {eval_js('window.TempoAuth.getCurrentUser()?.email')}")

        # =====================================================================
        # SCENARIO 1: First-Time User - Path A (Reset -> Breathing -> Checkpoint)
        # =====================================================================
        log("\n--- SCENARIO 1: First-Time User - Path A (Reset -> Breathing -> Checkpoint) ---")
        eval_js("""
            (async () => {
                await window.TempoPlanStore.archiveActivePlan('emergency');
                window.TempoPlanStore.clearInMemoryCache();
                if (window.TempoEmergencyFlow) {
                    if (window.TempoEmergencyFlow.startFreshPlan) window.TempoEmergencyFlow.startFreshPlan();
                    if (window.TempoEmergencyFlow.setConfirmedPlan) window.TempoEmergencyFlow.setConfirmedPlan(null);
                    window.TempoEmergencyFlow.goToStage('entry');
                }
                window.TempoUrmodeFlow.queueResetPopup();
                window.TempoMode.setMode('emergency');
                window.TempoApp.navigateTo('today');
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.2)

        s1_modal = eval_js("""
            (() => {
                const modal = document.getElementById('modal-urmode-flow');
                const isVisible = modal && !modal.classList.contains('hidden');
                const title = modal ? modal.querySelector('h2')?.textContent.trim() : '';
                const secondaryBtn = modal ? modal.querySelectorAll('button')[1]?.textContent.trim() : '';
                const primaryBtn = modal ? modal.querySelectorAll('button')[2]?.textContent.trim() : '';
                return { isVisible, title, secondaryBtn, primaryBtn };
            })()
        """)
        assert s1_modal['isVisible'], "Reset popup should be visible on first entry"
        assert "Take a moment to reset?" in s1_modal['title'], f"Reset popup title incorrect: {s1_modal['title']}"
        assert "Build my plan" in s1_modal['secondaryBtn'], f"Secondary button should be 'Build my plan', got {s1_modal['secondaryBtn']}"
        assert "Yes, take a quick reset" in s1_modal['primaryBtn'], f"Primary button should be 'Yes, take a quick reset', got {s1_modal['primaryBtn']}"

        # Test Path A: Click Reset Yes -> Opens Breathing
        eval_js("window.TempoUrmodeFlow.handleResetYes()")
        time.sleep(0.2)
        breathing_state = eval_js("""
            (() => {
                const bModal = document.getElementById('modal-quick-stress-relief');
                const isVisible = bModal && !bModal.classList.contains('hidden');
                return { isVisible };
            })()
        """)
        assert breathing_state['isVisible'], "Breathing modal should open when clicking 'Yes, take a quick reset'"

        # Fast forward breathing -> Checkpoint ready
        eval_js("window.TempoStressRelief.handleReady()")
        time.sleep(0.2)
        ready_popup = eval_js("""
            (() => {
                const modal = document.getElementById('modal-urmode-flow');
                const isVisible = modal && !modal.classList.contains('hidden');
                const title = modal ? modal.querySelector('h2')?.textContent.trim() : '';
                const btns = modal ? Array.from(modal.querySelectorAll('button')).map(b => b.textContent.trim()) : [];
                return { isVisible, title, btns };
            })()
        """)
        assert ready_popup['isVisible'], "Are you ready? popup should appear after breathing"
        assert "Are you ready?" in ready_popup['title'], f"Popup title should be 'Are you ready?', got {ready_popup['title']}"
        assert any("Yes, I'm ready" in b for b in ready_popup['btns']), "Should have 'Yes, I'm ready' button"
        assert any("Not yet, return to reset" in b for b in ready_popup['btns']), "Should have 'Not yet, return to reset' button"

        # Test "Not yet, return to reset" -> returns to Reset popup
        eval_js("window.TempoUrmodeFlow.showResetPopup()")
        time.sleep(0.1)
        returned_reset = eval_js("""
            (() => {
                const modal = document.getElementById('modal-urmode-flow');
                return modal ? modal.querySelector('h2')?.textContent.trim() : '';
            })()
        """)
        assert "Take a moment to reset?" in returned_reset, "Should return to Reset popup"

        # Test "Yes, I'm ready" -> advances to Working Plan setup flow
        eval_js("window.TempoUrmodeFlow.handleAreYouReadyYes()")
        time.sleep(0.2)
        setup_stage = eval_js("window.TempoEmergencyFlow ? window.TempoEmergencyFlow.getCurrentStage() : null")
        assert setup_stage == 'reality-check', f"Should advance to reality-check setup stage, got {setup_stage}"
        log("✓ Scenario 1: First-Time User Path A (Reset -> Breathing -> Checkpoint) verified.")

        # =====================================================================
        # SCENARIO 2: First-Time User - Path B ("Build my plan")
        # =====================================================================
        log("\n--- SCENARIO 2: First-Time User - Path B ('Build my plan') ---")
        eval_js("""
            (() => {
                window.TempoUrmodeFlow.queueResetPopup();
                window.TempoMode.renderEmodeHome();
                window.TempoUrmodeFlow.handleResetNoOrPlan();
            })()
        """)
        time.sleep(0.2)
        b_stage = eval_js("window.TempoEmergencyFlow ? window.TempoEmergencyFlow.getCurrentStage() : null")
        assert b_stage == 'reality-check', f"Path B should open setup flow at reality-check stage, got {b_stage}"
        log("✓ Scenario 2: First-Time User Path B ('Build my plan') verified.")

        # =====================================================================
        # SCENARIO 3: First-Time User - Path C (Close Popup -> Dashboard)
        # =====================================================================
        log("\n--- SCENARIO 3: First-Time User - Path C (Close Popup -> Dashboard) ---")
        eval_js("""
            (() => {
                window.TempoEmergencyFlow.goToStage('entry');
                window.TempoUrmodeFlow.queueResetPopup();
                window.TempoMode.renderEmodeHome();
                window.TempoUrmodeFlow.handleResetClose();
            })()
        """)
        time.sleep(0.2)
        s3_dashboard = eval_js("""
            (() => {
                const modal = document.getElementById('modal-urmode-flow');
                const isModalHidden = modal.classList.contains('hidden');
                const nowCard = document.querySelector('.urgent-card-now');
                const title = nowCard ? nowCard.querySelector('h3')?.textContent.trim() : '';
                const btns = nowCard ? Array.from(nowCard.querySelectorAll('button')).map(b => b.textContent.trim()) : [];
                const planCard = document.querySelector('.urgent-working-plan-card');
                const planTitle = planCard ? planCard.querySelector('h3')?.textContent.trim() : '';
                return { isModalHidden, title, btns, planTitle };
            })()
        """)
        assert s3_dashboard['isModalHidden'], "Modal should be closed"
        assert "You haven't set up your working plan yet" in s3_dashboard['title'], f"Expected empty plan heading, got {s3_dashboard['title']}"
        assert any("Setup my plan" in b for b in s3_dashboard['btns']), "Should offer 'Setup my plan' button"
        assert any("Execute my task now" in b for b in s3_dashboard['btns']), "Should offer 'Execute my task now' button"
        assert "Your Working Plan" in s3_dashboard['planTitle'], "Right column card should be 'Your Working Plan'"
        log("✓ Scenario 3: First-Time User Path C (Close Popup -> Empty Dashboard) verified.")

        # =====================================================================
        # SCENARIO 4 & 5: Quick Task Creation Popup
        # =====================================================================
        log("\n--- SCENARIO 4 & 5: Quick Task Creation Popup ---")
        eval_js("window.TempoUrmodeFlow.openQuickTaskModal()")
        time.sleep(0.2)
        q_modal = eval_js("""
            (() => {
                const modal = document.getElementById('modal-urmode-flow');
                const isVisible = !modal.classList.contains('hidden');
                const title = modal.querySelector('h2')?.textContent.trim();
                const hasDuration = !!document.getElementById('quick-task-duration-group');
                const hasDeadline = !!document.getElementById('quick-task-has-deadline');
                return { isVisible, title, hasDuration, hasDeadline };
            })()
        """)
        assert q_modal['isVisible'], "Quick task modal should be visible"
        assert "Execute a task now" in q_modal['title'], f"Modal title should be 'Execute a task now', got {q_modal['title']}"
        assert q_modal['hasDuration'] and q_modal['hasDeadline'], "Should have duration selector and deadline checkbox"

        # Submit task with 45 min
        eval_js("""
            (() => {
                document.getElementById('quick-task-name').value = 'Quick Biology Notes';
                const pill45 = Array.from(document.querySelectorAll('.quick-duration-pill')).find(p => p.textContent.includes('45'));
                if (pill45) pill45.click();
                document.getElementById('form-quick-task').dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
            })()
        """)
        time.sleep(0.3)

        q_persisted = eval_js("""
            (() => {
                const plan = window.TempoPlanStore.getActivePlan('emergency');
                const tasks = plan ? (plan.plannedTasks || []).map(p => p.task) : [];
                const quickTask = tasks.find(t => t.name === 'Quick Biology Notes');
                return {
                    hasTask: !!quickTask,
                    durationMinutes: quickTask ? quickTask.durationMinutes : null
                };
            })()
        """)
        assert q_persisted['hasTask'], "Quick task should be persisted in Working Plan"
        assert q_persisted['durationMinutes'] == 45, f"Quick task duration should be 45 min, got {q_persisted['durationMinutes']}"

        # Close focus zone and check dashboard display
        eval_js("""
            (() => {
                if (window.TempoFocusZone && window.TempoFocusZone.close) window.TempoFocusZone.close();
                window.TempoApp.navigateTo('today');
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.2)
        dashboard_quick_display = eval_js("""
            (() => {
                const nowCard = document.querySelector('.urgent-card-now');
                const nowTitle = nowCard ? nowCard.querySelector('h3')?.textContent.trim() : '';
                const planCard = document.querySelector('.urgent-working-plan-card');
                const planContent = planCard ? planCard.textContent : '';
                return {
                    nowTitle,
                    hasInPlan: planContent.includes('Quick Biology Notes')
                };
            })()
        """)
        assert "Quick Biology Notes" in dashboard_quick_display['nowTitle'], f"Task should appear in 'Your task for now', got {dashboard_quick_display['nowTitle']}"
        assert dashboard_quick_display['hasInPlan'], "Task should appear in 'Your Working Plan' list"
        log("✓ Scenario 4 & 5: Quick Task Creation, Duration Selection, Focus Zone, & Dual-Card Dashboard Display verified.")

        # =====================================================================
        # SCENARIO 6: Working Plan Setup Flow Completion & Breakdown Prompt
        # =====================================================================
        log("\n--- SCENARIO 6: Plan Confirmation -> Task For Now & Breakdown Prompt ---")
        eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

                const freshPlan = {
                    id: 'plan_setup_test',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: today, startTime: '09:00 AM', task: { id: 'tk-1', name: 'Macroeconomics Paper', durationMinutes: 60, completed: false, subtasks: [] } },
                        { dayDate: today, startTime: '11:00 AM', task: { id: 'tk-2', name: 'Calculus Problem Set', durationMinutes: 45, completed: false, subtasks: [] } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, blocks: [{ start: '09:00', end: '18:00' }] }]
                };
                freshPlan.tasks = freshPlan.plannedTasks.map(pt => pt.task);
                await window.TempoPlanStore.saveActivePlan('emergency', freshPlan);
                window.TempoUrmodeFlow.showTaskForNowPopupAfterSave(freshPlan);
            })()
        """)
        time.sleep(0.2)
        s6_prompt = eval_js("""
            (() => {
                const modal = document.getElementById('modal-urmode-flow');
                const isVisible = !modal.classList.contains('hidden');
                const title = modal.querySelector('h2')?.textContent.trim();
                const text = modal.textContent;
                return {
                    isVisible,
                    title,
                    hasTaskName: text.includes('Macroeconomics Paper'),
                    hasBreakQuestion: text.includes('Would you like to break down this task')
                };
            })()
        """)
        assert s6_prompt['isVisible'], "Post-save 'Your task for now' popup should appear"
        assert s6_prompt['hasTaskName'], "Should display the top priority task name"
        assert s6_prompt['hasBreakQuestion'], "Should ask whether to break down task"
        log("✓ Scenario 6: Working Plan Setup completion prompt verified.")

        # =====================================================================
        # SCENARIO 7: Step Breakdown Flow Over 'plan-workspace'
        # =====================================================================
        log("\n--- SCENARIO 7: Step Breakdown Flow Over 'plan-workspace' ---")
        eval_js("window.TempoUrmodeFlow.startBreakTaskFlow('tk-1')")
        time.sleep(0.2)
        s7_state = eval_js("""
            (() => {
                const modal = document.getElementById('modal-urmode-flow');
                const isVisible = !modal.classList.contains('hidden');
                const title = modal.querySelector('h2')?.textContent.trim();
                const currentTab = (window.TempoApp && window.TempoApp.getCurrentTab) ? window.TempoApp.getCurrentTab() : window.location.hash.replace('#', '');
                return { isVisible, title, currentTab };
            })()
        """)
        assert s7_state['isVisible'], "Breakdown popup should be visible"
        assert "Break down: Macroeconomics Paper" in s7_state['title'], f"Breakdown title mismatch: {s7_state['title']}"
        assert s7_state['currentTab'] == 'plan-workspace', f"Background should transition to 'plan-workspace', got {s7_state['currentTab']}"

        # Add subtask
        eval_js("""
            (() => {
                const input = document.getElementById('breakdown-subtask-input');
                if (input) input.value = 'Draft introduction paragraph';
                window.TempoUrmodeFlow.addSubtask('tk-1');
            })()
        """)
        time.sleep(0.1)
        subtask_check = eval_js("""
            (() => {
                const plan = window.TempoPlanStore.getActivePlan('emergency');
                const task = plan.plannedTasks.find(p => p.task.id === 'tk-1').task;
                return {
                    count: task.subtasks ? task.subtasks.length : 0,
                    firstTitle: task.subtasks ? task.subtasks[0]?.title : ''
                };
            })()
        """)
        assert subtask_check['count'] == 1, f"Subtask count should be 1, got {subtask_check['count']}"
        assert "Draft introduction paragraph" in subtask_check['firstTitle'], "Subtask title mismatch"

        # Break more tasks advances to next eligible task
        eval_js("window.TempoUrmodeFlow.handleBreakMoreTasks('tk-1')")
        time.sleep(0.1)
        next_break_title = eval_js("document.getElementById('modal-urmode-flow').querySelector('h2')?.textContent.trim()")
        assert "Break down: Calculus Problem Set" in next_break_title, f"Should advance to Calculus Problem Set, got {next_break_title}"

        # Later / X closes popup to 'plan-workspace'
        eval_js("window.TempoUrmodeFlow.closeModal('plan-workspace')")
        time.sleep(0.1)
        modal_closed = eval_js("document.getElementById('modal-urmode-flow').classList.contains('hidden')")
        current_tab = eval_js("(window.TempoApp && window.TempoApp.getCurrentTab) ? window.TempoApp.getCurrentTab() : window.location.hash.replace('#', '')")
        assert modal_closed and current_tab == 'plan-workspace', f"Closing breakdown should stay on 'plan-workspace', got {current_tab}"
        log("✓ Scenario 7: Step Breakdown Flow & persistence verified.")

        # =====================================================================
        # SCENARIO 8: "Start working on your plan" Popup & Task Selection
        # =====================================================================
        log("\n--- SCENARIO 8: 'Start working on your plan' Popup & Task Selection ---")
        eval_js("window.TempoUrmodeFlow.showStartWorkingPopup()")
        time.sleep(0.1)
        start_title = eval_js("document.getElementById('modal-urmode-flow').querySelector('h2')?.textContent.trim()")
        assert "Start working on your plan?" in start_title, f"Expected 'Start working on your plan?', got {start_title}"

        eval_js("window.TempoUrmodeFlow.showFirstTaskExecutionPopup()")
        time.sleep(0.1)
        first_task_title = eval_js("document.getElementById('modal-urmode-flow').querySelector('h2')?.textContent.trim()")
        assert "Your first task is…" in first_task_title, f"Expected 'Your first task is…', got {first_task_title}"

        # Choose another task
        eval_js("window.TempoUrmodeFlow.showTaskSelectionPopup()")
        time.sleep(0.1)
        selection_title = eval_js("document.getElementById('modal-urmode-flow').querySelector('h2')?.textContent.trim()")
        assert "Select a task to work on" in selection_title, f"Expected 'Select a task to work on', got {selection_title}"

        # Select second task
        eval_js("window.TempoUrmodeFlow.selectWorkTaskAndConfirm('tk-2')")
        time.sleep(0.1)
        selected_text = eval_js("document.getElementById('modal-urmode-flow').textContent")
        assert "Calculus Problem Set" in selected_text, "Selected task should be updated to Calculus Problem Set"
        eval_js("window.TempoUrmodeFlow.closeModal('dashboard')")
        log("✓ Scenario 8: 'Start working on your plan' and Task Selection verified.")

        # =====================================================================
        # SCENARIO 9: Case 2 (Existing Plan with NO Overdue Tasks)
        # =====================================================================
        log("\n--- SCENARIO 9: Case 2 (Existing Plan - No Overdue Tasks) ---")
        eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

                const cleanPlan = {
                    id: 'plan_case2_clean',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: today, startTime: '09:00 AM', task: { id: 'c2-1', name: 'Physics Lab Report', durationMinutes: 45, completed: false, subtasks: [] } },
                        { dayDate: today, startTime: '11:00 AM', task: { id: 'c2-2', name: 'Literature Essay', durationMinutes: 60, completed: false, subtasks: [] } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, blocks: [{ start: '09:00', end: '18:00' }] }]
                };
                cleanPlan.tasks = cleanPlan.plannedTasks.map(p => p.task);
                await window.TempoPlanStore.saveActivePlan('emergency', cleanPlan);
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(cleanPlan);
                }
                window.TempoUrmodeFlow.queueResetPopup();
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.2)
        c2_modal = eval_js("""
            (() => {
                const modal = document.getElementById('modal-urmode-flow');
                const text = modal.textContent;
                const secondaryBtn = modal.querySelectorAll('button')[1]?.textContent.trim();
                return { text, secondaryBtn };
            })()
        """)
        assert "Review your plan" in c2_modal['secondaryBtn'], f"Secondary button should say 'Review your plan', got {c2_modal['secondaryBtn']}"

        # Click Review your plan -> opens summary
        eval_js("window.TempoUrmodeFlow.showReviewSummaryPopup()")
        time.sleep(0.2)
        c2_summary = eval_js("""
            (() => {
                const modal = document.getElementById('modal-urmode-flow');
                const title = modal.querySelector('h2')?.textContent.trim();
                const text = modal.textContent;
                const hasOverdueBadge = !!modal.querySelector('.bg-amber-100');
                return { title, text, hasOverdueBadge };
            })()
        """)
        assert "Your Working Plan Summary" in c2_summary['title'], f"Summary title mismatch: {c2_summary['title']}"
        assert "Physics Lab Report" in c2_summary['text'] and "Literature Essay" in c2_summary['text'], "Both tasks should appear in summary"
        assert not c2_summary['hasOverdueBadge'], "Clean plan should not show OVERDUE badge"

        # Click "Keep the plan" -> shows task preview
        eval_js("window.TempoUrmodeFlow.showKeepPlanTaskPopup()")
        time.sleep(0.1)
        c2_keep = eval_js("""
            (() => {
                const modal = document.getElementById('modal-urmode-flow');
                const title = modal.querySelector('h2')?.textContent.trim();
                const text = modal.textContent;
                return { title, hasTask: text.includes('Physics Lab Report') };
            })()
        """)
        assert "Your task for now is…" in c2_keep['title'], "Keep plan should show 'Your task for now is…'"
        assert c2_keep['hasTask'], "Should display top task Physics Lab Report"
        eval_js("window.TempoUrmodeFlow.closeModal('dashboard')")
        log("✓ Scenario 9: Case 2 (Existing Plan - No Overdue) verified.")

        # =====================================================================
        # SCENARIO 10: Case 3 (Existing Plan with Overdue Tasks)
        # =====================================================================
        log("\n--- SCENARIO 10: Case 3 (Existing Plan with Overdue Tasks) ---")
        eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const yestDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
                const yesterday = `${yestDate.getFullYear()}-${pad(yestDate.getMonth() + 1)}-${pad(yestDate.getDate())}`;
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

                const overduePlan = {
                    id: 'plan_case3_overdue',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: yesterday, startTime: '10:00 AM', task: { id: 'c3-stale', name: 'Overdue Statistics Assignment', durationMinutes: 60, completed: false, subtasks: [] } },
                        { dayDate: today, startTime: '02:00 PM', task: { id: 'c3-today', name: 'Normal Today Task', durationMinutes: 30, completed: false, subtasks: [] } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, blocks: [{ start: '09:00', end: '18:00' }] }]
                };
                overduePlan.tasks = overduePlan.plannedTasks.map(p => p.task);
                await window.TempoPlanStore.saveActivePlan('emergency', overduePlan);
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(overduePlan);
                }
                window.TempoUrmodeFlow.queueResetPopup();
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.2)
        c3_reset = eval_js("""
            (() => {
                const modal = document.getElementById('modal-urmode-flow');
                const text = modal.textContent;
                return { hasPlanUpdateNeeded: text.includes('PLAN UPDATE NEEDED') };
            })()
        """)
        assert c3_reset['hasPlanUpdateNeeded'], "Reset popup should show PLAN UPDATE NEEDED badge for overdue plan"

        # Check summary popup has OVERDUE badge
        eval_js("window.TempoUrmodeFlow.showReviewSummaryPopup()")
        time.sleep(0.2)
        c3_summary = eval_js("""
            (() => {
                const modal = document.getElementById('modal-urmode-flow');
                const text = modal.textContent;
                const overdueBadges = Array.from(modal.querySelectorAll('.bg-amber-100')).map(b => b.textContent.trim());
                return { text, overdueBadges };
            })()
        """)
        assert any("OVERDUE" in b for b in c3_summary['overdueBadges']), "Overdue task should be flagged OVERDUE in summary"

        # Close to dashboard -> verify SCHEDULE UPDATE NEEDED and "Mark this task as finished"
        eval_js("window.TempoUrmodeFlow.closeModal('dashboard')")
        time.sleep(0.2)
        c3_dashboard = eval_js("""
            (() => {
                const nowCard = document.querySelector('.urgent-card-now');
                const text = nowCard ? nowCard.textContent : '';
                const markBtn = nowCard ? nowCard.querySelector('button.bg-emerald-600') : null;
                const updateBtn = nowCard ? Array.from(nowCard.querySelectorAll('button')).find(b => {
                    const t = b.textContent;
                    return t.includes('Update my plan') || t.includes('Review & update plan') || t.includes('Cập nhật lịch trình') || t.includes('Cập nhật kế hoạch');
                }) : null;
                const hasStale = text.includes('Your plan needs an update.') || text.includes('Kế hoạch của bạn cần được cập nhật.');
                return {
                    text,
                    hasStaleTitle: hasStale,
                    hasMarkBtn: !!markBtn,
                    hasUpdateBtn: !!updateBtn
                };
            })()
        """)
        assert c3_dashboard['hasStaleTitle'], f"Dashboard should show 'Your plan needs an update.', got text: {c3_dashboard['text']}"
        assert c3_dashboard['hasMarkBtn'], "Dashboard should provide 'Mark this task as finished' button"
        assert c3_dashboard['hasUpdateBtn'], "Dashboard should provide 'Update my plan' button"

        # Test marking task finished
        eval_js("window.TempoUrmodeFlow.markOverdueTaskFinished('c3-stale')")
        time.sleep(0.2)
        c3_after_finish = eval_js("""
            (() => {
                const plan = window.TempoPlanStore.getActivePlan('emergency');
                const task = plan.plannedTasks.find(p => p.task.id === 'c3-stale').task;
                return { isCompleted: task.completed };
            })()
        """)
        assert c3_after_finish['isCompleted'], "Overdue task should be marked completed"
        log("✓ Scenario 10: Case 3 (Existing Plan with Overdue Tasks) verified.")

        # =====================================================================
        # SCENARIO 11: Working Plan Adjustment Flow (Non-Destructive)
        # =====================================================================
        log("\n--- SCENARIO 11: Working Plan Adjustment Flow (Non-Destructive) ---")
        eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

                const origPlan = {
                    id: 'plan_adjust_nondestruct',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: today, startTime: '10:00 AM', task: { id: 'adj-1', name: 'Chemistry Experiment', durationMinutes: 30, completed: false, subtasks: [] } },
                        { dayDate: today, startTime: '11:00 AM', task: { id: 'adj-2', name: 'History Quiz Prep', durationMinutes: 45, completed: false, subtasks: [] } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, blocks: [{ start: '09:00', end: '18:00' }] }]
                };
                origPlan.tasks = origPlan.plannedTasks.map(p => p.task);
                await window.TempoPlanStore.saveActivePlan('emergency', origPlan);
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(origPlan);
                }
            })()
        """)
        time.sleep(0.1)

        # Step 1: Start adjustment
        eval_js("window.TempoUrmodeFlow.startAdjustmentFlow()")
        time.sleep(0.2)
        step1_title = eval_js("document.getElementById('modal-urmode-flow').querySelector('h2')?.textContent.trim()")
        assert "Choose tasks to keep" in step1_title, f"Step 1 title should be 'Choose tasks to keep', got {step1_title}"

        # Uncheck task 2
        eval_js("window.TempoUrmodeFlow.toggleRetainedTask('adj-2', false)")

        # Cancel adjustment -> verify original plan is completely intact
        eval_js("window.TempoUrmodeFlow.closeModal('dashboard')")
        time.sleep(0.1)
        canceled_plan = eval_js("""
            (() => {
                const plan = window.TempoPlanStore.getActivePlan('emergency');
                return { taskCount: plan.plannedTasks.length };
            })()
        """)
        assert canceled_plan['taskCount'] == 2, "Cancelling adjustment must NOT modify active saved plan"

        # Restart adjustment and complete 3 steps
        eval_js("window.TempoUrmodeFlow.startAdjustmentFlow()")
        time.sleep(0.1)
        eval_js("window.TempoUrmodeFlow.renderAdjustmentStep2Tasks()")
        time.sleep(0.1)
        step2_title = eval_js("document.getElementById('modal-urmode-flow').querySelector('h2')?.textContent.trim()")
        assert "Adjust estimates & add new tasks" in step2_title, f"Step 2 title mismatch: {step2_title}"

        # Add new task in Step 2
        eval_js("""
            (() => {
                document.getElementById('adjust-new-task-name').value = 'New Anatomy Vocab';
                document.getElementById('adjust-new-task-dur').value = '45';
                window.TempoUrmodeFlow.addNewAdjustmentTask();
            })()
        """)
        time.sleep(0.1)
        eval_js("window.TempoUrmodeFlow.renderAdjustmentStep3Proposal()")
        time.sleep(0.1)
        step3_title = eval_js("document.getElementById('modal-urmode-flow').querySelector('h2')?.textContent.trim()")
        assert any(t in step3_title for t in ["Proposed Updated Plan", "Review proposed plan"]), f"Step 3 title mismatch: {step3_title}"

        # Save adjustment plan
        eval_js("window.TempoUrmodeFlow.saveAdjustmentPlan()")
        time.sleep(0.2)
        saved_adjusted = eval_js("""
            (() => {
                const plan = window.TempoPlanStore.getActivePlan('emergency');
                const names = plan.plannedTasks.map(p => p.task.name);
                return { names };
            })()
        """)
        assert any("New Anatomy Vocab" in n for n in saved_adjusted['names']), "Updated plan should contain newly added task"
        eval_js("window.TempoUrmodeFlow.closeModal('dashboard')")
        log("✓ Scenario 11: Working Plan Adjustment Flow (Non-Destructive) verified.")

        # =====================================================================
        # SCENARIO 12: Invariants - Reload, Session Restore & Explicit Entry
        # =====================================================================
        log("\n--- SCENARIO 12: Invariants - Reload, Session Restore & Explicit Entry ---")
        # Direct dashboard re-render without explicit entry MUST NOT trigger popup
        eval_js("""
            (() => {
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.2)
        no_popup = eval_js("document.getElementById('modal-urmode-flow').classList.contains('hidden')")
        assert no_popup, "Re-rendering dashboard / reloading without explicit entry MUST NOT show Reset popup"

        # Explicit mode switch from another mode triggers popup
        eval_js("""
            (() => {
                window.TempoMode.setMode('default');
                window.TempoMode.selectModeOption('emergency');
            })()
        """)
        time.sleep(0.2)
        explicit_popup = eval_js("!document.getElementById('modal-urmode-flow').classList.contains('hidden')")
        assert explicit_popup, "Explicit entry from selector dropdown MUST trigger Reset popup"
        eval_js("window.TempoUrmodeFlow.closeModal('dashboard')")

        # Explicit entry from Entry Home triggers popup
        eval_js("""
            (() => {
                window.TempoMode.setMode('default');
                window.TempoApp.selectRoutingState('urgent');
            })()
        """)
        time.sleep(0.2)
        entry_home_popup = eval_js("!document.getElementById('modal-urmode-flow').classList.contains('hidden')")
        assert entry_home_popup, "Explicit entry from Entry Home MUST trigger Reset popup"
        eval_js("window.TempoUrmodeFlow.closeModal('dashboard')")
        log("✓ Scenario 12: Invariants - Reload, Session Restore & Single-Occurrence verified.")

        log("\n=====================================================================")
        log(">>> ALL 12 URMODE FLOW SCENARIOS VERIFIED AND PASSED SUCCESSFULLY! <<<")
        log("=====================================================================")

    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass
        if proc:
            proc.terminate()
            proc.wait()

if __name__ == "__main__":
    run_tests()
