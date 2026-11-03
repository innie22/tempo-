import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_check_load_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9586

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "http://127.0.0.1:8000/#home"
]

proc = subprocess.Popen(cmd)
time.sleep(3.0)

targets = None
for _ in range(20):
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
        targets = json.loads(req.read().decode("utf-8"))
        if targets:
            break
    except Exception:
        time.sleep(0.5)

page_target = next(t for t in targets if t.get("type") == "page")
ws = websocket.create_connection(page_target["webSocketDebuggerUrl"])

msg_id = 1
def send(method, params=None):
    global msg_id
    cmd_id = msg_id
    msg_id += 1
    ws.send(json.dumps({"id": cmd_id, "method": method, "params": params or {}}))
    while True:
        raw = ws.recv()
        res = json.loads(raw)
        if res.get("id") == cmd_id:
            return res.get("result", {})

send("Page.enable")
send("Runtime.enable")
time.sleep(2.0)

res = send("Runtime.evaluate", {
    "expression": "({ ready: document.readyState, TempoRecoverySetup: typeof window.TempoRecoverySetup, TempoMode: typeof window.TempoMode })",
    "returnByValue": True
})
print("Result:", res)

ws.close()
proc.terminate()
