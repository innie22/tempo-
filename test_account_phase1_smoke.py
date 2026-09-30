import subprocess
import time
import json
import urllib.request
import tempfile
import os
import websocket
import sys

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def log(msg):
    try:
        print(msg, flush=True)
    except Exception:
        print(msg.encode('ascii', errors='replace').decode('ascii'), flush=True)

def run_test():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_test_account_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    cmd = [
        edge_path,
        "--headless=new",
        "--remote-debugging-port=9223",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "http://localhost:8000/"
    ]
    
    log("Launching Edge with CDP on http://localhost:8000/ ...")
    proc = subprocess.Popen(cmd)
    ws = None
    try:
        ws_url = None
        for _ in range(30):
            try:
                with urllib.request.urlopen("http://127.0.0.1:9223/json") as resp:
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
                    if "error" in res:
                        raise RuntimeError(f"CDP error: {res['error']}")
                    return res.get("result", {})

        def eval_js(expr, await_promise=False):
            res = send_command("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": await_promise
            })
            val = res.get("result", {}).get("value")
            return val

        # Wait for page readiness
        log("Waiting for page load and TempoAuth...")
        for _ in range(30):
            ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined'")
            if ready:
                break
            time.sleep(0.5)
        
        eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")

        # Clear any local storage session before test
        eval_js("localStorage.clear(); window.TempoAuth.handleSignOut();", await_promise=True)
        time.sleep(0.5)

        log("\n--- TEST 1: Register Button Directly Opens Standard Registration Modal ---")
        eval_js("document.getElementById('btn-header-register').click()")
        time.sleep(0.3)
        
        is_reg_open = eval_js("!document.getElementById('modal-register').classList.contains('hidden')")
        is_role_select_hidden = eval_js("document.getElementById('modal-role-select').classList.contains('hidden')")
        
        log(f"modal-register open: {is_reg_open}")
        log(f"modal-role-select hidden: {is_role_select_hidden}")
        assert is_reg_open, "Clicking Register must open modal-register directly!"
        assert is_role_select_hidden, "modal-role-select must NOT be opened!"
        log("✓ Test 1 Passed: Register button opens standard registration without role choice.")

        log("\n--- TEST 2: Registration Fields Integrity (No Role Choice, No Student Questions) ---")
        has_name_input = eval_js("document.getElementById('reg-display-name') !== null")
        has_email_input = eval_js("document.getElementById('reg-email') !== null")
        has_password_input = eval_js("document.getElementById('reg-password') !== null")
        has_role_dropdown = eval_js("document.getElementById('modal-register').querySelector('select[name=\"role\"]') !== null")
        
        log(f"Has display name input: {has_name_input}")
        log(f"Has email input: {has_email_input}")
        log(f"Has password input: {has_password_input}")
        log(f"Has role dropdown (must be False): {has_role_dropdown}")
        
        assert has_name_input and has_email_input and has_password_input, "All 3 required registration inputs must exist!"
        assert not has_role_dropdown, "Normal registration form must not contain role selection!"
        log("✓ Test 2 Passed: Registration form fields correctly specified.")

        log("\n--- TEST 3: Initials Avatar Fallback Calculation ---")
        initials_nhi = eval_js("window.TempoAuth.getInitials('Nguyễn Yến Nhi')")
        initials_alex = eval_js("window.TempoAuth.getInitials('Alex')")
        initials_morgan = eval_js("window.TempoAuth.getInitials('Alex Morgan')")
        initials_email = eval_js("window.TempoAuth.getInitials('test.user@university.edu')")
        
        log(f"getInitials('Nguyễn Yến Nhi') -> '{initials_nhi}' (expected 'NY')")
        log(f"getInitials('Alex') -> '{initials_alex}' (expected 'A')")
        log(f"getInitials('Alex Morgan') -> '{initials_morgan}' (expected 'AM')")
        log(f"getInitials('test.user@university.edu') -> '{initials_email}' (expected 'T')")
        
        assert initials_nhi == "NY", f"Expected 'NY', got '{initials_nhi}'"
        assert initials_alex == "A", f"Expected 'A', got '{initials_alex}'"
        assert initials_morgan == "AM", f"Expected 'AM', got '{initials_morgan}'"
        log("✓ Test 3 Passed: Initials algorithm handles Vietnamese and Western names accurately.")

        log("\n--- TEST 4: Registration Creates Standard Account & Updates Header Identity ---")
        reg_result = eval_js("""
        (async () => {
            return await window.TempoAuth.register('Nguyễn Yến Nhi', 'nhi.nguyen@test.edu', 'secret123');
        })()
        """, await_promise=True)
        time.sleep(0.5)
        
        log(f"Registration result: {reg_result}")
        assert reg_result == True, "Registration should succeed!"
        
        header_name = eval_js("document.getElementById('header-user-name').textContent")
        header_avatar_text = eval_js("document.getElementById('header-user-avatar').textContent.trim()")
        role_pill_hidden = eval_js("document.getElementById('header-user-role-pill').classList.contains('hidden')")
        role_pill_text = eval_js("document.getElementById('header-user-role-pill').textContent.trim()")
        home_greeting = eval_js("document.querySelector('#dmode-home-content h2')?.textContent || ''")
        
        log(f"Header user name: '{header_name}'")
        log(f"Header avatar text: '{header_avatar_text}'")
        log(f"Role pill hidden: {role_pill_hidden}")
        log(f"Role pill text: '{role_pill_text}'")
        log(f"Home greeting: '{home_greeting}'")
        
        assert header_name == "Nguyễn Yến Nhi", f"Expected 'Nguyễn Yến Nhi', got '{header_name}'"
        assert header_avatar_text == "NY", f"Expected avatar 'NY', got '{header_avatar_text}'"
        assert role_pill_hidden, "Role pill must be hidden for standard account!"
        assert role_pill_text == "", "Role pill text must not show 'Student' for standard account!"
        assert "Nhi" in home_greeting, f"Expected greeting to address given name 'Nhi', got '{home_greeting}'"
        log("✓ Test 4 Passed: Standard account created, initials avatar displayed, visible 'Student' badge absent.")

        log("\n--- TEST 5: Sign In Modal Structure ---")
        eval_js("window.TempoAuth.handleSignOut()", await_promise=True)
        time.sleep(0.3)
        eval_js("window.TempoAuth.openSignInModal()")
        time.sleep(0.3)
        
        is_signin_open = eval_js("!document.getElementById('modal-signin').classList.contains('hidden')")
        has_forgot_link = eval_js("document.getElementById('auth-login-forgot-link') !== null")
        has_remember_me = eval_js("document.getElementById('modal-signin').querySelector('input[type=\"checkbox\"]') !== null")
        
        log(f"modal-signin open: {is_signin_open}")
        log(f"has forgot password link: {has_forgot_link}")
        log(f"has remember me checkbox (must be False): {has_remember_me}")
        
        assert is_signin_open, "Sign in modal must be open!"
        assert has_forgot_link, "Forgot password link must be present!"
        assert not has_remember_me, "Custom remember me checkbox must not exist (session managed via standard persistence)!"
        log("✓ Test 5 Passed: Sign in modal cleanly matches specification.")

        log("\n--- TEST 6: Pre-auth Accessible Language Toggle (EN <-> VI) ---")
        # Toggle to VI
        eval_js("window.TempoAuth.setAuthLanguage('vi')")
        time.sleep(0.2)
        
        vi_login_heading = eval_js("document.getElementById('auth-login-heading').textContent")
        vi_login_title = eval_js("document.getElementById('auth-login-title').textContent")
        vi_login_btn = eval_js("document.getElementById('btn-submit-signin').textContent.trim()")
        
        log(f"VI Login Heading: '{vi_login_heading}'")
        log(f"VI Login Title: '{vi_login_title}'")
        log(f"VI Login Button: '{vi_login_btn}'")
        
        assert vi_login_heading == "CHÀO MỪNG TRỞ LẠI", f"Expected VI heading, got '{vi_login_heading}'"
        assert vi_login_btn == "Đăng nhập", f"Expected VI button 'Đăng nhập', got '{vi_login_btn}'"
        
        # Open register modal in VI
        eval_js("window.TempoAuth.openRegisterModal()")
        time.sleep(0.2)
        vi_reg_heading = eval_js("document.getElementById('auth-reg-heading').textContent")
        vi_reg_btn = eval_js("document.getElementById('btn-submit-register').textContent.trim()")
        
        log(f"VI Reg Heading: '{vi_reg_heading}'")
        log(f"VI Reg Button: '{vi_reg_btn}'")
        assert vi_reg_heading == "TẠO TÀI KHOẢN TEMPO", f"Expected VI reg heading, got '{vi_reg_heading}'"
        assert vi_reg_btn == "Tạo tài khoản", f"Expected VI reg button 'Tạo tài khoản', got '{vi_reg_btn}'"
        
        # Switch back to EN
        eval_js("window.TempoAuth.setAuthLanguage('en')")
        time.sleep(0.2)
        en_reg_heading = eval_js("document.getElementById('auth-reg-heading').textContent")
        assert en_reg_heading == "CREATE YOUR TEMPO ACCOUNT", f"Expected EN reg heading, got '{en_reg_heading}'"
        log("✓ Test 6 Passed: Pre-auth language toggle functions instantaneously across modals.")

        log("\n--- TEST 7: Mode Gate Continuity Preserved ---")
        eval_js("""
        (async () => {
            await window.TempoAuth.handleSignOut();
            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
                window.TempoMode.setMode('default', { silent: true });
            }
        })()
        """, await_promise=True)
        time.sleep(0.3)

        curr_user = eval_js("window.TempoAuth.getCurrentUser()")
        log(f"Pre-test current user (should be None): {curr_user}")
        
        # Anonymous user requests Urgent Mode
        eval_js("window.TempoMode.requestMode('emergency')")
        time.sleep(0.3)
        
        # Pending mode should be 'emergency'
        has_pending = eval_js("window.TempoMode.hasPendingMode()")
        signin_open = eval_js("!document.getElementById('modal-signin').classList.contains('hidden')")
        banner_visible = eval_js("!document.querySelector('#modal-signin .auth-mode-gate-banner').classList.contains('hidden')")
        
        log(f"Has pending mode: {has_pending}")
        log(f"Sign in modal opened by mode gate: {signin_open}")
        log(f"Gate banner visible: {banner_visible}")
        
        assert has_pending, "TempoMode should remember pendingMode 'emergency'!"
        assert signin_open, "Auth gate modal should open for unauthenticated mode request!"
        assert banner_visible, "Mode gate banner should be visible!"
        
        # Authenticate with credentials and verify pending mode activates
        eval_js("""
        (async () => {
            return await window.TempoAuth.signIn('alex.urgent@university.edu', 'pass123');
        })()
        """, await_promise=True)
        time.sleep(0.5)
        
        active_mode = eval_js("window.TempoMode.getMode()")
        log(f"Active mode post-authentication: {active_mode}")
        assert active_mode == "emergency", f"Expected active mode 'emergency', got '{active_mode}'"
        log("✓ Test 7 Passed: Mode gate continuity preserved perfectly upon authentication.")

        log("\n=======================================================")
        log(">>> ALL ACCOUNT ECOSYSTEM PHASE 1 TESTS PASSED! <<<")
        log("=======================================================")

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

if __name__ == "__main__":
    run_test()
