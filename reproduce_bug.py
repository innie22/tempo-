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

        console_logs = []
        msg_id = 0
        def send_command(method, params=None):
            nonlocal msg_id
            msg_id += 1
            ws.send(json.dumps({'id': msg_id, 'method': method, 'params': params or {}}))
            while True:
                r = json.loads(ws.recv())
                if r.get('method') == 'Runtime.consoleAPICalled':
                    console_logs.append(r.get('params', {}))
                if r.get('id') == msg_id:
                    return r.get('result', {})

        send_command('Runtime.enable')
        send_command('Page.enable')
        send_command('Log.enable')

        def eval_js(exp):
            res = send_command('Runtime.evaluate', {'expression': exp, 'returnByValue': True, 'awaitPromise': True})
            if 'exceptionDetails' in res:
                print('JS Err:', res['exceptionDetails'])
            return res.get('result', {}).get('value')

        time.sleep(1)

        # Let's inspect mode and auth
        print('Initial mode:', eval_js('window.TempoMode ? window.TempoMode.getMode() : null'))
        print('Initial user:', eval_js('window.TempoAuth ? window.TempoAuth.getCurrentUser() : null'))
        
        # Switch to emergency mode
        eval_js('window.TempoMode.setMode("emergency")')
        time.sleep(0.5)

        # Inspect Streak card text and state
        print('\n--- STREAK CARD BEFORE CLICK ---')
        card_text = eval_js('document.querySelector("[data-tempo-ui=\\"lower-selfcheck-streak\\"]")?.innerText')
        print(card_text)

        # Inspect trackers and observations
        trackers = eval_js('window.TempoRecoverySelfCheck ? window.TempoRecoverySelfCheck.getActiveTrackers() : []')
        print('Active trackers:', trackers)
        today_chk = eval_js('window.TempoRecoverySelfCheck ? window.TempoRecoverySelfCheck.getTodayCheckin() : null')
        print('Today checkin in TempoRecoverySelfCheck:', today_chk)

        # Click the "View today's checkin" button!
        print('\n--- CLICKING "View today\'s checkin" BUTTON ---')
        eval_js('''
            (() => {
                const btn = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"] button');
                console.log("Button found:", btn?.innerText);
                btn?.click();
            })()
        ''')
        time.sleep(1)

        # Check which modals are visible
        modals = eval_js('''
            (() => {
                return {
                    daily: !document.getElementById('modal-selfcheck-daily')?.classList.contains('hidden'),
                    view: !document.getElementById('modal-selfcheck-view')?.classList.contains('hidden'),
                    manage: !document.getElementById('modal-selfcheck-manage')?.classList.contains('hidden'),
                    auth: !document.getElementById('modal-auth')?.classList.contains('hidden'),
                    toast: document.querySelector('.tempo-toast')?.innerText || document.getElementById('toast')?.innerText
                };
            })()
        ''')
        print('Modal states after click:', modals)
        print('Console logs:', console_logs)

    finally:
        proc.terminate()

if __name__ == '__main__':
    main()
