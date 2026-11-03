import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_modal_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9552

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#plan-workspace"
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
    app_tab = next(t for t in tabs if "8000" in t.get("url", ""))

    ws = websocket.create_connection(app_tab["webSocketDebuggerUrl"], timeout=10)
    send_cmd("Page.enable")
    send_cmd("DOM.enable")

    # Setup dev user and open plan-workspace
    eval_js("""
    (async () => {
        const u = { id: 'u1', email: 'alex@tempo.test', user_metadata: { display_name: 'Alex' } };
        localStorage.setItem('tempo_local_dev_user', JSON.stringify(u));
        localStorage.setItem('tempo_mock_account_alex@tempo.test', JSON.stringify(u));
        if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
            await window.TempoAuth.checkSession();
        }
        window.TempoApp.navigateTo('plan-workspace');
    })()
    """)
    time.sleep(1)

    # Test Delete Plan modal in VI
    eval_js("window.TempoI18n.setLanguage('vi'); window.TempoPlanWorkspace.render(); window.TempoPlanWorkspace.promptDeletePlan();")
    time.sleep(0.5)

    vi_modal = eval_js("""
    (() => {
        const modal = document.getElementById('modal-delete-plan-confirm');
        if (!modal) return null;
        return {
            title: modal.querySelector('#delete-plan-title')?.innerText.trim(),
            btnConfirm: modal.querySelector('#btn-confirm-delete-plan')?.innerText.trim()
        };
    })()
    """)
    print("VI Delete Plan Modal:", vi_modal)
    assert vi_modal["btnConfirm"] == "Xóa plan", f"VI modal confirm button mismatch: {vi_modal}"

    # Close modal
    eval_js("window.TempoPlanWorkspace.closeDeletePlanConfirm();")
    time.sleep(0.3)

    # Test Delete Plan modal in EN
    eval_js("window.TempoI18n.setLanguage('en'); window.TempoPlanWorkspace.render(); window.TempoPlanWorkspace.promptDeletePlan();")
    time.sleep(0.5)

    en_modal = eval_js("""
    (() => {
        const modal = document.getElementById('modal-delete-plan-confirm');
        if (!modal) return null;
        return {
            title: modal.querySelector('#delete-plan-title')?.innerText.trim(),
            btnConfirm: modal.querySelector('#btn-confirm-delete-plan')?.innerText.trim()
        };
    })()
    """)
    print("EN Delete Plan Modal:", en_modal)
    assert en_modal["btnConfirm"] == "Delete my plan", f"EN modal confirm button mismatch: {en_modal}"

    eval_js("window.TempoPlanWorkspace.closeDeletePlanConfirm();")
    print("Delete Plan Modal verification PASSED!")

finally:
    if ws:
        try:
            ws.close()
        except:
            pass
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
