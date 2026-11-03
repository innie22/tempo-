import subprocess, time, json, urllib.request, tempfile, websocket

edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9335
user_data_dir = tempfile.mkdtemp(prefix='tempo_debug_urmode_')

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
        pages = [t for t in tabs if t.get('type') == 'page' and not t.get('url', '').startswith('chrome-extension://')]
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

    send_cmd('Page.navigate', {'url': 'http://127.0.0.1:8000/'})
    time.sleep(2)

    for _ in range(30):
        ready = eval_js("typeof window.TempoMode !== 'undefined' && typeof window.TempoMode.setMode === 'function'")
        if ready:
            break
        time.sleep(0.3)

    print("Switching to emergency mode (URmode)...")
    eval_js('window.TempoMode.setMode("emergency")')
    time.sleep(1)

    mode = eval_js('window.TempoMode.getMode()')
    print('Current Mode:', mode)

    # Check tasks in URmode
    tasks_info = eval_js("""
        (() => {
            const planCard = document.querySelector('.urgent-working-plan-card');
            const items = Array.from(document.querySelectorAll('.urgent-timeline-item'));
            return {
                hasPlanCard: !!planCard,
                itemCount: items.length,
                items: items.map(el => ({
                    id: el.getAttribute('data-task-id'),
                    text: el.innerText.replace(/\\n+/g, ' | ')
                }))
            };
        })()
    """)
    print('URmode Tasks Info:', json.dumps(tasks_info, indent=2))

    ws.close()
finally:
    proc.terminate()
