import subprocess, time, json, urllib.request, websocket

def main():
    edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    port = 9222
    cmd = [edge_path, '--headless=new', f'--remote-debugging-port={port}', '--remote-allow-origins=*', '--disable-gpu', '--no-first-run', 'http://localhost:8000/']
    proc = subprocess.Popen(cmd)
    try:
        time.sleep(2)
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
            tabs = json.loads(resp.read().decode())
            ws_url = [t for t in tabs if t.get('type') == 'page'][0]['webSocketDebuggerUrl']
        ws = websocket.create_connection(ws_url)
        msg_id = 0
        console_logs = []
        def send_cmd(method, params=None):
            nonlocal msg_id
            msg_id += 1
            ws.send(json.dumps({'id': msg_id, 'method': method, 'params': params or {}}))
            while True:
                r = json.loads(ws.recv())
                if r.get('method') == 'Runtime.consoleAPICalled':
                    console_logs.append(r.get('params'))
                if r.get('method') == 'Runtime.exceptionThrown':
                    print('EXCEPTION THROWN:', r.get('params'))
                if r.get('id') == msg_id:
                    return r.get('result', {})

        send_cmd('Runtime.enable')
        send_cmd('Log.enable')
        send_cmd('Page.enable')

        time.sleep(3)
        res = send_cmd('Runtime.evaluate', {'expression': 'window.TempoRecoverySelfCheck', 'returnByValue': True})
        print('window.TempoRecoverySelfCheck:', res)
        res_mode = send_cmd('Runtime.evaluate', {'expression': 'window.TempoMode', 'returnByValue': True})
        print('window.TempoMode:', res_mode)
        print('Logs count:', len(console_logs))
    finally:
        proc.terminate()

if __name__ == '__main__':
    main()
