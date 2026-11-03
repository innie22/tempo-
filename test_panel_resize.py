# -*- coding: utf-8 -*-
import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_comm_test_')
port = 9522
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

    for width, label in [(1280, 'Desktop (1280px)'), (768, 'Tablet (768px)'), (375, 'Mobile (375px)')]:
        send('Emulation.setDeviceMetricsOverride', {
            'width': width,
            'height': 900,
            'deviceScaleFactor': 1,
            'mobile': width < 768
        })
        time.sleep(0.5)

        eval_res = send('Runtime.evaluate', {
            'expression': '''
            (() => {
                const panel = document.querySelector('[data-tempo-ui="entry-community-panel"]');
                const col = panel ? panel.parentElement : null;
                const posts = document.querySelectorAll('#homepage-community-posts-list > div');
                if (!panel) return { error: 'No panel' };

                const baselineRect = panel.getBoundingClientRect();
                const baselineWidth = baselineRect.width;
                const baselineHeight = baselineRect.height;

                return {
                    label: "''' + label + '''",
                    baselineWidth,
                    baselineHeight,
                    ratio: baselineWidth / baselineHeight
                };
            })()
            ''',
            'returnByValue': True
        })
        print(f"=== {label} ===")
        print(json.dumps(eval_res.get('result', {}).get('value', {}), indent=2))

    ws.close()
finally:
    proc.terminate()
