import subprocess, json, time, urllib.request, websocket, base64

edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9228
cmd = [edge_path, '--headless=new', f'--remote-debugging-port={port}', '--remote-allow-origins=*', '--disable-gpu', '--no-first-run', 'about:blank']
proc = subprocess.Popen(cmd)
try:
    time.sleep(1.5)
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        tabs = json.loads(resp.read().decode())
        ws_url = [t for t in tabs if t.get('type') == 'page'][0]['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)
    msg_id = 0
    def eval_js(exp):
        global msg_id
        msg_id += 1
        ws.send(json.dumps({'id': msg_id, 'method': 'Runtime.evaluate', 'params': {'expression': exp, 'returnByValue': True, 'awaitPromise': True}}))
        while True:
            r = json.loads(ws.recv())
            if r.get('id') == msg_id:
                return r.get('result', {}).get('result', {}).get('value')

    with open(r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\.user_uploaded\media_1793070414626_155afe5b.png', 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()

    eval_js(f"""
        (() => {{
            const img = new Image();
            img.src = 'data:image/png;base64,{img_b64}';
            img.onload = () => {{
                const canvas = document.createElement('canvas');
                // The card is on the left top: ~0..550 width, 0..260 height
                canvas.width = 550;
                canvas.height = 280;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 30, 20, 520, 260, 0, 0, 520, 260);
                window.cardCropData = canvas.toDataURL('image/png').split(',')[1];
            }};
        }})()
    """)
    time.sleep(1.5)
    crop_b64 = eval_js("window.cardCropData")
    if crop_b64:
        with open('scratch/ref_streak_card_crop.png', 'wb') as f:
            f.write(base64.b64decode(crop_b64))
        print("Saved crop to scratch/ref_streak_card_crop.png")

finally:
    proc.terminate()
