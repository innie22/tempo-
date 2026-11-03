import subprocess, time, json, urllib.request, websocket

def main():
    edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    port = 9222
    cmd = [edge_path, '--headless=new', f'--remote-debugging-port={port}', '--remote-allow-origins=*', '--disable-gpu', '--no-first-run', 'http://localhost:8000/']
    proc = subprocess.Popen(cmd)
    try:
        time.sleep(2)
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
            ws_url = json.loads(resp.read().decode())[0]['webSocketDebuggerUrl']
        ws = websocket.create_connection(ws_url)
        msg_id = 0
        def eval_js(exp):
            nonlocal msg_id
            msg_id += 1
            ws.send(json.dumps({'id': msg_id, 'method': 'Runtime.evaluate', 'params': {'expression': exp, 'returnByValue': True, 'awaitPromise': True}}))
            while True:
                r = json.loads(ws.recv())
                if r.get('id') == msg_id:
                    return r.get('result', {}).get('result', {}).get('value')

        time.sleep(2)
        # Switch to recovery mode
        eval_js('window.TempoMode.setMode("recovery")')
        time.sleep(0.5)

        rmode_card = eval_js('document.querySelector(".recovery-card-selfcheck")?.innerText')
        print('Rmode card text as guest:\n', rmode_card)

        # Click View today's checkin button in Rmode card
        eval_js('''
            (() => {
                const btn = document.querySelector('.recovery-card-selfcheck button');
                console.log("Rmode button:", btn?.innerText);
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
                    auth: document.querySelector('.auth-modal-overlay:not(.hidden)') !== null,
                    screen: document.getElementById('screen-stress-check')?.classList.contains('hidden') === false
                };
            })()
        ''')
        print('Modals/screen after clicking in Rmode:', modals)

    finally:
        proc.terminate()

if __name__ == '__main__':
    main()
