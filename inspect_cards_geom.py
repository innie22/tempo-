import subprocess, json, time, urllib.request, websocket, sys
sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = r'C:\Users\YEN NHI\AppData\Local\Temp\tempo_inspect_cards_geom'
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9301

cmd = [edge_path, '--headless=new', f'--remote-debugging-port={port}', '--remote-allow-origins=*', f'--user-data-dir={user_data_dir}', '--disable-gpu', '--no-first-run', '--window-size=1440,900', 'http://127.0.0.1:8000/']
proc = subprocess.Popen(cmd)
time.sleep(1.5)

try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        tabs = json.loads(resp.read().decode())
        ws_url = [t for t in tabs if t.get('type') == 'page'][0]['webSocketDebuggerUrl']

    ws = websocket.create_connection(ws_url)

    def eval_js(expr):
        ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True, 'awaitPromise': True}}))
        res = json.loads(ws.recv())
        return res.get('result', {}).get('result', {}).get('value')

    eval_js("window.TempoMode.setMode('recovery')")
    time.sleep(1)

    geom_info = eval_js("""(() => {
        const cards = Array.from(document.querySelectorAll('#recovery-working-plan [data-task-id]'));
        return cards.map(c => {
            const taskId = c.getAttribute('data-task-id');
            const rect = c.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            const topEl = document.elementFromPoint(centerX, centerY);
            const titleEl = c.querySelector('h5');
            return {
                taskId,
                title: titleEl ? titleEl.textContent.trim() : null,
                rect: { top: rect.top, bottom: rect.bottom, left: rect.left, right: rect.right, width: rect.width, height: rect.height },
                elementFromPointCenter: topEl ? { tag: topEl.tagName, className: topEl.className, text: topEl.textContent.trim().slice(0, 30) } : null,
                containsCenterEl: topEl ? c.contains(topEl) : false
            };
        });
    })()""")

    print(json.dumps(geom_info, indent=2))
    ws.close()
finally:
    proc.kill()
