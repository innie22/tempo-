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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_selfcheck_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9260
    
    cmd = [
        edge_path,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "--window-size=1440,900",
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

        def eval_js(expression):
            res = send_command("Runtime.evaluate", {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True
            })
            if "exceptionDetails" in res:
                raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        send_command("Runtime.enable")
        send_command("Page.enable")
        time.sleep(1)

        def wait_for_ready():
            for _ in range(30):
                try:
                    res = eval_js("Boolean(window.TempoAuth && window.TempoMode && window.TempoApp)")
                    if res is True:
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("Tempo was not initialized.")

        log("Waiting for app ready...")
        wait_for_ready()

        log("Authenticating test user...")
        eval_js("""
            (async () => {
                const mock = {
                    id: 'local_user_selfcheck',
                    email: 'selfcheck_user@tempo.edu',
                    raw_email: 'selfcheck_user@tempo.edu',
                    password: 'password123',
                    user_metadata: { full_name: 'Alex Chen', display_name: 'Alex Chen', role: 'student' }
                };
                localStorage.setItem('tempo_mock_account_selfcheck_user@tempo.edu', JSON.stringify(mock));
                if (window.TempoAuth) {
                    await window.TempoAuth.signIn("selfcheck_user@tempo.edu", "password123");
                }
            })()
        """)
        time.sleep(1)
        is_auth = eval_js("Boolean(window.TempoAuth && window.TempoAuth.getCurrentUser())")
        log(f"Authenticated status: {is_auth}")
        assert is_auth is True

        # =====================================================================
        # TEST 1: Open Self-check tool page from Recovery Mode
        # =====================================================================
        log("\n--- TEST 1: Open Self-check tool page from Recovery Mode ---")
        eval_js("window.TempoMode.setMode('recovery');")
        time.sleep(0.5)
        active_ctx = eval_js("window.TempoMode.getActiveContext()")
        log(f"Active context: {active_ctx}")
        assert active_ctx == 'recovery'

        # Navigate to stress-check screen
        eval_js("window.TempoApp.navigateTo('stress-check');")
        time.sleep(0.5)

        # Verify page elements
        page_title = (eval_js("document.querySelector('#self-check-workspace-root h1')?.textContent") or "").strip()
        log(f"Page title: {page_title}")
        assert page_title == "Tempo Self-check", f"Expected 'Tempo Self-check', got: {page_title}"

        return_home_btn = eval_js("Boolean(document.querySelector('#self-check-workspace-root button[onclick*=\"returnHome\"]')?.textContent.includes('Return Home'))")
        log(f"Return Home button exists: {return_home_btn}")
        assert return_home_btn is True

        # Check background colors
        body_bg = eval_js("document.body.style.backgroundColor")
        log(f"Body background: {body_bg}")
        assert "e6ede7" in body_bg.lower() or "rgb(230, 237, 231)" in body_bg.lower()

        # Check left column elements
        left_heading = eval_js("document.querySelector('#self-check-workspace-root span.uppercase')?.textContent")
        log(f"Left heading: {left_heading}")
        assert "Your daily check-in" in left_heading

        today_title = eval_js("document.querySelector('#self-check-workspace-root h2')?.textContent")
        log(f"Today's self-check title: {today_title}")
        assert "Today" in today_title and "self-check" in today_title.lower()

        streak_text = eval_js("document.querySelector('#self-check-workspace-root p.italic')?.textContent")
        log(f"Streak badge: {streak_text}")
        assert "streak" in streak_text.lower()

        # Check right column elements
        right_title = eval_js("Array.from(document.querySelectorAll('#self-check-workspace-root h2')).map(h => h.textContent).find(t => t.includes('Your Tracking System'))")
        log(f"Right column title: {right_title}")
        assert right_title is not None and "Your Tracking System" in right_title

        add_btn = eval_js("Boolean(document.querySelector('#self-check-workspace-root button[onclick*=\"openAddTracking\"]'))")
        clear_btn = eval_js("Boolean(document.querySelector('#self-check-workspace-root button[onclick*=\"promptClearAll\"]'))")
        log(f"Add Tracking button: {add_btn}, Clear all button: {clear_btn}")
        assert add_btn is True and clear_btn is True

        # =====================================================================
        # TEST 2: Left Column Interactions
        # =====================================================================
        log("\n--- TEST 2: Left Column Interactions ---")
        # 1. Tension slider
        initial_val = eval_js("document.getElementById('selfcheck-tension-val')?.textContent")
        log(f"Initial tension display: {initial_val}")
        eval_js("window.TempoSelfCheckWorkspace.onTensionChange(65);")
        time.sleep(0.3)
        updated_val = eval_js("document.getElementById('selfcheck-tension-val')?.textContent")
        log(f"Updated tension display: {updated_val}")
        assert updated_val == "65%"

        # 2. Sleep option toggle
        eval_js("window.TempoSelfCheckWorkspace.setSleepValue('not_good');")
        time.sleep(0.3)
        sleep_obs = eval_js("""
            (() => {
                const tr = window.TempoRecoverySelfCheck.getActiveTrackers().find(t => t.name.toLowerCase().includes('sleep'));
                return tr ? window.TempoSelfCheckWorkspace.getTodayObservation(tr.id)?.value : null;
            })()
        """)
        log(f"Sleep observation value: {sleep_obs}")
        assert sleep_obs == 'not_good'

        # 3. Walk options toggle
        eval_js("window.TempoSelfCheckWorkspace.setWalkChoice('no');")
        time.sleep(0.3)
        walk_obs = eval_js("""
            (() => {
                const tr = window.TempoRecoverySelfCheck.getActiveTrackers().find(t => t.name.toLowerCase().includes('walk'));
                return tr ? window.TempoSelfCheckWorkspace.getTodayObservation(tr.id)?.value : null;
            })()
        """)
        log(f"Walk observation value: {walk_obs}")
        assert walk_obs == 'no'

        eval_js("window.TempoSelfCheckWorkspace.setWalkChoice('yes');")
        eval_js("window.TempoSelfCheckWorkspace.setWalkMinutes(45);")
        time.sleep(0.3)
        walk_obs_45 = eval_js("""
            (() => {
                const tr = window.TempoRecoverySelfCheck.getActiveTrackers().find(t => t.name.toLowerCase().includes('walk'));
                return tr ? window.TempoSelfCheckWorkspace.getTodayObservation(tr.id)?.value : null;
            })()
        """)
        log(f"Walk observation value after 45m: {walk_obs_45}")
        assert walk_obs_45 == 45

        # 4. Note for today toggle & save
        eval_js("window.TempoSelfCheckWorkspace.toggleNoteInput();")
        time.sleep(0.2)
        note_visible = eval_js("Boolean(document.getElementById('selfcheck-today-note-textarea')) && !document.getElementById('selfcheck-today-note-box').classList.contains('hidden')")
        log(f"Note input visible: {note_visible}")
        assert note_visible is True

        eval_js("""
            (() => {
                const inp = document.getElementById('selfcheck-today-note-textarea');
                if (inp) inp.value = "Feeling relaxed after walking in the afternoon";
                window.TempoSelfCheckWorkspace.saveTodayNote();
            })()
        """)
        time.sleep(0.3)
        log("Note saved successfully.")

        # =====================================================================
        # TEST 3: Popups & Action Buttons
        # =====================================================================
        log("\n--- TEST 3: Popups & Action Buttons ---")
        # 1. My weekly report
        eval_js("window.TempoSelfCheckWorkspace.openWeeklyReport();")
        time.sleep(0.3)
        report_vis = eval_js("!document.getElementById('modal-selfcheck-weekly-report').classList.contains('hidden')")
        log(f"Weekly report modal visible: {report_vis}")
        assert report_vis is True
        eval_js("window.TempoSelfCheckWorkspace.closeWeeklyReport();")
        time.sleep(0.2)
        assert eval_js("document.getElementById('modal-selfcheck-weekly-report').classList.contains('hidden')") is True

        # 2. My Recovery notice (MUST open Recovery Note popup, NOT Tool Notes)
        eval_js("window.TempoSelfCheckWorkspace.openRecoveryNotice();")
        time.sleep(0.3)
        rec_note_modal_vis = eval_js("""
            (() => {
                const m = document.getElementById('modal-recovery-note-view');
                return Boolean(m && !m.classList.contains('hidden'));
            })()
        """)
        tool_notes_screen_vis = eval_js("""
            (() => {
                const s = document.getElementById('screen-tool-notes');
                return Boolean(s && !s.classList.contains('hidden'));
            })()
        """)
        log(f"Recovery Note modal visible: {rec_note_modal_vis}, Tool Notes screen visible: {tool_notes_screen_vis}")
        assert rec_note_modal_vis is True, "Recovery Note modal must be open"
        assert tool_notes_screen_vis is False, "Tool Notes screen MUST NOT be open"
        # Close recovery note modal
        eval_js("if (window.TempoRecoveryNote && typeof window.TempoRecoveryNote.closeViewModal === 'function') window.TempoRecoveryNote.closeViewModal();")
        time.sleep(0.2)

        # 3. View my full check placeholder popup
        eval_js("""
            (() => {
                const tr = window.TempoRecoverySelfCheck.getActiveTrackers()[0];
                window.TempoSelfCheckWorkspace.openFullCheckPlaceholder(tr ? tr.id : 'trk_1');
            })()
        """)
        time.sleep(0.3)
        full_check_vis = eval_js("!document.getElementById('modal-selfcheck-fullcheck').classList.contains('hidden')")
        log(f"Full check modal visible: {full_check_vis}")
        assert full_check_vis is True
        eval_js("window.TempoSelfCheckWorkspace.closeFullCheckPlaceholder();")
        time.sleep(0.2)
        assert eval_js("document.getElementById('modal-selfcheck-fullcheck').classList.contains('hidden')") is True

        # 4. Clear all confirmation modal
        eval_js("window.TempoSelfCheckWorkspace.promptClearAll();")
        time.sleep(0.3)
        clear_confirm_vis = eval_js("!document.getElementById('modal-selfcheck-clear-confirm').classList.contains('hidden')")
        log(f"Clear confirm modal visible: {clear_confirm_vis}")
        assert clear_confirm_vis is True
        eval_js("window.TempoSelfCheckWorkspace.closeClearConfirm();")
        time.sleep(0.2)
        assert eval_js("document.getElementById('modal-selfcheck-clear-confirm').classList.contains('hidden')") is True

        # =====================================================================
        # TEST 4: Return Home Navigation to Active Contexts
        # =====================================================================
        log("\n--- TEST 4: Return Home Navigation to Active Contexts ---")
        
        # A. From Recovery Mode
        eval_js("window.TempoMode.setMode('recovery');")
        eval_js("window.TempoApp.navigateTo('stress-check');")
        time.sleep(0.3)
        assert eval_js("!document.getElementById('screen-stress-check').classList.contains('hidden')") is True
        eval_js("window.TempoSelfCheckWorkspace.returnHome();")
        time.sleep(0.4)
        assert eval_js("window.TempoMode.getActiveContext()") == 'recovery'
        assert eval_js("!document.getElementById('rmode-home-content').classList.contains('hidden')") is True
        log("✓ Return Home from Recovery Mode verified.")

        # B. From Urgent Mode (Emergency)
        eval_js("window.TempoMode.setMode('emergency');")
        eval_js("window.TempoApp.navigateTo('stress-check');")
        time.sleep(0.3)
        assert eval_js("!document.getElementById('screen-stress-check').classList.contains('hidden')") is True
        eval_js("window.TempoSelfCheckWorkspace.returnHome();")
        time.sleep(0.4)
        assert eval_js("window.TempoMode.getActiveContext()") == 'emergency'
        assert eval_js("!document.getElementById('emode-home-content').classList.contains('hidden')") is True
        log("✓ Return Home from Urgent Mode verified.")

        # C. From Unclear Mode
        eval_js("window.TempoMode.setMode('unclear');")
        eval_js("window.TempoApp.navigateTo('stress-check');")
        time.sleep(0.3)
        assert eval_js("!document.getElementById('screen-stress-check').classList.contains('hidden')") is True
        eval_js("window.TempoSelfCheckWorkspace.returnHome();")
        time.sleep(0.4)
        assert eval_js("window.TempoMode.getActiveContext()") == 'unclear'
        assert eval_js("!document.getElementById('umode-home-content').classList.contains('hidden')") is True
        log("✓ Return Home from Unclear Mode verified.")

        # D. From Entry Home
        eval_js("window.TempoMode.setMode(null);")
        eval_js("window.TempoApp.navigateTo('stress-check');")
        time.sleep(0.3)
        assert eval_js("!document.getElementById('screen-stress-check').classList.contains('hidden')") is True
        eval_js("window.TempoSelfCheckWorkspace.returnHome();")
        time.sleep(0.4)
        assert eval_js("window.TempoMode.getActiveContext() === null || window.TempoMode.getActiveContext() === 'default'") is True
        assert eval_js("!document.getElementById('dmode-home-content').classList.contains('hidden')") is True
        log("✓ Return Home from Entry Home verified.")

        # =====================================================================
        # TEST 5: Tempo Logo Click Navigation
        # =====================================================================
        log("\n--- TEST 5: Tempo Logo Navigation ---")
        eval_js("window.TempoMode.setMode('recovery');")
        eval_js("window.TempoApp.navigateTo('stress-check');")
        time.sleep(0.3)
        eval_js("document.getElementById('brand-logo-container').click();")
        time.sleep(0.4)
        assert eval_js("window.TempoMode.getActiveContext()") == 'recovery'
        assert eval_js("!document.getElementById('rmode-home-content').classList.contains('hidden')") is True
        log("✓ Logo click returns to Recovery Mode.")

        # =====================================================================
        # TEST 6: Capture Desktop Screenshot
        # =====================================================================
        log("\n--- TEST 6: Capture Desktop Screenshot ---")
        eval_js("window.TempoMode.setMode('recovery');")
        eval_js("window.TempoApp.navigateTo('stress-check');")
        time.sleep(0.8)

        screenshot_resp = send_command("Page.captureScreenshot", {"format": "png"})
        import base64
        img_data = base64.b64decode(screenshot_resp.get("data", ""))
        screenshot_path = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\self_check_desktop_verified.png"
        with open(screenshot_path, "wb") as f:
            f.write(img_data)
        log(f"Saved verified screenshot to {screenshot_path}")

        log("\nALL SELF-CHECK PAGE TESTS PASSED SUCCESSFULLY! 🎉")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    run_tests()
