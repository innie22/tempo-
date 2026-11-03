import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_dmode_en_')
port = 9467
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
time.sleep(2.5)

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
                if 'error' in resp:
                    raise Exception(f"CDP Error in {method}: {resp['error']}")
                return resp.get('result', {})

    def evaluate(expr):
        res = send_cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
        if 'exceptionDetails' in res:
            raise Exception(f"JS Exception: {res['exceptionDetails']}")
        return res.get('result', {}).get('value')

    print("Initial VI in default mode:")
    btn_vi = evaluate("document.getElementById('btn-see-all-posts')?.textContent?.replace(/\\s+/g, ' ')?.trim()")
    h3_vi = evaluate("document.getElementById('btn-see-all-posts')?.parentElement?.querySelector('h3')?.textContent?.trim()")
    print(f"H3: {h3_vi}, Button: {btn_vi}")

    print("\nSwitching to English...")
    evaluate("window.TempoI18n.setLanguage('en');")
    time.sleep(0.5)

    btn_en = evaluate("document.getElementById('btn-see-all-posts')?.textContent?.replace(/\\s+/g, ' ')?.trim()")
    h3_en = evaluate("document.getElementById('btn-see-all-posts')?.parentElement?.querySelector('h3')?.textContent?.trim()")
    print(f"H3: {h3_en}, Button: {btn_en}")

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        proc.kill()
