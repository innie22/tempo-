# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, tempfile, websocket, sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
user_data_dir = tempfile.mkdtemp(prefix='tempo_ucheck_check_')
port = 9299
cmd = [edge_path, '--headless=new', f'--remote-debugging-port={port}', '--remote-allow-origins=*', f'--user-data-dir={user_data_dir}', '--disable-gpu', '--no-first-run', 'http://localhost:8000/']
proc = subprocess.Popen(cmd)
time.sleep(2)

try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        tabs = json.loads(resp.read().decode())
        ws_url = tabs[0]['webSocketDebuggerUrl']

    ws = websocket.create_connection(ws_url)
    msg_id = 1
    def send_cmd(method, params=None):
        global msg_id
        cid = msg_id; msg_id += 1
        ws.send(json.dumps({'id': cid, 'method': method, 'params': params or {}}))
        while True:
            raw = ws.recv()
            r = json.loads(raw)
            if r.get('id') == cid:
                return r

    def evaluate(expr):
        r = send_cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
        if 'exceptionDetails' in r.get('result', {}):
            print("EXCEPTION:", r['result']['exceptionDetails'])
        return r.get('result', {}).get('result', {}).get('value')

    for _ in range(30):
        if evaluate("Boolean(window.TempoMode && window.TempoApp && window.TempoAuth)"):
            break
        time.sleep(0.3)

    print("App ready!")
    evaluate("""
    window.TempoAuth.authenticateUser({
        id: 'user_ucheck_test',
        email: 'test@tempo.edu.vn',
        display_name: 'Alex Tester'
    });
    """)
    time.sleep(0.3)
    evaluate("window.TempoMode.setMode('recovery');")
    time.sleep(0.3)
    evaluate("window.TempoMode.openUcheck({ sourceContext: 'recovery' });")
    time.sleep(0.5)

    info = evaluate("""(() => {
        const header = document.querySelector('header');
        const links = Array.from(header.querySelectorAll('nav a')).map(a => ({
            id: a.id,
            text: a.textContent.trim(),
            hidden: a.classList.contains('hidden'),
            href: a.getAttribute('href')
        }));
        return {
            headerClass: header.className,
            links: links,
            activeContext: window.TempoMode.getActiveContext(),
            currentMode: window.TempoMode.getMode()
        };
    })()""")
    print("INFO:", json.dumps(info, indent=2, ensure_ascii=False))

finally:
    proc.terminate()
