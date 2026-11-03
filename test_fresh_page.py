import subprocess, json, time, urllib.request, websocket, sys
sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = r'C:\Users\YEN NHI\AppData\Local\Temp\tempo_test_fresh_page'
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9307

cmd = [edge_path, '--headless=new', f'--remote-debugging-port={port}', '--remote-allow-origins=*', f'--user-data-dir={user_data_dir}', '--disable-gpu', '--no-first-run', '--window-size=1440,900', 'http://127.0.0.1:8000/']
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
    print("Default HTML contains recovery-mode-view:", eval_js("document.body.innerHTML.includes('recovery-mode-view')"))
    print("Default HTML contains rmode-home-content:", eval_js("document.body.innerHTML.includes('rmode-home-content')"))
    
    # Try calling setMode('recovery')
    res_set = eval_js("window.TempoMode ? window.TempoMode.setMode('recovery') : 'NO TempoMode'")
    print("setMode recovery returned:", res_set)
    time.sleep(1)

    print("After setMode HTML contains recovery-working-plan:", eval_js("document.body.innerHTML.includes('recovery-working-plan')"))
    print("rmode-home-content innerHTML length:", eval_js("document.getElementById('rmode-home-content') ? document.getElementById('rmode-home-content').innerHTML.length : -1"))
    print("recovery-working-plan exists:", eval_js("!!document.getElementById('recovery-working-plan')"))

    ws.close()
finally:
    proc.kill()
