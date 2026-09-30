import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_mode_exclusivity_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9265
    
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

        def eval_js(expr, await_promise=False):
            params = {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": await_promise
            }
            res = send_command("Runtime.evaluate", params)
            if "exceptionDetails" in res:
                log(f"[JS ERR] {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        # Wait for page ready
        def wait_for_ready():
            for _ in range(30):
                try:
                    res = eval_js("document.readyState === 'complete' && typeof window.TempoMode !== 'undefined'")
                    if res is True:
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("TempoMode was not ready.")

        log("Waiting for page and TempoMode ready...")
        wait_for_ready()
        log("Page and TempoMode ready.")

        # Helper to get visibility state of all 4 mode dashboards on Home
        def get_home_dashboard_states():
            return eval_js("""
                (() => {
                    const dmode = document.getElementById('dmode-home-content');
                    const emode = document.getElementById('emode-home-content');
                    const rmode = document.getElementById('rmode-home-content');
                    const umode = document.getElementById('umode-home-content');

                    const isVisible = (el) => {
                        if (!el) return false;
                        return el.offsetParent !== null && el.offsetHeight > 0;
                    };

                    return {
                        currentMode: window.TempoMode.getMode(),
                        defaultVisible: isVisible(dmode),
                        urgentVisible: isVisible(emode),
                        recoveryVisible: isVisible(rmode),
                        unclearVisible: isVisible(umode),
                        dmodeHeight: dmode ? dmode.offsetHeight : 0,
                        emodeHeight: emode ? emode.offsetHeight : 0,
                        rmodeHeight: rmode ? rmode.offsetHeight : 0,
                        umodeHeight: umode ? umode.offsetHeight : 0,
                        // Check if any mode's Tempo Posts are visible
                        homepagePostsVisible: isVisible(document.getElementById('homepage-community-posts-list')),
                        urgentPostsVisible: isVisible(document.getElementById('urgent-community-posts-list')),
                        recoveryPostsVisible: isVisible(document.getElementById('recovery-community-posts-list'))
                    };
                })()
            """)

        # Clean slate: Authenticate test user and seed active urgent plan
        eval_js("""
            (() => {
                localStorage.clear();
                window.TempoRecoverySetup.resetSetupState();
            })()
        """)

        # Sign in
        eval_js("window.TempoAuth.signIn('alex.chen@university.edu', 'demo1234');", await_promise=True)
        time.sleep(0.5)
        log(f"Authenticated user: {eval_js('window.TempoAuth.getCurrentUser()?.email')}")

        # Seed an urgent plan with tasks
        eval_js("""
            (() => {
                const now = new Date();
                const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
                const testPlan = {
                    id: 'plan_mutual_test_101',
                    planId: 'plan_mutual_test_101',
                    planType: 'emergency',
                    plannedTasks: [
                        {
                            dayDate: todayStr,
                            timeSlot: '09:00 - 11:00',
                            task: { id: 'task_m1', name: 'Database Architecture Report', completed: false, isInProgress: false }
                        },
                        {
                            dayDate: todayStr,
                            timeSlot: '13:00 - 15:00',
                            task: { id: 'task_m2', name: 'Physics Problem Set 3', completed: true, isInProgress: false }
                        }
                    ],
                    availabilityDays: [{ date: todayStr, hours: 4 }]
                };
                testPlan.tasks = testPlan.plannedTasks.map(pt => pt.task);
                window.TempoPlanStore.saveActivePlan('emergency', testPlan);
            })()
        """)

        # =========================================================================
        # TEST 1: DEFAULT MODE
        # =========================================================================
        log("\n--- TEST 1: DEFAULT MODE ---")
        eval_js("window.TempoMode.setMode('default');")
        eval_js("window.TempoApp.navigateTo('today');")
        time.sleep(0.3)

        st1 = get_home_dashboard_states()
        log(f"Dashboard state in Default: {st1}")
        assert st1["currentMode"] == "default", f"Expected mode default, got {st1['currentMode']}"
        assert st1["defaultVisible"] is True, "Default Home should be visible"
        assert st1["urgentVisible"] is False, "Urgent Home MUST NOT be visible"
        assert st1["recoveryVisible"] is False, "Recovery Home MUST NOT be visible"
        assert st1["unclearVisible"] is False, "Unclear Home MUST NOT be visible"
        assert st1["urgentPostsVisible"] is False, "Urgent posts MUST NOT be visible"
        assert st1["recoveryPostsVisible"] is False, "Recovery posts MUST NOT be visible"
        log("PASS: TEST 1 — Only Default Home is visible.")

        # =========================================================================
        # TEST 2: URGENT MODE
        # =========================================================================
        log("\n--- TEST 2: URGENT MODE ---")
        eval_js("window.TempoMode.setMode('emergency');")
        eval_js("window.TempoApp.navigateTo('today');")
        time.sleep(0.3)

        st2 = get_home_dashboard_states()
        log(f"Dashboard state in Urgent: {st2}")
        assert st2["currentMode"] == "emergency", f"Expected mode emergency, got {st2['currentMode']}"
        assert st2["defaultVisible"] is False, "Default Home MUST NOT be visible"
        assert st2["urgentVisible"] is True, "Urgent Home should be visible"
        assert st2["recoveryVisible"] is False, "Recovery Home MUST NOT be visible"
        assert st2["unclearVisible"] is False, "Unclear Home MUST NOT be visible"
        assert st2["recoveryPostsVisible"] is False, "Recovery posts MUST NOT be visible"
        log("PASS: TEST 2 — Only Urgent Home is visible.")

        # =========================================================================
        # TEST 3: RECOVERY MODE
        # =========================================================================
        log("\n--- TEST 3: RECOVERY MODE ---")
        # Switch to recovery mode
        eval_js("window.TempoMode.setMode('recovery', { skipSetupCheck: true });")
        eval_js("window.TempoApp.navigateTo('today');")
        time.sleep(0.3)

        st3 = get_home_dashboard_states()
        log(f"Dashboard state in Recovery: {st3}")
        assert st3["currentMode"] == "recovery", f"Expected mode recovery, got {st3['currentMode']}"
        assert st3["defaultVisible"] is False, "Default Home MUST NOT be visible"
        assert st3["urgentVisible"] is False, "Urgent Home MUST NOT be visible"
        assert st3["recoveryVisible"] is True, "Recovery Home should be visible"
        assert st3["unclearVisible"] is False, "Unclear Home MUST NOT be visible"
        assert st3["urgentPostsVisible"] is False, "Urgent posts MUST NOT be visible"

        # Check DOM order and ensure no content from previous dashboard exists above Recovery Mode selector
        top_offset_test = eval_js("""
            (() => {
                const emode = document.getElementById('emode-home-content');
                const rmode = document.getElementById('rmode-home-content');
                const dmode = document.getElementById('dmode-home-content');
                const umode = document.getElementById('umode-home-content');

                const visibleElementsInToday = Array.from(document.getElementById('screen-today').children)
                    .filter(c => !c.classList.contains('hidden') && c.offsetHeight > 0);

                return {
                    visibleCount: visibleElementsInToday.length,
                    visibleId: visibleElementsInToday.length > 0 ? visibleElementsInToday[0].id : null,
                    emodeOffsetHeight: emode.offsetHeight,
                    dmodeOffsetHeight: dmode.offsetHeight,
                    rmodeOffsetHeight: rmode.offsetHeight
                };
            })()
        """)
        log(f"Top offset and visible children in screen-today: {top_offset_test}")
        assert top_offset_test["visibleCount"] == 1, f"Expected exactly 1 visible dashboard in screen-today, found {top_offset_test['visibleCount']}"
        assert top_offset_test["visibleId"] == "rmode-home-content", f"Visible element should be rmode-home-content, got {top_offset_test['visibleId']}"
        assert top_offset_test["emodeOffsetHeight"] == 0, "emode-home-content offsetHeight should be 0"
        assert top_offset_test["dmodeOffsetHeight"] == 0, "dmode-home-content offsetHeight should be 0"
        assert top_offset_test["rmodeOffsetHeight"] > 0, "rmode-home-content offsetHeight should be > 0"
        log("PASS: TEST 3 — Only Recovery Home is visible. No previous dashboard or Tempo Posts above it.")

        # =========================================================================
        # TEST 4: REPEATED SWITCHING WITHOUT REFRESH
        # Default -> Urgent -> Recovery -> Urgent -> Recovery -> Default
        # =========================================================================
        log("\n--- TEST 4: REPEATED SWITCHING WITHOUT REFRESH ---")
        sequence = [
            ('default', 'defaultVisible', ['urgentVisible', 'recoveryVisible', 'unclearVisible']),
            ('emergency', 'urgentVisible', ['defaultVisible', 'recoveryVisible', 'unclearVisible']),
            ('recovery', 'recoveryVisible', ['defaultVisible', 'urgentVisible', 'unclearVisible']),
            ('emergency', 'urgentVisible', ['defaultVisible', 'recoveryVisible', 'unclearVisible']),
            ('recovery', 'recoveryVisible', ['defaultVisible', 'urgentVisible', 'unclearVisible']),
            ('default', 'defaultVisible', ['urgentVisible', 'recoveryVisible', 'unclearVisible']),
            ('unclear', 'unclearVisible', ['defaultVisible', 'urgentVisible', 'recoveryVisible']),
            ('recovery', 'recoveryVisible', ['defaultVisible', 'urgentVisible', 'unclearVisible'])
        ]

        for step_idx, (target_mode, expected_visible, expected_hiddens) in enumerate(sequence, 1):
            log(f"Step {step_idx}: Switching to {target_mode}...")
            eval_js(f"window.TempoMode.setMode('{target_mode}', {{ skipSetupCheck: true }});")
            time.sleep(0.2)

            state = get_home_dashboard_states()
            assert state["currentMode"] == target_mode, f"Step {step_idx}: Mode mismatch, expected {target_mode}, got {state['currentMode']}"
            assert state[expected_visible] is True, f"Step {step_idx}: {expected_visible} should be True"
            for h in expected_hiddens:
                assert state[h] is False, f"Step {step_idx}: {h} MUST be False for mode {target_mode}"
            
            # Check exactly 1 child is visible in screen-today
            visible_children = eval_js("""
                Array.from(document.getElementById('screen-today').children)
                    .filter(c => !c.classList.contains('hidden') && c.offsetHeight > 0)
                    .map(c => c.id)
            """)
            assert len(visible_children) == 1, f"Step {step_idx}: Expected 1 visible child in screen-today, found: {visible_children}"
            log(f"  -> PASS: Mode {target_mode} shows alone (visible: {visible_children})")

        log("PASS: TEST 4 — Repeated switching cleanly displays exactly one dashboard with zero refresh.")

        # =========================================================================
        # TEST 5: DATA PRESERVATION ACROSS MODE SWITCHING
        # =========================================================================
        log("\n--- TEST 5: DATA PRESERVATION ACROSS MODE SWITCHING ---")
        # 1. In Recovery Mode, add a tracker and a Recovery Note reminder
        eval_js("""
            (() => {
                window.TempoRecoverySelfCheck.createTracker({
                    name: 'Sleep Quality',
                    category: 'supportive',
                    check_method: 'scale'
                });
                window.TempoRecoveryNote.addItem('reminder', 'Protect evening calm');
            })()
        """)

        # 2. Switch away to Urgent Mode
        eval_js("window.TempoMode.setMode('emergency');")
        time.sleep(0.2)
        # Verify Urgent Plan data is intact
        active_plan = eval_js("window.TempoPlanStore.getActivePlan('emergency')")
        assert active_plan is not None, "Active urgent plan should be intact"
        assert len(active_plan['plannedTasks']) == 2, "Urgent plan tasks should be preserved"
        log("PASS: Urgent plan tasks intact after switching away from Recovery.")

        # 3. Switch away to Default Mode
        eval_js("window.TempoMode.setMode('default');")
        time.sleep(0.2)

        # 4. Switch back to Recovery Mode
        eval_js("window.TempoMode.setMode('recovery', { skipSetupCheck: true });")
        time.sleep(0.2)

        # Verify Recovery Note and Trackers are still intact
        trackers = eval_js("window.TempoRecoverySelfCheck.getTrackers()")
        note_data = eval_js("window.TempoRecoveryNote.getNote()")
        has_sleep_tracker = any(t['name'] == 'Sleep Quality' for t in trackers)
        has_reminder = any(it['type'] == 'reminder' and it['text'] == 'Protect evening calm' for it in note_data.get('items', []))

        assert has_sleep_tracker is True, "User tracker 'Sleep Quality' should survive mode switches"
        assert has_reminder is True, "Recovery Note reminder 'Protect evening calm' should survive mode switches"
        log("PASS: Recovery trackers and Recovery Note reminders preserved across mode switches.")

        # 5. Verify task checkbox in Recovery Mode Today section preserves state and re-renders Recovery cleanly
        eval_js("window.TempoMode.toggleTaskCompletion('task_m1');")
        time.sleep(0.2)
        post_toggle_state = get_home_dashboard_states()
        assert post_toggle_state["recoveryVisible"] is True, "Recovery Home must remain visible after task toggle"
        assert post_toggle_state["urgentVisible"] is False, "Urgent Home must NOT appear after task toggle"
        assert post_toggle_state["defaultVisible"] is False, "Default Home must NOT appear after task toggle"
        log("PASS: Task toggle in Recovery Mode maintains Recovery Home visibility without reverting to Default or Urgent.")

        log("\n=======================================================")
        log("ALL MODE MUTUAL EXCLUSIVITY SMOKE TESTS PASSED! (100%)")
        log("=======================================================")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            pass

if __name__ == "__main__":
    run_tests()
