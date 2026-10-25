import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os
import base64

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_navbar_pill_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9260
    
    cmd = [
        edge_path,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--window-size=1280,850",
        "--disable-gpu",
        "--no-first-run",
        "about:blank"
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
                    
        def eval_js(expr):
            res = send_command("Runtime.evaluate", {"expression": expr, "returnByValue": True})
            if "exceptionDetails" in res:
                log(f"JS Exception for [{expr[:60]}...]: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        def capture_screenshot(artifact_name):
            res = send_command("Page.captureScreenshot", {"format": "png"})
            data = res.get("data")
            if data:
                artifact_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
                os.makedirs(artifact_dir, exist_ok=True)
                file_path = os.path.join(artifact_dir, f"{artifact_name}.png")
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(data))
                log(f"Screenshot saved: {file_path}")

        send_command("Page.enable")
        send_command("Runtime.enable")
        send_command("Page.navigate", {"url": "http://localhost:8000/"})
        time.sleep(3)
        
        log("Authenticating test user...")
        eval_js("""
            (async () => {
                const mock = {
                    id: 'local_user_test',
                    email: 'alex.chen@university.edu',
                    raw_email: 'alex.chen@university.edu',
                    password: 'password123',
                    user_metadata: { full_name: 'Alex Chen', display_name: 'Alex Chen', role: 'student' }
                };
                localStorage.setItem('tempo_mock_account_alex.chen@university.edu', JSON.stringify(mock));
                localStorage.setItem('tempo_recovery_intro_dismissed', 'true');
                if (window.TempoAuth) {
                    await window.TempoAuth.signIn("alex.chen@university.edu", "password123");
                }
            })()
        """)
        time.sleep(1)

        tests_passed = 0
        total_tests = 0

        def check(condition, desc):
            nonlocal tests_passed, total_tests
            total_tests += 1
            if condition:
                log(f"  [PASS] {desc}")
                tests_passed += 1
            else:
                log(f"  [FAIL] {desc}")

        # -------------------------------------------------------------
        # TEST CONTEXT 1: RECOVERY MODE
        # -------------------------------------------------------------
        log("\n--- CONTEXT 1: RECOVERY MODE ---")
        eval_js("window.TempoMode.setMode('recovery')")
        time.sleep(0.5)

        shell_hidden = eval_js("document.getElementById('mode-indicator-shell').classList.contains('hidden')")
        shell_visible = eval_js("document.getElementById('mode-indicator-shell').offsetParent !== null")
        check(shell_hidden and not shell_visible, "Navbar Recovery Mode pill/dropdown is hidden")

        dropdown_hidden = eval_js("document.getElementById('navbar-mode-dropdown').classList.contains('hidden')")
        check(dropdown_hidden, "Navbar mode dropdown menu is hidden")

        nav_check_text = eval_js("document.getElementById('nav-link-check').textContent.trim()")
        check(nav_check_text == "Plan", f"Navbar displays 'Plan' instead of 'Check' (got '{nav_check_text}')")

        nav_tool_text = eval_js("document.getElementById('nav-link-plan').textContent.trim()")
        check(nav_tool_text == "Tool", f"Navbar displays 'Tool' item (got '{nav_tool_text}')")

        # Check in-dashboard mode switcher
        in_page_selector = eval_js("document.querySelector('#rmode-home-content #btn-home-mode-selector') !== null")
        check(in_page_selector, "In-page Recovery Mode switcher button exists in dashboard card")

        # Test clicking Tempo logo returns to Recovery Dashboard
        eval_js("window.TempoApp.navigateTo('about')")
        time.sleep(0.3)
        check(eval_js("document.getElementById('screen-about') && !document.getElementById('screen-about').classList.contains('hidden')"), "Navigated to About page")
        eval_js("document.getElementById('brand-logo-container').click()")
        time.sleep(0.4)
        rmode_visible = eval_js("!document.getElementById('rmode-home-content').classList.contains('hidden')")
        check(rmode_visible, "Clicking Tempo logo returns to Recovery Mode dashboard")
        check(eval_js("document.getElementById('mode-indicator-shell').classList.contains('hidden')"), "Navbar mode pill remains hidden after logo click")
        eval_js("if (window.TempoRecoverySetup) window.TempoRecoverySetup.exploreFirst();")
        time.sleep(0.3)
        capture_screenshot("recovery_mode_navbar_verified")

        # -------------------------------------------------------------
        # TEST CONTEXT 2: URMODE (URGENT / EMERGENCY)
        # -------------------------------------------------------------
        log("\n--- CONTEXT 2: URMODE (URGENT MODE) ---")
        eval_js("window.TempoMode.setMode('urgent')")
        time.sleep(0.5)

        shell_hidden = eval_js("document.getElementById('mode-indicator-shell').classList.contains('hidden')")
        shell_visible = eval_js("document.getElementById('mode-indicator-shell').offsetParent !== null")
        check(shell_hidden and not shell_visible, "Navbar Urgent Mode pill/dropdown is hidden")

        dropdown_hidden = eval_js("document.getElementById('navbar-mode-dropdown').classList.contains('hidden')")
        check(dropdown_hidden, "Navbar mode dropdown menu is hidden")

        nav_check_text = eval_js("document.getElementById('nav-link-check').textContent.trim()")
        check(nav_check_text == "Check", f"Navbar displays 'Check' item (got '{nav_check_text}')")

        nav_tool_text = eval_js("document.getElementById('nav-link-plan').textContent.trim()")
        check(nav_tool_text == "Tool", f"Navbar displays 'Tool' item (got '{nav_tool_text}')")

        # Check in-dashboard mode switcher
        in_page_selector = eval_js("document.querySelector('#emode-home-content #btn-home-mode-selector') !== null")
        check(in_page_selector, "In-page Urgent Mode switcher button exists in dashboard card")

        # Test clicking Tempo logo returns to Urmode Dashboard
        eval_js("window.TempoApp.navigateTo('about')")
        time.sleep(0.3)
        eval_js("document.getElementById('brand-logo-container').click()")
        time.sleep(0.4)
        emode_visible = eval_js("!document.getElementById('emode-home-content').classList.contains('hidden')")
        check(emode_visible, "Clicking Tempo logo returns to Urmode dashboard")
        check(eval_js("document.getElementById('mode-indicator-shell').classList.contains('hidden')"), "Navbar mode pill remains hidden after logo click")

        capture_screenshot("urmode_navbar_verified")

        # -------------------------------------------------------------
        # TEST CONTEXT 3: ENTRY HOME (DEFAULT MODE)
        # -------------------------------------------------------------
        log("\n--- CONTEXT 3: ENTRY HOME (DEFAULT MODE) ---")
        eval_js("window.TempoMode.setMode('default')")
        time.sleep(0.5)

        shell_hidden = eval_js("document.getElementById('mode-indicator-shell').classList.contains('hidden')")
        shell_visible = eval_js("document.getElementById('mode-indicator-shell').offsetParent !== null")
        check(shell_hidden and not shell_visible, "Navbar Entry Home mode pill is hidden")

        nav_check_text = eval_js("document.getElementById('nav-link-check').textContent.trim()")
        check(nav_check_text == "Check", f"Navbar displays 'Check' item (got '{nav_check_text}')")

        # Test clicking Tempo logo returns to Entry Home Dashboard
        eval_js("window.TempoApp.navigateTo('about')")
        time.sleep(0.3)
        eval_js("document.getElementById('brand-logo-container').click()")
        time.sleep(0.4)
        dmode_visible = eval_js("!document.getElementById('dmode-home-content').classList.contains('hidden')")
        check(dmode_visible, "Clicking Tempo logo returns to Entry Home dashboard")
        check(eval_js("document.getElementById('mode-indicator-shell').classList.contains('hidden')"), "Navbar mode pill remains hidden after logo click")

        capture_screenshot("entry_home_navbar_verified")

        # -------------------------------------------------------------
        # TEST CONTEXT 4: UNCLEAR MODE
        # -------------------------------------------------------------
        log("\n--- CONTEXT 4: UNCLEAR MODE ---")
        eval_js("window.TempoMode.setMode('unclear')")
        time.sleep(0.5)

        shell_hidden = eval_js("document.getElementById('mode-indicator-shell').classList.contains('hidden')")
        shell_visible = eval_js("document.getElementById('mode-indicator-shell').offsetParent !== null")
        check(shell_hidden and not shell_visible, "Navbar mode pill is hidden in Unclear Mode")

        umode_visible = eval_js("!document.getElementById('umode-home-content').classList.contains('hidden')")
        check(umode_visible, "Unclear Mode content is visible")

        # Unclear Mode top navigation bar controls
        has_return_home = eval_js("document.querySelector('#umode-home-content button[title=\"Return Home\"]') !== null")
        check(has_return_home, "Unclear Mode has '← Return Home' control")

        has_sos = eval_js("document.querySelector('#umode-home-content button[title*=\"feel safe\"]') !== null")
        check(has_sos, "Unclear Mode has 'I don\\'t feel safe' SOS control")

        # Test clicking Tempo logo returns to Unclear Mode Dashboard
        eval_js("window.TempoApp.navigateTo('about')")
        time.sleep(0.3)
        eval_js("document.getElementById('brand-logo-container').click()")
        time.sleep(0.4)
        umode_visible_after_logo = eval_js("!document.getElementById('umode-home-content').classList.contains('hidden')")
        check(umode_visible_after_logo, "Clicking Tempo logo returns to Unclear Mode dashboard")
        check(eval_js("document.getElementById('mode-indicator-shell').classList.contains('hidden')"), "Navbar mode pill remains hidden after logo click")

        capture_screenshot("unclear_mode_navbar_verified")

        # -------------------------------------------------------------
        # TEST CONTEXT 5: UCHECK FLOW AND PRESERVATION ACROSS MODES
        # -------------------------------------------------------------
        log("\n--- CONTEXT 5: UCHECK ENTRY & EXIT ACROSS MODES ---")
        # Enter from Recovery Mode
        eval_js("window.TempoMode.transitionContext('recovery')")
        time.sleep(0.4)
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'recovery', startNew: true })")
        time.sleep(0.5)
        check(eval_js("window.TempoMode.getActiveSharedTool() === 'ucheck'"), "Ucheck is active tool from Recovery")
        
        # Click Tempo Logo from Ucheck
        eval_js("document.getElementById('brand-logo-container').click()")
        time.sleep(0.5)
        check(eval_js("!document.getElementById('rmode-home-content').classList.contains('hidden')"), "Logo click from Ucheck returns to Recovery dashboard")
        check(eval_js("document.getElementById('mode-indicator-shell').classList.contains('hidden')"), "Navbar mode pill remains hidden after Ucheck exit to Recovery")
        check(eval_js("document.getElementById('nav-link-check').textContent.trim()") == "Plan", "Navbar check link displays 'Plan' in Recovery Mode")

        # Enter from Urmode
        eval_js("window.TempoMode.transitionContext('emergency')")
        time.sleep(0.4)
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'emergency', startNew: true })")
        time.sleep(0.5)
        check(eval_js("window.TempoMode.getActiveSharedTool() === 'ucheck'"), "Ucheck is active tool from Urmode")
        
        # Click Tempo Logo from Ucheck
        eval_js("document.getElementById('brand-logo-container').click()")
        time.sleep(0.5)
        check(eval_js("!document.getElementById('emode-home-content').classList.contains('hidden')"), "Logo click from Ucheck returns to Urmode dashboard")
        check(eval_js("document.getElementById('mode-indicator-shell').classList.contains('hidden')"), "Navbar mode pill remains hidden after Ucheck exit to Urmode")
        check(eval_js("document.getElementById('nav-link-check').textContent.trim()") == "Check", "Navbar check link displays 'Check' in Urmode")

        log(f"\n==========================================")
        log(f"FINAL RESULT: {tests_passed} / {total_tests} checks passed.")
        log(f"==========================================")

        if tests_passed == total_tests:
            log("ALL NAVBAR MODE PILL TESTS PASSED SUCCESSFULLY!")
        else:
            log("SOME TESTS FAILED.")
            sys.exit(1)

    finally:
        if ws:
            ws.close()
        proc.terminate()

if __name__ == "__main__":
    run_tests()
