import subprocess, time, json, urllib.request, websocket, tempfile

user_data_dir = tempfile.mkdtemp(prefix='tempo_crop_check_')
port = 9462
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
        cmd = {'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}
        ws.send(json.dumps(cmd))
        return json.loads(ws.recv())['result']['result'].get('value')

    text_info = eval_js("""
        (async () => {
            const loadImg = (url) => new Promise((resolve) => {
                const img = new Image();
                img.onload = () => resolve(img);
                img.src = url;
            });
            const img = await loadImg('/scratch/ref2_search_crop.png');
            const canvas = document.createElement('canvas');
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0);

            // Group dark pixels by X
            const xHist = {};
            for (let x = 0; x < img.width; x++) {
                let cnt = 0;
                for (let y = 0; y < img.height; y++) {
                    const p = ctx.getImageData(x, y, 1, 1).data;
                    if (p[0] < 120 && p[1] < 120 && p[2] < 120) cnt++;
                }
                if (cnt > 0) xHist[x] = cnt;
            }
            return {
                width: img.width,
                height: img.height,
                xHist
            };
        })()
    """)

    xHist = text_info['xHist']
    # Print ranges of x where pixels exist
    cols = sorted([int(k) for k in xHist.keys()])
    if cols:
        print(f"Dark pixels from X={cols[0]} to X={cols[-1]}")
        # Find gaps > 20px
        clusters = []
        cur = [cols[0]]
        for c in cols[1:]:
            if c - cur[-1] > 15:
                clusters.append((cur[0], cur[-1]))
                cur = [c]
            else:
                cur.append(c)
        clusters.append((cur[0], cur[-1]))
        print("Clusters of dark pixels:", clusters)
    else:
        print("No dark pixels in crop")

finally:
    proc.terminate()
