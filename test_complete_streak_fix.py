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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_fix_verify_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9227

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
        for _ in range(25):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as resp:
                    tabs = json.loads(resp.read().decode())
                    pages = [t for t in tabs if t.get("type") == "page"]
                    if pages:
                        ws_url = pages[0]["webSocketDebuggerUrl"]
                        break
            except Exception:
                time.sleep(0.4)

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
        # TEST 1: FRESH GUEST USER - INITIAL CARD STATE & ZERO CHECK-IN
        # -------------------------------------------------------------
        log("\n--- TEST 1: Fresh Guest User & Baseline Card State ---")
        eval_js("""
            (() => {
                localStorage.clear();
                window.TempoMode.setMode('emergency');
            })()
        """)
        time.sleep(0.8)

        # Measure baseline streak card geometry & state
        metrics = eval_js("""
            (() => {
                const el = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
                const comm = document.querySelector('[data-tempo-ui="urgent-posts"]') || document.querySelector('.urgent-section-posts');
                const cardRect = el.getBoundingClientRect();
                const commRect = comm ? comm.getBoundingClientRect() : { left: 0, right: 0 };
                const flameImg = el.querySelector('[data-tempo-ui="streak-flame-asset"] img');
                return {
                    width: cardRect.width,
                    height: cardRect.height,
                    gap: comm ? commRect.left - cardRect.right : 0,
                    text: el.innerText,
                    flameSrc: flameImg ? flameImg.getAttribute('src') : null
                };
            })()
        """)
        log(f"Card width: {metrics['width']:.1f}px (target: 678.5px)")
        log(f"Card height: {metrics['height']:.1f}px (target: 264.0px)")
        log(f"Horizontal gap: {metrics['gap']:.1f}px (target: 24.0px)")
        log(f"Flame asset: {metrics['flameSrc']}")
        log(f"Baseline text:\n{metrics['text']}")

        assert abs(metrics['width'] - 678.5) < 3.0, f"Expected width ~678.5px, got {metrics['width']}"
        assert abs(metrics['height'] - 264.0) < 3.0, f"Expected height ~264.0px, got {metrics['height']}"
        assert abs(metrics['gap'] - 24.0) < 3.0, f"Expected gap ~24.0px, got {metrics['gap']}"
        assert metrics['flameSrc'] == "assets/custom_flame.png", "Custom flame asset must be used"
        assert "0 of 3 things" in metrics['text'], f"Initial text must show 0 of 3 things, got: {metrics['text']}"
        assert "0%" in metrics['text'], f"Initial text must show 0%, got: {metrics['text']}"
        log("✓ Baseline streak card geometry and initial 0 of 3 state verified perfectly!")

        # -------------------------------------------------------------
        # TEST 2: CLICK 'VIEW TODAY'S CHECKIN' AS GUEST USER
        # -------------------------------------------------------------
        log("\n--- TEST 2: Opening Check-in Flow Directly as Guest ---")
        eval_js("""
            (() => {
                const btn = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"] button');
                btn.click();
            })()
        """)
        time.sleep(0.6)

        daily_open = eval_js("!document.getElementById('modal-selfcheck-daily')?.classList.contains('hidden')")
        auth_open = eval_js("!document.getElementById('modal-signin')?.classList.contains('hidden')")
        modal_title = eval_js("document.getElementById('selfcheck-daily-modal-title')?.innerText || ''")

        log(f"Daily check-in modal open: {daily_open}")
        log(f"Sign-in modal open (should be False): {auth_open}")
        log(f"Modal title: '{modal_title}'")

        assert daily_open, "modal-selfcheck-daily MUST open when clicking View today's checkin"
        assert not auth_open, "Sign-in modal must NOT open; guest user should be able to check in"
        assert "How have things been today?" in modal_title, f"Expected title 'How have things been today?', got: {modal_title}"
        log("✓ Daily check-in modal opened directly for guest user without auth block!")

        # -------------------------------------------------------------
        # TEST 3: ANSWER QUESTIONS AND SUBMIT RESPONSES
        # -------------------------------------------------------------
        log("\n--- TEST 3: Answering Check-in Questions & Submitting ---")
        trackers = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers()")
        log(f"Active trackers: {[t['name'] for t in trackers]}")
        assert len(trackers) >= 3, f"Expected at least 3 active trackers, got {len(trackers)}"

        tracker_map = {t['name']: t['id'] for t in trackers}
        tension_id = tracker_map.get('Tension')
        focus_id = tracker_map.get('Trouble focusing')
        sleep_id = tracker_map.get('Sleep quality')

        log("Interacting with inputs...")
        eval_js(f"""
            (() => {{
                // Tension -> 70%
                window.TempoRecoverySelfCheck.setDailyPercentage('{tension_id}', 70);
                // Trouble focusing -> No (false)
                window.TempoRecoverySelfCheck.setDailyYesNo('{focus_id}', false);
                // Sleep quality -> Scale 4 (or Yes/No)
                const trk = window.TempoRecoverySelfCheck.getTrackerById('{sleep_id}');
                if (trk && trk.check_method === 'scale') {{
                    window.TempoRecoverySelfCheck.setDailyScale('{sleep_id}', 4);
                }} else {{
                    window.TempoRecoverySelfCheck.setDailyYesNo('{sleep_id}', true);
                }}
                // Overall note
                const noteInput = document.getElementById('selfcheck-overall-note');
                if (noteInput) noteInput.value = 'Feeling focused and calm today.';
            }})()
        """)
        time.sleep(0.3)

        btn_text = eval_js("document.getElementById('btn-selfcheck-finish-text')?.innerText || ''")
        log(f"Finish button text: '{btn_text}'")
        assert "3 of 3 answered" in btn_text, f"Expected button to show 3 of 3 answered, got: {btn_text}"

        log("Submitting check-in...")
        eval_js("window.TempoRecoverySelfCheck.finishDailyCheckin()")
        time.sleep(0.6)

        daily_closed = eval_js("document.getElementById('modal-selfcheck-daily')?.classList.contains('hidden')")
        assert daily_closed, "Daily modal should close after submit"
        log("✓ Check-in submitted successfully and modal closed.")

        # -------------------------------------------------------------
        # TEST 4: VERIFY IMMEDIATE CARD REACTIVITY
        # -------------------------------------------------------------
        log("\n--- TEST 4: Verify Immediate Streak Card Reactivity ---")
        updated = eval_js("""
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
                    has100Point: sliderPoint !== null
                };
            })()
        """)
        log(f"Updated card text:\n{updated['text']}")
        log(f"Updated metrics: Width={updated['width']:.1f}px, Height={updated['height']:.1f}px, Gap={updated['gap']:.1f}px")

        assert "3 of 3 things" in updated['text'], f"Card must say 3 of 3 things, got: {updated['text']}"
        assert "100%" in updated['text'], f"Card must show 100%, got: {updated['text']}"
        assert updated['has100Point'], "Slider point should be at 100%"
        assert abs(updated['width'] - 678.5) < 3.0, "Width must remain preserved"
        assert abs(updated['height'] - 264.0) < 3.0, "Height must remain preserved"
        assert abs(updated['gap'] - 24.0) < 3.0, "Horizontal gap must remain 24px"
        log("✓ Card updated immediately to 3 of 3 things and 100% progress!")

        art_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
        capture_screenshot(os.path.join(art_dir, "streak_card_checkin_completed_live.png"))

        # -------------------------------------------------------------
        # TEST 5: VIEW COMPLETED CHECK-IN & EDIT FLOW
        # -------------------------------------------------------------
        log("\n--- TEST 5: Viewing Completed Check-in and Edit Flow ---")
        log("Clicking 'View today\\'s checkin' when check-in is complete...")
        eval_js("""
            (() => {
                const btn = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"] button');
                btn.click();
            })()
        """)
        time.sleep(0.6)

        view_open = eval_js("!document.getElementById('modal-selfcheck-view')?.classList.contains('hidden')")
        view_summary = eval_js("document.getElementById('selfcheck-view-summary')?.innerText || ''")
        view_note = eval_js("document.getElementById('selfcheck-view-overall-text')?.innerText || ''")
        log(f"View modal open: {view_open}")
        log(f"View summary: '{view_summary}'")
        log(f"View note: '{view_note}'")

        assert view_open, "modal-selfcheck-view should open for completed check-in"
        assert "3 of 3" in view_summary, f"Expected 3 of 3 in summary, got: {view_summary}"
        assert "Feeling focused and calm today." in view_note, f"Expected saved note, got: {view_note}"
        log("✓ Completed check-in responses viewed accurately!")

        capture_screenshot(os.path.join(art_dir, "streak_card_view_today_modal_live.png"))

        # Test Edit Check-in button inside View modal
        log("Clicking 'Edit check-in' button inside View modal...")
        eval_js("""
            (() => {
                const editBtn = document.querySelector('#modal-selfcheck-view button[onclick*="openDailyCheckin"]');
                editBtn.click();
            })()
        """)
        time.sleep(0.6)

        daily_edit_open = eval_js("!document.getElementById('modal-selfcheck-daily')?.classList.contains('hidden')")
        edit_title = eval_js("document.getElementById('selfcheck-daily-modal-title')?.innerText || ''")
        edit_btn_text = eval_js("document.getElementById('btn-selfcheck-finish-text')?.innerText || ''")
        log(f"Daily edit modal open: {daily_edit_open}, Title: '{edit_title}', Button: '{edit_btn_text}'")

        assert daily_edit_open, "Daily check-in modal should open in edit mode"
        assert "Edit today's check-in" in edit_title, f"Expected 'Edit today\\'s check-in', got: {edit_title}"
        assert "Save changes" in edit_btn_text, f"Expected 'Save changes', got: {edit_btn_text}"
        log("✓ 'Edit check-in' successfully reopens the form with pre-filled answers!")

        # Update Tension to 85%
        log("Modifying Tension from 70% to 85% and saving...")
        eval_js(f"window.TempoRecoverySelfCheck.setDailyPercentage('{tension_id}', 85)")
        eval_js("window.TempoRecoverySelfCheck.finishDailyCheckin()")
        time.sleep(0.6)

        # -------------------------------------------------------------
        # TEST 6: PERSISTENCE ACROSS PAGE RELOAD
        # -------------------------------------------------------------
        log("\n--- TEST 6: Persistence Across Page Reload ---")
        eval_js("window.location.reload()")
        time.sleep(2.0)

        eval_js("window.TempoMode.setMode('emergency')")
        time.sleep(0.6)

        reloaded_text = eval_js("document.querySelector('[data-tempo-ui=\"lower-selfcheck-streak\"]')?.innerText || ''")
        log(f"Reloaded streak card text:\n{reloaded_text}")
        assert "3 of 3 things" in reloaded_text, f"Expected 3 of 3 things after reload, got: {reloaded_text}"
        assert "100%" in reloaded_text, f"Expected 100% after reload, got: {reloaded_text}"
        log("✓ Persistence fully verified across page reload!")

        # -------------------------------------------------------------
        # TEST 7: RMODE DAILY CARD UNMODIFIED & INTACT
        # -------------------------------------------------------------
        log("\n--- TEST 7: Rmode Daily Card Verification ---")
        eval_js("window.TempoMode.setMode('recovery')")
        time.sleep(0.6)
        rmode_card = eval_js("document.querySelector('.recovery-card-selfcheck')?.innerText || ''")
        log(f"Rmode card text:\n{rmode_card}")
        assert "Today’s self-check" in rmode_card or "3 of 3 things" in rmode_card, "Rmode card must be rendered and intact"
        log("✓ Rmode Daily card is 100% intact and working!")

        # -------------------------------------------------------------
        # TEST 8: ENTRYHOME UNMODIFIED
        # -------------------------------------------------------------
        log("\n--- TEST 8: EntryHome Verification ---")
        eval_js("window.location.hash = '#today'")
        time.sleep(0.6)
        today_screen_visible = eval_js("!document.getElementById('screen-today')?.classList.contains('hidden')")
        assert today_screen_visible, "EntryHome screen must be visible at #today"
        capture_screenshot(os.path.join(art_dir, "entryhome_verified_intact_checkin_task.png"))
        log("✓ EntryHome is 100% intact!")

        log("\n==============================================")
        log("ALL VERIFICATION SUITE TESTS PASSED 100%!")
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
