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
        ws_url = None
        for _ in range(10):
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
                    tabs = json.loads(resp.read().decode())
                    pages = [t for t in tabs if t.get('type') == 'page']
                    if pages:
                        ws_url = pages[0]['webSocketDebuggerUrl']
                        break
            except Exception:
                time.sleep(0.5)

        if not ws_url:
            print('Could not connect to CDP')
            return

        ws = websocket.create_connection(ws_url)
        msg_id = 0

        def send_command(method, params=None):
            nonlocal msg_id
            msg_id += 1
            req = {'id': msg_id, 'method': method}
            if params:
                req['params'] = params
            ws.send(json.dumps(req))
            while True:
                resp = json.loads(ws.recv())
                if resp.get('id') == msg_id:
                    return resp.get('result', {})

        def eval_js(expression):
            res = send_command('Runtime.evaluate', {
                'expression': expression,
                'returnByValue': True,
                'awaitPromise': True
            })
            if 'exceptionDetails' in res:
                print('JS Err:', res['exceptionDetails'])
            return res.get('result', {}).get('value')

        time.sleep(1)
        # Register/sign in a test user
        eval_js("""
            (() => {
                const email = 'test_checkin_user@tempo.app';
                const mockAccount = {
                    id: 'usr_test_checkin_123',
                    email: email,
                    password: 'password123',
                    user_metadata: { full_name: 'Test Checkin Student' },
                    created_at: new Date().toISOString()
                };
                localStorage.setItem('tempo_mock_account_' + email, JSON.stringify(mockAccount));
            })()
        """)
        
        eval_js("""
            window.TempoAuth.signIn('test_checkin_user@tempo.app', 'password123')
        """)
        time.sleep(0.5)

        user = eval_js('window.TempoAuth ? window.TempoAuth.getCurrentUser() : null')
        print('Authenticated user:', user.get('email') if user else None)

        # Switch to emergency mode / dashboard
        eval_js("""
            window.TempoMode.setMode('emergency');
        """)
        time.sleep(0.5)

        # Inspect current streak card DOM
        card_text = eval_js("""
            document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]')?.innerText
        """)
        print('Current card text:\n', card_text)
    finally:
        proc.terminate()

if __name__ == '__main__':
    main()
