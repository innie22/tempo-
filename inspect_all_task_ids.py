import subprocess, json, time, urllib.request, websocket, sys
sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = r'C:\Users\YEN NHI\AppData\Local\Temp\tempo_inspect_plan_state_2'
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9298

cmd = [edge_path, '--headless=new', f'--remote-debugging-port={port}', '--remote-allow-origins=*', f'--user-data-dir={user_data_dir}', '--disable-gpu', '--no-first-run', 'http://127.0.0.1:8000/']
proc = subprocess.Popen(cmd)
time.sleep(2)

try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        tabs = json.loads(resp.read().decode())
        ws_url = [t for t in tabs if t.get('type') == 'page'][0]['webSocketDebuggerUrl']

    ws = websocket.create_connection(ws_url)

    def eval_js(expr):
        ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True, 'awaitPromise': True}}))
        res = json.loads(ws.recv())
        return res.get('result', {}).get('result', {}).get('value')

    time.sleep(1)
    # Check default mode
    cur_mode = eval_js("window.TempoMode ? window.TempoMode.getMode() : 'no TempoMode'")
    print("Initial mode:", cur_mode)

    # Set recovery mode
    eval_js("window.TempoMode.setMode('recovery')")
    time.sleep(1)

    html_snippet = eval_js("""(() => {
        const wp = document.getElementById('recovery-working-plan');
        if (!wp) return 'NO recovery-working-plan element found!';
        return wp.outerHTML.slice(0, 1000);
    })()""")
    print("Working Plan HTML snippet:", html_snippet)

    # All data-task-id across the whole document:
    all_task_ids = eval_js("""(() => {
        const els = Array.from(document.querySelectorAll('[data-task-id]'));
        return els.map(e => ({
            id: e.getAttribute('data-task-id'),
            parent: e.parentElement ? e.parentElement.className : '',
            ancestor: e.closest('[data-tempo-ui]') ? e.closest('[data-tempo-ui]').getAttribute('data-tempo-ui') : ''
        }));
    })()""")
    print("All data-task-id elements on page:", json.dumps(all_task_ids, indent=2))

    ws.close()
finally:
    proc.kill()
