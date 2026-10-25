import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import sys
import base64

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run():
    user_data_dir = tempfile.mkdtemp(prefix='tempo_twocol_')
    port = 9398
    proc = subprocess.Popen([
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        '--headless=new',
        f'--remote-debugging-port={port}',
        '--remote-allow-origins=*',
        f'--user-data-dir={user_data_dir}',
        '--disable-gpu',
        '--no-first-run',
        'http://localhost:8000/'
    ])
    time.sleep(2)
    try:
        pages = []
        for _ in range(30):
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
                    tabs = json.loads(resp.read().decode())
                    pages = [t for t in tabs if t.get('type') == 'page' and 'localhost' in t.get('url', '')]
                    if pages:
                        break
            except Exception:
                pass
            time.sleep(0.5)

        if not pages:
            raise RuntimeError("Browser not connected")

        ws_url = pages[0]['webSocketDebuggerUrl']
        ws = websocket.create_connection(ws_url)

        msg_id = 1
        def send_cmd(method, params=None):
            nonlocal msg_id
            cid = msg_id
            msg_id += 1
            ws.send(json.dumps({'id': cid, 'method': method, 'params': params or {}}))
            while True:
                r = json.loads(ws.recv())
                if r.get('id') == cid:
                    return r.get('result', {})

        def eval_js(expr):
            r = send_cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
            if "exceptionDetails" in r:
                log(f"JS Exception: {r['exceptionDetails']}")
            return r.get('result', {}).get('value')

        def save_screenshot(path):
            data = send_cmd("Page.captureScreenshot", {"format": "png"})
            b64 = data.get("data", "")
            if b64:
                with open(path, "wb") as f:
                    f.write(base64.b64decode(b64))
                log(f"Saved screenshot: {path}")

        def set_viewport(w, h, mobile=False):
            send_cmd('Emulation.setDeviceMetricsOverride', {'width': w, 'height': h, 'deviceScaleFactor': 1, 'mobile': mobile})
            time.sleep(0.5)

        set_viewport(1280, 900, False)

        for _ in range(30):
            if eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'"):
                break
            time.sleep(0.5)

        eval_js("""
            window.TempoMode.setMode('recovery');
            window.TempoApp.navigateTo('today');
        """)
        time.sleep(1)

        # -------------------------------------------------------------
        # TEST 1: Exactly Two Columns Side by Side (Tasks & Task Done)
        # -------------------------------------------------------------
        log("\n--- TEST 1: Exactly Two Columns Side by Side ---")
        info1 = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                const sc = card.querySelector('[data-tempo-ui="recovery-plan-scroll-container"]');
                const container = card.querySelector('[data-tempo-ui="recovery-plan-columns"]');
                const children = Array.from(container.children).map((el, i) => {
                    const r = el.getBoundingClientRect();
                    return {
                        idx: i,
                        tag: el.tagName,
                        type: el.getAttribute('data-tempo-ui') || (el.classList.contains('recovery-plan-divider') ? 'divider' : 'other'),
                        header: el.querySelector('span')?.textContent.trim() || '',
                        tasksCount: el.querySelectorAll('[data-task-id]').length,
                        width: Math.round(r.width),
                        left: Math.round(r.left),
                        right: Math.round(r.right),
                        top: Math.round(r.top),
                        bottom: Math.round(r.bottom)
                    };
                });
                return {
                    cardHeight: card.offsetHeight,
                    scHeight: sc.offsetHeight,
                    scClientWidth: sc.clientWidth,
                    scScrollWidth: sc.scrollWidth,
                    children
                };
            })()
        """)
        log("Layout info: " + json.dumps(info1, indent=2))
        assert info1["cardHeight"] == 462, f"Expected card height 462px, got {info1['cardHeight']}"
        assert info1["scHeight"] == 312, f"Expected scroll height 312px, got {info1['scHeight']}"
        
        # Check exactly 3 children in container: Left Column, Divider, Right Column
        cols = [c for c in info1["children"] if c["type"] in ["recovery-date-column", "recovery-done-column"]]
        assert len(cols) == 2, f"Expected exactly 2 columns, got {len(cols)}"
        assert cols[0]["header"] == "Tasks", f"Expected left column 'Tasks', got '{cols[0]['header']}'"
        assert cols[1]["header"] == "Task Done", f"Expected right column 'Task Done', got '{cols[1]['header']}'"
        assert cols[0]["right"] < cols[1]["left"], "Left column must be to the left of right column"
        assert cols[0]["top"] == cols[1]["top"], "Both columns must be side-by-side on the same horizontal row"
        assert abs(cols[0]["width"] - cols[1]["width"]) <= 2, f"Both columns must have consistent equal widths: {cols[0]['width']} vs {cols[1]['width']}"

        # Capture initial screenshot
        eval_js("document.querySelector('[data-tempo-ui=\"recovery-working-plan\"]').scrollIntoView({ block: 'center' })")
        time.sleep(0.5)
        shot1 = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\rmode_wp_twocol_initial.png"
        save_screenshot(shot1)

        # -------------------------------------------------------------
        # TEST 2: Task Completion Toggle & Moving Between Columns
        # -------------------------------------------------------------
        log("\n--- TEST 2: Task Completion Toggle (Tasks -> Task Done) ---")
        # Click checkbox of first task in Tasks column
        eval_js("""
            (() => {
                const leftCol = document.querySelector('[data-tempo-ui="recovery-date-column"]');
                const btn = leftCol.querySelector('[data-task-id] button');
                if (btn) btn.click();
            })()
        """)
        time.sleep(1)

        t2_state = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                const leftCol = card.querySelector('[data-tempo-ui="recovery-date-column"]');
                const doneCol = card.querySelector('[data-tempo-ui="recovery-done-column"]');
                return {
                    leftTasks: Array.from(leftCol.querySelectorAll('[data-task-id]')).map(t => ({
                        id: t.getAttribute('data-task-id'),
                        name: t.querySelector('h5')?.textContent.trim(),
                        lineThrough: t.querySelector('h5')?.classList.contains('line-through')
                    })),
                    doneTasks: Array.from(doneCol.querySelectorAll('[data-task-id]')).map(t => ({
                        id: t.getAttribute('data-task-id'),
                        name: t.querySelector('h5')?.textContent.trim(),
                        lineThrough: t.querySelector('h5')?.classList.contains('line-through'),
                        checked: t.querySelector('button')?.textContent.trim().includes('✓'),
                        badge: t.querySelector('span.rounded-full')?.textContent.trim()
                    })),
                    progressText: card.querySelector('span.shrink-0')?.textContent.trim()
                };
            })()
        """)
        log("State after completing 1 task: " + json.dumps(t2_state, indent=2))
        assert len(t2_state["doneTasks"]) == 1, f"Expected 1 task in Task Done, got {len(t2_state['doneTasks'])}"
        assert t2_state["doneTasks"][0]["lineThrough"] is True, "Completed task must have strikethrough"
        assert t2_state["doneTasks"][0]["checked"] is True, "Completed task must have checkmark"
        assert t2_state["doneTasks"][0]["badge"] == "Done"
        assert "1/" in t2_state["progressText"]

        # Now uncheck the task from Task Done column
        log("Unchecking task in Task Done column...")
        eval_js("""
            (() => {
                const doneCol = document.querySelector('[data-tempo-ui="recovery-done-column"]');
                const btn = doneCol.querySelector('[data-task-id] button');
                if (btn) btn.click();
            })()
        """)
        time.sleep(1)

        t2_revert = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                const leftCol = card.querySelector('[data-tempo-ui="recovery-date-column"]');
                const doneCol = card.querySelector('[data-tempo-ui="recovery-done-column"]');
                return {
                    leftCount: leftCol.querySelectorAll('[data-task-id]').length,
                    doneCount: doneCol.querySelectorAll('[data-task-id]').length,
                    progressText: card.querySelector('span.shrink-0')?.textContent.trim()
                };
            })()
        """)
        log("State after reverting task: " + json.dumps(t2_revert, indent=2))
        assert t2_revert["doneCount"] == 0, "Task Done must be empty again"
        assert t2_revert["leftCount"] == 3, "Tasks column must have all 3 tasks restored"
        assert "0/" in t2_revert["progressText"]

        # -------------------------------------------------------------
        # TEST 3: Independent Vertical Scrolling within Column
        # -------------------------------------------------------------
        log("\n--- TEST 3: Independent Vertical Scrolling within Column ---")
        # Load 10 tasks in plan
        eval_js("""
            (() => {
                const plan = {
                    plannedTasks: Array.from({ length: 10 }, (_, i) => ({
                        dayDate: '2026-10-21',
                        task: { id: 'task-num-' + i, name: 'Task Item #' + (i + 1), completed: false }
                    })),
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
                window.TempoMode.renderRmodeHome();
            })()
        """)
        time.sleep(0.5)

        v_scroll_info = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                const leftCol = card.querySelector('[data-tempo-ui="recovery-date-column"]');
                const doneCol = card.querySelector('[data-tempo-ui="recovery-done-column"]');
                const leftTaskList = leftCol.querySelector('.recovery-column-tasks');
                const doneTaskList = doneCol.querySelector('.recovery-column-tasks');

                const initialLeftScroll = leftTaskList.scrollTop;
                const initialDoneScroll = doneTaskList.scrollTop;
                const leftScrollable = leftTaskList.scrollHeight > leftTaskList.clientHeight;
                
                // Scroll left column
                leftTaskList.scrollTop = 120;
                const scrolledLeft = leftTaskList.scrollTop;
                const scrolledDone = doneTaskList.scrollTop;

                return {
                    cardHeight: card.offsetHeight,
                    leftScrollable,
                    initialLeftScroll,
                    scrolledLeft,
                    scrolledDone
                };
            })()
        """)
        log("Vertical scrolling info: " + json.dumps(v_scroll_info, indent=2))
        assert v_scroll_info["cardHeight"] == 462, "Card height must remain strictly 462px"
        assert v_scroll_info["leftScrollable"] is True, "Left column task list must be scrollable"
        assert v_scroll_info["scrolledLeft"] > 0, "Left column must scroll vertically"
        assert v_scroll_info["scrolledDone"] == 0, "Right column must NOT move when left column is scrolled"

        shot3 = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\rmode_wp_twocol_vertical_overflow.png"
        save_screenshot(shot3)

        # -------------------------------------------------------------
        # TEST 4: Viewport Adaptability (Tablet & Mobile Side-by-Side)
        # -------------------------------------------------------------
        log("\n--- TEST 4: Viewport Adaptability (Tablet 768x1024) ---")
        set_viewport(768, 1024, False)
        tablet_info = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                const container = card.querySelector('[data-tempo-ui="recovery-plan-columns"]');
                const cols = container.querySelectorAll('.recovery-plan-column');
                const r0 = cols[0].getBoundingClientRect();
                const r1 = cols[1].getBoundingClientRect();
                return {
                    cardHeight: card.offsetHeight,
                    sideBySide: r0.top === r1.top && r0.right < r1.left,
                    col0Width: Math.round(r0.width),
                    col1Width: Math.round(r1.width)
                };
            })()
        """)
        log("Tablet info: " + json.dumps(tablet_info, indent=2))
        assert tablet_info["cardHeight"] == 462
        assert tablet_info["sideBySide"] is True, "Columns must remain side-by-side on tablet"

        log("\n--- TEST 4B: Viewport Adaptability (Mobile 375x812) ---")
        set_viewport(375, 812, True)
        mobile_info = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                const container = card.querySelector('[data-tempo-ui="recovery-plan-columns"]');
                const cols = container.querySelectorAll('.recovery-plan-column');
                const r0 = cols[0].getBoundingClientRect();
                const r1 = cols[1].getBoundingClientRect();
                return {
                    cardHeight: card.offsetHeight,
                    sideBySide: r0.top === r1.top && r0.right <= r1.left,
                    col0Width: Math.round(r0.width),
                    col1Width: Math.round(r1.width)
                };
            })()
        """)
        log("Mobile info: " + json.dumps(mobile_info, indent=2))
        assert mobile_info["cardHeight"] == 462
        assert mobile_info["sideBySide"] is True, "Columns must remain side-by-side on mobile (do not stack vertically)"

        # -------------------------------------------------------------
        # TEST 5: Two-Way Synchronization with Working Plan Tool
        # -------------------------------------------------------------
        log("\n--- TEST 5: Two-Way Synchronization with Working Plan Tool ---")
        set_viewport(1280, 900, False)
        # Set up a known plan with 1 completed task and 2 incomplete tasks
        eval_js("""
            (() => {
                const plan = {
                    plannedTasks: [
                        {
                            dayDate: '2026-10-21',
                            startTime: '14:00',
                            endTime: '16:00',
                            task: {
                                id: 'task-marketing-research',
                                name: 'Marketing Research',
                                deadlineDate: '2026-10-21',
                                completed: false,
                                subtasks: []
                            }
                        },
                        {
                            dayDate: '2026-10-21',
                            startTime: '17:00',
                            endTime: '19:00',
                            task: {
                                id: 'task-event-proposal',
                                name: 'Event Proposal',
                                deadlineDate: '2026-10-22',
                                completed: false,
                                subtasks: []
                            }
                        },
                        {
                            dayDate: '2026-10-22',
                            startTime: '13:00',
                            endTime: '17:00',
                            task: {
                                id: 'task-edit-video',
                                name: 'Edit Video',
                                deadlineDate: '2026-10-23',
                                completed: true,
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

        sync_check = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                const leftTasks = Array.from(card.querySelectorAll('[data-tempo-ui="recovery-date-column"] [data-task-id] h5')).map(h => h.textContent.trim());
                const doneTasks = Array.from(card.querySelectorAll('[data-tempo-ui="recovery-done-column"] [data-task-id] h5')).map(h => h.textContent.trim());
                return { leftTasks, doneTasks };
            })()
        """)
        log("Sync check: " + json.dumps(sync_check, indent=2))
        assert "Marketing Research" in sync_check["leftTasks"]
        assert "Event Proposal" in sync_check["leftTasks"]
        assert "Edit Video" in sync_check["doneTasks"]

        # Navigate to working plan tool
        eval_js("window.TempoApp.navigateTo('plan-workspace')")
        time.sleep(1)

        # In Working Plan tool, toggle 'Edit Video' back to incomplete
        eval_js("""
            (() => {
                const markActiveBtn = Array.from(document.querySelectorAll('[data-task-row="task-edit-video"] button')).find(b => b.textContent.includes('✓'));
                if (markActiveBtn) {
                    markActiveBtn.click();
                } else {
                    const btn = document.querySelector('[data-task-id="task-edit-video"] button') || document.querySelector('[data-task-row="task-edit-video"] button');
                    if (btn) btn.click();
                }
            })()
        """)
        time.sleep(1)

        # Return to Rmode dashboard
        eval_js("""
            (() => {
                window.TempoMode.setMode('recovery');
                window.TempoApp.navigateTo('today');
            })()
        """)
        time.sleep(1)

        post_sync = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                const leftTasks = Array.from(card.querySelectorAll('[data-tempo-ui="recovery-date-column"] [data-task-id] h5')).map(h => h.textContent.trim());
                const doneTasks = Array.from(card.querySelectorAll('[data-tempo-ui="recovery-done-column"] [data-task-id] h5')).map(h => h.textContent.trim());
                return { leftTasks, doneTasks };
            })()
        """)
        log("Post sync check after reverting in Working Plan: " + json.dumps(post_sync, indent=2))
        assert "Edit Video" in post_sync["leftTasks"], "Reverted task must appear in Tasks column"
        assert len(post_sync["doneTasks"]) == 0, "Task Done must be empty"

        shot5 = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\rmode_wp_twocol_final.png"
        save_screenshot(shot5)

        log("\n=======================================================")
        log("🎉 ALL TWO-COLUMN RESTORATION TESTS PASSED 100%!")
        log("=======================================================")

        ws.close()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    run()
