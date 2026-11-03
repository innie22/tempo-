import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_check_rmode_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9621

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#home"
]

proc = subprocess.Popen(cmd)
time.sleep(3.0)

req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
targets = json.loads(req.read().decode("utf-8"))
page_target = [t for t in targets if t.get("type") == "page" and "127.0.0.1" in t.get("url", "")][0]
ws = websocket.create_connection(page_target["webSocketDebuggerUrl"])

msg_id = 1
def send_cmd(method, params=None):
    global msg_id, ws
    cmd_obj = {"id": msg_id, "method": method, "params": params or {}}
    msg_id += 1
    ws.send(json.dumps(cmd_obj))
    while True:
        raw = ws.recv()
        res = json.loads(raw)
        if res.get("id") == cmd_obj["id"]:
            return res.get("result", {})

def eval_js(expression):
    res = send_cmd("Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True
    })
    if "exceptionDetails" in res:
        print("JS Exception:", json.dumps(res["exceptionDetails"], ensure_ascii=False, indent=2))
    return res.get("result", {}).get("value")

time.sleep(2.0)

res = eval_js("""
(() => {
    window.TempoI18n.setLanguage('vi');
    window.TempoMode.setMode('recovery');
    window.TempoMode.openStrack('open', { context: 'recovery' });
    const btn = document.getElementById('btn-self-check-return-home');
    const headerTitle = document.querySelector('#self-check-workspace-root h2.text-2xl, #self-check-workspace-root [data-tempo-ui="tracking-system-title"]');
    const rightCol = document.querySelector('#self-check-workspace-root');
    return {
        buttonHTML: btn ? btn.outerHTML : null,
        buttonText: btn ? btn.innerText.trim() : null,
        workspaceText: rightCol ? rightCol.innerText.substring(0, 500) : null
    };
})()
""")

print("Dashboard Info:", json.dumps(res, ensure_ascii=False, indent=2))

ws.close()
proc.terminate()
