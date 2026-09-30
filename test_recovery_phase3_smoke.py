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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_phase3_smoke_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9230
    
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
                    res = eval_js("typeof window.TempoRecoverySetup")
                    if res != 'undefined':
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("TempoRecoverySetup was not initialized.")

        log("Waiting for page and scripts ready...")
        wait_for_ready()
        log("Page and TempoRecoverySetup ready.")

        # Step 0: Clear localStorage and reset state for clean test run
        eval_js("""
            (() => {
                localStorage.clear();
                window.TempoRecoverySetup.resetSetupState();
            })()
        """)
        time.sleep(0.3)

        # Step 1 & 2: Enter Recovery Mode as a first-time Recovery user -> Welcome renders
        log("Testing Step 1 & 2: First-time entry opens Recovery Welcome...")
        eval_js("window.TempoMode.setMode('recovery')")
        time.sleep(0.5)
        welcome_visible = eval_js("!document.getElementById('modal-recovery-setup').classList.contains('hidden')")
        assert welcome_visible, "Welcome setup modal should be visible for first-time recovery user"
        welcome_text = eval_js("document.getElementById('recovery-setup-stage-container')?.innerText || ''")
        assert "RECOVERY MODE" in welcome_text.upper(), "Welcome header should be visible"
        assert "Start my recovery check-in" in welcome_text, "Start button should be present"
        assert "I'll explore first" in welcome_text, "'I'll explore first' link should be present"
        log("✓ Welcome screen rendered successfully.")

        # Quick check: 'I'll explore first' enters Recovery Home without creating fake data
        log("Testing 'I'll explore first' behavior...")
        eval_js("window.TempoRecoverySetup.exploreFirst()")
        time.sleep(0.3)
        modal_hidden = eval_js("document.getElementById('modal-recovery-setup').classList.contains('hidden')")
        assert modal_hidden, "Setup modal should close after 'I'll explore first'"
        home_text = eval_js("document.querySelector('#rmode-home-content')?.innerText || ''")
        assert "How have things been today?" not in home_text, "Should not create fake trackers or checkin"
        assert "What would you like to keep an eye on?" in home_text, "Should show empty Self-check setup state"
        log("✓ 'I'll explore first' leads cleanly to Recovery Home with no fake artifacts.")

        # Step 3 & 4: Start Recovery check-in -> Looking Back (Stage 2)
        log("Testing Step 3 & 4: Looking Back selection + custom...")
        eval_js("window.TempoRecoverySetup.open(2)")
        time.sleep(0.3)
        lb_text = eval_js("document.getElementById('recovery-setup-stage-container')?.innerText || ''")
        assert "What did you notice in yourself?" in lb_text, "Looking back prompt should be visible"

        # Select 'Trouble focusing' and add custom 'Felt spaced out'
        eval_js("""
            (() => {
                window.TempoRecoverySetup.toggleLookingBack('Trouble focusing');
                const inp = document.getElementById('input-custom-looking-back');
                if (inp) {
                    inp.value = 'Felt spaced out';
                    window.TempoRecoverySetup.addCustomLookingBack();
                }
            })()
        """)
        time.sleep(0.3)
        lb_updated = eval_js("document.getElementById('recovery-setup-stage-container')?.innerText || ''")
        assert "Trouble focusing" in lb_updated, "Selected item should be shown"
        assert "Felt spaced out" in lb_updated, "Custom item should be added"
        log("✓ Looking Back selections and custom item recorded.")

        # Step 5 & 6: Continue to Stage 3 What Helped
        log("Testing Step 5 & 6: What Helped selection...")
        eval_js("window.TempoRecoverySetup.goToStage(3)")
        time.sleep(0.3)
        wh_text = eval_js("document.getElementById('recovery-setup-stage-container')?.innerText || ''")
        assert "What seemed to make things a little easier?" in wh_text, "What Helped prompt should be visible"

        # Select 'Going outside' and 'Taking a real break'
        eval_js("""
            (() => {
                window.TempoRecoverySetup.toggleWhatHelped('Going outside');
                window.TempoRecoverySetup.toggleWhatHelped('Taking a real break');
            })()
        """)
        time.sleep(0.3)
        wh_updated = eval_js("document.getElementById('recovery-setup-stage-container')?.innerText || ''")
        assert "Going outside" in wh_updated, "Going outside should be selected"
        assert "Taking a real break" in wh_updated, "Taking a real break should be selected"
        log("✓ What Helped items selected.")

        # Step 7, 8, 9: Continue to Stage 4 Recovery Note
        log("Testing Step 7, 8, 9: Recovery Note suggestions & custom reminder...")
        eval_js("window.TempoRecoverySetup.goToStage(4)")
        time.sleep(0.3)
        rn_text = eval_js("document.getElementById('recovery-setup-stage-container')?.innerText || ''")
        assert "Create your Recovery Note" in rn_text, "Recovery Note title should be present"
        assert "Trouble focusing" in rn_text, "Should suggest reflection sign 'Trouble focusing'"
        assert "Going outside" in rn_text, "Should suggest reflection helper 'Going outside'"

        # Select warning sign, helper, gentle reminder, and custom support person
        eval_js("""
            (() => {
                window.TempoRecoverySetup.toggleNoteItem('warning_sign', 'Trouble focusing');
                window.TempoRecoverySetup.toggleNoteItem('helper', 'Going outside');
                window.TempoRecoverySetup.toggleNoteItem('reminder', 'One next step is enough.');
                
                const pName = document.getElementById('input-setup-person-name');
                const pRel = document.getElementById('input-setup-person-rel');
                if (pName && pRel) {
                    pName.value = 'Nhung';
                    pRel.value = 'Friend';
                    window.TempoRecoverySetup.addSupportPersonFromSetup();
                }
            })()
        """)
        time.sleep(0.3)
        log("✓ Recovery Note items configured in draft.")

        # Step 10 & 11: Save Note and proceed to Stage 5 Build My Self-check
        log("Testing Step 10 & 11: Build My Self-check with Phase 2 tracker integration...")
        eval_js("window.TempoRecoverySetup.saveNoteAndContinue()")
        time.sleep(0.3)
        stage5_text = eval_js("document.getElementById('recovery-setup-stage-container')?.innerText || ''")
        assert "What would you like to keep track of?" in stage5_text or "Build My Self-check" in stage5_text, "Stage 5 should be active"
        
        # Verify suggestions appear from reflection (e.g. Trouble focusing / Going outside)
        assert "Trouble focusing" in stage5_text, "Should suggest Trouble focusing as tracker"

        # Add a tracker using the Phase 2 system
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
                    name: 'Going outside',
                    category: 'supportive',
                    check_method: 'yes_no',
                    direction: 'higher_better'
                });
            })()
        """)
        time.sleep(0.3)
        eval_js("window.TempoRecoverySetup.goToStage(5)") # re-render to reflect new trackers
        time.sleep(0.3)
        stage5_after = eval_js("document.getElementById('recovery-setup-stage-container')?.innerText || ''")
        assert "Active Trackers (2)" in stage5_after or "keeping track of 2 things" in stage5_after, f"Expected 2 active trackers shown, got: {stage5_after}"
        log("✓ Build My Self-check successfully integrated with Phase 2 trackers.")

        # Step 12 & 13: Stage 6 First Self-check
        log("Testing Step 12 & 13: First Self-check using Phase 2 Daily Check-in...")
        eval_js("window.TempoRecoverySetup.goToStage(6)")
        time.sleep(0.3)
        stage6_text = eval_js("document.getElementById('recovery-setup-stage-container')?.innerText || ''")
        assert "How have things been today?" in stage6_text or "Check in now" in stage6_text, "First check-in prompt should be visible"

        # Launch and complete check-in
        eval_js("window.TempoRecoverySetup.launchFirstDailyCheckin()")
        time.sleep(0.4)
        daily_visible = eval_js("!document.getElementById('modal-selfcheck-daily').classList.contains('hidden')")
        assert daily_visible, "Phase 2 Daily Self-check modal should open"

        # Fill check-in: answer Yes for Trouble focusing
        trackers = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers()")
        t_trouble = next(t for t in trackers if t['name'] == 'Trouble focusing')
        eval_js(f"window.TempoRecoverySelfCheck.setDailyYesNo('{t_trouble['id']}', true)")
        time.sleep(0.2)
        eval_js("window.TempoRecoverySelfCheck.finishDailyCheckin()")
        time.sleep(0.5)

        # Step 14: Stage 7 Recovery Check-in Complete
        log("Testing Step 14: Stage 7 Recovery Check-in Complete...")
        stage7_text = eval_js("document.getElementById('recovery-setup-stage-container')?.innerText || ''")
        assert "RECOVERY CHECK-IN COMPLETE" in stage7_text.upper(), "Stage 7 Complete title should be visible"
        assert "Back to Dashboard" in stage7_text, "Back to Dashboard button should be present"
        assert "Recovery Plan" not in stage7_text, "Must NOT create or mention a 'Recovery Plan'"
        log("✓ Stage 7 Complete verified (no 'Recovery Plan' entity created).")

        # Step 15 & 16: Back to Dashboard & Recovery Home State
        log("Testing Step 15 & 16: Back to Dashboard and Recovery Home card state...")
        eval_js("window.TempoRecoverySetup.finishAndReturnHome()")
        time.sleep(0.5)
        modal_now_hidden = eval_js("document.getElementById('modal-recovery-setup').classList.contains('hidden')")
        assert modal_now_hidden, "Setup modal should close after finishing"

        # Verify Recovery Home shows Checked in today with real streak
        rmode_text = eval_js("document.querySelector('#rmode-home-content')?.innerText || ''")
        assert "Checked in today" in rmode_text, "Recovery Home should show Checked in today"
        assert "1 day check-in streak" in rmode_text, "Streak should reflect completed check-in"
        log("✓ Recovery Home reflects real check-in state.")

        # Step 17 & 18: Recovery Note Card on Home, View & Edit Modals
        log("Testing Step 17 & 18: Recovery Note Home card, View, and Edit modals...")
        assert "RECOVERY NOTE" in rmode_text.upper() or "A NOTE TO MYSELF" in rmode_text.upper(), "Recovery Note card should be in Recovery Home"
        assert "One next step is enough." in rmode_text, "Saved reminder quote should preview on Home card"

        # Open View Modal
        eval_js("window.TempoRecoveryNote.openViewModal()")
        time.sleep(0.3)
        view_text = eval_js("document.getElementById('modal-recovery-note-view')?.innerText || ''")
        assert "My Recovery Note" in view_text, "Recovery Note view title should be present"
        assert "Trouble focusing" in view_text, "Warning sign should be visible"
        assert "Going outside" in view_text, "Helper should be visible"
        assert "One next step is enough." in view_text, "Reminder should be visible"
        assert "Nhung" in view_text, "Support person should be visible"
        log("✓ Recovery Note detail view renders all 4 sections.")

        # Open Edit Modal and add an item
        eval_js("window.TempoRecoveryNote.openEditModal()")
        time.sleep(0.3)
        edit_visible = eval_js("!document.getElementById('modal-recovery-note-edit').classList.contains('hidden')")
        assert edit_visible, "Edit modal should be open"

        eval_js("""
            (() => {
                const inp = document.getElementById('input-add-reminder');
                if (inp) {
                    inp.value = 'Slow down before deciding.';
                    window.TempoRecoveryNote.handleAddFromInput('reminder');
                }
                window.TempoRecoveryNote.closeEditModal();
            })()
        """)
        time.sleep(0.4)

        note_items = eval_js("window.TempoRecoveryNote.getItems()")
        assert any(it['text'] == 'Slow down before deciding.' for it in note_items), "New reminder should be persisted in note"
        log("✓ Recovery Note edit and direct item addition verified.")

        # Step 19: Mode switching & Returning User behavior
        log("Testing Step 19: Mode switching and returning user (no forced setup)...")
        eval_js("window.TempoMode.setMode('emergency')")
        time.sleep(0.3)
        eval_js("window.TempoMode.setMode('recovery')")
        time.sleep(0.3)

        # Returning user should NOT see the welcome modal again
        setup_modal_visible = eval_js("!document.getElementById('modal-recovery-setup').classList.contains('hidden')")
        assert not setup_modal_visible, "Returning recovery user should NOT be forced into setup modal"
        log("✓ Returning user enters Recovery Home directly without forced setup.")

        log("\n==================================================")
        log("ALL PHASE 3 RECOVERY SETUP & NOTE TESTS PASSED (100%)")
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
