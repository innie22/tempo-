import subprocess
import time
import json
import urllib.request
import tempfile
import os
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_strack_reg_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9278
    
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
                    if "error" in resp:
                        raise RuntimeError(f"CDP error: {resp['error']}")
                    return resp.get("result", {})

        def eval_js(expr):
            res = send_command("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
            if "exceptionDetails" in res:
                raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        log("Waiting for app and Tempo modules to initialize...")
        for _ in range(40):
            try:
                ready = eval_js("Boolean(window.TempoMode && window.TempoAuth && window.TempoApp)")
                if ready:
                    break
            except Exception:
                pass
            time.sleep(0.5)

        # Clear state
        eval_js("""
            (() => {
                localStorage.clear();
                sessionStorage.clear();
                if (window.TempoAuth && typeof window.TempoAuth.signOut === 'function') {
                    window.TempoAuth.signOut();
                }
            })()
        """)
        time.sleep(0.5)

        for _ in range(40):
            try:
                ready = eval_js("Boolean(window.TempoMode && window.TempoAuth && window.TempoApp)")
                if ready:
                    break
            except Exception:
                pass
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
                    return Boolean(isVis(mManage) || isVis(mDaily) || isVis(mTracker) || isVis(mView) || isVis(mSetup) || isVis(sStress));
                })()
            """)

        log("\n=======================================================")
        log("STARTING STRACK REGISTRATION vs LOGIN CONTRACT TESTS")
        log("=======================================================\n")

        # -------------------------------------------------------------
        # TEST 1: Guest -> Strack -> Auth Gate -> Register -> Register Success
        # Strack remains blocked and Login is shown.
        # -------------------------------------------------------------
        log("--- TEST 1: Guest -> Strack -> Auth Gate -> Register -> Register Success ---")
        init_state = eval_js("""
            (() => {
                return {
                    authState: window.TempoAuth.getAuthState(),
                    currentUser: window.TempoAuth.getCurrentUser(),
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext()
                };
            })()
        """)
        assert init_state["authState"] == 'anonymous', "Guest must be anonymous"
        assert init_state["currentUser"] is None, "Guest currentUser must be null"

        # Guest selects Strack (Self-check)
        eval_js("window.TempoMode.openStrack('open', { sourceContext: 'entry' });")
        time.sleep(0.3)

        gate_state = eval_js("""
            (() => {
                const signInModal = document.getElementById('modal-signin');
                const stressCheckScreen = document.getElementById('screen-stress-check');
                return {
                    modalOpen: !signInModal.classList.contains('hidden'),
                    screenHidden: stressCheckScreen.classList.contains('hidden'),
                    pendingIntent: window.TempoMode.getPendingIntent(),
                    activeSharedTool: window.TempoMode.getActiveSharedTool()
                };
            })()
        """)
        assert gate_state["modalOpen"] is True, "Sign In modal must open for guest Strack access"
        assert gate_state["screenHidden"] is True, "Strack screen must remain hidden"
        assert gate_state["pendingIntent"] is not None, "Pending intent must be set"
        assert gate_state["pendingIntent"]["destination"] == 'strack', "Pending destination must be 'strack'"
        assert gate_state["activeSharedTool"] is None, "activeSharedTool must be null"
        log("✓ Guest access to Strack opens Auth Gate and captures Pending Intent without exposing Strack.")

        # Switch to Register Modal
        eval_js("window.TempoAuth.openRegisterModal();")
        time.sleep(0.3)
        assert eval_js("!document.getElementById('modal-register').classList.contains('hidden')") is True, "Register modal open"
        assert eval_js("window.TempoMode.getPendingIntent()") is not None, "Pending intent preserved across modal switch"

        # Fill and submit registration form
        email1 = "new_strack_user_1@tempo.edu"
        pass1 = "Secret123!"
        eval_js(f"""
            (async () => {{
                document.getElementById('reg-display-name').value = 'Strack Tester';
                document.getElementById('reg-email').value = '{email1}';
                document.getElementById('reg-password').value = '{pass1}';
                await window.TempoAuth.register('Strack Tester', '{email1}', '{pass1}');
            }})()
        """)
        time.sleep(0.5)

        # Verify state immediately after Register Success:
        reg_success_state = eval_js("""
            (() => {
                const signInModal = document.getElementById('modal-signin');
                const regModal = document.getElementById('modal-register');
                const stressCheckScreen = document.getElementById('screen-stress-check');
                const emailInput = document.getElementById('signin-email');
                return {
                    authState: window.TempoAuth.getAuthState(),
                    currentUser: window.TempoAuth.getCurrentUser(),
                    signInModalOpen: !signInModal.classList.contains('hidden'),
                    regModalClosed: regModal.classList.contains('hidden'),
                    prefilledEmail: emailInput ? emailInput.value : '',
                    screenHidden: stressCheckScreen.classList.contains('hidden'),
                    activeSharedTool: window.TempoMode.getActiveSharedTool(),
                    activeContext: window.TempoMode.getActiveContext(),
                    pendingIntent: window.TempoMode.getPendingIntent()
                };
            })()
        """)
        assert reg_success_state["authState"] == 'anonymous', f"Expected authState='anonymous', got {reg_success_state['authState']}"
        assert reg_success_state["currentUser"] is None, "currentUser must be null after Register Success"
        assert reg_success_state["signInModalOpen"] is True, "Sign In modal must be open after Register Success"
        assert reg_success_state["regModalClosed"] is True, "Register modal must be closed"
        assert reg_success_state["prefilledEmail"] == email1, f"Sign in email input must be prefilled with {email1}"
        assert reg_success_state["screenHidden"] is True, "CRITICAL: Strack screen MUST REMAIN HIDDEN after Register Success"
        assert reg_success_state["activeSharedTool"] is None, "CRITICAL: activeSharedTool must remain null"
        assert reg_success_state["activeContext"] is None, "CRITICAL: activeContext must remain null"
        assert reg_success_state["pendingIntent"] is not None, "CRITICAL: Pending Intent must be preserved"
        assert reg_success_state["pendingIntent"]["destination"] == 'strack', "Pending destination must remain 'strack'"
        log("✓ TEST 1 PASSED: Register Success keeps user anonymous, preserves pending Strack intent, keeps Strack blocked, and displays Login.")

        # -------------------------------------------------------------
        # TEST 2: Register Success -> Login failure
        # Strack remains blocked.
        # -------------------------------------------------------------
        log("\n--- TEST 2: Register Success -> Login failure ---")
        eval_js(f"""
            (async () => {{
                document.getElementById('signin-password').value = 'WrongPassword123';
                await window.TempoAuth.signIn('{email1}', 'WrongPassword123');
            }})()
        """)
        time.sleep(0.5)

        login_fail_state = eval_js("""
            (() => {
                const signInModal = document.getElementById('modal-signin');
                const stressCheckScreen = document.getElementById('screen-stress-check');
                const errorBox = document.getElementById('auth-login-error-box');
                return {
                    authState: window.TempoAuth.getAuthState(),
                    currentUser: window.TempoAuth.getCurrentUser(),
                    signInModalOpen: !signInModal.classList.contains('hidden'),
                    errorBoxVisible: !errorBox.classList.contains('hidden'),
                    screenHidden: stressCheckScreen.classList.contains('hidden'),
                    activeSharedTool: window.TempoMode.getActiveSharedTool(),
                    activeContext: window.TempoMode.getActiveContext(),
                    pendingIntent: window.TempoMode.getPendingIntent()
                };
            })()
        """)
        assert login_fail_state["authState"] == 'anonymous', "Must remain anonymous after failed login"
        assert login_fail_state["currentUser"] is None, "currentUser must remain null"
        assert login_fail_state["signInModalOpen"] is True, "Sign In modal must remain open"
        assert login_fail_state["errorBoxVisible"] is True, "Generic error box must be displayed"
        assert login_fail_state["screenHidden"] is True, "Strack screen must remain hidden"
        assert login_fail_state["activeSharedTool"] is None, "activeSharedTool must remain null"
        assert login_fail_state["pendingIntent"] is not None, "Pending Intent must be preserved across failed login"
        log("✓ TEST 2 PASSED: Login failure keeps Strack blocked and preserves pending intent.")

        # -------------------------------------------------------------
        # TEST 3: Register Success -> Login Success
        # Strack resumes exactly once; pending intent cleared.
        # -------------------------------------------------------------
        log("\n--- TEST 3: Register Success -> Login Success ---")
        eval_js(f"""
            (async () => {{
                document.getElementById('signin-password').value = '{pass1}';
                await window.TempoAuth.signIn('{email1}', '{pass1}');
            }})()
        """)
        time.sleep(0.8)

        login_success_state = eval_js("""
            (() => {
                const signInModal = document.getElementById('modal-signin');
                const stressCheckScreen = document.getElementById('screen-stress-check');
                return {
                    authState: window.TempoAuth.getAuthState(),
                    currentUser: window.TempoAuth.getCurrentUser(),
                    signInModalClosed: signInModal.classList.contains('hidden'),
                    screenVisible: !stressCheckScreen.classList.contains('hidden'),
                    activeSharedTool: window.TempoMode.getActiveSharedTool(),
                    activeContext: window.TempoMode.getActiveContext(),
                    sourceContext: window.TempoMode.getSourceContext(),
                    pendingIntent: window.TempoMode.getPendingIntent()
                };
            })()
        """)
        assert login_success_state["authState"] == 'authenticated', "Must be authenticated after login success"
        assert login_success_state["currentUser"] is not None, "currentUser must be populated"
        assert login_success_state["signInModalClosed"] is True, "Sign In modal must be closed"
        assert login_success_state["screenVisible"] is True, "CRITICAL: Strack screen must now be visible!"
        assert login_success_state["activeSharedTool"] == 'strack', "activeSharedTool must be 'strack'"
        assert login_success_state["activeContext"] is None, "activeContext must remain null (shared tool from entry)"
        assert login_success_state["sourceContext"] == 'entry', "sourceContext must be 'entry'"
        assert login_success_state["pendingIntent"] is None, "CRITICAL: Pending Intent must be cleared (resumed exactly once)"
        log("✓ TEST 3 PASSED: Login Success authenticates user, resumes Strack exactly once, and clears pending intent.")

        # Return from Strack returns to Entry Home
        eval_js("window.TempoMode.returnToSourceContext();")
        time.sleep(0.3)
        return_state = eval_js("""
            (() => {
                const stressCheckScreen = document.getElementById('screen-stress-check');
                const dmodeHome = document.getElementById('dmode-home-content');
                return {
                    screenHidden: stressCheckScreen.classList.contains('hidden'),
                    dmodeVisible: !dmodeHome.classList.contains('hidden'),
                    activeContext: window.TempoMode.getActiveContext(),
                    activeSharedTool: window.TempoMode.getActiveSharedTool()
                };
            })()
        """)
        assert return_state["screenHidden"] is True, "Strack screen must be hidden after return"
        assert return_state["dmodeVisible"] is True, "Entry Home must be visible"
        assert return_state["activeContext"] is None, "activeContext must remain null"
        assert return_state["activeSharedTool"] is None, "activeSharedTool must be null"
        log("✓ Return from Strack cleanly returns to Entry Home.")

        # -------------------------------------------------------------
        # TEST 4: Supabase auto-session event simulation during signUp
        # Even if signUp returns a session and emits onAuthStateChange SIGNED_IN,
        # Strack must NOT open and pending intent must not be consumed.
        # -------------------------------------------------------------
        log("\n--- TEST 4: Supabase auto-session & onAuthStateChange guard during registration ---")
        # Sign out to test fresh guest flow
        eval_js("window.TempoAuth.signOut();")
        time.sleep(0.5)
        assert eval_js("window.TempoAuth.getAuthState()") == 'anonymous'

        # Set up a mock Supabase client that emits SIGNED_IN during signUp
        eval_js("""
            (() => {
                const mockSession = {
                    access_token: 'fake_jwt_token',
                    user: { id: 'mock_supabase_user_99', email: 'cloud_auto_user@tempo.edu' }
                };
                let authListener = null;

                window.__mockSupabaseClient = {
                    auth: {
                        onAuthStateChange: (cb) => {
                            authListener = cb;
                            return { data: { subscription: { unsubscribe: () => {} } } };
                        },
                        signUp: async ({ email, password }) => {
                            // Simulate Supabase GoTrue firing SIGNED_IN synchronously or concurrently on signUp
                            if (authListener) {
                                await authListener('SIGNED_IN', mockSession);
                            }
                            // Store mock account for subsequent signIn
                            localStorage.setItem('tempo_mock_account_' + email.trim().toLowerCase(), JSON.stringify({
                                id: mockSession.user.id,
                                email: email.trim().toLowerCase(),
                                password: password,
                                full_name: 'Cloud Auto User'
                            }));
                            return { data: { user: mockSession.user, session: mockSession }, error: null };
                        },
                        signOut: async () => {
                            if (authListener) {
                                await authListener('SIGNED_OUT', null);
                            }
                            return { error: null };
                        },
                        getSession: async () => {
                            return { data: { session: null }, error: null };
                        },
                        signInWithPassword: async ({ email, password }) => {
                            return { data: { user: mockSession.user, session: mockSession }, error: null };
                        }
                    },
                    from: (table) => ({
                        select: () => ({
                            eq: () => ({
                                single: async () => ({ data: { id: mockSession.user.id, full_name: 'Cloud Auto User', role: 'student' }, error: null })
                            })
                        })
                    })
                };
            })()
        """)

        # Guest clicks Strack
        eval_js("window.TempoMode.openStrack('open', { sourceContext: 'entry' });")
        time.sleep(0.3)
        assert eval_js("window.TempoMode.getPendingIntent() !== null") is True
        assert eval_js("document.getElementById('screen-stress-check').classList.contains('hidden')") is True

        # Open register and execute registration using the mock Supabase client
        eval_js("window.TempoAuth.openRegisterModal();")
        time.sleep(0.3)

        eval_js("""
            (async () => {
                const origGetClient = window.TempoSupabase ? window.TempoSupabase.getClient : null;
                // Temporarily swap client to simulate Cloud Supabase auto-session
                window.TempoSupabase.getClient = () => window.__mockSupabaseClient;

                try {
                    await window.TempoAuth.register('Cloud Auto User', 'cloud_auto_user@tempo.edu', 'secret123456');
                } finally {
                    window.TempoSupabase.getClient = origGetClient;
                }
            })()
        """)
        time.sleep(0.8)

        cloud_sim_state = eval_js("""
            (() => {
                const signInModal = document.getElementById('modal-signin');
                const stressCheckScreen = document.getElementById('screen-stress-check');
                return {
                    authState: window.TempoAuth.getAuthState(),
                    currentUser: window.TempoAuth.getCurrentUser(),
                    signInModalOpen: !signInModal.classList.contains('hidden'),
                    screenHidden: stressCheckScreen.classList.contains('hidden'),
                    activeSharedTool: window.TempoMode.getActiveSharedTool(),
                    activeContext: window.TempoMode.getActiveContext(),
                    pendingIntent: window.TempoMode.getPendingIntent()
                };
            })()
        """)
        assert cloud_sim_state["authState"] == 'anonymous', f"Expected authState='anonymous', got {cloud_sim_state['authState']}"
        assert cloud_sim_state["currentUser"] is None, "currentUser must be null after auto-session registration"
        assert cloud_sim_state["signInModalOpen"] is True, "Sign In modal must be open"
        assert cloud_sim_state["screenHidden"] is True, "CRITICAL: Strack MUST REMAIN HIDDEN even when Supabase fires SIGNED_IN on signUp!"
        assert cloud_sim_state["activeSharedTool"] is None, "activeSharedTool must be null"
        assert cloud_sim_state["activeContext"] is None, "activeContext must be null"
        assert cloud_sim_state["pendingIntent"] is not None, "CRITICAL: pendingIntent must NOT be wiped by registration cleanup!"
        assert cloud_sim_state["pendingIntent"]["destination"] == 'strack', "pending destination must be 'strack'"
        log("✓ TEST 4 PASSED: Even under Cloud Supabase auto-session + SIGNED_IN event, Strack remains blocked and pending intent is preserved.")

        # Now test that login cleanly fulfills the pending intent
        eval_js("""
            (async () => {
                await window.TempoAuth.signIn('cloud_auto_user@tempo.edu', 'secret123456');
            })()
        """)
        time.sleep(0.8)

        cloud_login_state = eval_js("""
            (() => {
                const stressCheckScreen = document.getElementById('screen-stress-check');
                return {
                    authState: window.TempoAuth.getAuthState(),
                    screenVisible: !stressCheckScreen.classList.contains('hidden'),
                    activeSharedTool: window.TempoMode.getActiveSharedTool(),
                    pendingIntent: window.TempoMode.getPendingIntent()
                };
            })()
        """)
        assert cloud_login_state["authState"] == 'authenticated', "User must be authenticated"
        assert cloud_login_state["screenVisible"] is True, "Strack screen must be visible after login"
        assert cloud_login_state["activeSharedTool"] == 'strack', "activeSharedTool must be 'strack'"
        assert cloud_login_state["pendingIntent"] is None, "pendingIntent must be cleared after fulfillment"
        log("✓ TEST 4b PASSED: Subsequent login resumes Strack cleanly and clears pending intent.")

        # -------------------------------------------------------------
        # TEST 5: Direct navigation guard to #stress-check
        # Guest navigating directly to #stress-check is blocked and routed to Auth Gate.
        # -------------------------------------------------------------
        log("\n--- TEST 5: Direct navigation / hash guard to #stress-check ---")
        eval_js("window.TempoAuth.signOut();")
        time.sleep(0.5)

        eval_js("window.location.hash = '#stress-check';")
        time.sleep(0.5)

        direct_nav_state = eval_js("""
            (() => {
                const signInModal = document.getElementById('modal-signin');
                const stressCheckScreen = document.getElementById('screen-stress-check');
                return {
                    authState: window.TempoAuth.getAuthState(),
                    signInModalOpen: !signInModal.classList.contains('hidden'),
                    screenHidden: stressCheckScreen.classList.contains('hidden'),
                    pendingIntent: window.TempoMode.getPendingIntent()
                };
            })()
        """)
        assert direct_nav_state["screenHidden"] is True, "Direct hash navigation while unauthenticated MUST NOT open Strack"
        assert direct_nav_state["signInModalOpen"] is True, "Must redirect to Auth Gate"
        assert direct_nav_state["pendingIntent"] is not None, "Pending intent set for Strack"
        log("✓ TEST 5 PASSED: Unauthenticated direct route to #stress-check is blocked by route guard.")

        # -------------------------------------------------------------
        # TEST 6: Strack from Recovery Mode (sourceContext = 'recovery')
        # Preserves recovery source context across register -> login.
        # -------------------------------------------------------------
        log("\n--- TEST 6: Strack from Recovery Mode preserves sourceContext and restores activeContext ---")
        eval_js("window.TempoAuth.closeAllAuthModals(); window.TempoMode.clearPendingIntent();")
        time.sleep(0.2)

        # Authenticate user and choose recovery mode
        email_rec = "user_rec_flow@tempo.edu"
        eval_js(f"""
            (async () => {{
                await window.TempoAuth.register('Recovery Tester', '{email_rec}', 'secret123456');
                await window.TempoAuth.signIn('{email_rec}', 'secret123456');
                window.TempoMode.transitionContext('recovery');
            }})()
        """)
        time.sleep(0.5)
        assert eval_js("window.TempoMode.getActiveContext()") == 'recovery'

        # Sign out: guest is now at Entry Home, but previous user had recovery context
        eval_js("window.TempoAuth.signOut();")
        time.sleep(0.5)
        assert eval_js("window.TempoMode.getActiveContext()") is None

        # Guest opens Strack with sourceContext: 'recovery'
        eval_js("window.TempoMode.openStrack('open', { sourceContext: 'recovery' });")
        time.sleep(0.3)
        assert eval_js("window.TempoMode.getPendingIntent().sourceContext") == 'recovery'
        assert eval_js("document.getElementById('screen-stress-check').classList.contains('hidden')") is True

        # Register a NEW account from this gate
        email_new_rec = "new_rec_user@tempo.edu"
        eval_js(f"""
            (async () => {{
                await window.TempoAuth.register('New Rec User', '{email_new_rec}', 'secret123456');
            }})()
        """)
        time.sleep(0.5)
        # Register success: Strack must be blocked!
        assert is_strack_open() is False, "Strack MUST remain blocked after Register Success"
        assert eval_js("window.TempoAuth.getAuthState()") == 'anonymous'
        assert eval_js("window.TempoMode.getPendingIntent()") is not None

        # Sign in: Strack resumes!
        eval_js(f"""
            (async () => {{
                await window.TempoAuth.signIn('{email_new_rec}', 'secret123456');
            }})()
        """)
        time.sleep(0.8)
        assert is_strack_open() is True, "Strack must be open after login"
        assert eval_js("window.TempoMode.getActiveSharedTool()") == 'strack'
        assert eval_js("window.TempoMode.getSourceContext()") == 'recovery'

        # Return: returns to Recovery Mode Dashboard!
        eval_js("window.TempoMode.returnToSourceContext();")
        time.sleep(0.3)
        assert is_strack_open() is False, "Strack must be closed after return"
        assert eval_js("window.TempoMode.getActiveContext()") == 'recovery'
        assert eval_js("!document.getElementById('rmode-home-content').classList.contains('hidden')") is True
        log("✓ TEST 6 PASSED: Strack opened from Recovery Mode preserves sourceContext and returns cleanly to Recovery Dashboard.")

        log("\n=======================================================")
        log("🎉 ALL STRACK REGISTRATION vs LOGIN CONTRACT TESTS PASSED (100%)!")
        log("=======================================================\n")

    finally:
        if ws:
            try: ws.close()
            except Exception: pass
        proc.terminate()
        try: proc.wait(timeout=3)
        except Exception: proc.kill()

if __name__ == "__main__":
    run_tests()
