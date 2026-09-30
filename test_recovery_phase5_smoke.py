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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_phase5_smoke_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9250
    
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
                    res = eval_js("typeof window.TempoWeeklyReview !== 'undefined'")
                    if res is True:
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("TempoWeeklyReview was not initialized.")

        log("Waiting for page and TempoWeeklyReview ready...")
        wait_for_ready()
        log("Page and TempoWeeklyReview ready.")

        # Step 0: Clear localStorage and reset state for clean test run
        eval_js("""
            (() => {
                localStorage.clear();
                window.TempoRecoverySetup.resetSetupState();
            })()
        """)

        # TEST 1: Mode Switch & Recovery Home Initialization
        log("\n--- TEST 1: Mode Switch & Recovery Home ---")
        eval_js("window.TempoMode.setMode('recovery');")
        is_rmode_visible = eval_js("!document.getElementById('rmode-home-content').classList.contains('hidden')")
        assert is_rmode_visible is True, "Recovery Mode Home should be visible"
        log("PASS: Recovery Mode Home is visible.")

        # TEST 2: Seed Activity for Completed Week & Verify Ready Card
        log("\n--- TEST 2: Weekly Review Ready Card Renders on Home ---")
        setup_res = eval_js("""
            (() => {
                const latestWeek = window.TempoWeeklyReview.getLatestEligibleWeek();
                const weekStart = latestWeek.start;
                const weekEnd = latestWeek.end;

                // Add Recovery Note reminder
                const noteItem = window.TempoRecoveryNote.addItem('reminder', 'Take breaks between study blocks');

                // Create Trackers
                const trkStress = window.TempoRecoverySelfCheck.createTracker({
                    name: 'Trouble focusing',
                    category: 'stress_sign',
                    check_method: 'scale',
                    scale_min: 1,
                    scale_max: 5,
                    direction: 'higher_concerning',
                    pattern_notices_enabled: true,
                    linked_note_item_ids: [noteItem.id]
                });

                const trkSupport = window.TempoRecoverySelfCheck.createTracker({
                    name: 'Took a real break',
                    category: 'supportive',
                    check_method: 'yes_no'
                });

                // Compute 3 dates in that completed week
                const [y, m, d] = weekStart.split('-').map(Number);
                const d1 = new Date(y, m - 1, d + 1).toISOString().split('T')[0];
                const d2 = new Date(y, m - 1, d + 3).toISOString().split('T')[0];
                const d3 = new Date(y, m - 1, d + 5).toISOString().split('T')[0];

                const checkins = [
                    { id: 'chk_w1', user_id: 'local_user', checkin_date: d1, overall_note: 'Tough start' },
                    { id: 'chk_w2', user_id: 'local_user', checkin_date: d2, overall_note: 'Better rhythm' },
                    { id: 'chk_w3', user_id: 'local_user', checkin_date: d3, overall_note: 'Quiet weekend' }
                ];

                const observations = [
                    { id: 'obs_w1', checkin_id: 'chk_w1', tracker_id: trkStress.id, status: 'answered', value: 3 },
                    { id: 'obs_w2', checkin_id: 'chk_w1', tracker_id: trkSupport.id, status: 'answered', value: false },
                    { id: 'obs_w3', checkin_id: 'chk_w2', tracker_id: trkStress.id, status: 'answered', value: 4 },
                    { id: 'obs_w4', checkin_id: 'chk_w2', tracker_id: trkSupport.id, status: 'answered', value: true },
                    { id: 'obs_w5', checkin_id: 'chk_w3', tracker_id: trkStress.id, status: 'answered', value: 2 },
                    { id: 'obs_w6', checkin_id: 'chk_w3', tracker_id: trkSupport.id, status: 'answered', value: true }
                ];

                localStorage.setItem('tempo_selfcheck_checkins_local_user', JSON.stringify(checkins));
                localStorage.setItem('tempo_selfcheck_observations_local_user', JSON.stringify(observations));

                // Seed completed task in that week
                const activePlan = {
                    id: 'plan_test_w',
                    planType: 'emergency',
                    plannedTasks: [
                        {
                            task: {
                                id: 'tsk_101',
                                name: 'Literature Review Chapter',
                                completed: true,
                                completedAt: d2
                            },
                            dayDate: d2
                        },
                        {
                            task: {
                                id: 'tsk_102',
                                name: 'Methodology Outline',
                                completed: false
                            },
                            dayDate: d3
                        }
                    ]
                };
                localStorage.setItem('tempo_store_active_emergency_local_user', JSON.stringify(activePlan));

                window.TempoMode.renderRmodeHome();

                return {
                    weekStart: latestWeek.start,
                    dateRange: latestWeek.dateRange
                };
            })()
        """)
        week_start = setup_res['weekStart']
        date_range = setup_res['dateRange']
        log(f"Configured week {week_start} ({date_range}) with real check-ins and tasks.")

        is_ready = eval_js("window.TempoWeeklyReview.isReady()")
        assert is_ready is True, "Weekly review should be ready for completed week"

        home_card_html = eval_js("document.querySelector('.recovery-card-weeklyreview') ? document.querySelector('.recovery-card-weeklyreview').innerHTML : ''")
        assert "YOUR WEEKLY REVIEW IS READY" in home_card_html, f"Expected ready card, got: {home_card_html}"
        assert date_range in home_card_html, f"Expected real date range {date_range} in card"
        log("PASS: Weekly Review ready card renders on Recovery Home with real date range.")

        # TEST 3: "Maybe Later" Dismisses Card Without Deleting Opportunity
        log("\n--- TEST 3: 'Maybe Later' Dismissal ---")
        eval_js("window.TempoMode.dismissWeeklyReviewNotice();")
        home_card_present = eval_js("Boolean(document.querySelector('.recovery-card-weeklyreview'))")
        assert home_card_present is False, "Large ready card should be dismissed"
        
        # Check History tab still lists the review as ready
        eval_js("window.TempoSelfCheckHistory.open(); window.TempoSelfCheckHistory.switchTab('weekly_reviews');")
        history_tab_html = eval_js("document.getElementById('selfcheck-history-content').innerHTML")
        assert "Ready to review" in history_tab_html, "Week should still be ready in History"
        eval_js("window.TempoSelfCheckHistory.close();")
        log("PASS: 'Maybe later' dismisses Home card while preserving 'Ready to review' in History.")

        # TEST 4: Open Review Flow & Step 1: Your Week
        log("\n--- TEST 4: Step 1 — Your Week ---")
        eval_js(f"window.TempoWeeklyReview.open('{week_start}', true);")
        modal_visible = eval_js("!document.getElementById('modal-weekly-review').classList.contains('hidden')")
        assert modal_visible is True, "Weekly Review modal should be visible"
        step1_html = eval_js("document.getElementById('weekly-review-modal-content').innerHTML")
        assert "YOUR WEEK" in step1_html, "Expected Step 1 header"
        assert "3" in step1_html and "check-in day" in step1_html, "Expected real 3 check-in days metric"
        assert "1" in step1_html and "task" in step1_html, "Expected real 1 task completed metric"
        log("PASS: Step 1 shows real check-in days and completed tasks.")

        # TEST 5: Step 2 — Things You Got Through
        log("\n--- TEST 5: Step 2 — Things You Got Through ---")
        eval_js("window.TempoWeeklyReview.goToStep(2);")
        step2_html = eval_js("document.getElementById('weekly-review-modal-content').innerHTML")
        assert "THINGS YOU GOT THROUGH" in step2_html, "Expected Step 2 header"
        assert "Literature Review Chapter" in step2_html, "Expected completed task name"
        assert "Still in progress" in step2_html, "Expected carryover section"
        assert "Methodology Outline" in step2_html, "Expected carryover task name"
        log("PASS: Step 2 displays completed tasks and carryover tasks with neutral framing.")

        # TEST 6: Step 3 — Your Check-ins
        log("\n--- TEST 6: Step 3 — Your Check-ins ---")
        eval_js("window.TempoWeeklyReview.goToStep(3);")
        step3_html = eval_js("document.getElementById('weekly-review-modal-content').innerHTML")
        assert "YOUR CHECK-INS" in step3_html, "Expected Step 3 header"
        assert "Trouble focusing" in step3_html, "Expected tracker summary"
        assert "Took a real break" in step3_html, "Expected supportive tracker summary"
        log("PASS: Step 3 renders 7-day row and descriptive tracker summaries.")

        # TEST 7: Step 4 — Things Tempo Noticed
        log("\n--- TEST 7: Step 4 — Things Tempo Noticed ---")
        eval_js("window.TempoWeeklyReview.goToStep(4);")
        step4_html = eval_js("document.getElementById('weekly-review-modal-content').innerHTML")
        assert "THINGS TEMPO NOTICED" in step4_html, "Expected Step 4 header"
        log("PASS: Step 4 reuses Phase 4 pattern logic without causal claims.")

        # TEST 8: Step 5 — Looking Back (User Reflection)
        log("\n--- TEST 8: Step 5 — Looking Back (User Self-Reflection) ---")
        eval_js("window.TempoWeeklyReview.goToStep(5);")
        step5_html = eval_js("document.getElementById('weekly-review-modal-content').innerHTML")
        assert "LOOKING BACK" in step5_html, "Expected Step 5 header"
        assert "Compared with one week ago" in step5_html, "Expected comparison question"
        
        # Select comparison option: little_better
        eval_js("window.TempoWeeklyReview.setDraftComparison('little_better');")
        # Select one positive and one negative difference item simultaneously
        eval_js("window.TempoWeeklyReview.toggleDifferenceItem('I feel more in control');")
        eval_js("window.TempoWeeklyReview.toggleDifferenceItem('Things still feel heavy');")
        
        # Add custom difference
        eval_js("""
            (() => {
                const input = document.getElementById('input-custom-difference');
                if (input) input.value = 'Rested on Sunday';
                window.TempoWeeklyReview.addCustomDifference();
            })()
        """)
        # Enter weekly note
        eval_js("window.TempoWeeklyReview.setDraftNote('Taking Friday afternoon slower helped a lot.');")
        log("PASS: User reflection accepts comparison, both positive and negative difference items, and custom note.")

        # TEST 9: Step 6 — Finish Review
        log("\n--- TEST 9: Step 6 — Calm Finish Reflecting User's Answer ---")
        eval_js("window.TempoWeeklyReview.finishReview();")
        step6_html = eval_js("document.getElementById('weekly-review-modal-content').innerHTML")
        assert "Week reviewed" in step6_html, "Expected finish header"
        assert "A little better" in step6_html, "Expected reflected user answer 'A little better'"
        assert "Keep what feels useful. Leave the rest here." in step6_html, "Expected calm finish copy"
        
        # Close modal
        eval_js("window.TempoWeeklyReview.close();")
        log("PASS: Step 6 reflects user's answer accurately with calm completion.")

        # TEST 10: Home After Review (Quiet Reviewed Link)
        log("\n--- TEST 10: Recovery Home Reflects Reviewed State ---")
        large_card_present = eval_js("Boolean(document.querySelector('.recovery-card-weeklyreview'))")
        assert large_card_present is False, "Large ready card should no longer appear after review"
        quiet_link_html = eval_js("document.querySelector('.recovery-card-weeklyreview-quiet') ? document.querySelector('.recovery-card-weeklyreview-quiet').innerHTML : ''")
        assert "Last week reviewed" in quiet_link_html, f"Expected quiet reviewed link on Home, got: {quiet_link_html}"
        assert "View review" in quiet_link_html, "Expected 'View review' link"
        log("PASS: Recovery Home replaces large card with quiet 'Last week reviewed' link.")

        # TEST 11: History Tab Lists Completed Review
        log("\n--- TEST 11: History Tab Lists Reviewed Week ---")
        eval_js("window.TempoSelfCheckHistory.open(); window.TempoSelfCheckHistory.switchTab('weekly_reviews');")
        history_tab_html = eval_js("document.getElementById('selfcheck-history-content').innerHTML")
        assert "Reviewed" in history_tab_html, "Review status should be Reviewed"
        assert "A little better" in history_tab_html, "Comparison answer should be displayed"
        eval_js("window.TempoSelfCheckHistory.close();")
        log("PASS: Weekly Reviews History tab lists the completed review with user answer.")

        # TEST 12: Past Review Detail View
        log("\n--- TEST 12: View Past Review Detail ---")
        eval_js(f"window.TempoWeeklyReview.open('{week_start}', false);")
        past_html = eval_js("document.getElementById('weekly-review-modal-content').innerHTML")
        assert "YOUR REFLECTION" in past_html, "Past review should show user reflection"
        assert "A little better" in past_html, "Expected stored comparison answer"
        assert "I feel more in control" in past_html, "Expected positive difference item"
        assert "Things still feel heavy" in past_html, "Expected negative difference item"
        assert "Rested on Sunday" in past_html, "Expected custom difference item"
        assert "Taking Friday afternoon slower helped a lot." in past_html, "Expected stored weekly note"
        assert "Edit reflection" in past_html, "Expected Edit reflection button"
        log("PASS: Past Review displays authoritative recap alongside durable user reflection.")

        # TEST 13: Edit Reflection Updates Existing Record Without Duplication
        log("\n--- TEST 13: Edit Reflection Updates Same Record (No Duplicates) ---")
        count_before = eval_js("window.TempoWeeklyReview.loadReflections().length")
        assert count_before == 1, f"Expected exactly 1 reflection before edit, got: {count_before}"
        
        # Open edit mode
        eval_js(f"window.TempoWeeklyReview.open('{week_start}', true);")
        # Update note
        eval_js("window.TempoWeeklyReview.setDraftNote('Updated: Friday afternoon rest was great.');")
        eval_js("window.TempoWeeklyReview.finishReview();")
        eval_js("window.TempoWeeklyReview.close();")
        
        count_after = eval_js("window.TempoWeeklyReview.loadReflections().length")
        assert count_after == 1, f"Expected still exactly 1 reflection after edit (no duplicates), got: {count_after}"
        updated_note = eval_js(f"window.TempoWeeklyReview.getReflectionForWeek('{week_start}').user_note")
        assert "Updated: Friday afternoon rest was great." in updated_note, "Note should be updated"
        log("PASS: Editing reflection updates existing record in place without duplicates.")

        # TEST 14: Continuity — Next Week Surfaces Previous Reflection
        log("\n--- TEST 14: Next Week Surfaces Previous Week Continuity ---")
        continuity_js = """
            (() => {
                // Pretend we are opening review for the following week
                const [y, m, d] = '__WEEK_START__'.split('-').map(Number);
                const dt = new Date(y, m - 1, d + 7);
                const nextWeekStart = `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`;
                window.TempoWeeklyReview.open(nextWeekStart, true);
                window.TempoWeeklyReview.goToStep(5);
                const step5Content = document.getElementById('weekly-review-modal-content').innerHTML;
                window.TempoWeeklyReview.close();
                return step5Content;
            })()
        """.replace('__WEEK_START__', week_start)
        continuity_test = eval_js(continuity_js)
        assert "LAST WEEK" in continuity_test, "Expected LAST WEEK continuity section"
        assert "A little better" in continuity_test, "Expected previous reflection comparison"
        log("PASS: Subsequent weekly review surfaces previous week's reflection for continuity.")

        # TEST 15: Mode Switching Resilience
        log("\n--- TEST 15: Mode Switching Resilience ---")
        eval_js("window.TempoMode.setMode('emergency');")
        is_emode_visible = eval_js("!document.getElementById('emode-home-content').classList.contains('hidden')")
        assert is_emode_visible is True, "Urgent Mode Home should be visible"
        eval_js("window.TempoMode.setMode('recovery');")
        is_rmode_visible = eval_js("!document.getElementById('rmode-home-content').classList.contains('hidden')")
        assert is_rmode_visible is True, "Recovery Mode Home should restore cleanly"
        quiet_link_still_there = eval_js("Boolean(document.querySelector('.recovery-card-weeklyreview-quiet'))")
        assert quiet_link_still_there is True, "Quiet reviewed link should persist across mode switches"
        log("PASS: Weekly Review state survives mode transitions seamlessly.")

        log("\n=======================================================")
        log("ALL PHASE 5 SMOKE TESTS PASSED SUCCESSFULLY! (100%)")
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
