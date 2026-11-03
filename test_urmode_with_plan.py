import subprocess, time, json, urllib.request, tempfile, websocket, sys
sys.stdout.reconfigure(encoding='utf-8')

edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9338
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
        ws_url = [t for t in tabs if t.get('type') == 'page' and not t.get('url', '').startswith('chrome-extension://')][0]['webSocketDebuggerUrl']
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
        return resp.get('result', {}).get('result', {}).get('value')

    send_cmd('Page.navigate', {'url': 'http://127.0.0.1:8000/'})
    time.sleep(2)

    # Check reference plan and seed it to EmergencyFlow
    seed_res = eval_js("""
        (() => {
            const ref = window.TempoPlanWorkspace ? window.TempoPlanWorkspace.getDefaultReferencePlan() : null;
            if (ref && window.TempoEmergencyFlow) {
                window.TempoEmergencyFlow.setConfirmedPlan(ref);
                if (window.TempoPlanStore) {
                    window.TempoPlanStore.saveActivePlan('emergency', ref);
                }
                return { seeded: true, taskCount: ref.plannedTasks.length };
            }
            return { seeded: false };
        })()
    """)
    print("Seed result:", seed_res)

    eval_js('window.TempoMode.setMode("emergency")')
    time.sleep(1)

    # Inspect rendered items in URmode Working Plan
    items_info = eval_js("""
        (() => {
            const items = Array.from(document.querySelectorAll('.urgent-timeline-item'));
            return items.map(el => ({
                id: el.getAttribute('data-task-id'),
                title: el.querySelector('h4') ? el.querySelector('h4').innerText.trim() : null,
                badge: el.querySelector('span[class*="rounded-full"]') ? el.querySelector('span[class*="rounded-full"]').innerText.trim() : null,
                meta: el.querySelector('.pl-6\\.5') ? el.querySelector('.pl-6\\.5').innerText.trim() : null
            }));
        })()
    """)
    print("Rendered items in URmode:", json.dumps(items_info, indent=2))

    ws.close()
finally:
    proc.terminate()
