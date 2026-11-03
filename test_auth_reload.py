import urllib.request, json, websocket, time, tempfile, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')

edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
user_data_dir = tempfile.mkdtemp(prefix='tempo_auth_chk_')
port = 9494
cmd = [edge_path, '--headless=new', f'--remote-debugging-port={port}', '--remote-allow-origins=*', f'--user-data-dir={user_data_dir}', 'http://127.0.0.1:8000/#today']
proc = subprocess.Popen(cmd)
time.sleep(2)

try:
    tabs = json.loads(urllib.request.urlopen(f'http://127.0.0.1:{port}/json').read())
    ws = websocket.create_connection(tabs[0]['webSocketDebuggerUrl'])
    msg_id = 1
    def send_cmd(method, params=None):
        global msg_id
        cmd_obj = {'id': msg_id, 'method': method, 'params': params or {}}
        msg_id += 1
        ws.send(json.dumps(cmd_obj))
        while True:
            res = json.loads(ws.recv())
            if res.get('id') == cmd_obj['id']:
                return res.get('result', {})

    def eval_js(expr):
        res = send_cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
        if 'exceptionDetails' in res:
            print('EXCEPTION:', res['exceptionDetails'])
        return res.get('result', {}).get('value')

    send_cmd('Page.enable')
    send_cmd('Runtime.enable')

    # Seed mock auth + emergency mode + plan
    s = eval_js("""
    (() => {
        const mockUser = { id: 'dev_user_1', email: 'dev@tempo.local', user_metadata: { full_name: 'Innie', role: 'student' } };
        localStorage.setItem('tempo_local_dev_user', JSON.stringify(mockUser));
        localStorage.setItem('tempo_mock_account_dev@tempo.local', JSON.stringify(mockUser));
        localStorage.setItem('tempo_user_established_context_dev_user_1', 'emergency');
        localStorage.setItem('tempo_established_context', 'emergency');
        localStorage.setItem('tempo_current_mode', 'emergency');

        const todayStr = '2026-11-01';
        const plan = {
            id: 'plan_test',
            createdDate: todayStr,
            plannedTasks: [{ id: 'pt1', dayDate: todayStr, startTime: '14:00', endTime: '15:00', task: { id: 't1', title: 'Task 1' } }]
        };
        localStorage.setItem('tempo_confirmed_plan', JSON.stringify(plan));
        window.TempoMode.transitionContext('emergency');
        window.TempoMode.renderActiveModeHome();
        return {
            ctx: window.TempoMode.getActiveContext(),
            btn: document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText?.trim()
        };
    })()
    """)
    print('before reload:', s)

    send_cmd('Page.reload')
    time.sleep(2)

    s2 = eval_js("""
    (() => {
        return {
            ctx: window.TempoMode.getActiveContext(),
            auth: window.TempoAuth ? window.TempoAuth.getAuthState() : null,
            btn: document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText?.trim()
        };
    })()
    """)
    print('after reload:', s2)

finally:
    proc.terminate()
