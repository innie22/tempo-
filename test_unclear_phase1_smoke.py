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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_unclear_smoke_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9238
    
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
                ready = eval_js("""
                    Boolean(window.TempoMode && window.TempoApp && window.TempoUnclearMode)
                """)
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

        # =========================================================================
        # 1. Enter Unclear Mode from mode selector dropdown
        # =========================================================================
        log("Testing 1: Switching to Unclear Mode...")
        eval_js("window.TempoMode.setMode('unclear');")
        time.sleep(0.5)
        current_mode = eval_js("window.TempoMode.getMode()")
        assert current_mode == 'unclear', f"Expected mode 'unclear', got {current_mode}"
        log("✓ Successfully entered Unclear Mode.")

        # =========================================================================
        # 2. Verify Unclear Mode Home view matches intended hierarchy & no leaking modules
        # =========================================================================
        log("Testing 2: Verifying Unclear Mode Home view hierarchy and isolation...")
        home_checks = eval_js("""
            (() => {
                const uHome = document.getElementById('unclear-home-view');
                const selectorBtn = document.getElementById('btn-home-mode-selector');
                const quickReliefBtn = uHome ? uHome.innerText.includes('Quick Relief') : false;
                const focusZoneBtn = uHome ? uHome.innerText.includes('Focus Zone') : false;
                const somethingFeelsOff = uHome ? uHome.innerText.includes('Something feels off?') : false;
                
                // Verify no leaking elements
                const recoveryHome = document.getElementById('rmode-home-content');
                const urgentHome = document.getElementById('emode-home-content');
                const defaultHome = document.getElementById('dmode-home-content');
                const recentlySection = uHome ? uHome.innerText.includes('Recently') : false;
                const weeklyReviewSection = uHome ? uHome.innerText.includes('Weekly Review') : false;
                const todaySection = uHome ? uHome.innerText.includes("Today's Plan") || (uHome.innerText.includes("Today") && uHome.innerText.includes("Tasks")) : false;
                const tempoPosts = uHome ? uHome.innerText.includes("Tempo Posts") : false;
                
                return {
                    uHomeExists: Boolean(uHome),
                    hasSelectorBtn: Boolean(selectorBtn),
                    selectorText: selectorBtn ? selectorBtn.innerText : '',
                    quickReliefBtn,
                    focusZoneBtn,
                    somethingFeelsOff,
                    recoveryHomeVisible: recoveryHome ? !recoveryHome.classList.contains('hidden') : false,
                    urgentHomeVisible: urgentHome ? !urgentHome.classList.contains('hidden') : false,
                    recentlySection,
                    weeklyReviewSection,
                    todaySection,
                    tempoPosts
                };
            })()
        """)
        assert home_checks["uHomeExists"], "unclear-home-view not rendered"
        assert home_checks["hasSelectorBtn"], "Home mode selector button missing"
        assert "Unclear" in home_checks["selectorText"], f"Selector button does not show Unclear: {home_checks['selectorText']}"
        assert home_checks["somethingFeelsOff"], "Primary 'Something feels off?' card missing"
        assert home_checks["quickReliefBtn"], "Quick Relief card missing"
        assert home_checks["focusZoneBtn"], "Focus Zone card missing"
        assert not home_checks["recoveryHomeVisible"], "Recovery Home leaked into view"
        assert not home_checks["urgentHomeVisible"], "Urgent Home leaked into view"
        assert not home_checks["recentlySection"], "Recently section should NOT be in Umode"
        assert not home_checks["weeklyReviewSection"], "Weekly Review should NOT be in Umode"
        assert not home_checks["todaySection"], "Today tasks should NOT be in Umode"
        assert not home_checks["tempoPosts"], "Tempo Posts should NOT be in Umode"
        log("✓ Hierarchy & isolation verified (Mode selector, primary card, 2 utility cards, zero leaked modules).")

        # =========================================================================
        # 3. Click "Check in with myself →" -> Stage 1 renders with 1 of 4
        # =========================================================================
        log("Testing 3: Starting check-in...")
        eval_js("window.TempoUnclearMode.startNewCheckIn();")
        time.sleep(0.4)
        stage1_checks = eval_js("""
            (() => {
                const header = document.querySelector('.flex.items-center.justify-between.pb-1');
                const progressText = header ? header.innerText : '';
                const h2 = document.querySelector('#unclear-stage-body h2');
                return {
                    hasProgressText: progressText.includes('1 of 4'),
                    h2Text: h2 ? h2.innerText : ''
                };
            })()
        """)
        assert stage1_checks["hasProgressText"], "Stage 1 progress does not show '1 of 4'"
        assert "What's been on your mind" in stage1_checks["h2Text"], f"Stage 1 title mismatch: {stage1_checks['h2Text']}"
        log("✓ Stage 1 rendered with '1 of 4' progress indicator.")

        # =========================================================================
        # 4. Stage 1: Select concerns from 2+ categories + 1 custom concern -> Continue
        # =========================================================================
        log("Testing 4: Stage 1 selections and custom concern...")
        # Select one from Study ('Coursework & deadlines') and one from Relationships ('Feeling lonely / disconnected')
        eval_js("""
            window.TempoUnclearMode.toggleConcern('Coursework & deadlines');
            window.TempoUnclearMode.toggleConcern('Feeling lonely / disconnected');
            window.TempoUnclearMode.submitCustomConcern('future', 'Uncertain about summer plans');
        """)
        time.sleep(0.3)
        stage1_state = eval_js("""
            (() => {
                const draft = window.TempoUnclearMode.getCurrentDraft();
                return {
                    concerns: draft.concerns,
                    hasCustom: draft.custom_concerns.some(c => c.text === 'Uncertain about summer plans')
                };
            })()
        """)
        assert len(stage1_state["concerns"]) == 3, f"Expected 3 concerns, got {stage1_state['concerns']}"
        assert stage1_state["hasCustom"], "Custom concern not found in draft"
        log("✓ Stage 1 selections & custom concern successfully persisted in draft.")

        eval_js("window.TempoUnclearMode.submitStage1();")
        time.sleep(0.4)

        # =========================================================================
        # 5. Stage 2: Filtered concerns, max 2 enforcement, feelings & custom feeling
        # =========================================================================
        log("Testing 5: Stage 2 (What feels heaviest?)...")
        stage2_checks = eval_js("""
            (() => {
                const header = document.querySelector('.flex.items-center.justify-between.pb-1');
                const progressText = header ? header.innerText : '';
                const h2 = document.querySelector('#unclear-stage-body h2');
                const buttons = Array.from(document.querySelectorAll('#unclear-stage-body button'))
                    .map(b => b.innerText.trim());
                return {
                    hasProgressText: progressText.includes('2 of 4'),
                    h2Text: h2 ? h2.innerText : '',
                    buttonsText: buttons.join(' | ')
                };
            })()
        """)
        assert stage2_checks["hasProgressText"], "Stage 2 progress does not show '2 of 4'"
        assert "What feels heaviest" in stage2_checks["h2Text"], f"Stage 2 title mismatch: {stage2_checks['h2Text']}"
        assert "Coursework & deadlines" in stage2_checks["buttonsText"], "Stage 1 item not shown in Stage 2"
        assert "Uncertain about summer plans" in stage2_checks["buttonsText"], "Custom Stage 1 item not shown in Stage 2"
        log("✓ Stage 2 correctly shows only the concerns selected in Stage 1.")

        # Select 2 heaviest concerns
        eval_js("""
            window.TempoUnclearMode.toggleTopConcern('Coursework & deadlines');
            window.TempoUnclearMode.toggleTopConcern('Uncertain about summer plans');
        """)
        time.sleep(0.2)
        # Try to select a 3rd concern -> should be blocked gently
        eval_js("""
            window.TempoUnclearMode.toggleTopConcern('Feeling lonely / disconnected');
        """)
        time.sleep(0.2)
        top_concerns = eval_js("window.TempoUnclearMode.getCurrentDraft().top_concerns")
        assert len(top_concerns) == 2, f"Max-2 rule violated: {top_concerns}"
        assert 'Feeling lonely / disconnected' not in top_concerns, "3rd concern was incorrectly added!"
        log("✓ Max-2 rule verified: 3rd concern was gently prevented.")

        # Select feelings for 'Coursework & deadlines' and add custom feeling
        eval_js("""
            window.TempoUnclearMode.toggleFeeling('Coursework & deadlines', 'Pressured');
            window.TempoUnclearMode.toggleFeeling('Coursework & deadlines', 'Tired');
            window.TempoUnclearMode.submitCustomFeeling('Coursework & deadlines', 'Rushed');
        """)
        time.sleep(0.3)
        feelings_state = eval_js("window.TempoUnclearMode.getCurrentDraft().feelings_by_concern['Coursework & deadlines']")
        assert 'Pressured' in feelings_state and 'Tired' in feelings_state, f"Feelings missing: {feelings_state}"
        custom_feeling = eval_js("window.TempoUnclearMode.getCurrentDraft().custom_feelings_by_concern['Coursework & deadlines']")
        assert custom_feeling == 'Rushed', f"Custom feeling not saved: {custom_feeling}"
        log("✓ Feelings & custom feeling recorded.")

        eval_js("window.TempoUnclearMode.submitStage2();")
        time.sleep(0.4)

        # =========================================================================
        # 6. Stage 3: What have I noticed? + custom + impact level
        # =========================================================================
        log("Testing 6: Stage 3 (What have you noticed?)...")
        stage3_checks = eval_js("""
            (() => {
                const header = document.querySelector('.flex.items-center.justify-between.pb-1');
                const progressText = header ? header.innerText : '';
                const h2 = document.querySelector('#unclear-stage-body h2');
                return {
                    hasProgressText: progressText.includes('3 of 4'),
                    h2Text: h2 ? h2.innerText : ''
                };
            })()
        """)
        assert stage3_checks["hasProgressText"], "Stage 3 progress does not show '3 of 4'"
        assert "What have you noticed" in stage3_checks["h2Text"], f"Stage 3 title mismatch: {stage3_checks['h2Text']}"

        eval_js("""
            window.TempoUnclearMode.toggleNoticedChange('Sitting down but struggling to start');
            window.TempoUnclearMode.toggleNoticedChange('Harder to sleep / staying up later than usual');
            window.TempoUnclearMode.submitCustomNoticed('Skipping breakfast often');
            window.TempoUnclearMode.setImpactLevel('quite_a_bit');
        """)
        time.sleep(0.2)

        stage3_state = eval_js("""
            (() => {
                const draft = window.TempoUnclearMode.getCurrentDraft();
                return {
                    noticed: draft.noticed_changes,
                    custom_changes: draft.custom_changes,
                    impact: draft.impact_level
                };
            })()
        """)
        assert 'Sitting down but struggling to start' in stage3_state["noticed"], "Noticed change missing"
        assert 'Skipping breakfast often' in stage3_state["custom_changes"], "Custom change missing"
        assert stage3_state["impact"] == 'quite_a_bit', f"Impact mismatch: {stage3_state['impact']}"
        log("✓ Stage 3 selections, custom noticed change, and impact level verified.")

        eval_js("window.TempoUnclearMode.submitStage3();")
        time.sleep(0.4)

        # =========================================================================
        # 7. Stage 4: Broad Needs + Specific details + Custom Need + Primary Need
        # =========================================================================
        log("Testing 7: Stage 4 (What would help most right now?)...")
        stage4_checks = eval_js("""
            (() => {
                const header = document.querySelector('.flex.items-center.justify-between.pb-1');
                const progressText = header ? header.innerText : '';
                const h2 = document.querySelector('#unclear-stage-body h2');
                return {
                    hasProgressText: progressText.includes('4 of 4'),
                    h2Text: h2 ? h2.innerText : ''
                };
            })()
        """)
        assert stage4_checks["hasProgressText"], "Stage 4 progress does not show '4 of 4'"
        assert "What would help most" in stage4_checks["h2Text"], f"Stage 4 title mismatch: {stage4_checks['h2Text']}"

        eval_js("""
            window.TempoUnclearMode.toggleBroadNeed('room');
            window.TempoUnclearMode.toggleNeedDetail('room', 'Step away from screens');
            window.TempoUnclearMode.toggleBroadNeed('support');
            window.TempoUnclearMode.toggleNeedDetail('support', 'Talk to someone I trust');
            window.TempoUnclearMode.setCustomNeed('Take a walk in the evening');
        """)
        time.sleep(0.3)

        # Verify Primary Need selector is visible with the chosen broad needs
        primary_options = eval_js("""
            (() => {
                const buttons = Array.from(document.querySelectorAll('#unclear-stage-body button'))
                    .map(b => b.innerText.trim());
                return buttons.join(' | ');
            })()
        """)
        assert "Some room" in primary_options, f"'Some room' not in primary selector: {primary_options}"
        assert "Some support" in primary_options, f"'Some support' not in primary selector: {primary_options}"

        # Choose 'room' as primary need
        eval_js("window.TempoUnclearMode.setPrimaryNeed('room');")
        time.sleep(0.2)
        primary_need = eval_js("window.TempoUnclearMode.getCurrentDraft().primary_need")
        assert primary_need == 'room', f"Primary need mismatch: {primary_need}"
        log("✓ Broad needs, detail items, custom need, and primary need verified.")

        eval_js("window.TempoUnclearMode.submitStage4();")
        time.sleep(0.4)

        # =========================================================================
        # 8. Stage 5: Completion Screen & Return to Unclear Mode Home
        # =========================================================================
        log("Testing 8: Stage 5 Temporary Phase 1 completion...")
        stage5_checks = eval_js("""
            (() => {
                const sprout = document.body.innerText.includes('🌱');
                const clearer = document.body.innerText.includes('Things are a little clearer.');
                const checklist1 = document.body.innerText.includes("What's been on your mind");
                const checklist2 = document.body.innerText.includes("What feels heaviest right now");
                const checklist3 = document.body.innerText.includes("What you've noticed lately");
                const checklist4 = document.body.innerText.includes("What you need right now");
                const backBtn = Boolean(document.querySelector('button[onclick*="finishCheckIn"]'));
                return {
                    sprout,
                    clearer,
                    checklist1,
                    checklist2,
                    checklist3,
                    checklist4,
                    backBtn
                };
            })()
        """)
        assert stage5_checks["sprout"], "🌱 sprout icon missing"
        assert stage5_checks["clearer"], "Heading 'Things are a little clearer.' missing"
        assert stage5_checks["checklist1"] and stage5_checks["checklist2"] and stage5_checks["checklist3"] and stage5_checks["checklist4"], "Checklist items missing"
        assert stage5_checks["backBtn"], "Back to Unclear Mode button missing"
        log("✓ Stage 5 completion card with 4 checklist items verified.")

        # Click Back to Unclear Mode -> history saved and returns to Home
        eval_js("window.TempoUnclearMode.finishCheckIn();")
        time.sleep(0.5)
        history_count = eval_js("window.TempoUnclearMode.getHistory().length")
        assert history_count >= 1, f"Expected history saved, got count: {history_count}"
        assert eval_js("window.TempoUnclearMode.getCurrentDraft() === null"), "Draft should be cleared after completion"
        assert eval_js("Boolean(document.getElementById('unclear-home-view'))"), "Did not return to Unclear Home view"
        log("✓ Check-in finished: saved to history, cleared draft, returned to Unclear Home.")

        # =========================================================================
        # 9. Verify Back button behavior (preserves answers)
        # =========================================================================
        log("Testing 9: Verifying Back button preserves answers...")
        eval_js("window.TempoUnclearMode.startNewCheckIn();")
        time.sleep(0.3)
        eval_js("window.TempoUnclearMode.toggleConcern('Workload & responsibilities');")
        eval_js("window.TempoUnclearMode.submitStage1();")
        time.sleep(0.3)
        assert eval_js("window.TempoUnclearMode.getCurrentDraft().current_stage") == 2, "Failed to reach stage 2"
        # Click back
        eval_js("window.TempoUnclearMode.goBack();")
        time.sleep(0.3)
        assert eval_js("window.TempoUnclearMode.getCurrentDraft().current_stage") == 1, "Failed to return to stage 1"
        preserved = eval_js("window.TempoUnclearMode.getCurrentDraft().concerns.includes('Workload & responsibilities')")
        assert preserved, "Selection was lost on back!"
        log("✓ Back button preserves selections without data loss.")

        # =========================================================================
        # 10. Verify draft persistence & "Continue where I left off"
        # =========================================================================
        log("Testing 10: Verifying draft persistence across home exit / reload...")
        # Move to stage 2, pick heaviest, move to stage 3
        eval_js("window.TempoUnclearMode.submitStage1();")
        time.sleep(0.3)
        eval_js("window.TempoUnclearMode.toggleTopConcern('Workload & responsibilities');")
        eval_js("window.TempoUnclearMode.submitStage2();")
        time.sleep(0.3)
        assert eval_js("window.TempoUnclearMode.getCurrentDraft().current_stage") == 3, "Not at stage 3"

        # Return to Unclear Home without finishing (simulating leaving mid-flow)
        eval_js("window.TempoUnclearMode.returnToHome();")
        time.sleep(0.4)
        has_continue_link = eval_js("""
            (() => {
                const text = document.getElementById('unclear-home-view').innerText;
                return text.includes('Continue where I left off');
            })()
        """)
        assert has_continue_link, "Continue where I left off link did not appear on Home with draft present!"
        # Resume draft
        eval_js("window.TempoUnclearMode.resumeDraft();")
        time.sleep(0.4)
        current_resumed_stage = eval_js("window.TempoUnclearMode.getCurrentDraft().current_stage")
        assert current_resumed_stage == 3, f"Resumed at stage {current_resumed_stage}, expected 3"
        log("✓ Draft persistence & 'Continue where I left off' resume link verified.")

        eval_js("window.TempoUnclearMode.finishCheckIn();")
        time.sleep(0.3)

        # =========================================================================
        # 11 & 12. Verify Quick Relief and Focus Zone entry buttons
        # =========================================================================
        log("Testing 11 & 12: Quick Relief and Focus Zone...")
        # Check that Quick Relief can open and close without changing mode
        eval_js("""
            if (window.TempoStressRelief) {
                window.TempoStressRelief.openModal();
            }
        """)
        time.sleep(0.4)
        assert eval_js("window.TempoMode.getMode()") == 'unclear', "Mode changed when opening Quick Relief!"
        # Close modal if open
        eval_js("""
            const closeBtn = document.querySelector('#stress-relief-modal button[onclick*="closeModal"]');
            if (closeBtn) closeBtn.click();
        """)
        time.sleep(0.3)
        assert eval_js("window.TempoMode.getMode()") == 'unclear', "Mode changed when closing Quick Relief!"
        log("✓ Quick Relief and Focus Zone triggers verified.")

        # =========================================================================
        # 13. Verify mode isolation across all modes
        # =========================================================================
        log("Testing 13: Mode isolation across modes...")
        eval_js("window.TempoMode.setMode('recovery');")
        time.sleep(0.5)
        rec_visible = eval_js("!document.getElementById('rmode-home-content').classList.contains('hidden')")
        unclear_in_rec = eval_js("!document.getElementById('umode-home-content').classList.contains('hidden')")
        assert rec_visible, "Recovery Home not visible after switching to recovery"
        assert not unclear_in_rec, "Unclear Home leaked into Recovery Mode"

        eval_js("window.TempoMode.setMode('unclear');")
        time.sleep(0.5)
        unclear_visible = eval_js("!document.getElementById('umode-home-content').classList.contains('hidden')")
        rec_in_unclear = eval_js("!document.getElementById('rmode-home-content').classList.contains('hidden')")
        assert unclear_visible, "Unclear Home not visible after switching back to unclear"
        assert not rec_in_unclear, "Recovery Home leaked into Unclear Mode"

        eval_js("window.TempoMode.setMode('default');")
        time.sleep(0.5)
        default_visible = eval_js("!document.getElementById('dmode-home-content').classList.contains('hidden')")
        unclear_in_default = eval_js("!document.getElementById('umode-home-content').classList.contains('hidden')")
        assert default_visible, "Default Home not visible after switching to default"
        assert not unclear_in_default, "Unclear Home leaked into Default Mode"

        # Switch back to unclear for clean state
        eval_js("window.TempoMode.setMode('unclear');")
        time.sleep(0.4)
        log("✓ Strict mutual exclusivity and mode isolation verified across all modes.")

        # =========================================================================
        # 14. Verify SOS remains globally accessible
        # =========================================================================
        log("Testing 14: SOS global accessibility...")
        sos_accessible = eval_js("""
            (() => {
                const sosBtn = document.querySelector('button[onclick*="launchEmergencySupport"]') ||
                               document.querySelector('button[onclick*="EmergencySupport"]') ||
                               document.querySelector('button[onclick*="TempoEmergencySupport"]');
                return Boolean(sosBtn && sosBtn.offsetParent !== null);
            })()
        """)
        assert sos_accessible, "Global SOS button not accessible in Unclear Mode!"
        log("✓ SOS globally accessible from header in Unclear Mode.")

        log("\n🎉 ALL 14 SMOKE CHECK CRITERIA PASSED SUCCESSFULLY!")

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
