import subprocess, time, json, urllib.request, websocket, tempfile, os

user_data_dir = tempfile.mkdtemp(prefix='tempo_crop_')
port = 9457
proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={port}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--disable-gpu',
    '--no-first-run',
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

    ref_path = "file:///C:/Users/YEN NHI/.gemini/antigravity/brain/6baf9c9e-16aa-475f-b2c0-d941b08ac2c6/.user_uploaded/media_1792922507504_d96a1582.png"

    # Analyze the search bar in media_1792922507504_d96a1582.png
    analysis = eval_js(f"""
        new Promise((resolve) => {{
            const img = new Image();
            img.onload = () => {{
                const canvas = document.createElement('canvas');
                canvas.width = img.width;
                canvas.height = img.height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);
                
                // Scan the top 200px of image for horizontal bars of color around #F2EAE3
                // Let's sample pixels across x from 300 to 1200 at y=50, 70, 90
                const samples = [];
                for (let y = 30; y < 150; y += 10) {{
                    for (let x = 300; x < img.width - 50; x += 50) {{
                        const p = ctx.getImageData(x, y, 1, 1).data;
                        samples.push({{ x, y, r: p[0], g: p[1], b: p[2] }});
                    }}
                }}
                resolve({{ width: img.width, height: img.height, samples: samples.slice(0, 20) }});
            }};
            img.src = "{ref_path}";
        }})
    """)
    print("Image analysis:", analysis['width'], analysis['height'])

finally:
    proc.terminate()
