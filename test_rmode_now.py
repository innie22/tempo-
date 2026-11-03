import subprocess, time, json, urllib.request, tempfile, websocket

edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9322
user_data_dir = tempfile.mkdtemp(prefix='tempo_debug_')

cmd = [
    edge_path, '--headless=new', f'--remote-debugging-port={port}',
    '--remote-allow-origins=*', f'--user-data-dir={user_data_dir}',
    '--disable-gpu', '--no-first-run', '--window-size=1440,900'
]
proc = subprocess.Popen(cmd)
time.sleep(1.5)
try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        tabs = json.loads(resp.read().decode())
        print("Tabs available:", [(t.get('title'), t.get('url')) for t in tabs])
        pages = [t for t in tabs if t.get('type') == 'page']
        ws_url = pages[0]['webSocketDebuggerUrl']
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

    def eval_js(expr):
        resp = send_cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
        if 'exceptionDetails' in resp.get('result', {}):
            print('JS EXCEPTION:', resp['result']['exceptionDetails'])
        return resp.get('result', {}).get('result', {}).get('value')

    print("Navigating to http://127.0.0.1:8000/...")
    send_cmd('Page.navigate', {'url': 'http://127.0.0.1:8000/'})
    time.sleep(2.5)

    print("Title:", eval_js("document.title"))
    print("TempoMode:", eval_js("typeof window.TempoMode !== 'undefined'"))
    
    eval_js('window.TempoMode.setMode("recovery")')
    time.sleep(1)
    
    mode = eval_js('window.TempoMode.getMode()')
    print('Current Mode:', mode)
    cards = eval_js('Array.from(document.querySelectorAll("#recovery-working-plan [data-task-id]")).map(c => c.getAttribute("data-task-id"))')
    print('Rendered cards in recovery-working-plan:', cards)

    ws.close()
finally:
    proc.terminate()
