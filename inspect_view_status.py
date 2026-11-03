import subprocess, json, time, urllib.request, websocket, sys
sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = r'C:\Users\YEN NHI\AppData\Local\Temp\tempo_inspect_cards_geom_2'
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9303

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
    status = eval_js("""(() => {
        return {
            hash: window.location.hash,
            mode: window.TempoMode ? window.TempoMode.getMode() : null,
            recoveryView: document.getElementById('recovery-mode-view') ? {
                display: window.getComputedStyle(document.getElementById('recovery-mode-view')).display,
                classList: document.getElementById('recovery-mode-view').className
            } : null,
            rmodeBox: document.getElementById('rmode-home-content') ? {
                hasContent: document.getElementById('rmode-home-content').innerHTML.length > 50
            } : null
        };
    })()""")
    print("Page status before setMode:", json.dumps(status, indent=2))

    eval_js("window.TempoMode.setMode('recovery')")
    time.sleep(1)

    status_after = eval_js("""(() => {
        return {
            hash: window.location.hash,
            mode: window.TempoMode ? window.TempoMode.getMode() : null,
            recoveryView: document.getElementById('recovery-mode-view') ? {
                display: window.getComputedStyle(document.getElementById('recovery-mode-view')).display,
                classList: document.getElementById('recovery-mode-view').className
            } : null,
            rmodeBox: document.getElementById('rmode-home-content') ? {
                hasContent: document.getElementById('rmode-home-content').innerHTML.length > 50
            } : null,
            allDataTaskId: Array.from(document.querySelectorAll('[data-task-id]')).map(e => e.getAttribute('data-task-id'))
        };
    })()""")
    print("Page status after setMode:", json.dumps(status_after, indent=2))

    ws.close()
finally:
    proc.kill()
