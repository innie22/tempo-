import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_default_home_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9285
    
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
    passed_checks = 0
    total_checks = 0

    def assert_check(desc, condition):
        nonlocal passed_checks, total_checks
        total_checks += 1
        if condition:
            passed_checks += 1
            log(f"  [PASS] {desc}")
        else:
            log(f"  [FAIL] {desc}")

    try:
        ws_url = None
        for _ in range(30):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as resp:
                    tabs = json.loads(resp.read().decode())
                    pages = [t for t in tabs if t.get("type") == "page" and "localhost:8000" in t.get("url", "")]
                    if pages:
                        ws_url = pages[0]["webSocketDebuggerUrl"]
                        break
            except Exception:
                time.sleep(0.5)
        
        if not ws_url:
            raise RuntimeError("Failed to connect to Edge CDP endpoint for localhost:8000")
            
        log(f"Connected to CDP page: {ws_url}")
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
                resp = json.loads(ws.recv())
                if resp.get("id") == cid:
                    return resp.get("result", {})

        def eval_js(expr):
            res = send_command("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
            if "exceptionDetails" in res:
                log(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        # Allow app to fully initialize
        time.sleep(2)
        log("Resetting to clean default state...")

        eval_js("""(() => {
            localStorage.clear();
            if (window.TempoPlanStore) window.TempoPlanStore.saveActivePlan('emergency', null);
            if (window.TempoMode) {
                window.TempoMode.setMode('default', { silent: true });
                window.TempoMode.renderActiveModeHome();
            }
        })()""")
        time.sleep(1)

        log("\n--- TEST SUITE 1: ANONYMOUS / EMPTY STATE (State F) ---")
        current_mode = eval_js("window.TempoMode.getMode()")
        assert_check("Default mode is active", current_mode == "default")

        # Check mutual exclusivity
        dmode_hidden = eval_js("document.getElementById('dmode-home-content').classList.contains('hidden')")
        emode_hidden = eval_js("document.getElementById('emode-home-content').classList.contains('hidden')")
        rmode_hidden = eval_js("document.getElementById('rmode-home-content').classList.contains('hidden')")
        umode_hidden = eval_js("document.getElementById('umode-home-content').classList.contains('hidden')")
        assert_check("dmode-home-content is VISIBLE", dmode_hidden is False)
        assert_check("emode-home-content is HIDDEN", emode_hidden is True)
        assert_check("rmode-home-content is HIDDEN", rmode_hidden is True)
        assert_check("umode-home-content is HIDDEN", umode_hidden is True)

        # Check greeting and no "Default Mode" label
        dmode_html = eval_js("document.getElementById('dmode-home-content').innerHTML")
        assert_check("Greeting is safe fallback 'Hi there 👋'", "Hi there" in dmode_html)
        assert_check("No 'Default Mode' label in dmode content", "Default Mode" not in dmode_html)
        mode_badge_hidden = eval_js("document.getElementById('mode-indicator-shell').classList.contains('hidden')")
        assert_check("Mode badge shell is hidden on Default Home", mode_badge_hidden is True)

        # Your Day empty state
        assert_check("Your Day section exists", "Your Day" in dmode_html)
        assert_check("Your Day empty copy 'Nothing planned yet.'", "Nothing planned yet." in dmode_html)
        assert_check("View my plan CTA exists", "View my plan" in dmode_html)

        # Tools: Focus Zone & Quick Relief
        assert_check("Focus Zone card present with copy", "Settle into one thing at a time." in dmode_html)
        assert_check("Quick Relief card present with copy", "Take a short moment to reset." in dmode_html)

        # Self-check empty state (STATE_A)
        assert_check("Self-check empty copy 'Keep an eye on the things that matter to you over time.'", "Keep an eye on the things that matter to you over time." in dmode_html)
        assert_check("Set up my Self-check CTA present", "Set up my Self-check" in dmode_html)
        assert_check("No aggregate wellbeing score/percentage", "% wellbeing" not in dmode_html and "Good score" not in dmode_html)

        # Tempo Posts
        assert_check("Tempo Posts header present", "Tempo Posts" in dmode_html)
        assert_check("No article read times or magazine layout", "min read" not in dmode_html and "[STUDY TIPS]" not in dmode_html)
        posts_count = eval_js("document.querySelectorAll('#homepage-community-posts-list > *').length")
        assert_check(f"1-2 social peer posts previewed (got {posts_count})", 1 <= (posts_count or 0) <= 2)

        log("\n--- TEST SUITE 2: SHARED TASKS CONTINUITY (State A) ---")
        # Seed shared plan directly via TempoPlanStore using IIFE
        eval_js("""(() => {
            const todayISO = new Date().toISOString().split('T')[0];
            const samplePlan = {
                id: 'plan_shared_test_1',
                tasks: [
                    { id: 'task_1', name: 'Marketing report', durationMinutes: 45, completed: false, isInProgress: true, subtasks: [
                        { id: 'sub_1_1', title: 'Review guidelines', completed: true },
                        { id: 'sub_1_2', title: 'Draft executive summary', completed: false }
                    ]},
                    { id: 'task_2', name: 'Review presentation', durationMinutes: 30, completed: false, isInProgress: false, subtasks: [] },
                    { id: 'task_3', name: 'MAS reading', durationMinutes: 20, completed: false, isInProgress: false, subtasks: [] }
                ],
                plannedTasks: [
                    { dayDate: todayISO, dayLabel: 'TODAY', task: { id: 'task_1', name: 'Marketing report', durationMinutes: 45, completed: false, isInProgress: true, subtasks: [
                        { id: 'sub_1_1', title: 'Review guidelines', completed: true },
                        { id: 'sub_1_2', title: 'Draft executive summary', completed: false }
                    ]}, scheduledStartTime: '09:00', scheduledEndTime: '09:45' },
                    { dayDate: todayISO, dayLabel: 'TODAY', task: { id: 'task_2', name: 'Review presentation', durationMinutes: 30, completed: false, isInProgress: false, subtasks: [] }, scheduledStartTime: '14:30', scheduledEndTime: '15:00' },
                    { dayDate: todayISO, dayLabel: 'TODAY', task: { id: 'task_3', name: 'MAS reading', durationMinutes: 20, completed: false, isInProgress: false, subtasks: [] }, scheduledStartTime: null, scheduledEndTime: null }
                ],
                unarrangedTasks: []
            };
            window.TempoPlanStore.saveActivePlan('emergency', samplePlan);
            window.TempoMode.renderActiveModeHome();
        })()""")
        time.sleep(0.5)

        dmode_html_tasks = eval_js("document.getElementById('dmode-home-content').innerHTML")
        assert_check("Task 1 'Marketing report' rendered", "Marketing report" in dmode_html_tasks)
        assert_check("Task 2 'Review presentation' rendered", "Review presentation" in dmode_html_tasks)
        assert_check("Task 3 'MAS reading' rendered", "MAS reading" in dmode_html_tasks)
        assert_check("No 'Urgent Plan' label appears on Default Home", "Urgent Plan" not in dmode_html_tasks)
        assert_check("No 'Urgent Task' label appears on Default Home", "Urgent Task" not in dmode_html_tasks)
        assert_check("Task 1 planned time '09:00 AM' or '9:00 AM' present", "09:00 AM" in dmode_html_tasks or "9:00 AM" in dmode_html_tasks)
        assert_check("Task 1 estimate '~45 min' present", "~45 min" in dmode_html_tasks)
        assert_check("Task 1 subtask progress '1 of 2 steps' present", "1 of 2 steps" in dmode_html_tasks)
        assert_check("Task 2 formatted time '2:30 PM' present", "2:30 PM" in dmode_html_tasks)
        assert_check("Task 3 'Flexible' time present", "Flexible" in dmode_html_tasks)

        # Toggle task 2 completion
        eval_js("window.TempoMode.toggleDmodeTask('task_2');")
        time.sleep(0.5)

        task2_completed_in_store = eval_js("""(() => {
            const p = window.TempoPlanStore.getActivePlan('emergency');
            const pt = p.plannedTasks.find(x => x.task.id === 'task_2');
            return pt && pt.task && pt.task.completed;
        })()""")
        assert_check("Task 2 toggled complete in SHARED store", task2_completed_in_store is True)

        dmode_html_after_toggle = eval_js("document.getElementById('dmode-home-content').innerHTML")
        assert_check("Task 2 rendered with checkmark symbol '✓'", "✓" in dmode_html_after_toggle)

        # Expand subtasks and toggle subtask
        eval_js("window.TempoMode.toggleDmodeSubtasksExpanded('task_1');")
        time.sleep(0.5)
        dmode_html_expanded = eval_js("document.getElementById('dmode-home-content').innerHTML")
        assert_check("Subtask 'Review guidelines' visible in expanded view", "Review guidelines" in dmode_html_expanded)
        assert_check("Subtask 'Draft executive summary' visible in expanded view", "Draft executive summary" in dmode_html_expanded)

        eval_js("window.TempoMode.toggleDmodeSubtask('task_1', 'sub_1_2');")
        time.sleep(0.5)
        sub2_completed = eval_js("""(() => {
            const p = window.TempoPlanStore.getActivePlan('emergency');
            const pt = p.plannedTasks.find(x => x.task.id === 'task_1');
            const s = pt.task.subtasks.find(x => x.id === 'sub_1_2');
            return s && s.completed;
        })()""")
        assert_check("Subtask 'sub_1_2' toggled in SHARED store", sub2_completed is True)

        # Check View my plan opens plan workspace
        eval_js("window.TempoMode.openPlanWorkspace();")
        time.sleep(0.5)
        pw_visible = eval_js("!document.getElementById('screen-plan-workspace').classList.contains('hidden')")
        assert_check("View my plan opened screen-plan-workspace", pw_visible is True)

        # Navigate back to Home
        eval_js("window.TempoApp.navigateTo('today');")
        time.sleep(0.5)

        log("\n--- TEST SUITE 3: SELF-CHECK INTEGRATION (State B & C) ---")
        # Add a tracker via TempoRecoverySelfCheck
        eval_js("""(() => {
            window.TempoRecoverySelfCheck.createTracker({
                name: 'Adequate sleep',
                category: 'supportive',
                check_method: 'yes_no'
            });
            window.TempoMode.renderActiveModeHome();
        })()""")
        time.sleep(0.5)

        dmode_html_sc = eval_js("document.getElementById('dmode-home-content').innerHTML")
        assert_check("Self-check State B prompt 'How have things been today?'", "How have things been today?" in dmode_html_sc)
        assert_check("Trackers count '1 thing you're keeping an eye on'", "1 thing you're keeping an eye on" in dmode_html_sc)
        assert_check("Check in button present", "Check in" in dmode_html_sc)
        assert_check("Manage button present", "Manage" in dmode_html_sc)

        # Save a check-in for today
        eval_js("""(() => {
            const trackers = window.TempoRecoverySelfCheck.getActiveTrackers();
            const todayStr = new Date().toISOString().split('T')[0];
            window.TempoRecoverySelfCheck.saveTodayCheckin({
                date: todayStr,
                observations: [
                    { tracker_id: trackers[0].id, status: 'answered', value_yes_no: true }
                ]
            });
            window.TempoMode.renderActiveModeHome();
        })()""")
        time.sleep(0.5)

        dmode_html_sc_done = eval_js("document.getElementById('dmode-home-content').innerHTML")
        assert_check("Self-check State C status '✓ Checked in today'", "✓ Checked in today" in dmode_html_sc_done)
        assert_check("1 of 1 answered", "1 of 1 answered" in dmode_html_sc_done)
        assert_check("View / Edit CTA present", "View / Edit" in dmode_html_sc_done)
        assert_check("No aggregate score or percentage shown", "%" not in dmode_html_sc_done and "Score" not in dmode_html_sc_done)

        log("\n--- TEST SUITE 4: CONTEXTUAL WEEKLY REVIEW ---")
        # When isReady is false -> no card
        eval_js("""(() => {
            window.TempoWeeklyReview.isReady = () => false;
            window.TempoMode.renderActiveModeHome();
        })()""")
        time.sleep(0.5)
        dmode_html_not_ready = eval_js("document.getElementById('dmode-home-content').innerHTML")
        assert_check("No Weekly Review card when isReady() is false", "YOUR WEEK IS READY" not in dmode_html_not_ready)

        # When isReady is true -> card appears
        eval_js("""(() => {
            window.TempoWeeklyReview.isReady = () => true;
            window.TempoMode.renderActiveModeHome();
        })()""")
        time.sleep(0.5)
        dmode_html_wr = eval_js("document.getElementById('dmode-home-content').innerHTML")
        assert_check("Contextual card 'YOUR WEEK IS READY' appears when isReady() is true", "YOUR WEEK IS READY" in dmode_html_wr)
        assert_check("'Look back at my week' CTA present", "Look back at my week" in dmode_html_wr)

        # Reset isReady
        eval_js("""(() => {
            delete window.TempoWeeklyReview.isReady;
            window.TempoMode.renderActiveModeHome();
        })()""")
        time.sleep(0.5)

        log("\n--- TEST SUITE 5: CONTINUITY ACROSS MODES (State D) ---")
        # Switch to Urgent Mode
        eval_js("window.TempoMode.setMode('emergency');")
        time.sleep(0.5)
        emode_active = eval_js("window.TempoMode.getMode() === 'emergency'")
        emode_box_vis = eval_js("!document.getElementById('emode-home-content').classList.contains('hidden')")
        dmode_box_hid = eval_js("document.getElementById('dmode-home-content').classList.contains('hidden')")
        assert_check("Urgent Mode activated", emode_active is True and emode_box_vis is True and dmode_box_hid is True)

        # Use 'Take a break from modes' (select 'default')
        eval_js("window.TempoMode.selectModeFromDropdown('default', 'home');")
        time.sleep(0.5)
        dmode_active_again = eval_js("window.TempoMode.getMode() === 'default'")
        dmode_box_vis_again = eval_js("!document.getElementById('dmode-home-content').classList.contains('hidden')")
        emode_box_hid_again = eval_js("document.getElementById('emode-home-content').classList.contains('hidden')")
        assert_check("Returned to Default Mode via Take a break", dmode_active_again is True and dmode_box_vis_again is True and emode_box_hid_again is True)

        # Verify shared tasks and trackers persisted
        dmode_html_final = eval_js("document.getElementById('dmode-home-content').innerHTML")
        assert_check("Shared tasks preserved ('Marketing report' still present)", "Marketing report" in dmode_html_final)
        assert_check("Self-check state preserved ('Checked in today' still present)", "Checked in today" in dmode_html_final)
        assert_check("No Unclear reflection history surfaced", "Your last Unclear reflection" not in dmode_html_final and "Yesterday you said" not in dmode_html_final)
        assert_check("No SOS history surfaced", "Welcome back after your crisis" not in dmode_html_final and "You used SOS" not in dmode_html_final)

        log(f"\n==========================================")
        log(f"SMOKE TEST SUMMARY: {passed_checks}/{total_checks} CHECKS PASSED")
        log(f"==========================================")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    run_tests()
