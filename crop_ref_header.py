# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, tempfile, sys, base64

sys.stdout.reconfigure(encoding='utf-8')
CDP_PORT = 9555
user_data_dir = tempfile.mkdtemp(prefix='edge_crop_')

img_path = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\.user_uploaded\media_1792404879747_aaf7bf5a.png'
with open(img_path, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('ascii')

proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={CDP_PORT}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--window-size=1440,1100',
    'http://127.0.0.1:8000/'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    time.sleep(2.0)
    with urllib.request.urlopen(f'http://127.0.0.1:{CDP_PORT}/json') as resp:
        tabs = json.loads(resp.read().decode())
    pages = [t for t in tabs if t.get('type') == 'page' and '127.0.0.1' in t.get('url', '')]
    ws_url = (pages[0] if pages else tabs[0])['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)

    msg_id = [1]
    def send(method, params=None):
        mid = msg_id[0]
        msg_id[0] += 1
        ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == mid:
                return resp.get('result', {})

    send('Page.enable')

    def eval_js(expr):
        res = send('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
        if 'exceptionDetails' in res.get('result', {}):
            raise Exception('JS Exception: ' + str(res['result']['exceptionDetails']))
        return res.get('result', {}).get('value')

    code = f'''
    new Promise((resolve) => {{
        const img = new Image();
        img.src = 'data:image/png;base64,{b64}';
        img.onload = () => {{
            // Crop x: 50 to 500, y: 50 to 350
            const canvas = document.createElement('canvas');
            canvas.width = 450;
            canvas.height = 300;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 50, 50, 450, 300, 0, 0, 450, 300);
            const dataUrl = canvas.toDataURL('image/png');
            resolve(dataUrl);
        }};
    }})
    '''
    res = eval_js(code)
    # save cropped
    header, b64_data = res.split(',', 1)
    with open(r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\scratch\ref_header_crop.png', 'wb') as f:
        f.write(base64.b64decode(b64_data))
    print('Saved ref_header_crop.png successfully')
finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
