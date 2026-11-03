import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os
import base64

sys.stdout.reconfigure(encoding='utf-8')

artifact_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
os.makedirs(artifact_dir, exist_ok=True)

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_rmode_entry_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9596

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#home"
]

proc = subprocess.Popen(cmd)
time.sleep(3.0)

targets = None
for _ in range(30):
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
        targets = json.loads(req.read().decode("utf-8"))
        if targets:
            match = [t for t in targets if t.get("type") == "page" and "127.0.0.1" in t.get("url", "")]
            if match:
                page_target = match[0]
                break
    except Exception:
        pass
    time.sleep(0.5)

if not page_target:
    print("Failed to find 127.0.0.1 page target. Available targets:", targets)
    sys.exit(1)

print("Connected to target:", page_target["url"])
ws = websocket.create_connection(page_target["webSocketDebuggerUrl"])

msg_id = 1
def send_cmd(method, params=None):
    global msg_id, ws
    cmd_obj = {"id": msg_id, "method": method, "params": params or {}}
    msg_id += 1
    ws.send(json.dumps(cmd_obj))
    while True:
        raw = ws.recv()
        res = json.loads(raw)
        if res.get("id") == cmd_obj["id"]:
            return res.get("result", {})

def eval_js(expression):
    res = send_cmd("Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True
    })
    if "exceptionDetails" in res:
        print(f"JS Exception: {res['exceptionDetails']}")
    return res.get("result", {}).get("value")

def take_screenshot(filename):
    res = send_cmd("Page.captureScreenshot", {"format": "png"})
    data = base64.b64decode(res.get("data", ""))
    target_path = os.path.join(artifact_dir, filename)
    with open(target_path, "wb") as f:
        f.write(data)
    print(f"  [Screenshot] Saved: {target_path}")

