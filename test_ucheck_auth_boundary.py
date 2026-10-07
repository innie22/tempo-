"""
Test Suite: Ucheck Authentication Boundary Verification
======================================================
Tests the contract rules for Ucheck as an authenticated shared assessment flow:
1. Guest user at Entry Home selects/opens Ucheck -> Gated by Auth Gate (modal opened, banner updated)
2. activeContext remains null; pendingIntent preserves sourceContext = 'entry'
3. Canceling/closing the Auth Gate returns to the original source context (Entry Home)
4. Logging in fulfills pendingIntent -> resumes exact Ucheck assessment without modifying activeContext
5. Ucheck does NOT become an active context (activeContext remains null from Entry)
6. Exiting Ucheck returns to the source context (Entry Home)
7. Flow for Urmode -> Ucheck (Guest) -> Auth Gate -> Login -> Resume Ucheck -> Return -> Urmode (activeContext = emergency)
8. Flow for Rmode -> Ucheck (Guest) -> Auth Gate -> Login -> Resume Ucheck -> Return -> Rmode (activeContext = recovery)
9. Authenticated user opens Ucheck directly without triggering the Auth Gate
"""

import subprocess
import time
import json
import urllib.request
import websocket
import sys
sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run_tests():
    port = 9245
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    user_data_dir = r"C:\Users\YEN NHI\AppData\Local\Temp\edge_test_ucheck_auth_" + str(int(time.time()))
    
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
        log("STARTING UCHECK AUTHENTICATION BOUNDARY VERIFICATION")
        log("=======================================================\n")

        # ---------------------------------------------------------------------
        # TEST 1: Guest at Entry Home -> Open Ucheck -> Auth Gate opens
        # ---------------------------------------------------------------------
        log("--- TEST 1: Guest user at Entry Home attempting to enter Ucheck triggers Auth Gate ---")
        init_state = eval_js("""
            (() => {
                return {
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    isAuthed: Boolean(window.TempoAuth.getCurrentUser()),
                    pendingIntent: window.TempoMode.getPendingIntent()
                };
            })()
        """)
        assert init_state["activeContext"] is None, "Guest should start at activeContext = null"
        assert not init_state["isAuthed"], "User should be unauthenticated guest"
        assert init_state["pendingIntent"] is None, "No pending intent initially"

        # Attempt to open Ucheck as guest from Entry Home
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'entry' });")
        time.sleep(0.5)

        gated_state = eval_js("""
            (() => {
                const signInModal = document.getElementById('modal-signin');
                const umodeContent = document.getElementById('umode-home-content');
                const banner = document.querySelector('#modal-signin .auth-mode-gate-banner');
                const bannerTitle = banner ? banner.querySelector('.auth-mode-gate-title').innerText : '';
                return {
                    signInModalOpen: signInModal && !signInModal.classList.contains('hidden'),
                    umodeVisible: umodeContent && !umodeContent.classList.contains('hidden'),
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    activeSharedTool: window.TempoMode.getActiveSharedTool(),
                    pendingIntent: window.TempoMode.getPendingIntent(),
                    bannerVisible: banner && !banner.classList.contains('hidden'),
                    bannerTitle: bannerTitle
                };
            })()
        """)

        assert gated_state["signInModalOpen"] is True, "Sign In modal must open when guest attempts to enter Ucheck"
        assert gated_state["umodeVisible"] is False, "Ucheck assessment view must NOT be visible for guest"
        assert gated_state["activeContext"] is None, "activeContext must remain null for guest"
        assert gated_state["sourceContext"] == 'entry', "sourceContext must remain 'entry'"
        assert gated_state["activeSharedTool"] is None, "activeSharedTool must remain null until authenticated"
        assert gated_state["pendingIntent"] is not None, "pendingIntent must be recorded"
        assert gated_state["pendingIntent"]["type"] == 'ucheck', f"pendingIntent type must be 'ucheck', got {gated_state['pendingIntent']['type']}"
        assert gated_state["pendingIntent"]["sourceContext"] == 'entry', "pendingIntent must record sourceContext = 'entry'"
        assert gated_state["bannerVisible"] is True, "Auth gate banner must be visible"
        assert "Unclear" in gated_state["bannerTitle"] or "Account" in gated_state["bannerTitle"], f"Banner title should mention Unclear or Account, got: {gated_state['bannerTitle']}"
        log("✓ TEST 1 PASSED: Guest attempting to enter Ucheck is successfully sent to Auth Gate.")

        # ---------------------------------------------------------------------
        # TEST 2: Cancel/Close Auth Gate -> Return to original sourceContext (Entry Home)
        # ---------------------------------------------------------------------
        log("\n--- TEST 2: Canceling Auth Gate returns to original source context (Entry Home) ---")
        eval_js("""
            (() => {
                const closeBtn = document.querySelector('#modal-signin .btn-close-auth-modal');
                if (closeBtn) closeBtn.click();
                else if (window.TempoAuth.cancelAuthModal) window.TempoAuth.cancelAuthModal();
            })()
        """)
        time.sleep(0.5)

        cancel_state = eval_js("""
            (() => {
                const signInModal = document.getElementById('modal-signin');
                const dmodeHome = document.getElementById('dmode-home-content');
                const umodeContent = document.getElementById('umode-home-content');
                return {
                    signInModalOpen: signInModal && !signInModal.classList.contains('hidden'),
                    dmodeVisible: dmodeHome && !dmodeHome.classList.contains('hidden'),
                    umodeVisible: umodeContent && !umodeContent.classList.contains('hidden'),
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    pendingIntent: window.TempoMode.getPendingIntent()
                };
            })()
        """)

        assert cancel_state["signInModalOpen"] is False, "Sign In modal must be closed after cancel"
        assert cancel_state["dmodeVisible"] is True, "Entry Home must be visible after canceling Auth Gate"
        assert cancel_state["umodeVisible"] is False, "Ucheck must remain hidden"
        assert cancel_state["activeContext"] is None, "activeContext must remain null"
        assert cancel_state["sourceContext"] == 'entry', "sourceContext must remain 'entry'"
        assert cancel_state["pendingIntent"] is None, "pendingIntent must be cleared on cancel"
        log("✓ TEST 2 PASSED: Canceling Auth Gate safely returns user to Entry Home.")

        # ---------------------------------------------------------------------
        # TEST 3: Entry -> Ucheck (Guest) -> Login -> Resumes Ucheck -> Return -> Entry
        # ---------------------------------------------------------------------
        log("\n--- TEST 3: Entry -> Ucheck (Guest) -> Login -> Resumes Ucheck -> Return -> Entry ---")
        # Trigger Ucheck again as guest
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'entry' });")
        time.sleep(0.3)
        assert eval_js("Boolean(window.TempoMode.getPendingIntent())") is True

        # Now authenticate through existing auth mechanism
        eval_js("""
            (async () => {
                await window.TempoAuth.signIn('student_ucheck_1@tempo.edu', 'password123');
            })()
        """)
        time.sleep(0.8)

        resume_state = eval_js("""
            (() => {
                const umodeContent = document.getElementById('umode-home-content');
                const signInModal = document.getElementById('modal-signin');
                return {
                    isAuthed: Boolean(window.TempoAuth.getCurrentUser()),
                    signInModalOpen: signInModal && !signInModal.classList.contains('hidden'),
                    umodeVisible: umodeContent && !umodeContent.classList.contains('hidden'),
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    activeSharedTool: window.TempoMode.getActiveSharedTool(),
                    pendingIntent: window.TempoMode.getPendingIntent()
                };
            })()
        """)

        assert resume_state["isAuthed"] is True, "User should now be authenticated"
        assert resume_state["signInModalOpen"] is False, "Sign In modal must be closed after successful login"
        assert resume_state["umodeVisible"] is True, "Ucheck view must be visible after login resumption"
        assert resume_state["activeSharedTool"] == 'ucheck', "activeSharedTool must be 'ucheck'"
        assert resume_state["activeContext"] is None, f"activeContext MUST remain null (Ucheck is not a mode), got {resume_state['activeContext']}"
        assert resume_state["sourceContext"] == 'entry', f"sourceContext must remain 'entry', got {resume_state['sourceContext']}"
        assert resume_state["pendingIntent"] is None, "pendingIntent must be cleared after successful fulfillment"
        log("✓ Resumed Ucheck after login with activeContext = null, sourceContext = 'entry'.")

        # Now exit Ucheck back to Entry Home
        eval_js("window.TempoMode.returnToSourceContext();")
        time.sleep(0.5)

        exit_entry_state = eval_js("""
            (() => {
                const dmodeHome = document.getElementById('dmode-home-content');
                const umodeContent = document.getElementById('umode-home-content');
                return {
                    dmodeVisible: dmodeHome && !dmodeHome.classList.contains('hidden'),
                    umodeVisible: umodeContent && !umodeContent.classList.contains('hidden'),
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    activeSharedTool: window.TempoMode.getActiveSharedTool()
                };
            })()
        """)
        assert exit_entry_state["dmodeVisible"] is True, "Must return to Entry Home"
        assert exit_entry_state["umodeVisible"] is False, "Ucheck must be closed"
        assert exit_entry_state["activeContext"] is None, "activeContext must remain null"
        assert exit_entry_state["activeSharedTool"] is None, "activeSharedTool must be null after return"
        log("✓ TEST 3 PASSED: Entry -> Ucheck -> Login -> Resume Ucheck -> Return -> Entry verified.")

        # ---------------------------------------------------------------------
        # TEST 4: Urmode -> Ucheck (Guest) -> Login -> Resumes Ucheck -> Return -> Urmode
        # ---------------------------------------------------------------------
        log("\n--- TEST 4: Urmode -> Ucheck (Guest) -> Login -> Resumes Ucheck -> Return -> Urmode ---")
        # Sign out to test guest in Urmode context
        eval_js("""
            (() => {
                window.TempoAuth.signOut();
                // Establish Urmode in memory
                window.TempoMode.setMode('emergency');
            })()
        """)
        time.sleep(0.5)

        assert eval_js("window.TempoMode.getActiveContext()") == 'emergency'
        assert eval_js("Boolean(window.TempoAuth.getCurrentUser())") is False

        # Attempt to open Ucheck with sourceContext = 'emergency'
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'emergency' });")
        time.sleep(0.5)

        urmode_gated = eval_js("""
            (() => {
                const signInModal = document.getElementById('modal-signin');
                return {
                    signInModalOpen: signInModal && !signInModal.classList.contains('hidden'),
                    activeContext: window.TempoMode.getActiveContext(),
                    pendingIntent: window.TempoMode.getPendingIntent()
                };
            })()
        """)
        assert urmode_gated["signInModalOpen"] is True, "Sign In modal must open for guest in Urmode"
        assert urmode_gated["activeContext"] == 'emergency', "activeContext must remain 'emergency'"
        assert urmode_gated["pendingIntent"]["sourceContext"] == 'emergency'

        # Login
        eval_js("""
            (async () => {
                await window.TempoAuth.signIn('student_ucheck_urmode@tempo.edu', 'password123');
            })()
        """)
        time.sleep(0.8)

        urmode_resumed = eval_js("""
            (() => {
                const umodeContent = document.getElementById('umode-home-content');
                return {
                    umodeVisible: umodeContent && !umodeContent.classList.contains('hidden'),
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    activeSharedTool: window.TempoMode.getActiveSharedTool()
                };
            })()
        """)
        assert urmode_resumed["umodeVisible"] is True, "Ucheck must be visible"
        assert urmode_resumed["activeContext"] == 'emergency', f"activeContext must remain 'emergency', got {urmode_resumed['activeContext']}"
        assert urmode_resumed["sourceContext"] == 'emergency', f"sourceContext must be 'emergency', got {urmode_resumed['sourceContext']}"
        assert urmode_resumed["activeSharedTool"] == 'ucheck'

        # Return to source context -> must return to Urmode
        eval_js("window.TempoMode.returnToSourceContext();")
        time.sleep(0.5)

        urmode_returned = eval_js("""
            (() => {
                const emodeHome = document.getElementById('emode-home-content');
                const umodeContent = document.getElementById('umode-home-content');
                return {
                    emodeVisible: emodeHome && !emodeHome.classList.contains('hidden'),
                    umodeVisible: umodeContent && !umodeContent.classList.contains('hidden'),
                    activeContext: window.TempoMode.getActiveContext(),
                    activeSharedTool: window.TempoMode.getActiveSharedTool()
                };
            })()
        """)
        assert urmode_returned["emodeVisible"] is True, "Must return to Urmode dashboard"
        assert urmode_returned["umodeVisible"] is False, "Ucheck must be closed"
        assert urmode_returned["activeContext"] == 'emergency', "activeContext must be 'emergency'"
        assert urmode_returned["activeSharedTool"] is None
        log("✓ TEST 4 PASSED: Urmode -> Ucheck -> Login -> Resume Ucheck -> Return -> Urmode verified.")

        # ---------------------------------------------------------------------
        # TEST 5: Rmode -> Ucheck (Guest) -> Login -> Resumes Ucheck -> Return -> Rmode
        # ---------------------------------------------------------------------
        log("\n--- TEST 5: Rmode -> Ucheck (Guest) -> Login -> Resumes Ucheck -> Return -> Rmode ---")
        eval_js("""
            (() => {
                window.TempoAuth.signOut();
                window.TempoMode.setMode('recovery');
            })()
        """)
        time.sleep(0.5)

        assert eval_js("window.TempoMode.getActiveContext()") == 'recovery'
        assert eval_js("Boolean(window.TempoAuth.getCurrentUser())") is False

        # Attempt to open Ucheck with sourceContext = 'recovery'
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'recovery' });")
        time.sleep(0.5)

        rmode_gated = eval_js("""
            (() => {
                const signInModal = document.getElementById('modal-signin');
                return {
                    signInModalOpen: signInModal && !signInModal.classList.contains('hidden'),
                    activeContext: window.TempoMode.getActiveContext(),
                    pendingIntent: window.TempoMode.getPendingIntent()
                };
            })()
        """)
        assert rmode_gated["signInModalOpen"] is True
        assert rmode_gated["activeContext"] == 'recovery'
        assert rmode_gated["pendingIntent"]["sourceContext"] == 'recovery'

        # Login
        eval_js("""
            (async () => {
                await window.TempoAuth.signIn('student_ucheck_rmode@tempo.edu', 'password123');
            })()
        """)
        time.sleep(0.8)

        rmode_resumed = eval_js("""
            (() => {
                const umodeContent = document.getElementById('umode-home-content');
                return {
                    umodeVisible: umodeContent && !umodeContent.classList.contains('hidden'),
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    activeSharedTool: window.TempoMode.getActiveSharedTool()
                };
            })()
        """)
        assert rmode_resumed["umodeVisible"] is True
        assert rmode_resumed["activeContext"] == 'recovery', f"activeContext must remain 'recovery', got {rmode_resumed['activeContext']}"
        assert rmode_resumed["sourceContext"] == 'recovery'
        assert rmode_resumed["activeSharedTool"] == 'ucheck'

        # Return to source context -> must return to Rmode
        eval_js("window.TempoMode.returnToSourceContext();")
        time.sleep(0.5)

        rmode_returned = eval_js("""
            (() => {
                const rmodeHome = document.getElementById('rmode-home-content');
                const umodeContent = document.getElementById('umode-home-content');
                return {
                    rmodeVisible: rmodeHome && !rmodeHome.classList.contains('hidden'),
                    umodeVisible: umodeContent && !umodeContent.classList.contains('hidden'),
                    activeContext: window.TempoMode.getActiveContext(),
                    activeSharedTool: window.TempoMode.getActiveSharedTool()
                };
            })()
        """)
        assert rmode_returned["rmodeVisible"] is True, "Must return to Rmode dashboard"
        assert rmode_returned["umodeVisible"] is False, "Ucheck must be closed"
        assert rmode_returned["activeContext"] == 'recovery'
        assert rmode_returned["activeSharedTool"] is None
        log("✓ TEST 5 PASSED: Rmode -> Ucheck -> Login -> Resume Ucheck -> Return -> Rmode verified.")

        # ---------------------------------------------------------------------
        # TEST 6: Authenticated user opens Ucheck directly without Auth Gate
        # ---------------------------------------------------------------------
        log("\n--- TEST 6: Authenticated user opens Ucheck directly without Auth Gate ---")
        assert eval_js("Boolean(window.TempoAuth.getCurrentUser())") is True

        eval_js("window.TempoMode.openUcheck({ sourceContext: 'entry' });")
        time.sleep(0.3)

        direct_state = eval_js("""
            (() => {
                const signInModal = document.getElementById('modal-signin');
                const umodeContent = document.getElementById('umode-home-content');
                return {
                    signInModalOpen: signInModal && !signInModal.classList.contains('hidden'),
                    umodeVisible: umodeContent && !umodeContent.classList.contains('hidden'),
                    activeSharedTool: window.TempoMode.getActiveSharedTool()
                };
            })()
        """)
        assert direct_state["signInModalOpen"] is False, "Auth modal must NOT open for authenticated user"
        assert direct_state["umodeVisible"] is True, "Ucheck must open directly"
        assert direct_state["activeSharedTool"] == 'ucheck'
        log("✓ TEST 6 PASSED: Authenticated user opens Ucheck directly without Auth Gate.")

        # ---------------------------------------------------------------------
        # TEST 7: Resuming with action options (startNew, resumeDraft, etc.)
        # ---------------------------------------------------------------------
        log("\n--- TEST 7: Resuming with specific action options (startNew: true) ---")
        eval_js("""
            (() => {
                window.TempoAuth.signOut();
                window.TempoMode.transitionContext(null);
            })()
        """)
        time.sleep(0.5)

        # Guest triggers startNew
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'entry', startNew: true });")
        time.sleep(0.3)

        intent7 = eval_js("window.TempoMode.getPendingIntent()")
        assert intent7 is not None and intent7["options"]["startNew"] is True, "pendingIntent should preserve options.startNew"

        # Login
        eval_js("""
            (async () => {
                await window.TempoAuth.signIn('student_options_test@tempo.edu', 'password123');
            })()
        """)
        time.sleep(0.8)

        checkin_stage_state = eval_js("""
            (() => {
                const flowVisible = document.getElementById('unclear-flow-view') !== null;
                const draft = window.TempoUnclearMode.getDraft();
                return {
                    flowVisible,
                    hasDraft: Boolean(draft),
                    stage: draft ? draft.current_stage : null,
                    activeContext: window.TempoMode.getActiveContext()
                };
            })()
        """)
        assert checkin_stage_state["hasDraft"] is True, "startNewCheckIn must have created a fresh draft upon login resumption"
        assert checkin_stage_state["stage"] == 1, "Must be at Stage 1 of new check-in"
        assert checkin_stage_state["activeContext"] is None, "activeContext must remain null"
        log("✓ TEST 7 PASSED: Specific Ucheck action (startNew) cleanly resumed after login.")

        log("\n=======================================================")
        log("🎉 ALL 7 UCHECK AUTHENTICATION BOUNDARY TESTS PASSED (100%)!")
        log("=======================================================\n")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        proc.wait(timeout=5)

if __name__ == "__main__":
    run_tests()
