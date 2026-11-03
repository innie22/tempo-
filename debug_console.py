import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_debug_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9585

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "about:blank"
]

proc = subprocess.Popen(cmd)
time.sleep(2.0)
tabs_url = f"http://127.0.0.1:{port}/json"
with urllib.request.urlopen(tabs_url) as resp:
    tabs = json.loads(resp.read().decode())
page_tab = next(t for t in tabs if t.get("type") == "page")
ws = websocket.create_connection(page_tab["webSocketDebuggerUrl"])

msg_id = 1
def send(method, params=None):
    global msg_id
    cmd_id = msg_id
    msg_id += 1
    ws.send(json.dumps({"id": cmd_id, "method": method, "params": params or {}}))
    while True:
        raw = ws.recv()
        res = json.loads(raw)
        if "method" in res:
            if "exception" in res.get("method", "").lower() or "console" in res.get("method", "").lower():
                print("DEBUG EVENT:", res["method"], res["params"])
        if res.get("id") == cmd_id:
            return res.get("result", {})

send("Page.enable")
send("Runtime.enable")
send("Log.enable")

print("Navigating to http://127.0.0.1:8000/#home...")
send("Page.navigate", {"url": "http://127.0.0.1:8000/#home"})
time.sleep(3.0)

# Check console messages
while True:
    try:
        ws.settimeout(1.0)
        raw = ws.recv()
        res = json.loads(raw)
        if "method" in res:
            print("EVENT:", res["method"], str(res.get("params"))[:150])
    except:
        break

ws.close()
proc.terminate()
