import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import base64

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_rmode_adjust_plan_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9283
    
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
                    
        def evaluate(expr):
            res = send_command("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True
            })
            if "exceptionDetails" in res:
                log(f"JS Exception for [{expr[:60]}...]: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        def capture_screenshot(filename):
            res = send_command("Page.captureScreenshot", {"format": "png"})
            data = res.get("data")
            if data:
                with open(filename, "wb") as f:
                    f.write(base64.b64decode(data))
                log(f"Screenshot saved: {filename}")

        send_command("Page.enable")
        send_command("DOM.enable")
        send_command("Emulation.setDeviceMetricsOverride", {
            "width": 1280,
            "height": 820,
            "deviceScaleFactor": 1,
            "mobile": False
        })
        time.sleep(1)

        # Wait for scripts to initialize
        log("Waiting for TempoApp initialization...")
        for _ in range(30):
            is_ready = evaluate("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'")
            if is_ready:
                break
            time.sleep(0.5)

        # Authenticate test user and switch to recovery mode
        log("Setting up Recovery Mode user...")
        evaluate("""
            (async () => {
                const mock = {
                    id: 'local_user_test',
                    email: 'alex.chen@university.edu',
                    raw_email: 'alex.chen@university.edu',
                    password: 'password123',
                    user_metadata: { full_name: 'Alex Chen', display_name: 'Alex Chen', role: 'student' }
                };
                localStorage.setItem('tempo_mock_account_alex.chen@university.edu', JSON.stringify(mock));
                if (window.TempoAuth) {
                    await window.TempoAuth.signIn("alex.chen@university.edu", "password123");
                }
                if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
                    window.TempoMode.setMode('recovery', { syncDOM: true, persist: true });
                }
            })()
        """)
        time.sleep(1)

        # Verify we are in Recovery Mode dashboard
        active_mode = evaluate("window.TempoMode.getMode()")
        log(f"Active mode: {active_mode}")
        assert active_mode == 'recovery', f"Expected active mode 'recovery', got '{active_mode}'"

        r_card_exists = evaluate("document.getElementById('recovery-working-plan') !== null")
        log(f"Recovery Working Plan card exists: {r_card_exists}")
        assert r_card_exists, "Recovery Working Plan card should be visible in Rmode"

        # Capture Rmode dashboard with Working Plan card
        capture_screenshot("C:/Users/YEN NHI/.gemini/antigravity/brain/6baf9c9e-16aa-475f-b2c0-d941b08ac2c6/rmode_dashboard_working_plan_card.png")

        # -------------------------------------------------------------
        # TEST 1: Click Adjust Plan from Rmode Working Plan card
        # -------------------------------------------------------------
        log("\n--- TEST 1: Click Adjust Plan on Rmode Working Plan card ---")
        evaluate("""
            (() => {
                const btn = document.querySelector('#recovery-working-plan button');
                if (btn) btn.click();
            })()
        """)
        time.sleep(1)

        # 1. Verify navigation directly to Working Plan tool page
        is_plan_workspace_visible = evaluate("""
            (() => {
                const screen = document.getElementById('screen-plan-workspace');
                return screen && !screen.classList.contains('hidden');
            })()
        """)
        log(f"Working Plan tool page visible: {is_plan_workspace_visible}")
        assert is_plan_workspace_visible, "App must navigate directly to Working Plan tool page"

        page_title = evaluate("document.querySelector('#screen-plan-workspace h1') ? document.querySelector('#screen-plan-workspace h1').innerText : ''")
        log(f"Working Plan page title: '{page_title}'")
        assert "Tempo Working Plan" in page_title, "Page title must be 'Tempo Working Plan'"

        # 2. Verify that Urmode adjustment flow modal was NOT opened
        urmode_modal_active = evaluate("""
            (() => {
                const modal = document.getElementById('modal-urmode-flow');
                const isVisible = modal && !modal.classList.contains('hidden');
                const activeView = window.TempoUrmodeFlow ? window.TempoUrmodeFlow.getActiveModalView ? window.TempoUrmodeFlow.getActiveModalView() : null : null;
                return isVisible;
            })()
        """)
        log(f"Urmode adjustment modal visible: {urmode_modal_active}")
        assert not urmode_modal_active, "Adjustment flow modal must NOT be launched automatically"

        # 3. Verify active context is still 'recovery' (Rmode) and has NOT switched to Urmode
        mode_in_workspace = evaluate("window.TempoMode.getMode()")
        log(f"Active context inside Working Plan tool page: {mode_in_workspace}")
        assert mode_in_workspace == 'recovery', f"Active context must remain 'recovery' (Rmode), got '{mode_in_workspace}'"
        assert mode_in_workspace != 'emergency', "Active context must NOT switch to Urmode ('emergency')"

        capture_screenshot("C:/Users/YEN NHI/.gemini/antigravity/brain/6baf9c9e-16aa-475f-b2c0-d941b08ac2c6/working_plan_from_rmode.png")

        # -------------------------------------------------------------
        # TEST 2: Return Home returns to Recovery Mode dashboard
        # -------------------------------------------------------------
        log("\n--- TEST 2: Click '← Return Home' control ---")
        evaluate("window.TempoPlanWorkspace.navigateHome();")
        time.sleep(1)

        mode_after_home = evaluate("window.TempoMode.getMode()")
        log(f"Active context after Return Home: {mode_after_home}")
        assert mode_after_home == 'recovery', f"Returning to dashboard must restore Rmode ('recovery'), got '{mode_after_home}'"

        r_card_restored = evaluate("document.getElementById('recovery-working-plan') !== null")
        log(f"Recovery Working Plan card restored: {r_card_restored}")
        assert r_card_restored, "Recovery Mode dashboard must be restored"

        # -------------------------------------------------------------
        # TEST 3: Click Adjust Plan again and test Tempo logo navigation
        # -------------------------------------------------------------
        log("\n--- TEST 3: Re-enter Working Plan and click Tempo logo ---")
        evaluate("""
            (() => {
                const btn = document.querySelector('#recovery-working-plan button');
                if (btn) btn.click();
            })()
        """)
        time.sleep(1)

        is_wp_again = evaluate("!document.getElementById('screen-plan-workspace').classList.contains('hidden')")
        assert is_wp_again, "Must be back in Working Plan tool page"

        # Click Tempo logo in navbar
        evaluate("window.TempoApp.handleLogoClick();")
        time.sleep(1)

        mode_after_logo = evaluate("window.TempoMode.getMode()")
        log(f"Active context after clicking Tempo logo: {mode_after_logo}")
        assert mode_after_logo == 'recovery', f"Tempo logo must return to Rmode ('recovery'), got '{mode_after_logo}'"

        r_card_after_logo = evaluate("document.getElementById('recovery-working-plan') !== null")
        assert r_card_after_logo, "Recovery Mode dashboard must be active after clicking Tempo logo"

        log("\n=======================================================")
        log(">>> ALL RMODE ADJUST PLAN TESTS PASSED 100%! <<<")
        log("=======================================================")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        proc.wait()

if __name__ == '__main__':
    run_tests()
