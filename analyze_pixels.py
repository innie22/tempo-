import subprocess, time, json, urllib.request, websocket, tempfile

CDP_PORT = 9454
user_data_dir = tempfile.mkdtemp(prefix='edge_px_')

proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={CDP_PORT}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
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
    res = send('Runtime.evaluate', {
        'awaitPromise': True,
        'returnByValue': True,
        'expression': """
            (async () => {
                async function analyze(src) {
                    const img = new Image();
                    img.src = src;
                    await new Promise(r => img.onload = r);
                    const cvs = document.createElement('canvas');
                    cvs.width = img.naturalWidth;
                    cvs.height = img.naturalHeight;
                    const ctx = cvs.getContext('2d');
                    ctx.drawImage(img, 0, 0);
                    const id = ctx.getImageData(0, 0, cvs.width, cvs.height);
                    let nonTrans = 0;
                    let minX = cvs.width, maxX = 0, minY = cvs.height, maxY = 0;
                    for (let y = 0; y < cvs.height; y++) {
                        for (let x = 0; x < cvs.width; x++) {
                            const a = id.data[(y * cvs.width + x) * 4 + 3];
                            if (a > 10) {
                                nonTrans++;
                                if (x < minX) minX = x;
                                if (x > maxX) maxX = x;
                                if (y < minY) minY = y;
                                if (y > maxY) maxY = y;
                            }
                        }
                    }
                    return {
                        src,
                        w: img.naturalWidth,
                        h: img.naturalHeight,
                        nonTransCount: nonTrans,
                        bbox: { minX, minY, maxX, maxY, bw: maxX - minX + 1, bh: maxY - minY + 1 }
                    };
                }
                return {
                    img1: await analyze('/assets/notes-mascot.png'),
                    img2: await analyze('/scratch/uploaded_mascot.png')
                };
            })()
        """
    })
    print(json.dumps(res.get('result', {}).get('value'), indent=2))
finally:
    try:
        proc.kill()
    except:
        pass
