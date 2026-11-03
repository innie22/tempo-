import urllib.request, json, time, subprocess, tempfile, websocket, sys, os
sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp()
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9595

cmd = [
    edge_path, '--headless=new', f'--remote-debugging-port={port}',
    '--remote-allow-origins=*', f'--user-data-dir={user_data_dir}',
    '--disable-gpu', '--no-first-run', 'http://127.0.0.1:8000/#community?tab=tips'
]
proc = subprocess.Popen(cmd)
try:
    time.sleep(2.5)
    tabs = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/json').read().decode())
    app_tab = next(t for t in tabs if '8000' in t.get('url', ''))
    ws = websocket.create_connection(app_tab['webSocketDebuggerUrl'], timeout=10)
    ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {
        'expression': '''(() => {
            const sits = (window.TempoLearnSolve && typeof window.TempoLearnSolve.getSituations === 'function')
                ? window.TempoLearnSolve.getSituations() : [];
            return sits.map(s => ({ id: s.id, title: s.title, desc: s.shortDescription }));
        })()''',
        'returnByValue': True
    }}))
    while True:
        res = json.loads(ws.recv())
        if res.get('id') == 1:
            val = res.get('result', {}).get('result', {}).get('value')
            print(f'Total situations from TempoLearnSolve.getSituations(): {len(val)}')
            for idx, s in enumerate(val):
                print(f'{idx+1}: {s["id"]} | {s["title"]} | {s["desc"][:50]}')
            break
finally:
    proc.terminate()
