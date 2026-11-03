import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_test_rerender_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9495

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

    # Wait for page ready
    for _ in range(20):
        time.sleep(0.5)
        ready = eval_js("document.readyState === 'complete' && !!window.TempoMode && !!window.TempoI18n")
        if ready:
            break

    # Seed mock auth + emergency mode + plan
    res1 = eval_js("""
    (() => {
        window.TempoI18n.setLanguage('en');
        const mockUser = { id: 'dev_user_1', email: 'dev@tempo.local', user_metadata: { full_name: 'Innie', role: 'student' } };
        localStorage.setItem('tempo_local_dev_user', JSON.stringify(mockUser));
        localStorage.setItem('tempo_mock_account_dev@tempo.local', JSON.stringify(mockUser));
        localStorage.setItem('tempo_user_established_context_dev_user_1', 'emergency');
        localStorage.setItem('tempo_established_context', 'emergency');
        localStorage.setItem('tempo_current_mode', 'emergency');

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
        window.TempoMode.transitionContext('emergency');
        window.TempoMode.renderActiveModeHome();

        return {
            ctx: window.TempoMode.getActiveContext(),
            lang: window.TempoI18n.getLanguage(),
            btn: document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText?.trim()
        };
    })()
    """)
    print("Step 1 (before reload):", res1)

    # Reload page
    eval_js("window.__reloading = true;")
    send_cmd("Page.reload")

    for _ in range(30):
        time.sleep(0.5)
        ready = eval_js("document.readyState === 'complete' && !!window.TempoI18n && !!window.TempoMode && window.__reloading === undefined")
        if ready:
            break
    time.sleep(1)

    res2 = eval_js("""
    (() => {
        return {
            ctx: window.TempoMode.getActiveContext(),
            lang: window.TempoI18n.getLanguage(),
            auth: window.TempoAuth ? window.TempoAuth.getAuthState() : null,
            btn: document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText?.trim(),
            wpCard: !!document.querySelector('.urgent-working-plan-card'),
            qrCard: document.querySelector('.urgent-card-overwhelmed h3')?.innerText?.trim(),
            fnCard: document.querySelector('.urgent-card-focus-now h3')?.innerText?.trim(),
            transQ: document.querySelector('[data-tempo-ui="mode-transition-prompt"] p')?.innerText?.trim(),
            changeBtn: document.querySelector('[data-tempo-ui="change-mode-btn"]')?.innerText?.trim(),
        };
    })()
    """)
    print("Step 2 (after reload):", res2)

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
