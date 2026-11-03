import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_dmode_')
port = 9466
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

    time.sleep(1)
    dmode_btns = evaluate("""
        (() => {
            const btns = Array.from(document.querySelectorAll('button')).map(b => ({
                id: b.id,
                text: b.textContent.replace(/\\s+/g, ' ').trim(),
                classes: b.className
            }));
            return btns.filter(b => b.text.includes('Xem') || b.text.includes('all') || b.text.includes('All') || b.id.includes('see-all') || b.id.includes('post'));
        })()
    """)
    print("Buttons matching in default mode:", dmode_btns)

    headings = evaluate("""
        (() => {
            return Array.from(document.querySelectorAll('h1, h2, h3, h4')).map(h => h.textContent.replace(/\\s+/g, ' ').trim());
        })()
    """)
    print("Headings:", [h for h in headings if 'Community' in h or 'Cộng đồng' in h])

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        proc.kill()
