import subprocess, json, time, urllib.request, websocket, sys
sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = r'C:\Users\YEN NHI\AppData\Local\Temp\tempo_inspect_plan_state'
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9297

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

    plan_data = eval_js("""(() => {
        const wsPlan = window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.getActivePlan === 'function' ? window.TempoPlanWorkspace.getActivePlan() : null;
        const storePlan = window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function' ? window.TempoPlanStore.getActivePlan('recovery') : null;
        const lsPlan = localStorage.getItem('tempo_working_plan');
        const cards = Array.from(document.querySelectorAll('#recovery-working-plan [data-task-id]')).map(c => ({
            taskId: c.getAttribute('data-task-id'),
            text: c.querySelector('h5') ? c.querySelector('h5').textContent.trim() : null
        }));
        return {
            cards,
            wsPlannedTasks: wsPlan ? (wsPlan.plannedTasks || []).map(pt => ({ id: pt.task ? pt.task.id : pt.id, name: pt.task ? pt.task.name : pt.name })) : [],
            storePlannedTasks: storePlan ? (storePlan.plannedTasks || []).map(pt => ({ id: pt.task ? pt.task.id : pt.id, name: pt.task ? pt.task.name : pt.name })) : [],
            hasLs: !!lsPlan,
            lsRaw: lsPlan ? lsPlan.slice(0, 500) : null
        };
    })()""")

    print(json.dumps(plan_data, indent=2))
    ws.close()
finally:
    proc.kill()
