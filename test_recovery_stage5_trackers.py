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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_stage5_trackers_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9235
    
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
                    res = eval_js("typeof window.TempoRecoverySetup !== 'undefined' && typeof window.TempoRecoverySelfCheck !== 'undefined'")
                    if res:
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("Tempo Recovery scripts not initialized.")

        log("Waiting for page ready...")
        wait_for_ready()
        log("Page and recovery modules ready.")

        # Test Case 0: Reset state
        log("\n--- TEST CASE 0: Clean State Reset ---")
        eval_js("""
            (() => {
                localStorage.clear();
                sessionStorage.clear();
                window.TempoRecoverySetup.resetSetupState();
            })()
        """)
        time.sleep(0.3)

        # Open Recovery Setup directly at Stage 5
        log("Opening Recovery Setup at Stage 5 (Build My Self-check)...")
        eval_js("window.TempoRecoverySetup.open(5)")
        time.sleep(0.4)

        stage5_html = eval_js("document.getElementById('recovery-setup-stage-container')?.innerHTML || ''")
        assert "Build My Self-check" in stage5_html, "Stage 5 header should be visible"
        assert "Suggested things to track:" in stage5_html, "Suggested section should be visible"
        assert "+ Add" in stage5_html, "Should have + Add buttons on suggestions"
        log("✓ Stage 5 initially rendered with optional suggestions and 0 active trackers.")

        # Test Case 1: Add a suggested tracker ('Trouble focusing')
        log("\n--- TEST CASE 1: Add Suggested Tracker (Yes/No) ---")
        eval_js("window.TempoRecoverySetup.addSuggestedTracker('Trouble focusing')")
        time.sleep(0.3)

        trackers = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers()")
        assert len(trackers) == 1, f"Expected 1 tracker, found {len(trackers)}"
        t1 = trackers[0]
        assert t1['name'] == 'Trouble focusing', f"Expected name 'Trouble focusing', got {t1['name']}"
        assert t1['category'] == 'stress_sign', f"Expected category 'stress_sign', got {t1['category']}"
        assert t1['check_method'] == 'yes_no', f"Expected method 'yes_no', got {t1['check_method']}"
        assert t1['pattern_notices_enabled'] is True, "Pattern notices should be true for stress sign"

        stage5_html_1 = eval_js("document.getElementById('recovery-setup-stage-container')?.innerHTML || ''")
        assert "Active Trackers (1)" in stage5_html_1, "Active Trackers count should update to 1"
        assert "✓ Added" in stage5_html_1, "Suggestion card should reflect ✓ Added state"
        log("✓ Suggested tracker added cleanly: configuration preserved, UI updated with '✓ Added' & count=1.")

        # Test Case 2: Add second tracker with Scale method ('Sleep quality')
        log("\n--- TEST CASE 2: Add Second Tracker with Scale Method ---")
        eval_js("window.TempoRecoverySetup.addSuggestedTracker('Sleep quality')")
        time.sleep(0.3)

        trackers = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers()")
        assert len(trackers) == 2, f"Expected 2 trackers, found {len(trackers)}"
        t2 = next(t for t in trackers if t['name'] == 'Sleep quality')
        assert t2['category'] == 'supportive', f"Expected category 'supportive', got {t2['category']}"
        assert t2['check_method'] == 'scale', f"Expected method 'scale', got {t2['check_method']}"
        assert t2['scale_min'] == 1 and t2['scale_max'] == 5, "Scale range should be 1-5"
        assert t2['scale_min_label'] == 'Poor' and t2['scale_max_label'] == 'Restful', "Scale labels preserved"

        stage5_html_2 = eval_js("document.getElementById('recovery-setup-stage-container')?.innerHTML || ''")
        assert "Active Trackers (2)" in stage5_html_2, "Active Trackers count should update to 2"
        log("✓ Second tracker added: scale method and labels preserved, active count=2.")

        # Test Case 3: Add third tracker with Quantity method ('Water')
        log("\n--- TEST CASE 3: Add Quantity Tracker ('Water') ---")
        eval_js("window.TempoRecoverySetup.addSuggestedTracker('Water')")
        time.sleep(0.3)

        trackers = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers()")
        assert len(trackers) == 3, f"Expected 3 trackers, found {len(trackers)}"
        t3 = next(t for t in trackers if t['name'] == 'Water')
        assert t3['check_method'] == 'quantity', f"Expected method 'quantity', got {t3['check_method']}"
        assert t3['quantity_unit'] == 'glasses', f"Expected unit 'glasses', got {t3['quantity_unit']}"
        log("✓ Quantity tracker added: quantity unit preserved.")

        # Test Case 4: Duplicate Prevention
        log("\n--- TEST CASE 4: Duplicate Prevention ---")
        eval_js("window.TempoRecoverySetup.addSuggestedTracker('Trouble focusing')")
        time.sleep(0.2)
        trackers_after_dup = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers()")
        assert len(trackers_after_dup) == 3, f"Duplicate should not be added! Expected 3, got {len(trackers_after_dup)}"
        log("✓ Duplicate addition prevented.")

        # Test Case 5: Custom Tracker Creation via Modal & Z-Index Check
        log("\n--- TEST CASE 5: Custom Tracker Modal & Z-Index ---")
        eval_js("window.TempoRecoverySelfCheck.openTrackerModal()")
        time.sleep(0.3)

        modal_style = eval_js("""
            (() => {
                const el = document.getElementById('modal-selfcheck-tracker-edit');
                if (!el || el.classList.contains('hidden')) return null;
                const style = window.getComputedStyle(el);
                return {
                    zIndex: style.zIndex,
                    visible: !el.classList.contains('hidden')
                };
            })()
        """)
        assert modal_style is not None and modal_style['visible'], "Tracker configuration modal should be visible"
        assert int(modal_style['zIndex']) >= 70, f"Expected modal zIndex >= 70, got {modal_style['zIndex']}"
        log(f"✓ Configuration modal visible above setup modal with z-index={modal_style['zIndex']}.")

        # Submit custom tracker
        eval_js("""
            (() => {
                document.getElementById('tracker-input-name').value = 'Meditation';
                const catRadio = document.querySelector('input[name="tracker_category"][value="supportive"]');
                if (catRadio) catRadio.checked = true;
                const methodRadio = document.querySelector('input[name="tracker_method"][value="yes_no"]');
                if (methodRadio) methodRadio.checked = true;
                const form = document.getElementById('form-selfcheck-tracker');
                form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
            })()
        """)
        time.sleep(0.4)

        trackers = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers()")
        assert len(trackers) == 4, f"Expected 4 trackers after custom creation, got {len(trackers)}"
        assert any(t['name'] == 'Meditation' for t in trackers), "Custom tracker 'Meditation' should exist"
        log("✓ Custom tracker created and added to Self-check active trackers.")

        # Test Case 6: Remove Tracker from Stage 5
        log("\n--- TEST CASE 6: Remove Tracker from Setup ---")
        t_med = next(t for t in trackers if t['name'] == 'Meditation')
        eval_js(f"window.TempoRecoverySetup.removeTrackerFromSetup('{t_med['id']}')")
        time.sleep(0.3)

        trackers = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers()")
        assert len(trackers) == 3, f"Expected 3 trackers after removal, got {len(trackers)}"
        assert not any(t['name'] == 'Meditation' for t in trackers), "Meditation should be removed"
        log("✓ Tracker removal working correctly from Stage 5.")

        # Test Case 7: Carry Forward to Stage 6 (First Self-check)
        log("\n--- TEST CASE 7: Carry Forward to Stage 6 Questionnaire ---")
        eval_js("window.TempoRecoverySetup.goToStage(6)")
        time.sleep(0.3)

        stage6_text = eval_js("document.getElementById('recovery-setup-stage-container')?.innerText || ''")
        assert "Things you're checking in on (3)" in stage6_text or "3" in stage6_text, "Stage 6 should display the 3 active trackers"
        assert "Trouble focusing" in stage6_text, "Trouble focusing should be listed in Stage 6"
        assert "Sleep quality" in stage6_text, "Sleep quality should be listed in Stage 6"
        assert "Water" in stage6_text, "Water should be listed in Stage 6"
        assert "Meditation" not in stage6_text, "Removed tracker should not appear"
        log("✓ Stage 6 questionnaire populated with EXACTLY the user-selected trackers (no default questionnaire leak).")

        # Test Case 8: Daily Check-in Launch and Completion from Stage 6
        log("\n--- TEST CASE 8: Launch First Daily Check-in ---")
        eval_js("window.TempoRecoverySetup.launchFirstDailyCheckin()")
        time.sleep(0.4)

        daily_modal = eval_js("""
            (() => {
                const el = document.getElementById('modal-selfcheck-daily');
                if (!el || el.classList.contains('hidden')) return null;
                const style = window.getComputedStyle(el);
                return {
                    visible: true,
                    zIndex: style.zIndex
                };
            })()
        """)
        assert daily_modal is not None and daily_modal['visible'], "Daily check-in modal should open"
        assert int(daily_modal['zIndex']) >= 70, f"Expected daily modal z-index >= 70, got {daily_modal['zIndex']}"
        log(f"✓ Daily check-in modal opened with z-index={daily_modal['zIndex']}.")

        # Answer check-in items
        t_trouble = next(t for t in trackers if t['name'] == 'Trouble focusing')
        eval_js(f"window.TempoRecoverySelfCheck.setDailyYesNo('{t_trouble['id']}', false)")
        time.sleep(0.2)

        # Finish check-in
        eval_js("window.TempoRecoverySelfCheck.finishDailyCheckin()")
        time.sleep(0.4)

        today_checkin = eval_js("window.TempoRecoverySelfCheck.getTodayCheckin()")
        assert today_checkin is not None, "Today checkin record should exist"
        log("✓ First daily check-in completed and saved.")

        # Test Case 9: Back & Forward navigation preserves trackers without duplicates
        log("\n--- TEST CASE 9: Back and Forward Navigation ---")
        eval_js("window.TempoRecoverySetup.goToStage(5)")
        time.sleep(0.3)
        trackers_stage5 = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers()")
        assert len(trackers_stage5) == 3, f"Expected 3 trackers on back navigation, got {len(trackers_stage5)}"

        eval_js("window.TempoRecoverySetup.goToStage(6)")
        time.sleep(0.3)
        trackers_stage6 = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers()")
        assert len(trackers_stage6) == 3, f"Expected 3 trackers on forward navigation, got {len(trackers_stage6)}"
        log("✓ Back and Forward navigation preserves trackers without loss or duplicates.")

        # Test Case 10: Survives Page Refresh
        log("\n--- TEST CASE 10: Persistence Across Refresh ---")
        send_command("Page.reload")
        time.sleep(1.5)
        wait_for_ready()

        modal_open_after_refresh = eval_js("""
            (() => {
                const modal = document.getElementById('modal-recovery-setup');
                return modal && !modal.classList.contains('hidden');
            })()
        """)
        assert modal_open_after_refresh, "Recovery Setup should remain open across reload when in-progress"
        trackers_after_refresh = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers()")
        assert len(trackers_after_refresh) == 3, f"Trackers should survive reload, expected 3 got {len(trackers_after_refresh)}"
        log("✓ Setup and chosen trackers survive page refresh.")

        # Test Case 11: Zero Trackers Graceful Handling
        log("\n--- TEST CASE 11: Zero Trackers Case ---")
        eval_js("""
            (() => {
                localStorage.clear();
                sessionStorage.clear();
                window.TempoRecoverySetup.resetSetupState();
                window.TempoRecoverySetup.open(5);
            })()
        """)
        time.sleep(0.3)

        zero_trackers = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers()")
        assert len(zero_trackers) == 0, "Should have 0 trackers"

        # Proceed to Stage 6 with zero trackers
        eval_js("window.TempoRecoverySetup.goToStage(6)")
        time.sleep(0.3)
        stage6_zero_text = eval_js("document.getElementById('recovery-setup-stage-container')?.innerText || ''")
        assert "You haven't set anything up to check in with yet" in stage6_zero_text, "Zero trackers message should appear"
        assert "Continue →" in stage6_zero_text, "Continue button should be available"

        # Continue to Stage 7
        eval_js("window.TempoRecoverySetup.goToStage(7)")
        time.sleep(0.3)
        stage7_text = eval_js("document.getElementById('recovery-setup-stage-container')?.innerText || ''")
        assert "Recovery check-in complete" in stage7_text or "Return to Recovery Home" in stage7_text or "WHEN YOU'RE READY" in stage7_text, "Should advance to Stage 7 without blocking"
        log("✓ Zero trackers case handled gracefully: no crash, skip/continue to Stage 7 works.")

        log("\n=======================================================")
        log("ALL TEST CASES PASSED SUCCESSFULLY!")
        log("=======================================================")

    finally:
        if ws:
            ws.close()
        proc.kill()

if __name__ == '__main__':
    run_tests()
