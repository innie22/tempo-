import subprocess, time, json, urllib.request, websocket, tempfile

user_data_dir = tempfile.mkdtemp(prefix='tempo_ref_test_')
port = 9460
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

    res = eval_js("""
        (async () => {
            const loadImg = (url) => new Promise((resolve) => {
                const img = new Image();
                img.onload = () => resolve(img);
                img.onerror = () => resolve(null);
                img.src = url;
            });

            const img2 = await loadImg('/assets/test_ref2.png');
            if (!img2) return { error: 'Failed to load test_ref2' };

            const canvas = document.createElement('canvas');
            canvas.width = img2.naturalWidth;
            canvas.height = img2.naturalHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img2, 0, 0);

            // Find capsule search bar bounding box
            let minX = 9999, maxX = 0, minY = 9999, maxY = 0;
            for (let y = 10; y < 140; y++) {
                for (let x = 150; x < img2.naturalWidth; x++) {
                    const p = ctx.getImageData(x, y, 1, 1).data;
                    // Check light beige background
                    if (p[0] > 235 && p[0] < 250 && p[1] > 225 && p[1] < 242 && p[2] > 218 && p[2] < 235) {
                        minX = Math.min(minX, x);
                        maxX = Math.max(maxX, x);
                        minY = Math.min(minY, y);
                        maxY = Math.max(maxY, y);
                    }
                }
            }

            // In this capsule, check where dark pixels (text / icon) are
            const darkPixels = [];
            for (let y = minY; y <= maxY; y++) {
                for (let x = minX; x <= maxX; x++) {
                    const p = ctx.getImageData(x, y, 1, 1).data;
                    if (p[0] < 140 && p[1] < 140 && p[2] < 140) {
                        darkPixels.push({ x, y });
                    }
                }
            }

            // Cluster dark pixels into leftmost cluster and rightmost cluster
            const darkXs = darkPixels.map(p => p.x);
            const minDarkX = Math.min(...darkXs);
            const maxDarkX = Math.max(...darkXs);

            return {
                width: img2.naturalWidth,
                height: img2.naturalHeight,
                capsule: { minX, maxX, minY, maxY, width: maxX - minX, height: maxY - minY },
                minDarkX,
                maxDarkX,
                leftMargin: minDarkX - minX,
                rightMargin: maxX - maxDarkX,
                totalDark: darkPixels.length,
                leftDarkInFirst50px: darkPixels.filter(p => p.x - minX < 60).length,
                rightDarkInLast50px: darkPixels.filter(p => maxX - p.x < 60).length
            };
        })()
    """)

    print("Ref 2 Analysis:", json.dumps(res, indent=2))

finally:
    proc.terminate()
