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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_phase4_smoke_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9240
    
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
                    res = eval_js("typeof window.TempoSelfCheckHistory !== 'undefined' && typeof window.TempoSelfCheckPatterns !== 'undefined'")
                    if res is True:
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("TempoSelfCheckHistory or TempoSelfCheckPatterns was not initialized.")

        log("Waiting for page and scripts ready...")
        wait_for_ready()
        log("Page, TempoSelfCheckHistory, and TempoSelfCheckPatterns ready.")

        # Step 0: Clear localStorage and reset state for clean test run
        eval_js("""
            (() => {
                localStorage.clear();
                window.TempoRecoverySetup.resetSetupState();
            })()
        """)

        # TEST 1: Mode Switch & Recovery Home Initialization
        log("\n--- TEST 1: Mode Switch & Recovery Home Initialization ---")
        eval_js("window.TempoMode.setMode('recovery');")
        is_rmode_visible = eval_js("!document.getElementById('rmode-home-content').classList.contains('hidden')")
        assert is_rmode_visible is True, "Recovery Mode Home should be visible"
        log("PASS: Recovery Mode Home is visible.")

        # TEST 2: State 1 — 0 check-ins ("Nothing here yet")
        log("\n--- TEST 2: State 1 — 0 Check-ins ---")
        recently_html = eval_js("document.querySelector('.recovery-card-recently') ? document.querySelector('.recovery-card-recently').innerHTML : ''")
        assert "Nothing here yet" in recently_html, f"Expected State 1 text, got: {recently_html}"
        log("PASS: State 1 (Nothing here yet) rendered correctly.")

        # TEST 3: Configure Trackers and Recovery Note Items
        log("\n--- TEST 3: Configure Trackers & Recovery Note Items ---")
        setup_res = eval_js("""
            (() => {
                // Add items to Recovery Note
                const noteItem1 = window.TempoRecoveryNote.addItem('reminder', 'Take 5 deep breaths before opening email');
                const noteItem2 = window.TempoRecoveryNote.addItem('helper', 'Drink a glass of water');

                // Create Trackers
                const trkStress = window.TempoRecoverySelfCheck.createTracker({
                    name: 'Feeling tight chest',
                    category: 'stress_sign',
                    check_method: 'scale',
                    scale_min: 1,
                    scale_max: 5,
                    scale_min_label: 'Calm',
                    scale_max_label: 'Very tight',
                    direction: 'higher_concerning',
                    pattern_notices_enabled: true,
                    linked_note_item_ids: [noteItem1.id]
                });

                const trkSupport = window.TempoRecoverySelfCheck.createTracker({
                    name: 'Went outside for a walk',
                    category: 'supportive',
                    check_method: 'yes_no'
                });

                const trkNeutral = window.TempoRecoverySelfCheck.createTracker({
                    name: 'Hours of sleep',
                    category: 'neutral',
                    check_method: 'quantity',
                    quantity_unit: 'hours'
                });

                return {
                    noteItem1Id: noteItem1.id,
                    trkStressId: trkStress.id,
                    trkSupportId: trkSupport.id,
                    trkNeutralId: trkNeutral.id
                };
            })()
        """)
        trk_stress_id = setup_res['trkStressId']
        note_item1_id = setup_res['noteItem1Id']
        log(f"Configured trackers: stress={trk_stress_id}, noteItem={note_item1_id}")

        # TEST 4: State 2 — 1 Check-in ("You're just getting started")
        log("\n--- TEST 4: State 2 — 1 Check-in ---")
        test4_js = """
            (() => {
                // Seed 1 check-in for yesterday
                const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];
                const checkins = [{
                    id: 'chk_test_1',
                    user_id: 'local_user',
                    checkin_date: yesterday,
                    overall_note: 'Quiet day.',
                    completed_at: new Date().toISOString(),
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString()
                }];
                const observations = [{
                    id: 'obs_1',
                    checkin_id: 'chk_test_1',
                    tracker_id: '__TRK_ID__',
                    status: 'answered',
                    value: 2,
                    note: 'Felt okay'
                }];
                localStorage.setItem('tempo_selfcheck_checkins_local_user', JSON.stringify(checkins));
                localStorage.setItem('tempo_selfcheck_observations_local_user', JSON.stringify(observations));
                window.TempoMode.renderRmodeHome();
            })()
        """.replace('__TRK_ID__', trk_stress_id)
        eval_js(test4_js)
        recently_html = eval_js("document.querySelector('.recovery-card-recently') ? document.querySelector('.recovery-card-recently').innerHTML : ''")
        assert "You're just getting started" in recently_html, f"Expected State 2, got: {recently_html}"
        log("PASS: State 2 (You're just getting started) rendered correctly.")

        # TEST 5: State 3 — 3 Stable Check-ins (2-3 concise observations)
        log("\n--- TEST 5: State 3 — 3 Check-ins Stable Baseline ---")
        test5_js = """
            (() => {
                const day1 = '2026-09-25';
                const day2 = '2026-09-26';
                const day3 = '2026-09-27';
                const checkins = [
                    { id: 'chk_1', user_id: 'local_user', checkin_date: day1, overall_note: 'Day 1' },
                    { id: 'chk_2', user_id: 'local_user', checkin_date: day2, overall_note: 'Day 2' },
                    { id: 'chk_3', user_id: 'local_user', checkin_date: day3, overall_note: 'Day 3' }
                ];
                const observations = [
                    { id: 'obs_1', checkin_id: 'chk_1', tracker_id: '__TRK_ID__', status: 'answered', value: 2 },
                    { id: 'obs_2', checkin_id: 'chk_2', tracker_id: '__TRK_ID__', status: 'answered', value: 2 },
                    { id: 'obs_3', checkin_id: 'chk_3', tracker_id: '__TRK_ID__', status: 'answered', value: 2 }
                ];
                localStorage.setItem('tempo_selfcheck_checkins_local_user', JSON.stringify(checkins));
                localStorage.setItem('tempo_selfcheck_observations_local_user', JSON.stringify(observations));
                window.TempoMode.renderRmodeHome();
            })()
        """.replace('__TRK_ID__', trk_stress_id)
        eval_js(test5_js)
        recently_html = eval_js("document.querySelector('.recovery-card-recently') ? document.querySelector('.recovery-card-recently').innerHTML : ''")
        assert "View history" in recently_html, f"Expected 'View history' in State 3, got: {recently_html}"
        assert "Feeling tight chest" in recently_html, f"Expected tracker name in State 3, got: {recently_html}"
        log("PASS: State 3 (Normal history with concise observations) rendered correctly.")

        # TEST 6: State 4 — Elevated Stress Sign Elevates "Something to Notice"
        log("\n--- TEST 6: State 4 — Something to Notice with Linked Reminder ---")
        test6_js = """
            (() => {
                // Add earlier baseline (values: 2, 2, 2) + recent elevated (values: 4, 5, 4)
                const checkins = [
                    { id: 'chk_1', user_id: 'local_user', checkin_date: '2026-09-22', overall_note: '' },
                    { id: 'chk_2', user_id: 'local_user', checkin_date: '2026-09-23', overall_note: '' },
                    { id: 'chk_3', user_id: 'local_user', checkin_date: '2026-09-24', overall_note: '' },
                    { id: 'chk_4', user_id: 'local_user', checkin_date: '2026-09-25', overall_note: '' },
                    { id: 'chk_5', user_id: 'local_user', checkin_date: '2026-09-26', overall_note: '' },
                    { id: 'chk_6', user_id: 'local_user', checkin_date: '2026-09-27', overall_note: '' }
                ];
                const observations = [
                    { id: 'obs_1', checkin_id: 'chk_1', tracker_id: '__TRK_ID__', status: 'answered', value: 2 },
                    { id: 'obs_2', checkin_id: 'chk_2', tracker_id: '__TRK_ID__', status: 'answered', value: 2 },
                    { id: 'obs_3', checkin_id: 'chk_3', tracker_id: '__TRK_ID__', status: 'answered', value: 2 },
                    { id: 'obs_4', checkin_id: 'chk_4', tracker_id: '__TRK_ID__', status: 'answered', value: 4 },
                    { id: 'obs_5', checkin_id: 'chk_5', tracker_id: '__TRK_ID__', status: 'answered', value: 5 },
                    { id: 'obs_6', checkin_id: 'chk_6', tracker_id: '__TRK_ID__', status: 'answered', value: 4 }
                ];
                localStorage.setItem('tempo_selfcheck_checkins_local_user', JSON.stringify(checkins));
                localStorage.setItem('tempo_selfcheck_observations_local_user', JSON.stringify(observations));
                window.TempoMode.renderRmodeHome();
            })()
        """.replace('__TRK_ID__', trk_stress_id)
        eval_js(test6_js)
        notice_html = eval_js("document.querySelector('.recovery-card-something-notice') ? document.querySelector('.recovery-card-something-notice').innerHTML : ''")
        assert "SOMETHING TO NOTICE" in notice_html, f"Expected Something to Notice card, got: {notice_html}"
        assert "Take 5 deep breaths before opening email" in notice_html, f"Expected linked reminder quote, got: {notice_html}"
        assert "Quick Relief" in notice_html, "Expected Quick Relief action"
        assert "Remind me later" in notice_html, "Expected Remind me later action"
        assert "Dismiss" in notice_html, "Expected Dismiss action"
        log("PASS: Something to Notice elevated with linked Recovery Note reminder.")

        # TEST 7: Dismiss / Remind Later Suppression
        log("\n--- TEST 7: Notice Dismiss / Remind Later Suppression ---")
        eval_js(f"window.TempoSelfCheckPatterns.snoozeNotice('{trk_stress_id}');")
        is_snoozed = eval_js(f"window.TempoSelfCheckPatterns.isNoticeSuppressed('{trk_stress_id}')")
        assert is_snoozed is True, "Notice should be suppressed after snooze"
        has_notice_card = eval_js("Boolean(document.querySelector('.recovery-card-something-notice'))")
        assert has_notice_card is False, "Something to Notice card should be hidden when snoozed"
        log("PASS: Remind me later suppresses notice and returns card to standard Recently view.")

        # Clear suppression to test Dismiss
        eval_js(f"localStorage.removeItem('tempo_notice_state_local_user_{trk_stress_id}'); window.TempoMode.renderRmodeHome();")
        has_notice_card = eval_js("Boolean(document.querySelector('.recovery-card-something-notice'))")
        assert has_notice_card is True, "Notice should reappear after clearing suppression"
        eval_js(f"window.TempoSelfCheckPatterns.dismissNotice('{trk_stress_id}');")
        has_notice_card = eval_js("Boolean(document.querySelector('.recovery-card-something-notice'))")
        assert has_notice_card is False, "Something to Notice card should be hidden when dismissed"
        log("PASS: Dismiss suppresses notice and persists dismissed state.")

        # TEST 8: History Modal & Calendar Navigation
        log("\n--- TEST 8: History Modal & Calendar Navigation ---")
        eval_js("window.TempoSelfCheckHistory.open();")
        modal_visible = eval_js("!document.getElementById('modal-selfcheck-history').classList.contains('hidden')")
        assert modal_visible is True, "History modal should be visible"
        
        # Check tabs
        eval_js("window.TempoSelfCheckHistory.switchTab('weekly_reviews');")
        tab_content = eval_js("document.getElementById('selfcheck-history-content').innerHTML")
        assert "Weekly Reviews" in tab_content, "Weekly reviews tab placeholder should display"
        
        eval_js("window.TempoSelfCheckHistory.switchTab('checkins');")
        tab_content = eval_js("document.getElementById('selfcheck-history-content').innerHTML")
        assert "Your Trackers" in tab_content, "Check-ins tab should show Trackers"
        
        # Select day with check-in
        eval_js("window.TempoSelfCheckHistory.selectDate('2026-09-25');")
        day_detail = eval_js("document.getElementById('selfcheck-day-detail-panel').innerHTML")
        assert "Feeling tight chest" in day_detail, f"Expected day detail for 2026-09-25, got: {day_detail}"
        assert "Completed Check-in" in day_detail, "Expected completed check-in badge"
        log("PASS: History Modal, tabs, and day observation details function properly.")

        # TEST 9: Tracker Detail & SVG Chart
        log("\n--- TEST 9: Tracker Detail & Visual Chart ---")
        eval_js(f"window.TempoSelfCheckHistory.openTrackerDetail('{trk_stress_id}');")
        detail_html = eval_js("document.getElementById('selfcheck-history-content').innerHTML")
        assert "<svg" in detail_html, "Expected SVG chart in Tracker Detail"
        assert "Take 5 deep breaths before opening email" in detail_html, "Expected linked reminder in Tracker Detail"
        assert "Back to check-ins" in detail_html, "Expected back button"
        eval_js("window.TempoSelfCheckHistory.closeTrackerDetail();")
        overview_html = eval_js("document.getElementById('selfcheck-history-content').innerHTML")
        assert "Your Check-ins" in overview_html, "Back button returns to overview"
        eval_js("window.TempoSelfCheckHistory.close();")
        log("PASS: Tracker Detail displays inline SVG chart and linked reminder.")

        # TEST 10: Tracker Edit Modal & Recovery Note Link Selector
        log("\n--- TEST 10: Tracker Edit Modal & Note Link Selector ---")
        eval_js(f"window.TempoRecoverySelfCheck.openTrackerModal('{trk_stress_id}');")
        edit_modal_visible = eval_js("!document.getElementById('modal-selfcheck-tracker-edit').classList.contains('hidden')")
        assert edit_modal_visible is True, "Tracker edit modal should be visible"
        note_links_html = eval_js("document.getElementById('tracker-note-links-container').innerHTML")
        assert "Take 5 deep breaths before opening email" in note_links_html, "Note item should be rendered in link selector"
        is_checked = eval_js(f"document.querySelector('input[name=\"tracker_linked_note\"][value=\"{note_item1_id}\"]').checked")
        assert is_checked is True, "Linked note item should be checked"
        eval_js("window.TempoRecoverySelfCheck.closeTrackerModal();")
        log("PASS: Tracker Edit modal provides Recovery Note link selector with checked state.")

        # TEST 11: Mode Switch Resilience
        log("\n--- TEST 11: Mode Switch Resilience ---")
        eval_js("window.TempoMode.setMode('emergency');")
        is_emode_visible = eval_js("!document.getElementById('emode-home-content').classList.contains('hidden')")
        assert is_emode_visible is True, "Urgent Mode Home should be visible"
        eval_js("window.TempoMode.setMode('recovery');")
        is_rmode_visible = eval_js("!document.getElementById('rmode-home-content').classList.contains('hidden')")
        assert is_rmode_visible is True, "Recovery Mode Home should restore cleanly"
        log("PASS: Mode switching between Urgent and Recovery is smooth and preserves state.")

        log("\n=======================================================")
        log("ALL PHASE 4 SMOKE TESTS PASSED SUCCESSFULLY! (100%)")
        log("=======================================================")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()

if __name__ == "__main__":
    run_tests()
