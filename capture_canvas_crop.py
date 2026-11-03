import subprocess, time, json, urllib.request, websocket, base64, tempfile, os

HTTP_PORT = 8000
CDP_PORT = 9475
artifact_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'
user_data_dir = tempfile.mkdtemp(prefix='edge_crop_canvas_')

proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={CDP_PORT}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--window-size=800,560',
    f'http://127.0.0.1:{HTTP_PORT}/scratch/crop_viewer.html'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    time.sleep(2)
    with urllib.request.urlopen(f'http://127.0.0.1:{CDP_PORT}/json') as resp:
        tabs = json.loads(resp.read().decode())
    pages = [t for t in tabs if t.get('type') == 'page' and '127.0.0.1' in t.get('url', '')]
    ws = websocket.create_connection(pages[0]['webSocketDebuggerUrl'])

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
    res = send('Page.captureScreenshot', {'format': 'png'})
    data = base64.b64decode(res['data'])
    out_path = os.path.join(artifact_dir, 'urmode_create_notes_cards_closeup.png')
    with open(out_path, 'wb') as f:
        f.write(data)
    print("Saved cards closeup:", out_path, len(data))
finally:
    try:
        proc.kill()
    except:
        pass
