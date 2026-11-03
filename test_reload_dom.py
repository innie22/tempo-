import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_test_reload_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9297

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,900",
    "http://127.0.0.1:8000/#tool-workplan"
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
        res = json.loads(ws.recv())
        if res.get("id") == cmd_obj["id"]:
            return res.get("result", {})

def eval_js(expression):
    res = send_cmd("Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True
    })
    return res.get("result", {}).get("value")

try:
    time.sleep(2)
    tabs_res = urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read().decode()
    tabs = json.loads(tabs_res)
    app_tabs = [t for t in tabs if "127.0.0.1:8000" in t.get("url", "") or "localhost:8000" in t.get("url", "")]
    target_tab = app_tabs[0] if app_tabs else tabs[0]
    ws_url = target_tab["webSocketDebuggerUrl"]
    ws = websocket.create_connection(ws_url)

    send_cmd("Page.enable")
    send_cmd("Runtime.enable")
    time.sleep(2)

    # Reschedule task
    task_id = "task-marketing-research"
    eval_js(f"""
    (() => {{
        window.TempoPlanWorkspace.openRescheduleModal('{task_id}');
        const d = document.getElementById('pw-resched-avail-date');
        const s = document.getElementById('pw-resched-avail-start');
        const e = document.getElementById('pw-resched-avail-end');
        if (d) d.value = '2026-11-02';
        if (s) s.value = '14:00';
        if (e) e.value = '16:00';
        window.TempoPlanWorkspace.saveRescheduleAvailability();
    }})()
    """)
    time.sleep(1)
    eval_js(f"window.TempoPlanWorkspace.executeReschedule('{task_id}')")
    time.sleep(1)

    print("Before reload:")
    print("taskRow before reload:", eval_js(f"!!document.querySelector('[data-task-row=\"{task_id}\"]')"))

    send_cmd("Page.reload")
    time.sleep(3)

    print("After reload:")
    print("hash after reload:", eval_js("window.location.hash"))
    print("plan-workspace-root has children:", eval_js("document.getElementById('plan-workspace-root')?.children?.length"))
    print("is tool-workplan screen visible:", eval_js("!document.getElementById('tool-workplan')?.classList.contains('hidden')"))
    print("taskRow after reload:", eval_js(f"!!document.querySelector('[data-task-row=\"{task_id}\"]')"))
    print("all task-rows:", eval_js("Array.from(document.querySelectorAll('[data-task-row]')).map(el => el.getAttribute('data-task-row'))"))

finally:
    if ws:
        ws.close()
    proc.terminate()
