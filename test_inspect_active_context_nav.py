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

def run():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_act_nav_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9258
    
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
            ready = eval_js("Boolean(window.TempoMode && window.TempoApp && window.TempoAuth)")
            if ready:
                break
            time.sleep(0.3)

        eval_js("""
            (async () => {
                try {
                    await window.TempoAuth.register('Innie Tester', 'innie.test@tempo.edu', 'password123');
                } catch(e) {}
                await window.TempoAuth.signIn('innie.test@tempo.edu', 'password123');
            })()
        """)
        time.sleep(0.5)

        # 1. Switch to Emergency Mode (Urgent Mode)
        eval_js("window.TempoMode.setMode('emergency');")
        time.sleep(0.5)
        nav_emergency_vi = eval_js("""
            Array.from(document.querySelectorAll('header nav a')).map(a => ({
                id: a.id,
                text: a.textContent.trim(),
                href: a.getAttribute('href')
            }))
        """)
        
        # Switch to EN
        eval_js("window.TempoI18n.setLanguage('en');")
        time.sleep(0.3)
        nav_emergency_en = eval_js("""
            Array.from(document.querySelectorAll('header nav a')).map(a => ({
                id: a.id,
                text: a.textContent.trim(),
                href: a.getAttribute('href')
            }))
        """)

        # 2. Switch to Recovery Mode
        eval_js("window.TempoI18n.setLanguage('vi');")
        eval_js("window.TempoMode.setMode('recovery');")
        time.sleep(0.5)
        nav_recovery_vi = eval_js("""
            Array.from(document.querySelectorAll('header nav a')).map(a => ({
                id: a.id,
                text: a.textContent.trim(),
                href: a.getAttribute('href')
            }))
        """)

        eval_js("window.TempoI18n.setLanguage('en');")
        time.sleep(0.3)
        nav_recovery_en = eval_js("""
            Array.from(document.querySelectorAll('header nav a')).map(a => ({
                id: a.id,
                text: a.textContent.trim(),
                href: a.getAttribute('href')
            }))
        """)

        log(f"Urgent VI: {json.dumps(nav_emergency_vi, indent=2)}")
        log(f"Urgent EN: {json.dumps(nav_emergency_en, indent=2)}")
        log(f"Recovery VI: {json.dumps(nav_recovery_vi, indent=2)}")
        log(f"Recovery EN: {json.dumps(nav_recovery_en, indent=2)}")

    finally:
        if ws:
            ws.close()
        proc.terminate()

if __name__ == "__main__":
    run()
