import subprocess, time, json, urllib.request, websocket, tempfile, base64

user_data_dir = tempfile.mkdtemp(prefix='tempo_edge_img_')
port = 9459
proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={port}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--disable-gpu',
    '--no-first-run',
    'file:///C:/Users/YEN%20NHI/.gemini/antigravity/brain/6baf9c9e-16aa-475f-b2c0-d941b08ac2c6/.user_uploaded/media_1792922507504_d96a1582.png'
])
time.sleep(2)

try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        tabs = json.loads(resp.read().decode())
    ws_url = tabs[0]['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)

    def eval_js(expr):
        cmd = {'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True, 'awaitPromise': True}}
        ws.send(json.dumps(cmd))
        return json.loads(ws.recv())['result']['result'].get('value')

    info = eval_js("""
        (() => {
            return {
                url: window.location.href,
                body: document.body.innerHTML,
                tagCount: document.getElementsByTagName('*').length
            };
        })()
    """)
    print("Search bar info in Ref 2:", json.dumps(info, indent=2))

finally:
    proc.terminate()
