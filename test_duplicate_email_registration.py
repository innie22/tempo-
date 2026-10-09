"""
Automated Test Suite: Duplicate Account Registration by Email
Verifies TC1 through TC7, Invariant 14, error sanitization, and localization.
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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_dupreg_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9268
    
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
            ready = eval_js("Boolean(window.TempoMode && window.TempoAuth && window.TempoApp)")
            if ready:
                break
            time.sleep(0.5)

        # Clear state
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

        # Wait for ready
        for _ in range(30):
            ready = eval_js("Boolean(window.TempoMode && window.TempoAuth && window.TempoApp)")
            if ready:
                break
            time.sleep(0.5)

        log("\n--- TEST: Supabase GoTrue duplicate error detection contract ---")
        gotrue_checks = eval_js("""
            (() => {
                const fn = window.TempoAuth.isDuplicateEmailError;
                return {
                    emptyIdentities: fn(null, { user: { identities: [] } }),
                    nonEmptyIdentities: fn(null, { user: { identities: [{ id: '1' }] } }),
                    alreadyRegisteredMsg: fn({ message: "User already registered" }, null),
                    alreadyExistsMsg: fn({ message: "Email already exists" }, null),
                    duplicateMsg: fn({ message: "duplicate key value violates unique constraint" }, null),
                    userAlreadyExistsCode: fn({ code: "user_already_exists" }, null),
                    emailExistsCode: fn({ code: "email_exists" }, null),
                    invalidPassword: fn({ message: "Invalid password" }, null)
                };
            })()
        """)
        assert gotrue_checks["emptyIdentities"] is True, "empty identities must be detected as duplicate"
        assert gotrue_checks["nonEmptyIdentities"] is False, "non-empty identities must not be duplicate"
        assert gotrue_checks["alreadyRegisteredMsg"] is True, "already registered message must be detected"
        assert gotrue_checks["alreadyExistsMsg"] is True, "already exists message must be detected"
        assert gotrue_checks["duplicateMsg"] is True, "duplicate constraint message must be detected"
        assert gotrue_checks["userAlreadyExistsCode"] is True, "user_already_exists code must be detected"
        assert gotrue_checks["emailExistsCode"] is True, "email_exists code must be detected"
        assert gotrue_checks["invalidPassword"] is False, "invalid password must not be duplicate"
        log("PASS: Supabase GoTrue duplicate detection contract verified.")

        log("\n--- TC1: Register new email ---")
        # Ensure anonymous
        tc1_init = eval_js("""
            (() => {
                window.TempoAuth.setAuthLanguage('en');
                return {
                    authState: window.TempoAuth.getAuthState(),
                    activeContext: window.TempoMode.getActiveContext()
                };
            })()
        """)
        assert tc1_init["authState"] == "anonymous", f"Expected anonymous, got {tc1_init['authState']}"
        assert tc1_init["activeContext"] is None, f"Expected null activeContext, got {tc1_init['activeContext']}"

        # Register new account
        tc1_reg = eval_js("""
            (async () => {
                window.TempoAuth.openRegisterModal();
                const success = await window.TempoAuth.register("Alex Rivera", "alex.rivera@tempo.app", "Secret123!");
                return {
                    success,
                    authState: window.TempoAuth.getAuthState(),
                    activeContext: window.TempoMode.getActiveContext(),
                    signinModalOpen: !document.getElementById('modal-signin').classList.contains('hidden'),
                    signinEmailValue: document.getElementById('signin-email').value
                };
            })()
        """)
        assert tc1_reg["success"] is True, "New registration should succeed"
        assert tc1_reg["authState"] == "anonymous", "Invariant 14: Register Success does NOT authenticate"
        assert tc1_reg["activeContext"] is None, "activeContext must remain null on registration"
        assert tc1_reg["signinModalOpen"] is True, "Sign In modal should open after registration"
        assert tc1_reg["signinEmailValue"] == "alex.rivera@tempo.app", "Email must be prefilled in signin modal"
        log("PASS: TC1 Register new email verified (Invariant 14 honored).")

        log("\n--- TC2: Register existing email fails safely ---")
        tc2_res = eval_js("""
            (async () => {
                window.TempoAuth.setAuthLanguage('en');
                window.TempoAuth.openRegisterModal();
                // Attempt to register same email with uppercase/spaces variation
                const res = await window.TempoAuth.register("Alex Duplicate", "  ALEX.RIVERA@tempo.app  ", "NewPass999!");
                const errBox = document.getElementById('auth-reg-error-box');
                const errTitle = document.getElementById('auth-reg-error-title');
                const errDesc = document.getElementById('auth-reg-error-desc');
                const errAction = document.getElementById('auth-reg-error-action');
                const regModal = document.getElementById('modal-register');

                return {
                    res,
                    regModalOpen: !regModal.classList.contains('hidden'),
                    errBoxVisible: !errBox.classList.contains('hidden'),
                    errTitle: errTitle.textContent.trim(),
                    errDesc: errDesc.textContent.trim(),
                    errActionVisible: !errAction.classList.contains('hidden'),
                    authState: window.TempoAuth.getAuthState(),
                    activeContext: window.TempoMode.getActiveContext()
                };
            })()
        """)
        assert tc2_res["res"] is False, "Duplicate registration must fail (return false)"
        assert tc2_res["regModalOpen"] is True, "User must remain in Register modal on duplicate error"
        assert tc2_res["errBoxVisible"] is True, "Error box must be visible"
        assert tc2_res["errDesc"] == "This email is already registered. Please log in instead.", f"Expected localized error, got: {tc2_res['errDesc']}"
        assert tc2_res["errActionVisible"] is True, "Log in action button must be visible"
        assert tc2_res["authState"] == "anonymous", "User must remain anonymous"
        assert tc2_res["activeContext"] is None, "activeContext must remain null"
        log("PASS: TC2 Register existing email fails safely with user-friendly error and no state mutation.")

        log("\n--- TC2 (Localization): Vietnamese duplicate error message ---")
        tc2_vi = eval_js("""
            (async () => {
                window.TempoAuth.setAuthLanguage('vi');
                window.TempoAuth.openRegisterModal();
                const res = await window.TempoAuth.register("Alex Duplicate VI", "alex.rivera@tempo.app", "NewPass999!");
                const errDesc = document.getElementById('auth-reg-error-desc').textContent.trim();
                const errTitle = document.getElementById('auth-reg-error-title').textContent.trim();
                const btnText = document.getElementById('auth-reg-error-btn-text').textContent.trim();
                return { res, errDesc, errTitle, btnText };
            })()
        """)
        assert tc2_vi["res"] is False
        assert tc2_vi["errDesc"] == "Email này đã được đăng ký. Vui lòng đăng nhập.", f"Expected VI message, got: {tc2_vi['errDesc']}"
        assert tc2_vi["errTitle"] == "Thông báo", f"Expected VI title, got: {tc2_vi['errTitle']}"
        assert tc2_vi["btnText"] == "Đăng nhập với email này →", f"Expected VI button text, got: {tc2_vi['btnText']}"
        log("PASS: TC2 Vietnamese localization verified.")

        log("\n--- TC3: Register existing email preserves pending intent ---")
        tc3_res = eval_js("""
            (async () => {
                window.TempoAuth.setAuthLanguage('en');
                // Simulate guest triggering Wplan
                window.TempoMode.setPendingIntent({
                    type: 'tool',
                    destination: 'wplan',
                    sourceContext: 'entry'
                });
                
                // Guest goes to Register modal
                window.TempoAuth.openRegisterModal();
                
                // Tries to register with existing email
                const res = await window.TempoAuth.register("Alex Duplicate", "alex.rivera@tempo.app", "WrongPass123");
                
                const pending = window.TempoMode.getPendingIntent();
                const active = window.TempoMode.getActiveContext();
                
                return {
                    res,
                    pending,
                    active
                };
            })()
        """)
        assert tc3_res["res"] is False, "Registration must fail"
        assert tc3_res["pending"] is not None, "Pending intent must NOT be lost on failed registration"
        assert tc3_res["pending"]["destination"] == "wplan", f"Expected pending destination wplan, got {tc3_res['pending']}"
        assert tc3_res["active"] is None, "activeContext must remain null"
        log("PASS: TC3 Register existing email preserves pending intent.")

        log("\n--- TC4: Switch from failed register to login resumes intent ---")
        tc4_res = eval_js("""
            (async () => {
                // Click "Log in with this email ->" action button
                window.TempoAuth.openSignInModal("alex.rivera@tempo.app");
                
                const signinModalOpen = !document.getElementById('modal-signin').classList.contains('hidden');
                const emailPrefilled = document.getElementById('signin-email').value;
                
                // Sign in with correct password
                const loginSuccess = await window.TempoAuth.signIn("alex.rivera@tempo.app", "Secret123!");
                
                // Wait briefly for intent handling
                await new Promise(r => setTimeout(r, 200));
                
                const authState = window.TempoAuth.getAuthState();
                const remainingPending = window.TempoMode.getPendingIntent();
                
                return {
                    signinModalOpen,
                    emailPrefilled,
                    loginSuccess,
                    authState,
                    remainingPending
                };
            })()
        """)
        assert tc4_res["signinModalOpen"] is True, "Sign In modal should open"
        assert tc4_res["emailPrefilled"] == "alex.rivera@tempo.app", "Email must be prefilled"
        assert tc4_res["loginSuccess"] is True, "Sign In must succeed"
        assert tc4_res["authState"] == "authenticated", "User must now be authenticated"
        assert tc4_res["remainingPending"] is None, "Pending intent must be cleared after being resumed"
        log("PASS: TC4 Switch to login resumes intent and clears pending intent.")

        log("\n--- TC5: Existing account establishedContext is preserved ---")
        # Give alex.rivera@tempo.app an establishedContext = 'emergency'
        tc5_res = eval_js("""
            (async () => {
                const uid = window.TempoAuth.getCurrentUserId();
                localStorage.setItem('tempo_user_established_context_' + uid, 'emergency');
                
                // Sign out
                window.TempoAuth.signOut();
                
                // Verify guest
                const guestAuth = window.TempoAuth.getAuthState();
                const guestActive = window.TempoMode.getActiveContext();
                
                // Guest attempts to register using Alex's email
                window.TempoAuth.openRegisterModal();
                const regRes = await window.TempoAuth.register("Imposter", "alex.rivera@tempo.app", "HackerPass123");
                
                // Check Alex's establishedContext is completely intact in storage
                const savedEstablished = localStorage.getItem('tempo_user_established_context_' + uid);
                
                // Guest active context remains null
                const postRegActive = window.TempoMode.getActiveContext();
                
                // Now Alex logs in
                const loginRes = await window.TempoAuth.signIn("alex.rivera@tempo.app", "Secret123!");
                
                return {
                    guestAuth,
                    guestActive,
                    regRes,
                    savedEstablished,
                    postRegActive,
                    loginRes,
                    restoredUid: window.TempoAuth.getCurrentUserId()
                };
            })()
        """)
        assert tc5_res["guestAuth"] == "anonymous", "Should be anonymous after sign out"
        assert tc5_res["guestActive"] is None, "Guest active context must be null"
        assert tc5_res["regRes"] is False, "Duplicate registration must be rejected"
        assert tc5_res["savedEstablished"] == "emergency", "Established context must NOT be overwritten or mutated"
        assert tc5_res["postRegActive"] is None, "Guest active context must remain null"
        assert tc5_res["loginRes"] is True, "Login must succeed"
        log("PASS: TC5 Existing account establishedContext is preserved across duplicate registration attempts.")

        log("\n--- TC6: Two distinct accounts cannot collide ---")
        tc6_res = eval_js("""
            (async () => {
                window.TempoAuth.signOut();
                
                // Register second user: Bob
                window.TempoAuth.openRegisterModal();
                const regBob = await window.TempoAuth.register("Bob Martin", "bob.martin@tempo.app", "BobPass123!");
                
                // Verify Alex's account still exists and is untouched
                const alexAccountRaw = localStorage.getItem('tempo_mock_account_alex.rivera@tempo.app');
                const bobAccountRaw = localStorage.getItem('tempo_mock_account_bob.martin@tempo.app');
                
                const alexAcc = JSON.parse(alexAccountRaw);
                const bobAcc = JSON.parse(bobAccountRaw);
                
                // Attempt to register Bob again -> must fail
                window.TempoAuth.openRegisterModal();
                const regBobDup = await window.TempoAuth.register("Bob Fake", "bob.martin@tempo.app", "OtherPass!");
                
                // Attempt to register Alex again -> must fail
                window.TempoAuth.openRegisterModal();
                const regAlexDup = await window.TempoAuth.register("Alex Fake", "alex.rivera@tempo.app", "OtherPass!");
                
                // Sign in as Bob
                const bobLogin = await window.TempoAuth.signIn("bob.martin@tempo.app", "BobPass123!");
                const bobUser = window.TempoAuth.getCurrentUser();
                
                // Sign out, sign in as Alex
                window.TempoAuth.signOut();
                const alexLogin = await window.TempoAuth.signIn("alex.rivera@tempo.app", "Secret123!");
                const alexUser = window.TempoAuth.getCurrentUser();
                
                return {
                    regBob,
                    alexName: alexAcc.user_metadata.full_name,
                    bobName: bobAcc.user_metadata.full_name,
                    regBobDup,
                    regAlexDup,
                    bobLogin,
                    bobEmail: bobUser.email,
                    alexLogin,
                    alexEmail: alexUser.email
                };
            })()
        """)
        assert tc6_res["regBob"] is True, "Bob registration should succeed"
        assert tc6_res["alexName"] == "Alex Rivera", "Alex account data must not be corrupted"
        assert tc6_res["bobName"] == "Bob Martin", "Bob account data must be isolated"
        assert tc6_res["regBobDup"] is False, "Bob duplicate registration must fail"
        assert tc6_res["regAlexDup"] is False, "Alex duplicate registration must fail"
        assert tc6_res["bobLogin"] is True, "Bob login must succeed"
        assert tc6_res["bobEmail"] == "bob.martin@tempo.app", "Bob session must match Bob"
        assert tc6_res["alexLogin"] is True, "Alex login must succeed"
        assert tc6_res["alexEmail"] == "alex.rivera@tempo.app", "Alex session must match Alex"
        log("PASS: TC6 Two distinct accounts cannot collide or overwrite each other.")

        log("\n--- TC7: Register Success is NOT Login Success ---")
        tc7_res = eval_js("""
            (async () => {
                window.TempoAuth.signOut();
                
                // Set pending intent
                window.TempoMode.setPendingIntent({
                    type: 'tool',
                    destination: 'strack',
                    sourceContext: 'recovery'
                });
                
                // Register fresh user Charlie
                window.TempoAuth.openRegisterModal();
                const regCharlie = await window.TempoAuth.register("Charlie Kim", "charlie.kim@tempo.app", "Pass789!");
                
                const authState = window.TempoAuth.getAuthState();
                const user = window.TempoAuth.getCurrentUser();
                const active = window.TempoMode.getActiveContext();
                const pending = window.TempoMode.getPendingIntent();
                
                return {
                    regCharlie,
                    authState,
                    hasUser: user !== null,
                    active,
                    pending
                };
            })()
        """)
        assert tc7_res["regCharlie"] is True, "Charlie registration succeeds"
        assert tc7_res["authState"] == "anonymous", "Invariant 14: User must remain anonymous after registration"
        assert tc7_res["hasUser"] is False, "Invariant 14: No active currentUser after registration"
        assert tc7_res["active"] is None, "activeContext must remain null"
        assert tc7_res["pending"] is not None and tc7_res["pending"]["destination"] == "strack", "Pending intent must NOT be executed yet"
        log("PASS: TC7 Register Success is strictly isolated from Login Success.")

        log("\n========================================================")
        log("ALL TESTS (TC1 through TC7 + GoTrue Contract) PASSED!")
        log("========================================================")

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
