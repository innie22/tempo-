import urllib.request, json, time, subprocess, tempfile, websocket, sys, os
sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp()
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9610

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
    ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {
        'expression': '''(() => {
            if (window.TempoCommunity) window.TempoCommunity.selectTab('learn');
            const cards = [];
            document.querySelectorAll('#learn-cards-grid > div').forEach(c => {
                const title = c.querySelector('h3')?.innerText?.trim();
                const summary = c.querySelector('p')?.innerText?.trim();
                cards.push({ title, summary });
            });
            return cards;
        })()''',
        'returnByValue': True
    }}))
    while True:
        res = json.loads(ws.recv())
        if res.get('id') == 1:
            val = res.get('result', {}).get('result', {}).get('value')
            print(f'Total cards rendered in Learn: {len(val)}')
            for idx, c in enumerate(val):
                print(f'{idx+1}: {c["title"]} | {c["summary"][:60]}')
            break
finally:
    proc.terminate()
