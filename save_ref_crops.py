import subprocess, time, json, urllib.request, websocket, tempfile, base64

user_data_dir = tempfile.mkdtemp(prefix='tempo_save_crop_')
port = 9461
proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={port}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    'http://localhost:8000/'
])
time.sleep(2)

try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        tabs = json.loads(resp.read().decode())
        pages = [t for t in tabs if t.get('type') == 'page' and 'localhost' in t.get('url', '')]
    ws_url = pages[0]['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)

    def eval_js(expr):
        cmd = {'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True, 'awaitPromise': True}}
        ws.send(json.dumps(cmd))
        return json.loads(ws.recv())['result']['result'].get('value')

    b64 = eval_js("""
        (async () => {
            const loadImg = (url) => new Promise((resolve) => {
                const img = new Image();
                img.onload = () => resolve(img);
                img.onerror = () => resolve(null);
                img.src = url;
            });

            const img2 = await loadImg('/assets/test_ref2.png');
            const canvas = document.createElement('canvas');
            canvas.width = 600;
            canvas.height = 70;
            const ctx = canvas.getContext('2d');
            // Crop the actual search bar
            ctx.drawImage(img2, 230, 25, 600, 70, 0, 0, 600, 70);
            return canvas.toDataURL('image/png').split(',')[1];
        })()
    """)

    with open('scratch/ref2_search_crop.png', 'wb') as f:
        f.write(base64.b64decode(b64))
    print("Saved scratch/ref2_search_crop.png")

    # Let's also crop test_ref4.png
    b64_4 = eval_js("""
        (async () => {
            const loadImg = (url) => new Promise((resolve) => {
                const img = new Image();
                img.onload = () => resolve(img);
                img.onerror = () => resolve(null);
                img.src = url;
            });

            const img4 = await loadImg('/assets/test_ref4.png');
            const canvas = document.createElement('canvas');
            canvas.width = 600;
            canvas.height = 70;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img4, 230, 25, 600, 70, 0, 0, 600, 70);
            return canvas.toDataURL('image/png').split(',')[1];
        })()
    """)

    with open('scratch/ref4_search_crop.png', 'wb') as f:
        f.write(base64.b64decode(b64_4))
    print("Saved scratch/ref4_search_crop.png")

finally:
    proc.terminate()
