# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile

CDP_PORT = 9497
user_data_dir = tempfile.mkdtemp(prefix='edge_test_btn_')

proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={CDP_PORT}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--window-size=1440,1100',
    'http://127.0.0.1:8000/'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    time.sleep(2.5)
    with urllib.request.urlopen(f'http://127.0.0.1:{CDP_PORT}/json') as resp:
        tabs = json.loads(resp.read().decode())
    pages = [t for t in tabs if t.get('type') == 'page' and '127.0.0.1' in t.get('url', '')]
    ws_url = (pages[0] if pages else tabs[0])['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)

    msg_id = [1]
    def send(method, params=None):
        mid = msg_id[0]
        msg_id[0] += 1
        ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == mid:
                return resp.get('result', {})

    send('Page.enable')
    send('DOM.enable')

    def eval_js(expr, await_promise=False):
        params = {'expression': expr, 'returnByValue': True}
        if await_promise:
            params['awaitPromise'] = True
        res = send('Runtime.evaluate', params)
        return res.get('result', {}).get('value')

    time.sleep(1)
    res = eval_js("""
        (function() {
            const btn = document.createElement('button');
            btn.className = 'w-24 sm:w-32 h-20';
            document.body.appendChild(btn);
            const cs = window.getComputedStyle(btn);
            const r = btn.getBoundingClientRect();
            const out = {
                w: cs.width,
                h: cs.height,
                rw: r.width,
                rh: r.height
            };
            btn.remove();
            return out;
        })()
    """)
    print("w-24 sm:w-32:", res)

    res2 = eval_js("""
        (function() {
            const btn = document.createElement('button');
            btn.className = 'w-24 h-20';
            document.body.appendChild(btn);
            const cs = window.getComputedStyle(btn);
            const r = btn.getBoundingClientRect();
            const out = {
                w: cs.width,
                h: cs.height,
                rw: r.width,
                rh: r.height
            };
            btn.remove();
            return out;
        })()
    """)
    print("w-24:", res2)

    res3 = eval_js("""
        (function() {
            const btn = document.createElement('button');
            btn.className = 'w-20 h-20';
            document.body.appendChild(btn);
            const cs = window.getComputedStyle(btn);
            const r = btn.getBoundingClientRect();
            const out = {
                w: cs.width,
                h: cs.height,
                rw: r.width,
                rh: r.height
            };
            btn.remove();
            return out;
        })()
    """)
    print("w-20:", res3)
finally:
    try: ws.close()
    except: pass
    try: proc.terminate()
    except: pass
