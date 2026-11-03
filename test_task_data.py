import subprocess, json, time, urllib.request, websocket, sys
sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = r'C:\Users\YEN NHI\AppData\Local\Temp\tempo_test_task_data'
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9305

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

    eval_js("window.TempoMode.setMode('recovery')")
    time.sleep(1)

    cards = eval_js("""(() => {
        const els = Array.from(document.querySelectorAll('[data-task-id]'));
        return els.map(e => e.getAttribute('data-task-id'));
    })()""")
    print("Cards on page:", cards)

    for cid in cards:
        tdata = eval_js(f"window.TempoMode.getRmodeTaskData('{cid}')")
        html_modal = eval_js(f"""(() => {{
            window.TempoMode.openRmodeTaskDetailModal('{cid}');
            const m = document.getElementById('rmode-task-detail-modal');
            const title = m ? (m.querySelector('#rmode-task-modal-title') ? m.querySelector('#rmode-task-modal-title').textContent.trim() : 'NO TITLE') : null;
            window.TempoMode.closeRmodeTaskDetailModal();
            return {{ modalFound: !!m, title }};
        }})()""")
        print(f"Task ID '{cid}': taskFound={bool(tdata and tdata.get('task'))}, modal={html_modal}")

    ws.close()
finally:
    proc.kill()
