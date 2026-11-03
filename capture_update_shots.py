import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import base64
import os

user_data_dir = tempfile.mkdtemp(prefix='tempo_final_shots_')
port = 9466
proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={port}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
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
    art_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'

    for _ in range(30):
        if eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoCommunity !== 'undefined'"):
            break
        time.sleep(0.5)

    # 1. Desktop Tips Tab (showing updated non-overlapping search bar & reduced typography)
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 1280,
        "height": 900,
        "deviceScaleFactor": 1,
        "mobile": False
    })
    eval_js("window.TempoApp.navigateTo('community', 'tips');")
    time.sleep(0.5)
    save_screenshot(os.path.join(art_dir, "community_tips_tab.png"))

    # 2. Desktop Posts Tab
    eval_js("window.TempoCommunity.navigateToPostsFeed();")
    time.sleep(0.5)
    save_screenshot(os.path.join(art_dir, "community_posts_tab.png"))

    # 3. Direct Message Empty State (with Chat Requests symbol in header)
    eval_js("""
        (() => {
            if (window.TempoAuth) {
                window.TempoAuth.getCurrentUser = () => ({ id: 'u1', email: 'student@tempo.edu' });
            }
            localStorage.removeItem('tempo_direct_messages');
            localStorage.removeItem('tempo_chat_requests');
            window.TempoCommunity.init();
            window.TempoCommunity.selectTab('messages');
        })()
    """)
    time.sleep(0.5)
    save_screenshot(os.path.join(art_dir, "community_dm_empty_state.png"))

    # 4. Chat Requests Modal
    eval_js("window.TempoCommunity.openChatRequests();")
    time.sleep(0.5)
    save_screenshot(os.path.join(art_dir, "community_chat_requests_modal.png"))
    eval_js("window.TempoCommunity.closeChatRequests();")

    # 5. Mobile Search View (390px)
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 390,
        "height": 844,
        "deviceScaleFactor": 2,
        "mobile": True
    })
    eval_js("window.TempoCommunity.selectTab('tips');")
    time.sleep(0.5)
    save_screenshot(os.path.join(art_dir, "community_mobile_tips.png"))

finally:
    proc.terminate()
