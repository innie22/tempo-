import subprocess, time, json, urllib.request, websocket, sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    port = 9226
    cmd = [edge_path, '--headless=new', f'--remote-debugging-port={port}', '--remote-allow-origins=*', '--disable-gpu', '--no-first-run', 'http://localhost:8000/#mode']
    proc = subprocess.Popen(cmd)
    try:
        time.sleep(2)
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
            tabs = json.loads(resp.read().decode())
            ws_url = [t for t in tabs if t.get('type') == 'page'][0]['webSocketDebuggerUrl']
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
        time.sleep(1.5)
        eval_js("window.TempoMode.setMode('emergency')")
        time.sleep(1.0)
        print('Clicking View today checkin button...')
        eval_js("""
            (() => {
                const btn = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"] button');
                btn.click();
            })()
        """)
        time.sleep(1.0)
        print('modal-auth hidden?:', eval_js('document.getElementById("modal-auth")?.classList.contains("hidden")'))
        print('modal-selfcheck-daily hidden?:', eval_js('document.getElementById("modal-selfcheck-daily")?.classList.contains("hidden")'))
        print('modal-selfcheck-view hidden?:', eval_js('document.getElementById("modal-selfcheck-view")?.classList.contains("hidden")'))
        print('screen-stress-check hidden?:', eval_js('document.getElementById("screen-stress-check")?.classList.contains("hidden")'))


        print('Localstorage items:', eval_js('Object.fromEntries(Object.keys(localStorage).map(k => [k, localStorage.getItem(k)]))'))
    finally:
        proc.terminate()

if __name__ == '__main__':
    main()
