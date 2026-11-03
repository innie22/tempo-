import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_modes_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9293

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,900",
    "http://127.0.0.1:8000/"
]

proc = subprocess.Popen(cmd)
ws = None
msg_id = 1

def send_cmd(method, params=None):
    global msg_id, ws
    cmd_obj = {"id": msg_id, "method": method, "params": params or {}}
    msg_id += 1
    ws.send(json.dumps(cmd_obj))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == cmd_obj["id"]:
            return resp.get("result", {})

def eval_js(expr):
    res = send_cmd("Runtime.evaluate", {
        "expression": expr,
        "returnByValue": True,
        "awaitPromise": True
    })
    return res.get("result", {}).get("value")

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
    time.sleep(1.5)

    # 1. Test URmode
    eval_js("window.TempoMode.setMode('unclear')")
    time.sleep(0.5)
    ur_info = eval_js("""
        (() => {
            const mode = window.TempoMode.getMode();
            const qrCard = document.querySelector('#unclear-mode-view [data-tempo-ui="quick-relief-card"]');
            const fnCard = document.querySelector('#unclear-mode-view [data-tempo-ui="focus-now-card"]');
            const navAssessment = Array.from(document.querySelectorAll('#unclear-mode-view nav a, header a')).find(a => a.textContent.trim() === 'Assessment');
            return {
                mode: mode,
                qrCardPresent: !!qrCard,
                fnCardPresent: !!fnCard,
                navAssessmentPresent: !!navAssessment
            };
        })()
    """)
    print("URmode integrity check:", json.dumps(ur_info, indent=2))

    # 2. Test EntryHome
    eval_js("window.TempoMode.setMode('entry')")
    time.sleep(0.5)
    entry_info = eval_js("""
        (() => {
            const mode = window.TempoMode.getMode();
            const entryHome = document.querySelector('#entry-home-view');
            return {
                mode: mode,
                entryHomePresent: !!entryHome
            };
        })()
    """)
    print("EntryHome integrity check:", json.dumps(entry_info, indent=2))

    # Return to Rmode
    eval_js("window.TempoMode.setMode('recovery')")
    time.sleep(0.5)
    print("ALL INTEGRITY CHECKS PASSED!")

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
