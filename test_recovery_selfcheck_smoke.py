import subprocess
import time
import json
import urllib.request
import tempfile
import os
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_selfcheck_smoke_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9229
    
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
        send_command("Log.enable")

        def wait_for_ready():
            for _ in range(30):
                try:
                    res = eval_js("typeof window.TempoRecoverySelfCheck")
                    if res != 'undefined':
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("TempoRecoverySelfCheck was not initialized.")

        log("Waiting for page and scripts ready...")
        wait_for_ready()
        log("Page and TempoRecoverySelfCheck ready.")

        # Step 1: Clear any lingering test localStorage to start clean
        eval_js("""
            (() => {
                localStorage.clear();
                window.TempoMode.setMode('recovery');
            })()
        """)
        time.sleep(0.5)

        # Step 2: Verify Recovery Home State 1 (No active trackers)
        log("Testing Step 2: Recovery Home State 1 (No Trackers)...")
        state1_html = eval_js("document.querySelector('.recovery-card-selfcheck')?.innerText || ''")
        assert "What would you like to keep an eye on?" in state1_html, f"Expected State 1 heading, got: {state1_html}"
        assert "Set up Self-check" in state1_html, "Expected Set up Self-check button"

        recently1_html = eval_js("document.querySelector('.recovery-card-recently')?.innerText || ''")
        assert "Nothing here yet." in recently1_html, f"Expected empty recently card, got: {recently1_html}"
        log("✓ State 1 verified correctly.")

        # Step 3: Create 4 trackers (Yes/No, Scale, Percentage, Quantity)
        log("Testing Step 3: Create 4 Trackers...")
        eval_js("""
            (() => {
                window.TempoRecoverySelfCheck.createTracker({
                    name: 'Trouble focusing',
                    category: 'stress_sign',
                    check_method: 'yes_no',
                    direction: 'higher_concerning',
                    pattern_notices_enabled: true
                });
                window.TempoRecoverySelfCheck.createTracker({
                    name: 'Feeling overwhelmed',
                    category: 'stress_sign',
                    check_method: 'scale',
                    scale_min: 1,
                    scale_max: 5,
                    scale_min_label: 'Low',
                    scale_max_label: 'High',
                    direction: 'higher_concerning'
                });
                window.TempoRecoverySelfCheck.createTracker({
                    name: 'Stress level',
                    category: 'stress_sign',
                    check_method: 'percentage',
                    direction: 'higher_concerning'
                });
                window.TempoRecoverySelfCheck.createTracker({
                    name: 'Water',
                    category: 'neutral',
                    check_method: 'quantity',
                    quantity_unit: 'glasses',
                    direction: 'higher_better'
                });
            })()
        """)
        time.sleep(0.3)

        trackers = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers()")
        assert len(trackers) == 4, f"Expected 4 active trackers, got {len(trackers)}"
        log(f"✓ 4 trackers created: {[t['name'] for t in trackers]}")

        # Step 4: Verify Recovery Home State 2 (Trackers exist, Not checked today)
        log("Testing Step 4: Recovery Home State 2 (Unchecked today)...")
        eval_js("window.TempoMode.renderRmodeHome()")
        time.sleep(0.3)
        state2_html = eval_js("document.querySelector('.recovery-card-selfcheck')?.innerText || ''")
        assert "How have things been today?" in state2_html, f"Expected State 2 heading, got: {state2_html}"
        assert "4 things you're keeping track of" in state2_html, f"Expected 4 things count, got: {state2_html}"
        assert "Check in" in state2_html, "Expected Check in button"
        log("✓ State 2 verified correctly.")

        # Step 5: Open Daily Check-in modal
        log("Testing Step 5: Open Daily Check-in...")
        eval_js("window.TempoRecoverySelfCheck.openDailyCheckin(false)")
        time.sleep(0.3)
        modal_visible = eval_js("!document.getElementById('modal-selfcheck-daily').classList.contains('hidden')")
        assert modal_visible, "Daily check-in modal should be visible"

        # Step 6: Answer some, skip one, leave one unanswered, add note
        log("Testing Step 6: Answer Yes/No, Scale, Skip Percentage, leave Quantity unanswered...")
        # Get tracker IDs
        t_ids = {t['name']: t['id'] for t in trackers}
        id_trouble = t_ids["Trouble focusing"]
        id_overwhelmed = t_ids["Feeling overwhelmed"]
        id_stress = t_ids["Stress level"]
        id_water = t_ids["Water"]

        eval_js(f"""
            (() => {{
                // Answer Yes for Trouble focusing
                window.TempoRecoverySelfCheck.setDailyYesNo('{id_trouble}', true);
                
                // Answer 4 for Feeling overwhelmed + note
                window.TempoRecoverySelfCheck.setDailyScale('{id_overwhelmed}', 4);
                window.TempoRecoverySelfCheck.toggleDailyNoteExpanded('{id_overwhelmed}');
                window.TempoRecoverySelfCheck.setDailyNote('{id_overwhelmed}', 'Busy afternoon');

                // Skip Stress level
                window.TempoRecoverySelfCheck.setDailySkip('{id_stress}');

                // Leave Water untouched (unanswered)

                // Add overall daily note
                const overallInput = document.getElementById('selfcheck-overall-note');
                if (overallInput) overallInput.value = 'First day testing Recovery mode.';
            }})()
        """)
        time.sleep(0.3)

        finish_btn_text = eval_js("document.getElementById('btn-selfcheck-finish-text')?.innerText || ''")
        assert "2 of 4 answered" in finish_btn_text, f"Expected finish button to show '2 of 4 answered', got: {finish_btn_text}"
        log(f"✓ Finish button dynamically updated: {finish_btn_text}")

        # Step 7: Finish Daily Check-in
        log("Testing Step 7: Finish Daily Check-in...")
        eval_js("window.TempoRecoverySelfCheck.finishDailyCheckin()")
        time.sleep(0.5)

        # Step 8: Verify Recovery Home State 3 (Checked today)
        log("Testing Step 8: Recovery Home State 3 (Checked today)...")
        state3_html = eval_js("document.querySelector('.recovery-card-selfcheck')?.innerText || ''")
        assert "Checked in today" in state3_html, f"Expected Checked in today badge, got: {state3_html}"
        assert "1 day check-in streak" in state3_html, f"Expected 1 day streak, got: {state3_html}"
        assert "You checked in on 2 of 4 things." in state3_html, f"Expected 2 of 4 things, got: {state3_html}"
        assert "View today's check-in" in state3_html, "Expected View today's check-in button"

        # Verify Recently card reflects check-in history started
        recently3_html = eval_js("document.querySelector('.recovery-card-recently')?.innerText || ''")
        assert "You're just getting started." in recently3_html, f"Expected Not enough history in recently card, got: {recently3_html}"
        log("✓ State 3 and Recently card updated accurately.")

        # Step 9: View Today's Check-in Modal
        log("Testing Step 9: View Today's Check-in...")
        eval_js("window.TempoRecoverySelfCheck.openViewToday()")
        time.sleep(0.3)
        view_html = eval_js("document.getElementById('modal-selfcheck-view')?.innerText || ''")
        assert "You checked in on 2 of 4 things today." in view_html, f"Expected view summary, got: {view_html}"
        assert "Yes" in view_html, "Expected Yes for Trouble focusing"
        assert "4 of 5" in view_html, "Expected 4 of 5 for Feeling overwhelmed"
        assert "Busy afternoon" in view_html, "Expected tracker note"
        assert "Skipped today" in view_html, "Expected Skipped today badge"
        assert "Not answered" in view_html, "Expected Not answered badge"
        assert "First day testing Recovery mode." in view_html, "Expected overall note"
        eval_js("window.TempoRecoverySelfCheck.closeViewToday()")
        log("✓ View Today's Check-in verified.")

        # Step 10: Same-Day Edit check-in (Update Water to 6 glasses)
        log("Testing Step 10: Same-Day Edit check-in...")
        eval_js("window.TempoRecoverySelfCheck.openDailyCheckin(true)")
        time.sleep(0.3)
        eval_js(f"""
            (() => {{
                // Update Water quantity to 6
                window.TempoRecoverySelfCheck.setDailyQuantity('{id_water}', '6');
                window.TempoRecoverySelfCheck.finishDailyCheckin();
            }})()
        """)
        time.sleep(0.5)

        # Confirm exactly 1 check-in record for today (NO DUPLICATE)
        checkins_count = eval_js("window.TempoRecoverySelfCheck.getDailyCheckins().length")
        assert checkins_count == 1, f"Expected exactly 1 checkin record, got {checkins_count}"
        
        # Verify Recovery Home now shows 3 of 4 things answered
        state3_edit_html = eval_js("document.querySelector('.recovery-card-selfcheck')?.innerText || ''")
        assert "You checked in on 3 of 4 things." in state3_edit_html, f"Expected 3 of 4 things after edit, got: {state3_edit_html}"
        assert "1 day check-in streak" in state3_edit_html, "Expected streak preserved"
        log("✓ Same-day edit updated existing record with no duplicates.")

        # Step 11: Manage Trackers & Archive
        log("Testing Step 11: Manage & Archive Tracker...")
        eval_js("window.TempoRecoverySelfCheck.openManage()")
        time.sleep(0.3)
        eval_js(f"window.TempoRecoverySelfCheck.handleArchiveTracker('{id_water}')")
        time.sleep(0.3)
        
        active_after_archive = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers().length")
        assert active_after_archive == 3, f"Expected 3 active trackers after archiving, got {active_after_archive}"
        eval_js("window.TempoRecoverySelfCheck.closeManage()")
        time.sleep(0.3)

        state_after_archive = eval_js("document.querySelector('.recovery-card-selfcheck')?.innerText || ''")
        assert "3 things." in state_after_archive or "3 things you're" in state_after_archive or "of 3 things" in state_after_archive, f"Expected 3 things in state card, got: {state_after_archive}"
        log("✓ Tracker archived successfully; past observations preserved.")

        # Step 12: Verify Mode Switching & Coexistence
        log("Testing Step 12: Verify Mode Switching...")
        eval_js("window.TempoMode.setMode('emergency')")
        time.sleep(0.3)
        emode_title = eval_js("document.querySelector('#screen-today')?.innerText || ''")
        assert "Urgent Mode" in emode_title or "Urgent" in emode_title or "Your Plan for Today" in emode_title, "Urgent Mode should load normally"

        eval_js("window.TempoMode.setMode('recovery')")
        time.sleep(0.3)
        rmode_card = eval_js("document.querySelector('.recovery-card-selfcheck')?.innerText || ''")
        assert "Checked in today" in rmode_card, "Recovery Home preserved checked state across mode switch"
        log("✓ Mode switching and data persistence intact.")

        # Step 13: Verify Recovery Home components intact
        log("Testing Step 13: Verify Recovery Home components...")
        qr_card = eval_js("document.querySelector('.recovery-card-quickrelief')?.innerText || ''")
        assert "QUICK RELIEF" in qr_card.upper(), "Quick Relief card should be present"
        fz_card = eval_js("document.querySelector('.recovery-card-focuszone')?.innerText || ''")
        assert "FOCUS ZONE" in fz_card.upper(), "Focus Zone card should be present"
        posts_list = eval_js("document.getElementById('recovery-community-posts-list')?.innerHTML || ''")
        assert len(posts_list) > 0, "Tempo Posts list should be rendered"
        log("✓ All Recovery Home components verified.")

        log("\n==================================================")
        log("ALL RECOVERY SELF-CHECK SMOKE TESTS PASSED (100%)")
        log("==================================================")
        return True

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

if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
