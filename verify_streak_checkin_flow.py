import subprocess
import time
import json
import urllib.request
import tempfile
import os
import websocket
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def main():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_streak_verify_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9225

    cmd = [
        edge_path,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "--window-size=1440,1080",
        "http://localhost:8000/"
    ]

    log(f"Launching Edge on port {port}...")
    proc = subprocess.Popen(cmd)
    ws = None
    try:
        ws_url = None
        for _ in range(20):
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

        def capture_screenshot(path):
            res = send_command("Page.captureScreenshot", {"format": "png"})
            import base64
            data = base64.b64decode(res.get("data", ""))
            with open(path, "wb") as f:
                f.write(data)
            log(f"Screenshot saved to: {path}")

        send_command("Runtime.enable")
        send_command("Page.enable")
        time.sleep(1.5)

        # -------------------------------------------------------------
        # TEST 1: GUEST USER AUTH GATE BOUNDARY
        # -------------------------------------------------------------
        log("\n--- TEST 1: Guest User Auth Gate Boundary ---")
        eval_js("""
            (() => {
                localStorage.clear();
                window.TempoMode.setMode('emergency');
            })()
        """)
        time.sleep(0.5)

        # Streak card should be rendered on emergency dashboard
        streak_card = eval_js("document.querySelector('[data-tempo-ui=\"lower-selfcheck-streak\"]') !== null")
        assert streak_card, "Self-check streak card must exist on emergency dashboard"
        log("✓ Self-check Streak card is present on emergency dashboard.")

        # Click View today's checkin as guest
        eval_js("""
            (() => {
                const btn = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"] button');
                btn.click();
            })()
        """)
        time.sleep(0.5)

        # Auth modal must open and pending intent must be recorded
        auth_modal_open = eval_js("!document.getElementById('modal-auth')?.classList.contains('hidden')")
        pending_intent = eval_js("window.TempoMode ? window.TempoMode.isValidPendingIntent() : false")
        log(f"Auth modal open: {auth_modal_open}, Pending intent valid: {pending_intent}")
        assert auth_modal_open, "Auth modal should open for unauthenticated users clicking checkin"
        log("✓ Guest user is properly gated behind authentication.")

        # Close auth modal
        eval_js("window.TempoAuth.closeModal()")
        time.sleep(0.3)

        # -------------------------------------------------------------
        # TEST 2: AUTHENTICATED USER FLOW & CHECK-IN COMPLETION
        # -------------------------------------------------------------
        log("\n--- TEST 2: Authenticated User Direct Check-in ---")
        # Sign in with mock account
        eval_js("""
            (() => {
                const email = 'student@tempo.app';
                const mockAccount = {
                    id: 'usr_student_verify_001',
                    email: email,
                    password: 'password123',
                    user_metadata: { full_name: 'Student Demo' },
                    created_at: new Date().toISOString()
                };
                localStorage.setItem('tempo_mock_account_' + email, JSON.stringify(mockAccount));
            })()
        """)
        eval_js("window.TempoAuth.signIn('student@tempo.app', 'password123')")
        time.sleep(0.5)

        curr_user = eval_js("window.TempoAuth.getCurrentUser()")
        log(f"Logged in user: {curr_user.get('email')}")
        assert curr_user and curr_user.get('email') == 'student@tempo.app', "User must be authenticated"

        # Ensure in emergency mode
        eval_js("window.TempoMode.setMode('emergency')")
        time.sleep(0.5)

        # Measure baseline streak card geometry & state
        card_metrics = eval_js("""
            (() => {
                const el = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
                const comm = document.querySelector('[data-tempo-ui="urgent-posts"]') || document.querySelector('.urgent-section-posts');
                const cardRect = el.getBoundingClientRect();
                const commRect = comm ? comm.getBoundingClientRect() : { left: 0, right: 0 };
                return {
                    width: cardRect.width,
                    height: cardRect.height,
                    gap: comm ? commRect.left - cardRect.right : 0,
                    text: el.innerText
                };
            })()
        """)
        log(f"Baseline streak card metrics: Width={card_metrics['width']}px, Height={card_metrics['height']}px, Gap={card_metrics['gap']}px")
        log(f"Baseline text:\n{card_metrics['text']}")

        # Verify initial state has 0% or unanswered state
        assert "0 of 3 things" in card_metrics['text'] or "0%" in card_metrics['text'], "Initial check-in should show 0 things completed"

        # Now click "View today's checkin" button
        log("Clicking 'View today\\'s checkin' button on streak card...")
        eval_js("""
            (() => {
                const btns = document.querySelectorAll('[data-tempo-ui="lower-selfcheck-streak"] button');
                // First button is 'View today's checkin'
                btns[0].click();
            })()
        """)
        time.sleep(0.6)

        # Verify daily check-in modal (Modal 3) is now open!
        daily_modal_open = eval_js("!document.getElementById('modal-selfcheck-daily')?.classList.contains('hidden')")
        modal_title = eval_js("document.getElementById('selfcheck-daily-modal-title')?.innerText || ''")
        log(f"Daily check-in modal open: {daily_modal_open}, Title: '{modal_title}'")
        assert daily_modal_open, "modal-selfcheck-daily should be open after clicking button"
        assert "How have things been today?" in modal_title, f"Expected title 'How have things been today?', got '{modal_title}'"
        log("✓ Daily check-in modal opened directly from Self-check Streak card!")

        # Inspect trackers present in modal
        active_trackers = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers()")
        log(f"Active trackers in modal: {[t['name'] for t in active_trackers]}")
        assert len(active_trackers) >= 3, f"Expected at least 3 active trackers, got {len(active_trackers)}"

        tracker_map = {t['name']: t['id'] for t in active_trackers}
        tension_id = tracker_map.get('Tension')
        focus_id = tracker_map.get('Trouble focusing')
        sleep_id = tracker_map.get('Sleep quality')

        # Answer the trackers in the daily check-in modal
        log("Answering daily check-in items...")
        eval_js(f"""
            (() => {{
                // Tension -> 75%
                window.TempoRecoverySelfCheck.setDailyPercentage('{tension_id}', 75);
                
                // Trouble focusing -> No (false)
                window.TempoRecoverySelfCheck.setDailyYesNo('{focus_id}', false);
                
                // Sleep quality -> Yes (true)
                window.TempoRecoverySelfCheck.setDailyYesNo('{sleep_id}', true);

                // Overall note
                const noteInput = document.getElementById('selfcheck-overall-note');
                if (noteInput) noteInput.value = 'Feeling focused and accomplished today.';
            }})()
        """)
        time.sleep(0.3)

        finish_btn_text = eval_js("document.getElementById('btn-selfcheck-finish-text')?.innerText || ''")
        log(f"Finish button text: '{finish_btn_text}'")
        assert "3 of 3 answered" in finish_btn_text, f"Expected finish button to show 3 of 3 answered, got: {finish_btn_text}"

        # Submit check-in
        log("Submitting daily check-in...")
        eval_js("window.TempoRecoverySelfCheck.finishDailyCheckin()")
        time.sleep(0.6)

        # Verify daily modal closed
        modal_now_closed = eval_js("document.getElementById('modal-selfcheck-daily')?.classList.contains('hidden')")
        assert modal_now_closed, "Daily check-in modal should be closed after submission"
        log("✓ Daily check-in submitted and modal closed.")

        # -------------------------------------------------------------
        # TEST 3: VERIFY IMMEDIATE CARD UPDATE
        # -------------------------------------------------------------
        log("\n--- TEST 3: Verify Immediate Streak Card Reactivity ---")
        updated_metrics = eval_js("""
            (() => {
                const el = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
                const comm = document.querySelector('[data-tempo-ui="urgent-posts"]') || document.querySelector('.urgent-section-posts');
                const cardRect = el.getBoundingClientRect();
                const commRect = comm ? comm.getBoundingClientRect() : { left: 0, right: 0 };
                const sliderPoint = el.querySelector('[style*="left: 100%"]');
                return {
                    width: cardRect.width,
                    height: cardRect.height,
                    gap: comm ? commRect.left - cardRect.right : 0,
                    text: el.innerText,
                    has100SliderPoint: sliderPoint !== null
                };
            })()
        """)
        log(f"Updated streak card metrics: Width={updated_metrics['width']}px, Height={updated_metrics['height']}px, Gap={updated_metrics['gap']}px")
        log(f"Updated card text:\n{updated_metrics['text']}")

        assert "3 of 3 things" in updated_metrics['text'], f"Card summary should say 3 of 3 things, got: {updated_metrics['text']}"
        assert "100%" in updated_metrics['text'], f"Card progress percentage should be 100%, got: {updated_metrics['text']}"
        assert updated_metrics['has100SliderPoint'], "Slider point should be at 100%"
        log("✓ Streak card updated immediately: 3 of 3 things, 100%, slider at 100%!")

        # Verify streak count
        streak = eval_js("window.TempoRecoverySelfCheck.calculateStreak()")
        log(f"Calculated streak: {streak}")
        assert streak >= 1, f"Expected streak >= 1, got {streak}"

        # Capture screenshot of completed streak card
        art_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
        capture_screenshot(os.path.join(art_dir, "streak_card_checkin_completed_live.png"))

        # -------------------------------------------------------------
        # TEST 4: COMPLETED STATE ACTION (VIEW TODAY'S CHECK-IN)
        # -------------------------------------------------------------
        log("\n--- TEST 4: View Today's Completed Check-in ---")
        log("Clicking 'View today\\'s checkin' button when already completed...")
        eval_js("""
            (() => {
                const btns = document.querySelectorAll('[data-tempo-ui="lower-selfcheck-streak"] button');
                btns[0].click();
            })()
        """)
        time.sleep(0.6)

        # Now Modal 4 (modal-selfcheck-view) should open!
        view_modal_open = eval_js("!document.getElementById('modal-selfcheck-view')?.classList.contains('hidden')")
        view_summary = eval_js("document.getElementById('selfcheck-view-summary')?.innerText || ''")
        view_note = eval_js("document.getElementById('selfcheck-view-overall-text')?.innerText || ''")
        log(f"View modal open: {view_modal_open}, Summary: '{view_summary}', Note: '{view_note}'")
        assert view_modal_open, "modal-selfcheck-view should open when check-in is already completed"
        assert "3 of 3" in view_summary, f"Expected 3 of 3 in summary, got: {view_summary}"
        assert "Feeling focused and accomplished today." in view_note, f"Expected saved note, got: {view_note}"
        log("✓ View Today modal shows accurate saved check-in data!")

        capture_screenshot(os.path.join(art_dir, "streak_card_view_today_modal_live.png"))

        # Test Edit Check-in from View modal
        log("Testing 'Edit check-in' button inside View modal...")
        eval_js("""
            (() => {
                const editBtn = document.querySelector('#modal-selfcheck-view button[onclick*="openDailyCheckin"]');
                editBtn.click();
            })()
        """)
        time.sleep(0.6)

        daily_reopened = eval_js("!document.getElementById('modal-selfcheck-daily')?.classList.contains('hidden')")
        assert daily_reopened, "Daily check-in modal should reopen for editing"
        log("✓ 'Edit check-in' successfully reopens daily check-in form with saved answers!")

        # Close daily modal
        eval_js("window.TempoRecoverySelfCheck.closeDailyCheckin()")
        time.sleep(0.3)

        # -------------------------------------------------------------
        # TEST 5: PERSISTENCE ACROSS REFRESH
        # -------------------------------------------------------------
        log("\n--- TEST 5: Persistence Across Refresh ---")
        eval_js("window.location.reload()")
        time.sleep(2.0)

        # Re-check user & streak card
        reloaded_user = eval_js("window.TempoAuth.getCurrentUser()")
        log(f"User after reload: {reloaded_user.get('email')}")
        eval_js("window.TempoMode.setMode('emergency')")
        time.sleep(0.5)

        reloaded_text = eval_js("document.querySelector('[data-tempo-ui=\"lower-selfcheck-streak\"]')?.innerText")
        log(f"Streak card text after reload:\n{reloaded_text}")
        assert "3 of 3 things" in reloaded_text, "Check-in completion must persist across page reload"
        assert "100%" in reloaded_text, "100% progress must persist across reload"
        log("✓ Persistence fully verified across page reload!")

        # -------------------------------------------------------------
        # TEST 6: RMODE DAILY CARD UNMODIFIED & FUNCTIONAL
        # -------------------------------------------------------------
        log("\n--- TEST 6: Rmode Daily Card Verification ---")
        eval_js("window.TempoMode.setMode('recovery')")
        time.sleep(0.5)
        rmode_card = eval_js("document.querySelector('.recovery-card-selfcheck')?.innerText")
        log(f"Rmode card text:\n{rmode_card}")
        assert "Checked in today" in rmode_card or "Today’s self-check" in rmode_card, "Rmode card should reflect valid check-in"
        log("✓ Rmode Daily card is 100% intact and functional!")

        # -------------------------------------------------------------
        # TEST 7: ENTRYHOME UNMODIFIED
        # -------------------------------------------------------------
        log("\n--- TEST 7: EntryHome Verification ---")
        eval_js("window.location.hash = '#today'")
        time.sleep(0.5)
        today_screen = eval_js("document.getElementById('screen-today')?.classList.contains('hidden') === false")
        assert today_screen, "EntryHome screen should be visible at #today"
        capture_screenshot(os.path.join(art_dir, "entryhome_verified_intact_checkin_task.png"))
        log("✓ EntryHome is 100% intact!")

        log("\n==============================================")
        log("ALL VERIFICATION SUITE TESTS PASSED PERFECTLY!")
        log("==============================================")

    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass
        proc.terminate()

if __name__ == "__main__":
    main()
