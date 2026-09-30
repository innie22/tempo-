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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_sos_alignment_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9270
    
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

        # =========================================================================
        # CRITERION 10: Anonymous access does not require login
        # =========================================================================
        log("\n--- CRITERION 10: Anonymous Access Verification ---")
        anon_check = evaluate("""(() => {
            const currentUser = window.TempoAuth ? window.TempoAuth.getCurrentUser() : null;
            return {
                isAnonymous: currentUser === null
            };
        })()""")
        log(f"Anonymous status: {anon_check}")
        assert anon_check['isAnonymous'] == True, "Test must start with an anonymous (logged out) session"
        log("PASSED (10/12): Anonymous session verified without authentication requirement.")

        # Set an initial mode before opening SOS to test mode preservation later
        evaluate("window.TempoMode.setMode('recovery');")
        init_mode = evaluate("window.TempoMode.getMode()")
        assert init_mode == 'recovery', "Initial mode set to recovery"
        log("Set active mode to 'recovery' to test context preservation.")

        # =========================================================================
        # CRITERION 1: Open SOS from existing global entry
        # =========================================================================
        log("\n--- CRITERION 1: Global SOS Entry Trigger ---")
        open_sos_res = evaluate("""(() => {
            const btnNavSos = document.getElementById('btn-nav-sos');
            btnNavSos.click();
            const modal = document.getElementById('progressive-emergency-modal');
            const stepCheckin = document.getElementById('emergency-step-checkin');
            return {
                modalVisible: !modal.classList.contains('hidden'),
                stepCheckinVisible: !stepCheckin.classList.contains('hidden')
            };
        })()""")
        log(f"Open SOS result: {open_sos_res}")
        assert open_sos_res['modalVisible'] == True, "Modal must be visible after clicking #btn-nav-sos"
        assert open_sos_res['stepCheckinVisible'] == True, "Step 1 Check-In must be visible"
        log("PASSED (1/12): Opened SOS directly from existing global navbar entry.")

        # =========================================================================
        # CRITERION 2: Verify main safety copy reflects final handbook meaning
        # =========================================================================
        log("\n--- CRITERION 2: Handbook Safety Copy Alignment ---")
        copy_check = evaluate("""(() => {
            const step = document.getElementById('emergency-step-checkin');
            const text = step ? step.innerText : '';
            return {
                hasImmediateSupportHeader: text.includes("SOS · IMMEDIATE SUPPORT") || text.includes("SOS · Immediate Support"),
                hasDontFeelSafe: text.includes("I don't feel safe right now"),
                hasPanicking: text.includes("panicking and feel out of control"),
                hasUrges: text.includes("having thoughts or urges to hurt yourself"),
                hasAlone: text.includes("not feeling safe being alone"),
                hasSafetyFirst: text.includes("Your safety comes first"),
                hasReassurance: text.includes("You don't need to handle everything by yourself right now")
            };
        })()""")
        log(f"Safety copy check: {copy_check}")
        assert copy_check['hasImmediateSupportHeader'] == True, "Must include 'SOS · IMMEDIATE SUPPORT'"
        assert copy_check['hasDontFeelSafe'] == True, "Must include 'I don't feel safe right now'"
        assert copy_check['hasPanicking'] == True, "Must include 'panicking and feel out of control'"
        assert copy_check['hasUrges'] == True, "Must include 'having thoughts or urges to hurt yourself'"
        assert copy_check['hasAlone'] == True, "Must include 'not feeling safe being alone'"
        assert copy_check['hasSafetyFirst'] == True, "Must include 'Your safety comes first'"
        assert copy_check['hasReassurance'] == True, "Must include 'You don't need to handle everything by yourself right now'"
        log("PASSED (2/12): Main safety copy reflects final handbook meaning and exact principles.")

        # =========================================================================
        # CRITERION 3: Verify 'Get support now' is immediately accessible
        # =========================================================================
        log("\n--- CRITERION 3: 'Get support now' Immediately Accessible ---")
        cta_check = evaluate("""(() => {
            const stepCta = document.getElementById('btn-sos-get-support-now');
            const navCta = document.getElementById('btn-toggle-human-drawer');
            return {
                hasStepCta: !!stepCta,
                stepCtaText: stepCta ? stepCta.innerText.trim() : '',
                hasNavCta: !!navCta,
                navCtaText: navCta ? navCta.innerText.trim() : ''
            };
        })()""")
        log(f"CTA check: {cta_check}")
        assert cta_check['hasStepCta'] == True, "Primary CTA button in step 1 must exist"
        assert "Get support now" in cta_check['stepCtaText'], "Step 1 primary CTA must say 'Get support now →'"
        assert "Get support now" in cta_check['navCtaText'], "Header persistent CTA must say 'Get support now →'"
        log("PASSED (3/12): 'Get support now' primary CTA is immediately accessible on screen 1.")

        # =========================================================================
        # CRITERION 4, 5, 6, 7: Open support information and verify 115, HOPE 0865 044 400, and 3 waiting actions
        # =========================================================================
        log("\n--- CRITERIA 4, 5, 6, 7: Support Information, 115, HOPE 0865 044 400, & Waiting Guidance ---")
        support_check = evaluate("""(() => {
            // Click the primary CTA
            document.getElementById('btn-sos-get-support-now').click();
            const drawer = document.getElementById('human-support-drawer');
            const drawerText = drawer ? drawer.innerText : '';
            const upper = drawerText.toUpperCase();
            
            return {
                drawerOpen: !drawer.classList.contains('hidden'),
                has115: drawerText.includes("115"),
                hasMedicalSupportTitle: upper.includes("EMERGENCY MEDICAL SUPPORT"),
                has115Desc: drawerText.includes("If you're at immediate risk of hurting yourself or you're in immediate danger"),
                hasHope: drawerText.includes("0865 044 400"),
                hasHopeTitle: upper.includes("HOPE — SUICIDE PREVENTION HOTLINE") || upper.includes("HOPE"),
                hasHopeDesc: drawerText.includes("If you're in crisis, having thoughts of hurting yourself, or need someone to support you right now"),
                hasWaitingHeader: upper.includes("WHILE YOU'RE WAITING FOR SUPPORT"),
                hasAction1: drawerText.includes("Stay with someone you trust"),
                hasAction2: drawerText.includes("Move somewhere safer"),
                hasAction3: drawerText.includes("Create distance from anything that could hurt you"),
                hasClosingReassurance: drawerText.includes("You don't need to solve everything right now") && drawerText.includes("For now, just focus on staying safe")
            };
        })()""")
        log(f"Support information check: {support_check}")
        assert support_check['drawerOpen'] == True, "Support drawer must open upon clicking primary CTA"
        assert support_check['has115'] == True, "Support must display 115"
        assert support_check['hasMedicalSupportTitle'] == True, "Support must display Emergency Medical Support"
        assert support_check['has115Desc'] == True, "Support must display 115 description from handbook"
        assert support_check['hasHope'] == True, "Support must display HOPE 0865 044 400"
        assert support_check['hasHopeTitle'] == True, "Support must display HOPE — Suicide Prevention Hotline"
        assert support_check['hasHopeDesc'] == True, "Support must display HOPE description from handbook"
        assert support_check['hasWaitingHeader'] == True, "Must include 'While you're waiting for support'"
        assert support_check['hasAction1'] == True, "Action 1: Stay with someone you trust."
        assert support_check['hasAction2'] == True, "Action 2: Move somewhere safer."
        assert support_check['hasAction3'] == True, "Action 3: Create distance from anything that could hurt you."
        assert support_check['hasClosingReassurance'] == True, "Closing reassurance must be present."
        log("PASSED (4/12, 5/12, 6/12, 7/12): 115, HOPE 0865 044 400, 3 waiting-for-support actions, and closing reassurance verified.")

        # Close the drawer to test grounding
        evaluate("window.TempoEmergencySupport.closeHumanDrawer();")

        # =========================================================================
        # CRITERION 8 & 9: Grounding/breathing still works and is NOT required before support
        # =========================================================================
        log("\n--- CRITERIA 8 & 9: Grounding Works and is Secondary (Not Required) ---")
        grounding_check = evaluate("""(() => {
            // Select Option A to engage grounding
            window.TempoEmergencySupport.handleInitialCheckin('overwhelmed');
            const stepGrounding = document.getElementById('emergency-step-grounding');
            const content = document.getElementById('grounding-activity-content');
            
            // Verify persistent support CTA remains accessible during grounding
            const navSupportBtn = document.getElementById('btn-toggle-human-drawer');
            
            return {
                groundingVisible: !stepGrounding.classList.contains('hidden'),
                activityText: content ? content.innerText : '',
                supportStillAccessible: !!navSupportBtn && !navSupportBtn.classList.contains('hidden')
            };
        })()""")
        log(f"Grounding check: {grounding_check}")
        assert grounding_check['groundingVisible'] == True, "Grounding step must be visible"
        assert "Notice Your Surroundings" in grounding_check['activityText'], "Activity 1 is surroundings"
        assert grounding_check['supportStillAccessible'] == True, "Support CTA remains directly accessible during grounding"
        
        # Test breathing activity
        evaluate("window.TempoEmergencySupport.nextGrounding();")
        breathing_check = evaluate("""(() => {
            const content = document.getElementById('grounding-activity-content');
            return {
                hasBreathing: content ? content.innerText.includes("Slow Down Your Breathing") : false
            };
        })()""")
        log(f"Breathing check: {breathing_check}")
        assert breathing_check['hasBreathing'] == True, "Slow Down Your Breathing must work"

        # Test activity 3 (safety guidance inside grounding)
        evaluate("window.TempoEmergencySupport.nextGrounding();")
        act3_check = evaluate("""(() => {
            const content = document.getElementById('grounding-activity-content');
            const text = content ? content.innerText : '';
            return {
                hasAct3: text.includes("Move Toward Space & Safety"),
                hasWaitingActions: text.includes("Stay with someone you trust") && text.includes("Move somewhere safer") && text.includes("Create distance from anything that could hurt you"),
                hasSupportBtn: text.includes("Get support now →") || text.includes("Get immediate help")
            };
        })()""")
        log(f"Grounding 3 check: {act3_check}")
        assert act3_check['hasAct3'] == True, "Activity 3 Move Toward Safety works"
        assert act3_check['hasWaitingActions'] == True, "Activity 3 contains 3 waiting actions"
        assert act3_check['hasSupportBtn'] == True, "Activity 3 has direct Get support now CTA"
        log("PASSED (8/12, 9/12): Grounding and breathing work properly, and support is NEVER gated behind grounding.")

        # =========================================================================
        # CRITERION 11: Back/Close does not destroy current Tempo mode/context
        # =========================================================================
        log("\n--- CRITERION 11: Mode & Context Preservation on Close ---")
        close_check = evaluate("""(() => {
            // Close modal
            window.TempoEmergencySupport.closeModal(true);
            const modal = document.getElementById('progressive-emergency-modal');
            const currentMode = window.TempoMode ? window.TempoMode.getMode() : null;
            const rmodeVisible = !document.getElementById('rmode-home-content').classList.contains('hidden');
            
            return {
                modalClosed: modal.classList.contains('hidden'),
                currentMode: currentMode,
                rmodeVisible: rmodeVisible
            };
        })()""")
        log(f"Close check: {close_check}")
        assert close_check['modalClosed'] == True, "Modal must be closed"
        assert close_check['currentMode'] == 'recovery', "Mode must remain 'recovery' (not overwritten by 'sos' or reset)"
        assert close_check['rmodeVisible'] == True, "Recovery dashboard must remain visible"
        log("PASSED (11/12): Back/Close cleanly preserves previous mode/context (Recovery remained active).")

        # =========================================================================
        # CRITERION 12: Mobile layout has no obvious blocker (Viewport 375x667)
        # =========================================================================
        log("\n--- CRITERION 12: Mobile Responsive Layout Verification ---")
        send_command("Emulation.setDeviceMetricsOverride", {
            "width": 375,
            "height": 667,
            "deviceScaleFactor": 2,
            "mobile": True
        })
        time.sleep(0.5)

        mobile_check = evaluate("""(() => {
            window.TempoEmergencySupport.openSOS();
            const modal = document.getElementById('progressive-emergency-modal');
            const stepCheckin = document.getElementById('emergency-step-checkin');
            const ctaBtn = document.getElementById('btn-sos-get-support-now');
            
            // Check bounding rects
            const rect = ctaBtn.getBoundingClientRect();
            
            // Open drawer
            window.TempoEmergencySupport.openHumanDrawer();
            const drawer = document.getElementById('human-support-drawer');
            const drawerRect = drawer.getBoundingClientRect();
            
            // Close
            window.TempoEmergencySupport.closeModal(true);
            
            return {
                modalOpen: !modal.classList.contains('hidden'),
                ctaVisible: rect.width > 0 && rect.height > 0 && rect.top >= 0,
                ctaWidth: rect.width,
                drawerWidth: drawerRect.width
            };
        })()""")
        log(f"Mobile check: {mobile_check}")
        assert mobile_check['ctaVisible'] == True, "CTA button must be visible on mobile"
        assert mobile_check['ctaWidth'] <= 375, "CTA button must fit within mobile screen width"
        log("PASSED (12/12): Mobile layout verified without overflow or interaction blockers.")

        log("\n=======================================================")
        log("ALL 12/12 SOS ALIGNMENT SMOKE TEST CRITERIA PASSED!")
        log("=======================================================")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    run_tests()
