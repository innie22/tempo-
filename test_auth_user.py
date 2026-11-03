import subprocess, time, json, urllib.request, websocket, sys

def main():
    edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    port = 9222
    cmd = [
        edge_path,
        '--headless=new',
        f'--remote-debugging-port={port}',
        '--remote-allow-origins=*',
        '--disable-gpu',
        '--no-first-run',
        'http://localhost:8000/'
    ]
    proc = subprocess.Popen(cmd)
    try:
        time.sleep(2)
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
            tabs = json.loads(resp.read().decode())
            ws_url = [t for t in tabs if t.get('type') == 'page'][0]['webSocketDebuggerUrl']
        ws = websocket.create_connection(ws_url)

        msg_id = 0
        def send_command(method, params=None):
            nonlocal msg_id
            msg_id += 1
            ws.send(json.dumps({'id': msg_id, 'method': method, 'params': params or {}}))
            while True:
                r = json.loads(ws.recv())
                if r.get('id') == msg_id:
                    return r.get('result', {})

        send_command('Runtime.enable')

        def eval_js(exp):
            res = send_command('Runtime.evaluate', {'expression': exp, 'returnByValue': True, 'awaitPromise': True})
            if 'exceptionDetails' in res:
                print('JS Err:', res['exceptionDetails'])
            return res.get('result', {}).get('value')

        for _ in range(20):
            ready = eval_js('typeof window.TempoMode !== "undefined" && typeof window.TempoAuth !== "undefined"')
            if ready:
                break
            time.sleep(0.3)

        print('Scripts ready!')

        # Sign in as student@tempo.app
        eval_js("""
            (() => {
                const email = 'student@tempo.app';
                const mockAccount = {
                    id: 'usr_student_verify_001',
                    email: email,
                    password: 'password123',
                    user_metadata: { full_name: 'Student Demo' },
                    created_at: new Date().toISOString()
                };
                localStorage.setItem('tempo_mock_account_' + email, JSON.stringify(mockAccount));
            })()
        """)
        eval_js("window.TempoAuth.signIn('student@tempo.app', 'password123')")
        time.sleep(0.5)

        # Go to emergency
        eval_js('window.TempoMode.setMode("emergency")')
        time.sleep(0.5)

        card_text = eval_js('document.querySelector("[data-tempo-ui=\\"lower-selfcheck-streak\\"]")?.innerText')
        print('Streak card for student@tempo.app:\n', card_text)

        # Now click button
        eval_js('''
            (() => {
                const btn = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"] button');
                btn?.click();
            })()
        ''')
        time.sleep(0.5)

        modals = eval_js('''
            (() => {
                return {
                    daily: !document.getElementById('modal-selfcheck-daily')?.classList.contains('hidden'),
                    view: !document.getElementById('modal-selfcheck-view')?.classList.contains('hidden'),
                    manage: !document.getElementById('modal-selfcheck-manage')?.classList.contains('hidden'),
                    auth: !document.getElementById('modal-auth')?.classList.contains('hidden')
                };
            })()
        ''')
        print('Modals for authenticated user:', modals)

    finally:
        proc.terminate()

if __name__ == '__main__':
    main()
