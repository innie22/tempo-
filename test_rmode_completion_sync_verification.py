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

def run():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_rmode_sync_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9366

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
    try:
        pages = []
        for _ in range(30):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as resp:
                    tabs = json.loads(resp.read().decode())
                    pages = [t for t in tabs if t.get("type") == "page" and "localhost" in t.get("url", "")]
                    if pages:
                        break
            except Exception:
                pass
            time.sleep(0.5)

        if not pages:
            raise RuntimeError("Could not connect to browser page")

        ws_url = pages[0]["webSocketDebuggerUrl"]
        ws = websocket.create_connection(ws_url)

        msg_id = 1
        def send_cmd(method, params=None):
            nonlocal msg_id
            cid = msg_id
            msg_id += 1
            req = {"id": cid, "method": method}
            if params:
                req["params"] = params
            ws.send(json.dumps(req))
            while True:
                r = json.loads(ws.recv())
                if r.get("id") == cid:
                    return r.get("result", {})

        def eval_js(expr):
            res = send_cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
            if "exceptionDetails" in res:
                log(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        def save_screenshot(filepath):
            data = send_cmd("Page.captureScreenshot", {"format": "png"})
            b64 = data.get("data", "")
            if b64:
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(b64))
                log(f"Saved screenshot: {filepath}")

        # Set viewport
        send_cmd("Emulation.setDeviceMetricsOverride", {
            "width": 1280,
            "height": 900,
            "deviceScaleFactor": 1,
            "mobile": False
        })
        time.sleep(1)

        # Wait for scripts
        for _ in range(30):
            if eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'"):
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

        # =======================================================
        # TEST 1: Exactly 3 Tasks (1 Completed, 2 Incomplete) with STALE MOCK STATE
        # =======================================================
        log("\n=== TEST 1: Working Plan with 3 Tasks (1 completed, 2 incomplete) ===")
        # We intentionally set dirty stale tempo_rmode_mock_tasks where ALL tasks are marked true!
        # The fix MUST ensure Rmode DOES NOT mark all 3 as completed!
        eval_js("""
            (() => {
                localStorage.setItem('tempo_rmode_mock_tasks', JSON.stringify({
                    'task-marketing-research': true,
                    'task-event-proposal': true,
                    'task-edit-video': true,
                    'rmode-mock-1': true,
                    'rmode-mock-2': true,
                    'rmode-mock-3': true
                }));

                const today = '2026-10-20';
                const tomorrow = '2026-10-21';
                const plan = {
                    plannedTasks: [
                        {
                            dayDate: today,
                            startTime: '9:00 AM',
                            endTime: '11:30 AM',
                            executionBadge: 'Now',
                            task: {
                                id: 'task-marketing-research',
                                name: 'Marketing Research',
                                deadlineDate: '2026-10-17',
                                completed: true,
                                executionStatus: 'completed',
                                subtasks: [{ id: 's1', title: 'Outline', completed: true }]
                            }
                        },
                        {
                            dayDate: today,
                            startTime: '3:00 PM',
                            endTime: '5:30 PM',
                            executionBadge: 'Later',
                            task: {
                                id: 'task-event-proposal',
                                name: 'Event Proposal',
                                deadlineDate: '2026-10-18',
                                completed: false,
                                executionStatus: 'pending',
                                subtasks: [{ id: 's2', title: 'Budget', completed: false }]
                            }
                        },
                        {
                            dayDate: tomorrow,
                            startTime: '9:00 AM',
                            endTime: '11:30 AM',
                            executionBadge: 'Later',
                            task: {
                                id: 'task-edit-video',
                                name: 'Edit Video',
                                deadlineDate: '2026-10-20',
                                completed: false,
                                executionStatus: 'pending',
                                subtasks: []
                            }
                        }
                    ],
                    unarrangedTasks: [],
                    tasks: []
                };

                localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
                if (window.TempoPlanStore) {
                    window.TempoPlanStore.saveActivePlan('recovery', plan);
                    window.TempoPlanStore.saveActivePlan('emergency', plan);
                }
                if (window.TempoEmergencyFlow) {
                    window.TempoEmergencyFlow.setConfirmedPlan(plan);
                }

                window.TempoMode.setMode('recovery');
                window.TempoApp.navigateTo('today');
            })()
        """)
        time.sleep(1)

        card_state = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                const dateCols = Array.from(card.querySelectorAll('[data-tempo-ui="recovery-date-column"]')).map(col => ({
                    dateKey: col.getAttribute('data-date-key'),
                    header: col.querySelector('span')?.textContent.trim(),
                    tasks: Array.from(col.querySelectorAll('[data-task-id]')).map(t => ({
                        id: t.getAttribute('data-task-id'),
                        name: t.querySelector('h5')?.textContent.trim(),
                        lineThrough: t.querySelector('h5')?.classList.contains('line-through'),
                        checked: t.querySelector('button')?.textContent.trim().includes('✓'),
                        badge: t.querySelector('span.rounded-full')?.textContent.trim()
                    }))
                }));
                const doneCol = card.querySelector('[data-tempo-ui="recovery-done-column"]');
                const doneTasks = Array.from(doneCol.querySelectorAll('[data-task-id]')).map(t => ({
                    id: t.getAttribute('data-task-id'),
                    name: t.querySelector('h5')?.textContent.trim(),
                    lineThrough: t.querySelector('h5')?.classList.contains('line-through'),
                    checked: t.querySelector('button')?.textContent.trim().includes('✓'),
                    badge: t.querySelector('span.rounded-full')?.textContent.trim()
                }));
                const progressText = card.querySelector('span.shrink-0')?.textContent.trim();
                return {
                    progressText,
                    dateCols,
                    doneTasks
                };
            })()
        """)
        log("Rmode Card State:\n" + json.dumps(card_state, indent=2))

        # Assertions
        assert len(card_state["doneTasks"]) == 1, f"Expected exactly 1 task in Done column, got {len(card_state['doneTasks'])}"
        done_task = card_state["doneTasks"][0]
        assert done_task["name"] == "Marketing Research", f"Expected Marketing Research in Done, got {done_task['name']}"
        assert done_task["lineThrough"] == True, "Completed task must have lineThrough strikethrough"
        assert done_task["checked"] == True, "Completed task checkbox must be checked with ✓"
        assert done_task["badge"] == "Done", "Completed task badge must be 'Done'"

        # Check date columns: October 20 and October 21
        assert len(card_state["dateCols"]) >= 1, "Must have date columns for incomplete tasks"
        all_incomplete_names = [t["name"] for col in card_state["dateCols"] for t in col["tasks"]]
        assert "Event Proposal" in all_incomplete_names, "Event Proposal must be in scheduled date column"
        assert "Edit Video" in all_incomplete_names, "Edit Video must be in scheduled date column"

        # Check no strikethrough on incomplete tasks
        for col in card_state["dateCols"]:
            for t in col["tasks"]:
                assert t["lineThrough"] == False, f"Incomplete task {t['name']} must NOT have strikethrough"
                assert t["checked"] == False, f"Incomplete task {t['name']} must NOT be checked"
                assert t["badge"] != "Done", f"Incomplete task {t['name']} must NOT have Done badge"

        log("✓ TEST 1 PASSED: Exactly 1 completed task in Done column with strikethrough, 2 incomplete tasks in scheduled-date columns without strikethrough!")

        shot1 = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\rmode_working_plan_sync_verified.png"
        save_screenshot(shot1)

        # =======================================================
        # TEST 2: Toggle Incomplete Task in Rmode Dashboard
        # =======================================================
        log("\n=== TEST 2: Toggle Incomplete Task ('Event Proposal') in Rmode ===")
        eval_js("""
            (() => {
                const btn = document.querySelector('[data-task-id="task-event-proposal"] button');
                if (btn) btn.click();
            })()
        """)
        time.sleep(1)

        card_state_2 = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                const doneCol = card.querySelector('[data-tempo-ui="recovery-done-column"]');
                const doneTasks = Array.from(doneCol.querySelectorAll('[data-task-id]')).map(t => ({
                    id: t.getAttribute('data-task-id'),
                    name: t.querySelector('h5')?.textContent.trim(),
                    lineThrough: t.querySelector('h5')?.classList.contains('line-through')
                }));
                const dateCols = Array.from(card.querySelectorAll('[data-tempo-ui="recovery-date-column"]')).map(col => ({
                    dateKey: col.getAttribute('data-date-key'),
                    tasks: Array.from(col.querySelectorAll('[data-task-id]')).map(t => t.querySelector('h5')?.textContent.trim())
                }));
                return { doneTasks, dateCols };
            })()
        """)
        log("After toggling Event Proposal:\n" + json.dumps(card_state_2, indent=2))
        assert len(card_state_2["doneTasks"]) == 2, f"Expected 2 completed tasks, got {len(card_state_2['doneTasks'])}"
        done_names = [t["name"] for t in card_state_2["doneTasks"]]
        assert "Event Proposal" in done_names, "Event Proposal should now be in Done column"
        assert "Marketing Research" in done_names, "Marketing Research should still be in Done column"
        log("✓ TEST 2 PASSED: Toggling incomplete task in Rmode moves it to Done column with strikethrough.")

        # =======================================================
        # TEST 3: Synchronization to Working Plan Tool
        # =======================================================
        log("\n=== TEST 3: Verify Synchronization in Working Plan Tool ===")
        eval_js("window.TempoApp.navigateTo('plan-workspace')")
        time.sleep(1)

        wp_tasks = eval_js("""
            (() => {
                const doneSection = document.querySelector('[data-tempo-ui="done-section"]');
                const doneTasks = doneSection ? Array.from(doneSection.querySelectorAll('[data-task-row]')).map(row => ({
                    id: row.getAttribute('data-task-row'),
                    name: row.querySelector('h4')?.textContent.trim(),
                    lineThrough: row.querySelector('h4')?.classList.contains('line-through')
                })) : [];

                const activeRows = Array.from(document.querySelectorAll('#plan-workspace-task-list > div:not([data-tempo-ui="done-section"]) [data-task-row]')).map(row => ({
                    id: row.getAttribute('data-task-row'),
                    name: row.querySelector('h4')?.textContent.trim(),
                    lineThrough: row.querySelector('h4')?.classList.contains('line-through')
                }));

                return { doneTasks, activeRows };
            })()
        """)
        log("Working Plan Tool State:\n" + json.dumps(wp_tasks, indent=2))
        wp_done_names = [t["name"] for t in wp_tasks["doneTasks"]]
        assert "Marketing Research" in wp_done_names, "Marketing Research should be in WP Done section"
        assert "Event Proposal" in wp_done_names, "Event Proposal should be in WP Done section"
        assert len(wp_tasks["activeRows"]) == 1, f"Expected 1 active task (Edit Video), got {len(wp_tasks['activeRows'])}"
        assert wp_tasks["activeRows"][0]["name"] == "Edit Video", f"Expected Edit Video active, got {wp_tasks['activeRows'][0]['name']}"
        log("✓ TEST 3 PASSED: Working Plan tool is 100% synchronized with Rmode changes.")

        # =======================================================
        # TEST 4: Toggle Back to Incomplete in Working Plan Tool
        # =======================================================
        log("\n=== TEST 4: Mark 'Marketing Research' Incomplete in Working Plan Tool ===")
        eval_js("""
            (() => {
                const markActiveBtn = Array.from(document.querySelectorAll('[data-task-row="task-marketing-research"] button')).find(b => b.textContent.includes('✓'));
                if (markActiveBtn) markActiveBtn.click();
            })()
        """)
        time.sleep(1)

        # Return to Rmode
        eval_js("""
            (() => {
                window.TempoMode.setMode('recovery');
                window.TempoApp.navigateTo('today');
            })()
        """)
        time.sleep(1)

        card_state_4 = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                const doneCol = card.querySelector('[data-tempo-ui="recovery-done-column"]');
                const doneTasks = Array.from(doneCol.querySelectorAll('[data-task-id]')).map(t => t.querySelector('h5')?.textContent.trim());
                const dateCols = Array.from(card.querySelectorAll('[data-tempo-ui="recovery-date-column"]')).map(col => ({
                    dateKey: col.getAttribute('data-date-key'),
                    tasks: Array.from(col.querySelectorAll('[data-task-id]')).map(t => ({
                        name: t.querySelector('h5')?.textContent.trim(),
                        lineThrough: t.querySelector('h5')?.classList.contains('line-through')
                    }))
                }));
                return { doneTasks, dateCols };
            })()
        """)
        log("Rmode card after marking Marketing Research incomplete:\n" + json.dumps(card_state_4, indent=2))
        assert "Marketing Research" not in card_state_4["doneTasks"], "Marketing Research must NOT be in Done column"
        assert "Event Proposal" in card_state_4["doneTasks"], "Event Proposal must remain in Done column"

        mr_in_date_col = any(t["name"] == "Marketing Research" and not t["lineThrough"] for col in card_state_4["dateCols"] for t in col["tasks"])
        assert mr_in_date_col, "Marketing Research must return to scheduled date column without strikethrough"
        log("✓ TEST 4 PASSED: Reverting task in Working Plan updates Rmode dashboard card correctly!")

        # =======================================================
        # TEST 5: Refresh and Persistence
        # =======================================================
        log("\n=== TEST 5: Reload Page and Verify State Persistence ===")
        send_cmd("Page.reload")
        time.sleep(2)

        for _ in range(30):
            if eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'"):
                break
            time.sleep(0.5)

        eval_js("""
            (() => {
                window.TempoMode.setMode('recovery');
                window.TempoApp.navigateTo('today');
            })()
        """)
        time.sleep(1)

        card_state_after_reload = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                const doneCol = card.querySelector('[data-tempo-ui="recovery-done-column"]');
                const doneTasks = Array.from(doneCol.querySelectorAll('[data-task-id]')).map(t => t.querySelector('h5')?.textContent.trim());
                return { doneTasks };
            })()
        """)
        log("Rmode Done tasks after page reload: " + str(card_state_after_reload["doneTasks"]))
        assert "Event Proposal" in card_state_after_reload["doneTasks"], "Event Proposal must persist in Done column across reload"
        assert "Marketing Research" not in card_state_after_reload["doneTasks"], "Marketing Research must persist as incomplete across reload"
        log("✓ TEST 5 PASSED: Persistence across reload confirmed!")

        log("\n=======================================================")
        log("ALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
        log("=======================================================")

        ws.close()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    run()
