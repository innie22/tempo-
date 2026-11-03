import urllib.request, json, time, subprocess, tempfile, websocket, sys, os
sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp()
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9615

cmd = [
    edge_path, '--headless=new', f'--remote-debugging-port={port}',
    '--remote-allow-origins=*', f'--user-data-dir={user_data_dir}',
    '--disable-gpu', '--no-first-run', 'http://127.0.0.1:8000/#community?tab=learn'
]
proc = subprocess.Popen(cmd)
try:
    time.sleep(2.5)
    tabs = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/json').read().decode())
    app_tab = next(t for t in tabs if '8000' in t.get('url', ''))
    ws = websocket.create_connection(app_tab['webSocketDebuggerUrl'], timeout=10)
    
    def eval_js(expr):
        ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {
            'expression': expr,
            'returnByValue': True
        }}))
        while True:
            res = json.loads(ws.recv())
            if res.get('id') == 1:
                return res.get('result', {}).get('result', {}).get('value')

    eval_js("window.TempoCommunity.selectTab('learn'); window.TempoCommunity.openLearnDetail('what_is_stress');")
    time.sleep(1)
    
    modal_html = eval_js("document.getElementById('tempo-learn-solve-modal-card')?.innerHTML")
    print("Modal HTML for 'what_is_stress':\n", modal_html[:1500])

finally:
    proc.terminate()
