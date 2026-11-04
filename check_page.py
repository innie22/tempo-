# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, tempfile, websocket, os

CDP_PORT = 9662
TARGET_URL = 'http://127.0.0.1:8000/'
edge_bin = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
user_data_dir = tempfile.mkdtemp(prefix='tempo_test2_')
cmd = [edge_bin, '--headless=new', f'--remote-debugging-port={CDP_PORT}', '--remote-allow-origins=*', f'--user-data-dir={user_data_dir}', '--disable-gpu', TARGET_URL]
proc = subprocess.Popen(cmd)
time.sleep(2)
try:
    req = urllib.request.urlopen(f'http://127.0.0.1:{CDP_PORT}/json')
    pages = json.loads(req.read().decode())
    ws_url = next(p['webSocketDebuggerUrl'] for p in pages if p.get('type') == 'page')
    ws = websocket.create_connection(ws_url, timeout=30)
    req_id = [0]
    def send(method, params=None):
        req_id[0] += 1
        ws.send(json.dumps({'id': req_id[0], 'method': method, 'params': params or {}}))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == req_id[0]:
                return resp.get('result', {})
    
    send('Page.enable')
    send('Runtime.enable')
    send('Page.navigate', {'url': 'http://127.0.0.1:8000/'})
    time.sleep(3)
    loc = send('Runtime.evaluate', {'expression': 'window.location.href', 'returnByValue': True})
    mode_obj = send('Runtime.evaluate', {'expression': 'typeof window.TempoMode', 'returnByValue': True})
    print('location:', loc.get('result', {}).get('value'))
    print('mode_obj:', mode_obj.get('result', {}).get('value'))
    
    # Check console errors
    res = send('Runtime.evaluate', {'expression': 'window.__errors || []', 'returnByValue': True})
    print('errors:', res.get('result', {}).get('value'))

    ws.close()
finally:
    proc.terminate()
