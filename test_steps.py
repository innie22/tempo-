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
port = 9699

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,900",
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
        if res.get("method") == "Runtime.consoleAPICalled":
            print("[BROWSER CONSOLE]", res.get("params", {}).get("args", []))
        if res.get("method") == "Runtime.exceptionThrown":
            print("[BROWSER EXCEPTION]", res.get("params", {}))
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
    tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read().decode())
    ws = websocket.create_connection(tabs[0]["webSocketDebuggerUrl"])
    send_cmd("Page.enable")
    send_cmd("Runtime.enable")
    
    # Wait until TempoI18n and TempoMode are fully loaded
    for _ in range(30):
        ready = eval_js("Boolean(window.TempoI18n && window.TempoMode && document.readyState === 'complete')")
        if ready:
            print("Tempo fully loaded and ready!")
            break
        time.sleep(0.5)

    print("--- 1. Set vi ---")
    res1 = eval_js("""
    (() => {
        window.TempoI18n.setLanguage('vi');
        const todayStr = window.TempoI18n.getLocalTodayISO();
        localStorage.setItem('tempo_confirmed_plan', JSON.stringify({
            id: 'p1', createdDate: todayStr, status: 'active',
            tasks: [{ id: 't1', title: 'Task 1', estimatedMinutes: 30, scheduledDate: todayStr, scheduledStart: '14:00', scheduledEnd: '14:30' }]
        }));
        localStorage.setItem('tempo_current_mode', 'emergency');
        localStorage.setItem('tempo_established_context', 'emergency');
        window.TempoMode.transitionContext('emergency');
        window.TempoMode.renderActiveModeHome();
        return {
            lang: window.TempoI18n.getLanguage(),
            wpTitle: document.querySelector('.urgent-working-plan-card h3')?.innerText,
            editPlanBtn: document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText
        };
    })()
    """)
    print("Res1:", res1)

    print("--- 2. Call setLanguage('en') ---")
    res2 = eval_js("window.TempoI18n.setLanguage('en')")
    print("Res2 (setLanguage result):", res2)

    print("--- 3. Check DOM in English ---")
    res3 = eval_js("""
    (() => {
        return {
            lang: window.TempoI18n.getLanguage(),
            wpTitle: document.querySelector('.urgent-working-plan-card h3')?.innerText,
            editPlanBtn: document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText,
            qrCard: document.querySelector('.urgent-card-overwhelmed h3')?.innerText,
            fnCard: document.querySelector('.urgent-card-focus-now h3')?.innerText,
            switcher: document.getElementById('nav-current-lang-label')?.innerText
        };
    })()
    """)
    print("Res3:", res3)

finally:
    if ws:
        try: ws.close()
        except: pass
    proc.terminate()
    try: proc.wait(timeout=3)
    except: proc.kill()
