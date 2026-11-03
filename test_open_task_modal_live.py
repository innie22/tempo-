import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_test_task_modal_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9538

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#tool-notes"
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
    ws_url = app_tabs[0]["webSocketDebuggerUrl"] if app_tabs else tabs[0]["webSocketDebuggerUrl"]

    ws = websocket.create_connection(ws_url)
    send_cmd("Page.enable")
    time.sleep(1.5)

    eval_js("""
    (() => {
        let globalRoot = document.getElementById('urmode-task-modal-global-root');
        if (!globalRoot) {
            globalRoot = document.createElement('div');
            globalRoot.id = 'urmode-task-modal-global-root';
            document.body.appendChild(globalRoot);
        }
        window.TempoMode.openUrmodeTaskDetailModal('task-marketing-research');
        globalRoot.innerHTML = window.TempoMode.renderUrmodeTaskDetailModalHTML();
    })()
    """)
    time.sleep(0.5)

    modal_info = eval_js("""
    (() => {
        const modal = document.getElementById('urmode-task-detail-modal');
        return {
            modalExists: modal !== null,
            title: document.getElementById('urmode-task-modal-title')?.innerText.trim(),
            badge: modal?.querySelector('button[onclick*="toggleUrmodeDetailLabelMenu"]')?.innerText.trim(),
            hasSubtasks: modal?.querySelectorAll('[id^="subtask-checkbox-"]').length,
            hasCloseBtn: modal?.querySelector('button[onclick*="closeUrmodeTaskDetailModal"]') !== null
        };
    })()
    """)

    print("Modal test info:")
    print(modal_info)

finally:
    if ws:
        ws.close()
    proc.terminate()
