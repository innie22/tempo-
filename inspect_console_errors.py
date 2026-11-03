import subprocess, time, json, urllib.request, tempfile, websocket

edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9320
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
    def send_cmd(method, params=None):
        global msg_id
        cmd_obj = {'id': msg_id, 'method': method, 'params': params or {}}
        msg_id += 1
        ws.send(json.dumps(cmd_obj))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == cmd_obj['id']:
                return resp

    send_cmd('Console.enable')
    send_cmd('Runtime.enable')

    # Reload page to capture all errors
    send_cmd('Page.reload')
    
    start = time.time()
    errors = []
    while time.time() - start < 4:
        ws.settimeout(0.5)
        try:
            msg = json.loads(ws.recv())
            if msg.get('method') == 'Runtime.exceptionThrown':
                errors.append(msg)
            elif msg.get('method') == 'Console.messageAdded':
                errors.append(msg)
        except Exception:
            pass

    print('Captured errors/console count:', len(errors))
    for e in errors:
        print(json.dumps(e, indent=2))

    res = send_cmd('Runtime.evaluate', {'expression': 'window.TempoMode ? "EXISTS" : "UNDEFINED"'})
    print('TempoMode status:', res)

    ws.close()
finally:
    proc.terminate()
