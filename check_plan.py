import subprocess
import urllib.request
import json
import websocket
import time

port = 9399
proc = subprocess.Popen([
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    "http://localhost:8000/"
])
time.sleep(2)
try:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as resp:
        tabs = json.loads(resp.read().decode())
        ws_url = tabs[0]["webSocketDebuggerUrl"]
    ws = websocket.create_connection(ws_url)

    msg_id = 1
    def eval_js(expr):
        global msg_id
        cid = msg_id
        msg_id += 1
        ws.send(json.dumps({"id": cid, "method": "Runtime.evaluate", "params": {"expression": expr, "returnByValue": True, "awaitPromise": True}}))
        while True:
            r = json.loads(ws.recv())
            if r.get("id") == cid:
                return r.get("result", {}).get("value")

    for _ in range(20):
        ready = eval_js("typeof window.TempoPlanWorkspace !== 'undefined'")
        if ready:
            break
        time.sleep(0.5)

    print("TempoPlanWorkspace loaded:", eval_js("typeof window.TempoPlanWorkspace !== 'undefined'"))
    keys = eval_js("Object.keys(localStorage)")
    print("localStorage keys:", keys)
    plan = eval_js("window.TempoPlanWorkspace ? window.TempoPlanWorkspace.getActivePlan() : null")
    print("Active Plan:", json.dumps(plan, indent=2))
    mock = eval_js("localStorage.getItem('tempo_rmode_mock_tasks')")
    print("tempo_rmode_mock_tasks:", mock)
    wp = eval_js("localStorage.getItem('tempo_working_plan')")
    print("tempo_working_plan raw:", wp[:200] if wp else None)
    ws.close()
finally:
    proc.terminate()
    proc.wait()
