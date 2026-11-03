import subprocess, json, time, urllib.request, websocket, sys
sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = r'C:\Users\YEN NHI\AppData\Local\Temp\tempo_inspect_plan_tasks_full'
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9299

cmd = [edge_path, '--headless=new', f'--remote-debugging-port={port}', '--remote-allow-origins=*', f'--user-data-dir={user_data_dir}', '--disable-gpu', '--no-first-run', 'http://127.0.0.1:8000/']
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

    plan_dump = eval_js("""(() => {
        const p = window.TempoPlanWorkspace ? window.TempoPlanWorkspace.getActivePlan() : null;
        return p;
    })()""")

    print("Planned tasks count:", len(plan_dump.get('plannedTasks', [])))
    for idx, pt in enumerate(plan_dump.get('plannedTasks', [])):
        t = pt.get('task', pt)
        print(f"Task {idx}: id={t.get('id')}, name={t.get('name')}, pt.id={pt.get('id')}")

    ws.close()
finally:
    proc.kill()
