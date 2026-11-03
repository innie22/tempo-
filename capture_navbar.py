# -*- coding: utf-8 -*-
import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import base64
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_logo_cap_')
port = 9488
proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={port}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    'http://localhost:8000'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    time.sleep(2)
    tabs = json.loads(urllib.request.urlopen(f'http://localhost:{port}/json').read().decode())
    ws_url = tabs[0]['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)

    def send(method, params=None):
        mid = int(time.time() * 1000) % 1000000
        ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
        while True:
            res = json.loads(ws.recv())
            if res.get('id') == mid:
                return res.get('result', {})

    send('Page.enable')
    send('DOM.enable')
    send('Page.navigate', {'url': 'http://localhost:8000'})
    time.sleep(2)

    artifact_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'

    # 1. Desktop screenshot (top 200px)
    send('Emulation.setDeviceMetricsOverride', {
        'width': 1280,
        'height': 900,
        'deviceScaleFactor': 1,
        'mobile': False
    })
    time.sleep(0.5)
    shot = send('Page.captureScreenshot', {
        'format': 'png',
        'clip': {'x': 0, 'y': 0, 'width': 1280, 'height': 220, 'scale': 1}
    })
    with open(os.path.join(artifact_dir, 'navbar_desktop_logo_10px.png'), 'wb') as f:
        f.write(base64.b64decode(shot['data']))
    print('Saved navbar_desktop_logo_10px.png')

    # 2. Mobile screenshot
    send('Emulation.setDeviceMetricsOverride', {
        'width': 375,
        'height': 812,
        'deviceScaleFactor': 1,
        'mobile': True
    })
    time.sleep(0.5)
    shot = send('Page.captureScreenshot', {
        'format': 'png',
        'clip': {'x': 0, 'y': 0, 'width': 375, 'height': 150, 'scale': 1}
    })
    with open(os.path.join(artifact_dir, 'navbar_mobile_logo_10px.png'), 'wb') as f:
        f.write(base64.b64decode(shot['data']))
    print('Saved navbar_mobile_logo_10px.png')

    ws.close()
finally:
    proc.terminate()
