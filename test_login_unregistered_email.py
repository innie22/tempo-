"""
Automated Test Suite: Fix Login Accepting Unregistered Emails
Verifies TC1 through TC8, Error Sanitization, No Fake Sessions, and Localization.
"""

import json
import os
import subprocess
import tempfile
import time
import urllib.request
import websocket

def log(msg):
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode('ascii', errors='replace').decode('ascii'), flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_login_guard_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9272
    
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
        for _ in range(30):
            ready = eval_js("Boolean(window.TempoMode && window.TempoAuth && window.TempoApp && window.TempoAuth.getAuthState() !== 'AUTH_LOADING')")
            if ready:
                break
            time.sleep(0.5)

        # Clear state for a pristine test run
        eval_js("""
            (() => {
                localStorage.clear();
                sessionStorage.clear();
                if (window.TempoAuth && typeof window.TempoAuth.signOut === 'function') {
                    window.TempoAuth.signOut();
                }
                window.location.reload();
            })()
        """)
        time.sleep(1.5)

        # Reconnect after reload
        if ws:
            try: ws.close()
            except Exception: pass
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
        ws = websocket.create_connection(ws_url)

        # Wait for ready after reload
        for _ in range(30):
            ready = eval_js("Boolean(window.TempoMode && window.TempoAuth && window.TempoApp && window.TempoAuth.getAuthState() !== 'AUTH_LOADING')")
            if ready:
                break
            time.sleep(0.5)

        log("\n=======================================================")
        log("STARTING LOGIN AUTHENTICATION GUARD VERIFICATION")
        log("=======================================================")

        # ---------------------------------------------------------------------
        # TC1: Unregistered email fails login
        # ---------------------------------------------------------------------
        log("\n--- TC1: Unregistered email fails login ---")
        tc1_res = eval_js("""
            (async () => {
                window.TempoAuth.setAuthLanguage('en');
                window.TempoAuth.openSignInModal();

                // Attempt to sign in with an email that was NEVER registered
                const loginSuccess = await window.TempoAuth.signIn("ghost.user@never-registered.org", "AnyPassword123!");
                
                const authState = window.TempoAuth.getAuthState();
                const user = window.TempoAuth.getCurrentUser();
                const activeContext = window.TempoMode.getActiveContext();
                const signinModal = document.getElementById('modal-signin');
                const signinOpen = signinModal && !signinModal.classList.contains('hidden');
                
                const errBox = document.getElementById('auth-login-error-box');
                const errVisible = errBox && !errBox.classList.contains('hidden');
                const errTitle = document.getElementById('auth-login-error-title')?.textContent.trim();
                const errDesc = document.getElementById('auth-login-error-desc')?.textContent.trim();

                return {
                    loginSuccess,
                    authState,
                    hasUser: user !== null,
                    activeContext,
                    signinOpen,
                    errVisible,
                    errTitle,
                    errDesc
                };
            })()
        """)
        assert tc1_res["loginSuccess"] is False, "Login with unregistered email MUST fail (return false)"
        assert tc1_res["authState"] == "anonymous", f"User must remain anonymous, got {tc1_res['authState']}"
        assert tc1_res["hasUser"] is False, "No user object should exist after failed login"
        assert tc1_res["activeContext"] is None, f"activeContext must remain null, got {tc1_res['activeContext']}"
        assert tc1_res["signinOpen"] is True, "User must remain in Sign In modal on failed login"
        assert tc1_res["errVisible"] is True, "Sign-in error box must be displayed"
        assert tc1_res["errDesc"] == "Email or password is incorrect.", f"Expected generic error, got: {tc1_res['errDesc']}"
        assert tc1_res["errTitle"] == "Notice", f"Expected 'Notice', got: {tc1_res['errTitle']}"
        log("PASS: TC1 Unregistered email rejected safely; user remains anonymous and in signin modal.")

        # ---------------------------------------------------------------------
        # TC1 Localization: Vietnamese generic error message
        # ---------------------------------------------------------------------
        log("\n--- TC1 (Localization): Vietnamese generic error message ---")
        tc1_vi = eval_js("""
            (async () => {
                window.TempoAuth.setAuthLanguage('vi');
                window.TempoAuth.openSignInModal();
                const loginSuccess = await window.TempoAuth.signIn("unregistered.vn@tempo.app", "WrongPass!");
                const errDesc = document.getElementById('auth-login-error-desc')?.textContent.trim();
                const errTitle = document.getElementById('auth-login-error-title')?.textContent.trim();
                return { loginSuccess, errDesc, errTitle };
            })()
        """)
        assert tc1_vi["loginSuccess"] is False
        assert tc1_vi["errDesc"] == "Email hoặc mật khẩu không chính xác.", f"Expected VI error, got: {tc1_vi['errDesc']}"
        assert tc1_vi["errTitle"] == "Thông báo", f"Expected 'Thông báo', got: {tc1_vi['errTitle']}"
        log("PASS: TC1 Vietnamese error message verified.")

        # ---------------------------------------------------------------------
        # TC2: Existing email + wrong password
        # ---------------------------------------------------------------------
        log("\n--- TC2: Existing email + wrong password ---")
        # Register a valid user
        eval_js("""
            (async () => {
                window.TempoAuth.setAuthLanguage('en');
                window.TempoAuth.openRegisterModal();
                await window.TempoAuth.register("Valid Alice", "alice@tempo.app", "AliceSecretPass123!");
            })()
        """)
        tc2_res = eval_js("""
            (async () => {
                window.TempoAuth.openSignInModal();
                // Attempt login with wrong password
                const loginSuccess = await window.TempoAuth.signIn("alice@tempo.app", "TotallyWrongPassword!");
                
                const authState = window.TempoAuth.getAuthState();
                const user = window.TempoAuth.getCurrentUser();
                const activeContext = window.TempoMode.getActiveContext();
                const errDesc = document.getElementById('auth-login-error-desc')?.textContent.trim();

                return {
                    loginSuccess,
                    authState,
                    hasUser: user !== null,
                    activeContext,
                    errDesc
                };
            })()
        """)
        assert tc2_res["loginSuccess"] is False, "Login with wrong password must fail"
        assert tc2_res["authState"] == "anonymous", "User must remain anonymous on wrong password"
        assert tc2_res["hasUser"] is False, "No user object on wrong password"
        assert tc2_res["activeContext"] is None, "activeContext must remain null"
        assert tc2_res["errDesc"] == "Email or password is incorrect.", "Must use identical generic error message"
        log("PASS: TC2 Wrong password fails safely with identical generic error (no account enumeration).")

        # ---------------------------------------------------------------------
        # TC3: Existing email + correct password
        # ---------------------------------------------------------------------
        log("\n--- TC3: Existing email + correct password ---")
        tc3_res = eval_js("""
            (async () => {
                window.TempoAuth.openSignInModal();
                const loginSuccess = await window.TempoAuth.signIn("alice@tempo.app", "AliceSecretPass123!");
                
                const authState = window.TempoAuth.getAuthState();
                const user = window.TempoAuth.getCurrentUser();
                const signinModal = document.getElementById('modal-signin');
                const signinClosed = signinModal && signinModal.classList.contains('hidden');

                return {
                    loginSuccess,
                    authState,
                    userEmail: user?.email,
                    signinClosed
                };
            })()
        """)
        assert tc3_res["loginSuccess"] is True, "Login with correct credentials must succeed"
        assert tc3_res["authState"] == "authenticated", f"Expected authenticated, got {tc3_res['authState']}"
        assert tc3_res["userEmail"] == "alice@tempo.app", f"Expected alice@tempo.app, got {tc3_res['userEmail']}"
        assert tc3_res["signinClosed"] is True, "Sign In modal should close on success"
        log("PASS: TC3 Valid credentials log in successfully and authenticate user.")

        # ---------------------------------------------------------------------
        # TC4: Unregistered email + Pending Intent
        # ---------------------------------------------------------------------
        log("\n--- TC4: Unregistered email + Pending Intent ---")
        # Sign out to return to guest
        eval_js("window.TempoAuth.signOut();")
        tc4_res = eval_js("""
            (async () => {
                // Guest initiates protected tool (Wplan)
                window.TempoMode.setPendingIntent({
                    type: 'tool',
                    destination: 'plan-workspace',
                    sourceContext: 'entry'
                });

                // Guest opens sign-in modal
                window.TempoAuth.openSignInModal();

                // Attempts login with unregistered email
                const loginSuccess = await window.TempoAuth.signIn("fraudulent.intruder@fakemail.org", "Pass123!");

                const authState = window.TempoAuth.getAuthState();
                const pending = window.TempoMode.getPendingIntent();
                const planScreen = document.getElementById('screen-plan-workspace');
                const planVisible = planScreen && !planScreen.classList.contains('hidden');
                const activeContext = window.TempoMode.getActiveContext();

                return {
                    loginSuccess,
                    authState,
                    pendingIntact: pending !== null && pending.destination === 'plan-workspace',
                    planVisible,
                    activeContext
                };
            })()
        """)
        assert tc4_res["loginSuccess"] is False, "Login with unregistered email must fail"
        assert tc4_res["authState"] == "anonymous", "User must remain anonymous"
        assert tc4_res["pendingIntact"] is True, "Pending Intent must NOT be cleared or modified on failed login"
        assert tc4_res["planVisible"] is False, "Wplan must NOT open on failed login"
        assert tc4_res["activeContext"] is None, "activeContext must remain null"
        log("PASS: TC4 Unregistered email does NOT open protected tools; Pending Intent is preserved.")

        # ---------------------------------------------------------------------
        # TC5: Existing account + Pending Intent
        # ---------------------------------------------------------------------
        log("\n--- TC5: Existing account + Pending Intent resumes successfully ---")
        tc5_res = eval_js("""
            (async () => {
                // Sign in with Alice's valid credentials
                const loginSuccess = await window.TempoAuth.signIn("alice@tempo.app", "AliceSecretPass123!");
                
                await new Promise(r => setTimeout(r, 200));
                
                const authState = window.TempoAuth.getAuthState();
                const remainingPending = window.TempoMode.getPendingIntent();
                const planScreen = document.getElementById('screen-plan-workspace');
                const planVisible = planScreen && !planScreen.classList.contains('hidden');

                return {
                    loginSuccess,
                    authState,
                    remainingPending,
                    planVisible
                };
            })()
        """)
        assert tc5_res["loginSuccess"] is True, "Login with valid account must succeed"
        assert tc5_res["authState"] == "authenticated", "User must be authenticated"
        assert tc5_res["planVisible"] is True, "Wplan should be resumed"
        assert tc5_res["remainingPending"] is None, "Pending Intent must be cleared after being resumed"
        log("PASS: TC5 Valid login resumes Pending Intent and clears it.")

        # ---------------------------------------------------------------------
        # TC6: Guest cannot become authenticated through Login UI alone
        # ---------------------------------------------------------------------
        log("\n--- TC6: Guest cannot become authenticated through Login UI alone ---")
        eval_js("window.TempoAuth.signOut();")
        tc6_res = eval_js("""
            (async () => {
                // Attempt several validly-formatted RFC emails that are not registered
                const candidates = [
                    "student.random@harvard.edu",
                    "jane.doe@oxford.ac.uk",
                    "test.account@tempo-wellbeing.vn"
                ];

                const results = [];
                for (const em of candidates) {
                    const ok = await window.TempoAuth.signIn(em, "ComplexP@ssw0rd!2026");
                    results.push({ email: em, ok, state: window.TempoAuth.getAuthState() });
                }
                return results;
            })()
        """)
        for r in tc6_res:
            assert r["ok"] is False, f"Candidate {r['email']} should NOT have logged in"
            assert r["state"] == "anonymous", f"Candidate {r['email']} produced state {r['state']}"
        log("PASS: TC6 Arbitrary valid-looking credentials cannot bypass authentication.")

        # ---------------------------------------------------------------------
        # TC7: No fake session stored in localStorage after failed login
        # ---------------------------------------------------------------------
        log("\n--- TC7: No fake session stored after failed login ---")
        tc7_res = eval_js("""
            (async () => {
                // Ensure signed out
                window.TempoAuth.signOut();
                
                // Submit failed login
                await window.TempoAuth.signIn("fake.session.test@nowhere.com", "anypass");
                
                const devUser = localStorage.getItem('tempo_local_dev_user');
                const authState = window.TempoAuth.getAuthState();
                const currentUser = window.TempoAuth.getCurrentUser();
                const activeContext = window.TempoMode.getActiveContext();

                return {
                    devUser,
                    authState,
                    hasUser: currentUser !== null,
                    activeContext
                };
            })()
        """)
        assert tc7_res["devUser"] is None, f"tempo_local_dev_user must be null, got: {tc7_res['devUser']}"
        assert tc7_res["authState"] == "anonymous", "authState must be anonymous"
        assert tc7_res["hasUser"] is False, "No user object"
        assert tc7_res["activeContext"] is None, "activeContext must remain null"
        log("PASS: TC7 No fake session stored in localStorage; complete state isolation.")

        # ---------------------------------------------------------------------
        # TC8: Existing account isolation
        # ---------------------------------------------------------------------
        log("\n--- TC8: Existing account isolation across login/logout ---")
        # Register Bob with different credentials
        eval_js("""
            (async () => {
                window.TempoAuth.openRegisterModal();
                await window.TempoAuth.register("Bob Builder", "bob.builder@tempo.app", "BobPassword999!");
            })()
        """)
        tc8_res = eval_js("""
            (async () => {
                // Give Alice establishedContext = 'emergency'
                const aliceUid = 'local_user_' + btoa('alice@tempo.app').replace(/[^a-zA-Z0-9]/g, '');
                localStorage.setItem('tempo_user_established_context_' + aliceUid, 'emergency');
                
                // Give Bob establishedContext = 'recovery'
                const bobUid = 'local_user_' + btoa('bob.builder@tempo.app').replace(/[^a-zA-Z0-9]/g, '');
                localStorage.setItem('tempo_user_established_context_' + bobUid, 'recovery');

                // Sign in Alice
                await window.TempoAuth.signIn("alice@tempo.app", "AliceSecretPass123!");
                const aliceUser = window.TempoAuth.getCurrentUser();
                const aliceActive = window.TempoMode.getActiveContext();

                // Sign out
                window.TempoAuth.signOut();
                const postAliceActive = window.TempoMode.getActiveContext();

                // Sign in Bob
                await window.TempoAuth.signIn("bob.builder@tempo.app", "BobPassword999!");
                const bobUser = window.TempoAuth.getCurrentUser();
                const bobActive = window.TempoMode.getActiveContext();

                return {
                    aliceEmail: aliceUser?.email,
                    aliceActive,
                    postAliceActive,
                    bobEmail: bobUser?.email,
                    bobActive
                };
            })()
        """)
        assert tc8_res["aliceEmail"] == "alice@tempo.app"
        assert tc8_res["aliceActive"] == "emergency", f"Expected Alice emergency, got {tc8_res['aliceActive']}"
        assert tc8_res["postAliceActive"] is None, "Guest active context must be null"
        assert tc8_res["bobEmail"] == "bob.builder@tempo.app"
        assert tc8_res["bobActive"] == "recovery", f"Expected Bob recovery, got {tc8_res['bobActive']}"
        log("PASS: TC8 Multi-account isolation preserved with respective established contexts.")

        log("\n=======================================================")
        log("ALL LOGIN AUTHENTICATION GUARD TESTS (TC1-TC8) PASSED!")
        log("=======================================================")

    finally:
        if ws:
            try: ws.close()
            except Exception: pass
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                try: proc.kill()
                except Exception: pass
        import shutil
        try: shutil.rmtree(user_data_dir, ignore_errors=True)
        except Exception: pass

if __name__ == "__main__":
    run_tests()
