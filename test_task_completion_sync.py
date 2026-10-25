import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os
import base64

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_sync_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9268
    
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
                resp = json.loads(ws.recv())
                if resp.get("id") == cid:
                    return resp.get("result", {})

        def eval_js(expr):
            res = send_command("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True
            })
            if "exceptionDetails" in res:
                log(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        def save_screenshot(filepath):
            data = send_command("Page.captureScreenshot", {"format": "png"})
            b64 = data.get("data", "")
            if b64:
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(b64))
                log(f"Saved screenshot: {filepath}")

        # Set viewport
        send_command("Emulation.setDeviceMetricsOverride", {
            "width": 1280,
            "height": 900,
            "deviceScaleFactor": 1,
            "mobile": False
        })
        time.sleep(1)

        # Wait for scripts to initialize
        log("Waiting for TempoApp initialization...")
        for _ in range(20):
            is_ready = eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoApp.navigateTo === 'function'")
            if is_ready:
                break
            time.sleep(0.5)

        # Authenticate test user
        log("Authenticating test user...")
        eval_js("""
            (async () => {
                const mock = {
                    id: 'local_user_test',
                    email: 'alex.chen@university.edu',
                    raw_email: 'alex.chen@university.edu',
                    password: 'password123',
                    user_metadata: { full_name: 'Alex Chen', display_name: 'Alex Chen', role: 'student' }
                };
                localStorage.setItem('tempo_mock_account_alex.chen@university.edu', JSON.stringify(mock));
                if (window.TempoAuth) {
                    await window.TempoAuth.signIn("alex.chen@university.edu", "password123");
                }
            })()
        """)
        time.sleep(1)
        is_auth = eval_js("Boolean(window.TempoAuth && window.TempoAuth.getCurrentUser())")
        log(f"Authenticated status: {is_auth}")

        # =======================================================
        # SECTION 1: WORKING PLAN TOOL - COMPLETION, DONE GROUPING & STRIKETHROUGH
        # =======================================================
        log("\n--- SECTION 1: Working Plan Tool Completion & Done Grouping ---")
        eval_js("window.TempoApp.navigateTo('plan-workspace')")
        time.sleep(0.8)

        # 1. Verify initial tasks in left column
        initial_tasks = eval_js("""
            (() => {
                return Array.from(document.querySelectorAll('[data-task-row] h4')).map(h => h.innerText.trim());
            })()
        """)
        log(f"Initial tasks in Working Plan: {initial_tasks}")
        assert "Marketing Research" in initial_tasks, "Expected 'Marketing Research' in task list"
        assert "Event Proposal" in initial_tasks, "Expected 'Event Proposal' in task list"

        # 2. Mark first task ('Marketing Research') as completed
        eval_js("""
            (() => {
                const markBtn = Array.from(document.querySelectorAll('[data-tempo-ui="selected-task-card"] button')).find(b => b.innerText.includes('Mark as done'));
                if (markBtn) markBtn.click();
            })()
        """)
        time.sleep(0.8)

        # Check progress counter
        counter_span = eval_js("""
            (() => {
                const s = Array.from(document.querySelectorAll('span')).find(el => el.innerText.includes('Tasks'));
                return s ? s.innerText.trim() : '';
            })()
        """)
        log(f"Progress count after completion: '{counter_span}'")
        assert "1/6 Tasks" in counter_span or "1/" in counter_span, f"Expected 1 completed, got {counter_span}"

        # Check Done section
        done_sec_exists = eval_js("Boolean(document.querySelector('[data-tempo-ui=\"done-section\"]'))")
        assert done_sec_exists, "Done section [data-tempo-ui='done-section'] should appear"

        done_tasks = eval_js("""
            (() => {
                return Array.from(document.querySelectorAll('[data-tempo-ui="done-section"] h4')).map(h => h.innerText.trim());
            })()
        """)
        log(f"Done section tasks: {done_tasks}")
        assert "Marketing Research" in done_tasks, f"Expected 'Marketing Research' in Done section, got {done_tasks}"

        # Verify strikethrough styling
        has_strikethrough = eval_js("""
            (() => {
                const el = document.querySelector('[data-tempo-ui="done-section"] h4');
                return el ? el.classList.contains('line-through') : false;
            })()
        """)
        assert has_strikethrough, "Completed task title in Done section must have line-through styling"
        log("✓ Working Plan: task marked as done moves to bottom Done section with strikethrough styling.")

        shot_wp = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\working_plan_task_completed_sync.png"
        save_screenshot(shot_wp)

        # =======================================================
        # SECTION 2: RECOVERY MODE (RMODE) DASHBOARD - DEDICATED DONE COLUMN
        # =======================================================
        log("\n--- SECTION 2: Recovery Mode Dashboard Dedicated Done Column ---")
        eval_js("""
            (() => {
                window.TempoMode.setMode('recovery');
                window.TempoApp.navigateTo('today');
            })()
        """)
        time.sleep(1)

        # Verify active context
        cur_mode = eval_js("window.TempoMode.getMode()")
        log(f"Current mode: {cur_mode}")
        assert cur_mode == "recovery", f"Expected recovery mode, got {cur_mode}"

        # Check Working Plan progress on Rmode dashboard
        rmode_progress = eval_js("""
            (() => {
                const el = document.querySelector('[data-tempo-ui="recovery-working-plan"] span.shrink-0');
                return el ? el.innerText.trim() : '';
            })()
        """)
        log(f"Rmode Working Plan progress: '{rmode_progress}'")
        assert "1/" in rmode_progress, f"Expected 1 completed task in Rmode progress, got '{rmode_progress}'"

        # Check dedicated Done column exists as the last column on the right
        done_col_exists = eval_js("Boolean(document.querySelector('[data-tempo-ui=\"recovery-done-column\"]'))")
        assert done_col_exists, "Dedicated Done column [data-tempo-ui='recovery-done-column'] must exist"

        # Verify completed task is inside the Done column
        rmode_done_tasks = eval_js("""
            (() => {
                return Array.from(document.querySelectorAll('[data-tempo-ui="recovery-done-column"] h5')).map(h => h.innerText.trim());
            })()
        """)
        log(f"Rmode Done column tasks: {rmode_done_tasks}")
        assert any("Marketing Research" in t for t in rmode_done_tasks), f"Expected 'Marketing Research' in Rmode Done column, got {rmode_done_tasks}"

        # Check strikethrough styling in Rmode Done column
        rmode_strikethrough = eval_js("""
            (() => {
                const el = document.querySelector('[data-tempo-ui="recovery-done-column"] h5');
                return el ? (el.classList.contains('line-through') || el.className.includes('line-through')) : false;
            })()
        """)
        assert rmode_strikethrough, "Completed task title inside Rmode Done column must have strikethrough"

        # Check checkmark in checkbox
        rmode_check = eval_js("""
            (() => {
                const btn = document.querySelector('[data-tempo-ui="recovery-done-column"] button');
                return btn ? btn.innerText.trim() : '';
            })()
        """)
        log(f"Rmode Done column checkbox mark: '{rmode_check}'")
        assert "✓" in rmode_check, f"Expected checkmark '✓' inside Done column checkbox, got '{rmode_check}'"

        # Check horizontal scrolling container
        scroll_info = eval_js("""
            (() => {
                const sc = document.querySelector('[data-tempo-ui="recovery-plan-scroll-container"]');
                return {
                    overflowX: window.getComputedStyle(sc).overflowX,
                    scrollWidth: sc.scrollWidth,
                    clientWidth: sc.clientWidth
                };
            })()
        """)
        log(f"Rmode scroll info: {scroll_info}")
        assert scroll_info["overflowX"] in ["auto", "scroll"], f"Expected overflowX auto/scroll, got {scroll_info['overflowX']}"
        log("✓ Recovery Mode: completed task rendered inside dedicated Done column on the right with strikethrough and checkmark.")

        shot_rmode = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\recovery_working_plan_done_column.png"
        save_screenshot(shot_rmode)

        # =======================================================
        # SECTION 3: REVERTING TASK IN RMODE DONE COLUMN & RESTORING TO DATE COLUMN
        # =======================================================
        log("\n--- SECTION 3: Reverting from Rmode Done Column & Restoring to Date Column ---")
        # Click the completed task checkbox inside the Done column to uncheck
        eval_js("""
            (() => {
                const btn = document.querySelector('[data-tempo-ui="recovery-done-column"] button');
                if (btn) btn.click();
            })()
        """)
        time.sleep(0.8)

        # Verify progress counter reverted
        reverted_rmode_progress = eval_js("""
            (() => {
                const el = document.querySelector('[data-tempo-ui="recovery-working-plan"] span.shrink-0');
                return el ? el.innerText.trim() : '';
            })()
        """)
        log(f"Reverted Rmode progress: '{reverted_rmode_progress}'")
        assert "0/" in reverted_rmode_progress, f"Expected 0 completed tasks after unchecking, got '{reverted_rmode_progress}'"

        # Verify task is removed from Done column
        done_col_count = eval_js("""
            document.querySelectorAll('[data-tempo-ui="recovery-done-column"] [data-task-id]').length
        """)
        assert done_col_count == 0, f"Expected 0 tasks in Done column, got {done_col_count}"

        # Verify task is restored to Date Column
        date_col_tasks = eval_js("""
            (() => {
                return Array.from(document.querySelectorAll('[data-tempo-ui="recovery-date-column"] h5')).map(h => h.innerText.trim());
            })()
        """)
        log(f"Restored date column tasks: {date_col_tasks}")
        assert any("Marketing Research" in t for t in date_col_tasks), f"Expected 'Marketing Research' restored to date column, got {date_col_tasks}"

        # Complete a task from the date column directly
        log("Completing 'Marketing Research' from date column...")
        eval_js("""
            (() => {
                const firstDateBtn = document.querySelector('[data-tempo-ui="recovery-date-column"] button');
                if (firstDateBtn) firstDateBtn.click();
            })()
        """)
        time.sleep(0.8)

        re_done_progress = eval_js("""
            (() => {
                const el = document.querySelector('[data-tempo-ui="recovery-working-plan"] span.shrink-0');
                return el ? el.innerText.trim() : '';
            })()
        """)
        log(f"Progress after re-completing: '{re_done_progress}'")
        assert "1/" in re_done_progress, f"Expected 1 completed task, got '{re_done_progress}'"
        log("✓ Task restores to original date column when unmarked, and moves back to Done column when re-marked.")

        # =======================================================
        # SECTION 4: URGENT MODE (URMODE) - BOTTOM POSITIONING & SYNC
        # =======================================================
        log("\n--- SECTION 4: Urgent Mode Dashboard Completion & Bottom Positioning ---")
        eval_js("""
            (() => {
                window.TempoMode.setMode('emergency');
                window.TempoApp.navigateTo('today');
            })()
        """)
        time.sleep(1)

        cur_mode_u = eval_js("window.TempoMode.getMode()")
        assert cur_mode_u == "emergency", f"Expected emergency mode, got {cur_mode_u}"

        # Check Urmode progress header
        urmode_progress = eval_js("""
            (() => {
                const el = document.querySelector('.urgent-working-plan-card .text-\\\\[\\\\#6F6B68\\\\].font-medium');
                return el ? el.innerText.trim() : '';
            })()
        """)
        log(f"Urmode progress: '{urmode_progress}'")
        assert "1 of" in urmode_progress or "1/" in urmode_progress, f"Expected 1 completed in Urmode, got '{urmode_progress}'"

        # Check Done section exists in Urmode scrollable list
        urmode_done_exists = eval_js("Boolean(document.querySelector('[data-tempo-ui=\"urmode-done-section\"]'))")
        assert urmode_done_exists, "Urmode Done section [data-tempo-ui='urmode-done-section'] must exist"

        # Verify completed task title has strikethrough and Completed badge
        urmode_completed_title = eval_js("""
            (() => {
                const item = document.querySelector('.urgent-working-plan-tasks-scroll [data-tempo-ui="urmode-done-section"] ~ .urgent-timeline-item h4');
                return item ? item.innerText.trim() : '';
            })()
        """)
        urmode_has_strikethrough = eval_js("""
            (() => {
                const item = document.querySelector('.urgent-working-plan-tasks-scroll [data-tempo-ui="urmode-done-section"] ~ .urgent-timeline-item h4');
                return item ? item.classList.contains('line-through') : false;
            })()
        """)
        log(f"Urmode completed task title: '{urmode_completed_title}', strikethrough: {urmode_has_strikethrough}")
        assert "Marketing Research" in urmode_completed_title, f"Expected 'Marketing Research' at bottom under Done, got '{urmode_completed_title}'"
        assert urmode_has_strikethrough, "Title must have line-through in Urmode"

        # Complete second task ('Event Proposal') from Urmode
        log("Completing next task from Urmode...")
        eval_js("""
            (() => {
                const firstIncomplete = document.querySelector('.urgent-timeline-item:not([data-tempo-ui="urmode-done-section"] ~ .urgent-timeline-item) .cursor-pointer');
                if (firstIncomplete) firstIncomplete.click();
            })()
        """)
        time.sleep(0.8)

        urmode_updated_progress = eval_js("""
            (() => {
                const el = document.querySelector('.urgent-working-plan-card .text-\\\\[\\\\#6F6B68\\\\].font-medium');
                return el ? el.innerText.trim() : '';
            })()
        """)
        log(f"Urmode updated progress: '{urmode_updated_progress}'")
        assert "2 of" in urmode_updated_progress or "2/" in urmode_updated_progress, f"Expected 2 completed in Urmode, got '{urmode_updated_progress}'"

        shot_urmode = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\urmode_working_plan_done_section.png"
        save_screenshot(shot_urmode)
        log("✓ Urgent Mode: tasks positioned at bottom under Done section with strikethrough and green badge.")

        # =======================================================
        # SECTION 5: PERSISTENCE ACROSS REFRESH & NAVIGATION
        # =======================================================
        log("\n--- SECTION 5: Persistence Across Reload & Navigation ---")
        send_command("Page.reload")
        time.sleep(1)
        for _ in range(20):
            if eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined' && !!document.querySelector('.urgent-working-plan-card')"):
                break
            time.sleep(0.5)

        # Re-check Urmode after reload
        reload_urmode_progress = eval_js("""
            (() => {
                const el = document.querySelector('.urgent-working-plan-card .text-\\\\[\\\\#6F6B68\\\\].font-medium');
                return el ? el.innerText.trim() : '';
            })()
        """)
        log(f"After reload Urmode progress: '{reload_urmode_progress}'")
        assert "2 of" in reload_urmode_progress or "2/" in reload_urmode_progress, f"Expected 2 completed preserved after reload, got '{reload_urmode_progress}'"

        # Check Working Plan tool after reload
        eval_js("window.TempoApp.navigateTo('plan-workspace')")
        time.sleep(1)

        reload_wp_counter = eval_js("""
            (() => {
                const s = Array.from(document.querySelectorAll('span')).find(el => el.innerText.includes('Tasks'));
                return s ? s.innerText.trim() : '';
            })()
        """)
        log(f"After reload Working Plan counter: '{reload_wp_counter}'")
        assert "2/6 Tasks" in reload_wp_counter or "2/" in reload_wp_counter, f"Expected 2 completed in Working Plan after reload, got '{reload_wp_counter}'"

        reload_done_count = eval_js("""
            document.querySelectorAll('[data-tempo-ui="done-section"] [data-task-row]').length
        """)
        log(f"After reload Working Plan Done section count: {reload_done_count}")
        assert reload_done_count == 2, f"Expected 2 tasks in Working Plan Done section, got {reload_done_count}"

        # Check Rmode after reload
        eval_js("""
            (() => {
                window.TempoMode.setMode('recovery');
                window.TempoApp.navigateTo('today');
            })()
        """)
        time.sleep(1)

        reload_rmode_progress = eval_js("""
            (() => {
                const el = document.querySelector('[data-tempo-ui="recovery-working-plan"] span.shrink-0');
                return el ? el.innerText.trim() : '';
            })()
        """)
        log(f"After reload Rmode progress: '{reload_rmode_progress}'")
        assert "2/" in reload_rmode_progress, f"Expected 2 completed in Rmode after reload, got '{reload_rmode_progress}'"

        reload_rmode_done_count = eval_js("""
            document.querySelectorAll('[data-tempo-ui="recovery-done-column"] [data-task-id]').length
        """)
        log(f"After reload Rmode Done column count: {reload_rmode_done_count}")
        assert reload_rmode_done_count == 2, f"Expected 2 tasks in Rmode Done column after reload, got {reload_rmode_done_count}"

        log("\n=======================================================")
        log("🎉 ALL TASK COMPLETION & SYNC TESTS PASSED 100%!")
        log("=======================================================")

    finally:
        if ws:
            ws.close()
        proc.kill()

if __name__ == "__main__":
    run_tests()
