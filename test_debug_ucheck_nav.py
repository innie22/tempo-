import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_debug_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9274
    
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

        send_command("Runtime.enable")
        send_command("Page.enable")

        for _ in range(40):
            ready = eval_js("Boolean(window.TempoMode && window.TempoApp && window.TempoUnclearMode && window.TempoAuth && window.TempoI18n)")
            if ready:
                break
            time.sleep(0.3)

        # Login
        eval_js("""
            (async () => {
                try {
                    await window.TempoAuth.register('Innie Tester', 'innie.test@tempo.edu', 'password123');
                } catch(e) {}
                await window.TempoAuth.signIn('innie.test@tempo.edu', 'password123');
            })()
        """)
        time.sleep(0.5)

        # What if user opens UCheck from Emergency mode?
        log("\n--- Testing openUcheck from Emergency Mode ---")
        eval_js("window.TempoMode.setMode('emergency');")
        time.sleep(0.5)
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'emergency' });")
        time.sleep(0.5)

        from_emergency_state = eval_js("""
            (() => {
                const links = Array.from(document.querySelectorAll('header nav a:not([class*="hidden"])')).map(a => ({
                    id: a.id,
                    text: a.textContent.trim(),
                    href: a.getAttribute('href')
                }));
                const mode = window.TempoMode.getMode();
                const activeSharedTool = window.TempoMode.getActiveSharedTool ? window.TempoMode.getActiveSharedTool() : null;
                const activeContext = window.TempoMode.getActiveContext ? window.TempoMode.getActiveContext() : null;
                return { mode, activeSharedTool, activeContext, links };
            })()
        """)
        log(f"State after openUcheck from emergency: {json.dumps(from_emergency_state, indent=2)}")

        # What if user opens UCheck from Recovery mode?
        log("\n--- Testing openUcheck from Recovery Mode ---")
        eval_js("window.TempoMode.setMode('recovery');")
        time.sleep(0.5)
        eval_js("window.TempoMode.openUcheck({ sourceContext: 'recovery' });")
        time.sleep(0.5)

        from_recovery_state = eval_js("""
            (() => {
                const links = Array.from(document.querySelectorAll('header nav a:not([class*="hidden"])')).map(a => ({
                    id: a.id,
                    text: a.textContent.trim(),
                    href: a.getAttribute('href')
                }));
                const mode = window.TempoMode.getMode();
                return { mode, links };
            })()
        """)
        log(f"State after openUcheck from recovery: {json.dumps(from_recovery_state, indent=2)}")

        # What if user clicks on URL #ucheck?
        log("\n--- Testing navigation to #ucheck ---")
        eval_js("window.location.hash = '#ucheck';")
        time.sleep(0.5)

        hash_state = eval_js("""
            (() => {
                const links = Array.from(document.querySelectorAll('header nav a:not([class*="hidden"])')).map(a => ({
                    id: a.id,
                    text: a.textContent.trim(),
                    href: a.getAttribute('href')
                }));
                const mode = window.TempoMode.getMode();
                const uVisible = !document.getElementById('umode-home-content').classList.contains('hidden');
                return { mode, uVisible, links };
            })()
        """)
        log(f"State after hash = '#ucheck': {json.dumps(hash_state, indent=2)}")

    finally:
        if ws:
            ws.close()
        proc.terminate()

if __name__ == "__main__":
    run()
