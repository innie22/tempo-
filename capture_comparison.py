import subprocess, time, json, urllib.request, websocket, base64, tempfile, os

CDP_PORT = 9452
user_data_dir = tempfile.mkdtemp(prefix='edge_comp_')

proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={CDP_PORT}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--window-size=1000,600',
    'http://127.0.0.1:8000/scratch/compare.html'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    time.sleep(2)
    with urllib.request.urlopen(f'http://127.0.0.1:{CDP_PORT}/json') as resp:
        tabs = json.loads(resp.read().decode())
    pages = [t for t in tabs if t.get('type') == 'page' and '127.0.0.1' in t.get('url', '')]
    ws_url = (pages[0] if pages else tabs[0])['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)

    mid = [1]
    def send(method, params=None):
        m = mid[0]
        mid[0] += 1
        ws.send(json.dumps({'id': m, 'method': method, 'params': params or {}}))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == m:
                return resp.get('result', {})

    send("Page.enable")
    time.sleep(1)
    res = send('Page.captureScreenshot')
    data = base64.b64decode(res['data'])
    out_path = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\mascot_comparison_rendered.png'
    with open(out_path, 'wb') as f:
        f.write(data)
    print(f"Captured: {out_path} ({len(data)} bytes)")
finally:
    try:
        proc.kill()
    except:
        pass
