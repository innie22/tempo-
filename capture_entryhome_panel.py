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

user_data_dir = tempfile.mkdtemp(prefix='tempo_panel_cap_')
port = 9533
proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={port}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    'http://localhost:8000'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    time.sleep(2.5)
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        tabs = json.loads(resp.read().decode())
        pages = [t for t in tabs if t.get('type') == 'page' and 'localhost' in t.get('url', '')]
    ws_url = pages[0]['webSocketDebuggerUrl']
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

    for _ in range(30):
        res = send('Runtime.evaluate', {
            'expression': "typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'",
            'returnByValue': True
        })
        if res.get('result', {}).get('value'):
            break
        time.sleep(0.5)

    send('Runtime.evaluate', {
        'expression': """
            if (window.TempoAuth && typeof window.TempoAuth.setAuthLanguage === 'function') {
                window.TempoAuth.setAuthLanguage('en');
            }
            window.TempoMode.setMode('default');
            window.TempoApp.navigateTo('today');
        """
    })
    time.sleep(0.5)

    artifact_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'

    # 1. Desktop full viewport
    send('Emulation.setDeviceMetricsOverride', {
        'width': 1280,
        'height': 900,
        'deviceScaleFactor': 1,
        'mobile': False
    })
    time.sleep(0.5)
    shot = send('Page.captureScreenshot', {'format': 'png'})
    with open(os.path.join(artifact_dir, 'entryhome_panel_resized_desktop_1280.png'), 'wb') as f:
        f.write(base64.b64decode(shot['data']))
    print('Saved entryhome_panel_resized_desktop_1280.png')

    # 2. Desktop closeup of Community panel
    shot_clip = send('Page.captureScreenshot', {
        'format': 'png',
        'clip': {'x': 60, 'y': 80, 'width': 1160, 'height': 600, 'scale': 1}
    })
    with open(os.path.join(artifact_dir, 'entryhome_panel_resized_closeup.png'), 'wb') as f:
        f.write(base64.b64decode(shot_clip['data']))
    print('Saved entryhome_panel_resized_closeup.png')

    # 3. Tablet
    send('Emulation.setDeviceMetricsOverride', {
        'width': 768,
        'height': 1024,
        'deviceScaleFactor': 1,
        'mobile': False
    })
    time.sleep(0.5)
    shot = send('Page.captureScreenshot', {'format': 'png'})
    with open(os.path.join(artifact_dir, 'entryhome_panel_resized_tablet_768.png'), 'wb') as f:
        f.write(base64.b64decode(shot['data']))
    print('Saved entryhome_panel_resized_tablet_768.png')

    # 4. Mobile
    send('Emulation.setDeviceMetricsOverride', {
        'width': 375,
        'height': 812,
        'deviceScaleFactor': 1,
        'mobile': True
    })
    time.sleep(0.5)
    shot = send('Page.captureScreenshot', {'format': 'png'})
    with open(os.path.join(artifact_dir, 'entryhome_panel_resized_mobile_375.png'), 'wb') as f:
        f.write(base64.b64decode(shot['data']))
    print('Saved entryhome_panel_resized_mobile_375.png')

    ws.close()
finally:
    proc.terminate()
