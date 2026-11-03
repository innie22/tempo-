import subprocess, time, json, urllib.request, websocket, tempfile, base64

user_data_dir = tempfile.mkdtemp(prefix='tempo_crop_')
port = 9458
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

    # Crop search bar from ref
    b64 = eval_js(f"""
        new Promise((resolve) => {{
            const img = new Image();
            img.onload = () => {{
                // Search bar is roughly in the top right area
                const canvas = document.createElement('canvas');
                canvas.width = 800;
                canvas.height = 120;
                const ctx = canvas.getContext('2d');
                // Draw crop
                ctx.drawImage(img, 250, 20, 800, 120, 0, 0, 800, 120);
                resolve(canvas.toDataURL('image/png').split(',')[1]);
            }};
            img.src = "{ref_path}";
        }})
    """)
    if b64:
        with open('scratch/ref_search_bar.png', 'wb') as f:
            f.write(base64.b64decode(b64))
        print("Saved scratch/ref_search_bar.png")

    # Let's inspect where dark pixels (text vs icon) are located in that crop:
    crop_info = eval_js(f"""
        new Promise((resolve) => {{
            const img = new Image();
            img.onload = () => {{
                const canvas = document.createElement('canvas');
                canvas.width = 800;
                canvas.height = 120;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 250, 20, 800, 120, 0, 0, 800, 120);
                const data = ctx.getImageData(0, 0, 800, 120).data;
                // Find dark pixels (r < 100, g < 100, b < 100)
                let minX = 800, maxX = 0;
                const xs = [];
                for (let y = 0; y < 120; y++) {{
                    for (let x = 0; x < 800; x++) {{
                        const idx = (y * 800 + x) * 4;
                        if (data[idx] < 120 && data[idx+1] < 120 && data[idx+2] < 120) {{
                            xs.push(x);
                        }}
                    }}
                }}
                resolve({{ count: xs.length, minX: Math.min(...xs), maxX: Math.max(...xs), sampleXs: xs.filter((_, i) => i % 50 === 0) }});
            }};
            img.src = "{ref_path}";
        }})
    """)
    print("Crop dark pixel info:", crop_info)

finally:
    proc.terminate()
