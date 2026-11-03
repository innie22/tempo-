import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_check_loop_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9589

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
for _ in range(30):
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

send_cmd("Page.enable")
send_cmd("Runtime.enable")

for i in range(15):
    res = send_cmd("Runtime.evaluate", {
        "expression": "({ ready: document.readyState, setup: typeof window.TempoRecoverySetup, mode: typeof window.TempoMode })",
        "returnByValue": True
    })
    val = res.get("result", {}).get("value")
    print(f"Iteration {i}: {val}")
    if val and val.get("setup") == "object":
        print("Ready!")
        break
    time.sleep(0.5)

ws.close()
proc.terminate()
