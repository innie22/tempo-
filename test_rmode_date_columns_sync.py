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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_rmode_col_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9388
    
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

        # Switch to Recovery Mode (Rmode)
        log("Switching to Recovery Mode...")
        eval_js("""
            (() => {
                window.TempoMode.setMode('recovery');
                window.TempoApp.navigateTo('today');
                // Dismiss any modal and scroll directly to Working Plan card
                const closeBtn = document.querySelector('button[aria-label="Close"], button.close, [onclick*="close"], [onclick*="explore"]');
                if (closeBtn) closeBtn.click();
                const modalBackdrops = document.querySelectorAll('.fixed.inset-0');
                modalBackdrops.forEach(m => m.remove());
                const wp = document.getElementById('recovery-working-plan');
                if (wp) wp.scrollIntoView({ behavior: 'instant', block: 'center' });
            })()
        """)
        time.sleep(1)

        # =======================================================
        # TEST 1: Initial Rmode Working Plan Card & Dynamic Date Columns
        # =======================================================
        log("\n--- TEST 1: Initial Rmode Working Plan Card & Date Columns ---")
        card_info = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                if (!card) return null;
                const dateCols = Array.from(card.querySelectorAll('[data-tempo-ui="recovery-date-column"]')).map(col => ({
                    dateKey: col.getAttribute('data-date-key'),
                    header: col.querySelector('span')?.textContent.trim(),
                    tasksCount: col.querySelectorAll('[data-task-id]').length,
                    taskTitles: Array.from(col.querySelectorAll('[data-task-id] h5')).map(h => h.textContent.trim())
                }));
                const doneCol = card.querySelector('[data-tempo-ui="recovery-done-column"]');
                const doneTasks = doneCol ? Array.from(doneCol.querySelectorAll('[data-task-id] h5')).map(h => h.textContent.trim()) : [];
                const progressText = card.querySelector('span.shrink-0')?.textContent.trim();
                return {
                    dateCols,
                    doneTasks,
                    progressText
                };
            })()
        """)
        log(f"Initial card info: {json.dumps(card_info, indent=2)}")
        assert card_info is not None, "Rmode Working Plan card must exist"
        assert len(card_info["dateCols"]) >= 2, f"Expected at least 2 date columns initially, got {len(card_info['dateCols'])}"
        
        # Verify chronological order
        date_keys = [c["dateKey"] for c in card_info["dateCols"]]
        sorted_keys = sorted(date_keys)
        assert date_keys == sorted_keys, f"Date columns must be sorted chronologically: {date_keys} vs {sorted_keys}"
        log("✓ Date columns are sorted chronologically from earliest to latest")

        # Verify Done column exists and has 0 tasks initially
        assert len(card_info["doneTasks"]) == 0, f"Expected 0 completed tasks in Done column, got {card_info['doneTasks']}"
        log("✓ Permanent Done column rendered on the right with empty placeholder")

        screenshot_initial = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\rmode_dynamic_date_columns_initial.png"
        save_screenshot(screenshot_initial)

        # =======================================================
        # TEST 2: Completing the only task on a date removes that date column
        # =======================================================
        log("\n--- TEST 2: Completing Last Active Task on a Date Removes Date Column ---")
        # In default plan, column 2 has 'Edit Video' (the only task on that date)
        col2_key = card_info["dateCols"][1]["dateKey"]
        col2_task_title = card_info["dateCols"][1]["taskTitles"][0]
        log(f"Completing task '{col2_task_title}' on date '{col2_key}'...")

        eval_js(f"""
            (() => {{
                const col = document.querySelector('[data-tempo-ui="recovery-date-column"][data-date-key="{col2_key}"]');
                const btn = col ? col.querySelector('[data-task-id] button') : null;
                if (btn) btn.click();
            }})()
        """)
        time.sleep(1)

        # Check date columns after completion
        after_comp_info = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                const dateCols = Array.from(card.querySelectorAll('[data-tempo-ui="recovery-date-column"]')).map(col => ({
                    dateKey: col.getAttribute('data-date-key'),
                    header: col.querySelector('span')?.textContent.trim(),
                    tasksCount: col.querySelectorAll('[data-task-id]').length
                }));
                const doneCol = card.querySelector('[data-tempo-ui="recovery-done-column"]');
                const doneTasks = Array.from(doneCol.querySelectorAll('[data-task-id] h5')).map(h => ({
                    title: h.textContent.trim(),
                    isLineThrough: window.getComputedStyle(h).textDecorationLine.includes('line-through') || h.className.includes('line-through')
                }));
                const progressText = card.querySelector('span.shrink-0')?.textContent.trim();
                return {
                    dateCols,
                    doneTasks,
                    progressText
                };
            })()
        """)
        log(f"After completing task on date 2: {json.dumps(after_comp_info, indent=2)}")
        
        # Verify col2 disappeared!
        remaining_keys = [c["dateKey"] for c in after_comp_info["dateCols"]]
        assert col2_key not in remaining_keys, f"Date column '{col2_key}' should have disappeared when its only task was completed! Remaining: {remaining_keys}"
        log(f"✓ Date column '{col2_key}' disappeared immediately because it has 0 active tasks")

        # Verify completed task is now in Done column with strikethrough
        done_titles = [t["title"] for t in after_comp_info["doneTasks"]]
        assert any(col2_task_title in dt for dt in done_titles), f"Expected '{col2_task_title}' in Done column, got {done_titles}"
        done_item = next(t for t in after_comp_info["doneTasks"] if col2_task_title in t["title"])
        assert done_item["isLineThrough"] is True, f"Completed task '{col2_task_title}' must have strikethrough styling"
        log(f"✓ Task '{col2_task_title}' appears in Done column with strikethrough title")

        screenshot_completed = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\rmode_date_column_disappeared_done_column.png"
        save_screenshot(screenshot_completed)

        # =======================================================
        # TEST 3: Unchecking task in Done column restores date column in order
        # =======================================================
        log("\n--- TEST 3: Unchecking Task in Done Column Restores Date Column Chronologically ---")
        eval_js(f"""
            (() => {{
                const doneCol = document.querySelector('[data-tempo-ui="recovery-done-column"]');
                const taskCard = Array.from(doneCol.querySelectorAll('[data-task-id]')).find(c => c.textContent.includes('{col2_task_title}'));
                const btn = taskCard ? taskCard.querySelector('button') : null;
                if (btn) btn.click();
            }})()
        """)
        time.sleep(1)

        restored_info = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                const dateCols = Array.from(card.querySelectorAll('[data-tempo-ui="recovery-date-column"]')).map(col => ({
                    dateKey: col.getAttribute('data-date-key'),
                    header: col.querySelector('span')?.textContent.trim(),
                    tasksCount: col.querySelectorAll('[data-task-id]').length,
                    taskTitles: Array.from(col.querySelectorAll('[data-task-id] h5')).map(h => ({
                        title: h.textContent.trim(),
                        isLineThrough: window.getComputedStyle(h).textDecorationLine.includes('line-through') || h.className.includes('line-through')
                    }))
                }));
                const doneCol = card.querySelector('[data-tempo-ui="recovery-done-column"]');
                const doneTasks = doneCol ? Array.from(doneCol.querySelectorAll('[data-task-id] h5')).map(h => h.textContent.trim()) : [];
                return {
                    dateCols,
                    doneTasks
                };
            })()
        """)
        log(f"After unchecking task: {json.dumps(restored_info, indent=2)}")
        restored_keys = [c["dateKey"] for c in restored_info["dateCols"]]
        assert col2_key in restored_keys, f"Date column '{col2_key}' must be restored when task is marked incomplete! Got: {restored_keys}"
        assert restored_keys == sorted(restored_keys), f"Restored date columns must remain in chronological order: {restored_keys}"
        
        # Verify strikethrough removed
        col2_obj = next(c for c in restored_info["dateCols"] if c["dateKey"] == col2_key)
        restored_task = next(t for t in col2_obj["taskTitles"] if col2_task_title in t["title"])
        assert restored_task["isLineThrough"] is False, f"Restored task '{col2_task_title}' must NOT have strikethrough styling"
        assert len(restored_info["doneTasks"]) == 0, "Done column should be empty again"
        log(f"✓ Date column '{col2_key}' restored in chronological order and task strikethrough removed")

        # =======================================================
        # TEST 4: Two-way synchronization with Working Plan tool
        # =======================================================
        log("\n--- TEST 4: Two-way Synchronization with Working Plan Tool ---")
        # 1. Click Adjust Plan button from Rmode card
        log("Clicking Adjust Plan button...")
        eval_js("""
            (() => {
                const btn = document.querySelector('[data-tempo-ui="recovery-working-plan"] button');
                btn.click();
            })()
        """)
        time.sleep(1)

        cur_route = eval_js("window.location.hash")
        cur_mode = eval_js("window.TempoMode ? window.TempoMode.getMode() : null")
        log(f"After Adjust Plan click - Route: '{cur_route}', Active mode: '{cur_mode}'")
        assert 'plan-workspace' in cur_route, f"Expected route to be #plan-workspace, got {cur_route}"
        assert cur_mode == 'recovery', f"Expected active mode to remain 'recovery', got {cur_mode}"
        log("✓ Adjust Plan button navigated directly to Working Plan tool without mode switch")

        # 2. In Working Plan tool, edit task name
        log("Editing task name in Working Plan tool...")
        eval_js("""
            (() => {
                const plan = window.TempoPlanWorkspace.getActivePlan();
                if (plan && plan.plannedTasks && plan.plannedTasks[0] && plan.plannedTasks[0].task) {
                    plan.plannedTasks[0].task.name = "Marketing Research - Updated";
                    // Also reschedule task 3 to a future distinct date e.g. 2026-10-25
                    if (plan.plannedTasks[2]) {
                        plan.plannedTasks[2].dayDate = "2026-10-25";
                        plan.plannedTasks[2].dayLabel = "October 25";
                        if (plan.plannedTasks[2].task) {
                            plan.plannedTasks[2].task.scheduledDate = "2026-10-25";
                        }
                    }
                    localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
                    if (window.TempoPlanStore) {
                        window.TempoPlanStore.saveActivePlan('recovery', plan);
                    }
                }
            })()
        """)
        time.sleep(0.5)

        # 3. Return to Home (Rmode dashboard)
        log("Returning to Home...")
        eval_js("window.TempoPlanWorkspace.navigateHome()")
        time.sleep(1)
        eval_js("""
            (() => {
                const wp = document.getElementById('recovery-working-plan');
                if (wp) wp.scrollIntoView({ behavior: 'instant', block: 'center' });
            })()
        """)
        time.sleep(0.5)

        post_return_info = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                const dateCols = Array.from(card.querySelectorAll('[data-tempo-ui="recovery-date-column"]')).map(col => ({
                    dateKey: col.getAttribute('data-date-key'),
                    header: col.querySelector('span')?.textContent.trim(),
                    taskTitles: Array.from(col.querySelectorAll('[data-task-id] h5')).map(h => h.textContent.trim())
                }));
                return dateCols;
            })()
        """)
        log(f"Rmode card after returning from Working Plan: {json.dumps(post_return_info, indent=2)}")
        
        # Verify updated task title is reflected
        all_titles = []
        for col in post_return_info:
            all_titles.extend(col["taskTitles"])
        assert any("Marketing Research - Updated" in t for t in all_titles), f"Expected 'Marketing Research - Updated' to reflect in Rmode card, got {all_titles}"
        log("✓ Task name edits made in Working Plan tool immediately reflect on Rmode card")

        # Verify new date column '2026-10-25' exists and is chronologically sorted
        post_keys = [c["dateKey"] for c in post_return_info]
        assert "2026-10-25" in post_keys, f"Expected rescheduled date '2026-10-25' column to appear on Rmode card! Got: {post_keys}"
        assert post_keys == sorted(post_keys), f"Date columns must be chronologically sorted: {post_keys}"
        assert "October 25" in [c["header"] for c in post_return_info], f"Header for 2026-10-25 should be 'October 25'"
        log("✓ Rescheduled task created new date column 'October 25' in chronological position")

        eval_js("""
            (() => {
                const modalBackdrops = document.querySelectorAll('.fixed.inset-0, #recovery-welcome-modal, #recovery-intro-banner');
                modalBackdrops.forEach(m => m.remove());
                const wp = document.getElementById('recovery-working-plan');
                if (wp) wp.scrollIntoView({ behavior: 'instant', block: 'center' });
            })()
        """)
        time.sleep(0.5)

        screenshot_synced = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\rmode_working_plan_sync_verified.png"
        save_screenshot(screenshot_synced)

        # =======================================================
        # TEST 5: Bidirectional Scrolling in Working Plan Card
        # =======================================================
        log("\n--- TEST 5: Bidirectional Scrolling & Responsive Containment ---")
        scroll_check = eval_js("""
            (() => {
                const sc = document.querySelector('[data-tempo-ui="recovery-plan-scroll-container"]');
                if (!sc) return null;
                const cs = window.getComputedStyle(sc);
                const doneCol = sc.querySelector('[data-tempo-ui="recovery-done-column"]');
                return {
                    overflowX: cs.overflowX,
                    overflowY: cs.overflowY,
                    scrollWidth: sc.scrollWidth,
                    clientWidth: sc.clientWidth,
                    doneColVisible: !!doneCol
                };
            })()
        """)
        log(f"Scroll container check: {json.dumps(scroll_check, indent=2)}")
        assert scroll_check["overflowX"] in ["auto", "scroll"], f"Expected overflowX auto/scroll, got {scroll_check['overflowX']}"
        assert scroll_check["overflowY"] in ["auto", "scroll"], f"Expected overflowY auto/scroll, got {scroll_check['overflowY']}"
        assert scroll_check["doneColVisible"] is True, "Done column must be rendered"
        log("✓ Bidirectional scroll container verified with overflow-x: auto and overflow-y: auto")

        log("\nALL RMODE WORKING PLAN CARD & DYNAMIC DATE COLUMN TESTS PASSED SUCCESSFULLY! 🎉")

    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == '__main__':
    run_tests()
