import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_diag_tasks_")
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
    if "exceptionDetails" in res:
        print(f"JS ERROR: {res['exceptionDetails']}")
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

    # Let's see what the DOM displays for groups
    grouped = eval_js("""
    (() => {
        const groups = [];
        // Look for date headings and tasks inside them
        document.querySelectorAll('.font-heading, h3, h4').forEach(h => {
            const text = h.textContent.trim();
            if (text.includes('01/11/2026') || text.includes('02/11/2026') || text.includes('Hôm nay') || text.includes('Ngày mai')) {
                // Find parent container or following siblings
                const parent = h.closest('.rounded-2xl, .rounded-3xl, div.space-y-3, div.space-y-4') || h.parentElement;
                groups.push({
                    heading: text,
                    tasks: Array.from(parent ? parent.querySelectorAll('[data-task-id], h4, .font-bold') : []).map(t => t.textContent.trim())
                });
            }
        });
        return groups;
    })()
    """)
    print("Initial Grouped HTML:")
    print(json.dumps(grouped, indent=2, ensure_ascii=False))

finally:
    if ws:
        ws.close()
    proc.terminate()
