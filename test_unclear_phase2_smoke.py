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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_unclear_phase2_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9245
    
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
            for _ in range(40):
                ready = eval_js("Boolean(window.TempoMode && window.TempoApp && window.TempoUnclearMode)")
                if ready:
                    return True
                time.sleep(0.3)
            return False

        if not wait_for_ready():
            raise RuntimeError("Tempo app did not initialize in time")
            
        log("App initialized and TempoUnclearMode is available.")

        # Sign in test user
        eval_js("window.TempoAuth.signIn('alex.chen@university.edu', 'demo1234');")
        time.sleep(0.5)
        log(f"Authenticated user: {eval_js('window.TempoAuth.getCurrentUser()?.email')}")

        # Switch to Unclear Mode
        eval_js("window.TempoMode.setMode('unclear');")
        time.sleep(0.4)
        assert eval_js("window.TempoMode.getMode()") == 'unclear', "Failed to switch to unclear mode"
        log("✓ Successfully entered Unclear Mode.")

        # =========================================================================
        # 1. Start Check-in & Complete Stages 1 to 4 with primary_need = 'handle'
        # =========================================================================
        log("\n--- TEST CASE A: primary_need = 'handle' ---")
        eval_js("window.TempoUnclearMode.startNewCheckIn();")
        time.sleep(0.3)

        # Stage 1: Concerns
        eval_js("""
            window.TempoUnclearMode.toggleConcern('Coursework & deadlines');
            window.TempoUnclearMode.toggleConcern('Feeling lonely / disconnected');
            window.TempoUnclearMode.submitCustomConcern('future', 'Uncertain about summer plans');
            window.TempoUnclearMode.submitStage1();
        """)
        time.sleep(0.3)
        assert eval_js("window.TempoUnclearMode.getCurrentDraft().current_stage") == 2, "Not at stage 2"

        # Stage 2: Heaviest concerns + feelings
        eval_js("""
            window.TempoUnclearMode.toggleTopConcern('Coursework & deadlines');
            window.TempoUnclearMode.toggleTopConcern('Uncertain about summer plans');
            window.TempoUnclearMode.toggleFeeling('Coursework & deadlines', 'Pressured');
            window.TempoUnclearMode.toggleFeeling('Coursework & deadlines', 'Tired');
            window.TempoUnclearMode.submitCustomFeeling('Coursework & deadlines', 'Rushed');
            window.TempoUnclearMode.submitStage2();
        """)
        time.sleep(0.3)
        assert eval_js("window.TempoUnclearMode.getCurrentDraft().current_stage") == 3, "Not at stage 3"

        # Stage 3: Noticed changes + impact
        eval_js("""
            window.TempoUnclearMode.toggleNoticedChange('Sitting down but struggling to start');
            window.TempoUnclearMode.toggleNoticedChange('Harder to sleep / staying up later than usual');
            window.TempoUnclearMode.submitCustomNoticed('Skipping breakfast often');
            window.TempoUnclearMode.setImpactLevel('quite_a_bit');
            window.TempoUnclearMode.submitStage3();
        """)
        time.sleep(0.3)
        assert eval_js("window.TempoUnclearMode.getCurrentDraft().current_stage") == 4, "Not at stage 4"

        # Stage 4: Needs (handle, room, support) with primary = handle
        eval_js("""
            window.TempoUnclearMode.toggleBroadNeed('handle');
            window.TempoUnclearMode.toggleNeedDetail('handle', 'Tackle one urgent task');
            window.TempoUnclearMode.toggleBroadNeed('room');
            window.TempoUnclearMode.toggleBroadNeed('support');
            window.TempoUnclearMode.setPrimaryNeed('handle');
            window.TempoUnclearMode.submitStage4();
        """)
        time.sleep(0.4)
        assert eval_js("window.TempoUnclearMode.getCurrentDraft().current_stage") == 5, "Not at stage 5"
        log("✓ Stages 1-4 completed. Now at Stage 5 Final Result.")

        # =========================================================================
        # 2. Verify Reflection Summary Data
        # =========================================================================
        log("Verifying Stage 5 Reflection Summary...")
        summary_checks = eval_js("""
            (() => {
                const text = document.getElementById('umode-home-content').innerText;
                return {
                    hasClearer: text.includes('Things are a little clearer'),
                    hasNoticedIntro: text.includes("Here's what you noticed"),
                    hasTopConcern1: text.includes('Coursework & deadlines'),
                    hasTopConcern2: text.includes('Uncertain about summer plans'),
                    hasFeeling1: text.includes('Pressured'),
                    hasFeeling2: text.includes('Rushed'),
                    hasNoticed1: text.includes('Sitting down but struggling to start'),
                    hasNoticed2: text.includes('Skipping breakfast often'),
                    hasImpact: text.includes('Quite a bit'),
                    hasNeedHandle: text.includes('Deal with something'),
                    hasNeedRoom: text.includes('Some room'),
                    hasNeedSupport: text.includes('Some support'),
                    hasPrimaryLead: text.includes('MOST USEFUL TO START WITH')
                };
            })()
        """)
        assert summary_checks["hasClearer"], "Header 'Things are a little clearer' missing"
        assert summary_checks["hasNoticedIntro"], "Intro 'Here's what you noticed' missing"
        assert summary_checks["hasTopConcern1"] and summary_checks["hasTopConcern2"], "Top concerns missing in summary"
        assert summary_checks["hasFeeling1"] and summary_checks["hasFeeling2"], "Feelings missing in summary"
        assert summary_checks["hasNoticed1"] and summary_checks["hasNoticed2"], "Noticed changes missing in summary"
        assert summary_checks["hasImpact"], "Everyday impact missing in summary"
        assert summary_checks["hasNeedHandle"] and summary_checks["hasNeedRoom"], "Selected needs missing in summary"
        assert summary_checks["hasPrimaryLead"], "Primary need lead missing in summary"
        log("✓ Structured Reflection Summary reflects actual user data accurately without AI prose.")

        # =========================================================================
        # 3. Verify Featured Direction for 'handle' (Urgent Featured)
        # =========================================================================
        log("Verifying Featured Direction (Urgent Mode featured first)...")
        direction_checks = eval_js("""
            (() => {
                const text = document.getElementById('umode-home-content').innerText;
                const buttons = Array.from(document.querySelectorAll('#umode-home-content button'))
                    .map(b => b.innerText.trim());
                return {
                    hasUrgentFeatured: text.includes('Handle what needs attention') && text.includes('Urgent Mode can help you decide what comes first'),
                    hasUrgentBtn: buttons.some(b => b.includes('Go to Urgent Mode')),
                    hasRecoverySec: buttons.some(b => b.includes('Go to Recovery Mode')),
                    hasDefaultSec: buttons.some(b => b.includes('Return to Tempo')),
                    hasSupportSec: buttons.some(b => b.includes('Explore support options')),
                    hasStayUnclear: buttons.some(b => b.includes('Stay in Unclear Mode for now')),
                    hasEvaluativeLabel: text.includes('Tempo recommends') || text.includes('Recommended') || text.includes('Best choice')
                };
            })()
        """)
        assert direction_checks["hasUrgentFeatured"], "Urgent Mode is not featured first"
        assert direction_checks["hasUrgentBtn"], "Go to Urgent Mode button missing"
        assert direction_checks["hasRecoverySec"], "Secondary Recovery Mode missing"
        assert direction_checks["hasDefaultSec"], "Secondary Default Tempo missing"
        assert direction_checks["hasSupportSec"], "Secondary Support options missing"
        assert direction_checks["hasStayUnclear"], "Stay in Unclear Mode option missing"
        assert not direction_checks["hasEvaluativeLabel"], "Forbidden evaluative label found in UI!"
        log("✓ Urgent Mode is featured first without evaluative labels. Secondary options are present.")

        # Verify NO automatic switch occurred
        current_mode = eval_js("window.TempoMode.getMode()")
        assert current_mode == 'unclear', f"Mode was automatically changed to {current_mode}!"
        log("✓ Hard rule verified: NO automatic mode switch occurred.")

        # =========================================================================
        # 4. TEST CASE B: Back & Edit primary need to 'room' -> Recovery Featured
        # =========================================================================
        log("\n--- TEST CASE B: Back & Edit primary need to 'room' ---")
        eval_js("window.TempoUnclearMode.goBack();")
        time.sleep(0.3)
        assert eval_js("window.TempoUnclearMode.getCurrentDraft().current_stage") == 4, "Did not return to stage 4"

        # Change primary need to 'room'
        eval_js("window.TempoUnclearMode.setPrimaryNeed('room');")
        time.sleep(0.2)
        eval_js("window.TempoUnclearMode.submitStage4();")
        time.sleep(0.3)
        assert eval_js("window.TempoUnclearMode.getCurrentDraft().current_stage") == 5, "Did not return to stage 5"

        room_checks = eval_js("""
            (() => {
                const text = document.getElementById('umode-home-content').innerText;
                const buttons = Array.from(document.querySelectorAll('#umode-home-content button'))
                    .map(b => b.innerText.trim());
                return {
                    hasRecoveryFeatured: text.includes('Give yourself some room') && text.includes('Recovery Mode gives you space to slow things down'),
                    hasUrgentSec: buttons.some(b => b.includes('Go to Urgent Mode')),
                    hasRecoveryBtn: buttons.some(b => b.includes('Go to Recovery Mode'))
                };
            })()
        """)
        assert room_checks["hasRecoveryFeatured"], "Recovery Mode was not featured after updating primary need!"
        assert room_checks["hasUrgentSec"], "Urgent Mode did not move to secondary directions!"
        assert eval_js("window.TempoMode.getMode()") == 'unclear', "Mode automatically switched during edit!"
        log("✓ Editing primary need to 'room' dynamically reorders emphasis to Recovery Mode without stale UI.")

        # =========================================================================
        # 5. Hand-off Execution: Choose Urgent Mode
        # =========================================================================
        log("\n--- TEST CASE C: Explicit Destination Handoff (Urgent Mode) ---")
        # Click Go to Urgent Mode explicitly
        eval_js("window.TempoUnclearMode.chooseDirection('urgent');")
        time.sleep(0.5)

        assert eval_js("window.TempoMode.getMode()") == 'emergency', "Mode did not switch to emergency/urgent!"
        assert eval_js("window.TempoUnclearMode.getCurrentDraft() === null"), "Active draft was not cleared after handoff!"
        
        # Check history recorded chosen_direction = 'urgent'
        last_history = eval_js("window.TempoUnclearMode.getHistory()[0]")
        assert last_history["chosen_direction"] == 'urgent', f"Expected chosen_direction 'urgent', got {last_history.get('chosen_direction')}"
        assert last_history["primary_need"] == 'room', "Primary need in history should be user's selected primary need ('room')"
        
        # Verify no auto-created task from Umode
        plan = eval_js("window.TempoPlanStore ? window.TempoPlanStore.getActivePlan('emergency') : null")
        if plan and plan.get("tasks"):
            task_names = [t.get("name") for t in plan.get("tasks")]
            assert "Coursework & deadlines" not in task_names, "Concern was auto-converted into an urgent task!"
        log("✓ Urgent handoff clean: mode switched to emergency, chosen_direction='urgent', no auto-created tasks.")

        # =========================================================================
        # 6. Hand-off Execution: Default Mode ('self_directed') with next_step field
        # =========================================================================
        log("\n--- TEST CASE D: Default Mode Handoff with optional next_step ---")
        eval_js("window.TempoMode.setMode('unclear');")
        time.sleep(0.4)
        eval_js("window.TempoUnclearMode.startNewCheckIn();")
        time.sleep(0.2)

        # Fast forward through check-in
        eval_js("""
            window.TempoUnclearMode.toggleConcern('Workload & responsibilities');
            window.TempoUnclearMode.submitStage1();
            window.TempoUnclearMode.toggleTopConcern('Workload & responsibilities');
            window.TempoUnclearMode.submitStage2();
            window.TempoUnclearMode.toggleNoticedChange('Sitting down but struggling to start');
            window.TempoUnclearMode.setImpactLevel('little');
            window.TempoUnclearMode.submitStage3();
            window.TempoUnclearMode.toggleBroadNeed('self_directed');
            window.TempoUnclearMode.setPrimaryNeed('self_directed');
            window.TempoUnclearMode.submitStage4();
        """)
        time.sleep(0.4)

        default_feat_checks = eval_js("""
            (() => {
                const text = document.getElementById('umode-home-content').innerText;
                const nextStepInput = Boolean(document.getElementById('unclear-next-step-input'));
                return {
                    hasTakeItFromHere: text.includes('Take it from here'),
                    hasNextStepInput: nextStepInput
                };
            })()
        """)
        assert default_feat_checks["hasTakeItFromHere"], "'Take it from here' not featured for self_directed"
        assert default_feat_checks["hasNextStepInput"], "Optional 'One thing I want to do next' field missing"

        # Enter next step and choose default
        eval_js("""
            const ninput = document.getElementById('unclear-next-step-input');
            if (ninput) ninput.value = 'Finish the outline, then stop for tonight';
            window.TempoUnclearMode.chooseDirection('default');
        """)
        time.sleep(0.5)

        assert eval_js("window.TempoMode.getMode()") == 'default', "Mode did not switch to default!"
        last_hist2 = eval_js("window.TempoUnclearMode.getHistory()[0]")
        assert last_hist2["chosen_direction"] == 'default', f"Expected chosen_direction 'default', got {last_hist2.get('chosen_direction')}"
        assert last_hist2["next_step"] == 'Finish the outline, then stop for tonight', f"next_step mismatch: {last_hist2.get('next_step')}"
        log("✓ Default Tempo handoff clean: mode switched to default, next_step preserved without task creation.")

        # =========================================================================
        # 7. Hand-off Execution: Support options
        # =========================================================================
        log("\n--- TEST CASE E: Support Handoff ---")
        eval_js("window.TempoMode.setMode('unclear');")
        time.sleep(0.4)
        eval_js("window.TempoUnclearMode.startNewCheckIn();")
        time.sleep(0.2)
        eval_js("""
            window.TempoUnclearMode.toggleConcern('Feeling lonely / disconnected');
            window.TempoUnclearMode.submitStage1();
            window.TempoUnclearMode.toggleTopConcern('Feeling lonely / disconnected');
            window.TempoUnclearMode.submitStage2();
            window.TempoUnclearMode.toggleNoticedChange('Harder to sleep / staying up later than usual');
            window.TempoUnclearMode.setImpactLevel('quite_a_bit');
            window.TempoUnclearMode.submitStage3();
            window.TempoUnclearMode.toggleBroadNeed('support');
            window.TempoUnclearMode.setPrimaryNeed('support');
            window.TempoUnclearMode.submitStage4();
        """)
        time.sleep(0.4)

        support_checks = eval_js("""
            (() => {
                const text = document.getElementById('umode-home-content').innerText;
                return text.includes('Get some support') && text.includes('Explore support options');
            })()
        """)
        assert support_checks, "Support not featured for primary_need = 'support'"

        eval_js("window.TempoUnclearMode.chooseDirection('support');")
        time.sleep(0.5)

        last_hist3 = eval_js("window.TempoUnclearMode.getHistory()[0]")
        assert last_hist3["chosen_direction"] == 'support', f"Expected chosen_direction 'support', got {last_hist3.get('chosen_direction')}"
        # Verify real support screen opened
        support_screen_visible = eval_js("!document.getElementById('screen-support').classList.contains('hidden')")
        assert support_screen_visible, "Support screen (screen-support) was not opened!"
        log("✓ Support handoff clean: connected to real campus support screen, chosen_direction='support'.")

        # =========================================================================
        # 8. Hand-off Execution: Stay in Unclear Mode & Returning Later
        # =========================================================================
        log("\n--- TEST CASE F: Stay in Unclear Mode & Fresh Check-in on Return ---")
        eval_js("window.TempoApp.navigateTo('today');")
        eval_js("window.TempoMode.setMode('unclear');")
        time.sleep(0.4)

        eval_js("window.TempoUnclearMode.startNewCheckIn();")
        time.sleep(0.2)
        eval_js("""
            window.TempoUnclearMode.toggleConcern('Finances');
            window.TempoUnclearMode.submitStage1();
            window.TempoUnclearMode.toggleTopConcern('Finances');
            window.TempoUnclearMode.submitStage2();
            window.TempoUnclearMode.toggleNoticedChange('Harder to sleep / staying up later than usual');
            window.TempoUnclearMode.setImpactLevel('little');
            window.TempoUnclearMode.submitStage3();
            window.TempoUnclearMode.toggleBroadNeed('room');
            window.TempoUnclearMode.setPrimaryNeed('room');
            window.TempoUnclearMode.submitStage4();
        """)
        time.sleep(0.4)

        # Click "Stay in Unclear Mode for now"
        eval_js("window.TempoUnclearMode.chooseDirection('unclear');")
        time.sleep(0.4)

        assert eval_js("window.TempoMode.getMode()") == 'unclear', "Mode should remain unclear"
        assert eval_js("window.TempoUnclearMode.getCurrentDraft() === null"), "Active draft should be cleared"
        
        # Verify Unclear Home shows fresh start button and last check-in note
        home_after = eval_js("""
            (() => {
                const text = document.getElementById('unclear-home-view').innerText;
                const buttons = Array.from(document.querySelectorAll('#unclear-home-view button'))
                    .map(b => b.innerText.trim());
                return {
                    hasCheckInBtn: buttons.some(b => b.includes('Check in with myself')),
                    hasLastCheckIn: text.includes('Last check-in'),
                    hasContinueDraft: text.includes('Continue where I left off')
                };
            })()
        """)
        assert home_after["hasCheckInBtn"], "Check in with myself button missing on Home"
        assert home_after["hasLastCheckIn"], "Last check-in quiet note missing on Home"
        assert not home_after["hasContinueDraft"], "Completed check-in incorrectly treated as active draft!"
        log("✓ Clean return to Unclear Home: user is not trapped on old result, fresh check-in available.")

        # =========================================================================
        # 9. SOS Global Accessibility
        # =========================================================================
        log("Testing SOS global accessibility...")
        sos_accessible = eval_js("""
            (() => {
                const sosBtn = document.getElementById('btn-nav-sos');
                return Boolean(sosBtn && sosBtn.offsetParent !== null);
            })()
        """)
        assert sos_accessible, "Global SOS button not accessible in top navbar!"
        log("✓ SOS globally accessible at all times.")

        log("\n🎉 ALL PHASE 2 SMOKE CHECK TESTS PASSED SUCCESSFULLY!")

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

if __name__ == '__main__':
    run_tests()
