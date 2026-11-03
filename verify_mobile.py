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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_mobile_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9264
    
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
            "width": 375,
            "height": 720,
            "deviceScaleFactor": 2,
            "mobile": True
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

        # Open Ucheck
        eval_js("window.TempoI18n.setLanguage('vi');")
        eval_js("window.TempoMode.openUcheck();")
        time.sleep(1.0)

        mobile_vi = eval_js("""
            (() => {
                const header = document.querySelector('header.entry-header');
                const scrollWidth = document.documentElement.scrollWidth;
                const clientWidth = document.documentElement.clientWidth;
                const hasOverflow = scrollWidth > clientWidth;
                return {
                    headerVisible: !!header && window.getComputedStyle(header).display !== 'none',
                    scrollWidth,
                    clientWidth,
                    hasOverflow
                };
            })()
        """)
        log(f"Mobile VI state: {json.dumps(mobile_vi)}")
        assert mobile_vi["headerVisible"] is True
        assert mobile_vi["hasOverflow"] is False, f"Mobile has horizontal overflow: {mobile_vi}"
        capture_screenshot("ucheck_cleaned_layout_mobile_vi.png")

        eval_js("window.TempoI18n.setLanguage('en');")
        time.sleep(0.5)
        capture_screenshot("ucheck_cleaned_layout_mobile_en.png")
        log("✓ Mobile screenshots captured without horizontal overflow.")

    finally:
        if ws:
            ws.close()
        proc.terminate()

if __name__ == "__main__":
    run()
