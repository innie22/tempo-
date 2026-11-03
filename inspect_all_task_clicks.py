import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_inspect_tasks_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9295

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

    # Set Recovery mode
    eval_js("window.TempoMode.setMode('recovery')")
    time.sleep(1)

    cards_inspection = eval_js("""
        (() => {
            const cards = Array.from(document.querySelectorAll('#recovery-working-plan [data-task-id]'));
            return cards.map(c => {
                const taskId = c.getAttribute('data-task-id');
                const titleEl = c.querySelector('h5');
                const title = titleEl ? titleEl.textContent.trim() : null;
                const buttonContainer = c.querySelector('[role="button"]');
                const onclickAttr = buttonContainer ? buttonContainer.getAttribute('onclick') : null;
                const checkbox = c.querySelector('button');
                const chkOnclick = checkbox ? checkbox.getAttribute('onclick') : null;
                return {
                    taskId,
                    title,
                    hasRoleButton: !!buttonContainer,
                    onclickAttr,
                    chkOnclick,
                    outerHTMLSnippet: c.outerHTML.slice(0, 300)
                };
            });
        })()
    """)
    print("Cards Inspection:", json.dumps(cards_inspection, indent=2))

    # Test clicking each card individually and see if modal opens and what task it shows
    test_clicks = eval_js("""
        (() => {
            const results = [];
            const cards = Array.from(document.querySelectorAll('#recovery-working-plan [data-task-id]'));
            for (const c of cards) {
                const taskId = c.getAttribute('data-task-id');
                const titleEl = c.querySelector('h5');
                const title = titleEl ? titleEl.textContent.trim() : '';
                const btn = c.querySelector('[role="button"]');
                if (!btn) {
                    results.push({ taskId, title, error: 'no role button' });
                    continue;
                }
                // Click the card
                btn.click();
                const modal = document.getElementById('rmode-task-detail-modal');
                const modalOpen = !!modal;
                let modalTitle = null;
                let modalTaskId = null;
                if (modalOpen) {
                    const mTitleEl = document.getElementById('rmode-task-modal-title');
                    modalTitle = mTitleEl ? mTitleEl.textContent.trim() : null;
                    // close modal
                    window.TempoMode.closeRmodeTaskDetailModal();
                }
                results.push({
                    taskId,
                    cardTitle: title,
                    modalOpened: modalOpen,
                    modalTitle: modalTitle
                });
            }
            return results;
        })()
    """)
    print("Click Test Results:", json.dumps(test_clicks, indent=2))

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
