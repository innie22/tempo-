"""
Test Suite: Strack Authentication Boundary & Display Name Mapping Verification
==============================================================================
Verifies contract rules for Strack (UI display label: "Self-check"):
1. Guest -> Rmode -> Self-check -> Auth Gate appears BEFORE Strack opens
2. Guest -> Self-check / Strack -> Cancel Auth -> Strack does not open; no Rmode access; Pending Intent cleared
3. Guest -> Self-check / Strack -> Login -> Login success resumes Strack
4. Authenticated -> Rmode -> Self-check -> Strack opens directly (NO Auth Gate)
5. Authenticated -> Rmode -> Self-check -> Return -> Returns to Rmode Dashboard
6. Verify: "Self-check" display label maps to internal destination "strack"
7. Verify: Ucheck remains a separate destination and is not affected
"""

import subprocess
import time
import json
import urllib.request
import websocket
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run_tests():
    port = 9257
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    user_data_dir = tempfile.mkdtemp(prefix="tempo_test_strack_auth_")
    
    cmd = [
        edge_path,
        "--headless",
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
                    pages = [t for t in tabs if t.get("type") == "page" and "localhost:8000" in t.get("url", "")]
                    if pages:
                        ws_url = pages[0]["webSocketDebuggerUrl"]
                        break
            except Exception:
                time.sleep(0.5)
                
        if not ws_url:
            raise RuntimeError("Failed to connect to Edge CDP endpoint")
            
        log(f"Connected to CDP page: {ws_url}")
        ws = websocket.create_connection(ws_url)
        
        msg_id = 1
        def send_cmd(method, params=None):
            nonlocal msg_id
            cid = msg_id
            msg_id += 1
            req = {"id": cid, "method": method}
            if params:
                req["params"] = params
            ws.send(json.dumps(req))
            while True:
                raw = ws.recv()
                msg = json.loads(raw)
                if msg.get("id") == cid:
                    if "error" in msg:
                        raise RuntimeError(f"CDP error: {msg['error']}")
                    return msg.get("result", {})

        def eval_js(expr):
            res = send_cmd("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True
            })
            if "exceptionDetails" in res:
                raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        log("Waiting for app and TempoMode to initialize...")
        for _ in range(40):
            ready = eval_js("Boolean(window.TempoMode && window.TempoAuth && window.TempoApp)")
            if ready:
                break
            time.sleep(0.5)

        # Helper to check if any Strack modal/screen is open
        def is_strack_open():
            return eval_js("""
                (() => {
                    const mManage = document.getElementById('modal-selfcheck-manage');
                    const mDaily = document.getElementById('modal-selfcheck-daily');
                    const mTracker = document.getElementById('modal-selfcheck-tracker-edit');
                    const mView = document.getElementById('modal-selfcheck-view');
                    const mSetup = document.getElementById('modal-recovery-setup');
                    const sStress = document.getElementById('screen-stress-check');

                    const isVis = el => el && !el.classList.contains('hidden');
                    return isVis(mManage) || isVis(mDaily) || isVis(mTracker) || isVis(mView) || isVis(mSetup) || isVis(sStress);
                })()
            """)

        # Clear state for clean testing
        eval_js("""
            (() => {
                localStorage.clear();
                sessionStorage.clear();
                if (window.TempoAuth && typeof window.TempoAuth.signOut === 'function') {
                    window.TempoAuth.signOut();
                }
            })()
        """)
        time.sleep(1)

        log("\n=======================================================")
        log("STARTING STRACK AUTHENTICATION BOUNDARY TEST SUITE")
        log("=======================================================\n")

        # ---------------------------------------------------------------------
        # TEST 6: Verify display label "Self-check" maps to internal destination "strack"
        # ---------------------------------------------------------------------
        log("--- TEST 6: Display Label Mapping (Self-check -> strack) ---")
        label_mapped = eval_js("window.TempoMode.getDestinationDisplayName('strack')")
        assert label_mapped == "Self-check", f"Expected 'Self-check', got: {label_mapped}"
        
        is_valid_dest = eval_js("window.TempoMode.isValidPendingIntent({ destination: 'strack', action: 'open' })")
        assert is_valid_dest is True, "Internal destination 'strack' must be a valid pending intent destination"
        log("✓ Test 6 PASSED: Display label 'Self-check' maps to internal destination 'strack'.")

        # ---------------------------------------------------------------------
        # TEST 7: Verify Ucheck remains a separate destination and is unaffected
        # ---------------------------------------------------------------------
        log("\n--- TEST 7: Destination Distinction (Ucheck vs Strack) ---")
        ucheck_mapped = eval_js("window.TempoMode.getDestinationDisplayName('ucheck')")
        assert ucheck_mapped == "Unclear Mode assessment", f"Expected 'Unclear Mode assessment', got: {ucheck_mapped}"
        assert ucheck_mapped != label_mapped, "Ucheck display name must NOT collide with Strack display name"
        
        # Test guest opening Ucheck creates intent for 'ucheck' (not 'strack')
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'entry' });")
        time.sleep(0.3)
        ucheck_intent = eval_js("window.TempoMode.getPendingIntent()")
        assert ucheck_intent is not None, "Ucheck must create pending intent for guest"
        assert ucheck_intent["destination"] == "ucheck", f"Expected destination 'ucheck', got {ucheck_intent['destination']}"
        eval_js("window.TempoAuth.cancelAuthModal();")
        time.sleep(0.3)
        log("✓ Test 7 PASSED: Ucheck remains a distinct destination ('ucheck') and is unaffected by Strack.")

        # ---------------------------------------------------------------------
        # TEST 1: Guest -> Rmode -> Self-check
        # Expected: Auth Gate appears BEFORE Strack opens
        # ---------------------------------------------------------------------
        log("\n--- TEST 1: Guest -> Rmode -> Self-check -> Auth Gate Appears BEFORE Strack Opens ---")
        # Ensure user is anonymous
        auth_state = eval_js("window.TempoAuth.getAuthState()")
        assert auth_state == "anonymous", f"Must be anonymous, got {auth_state}"

        # Guest clicks Self-check in Recovery Mode context
        eval_js("""
            (() => {
                // Simulate clicking Self-check from Recovery Mode context
                window.TempoMode.setSourceContext('recovery');
                window.TempoMode.openStrack('setup');
            })()
        """)
        time.sleep(0.5)

        t1_state = eval_js("""
            (() => {
                const signInModal = document.getElementById('modal-signin');
                const intent = window.TempoMode.getPendingIntent();
                return {
                    authGateVisible: signInModal && !signInModal.classList.contains('hidden'),
                    intent: intent,
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext()
                };
            })()
        """)

        assert t1_state["authGateVisible"] is True, "Auth Gate modal MUST be visible for guest clicking Self-check"
        assert is_strack_open() is False, "Strack MUST NOT open for guest before authentication"
        assert t1_state["intent"] is not None, "Pending Intent must be created for Strack"
        assert t1_state["intent"]["destination"] == "strack", f"Pending Intent destination must be 'strack', got: {t1_state['intent']['destination']}"
        assert t1_state["intent"]["source"] == "recovery", f"Source context must be preserved as 'recovery', got: {t1_state['intent']['source']}"
        assert t1_state["activeContext"] is None, "activeContext must NOT become recovery before authentication"
        log("✓ Test 1 PASSED: Auth Gate appeared BEFORE Strack opened. Destination is strictly 'strack'.")

        # ---------------------------------------------------------------------
        # TEST 2: Guest -> Self-check / Strack -> Cancel Auth
        # Expected: Strack does not open; no Recovery Mode access; Pending Intent cleared
        # ---------------------------------------------------------------------
        log("\n--- TEST 2: Guest -> Cancel Auth -> Strack Closed, No Rmode Access, Intent Cleared ---")
        eval_js("window.TempoAuth.cancelAuthModal();")
        time.sleep(0.5)

        t2_state = eval_js("""
            (() => {
                const signInModal = document.getElementById('modal-signin');
                return {
                    authGateVisible: signInModal && !signInModal.classList.contains('hidden'),
                    intent: window.TempoMode.getPendingIntent(),
                    activeContext: window.TempoMode.getActiveContext(),
                    user: window.TempoAuth.getCurrentUser()
                };
            })()
        """)

        assert t2_state["authGateVisible"] is False, "Auth Gate modal must be closed"
        assert is_strack_open() is False, "Strack must remain closed after cancel"
        assert t2_state["intent"] is None, "Pending Intent must be cleared on cancel"
        assert t2_state["activeContext"] is None, "Guest MUST NOT gain Recovery Mode access through cancel/return"
        assert t2_state["user"] is None, "User must still be anonymous"

        # Explicitly test returnToSourceContext while unauthenticated
        eval_js("window.TempoMode.returnToSourceContext();")
        time.sleep(0.3)
        post_return_ctx = eval_js("window.TempoMode.getActiveContext()")
        assert post_return_ctx is None, f"returnToSourceContext must never grant guest activeContext, got: {post_return_ctx}"
        log("✓ Test 2 PASSED: Strack did not open, guest has no Rmode access, Pending Intent is cleared.")

        # ---------------------------------------------------------------------
        # TEST 3: Guest -> Self-check / Strack -> Login
        # Expected: Login success -> Resume Strack
        # ---------------------------------------------------------------------
        log("\n--- TEST 3: Guest -> Self-check / Strack -> Login -> Resume Strack ---")
        # Trigger Self-check gating again
        eval_js("""
            (() => {
                window.TempoMode.setSourceContext('recovery');
                window.TempoMode.openStrack('manage');
            })()
        """)
        time.sleep(0.5)

        assert eval_js("window.TempoMode.getPendingIntent()") is not None, "Pending Intent must exist"

        # Register and log in
        eval_js("""
            (async () => {
                await window.TempoAuth.register('Strack Student', 'strack.student@test.edu', 'secret123');
                await window.TempoAuth.signIn('strack.student@test.edu', 'secret123');
            })()
        """)
        time.sleep(1.0)

        t3_state = eval_js("""
            (() => {
                const signInModal = document.getElementById('modal-signin');
                const mManage = document.getElementById('modal-selfcheck-manage');
                return {
                    authState: window.TempoAuth.getAuthState(),
                    authGateVisible: signInModal && !signInModal.classList.contains('hidden'),
                    intent: window.TempoMode.getPendingIntent(),
                    manageOpen: mManage && !mManage.classList.contains('hidden'),
                    sourceContext: window.TempoMode.getSourceContext()
                };
            })()
        """)

        assert t3_state["authState"] == "authenticated", f"Expected authenticated, got: {t3_state['authState']}"
        assert t3_state["authGateVisible"] is False, "Auth Gate must be closed after login"
        assert t3_state["intent"] is None, "Pending Intent must be cleared after fulfillment"
        assert t3_state["manageOpen"] is True, "Strack manage view MUST be resumed after login"
        assert t3_state["sourceContext"] == "recovery", f"Source context must remain 'recovery', got: {t3_state['sourceContext']}"
        log("✓ Test 3 PASSED: Login successfully resumed Strack without lingering Pending Intent.")

        # Clean up Strack modal
        eval_js("window.TempoRecoverySelfCheck.closeManage();")
        time.sleep(0.3)

        # ---------------------------------------------------------------------
        # TEST 4: Authenticated -> Rmode -> Self-check
        # Expected: Strack opens directly; NO Auth Gate
        # ---------------------------------------------------------------------
        log("\n--- TEST 4: Authenticated -> Rmode -> Self-check -> Opens Directly Without Auth Gate ---")
        # Enter Recovery Mode
        eval_js("window.TempoMode.requestContext('recovery');")
        time.sleep(0.5)
        assert eval_js("window.TempoMode.getActiveContext()") == "recovery", "Recovery Mode must be active"

        # Click Self-check
        eval_js("window.TempoMode.openStrack('manage');")
        time.sleep(0.5)

        t4_state = eval_js("""
            (() => {
                const signInModal = document.getElementById('modal-signin');
                const mManage = document.getElementById('modal-selfcheck-manage');
                return {
                    authGateVisible: signInModal && !signInModal.classList.contains('hidden'),
                    manageOpen: mManage && !mManage.classList.contains('hidden'),
                    activeSharedTool: window.TempoMode.getActiveSharedTool()
                };
            })()
        """)

        assert t4_state["manageOpen"] is True, "Strack must open directly for authenticated user"
        assert t4_state["authGateVisible"] is False, "Auth Gate MUST NOT appear for authenticated user"
        assert t4_state["activeSharedTool"] == "strack", f"Active shared tool must be 'strack', got: {t4_state['activeSharedTool']}"
        log("✓ Test 4 PASSED: Authenticated user in Rmode opened Strack directly without Auth Gate.")

        # ---------------------------------------------------------------------
        # TEST 5: Authenticated -> Rmode -> Self-check -> Return
        # Expected: Return -> Rmode Dashboard
        # ---------------------------------------------------------------------
        log("\n--- TEST 5: Authenticated -> Rmode -> Self-check -> Return -> Rmode Dashboard ---")
        eval_js("window.TempoMode.returnToSourceContext();")
        time.sleep(0.5)

        t5_state = eval_js("""
            (() => {
                const rmodeHome = document.getElementById('rmode-home-content');
                const mManage = document.getElementById('modal-selfcheck-manage');
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    rmodeVisible: rmodeHome && !rmodeHome.classList.contains('hidden'),
                    manageOpen: mManage && !mManage.classList.contains('hidden'),
                    activeSharedTool: window.TempoMode.getActiveSharedTool()
                };
            })()
        """)

        assert t5_state["manageOpen"] is False, "Strack modal must be closed after return"
        assert t5_state["activeContext"] == "recovery", f"Must return to Recovery Mode, got: {t5_state['activeContext']}"
        assert t5_state["rmodeVisible"] is True, "Recovery Mode Home dashboard must be visible"
        assert t5_state["activeSharedTool"] is None, "activeSharedTool must be cleared after return"
        log("✓ Test 5 PASSED: Returning from Strack returned cleanly to Rmode Dashboard.")

        # ---------------------------------------------------------------------
        # TEST 8: Entry Home -> Strack does NOT create Recovery Context
        # Expected: activeContext remains null, sourceContext = entry, destination = strack
        # ---------------------------------------------------------------------
        log("\n--- TEST 8: Entry Home -> Strack does NOT create Recovery Context ---")
        # Return to Entry Home
        eval_js("window.TempoMode.transitionContext(null);")
        time.sleep(0.5)
        assert eval_js("window.TempoMode.getActiveContext()") is None, "activeContext must be null on Entry Home"
        assert eval_js("window.TempoMode.getSourceContext()") == "entry", "sourceContext must be 'entry' on Entry Home"

        # Open Strack from Entry Home as authenticated user
        eval_js("window.TempoMode.openStrack('open');")
        time.sleep(0.5)

        t8_state = eval_js("""
            (() => {
                const sStress = document.getElementById('screen-stress-check');
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    activeSharedTool: window.TempoMode.getActiveSharedTool(),
                    stressScreenVisible: sStress && !sStress.classList.contains('hidden')
                };
            })()
        """)

        assert t8_state["activeContext"] is None, f"activeContext MUST remain null when opening Strack from Entry, got: {t8_state['activeContext']}"
        assert t8_state["sourceContext"] == "entry", f"sourceContext must remain 'entry', got: {t8_state['sourceContext']}"
        assert t8_state["activeSharedTool"] == "strack", f"activeSharedTool must be 'strack', got: {t8_state['activeSharedTool']}"
        assert t8_state["stressScreenVisible"] is True, "Shared stress check screen must be visible"
        log("✓ Test 8 PASSED: Entry Home -> Strack opened cleanly without creating Recovery Mode (activeContext is null).")

        # ---------------------------------------------------------------------
        # TEST 9: Entry Home -> Strack -> Return -> Returns cleanly to Entry Home
        # Expected: activeContext remains null, Entry Home rendered
        # ---------------------------------------------------------------------
        log("\n--- TEST 9: Entry Home -> Strack -> Return -> Returns to Entry Home ---")
        eval_js("window.TempoMode.returnToSourceContext();")
        time.sleep(0.5)

        t9_state = eval_js("""
            (() => {
                const defaultHome = document.getElementById('dmode-home-content');
                const rmodeHome = document.getElementById('rmode-home-content');
                const sStress = document.getElementById('screen-stress-check');
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    activeSharedTool: window.TempoMode.getActiveSharedTool(),
                    defaultHomeVisible: defaultHome && !defaultHome.classList.contains('hidden'),
                    rmodeVisible: rmodeHome && !rmodeHome.classList.contains('hidden'),
                    stressScreenVisible: sStress && !sStress.classList.contains('hidden')
                };
            })()
        """)

        assert t9_state["activeContext"] is None, f"activeContext MUST remain null after return to Entry, got: {t9_state['activeContext']}"
        assert t9_state["sourceContext"] == "entry", f"sourceContext must be 'entry', got: {t9_state['sourceContext']}"
        assert t9_state["activeSharedTool"] is None, "activeSharedTool must be cleared after return"
        assert t9_state["defaultHomeVisible"] is True, "Entry Home content must be visible"
        assert t9_state["rmodeVisible"] is False, "Recovery Mode content MUST NOT be visible"
        assert t9_state["stressScreenVisible"] is False, "Stress screen must be hidden"
        log("✓ Test 9 PASSED: Strack returned cleanly to Entry Home without switching to Recovery Mode.")

        # ---------------------------------------------------------------------
        # TEST 10: Guest on Entry Home -> Strack -> Login -> Resume Strack -> Return -> Entry Home
        # ---------------------------------------------------------------------
        log("\n--- TEST 10: Guest Entry Home -> Strack -> Auth Gate -> Login -> Resume -> Return -> Entry Home ---")
        # Sign out
        eval_js("window.TempoAuth.signOut();")
        time.sleep(0.5)
        assert eval_js("window.TempoAuth.getAuthState()") == "anonymous", "Must be anonymous"
        assert eval_js("window.TempoMode.getActiveContext()") is None, "activeContext must be null"

        # Guest clicks Strack from Entry Home via navigateTo('strack')
        eval_js("window.TempoApp.navigateTo('strack');")
        time.sleep(0.5)

        t10_gated = eval_js("""
            (() => {
                const signInModal = document.getElementById('modal-signin');
                const intent = window.TempoMode.getPendingIntent();
                return {
                    authGateVisible: signInModal && !signInModal.classList.contains('hidden'),
                    intent: intent,
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext()
                };
            })()
        """)

        assert t10_gated["authGateVisible"] is True, "Auth Gate modal must be visible for guest"
        assert t10_gated["intent"] is not None, "Pending Intent must exist"
        assert t10_gated["intent"]["destination"] == "strack", f"Pending intent destination must be 'strack', got: {t10_gated['intent']['destination']}"
        assert t10_gated["intent"]["source"] == "entry", f"Pending intent source must be 'entry', got: {t10_gated['intent']['source']}"
        assert t10_gated["activeContext"] is None, "activeContext must remain null"

        # Guest signs in
        eval_js("""
            (async () => {
                await window.TempoAuth.signIn('strack.student@test.edu', 'secret123');
            })()
        """)
        time.sleep(1.0)

        t10_resumed = eval_js("""
            (() => {
                const sStress = document.getElementById('screen-stress-check');
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    activeSharedTool: window.TempoMode.getActiveSharedTool(),
                    stressScreenVisible: sStress && !sStress.classList.contains('hidden'),
                    intent: window.TempoMode.getPendingIntent()
                };
            })()
        """)

        assert t10_resumed["intent"] is None, "Pending Intent must be cleared"
        assert t10_resumed["activeSharedTool"] == "strack", "Strack must be active shared tool"
        assert t10_resumed["activeContext"] is None, f"activeContext must remain null after login for Strack opened from Entry, got: {t10_resumed['activeContext']}"
        assert t10_resumed["sourceContext"] == "entry", f"sourceContext must remain 'entry', got: {t10_resumed['sourceContext']}"

        # Click Return
        eval_js("window.TempoMode.returnToSourceContext();")
        time.sleep(0.5)

        t10_returned = eval_js("""
            (() => {
                const defaultHome = document.getElementById('dmode-home-content');
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    defaultHomeVisible: defaultHome && !defaultHome.classList.contains('hidden')
                };
            })()
        """)

        assert t10_returned["activeContext"] is None, "User must still have activeContext = null"
        assert t10_returned["defaultHomeVisible"] is True, "User must be back on Entry Home"
        log("✓ Test 10 PASSED: Guest Entry -> Strack -> Login -> Resumed Strack -> Returned cleanly to Entry Home.")

        # ---------------------------------------------------------------------
        # TEST 11: Emergency Mode -> Strack -> activeContext remains emergency -> Return -> Urmode
        # ---------------------------------------------------------------------
        log("\n--- TEST 11: Emergency Mode -> Strack -> activeContext remains emergency -> Return -> Urmode ---")
        eval_js("window.TempoMode.requestContext('emergency');")
        time.sleep(0.5)
        assert eval_js("window.TempoMode.getActiveContext()") == "emergency", "activeContext must be emergency"

        eval_js("window.TempoMode.openStrack('manage');")
        time.sleep(0.5)

        t11_state = eval_js("""
            (() => {
                const mManage = document.getElementById('modal-selfcheck-manage');
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    manageOpen: mManage && !mManage.classList.contains('hidden'),
                    activeSharedTool: window.TempoMode.getActiveSharedTool()
                };
            })()
        """)

        assert t11_state["activeContext"] == "emergency", "activeContext must remain emergency"
        assert t11_state["sourceContext"] == "emergency", "sourceContext must be emergency"
        assert t11_state["manageOpen"] is True, "Manage modal must be open"
        assert t11_state["activeSharedTool"] == "strack", "activeSharedTool must be 'strack'"

        # Return
        eval_js("window.TempoMode.returnToSourceContext();")
        time.sleep(0.5)

        t11_post = eval_js("""
            (() => {
                const emodeHome = document.getElementById('emode-home-content');
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    emodeVisible: emodeHome && !emodeHome.classList.contains('hidden'),
                    activeSharedTool: window.TempoMode.getActiveSharedTool()
                };
            })()
        """)

        assert t11_post["activeContext"] == "emergency", "activeContext must return to emergency"
        assert t11_post["emodeVisible"] is True, "Urgent Mode Home dashboard must be visible"
        assert t11_post["activeSharedTool"] is None, "activeSharedTool must be cleared"
        log("✓ Test 11 PASSED: Strack correctly preserves emergency context and returns to Urmode Dashboard.")

        log("\n=======================================================")
        log("ALL 11 STRACK DECOUPLING & BOUNDARY TESTS PASSED (100%)")
        log("=======================================================\n")
        return True

    finally:
        if ws:
            try: ws.close()
            except Exception: pass
        if proc:
            proc.kill()

if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
