import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import base64
import os

user_data_dir = tempfile.mkdtemp(prefix='ann_shot_')
port = 9460
proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={port}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--disable-gpu',
    '--no-first-run',
    'http://localhost:8000/'
])
time.sleep(2)

try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        tabs = json.loads(resp.read().decode())
        pages = [t for t in tabs if t.get('type') == 'page' and 'localhost' in t.get('url', '')]
    ws_url = pages[0]['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)

    msg_id = 1
    def send_cmd(method, params=None):
        global msg_id
        cmd = {'id': msg_id, 'method': method, 'params': params or {}}
        msg_id += 1
        ws.send(json.dumps(cmd))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == cmd['id']:
                return resp.get('result', {})

    def eval_js(expr):
        res = send_cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
        return res.get('result', {}).get('value')

    def save_screenshot(path):
        data = send_cmd("Page.captureScreenshot", {"format": "png"})
        b64 = data.get("data", "")
        if b64:
            with open(path, "wb") as f:
                f.write(base64.b64decode(b64))
            print(f"Saved: {path}")

    send_cmd('Page.enable')
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 1280,
        "height": 800,
        "deviceScaleFactor": 1,
        "mobile": False
    })

    for _ in range(30):
        if eval_js("typeof window.TempoApp !== 'undefined'"):
            break
        time.sleep(0.5)

    os.makedirs('assets', exist_ok=True)

    # Authenticate user and setup recovery mode
    eval_js("""
        (() => {
            if (window.TempoAuth) {
                window.TempoAuth.getCurrentUser = () => ({ id: 'u1', email: 'innie@tempo.edu' });
                window.TempoAuth.getCurrentProfile = () => ({ full_name: 'Innie', role: 'student' });
                window.TempoAuth.getAuthState = () => 'authenticated';
            }
            if (window.TempoMode) {
                window.TempoMode.setMode('recovery');
            }
        })()
    """)
    time.sleep(0.5)

    # 1. Recovery Mode Dashboard screenshot
    eval_js("window.TempoApp.navigateTo('today');")
    time.sleep(0.8)
    save_screenshot("assets/announcement_rmode_v21.png")

    # 2. Daily Self-check tool screenshot
    eval_js("window.TempoApp.navigateTo('stress-check');")
    time.sleep(0.8)
    save_screenshot("assets/announcement_selfcheck_v21.png")

finally:
    proc.terminate()
