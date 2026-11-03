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

user_data_dir = tempfile.mkdtemp(prefix='tempo_welcome_compare_')
port = 9566
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

    send('Emulation.setDeviceMetricsOverride', {
        'width': 1280,
        'height': 900,
        'deviceScaleFactor': 1,
        'mobile': False
    })
    time.sleep(0.5)

    artifact_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'

    # Option A: card height 327.22px, left col justify-start (natural 24px gap)
    send('Runtime.evaluate', {
        'expression': '''
        (() => {
            const card = document.querySelector('[data-tempo-ui="entry-welcome-card"]');
            const leftCol = card ? card.parentElement : null;
            card.style.backgroundColor = '#FEFAF4';
            card.style.boxShadow = '0 4px 20px rgba(74, 69, 65, 0.06)';
            card.style.height = '327.22px';
            card.style.flex = 'none';
            card.style.padding = '28px 32px 32px 32px';
            if (leftCol) {
                leftCol.classList.remove('justify-between');
                leftCol.classList.add('justify-start');
            }
        })()
        '''
    })
    time.sleep(0.3)
    shotA = send('Page.captureScreenshot', {
        'format': 'png',
        'clip': {'x': 60, 'y': 80, 'width': 1160, 'height': 600, 'scale': 1}
    })
    with open(os.path.join(artifact_dir, 'welcome_compare_optionA.png'), 'wb') as f:
        f.write(base64.b64decode(shotA['data']))
    print('Saved option A')

    # Option B: card height 327.22px, left col justify-between (align bottom with community panel)
    send('Runtime.evaluate', {
        'expression': '''
        (() => {
            const card = document.querySelector('[data-tempo-ui="entry-welcome-card"]');
            const leftCol = card ? card.parentElement : null;
            if (leftCol) {
                leftCol.classList.remove('justify-start');
                leftCol.classList.add('justify-between');
            }
        })()
        '''
    })
    time.sleep(0.3)
    shotB = send('Page.captureScreenshot', {
        'format': 'png',
        'clip': {'x': 60, 'y': 80, 'width': 1160, 'height': 600, 'scale': 1}
    })
    with open(os.path.join(artifact_dir, 'welcome_compare_optionB.png'), 'wb') as f:
        f.write(base64.b64decode(shotB['data']))
    print('Saved option B')

    ws.close()
finally:
    proc.terminate()
