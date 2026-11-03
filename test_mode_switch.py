import subprocess, time, json, urllib.request, tempfile, websocket

edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9319
user_data_dir = tempfile.mkdtemp(prefix='tempo_debug_')

cmd = [
    edge_path, '--headless=new', f'--remote-debugging-port={port}',
    '--remote-allow-origins=*', f'--user-data-dir={user_data_dir}',
    '--disable-gpu', '--no-first-run', '--window-size=1440,900', 'http://127.0.0.1:8000/'
]
proc = subprocess.Popen(cmd)
time.sleep(2)
try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        tabs = json.loads(resp.read().decode())
        ws_url = [t for t in tabs if t.get('type') == 'page'][0]['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)
    msg_id = 1
    def eval_js(expr):
        global msg_id
        cmd_obj = {'id': msg_id, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True, 'awaitPromise': True}}
        msg_id += 1
        ws.send(json.dumps(cmd_obj))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == cmd_obj['id']:
                return resp

    res1 = eval_js('window.TempoMode ? window.TempoMode.getMode() : null')
    print('Initial mode:', res1)
    
    res2 = eval_js('window.TempoMode.setMode("recovery")')
    print('setMode res:', res2)
    time.sleep(1)
    
    res3 = eval_js('window.TempoMode.getMode()')
    print('Mode after setMode:', res3)
    
    res4 = eval_js('document.querySelectorAll("[data-task-id]").length')
    print('Task cards count:', res4)
    
    ws.close()
finally:
    proc.terminate()