try:
    send_cmd("Page.enable")
    send_cmd("Runtime.enable")

    # Wait for page and scripts to fully initialize
    print("Waiting for page scripts (TempoRecoverySetup, TempoMode) to initialize...")
    for i in range(30):
        res = eval_js("({ ready: document.readyState, setup: typeof window.TempoRecoverySetup, mode: typeof window.TempoMode })")
        if res and res.get("setup") == "object" and res.get("mode") == "object":
            print(f"Initialized after {i*0.5}s: {res}")
            break
        time.sleep(0.5)

    print("=== STARTING RMODE ENTRY FLOW VERIFICATION ===")

    # Authenticate mock user
    eval_js("""
        (async () => {
            const u = { id: 'local_dev_alex', email: 'alex@tempo.test', user_metadata: { display_name: 'Alex' } };
            localStorage.setItem('tempo_local_dev_user', JSON.stringify(u));
            localStorage.setItem('tempo_mock_account_alex@tempo.test', JSON.stringify(u));
            if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
                await window.TempoAuth.checkSession();
            }
        })();
    """)
    time.sleep(1.0)
    auth_check = eval_js("({ user: window.TempoAuth.getCurrentUser(), isAuth: window.TempoMode.isUserAuthenticated ? window.TempoMode.isUserAuthenticated() : true })")
    print("Auth status:", auth_check)

    # -------------------------------------------------------------
    # TEST 1: New User Entry Flow (CASE 1 - Welcome to Rmode)
    # -------------------------------------------------------------
    print("\n--- TEST 1: New User Entry Flow (Case 1) ---")
    eval_js("""
        (() => {
            const uid = (window.TempoAuth && window.TempoAuth.getCurrentUserId && window.TempoAuth.getCurrentUserId()) || 'local_dev_alex';
            localStorage.removeItem(`tempo_selfcheck_trackers_${uid}`);
            localStorage.removeItem('tempo_selfcheck_trackers');
            localStorage.removeItem(`tempo_selfcheck_checkins_${uid}`);
            localStorage.removeItem('tempo_selfcheck_checkins');
            localStorage.removeItem(`tempo_selfcheck_observations_${uid}`);
            localStorage.removeItem('tempo_selfcheck_observations');
            localStorage.removeItem(`tempo_recovery_setups_${uid}`);
            localStorage.removeItem(`tempo_selfcheck_setups_${uid}`);
            localStorage.removeItem(`tempo_recovery_setup_status_${uid}`);
            localStorage.removeItem(`tempo_recovery_intro_seen_${uid}`);
            sessionStorage.removeItem(`tempo_rmode_session_welcomed_${uid}`);
            sessionStorage.removeItem(`tempo_recovery_setup_open_${uid}`);
            if (window.TempoI18n) window.TempoI18n.setLanguage('vi');
        })();
    """)

    # Check tracking status: must be isReturning == false
    status1 = eval_js("window.TempoRecoverySetup.checkUserTrackingStatus()")
    print("User tracking status for new user:", status1)
    assert not status1["isReturning"], "Expected isReturning to be False for new user"
    assert status1["activeCount"] == 0, "Expected activeCount == 0"

    # User enters Rmode
    eval_js("window.TempoMode.transitionContext('recovery')")
    time.sleep(0.5)

    # Verify modal is open and has Case 1 UI
    modal_visible = eval_js("!document.getElementById('modal-recovery-setup').classList.contains('hidden')")
    case1_ui = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case1-welcome\"]') !== null")
    title_text = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case1-welcome\"] h2')?.textContent?.trim()")
    question_text = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case1-welcome\"] h3')?.textContent?.trim()")
    print(f"Modal visible: {modal_visible}, Case 1 UI: {case1_ui}")
    print(f"Title: {title_text}")
    print(f"Question: {question_text}")

    assert modal_visible and case1_ui, "Case 1 Welcome modal should be visible"
    assert "Chào mừng" in title_text or "Hồi phục" in title_text, f"Expected Vietnamese welcome title, got: {title_text}"
    take_screenshot("rmode_case1_welcome_vi.png")

    # -------------------------------------------------------------
    # TEST 2: New User clicks "Later" / Skip Setup
    # -------------------------------------------------------------
    print("\n--- TEST 2: New User Action 'Later' ---")
    eval_js("window.TempoRecoverySetup.handleCase1Later()")
    time.sleep(0.5)

    modal_closed = eval_js("document.getElementById('modal-recovery-setup').classList.contains('hidden')")
    cur_mode = eval_js("window.TempoMode.getMode()")
    trackers_count = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers().length")
    setup_status = eval_js("(() => { const uid = (window.TempoAuth && window.TempoAuth.getCurrentUserId && window.TempoAuth.getCurrentUserId()) || 'local_dev_alex'; return localStorage.getItem('tempo_recovery_setup_status_' + uid); })()")
    session_welcomed = eval_js("(() => { const uid = (window.TempoAuth && window.TempoAuth.getCurrentUserId && window.TempoAuth.getCurrentUserId()) || 'local_dev_alex'; return sessionStorage.getItem('tempo_rmode_session_welcomed_' + uid); })()")

    print(f"Modal closed: {modal_closed}, Mode: {cur_mode}")
    print(f"Active trackers: {trackers_count}, Setup status: {setup_status}, Session welcomed: {session_welcomed}")

    assert modal_closed, "Modal should be closed after clicking Later"
    assert cur_mode == 'recovery', "Should remain on Recovery dashboard"
    assert trackers_count == 0, "No trackers should have been created"
    assert setup_status is None, "Setup status must NOT be marked completed"
    assert session_welcomed == 'true', "Session welcomed flag should be set to prevent duplicates"

    # Test navigating within Rmode: modal should NOT re-appear
    eval_js("window.TempoRecoverySetup.handleRmodeEntry()")
    time.sleep(0.3)
    modal_still_closed = eval_js("document.getElementById('modal-recovery-setup').classList.contains('hidden')")
    assert modal_still_closed, "Navigating within Rmode should not re-trigger modal in same session"

    # Now simulate switching out of Rmode to Urgent mode, then switching back to Rmode
    eval_js("window.TempoMode.transitionContext('emergency')")
    time.sleep(0.5)
    # Session flag should be cleared when leaving Rmode
    session_cleared = eval_js("(() => { const uid = (window.TempoAuth && window.TempoAuth.getCurrentUserId && window.TempoAuth.getCurrentUserId()) || 'local_dev_alex'; return sessionStorage.getItem('tempo_rmode_session_welcomed_' + uid); })()")
    print(f"After switching to emergency, session welcomed flag: {session_cleared}")
    assert session_cleared is None, "Session welcomed flag should be cleared when switching away from Rmode"

    # Switch back to Rmode: because user skipped setup and has no trackers, Case 1 modal must re-appear!
    eval_js("window.TempoMode.transitionContext('recovery')")
    time.sleep(0.5)
    reopened_case1 = eval_js("!document.getElementById('modal-recovery-setup').classList.contains('hidden') && document.querySelector('[data-tempo-ui=\"rmode-case1-welcome\"]') !== null")
    print(f"Re-entering Rmode treats user as New User again: {reopened_case1}")
    assert reopened_case1, "User should be treated as new user again upon re-entering Rmode until setup is completed"

    # -------------------------------------------------------------
    # TEST 3: New User clicks "Yes, let's set it up" -> Configures Trackers -> Navigates to Self-check
    # -------------------------------------------------------------
    print("\n--- TEST 3: New User Setup Flow ('Yes, let's set it up') ---")
    eval_js("window.TempoRecoverySetup.startNewUserSetupFlow()")
    time.sleep(0.5)

    current_stage = eval_js("document.querySelector('button[onclick*=\"saveNewUserSetupAndGoToSelfCheck\"]') !== null")
    print(f"Stage 5 setup container loaded: {current_stage}")
    assert current_stage, "Setup should navigate to tracking items configuration"

    # Add candidate trackers
    eval_js("""
        (() => {
            window.TempoRecoverySelfCheck.createTracker({
                name: 'Căng thẳng',
                category: 'stress_sign',
                check_method: 'percentage'
            });
            window.TempoRecoverySelfCheck.createTracker({
                name: 'Giấc ngủ',
                category: 'supportive',
                check_method: 'scale',
                scale_min: 1,
                scale_max: 5
            });
            window.TempoRecoverySetup.goToStage(5);
        })();
    """)
    time.sleep(0.3)
    active_now = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers().length")
    print(f"Added trackers: {active_now}")
    assert active_now == 2, "Expected 2 active trackers configured"

    # Click 'Save configuration & go to Self-check'
    eval_js("window.TempoRecoverySetup.saveNewUserSetupAndGoToSelfCheck()")
    time.sleep(0.5)

    # Verify setup marked completed and navigated to Self-check tool (#stress-check)
    setup_status_after = eval_js("(() => { const uid = (window.TempoAuth && window.TempoAuth.getCurrentUserId && window.TempoAuth.getCurrentUserId()) || 'local_dev_alex'; return localStorage.getItem('tempo_recovery_setup_status_' + uid); })()")
    current_hash = eval_js("window.location.hash")
    stress_check_visible = eval_js("!document.getElementById('screen-stress-check').classList.contains('hidden')")
    print(f"Setup status after save: {setup_status_after}, Current hash: {current_hash}, Screen stress-check visible: {stress_check_visible}")
    assert setup_status_after == 'completed', "Setup status should be marked completed"
    assert current_hash == '#stress-check' and stress_check_visible, "Should navigate to Self-check tool page"

    # Verify return to Rmode Dashboard from Self-check tool
    return_label = eval_js("document.getElementById('selfcheck-return-home-text')?.textContent?.trim()")
    print(f"Self-check return link label: {return_label}")
    eval_js("window.TempoSelfCheckWorkspace.returnHome()")
    time.sleep(0.5)
    home_hash = eval_js("window.location.hash")
    home_visible = eval_js("!document.getElementById('screen-today').classList.contains('hidden')")
    print(f"After returnHome: hash={home_hash}, screen-today visible={home_visible}")
    assert home_hash == '#home' or home_visible, "Should return to Rmode dashboard"

    # -------------------------------------------------------------
    # TEST 4: Returning User Flow (CASE 2 - Welcome Back Modal)
    # -------------------------------------------------------------
    print("\n--- TEST 4: Returning User Entry Flow (Case 2) ---")
    # Clear session guard to simulate a new entry into Rmode for returning user
    eval_js("(() => { const uid = (window.TempoAuth && window.TempoAuth.getCurrentUserId && window.TempoAuth.getCurrentUserId()) || 'local_dev_alex'; sessionStorage.removeItem('tempo_rmode_session_welcomed_' + uid); })()")
    status2 = eval_js("window.TempoRecoverySetup.checkUserTrackingStatus()")
    print("User tracking status for returning user:", status2)
    assert status2["isReturning"], "User should now be detected as Returning User"
    assert status2["activeCount"] == 2, "Active trackers count should be 2"

    # User enters Rmode
    eval_js("window.TempoMode.transitionContext('recovery')")
    time.sleep(0.5)

    case2_ui = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case2-welcome\"]') !== null")
    case2_title = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case2-welcome\"] h2')?.textContent?.trim()")
    case2_question = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case2-welcome\"] p.text-sm')?.textContent?.trim()")
    case2_summary = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case2-welcome\"] p.text-xs')?.textContent?.trim()")
    print(f"Case 2 UI visible: {case2_ui}")
    print(f"Case 2 title: {case2_title}")
    print(f"Case 2 question: {case2_question}")
    print(f"Case 2 summary: {case2_summary}")

    assert case2_ui, "Case 2 Welcome Back modal should be visible"
    assert "quay lại" in case2_title.lower() or "welcome back" in case2_title.lower(), "Expected welcome back title"
    assert "2 mục" in case2_summary or "2 active" in case2_summary, "Expected 2 active items in summary"
    take_screenshot("rmode_case2_welcome_vi.png")

    # -------------------------------------------------------------
    # TEST 5: Returning User clicks "No, go to dashboard"
    # -------------------------------------------------------------
    print("\n--- TEST 5: Returning User Action 'No, go to dashboard' ---")
    eval_js("window.TempoRecoverySetup.handleCase2GoToDashboard()")
    time.sleep(0.5)

    modal_closed2 = eval_js("document.getElementById('modal-recovery-setup').classList.contains('hidden')")
    cur_trackers = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers().length")
    print(f"Modal closed: {modal_closed2}, Active trackers intact: {cur_trackers}")
    assert modal_closed2, "Modal should close"
    assert cur_trackers == 2, "Active trackers must remain completely untouched"

    # -------------------------------------------------------------
    # TEST 6: Returning User clicks "Yes, review my system" -> Option A (Keep current system)
    # -------------------------------------------------------------
    print("\n--- TEST 6: Returning User Review System -> Option A (Keep) ---")
    eval_js("window.TempoRecoverySetup.open('case2_welcome', { force: true })")
    time.sleep(0.3)
    eval_js("window.TempoRecoverySetup.openTrackingSystemReview()")
    time.sleep(0.5)

    review_ui = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case2-review\"]') !== null")
    review_title = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case2-review\"] h2')?.textContent?.trim()")
    print(f"Review interface visible: {review_ui}, Title: {review_title}")
    assert review_ui, "Tracking System Review interface should be visible"
    take_screenshot("rmode_case2_review_vi.png")

    # Click Option A (Keep current system)
    eval_js("window.TempoRecoverySetup.executeKeepCurrentSystem()")
    time.sleep(0.5)

    modal_closed3 = eval_js("document.getElementById('modal-recovery-setup').classList.contains('hidden')")
    sc_visible = eval_js("!document.getElementById('screen-stress-check').classList.contains('hidden')")
    trackers_kept = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers().length")
    print(f"Option A executed: Modal closed={modal_closed3}, Self-check visible={sc_visible}, Trackers kept={trackers_kept}")
    assert modal_closed3 and sc_visible, "Option A should navigate to Self-check tool"
    assert trackers_kept == 2, "Option A must not alter active trackers"

    # Return to home
    eval_js("window.TempoSelfCheckWorkspace.returnHome()")
    time.sleep(0.3)

    # -------------------------------------------------------------
    # TEST 7: Returning User Review System -> Option B (Adjust my system)
    # -------------------------------------------------------------
    print("\n--- TEST 7: Returning User Review System -> Option B (Adjust) ---")
    eval_js("window.TempoRecoverySetup.open('case2_review', { force: true })")
    time.sleep(0.3)
    eval_js("window.TempoRecoverySetup.startAdjustmentFlowFromReview()")
    time.sleep(0.5)

    # Verify adjustment draft has the trackers
    draft_trackers_count = eval_js("document.querySelectorAll('#recovery-setup-stage-container button[onclick*=\"toggleTrackerKept\"]').length")
    print(f"Adjust trackers screen loaded with buttons: {draft_trackers_count}")
    assert draft_trackers_count >= 2, "Adjustment screen should list existing trackers with toggle/edit controls"

    # Add a new tracker in adjustment
    eval_js("""
        (() => {
            window.TempoRecoverySelfCheck.createTracker({
                name: 'Đi bộ',
                category: 'supportive',
                check_method: 'yes_no'
            });
            window.TempoRecoverySetup.executeAdjustSetupConfirm();
        })();
    """)
    time.sleep(0.5)
    modal_closed4 = eval_js("document.getElementById('modal-recovery-setup').classList.contains('hidden')")
    sc_visible2 = eval_js("!document.getElementById('screen-stress-check').classList.contains('hidden')")
    new_active_count = eval_js("window.TempoRecoverySelfCheck.getActiveTrackers().length")
    print(f"Option B confirmed: Modal closed={modal_closed4}, Self-check visible={sc_visible2}, New active count={new_active_count}")
    assert modal_closed4 and sc_visible2, "Option B should navigate to Self-check tool after confirmation"
    assert new_active_count == 3, "New tracker should be added"

    eval_js("window.TempoSelfCheckWorkspace.returnHome()")
    time.sleep(0.3)

    # -------------------------------------------------------------
    # TEST 8: User with tracking history but 0 active items (Archived)
    # -------------------------------------------------------------
    print("\n--- TEST 8: User with tracking history but 0 active items ---")
    eval_js("""
        (() => {
            const active = window.TempoRecoverySelfCheck.getActiveTrackers();
            active.forEach(t => window.TempoRecoverySelfCheck.archiveTracker(t.id));
            const uid = (window.TempoAuth && window.TempoAuth.getCurrentUserId && window.TempoAuth.getCurrentUserId()) || 'local_dev_alex';
            sessionStorage.removeItem('tempo_rmode_session_welcomed_' + uid);
        })();
    """)
    time.sleep(0.3)

    status_archived = eval_js("window.TempoRecoverySetup.checkUserTrackingStatus()")
    print("Status when all trackers are archived:", status_archived)
    assert status_archived["isReturning"], "User with archived trackers/history must be treated as Returning User"
    assert status_archived["activeCount"] == 0, "Active count is 0"
    assert status_archived["hasHistory"], "hasHistory must be True"

    eval_js("window.TempoMode.transitionContext('recovery')")
    time.sleep(0.5)

    case2_archived_ui = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case2-welcome\"]') !== null")
    summary_archived = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case2-welcome\"] p.text-xs')?.textContent?.trim()")
    print(f"Case 2 shown for archived history user: {case2_archived_ui}")
    print(f"Summary message: {summary_archived}")
    assert case2_archived_ui, "Should show Case 2 Welcome Back for user with archived history"
    assert ("không có" in summary_archived or "0" in summary_archived) and ("lưu trữ" in summary_archived or "archive" in summary_archived), "Summary should explain 0 active items and safe archive"

    # -------------------------------------------------------------
    # TEST 9: Bilingual Localization (English & Vietnamese)
    # -------------------------------------------------------------
    print("\n--- TEST 9: Bilingual Localization Verification (EN & VI) ---")
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(0.3)

    # Verify English Case 2
    case2_title_en = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case2-welcome\"] h2')?.textContent?.trim()")
    case2_btn_en = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case2-welcome\"] button.btn-primary')?.textContent?.trim()")
    print(f"Case 2 EN title: {case2_title_en}")
    print(f"Case 2 EN primary button: {case2_btn_en}")
    assert "Welcome back!" in case2_title_en, f"Expected English welcome back, got: {case2_title_en}"
    assert "review my system" in case2_btn_en.lower(), f"Expected English review button, got: {case2_btn_en}"
    take_screenshot("rmode_case2_welcome_en.png")

    # Open English Review System
    eval_js("window.TempoRecoverySetup.openTrackingSystemReview()")
    time.sleep(0.5)
    review_title_en = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case2-review\"] h2')?.textContent?.trim()")
    option_a_en = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case2-review\"] h3')?.textContent?.trim()")
    print(f"Review EN title: {review_title_en}")
    print(f"Review EN Option A: {option_a_en}")
    assert "Your Tracking System" in review_title_en, f"Expected English review title, got: {review_title_en}"
    assert "Option A" in option_a_en, f"Expected English Option A, got: {option_a_en}"
    take_screenshot("rmode_case2_review_en.png")

    # Now verify Case 1 in English
    eval_js("window.TempoRecoverySetup.open('case1_welcome', { force: true })")
    time.sleep(0.5)
    case1_title_en = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case1-welcome\"] h2')?.textContent?.trim()")
    case1_question_en = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case1-welcome\"] h3')?.textContent?.trim()")
    case1_btn_en = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case1-welcome\"] button.btn-primary')?.textContent?.trim()")
    case1_later_en = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case1-welcome\"] button.text-xs')?.textContent?.trim()")
    print(f"Case 1 EN title: {case1_title_en}")
    print(f"Case 1 EN question: {case1_question_en}")
    print(f"Case 1 EN primary button: {case1_btn_en}")
    print(f"Case 1 EN later button: {case1_later_en}")
    assert "Welcome to Rmode" in case1_title_en, f"Expected Welcome to Rmode, got: {case1_title_en}"
    assert "ready to set up" in case1_question_en.lower(), f"Expected ready to set up question, got: {case1_question_en}"
    assert "Yes, let's set it up" in case1_btn_en, f"Expected Yes, let's set it up, got: {case1_btn_en}"
    assert "Later" in case1_later_en, f"Expected Later, got: {case1_later_en}"
    take_screenshot("rmode_case1_welcome_en.png")

    # Test Live Language Switch while modal is open: switch to 'vi'
    eval_js("window.TempoI18n.setLanguage('vi')")
    time.sleep(0.5)
    case1_title_vi_live = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case1-welcome\"] h2')?.textContent?.trim()")
    case1_btn_vi_live = eval_js("document.querySelector('[data-tempo-ui=\"rmode-case1-welcome\"] button.btn-primary')?.textContent?.trim()")
    print(f"Live switched to VI title: {case1_title_vi_live}")
    print(f"Live switched to VI primary button: {case1_btn_vi_live}")
    assert "Chào mừng" in case1_title_vi_live, f"Expected Vietnamese title after live switch, got: {case1_title_vi_live}"
    assert "Có, hãy thiết lập ngay" in case1_btn_vi_live, f"Expected Vietnamese button after live switch, got: {case1_btn_vi_live}"

    # Close modal and return
    eval_js("window.TempoRecoverySetup.close()")
    time.sleep(0.3)

    print("\n=======================================================")
    print("ALL 9 TESTS COMPLETED SUCCESSFULLY WITH 100% PASS RATE!")
    print("=======================================================")

finally:
    if ws:
        try: ws.close()
        except: pass
    if proc:
        try: proc.terminate()
        except: pass
