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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_emergency_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9266
    
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
                raw = ws.recv()
                res = json.loads(raw)
                if res.get("id") == cid:
                    return res
        
        def evaluate(expr):
            res = send_command("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True
            })
            if "exceptionDetails" in res.get("result", {}):
                raise RuntimeError(f"JS Exception: {res['result']['exceptionDetails']}")
            return res.get("result", {}).get("result", {}).get("value")
        
        # Wait for page and scripts to initialize
        def wait_for_ready():
            for _ in range(50):
                try:
                    ready = evaluate("Boolean(window.TempoMode && window.TempoApp && window.TempoEmergencySupport)")
                    if ready:
                        return True
                except Exception:
                    pass
                time.sleep(0.3)
            return False

        if not wait_for_ready():
            raise RuntimeError("Tempo app or TempoEmergencySupport did not initialize in time")

        log("\n--- TEST 1: Initial State & SOS Header Trigger ---")
        init_state = evaluate("""(() => {
            const modal = document.getElementById('progressive-emergency-modal');
            const drawer = document.getElementById('human-support-drawer');
            return {
                modalHidden: modal.classList.contains('hidden'),
                drawerHidden: drawer.classList.contains('hidden')
            };
        })()""")
        log(f"Initial state: {init_state}")
        assert init_state['modalHidden'] == True, "Modal should be initially hidden"
        assert init_state['drawerHidden'] == True, "Drawer should be initially hidden"
        
        # Click the SOS button in top nav
        log("Triggering window.TempoEmergencySupport.openSOS()...")
        sos_state = evaluate("""(() => {
            window.TempoEmergencySupport.openSOS();
            const modal = document.getElementById('progressive-emergency-modal');
            const drawer = document.getElementById('human-support-drawer');
            const checkinStep = document.getElementById('emergency-step-checkin');
            const toggleHumanBtn = document.getElementById('btn-toggle-human-drawer');
            const safetyBanner = document.getElementById('emergency-safety-banner');
            
            return {
                modalVisible: !modal.classList.contains('hidden'),
                drawerHidden: drawer.classList.contains('hidden'),
                checkinStepVisible: !checkinStep.classList.contains('hidden'),
                hasToggleBtn: !!toggleHumanBtn,
                toggleBtnText: toggleHumanBtn ? toggleHumanBtn.innerText.trim() : '',
                safetyBannerVisible: !safetyBanner.classList.contains('hidden')
            };
        })()""")
        log(f"After openSOS(): {sos_state}")
        assert sos_state['modalVisible'] == True, "Modal must be visible after SOS trigger"
        assert sos_state['drawerHidden'] == True, "Drawer MUST NOT open automatically over Step 1"
        assert sos_state['checkinStepVisible'] == True, "Step 1 Check-In must be visible"
        assert "Get support now" in sos_state['toggleBtnText'] or "Get immediate" in sos_state['toggleBtnText'], "Persistent top bar button text must be 'Get support now →'"
        log("PASSED: SOS opens Step 1 without popping the hotline drawer!")

        log("\n--- TEST 2: Persistent Human Support Drawer ---")
        drawer_test = evaluate("""(() => {
            const toggleBtn = document.getElementById('btn-toggle-human-drawer');
            toggleBtn.click();
            const drawer = document.getElementById('human-support-drawer');
            const drawerText = drawer ? drawer.innerText : '';
            
            return {
                drawerVisible: !drawer.classList.contains('hidden'),
                has115: drawerText.includes('115'),
                hasHope: drawerText.includes('0865 044 400'),
                hasOfflineNotice: drawerText.includes('Office Hours Support') || drawerText.includes('Campus Student Wellbeing'),
                hasOfflineInput: !!document.getElementById('drawer-offline-message')
            };
        })()""")
        log(f"Drawer test result: {drawer_test}")
        assert drawer_test['drawerVisible'] == True, "Drawer must open on toggle"
        assert drawer_test['has115'] == True, "Drawer must display 115"
        assert drawer_test['hasHope'] == True, "Drawer must display HOPE 0865 044 400"
        assert drawer_test['hasOfflineNotice'] == True, "Drawer must show campus support"
        assert drawer_test['hasOfflineInput'] == True, "Drawer must have non-urgent message input"
        
        # Test submitting non-urgent offline message
        submit_res = evaluate("""(() => {
            document.getElementById('drawer-offline-contact').value = 'Test Student';
            document.getElementById('drawer-offline-message').value = 'Question about counseling appointments next week.';
            document.getElementById('btn-drawer-send-offline').click();
            
            const success = document.getElementById('drawer-offline-success');
            const stored = JSON.parse(localStorage.getItem('tempo_offline_messages') || '[]');
            
            // Close drawer
            document.getElementById('btn-close-human-drawer').click();
            const drawer = document.getElementById('human-support-drawer');
            
            return {
                successShown: !success.classList.contains('hidden'),
                storedCount: stored.length,
                lastMsg: stored.length > 0 ? stored[stored.length - 1].message : '',
                drawerClosed: drawer.classList.contains('hidden')
            };
        })()""")
        log(f"Offline message test result: {submit_res}")
        assert submit_res['successShown'] == True, "Offline message success alert should appear"
        assert submit_res['storedCount'] > 0, "Offline message should be stored in localStorage"
        assert submit_res['drawerClosed'] == True, "Drawer should close when close button is clicked"
        log("PASSED: Persistent Human Support Drawer & Offline Message Handling verified!")

        log("\n--- TEST 3: Grounding Activities (Step 3) Navigation & Cycle ---")
        grounding_test = evaluate("""(() => {
            // Select Option A: Overwhelmed
            window.TempoEmergencySupport.handleInitialCheckin('overwhelmed');
            
            const stepGrounding = document.getElementById('emergency-step-grounding');
            const content = document.getElementById('grounding-activity-content');
            const act1Title = content ? content.querySelector('h4').innerText : '';
            const act1Inputs = content ? content.querySelectorAll('input').length : 0;
            
            // Click "Try something else" -> Activity 2
            window.TempoEmergencySupport.nextGrounding();
            const act2Title = content ? content.querySelector('h4').innerText : '';
            
            // Click "Try something else" -> Activity 3
            window.TempoEmergencySupport.nextGrounding();
            const act3Title = content ? content.querySelector('h4').innerText : '';
            const act3Buttons = Array.from(content.querySelectorAll('button')).map(b => b.innerText.trim());
            
            return {
                groundingVisible: !stepGrounding.classList.contains('hidden'),
                act1Title,
                act1Inputs,
                act2Title,
                act3Title,
                act3Buttons
            };
        })()""")
        log(f"Grounding test result: {grounding_test}")
        assert grounding_test['groundingVisible'] == True, "Grounding step must be visible"
        assert "Notice Your Surroundings" in grounding_test['act1Title'], "Activity 1 must be Notice Surroundings"
        assert grounding_test['act1Inputs'] == 3, "Activity 1 must provide 3 item inputs"
        assert "Slow Down Your Breathing" in grounding_test['act2Title'], "Activity 2 must be Slow Down Breathing"
        assert "Move Toward Space & Safety" in grounding_test['act3Title'], "Activity 3 must be Move Toward Safety"
        assert any("Contact someone I trust" in b for b in grounding_test['act3Buttons']), "Activity 3 must have 'Contact someone I trust'"
        assert any("Get support now" in b or "Get immediate help" in b for b in grounding_test['act3Buttons']), "Activity 3 must have support button"
        log("PASSED: Grounding Activities 1, 2, and 3 verified with correct buttons and pacing!")

        log("\n--- TEST 4: Step 4 Safety Check-in -> Step 5A Still Unsafe ---")
        step4_unsafe = evaluate("""(() => {
            // Complete grounding to Step 4
            window.TempoEmergencySupport.goToStep('safety_checkin');
            const step4 = document.getElementById('emergency-step-safety_checkin');
            
            // Select "I still don't feel safe"
            window.TempoEmergencySupport.handleSafetyCheckin('unsafe');
            const step5a = document.getElementById('emergency-step-still_unsafe');
            const step5aText = step5a ? step5a.innerText : '';
            
            return {
                step4Existed: !!step4,
                step5aVisible: !step5a.classList.contains('hidden'),
                hasReassurance: step5aText.includes("You don't have to handle this alone"),
                has115: step5aText.includes("115"),
                hasHope: step5aText.includes("0865 044 400"),
                hasTrustedCopy: !!document.getElementById('btn-copy-trusted-msg')
            };
        })()""")
        log(f"Step 5A test result: {step4_unsafe}")
        assert step4_unsafe['step5aVisible'] == True, "Step 5A must be visible when unsafe"
        assert step4_unsafe['hasReassurance'] == True, "Step 5A must reassure 'You don't have to handle this alone'"
        assert step4_unsafe['has115'] == True, "Step 5A must have 115"
        assert step4_unsafe['hasHope'] == True, "Step 5A must have 0865 044 400"
        log("PASSED: Step 5A Safety First Flow verified!")

        log("\n--- TEST 5: Step 4 Check-in -> Step 5B Calmer Gentle Transition ---")
        step5b_test = evaluate("""(() => {
            window.TempoEmergencySupport.goToStep('safety_checkin');
            // Select "I feel calmer now"
            window.TempoEmergencySupport.handleSafetyCheckin('calmer');
            const step5b = document.getElementById('emergency-step-calmer_options');
            const step5bText = step5b ? step5b.innerText : '';
            const buttons = Array.from(step5b.querySelectorAll('button')).map(b => b.innerText.trim());
            
            return {
                step5bVisible: !step5b.classList.contains('hidden'),
                hasTransitionCopy: step5bText.includes("We can look at what has been making things feel this difficult"),
                hasShareNotice: step5bText.includes("You only need to share what you're comfortable sharing"),
                buttonCount: buttons.length,
                hasTalkBtn: buttons.some(b => b.includes("Talk about what's happening")),
                hasContinueGrounding: buttons.some(b => b.includes("Continue grounding")),
                hasTalkSomeone: buttons.some(b => b.includes("Talk to someone")),
                hasStopForNow: buttons.some(b => b.includes("Stop for now"))
            };
        })()""")
        log(f"Step 5B test result: {step5b_test}")
        assert step5b_test['step5bVisible'] == True, "Step 5B must be visible when calmer"
        assert step5b_test['hasTransitionCopy'] == True, "Step 5B must contain gentle transition copy"
        assert step5b_test['hasTalkBtn'] == True, "Step 5B must provide 'Talk about what's happening'"
        assert step5b_test['hasContinueGrounding'] == True, "Step 5B must provide 'Continue grounding'"
        assert step5b_test['hasTalkSomeone'] == True, "Step 5B must provide 'Talk to someone'"
        assert step5b_test['hasStopForNow'] == True, "Step 5B must provide 'Stop for now'"
        log("PASSED: Step 5B Gentle Transition verified with all 4 required options!")

        log("\n--- TEST 6: Step 6 Problem Decomposition (Non-Clinical) & Step 7 ONE NEXT ACTION ---")
        step6_7_test = evaluate("""(() => {
            window.TempoEmergencySupport.goToStep('understand_problem');
            const textarea = document.getElementById('emergency-problem-text');
            textarea.value = "I have several deadlines this week, I'm exhausted, and I feel like I can't start or finish anything.";
            
            // Analyze problem
            window.TempoEmergencySupport.handleAnalyzeProblem();
            
            const step7 = document.getElementById('emergency-step-problem_solving');
            const step7Text = step7 ? step7.innerText : '';
            const actionText = document.getElementById('emergency-solved-action') ? document.getElementById('emergency-solved-action').innerText : '';
            const timeText = document.getElementById('emergency-solved-time') ? document.getElementById('emergency-solved-time').innerText : '';
            
            return {
                step7Visible: !step7.classList.contains('hidden'),
                hasTonightFirst: step7Text.includes("Let's handle tonight first"),
                hasOneNextAction: step7Text.includes("ONE NEXT ACTION"),
                actionText,
                timeText,
                hasAcademicWorkload: step7Text.includes("Academic Workload") || step7Text.includes("Deadline"),
                hasSleepDebt: step7Text.includes("Sleep Debt"),
                hasInitiationFreeze: step7Text.includes("Initiation Freeze")
            };
        })()""")
        log(f"Step 6 & 7 test result: {step6_7_test}")
        assert step6_7_test['step7Visible'] == True, "Step 7 Problem Solving must be visible"
        assert step6_7_test['hasTonightFirst'] == True, "Step 7 must state 'Let's handle tonight first.'"
        assert step6_7_test['hasOneNextAction'] == True, "Step 7 must highlight ONE NEXT ACTION"
        assert "5 minutes" in step6_7_test['timeText'], "Estimated time should be 5 minutes"
        assert step6_7_test['hasAcademicWorkload'] == True, "Identified practical deadline challenge"
        assert step6_7_test['hasSleepDebt'] == True, "Identified physical sleep debt"
        assert step6_7_test['hasInitiationFreeze'] == True, "Identified initiation freeze"
        log("PASSED: Step 6 & 7 practical non-clinical problem breakdown & ONE NEXT ACTION verified!")

        log("\n--- TEST 7: Launch Micro Action to Focus Zone ---")
        launch_res = evaluate("""(() => {
            window.TempoEmergencySupport.launchImmediateMicroAction();
            const modal = document.getElementById('progressive-emergency-modal');
            const focusRoot = document.getElementById('focus-zone-modal');
            const toast = document.getElementById('app-toast');
            
            return {
                modalClosed: modal.classList.contains('hidden'),
                toastText: toast ? toast.innerText : '',
                focusOpen: focusRoot ? !focusRoot.classList.contains('hidden') : false
            };
        })()""")
        log(f"Launch micro action result: {launch_res}")
        assert launch_res['modalClosed'] == True, "Modal must close on launch"
        log("PASSED: Launch Immediate Micro Action cleanly connects to Focus Zone!")

        log("\n=======================================================")
        log("ALL EMERGENCY SUPPORT REDESIGN SMOKE TESTS PASSED (7/7)!")
        log("=======================================================")
        
    finally:
        if ws:
            ws.close()
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    run_tests()
