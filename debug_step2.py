import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_debug_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9490

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1050",
    "http://127.0.0.1:8000/#today"
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

    res1 = eval_js("""
    (() => {
        window.TempoI18n.setLanguage('vi');
        return {
            lang: window.TempoI18n.getLanguage(),
            t_edit: window.t('modes.urgent.editPlan'),
            t_qr: window.t('modes.urgent.quickRelief'),
            t_fn: window.t('modes.urgent.focusNow'),
            t_q: window.t('modes.urgent.transitionQuestion'),
            t_btn: window.t('modes.urgent.changeMyMode'),
        };
    })()
    """)
    print("VI translations:", res1)

    res2 = eval_js("""
    (() => {
        window.TempoI18n.setLanguage('en');
        return {
            lang: window.TempoI18n.getLanguage(),
            t_edit: window.t('modes.urgent.editPlan'),
            t_qr: window.t('modes.urgent.quickRelief'),
            t_fn: window.t('modes.urgent.focusNow'),
            t_q: window.t('modes.urgent.transitionQuestion'),
            t_btn: window.t('modes.urgent.changeMyMode'),
        };
    })()
    """)
    print("EN translations:", res2)

    # Now let's see what happens to the DOM when we transition to emergency and set EN
    res3 = eval_js("""
    (() => {
        window.TempoI18n.setLanguage('vi');
        const todayStr = '2026-11-01';
        const plan = {
            id: 'plan_test_localization',
            createdDate: todayStr,
            plannedTasks: [
                {
                    id: 'pt_1',
                    dayDate: todayStr,
                    startTime: '14:00',
                    endTime: '15:00',
                    task: { id: 't1', title: 'Task 1' }
                }
            ]
        };
        localStorage.setItem('tempo_confirmed_plan', JSON.stringify(plan));
        localStorage.setItem('tempo_current_mode', 'emergency');
        localStorage.setItem('tempo_established_context', 'emergency');
        window.TempoMode.transitionContext('emergency');
        window.TempoMode.renderActiveModeHome();

        const vi_btn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText?.trim();

        // Now switch to EN
        window.TempoI18n.setLanguage('en');

        const en_btn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText?.trim();

        return {
            vi_btn,
            en_btn,
            activeContext: window.TempoMode.getActiveContext(),
            emodeBoxExists: !!document.getElementById('emode-home-content')
        };
    })()
    """)
    print("DOM switch test:", res3)

finally:
    if ws:
        try: ws.close()
        except: pass
    if proc:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except:
            proc.kill()
