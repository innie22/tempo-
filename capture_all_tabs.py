import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import base64
import os

user_data_dir = tempfile.mkdtemp(prefix='tempo_shots_')
port = 9452
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
        "height": 900,
        "deviceScaleFactor": 1,
        "mobile": False
    })

    for _ in range(30):
        if eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoCommunity !== 'undefined'"):
            break
        time.sleep(0.5)

    art_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'

    # 1. Announcement Tab
    eval_js("window.TempoApp.navigateTo('community', 'announcement');")
    time.sleep(0.6)
    save_screenshot(os.path.join(art_dir, "community_announcement_tab.png"))

    # 2. Tips (Solve) Tab
    eval_js("window.TempoCommunity.selectTab('tips');")
    time.sleep(0.6)
    save_screenshot(os.path.join(art_dir, "community_tips_tab.png"))

    # 3. Learn Tab
    eval_js("window.TempoCommunity.selectTab('learn');")
    time.sleep(0.6)
    save_screenshot(os.path.join(art_dir, "community_learn_tab.png"))

    # 4. Posts Tab
    eval_js("window.TempoCommunity.selectTab('posts');")
    time.sleep(0.6)
    save_screenshot(os.path.join(art_dir, "community_posts_tab.png"))

    # 5. Direct Message (Authenticated)
    eval_js("""
        (() => {
            if (window.TempoAuth) {
                window.TempoAuth.getCurrentUser = () => ({ id: 'u1', email: 'student@tempo.edu' });
            }
            window.TempoCommunity.selectTab('messages');
        })()
    """)
    time.sleep(0.6)
    save_screenshot(os.path.join(art_dir, "community_messages_tab.png"))

    # 6. Direct Message (Guest)
    eval_js("""
        (() => {
            if (window.TempoAuth) {
                window.TempoAuth.getCurrentUser = () => null;
            }
            window.TempoCommunity.selectTab('messages');
        })()
    """)
    time.sleep(0.6)
    save_screenshot(os.path.join(art_dir, "community_messages_guest_tab.png"))

    # 7. Announcement Detail Modal
    eval_js("window.TempoCommunity.selectTab('announcement'); window.TempoCommunity.openAnnouncementDetail('ann-1');")
    time.sleep(0.6)
    save_screenshot(os.path.join(art_dir, "community_announcement_detail_modal.png"))
    eval_js("window.TempoCommunity.closeAnnouncementDetail();")

finally:
    proc.terminate()
