import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_check_auth_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9593

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
            match = [t for t in targets if t.get("type") == "page" and "127.0.0.1" in t.get("url", "")]
            if match:
                page_target = match[0]
                break
    except Exception:
        pass
    time.sleep(0.5)

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
    return res.get("result", {}).get("value")

send_cmd("Page.enable")
send_cmd("Runtime.enable")
time.sleep(2.0)

eval_js("""
    localStorage.setItem('tempo_mock_account_test_entry@tempo.com', JSON.stringify({
        id: 'test_user_rmode_entry',
        email: 'test_entry@tempo.com',
        password: 'password123',
        user_metadata: { full_name: 'Alex' }
    }));
    window.TempoAuth.signInWithCredentials('test_entry@tempo.com', 'password123');
""")
time.sleep(1.0)

res = eval_js("({ authUser: window.TempoAuth.getCurrentUser(), userId: window.TempoAuth.getCurrentUserId() })")
print("Auth result:", res)

ws.close()
proc.terminate()
