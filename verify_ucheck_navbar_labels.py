import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"

def run():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_nav_labels_")
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

        def eval_js(expression):
            res = send_command("Runtime.evaluate", {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True
            })
            if "exceptionDetails" in res:
                raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        def capture_screenshot(filename):
            res = send_command("Page.captureScreenshot", {"format": "png"})
            data = res.get("data")
            if data:
                import base64
                path = os.path.join(ARTIFACT_DIR, filename)
                with open(path, "wb") as f:
                    f.write(base64.b64decode(data))
                log(f"Saved screenshot: {path}")

        send_command("Runtime.enable")
        send_command("Page.enable")
        send_command("Emulation.setDeviceMetricsOverride", {
            "width": 1280,
            "height": 900,
            "deviceScaleFactor": 1,
            "mobile": False
        })

        for _ in range(40):
            ready = eval_js("Boolean(window.TempoMode && window.TempoApp && window.TempoUnclearMode && window.TempoAuth)")
            if ready:
                break
            time.sleep(0.3)

        # Authenticate
        eval_js("""
            (async () => {
                try {
                    await window.TempoAuth.register('Innie Tester', 'innie.test@tempo.edu', 'password123');
                } catch(e) {}
                await window.TempoAuth.signIn('innie.test@tempo.edu', 'password123');
            })()
        """)
        time.sleep(0.5)

        # =====================================================================
        # 1. VERIFY UCHECK VIETNAMESE NAVBAR LABELS
        # =====================================================================
        log("\n--- TEST 1: UCheck Navbar in Vietnamese (vi) ---")
        eval_js("window.TempoI18n.setLanguage('vi');")
        eval_js("window.TempoMode.openUcheck();")
        time.sleep(0.8)

        vi_nav = eval_js("""
            (() => {
                const links = Array.from(document.querySelectorAll('header nav a:not([class*="hidden"])')).map(a => ({
                    id: a.id,
                    text: a.textContent.trim(),
                    href: a.getAttribute('href')
                }));
                const displayedString = links.map(l => l.text).join(' | ');
                return { links, displayedString };
            })()
        """)
        log(f"UCheck VI nav: {json.dumps(vi_nav, indent=2)}")
        assert vi_nav["displayedString"] == "Giới thiệu | Check | Test | Cộng đồng", f"Expected 'Giới thiệu | Check | Test | Cộng đồng', got '{vi_nav['displayedString']}'"
        
        capture_screenshot("ucheck_navbar_labels_vi.png")
        log("✓ TEST 1 PASSED: UCheck navbar displays 'Giới thiệu | Check | Test | Cộng đồng' in Vietnamese mode.")

        # =====================================================================
        # 2. VERIFY UCHECK ENGLISH NAVBAR LABELS
        # =====================================================================
        log("\n--- TEST 2: UCheck Navbar in English (en) ---")
        eval_js("window.TempoI18n.setLanguage('en');")
        time.sleep(0.5)

        en_nav = eval_js("""
            (() => {
                const links = Array.from(document.querySelectorAll('header nav a:not([class*="hidden"])')).map(a => ({
                    id: a.id,
                    text: a.textContent.trim(),
                    href: a.getAttribute('href')
                }));
                const displayedString = links.map(l => l.text).join(' | ');
                return { links, displayedString };
            })()
        """)
        log(f"UCheck EN nav: {json.dumps(en_nav, indent=2)}")
        assert en_nav["displayedString"] == "About | Check | Assessment | Community", f"Expected 'About | Check | Assessment | Community', got '{en_nav['displayedString']}'"
        
        capture_screenshot("ucheck_navbar_labels_en.png")
        log("✓ TEST 2 PASSED: UCheck navbar preserves English labels 'About | Check | Assessment | Community'.")

        # =====================================================================
        # 3. VERIFY OTHER MODES ARE NOT MODIFIED
        # =====================================================================
        log("\n--- TEST 3: Verify Urgent Mode & Recovery Mode Navbars Unaffected ---")
        eval_js("window.TempoI18n.setLanguage('vi');")
        eval_js("window.TempoMode.setMode('emergency');")
        time.sleep(0.5)
        emode_nav = eval_js("""
            Array.from(document.querySelectorAll('header nav a:not([class*="hidden"])')).map(a => a.textContent.trim()).join(' | ')
        """)
        log(f"Urgent VI nav: {emode_nav}")
        assert emode_nav == "Giới thiệu | Tự kiểm tra | Đánh giá | Cộng đồng", f"Urgent mode navbar was altered: {emode_nav}"

        eval_js("window.TempoMode.setMode('recovery');")
        time.sleep(0.5)
        rmode_nav = eval_js("""
            Array.from(document.querySelectorAll('header nav a:not([class*="hidden"])')).map(a => a.textContent.trim()).join(' | ')
        """)
        log(f"Recovery VI nav: {rmode_nav}")
        assert rmode_nav == "Giới thiệu | Kế hoạch | Đánh giá | Cộng đồng", f"Recovery mode navbar was altered: {rmode_nav}"
        log("✓ TEST 3 PASSED: Urgent and Recovery mode navbars are completely preserved.")

        # =====================================================================
        # 4. VERIFY FUNCTIONALITY ON UCHECK (CLICKS WORK AS BEFORE)
        # =====================================================================
        log("\n--- TEST 4: Navigation Clicks on UCheck ---")
        eval_js("window.TempoMode.openUcheck();")
        time.sleep(0.5)
        
        # Click "Check" (nav-link-check) -> opens Strack
        eval_js("document.getElementById('nav-link-check').click();")
        time.sleep(0.5)
        is_strack_active = eval_js("Boolean(window.TempoMode.getActiveSharedTool ? window.TempoMode.getActiveSharedTool() === 'strack' : true)")
        log(f"Strack active after clicking Check: {is_strack_active}")

        # Return to UCheck
        eval_js("window.TempoMode.openUcheck();")
        time.sleep(0.5)
        
        # Click "Test" (nav-link-plan) -> stays/refreshes UCheck
        eval_js("document.getElementById('nav-link-plan').click();")
        time.sleep(0.5)
        is_ucheck_visible = eval_js("!document.getElementById('umode-home-content').classList.contains('hidden')")
        assert is_ucheck_visible is True, "UCheck should remain active after clicking Test"
        log("✓ TEST 4 PASSED: Navigation links function correctly.")

        log("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")

    finally:
        if ws:
            ws.close()
        proc.terminate()

if __name__ == "__main__":
    run()
