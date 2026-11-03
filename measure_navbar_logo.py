# -*- coding: utf-8 -*-
import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_logo_measure_')
port = 9477
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
                const img = document.querySelector('#brand-logo-container img');
                const parent = document.querySelector('#brand-logo-container');
                const header = document.querySelector('header');
                const headerInner = document.querySelector('header > div');
                if (!img) return { error: 'No logo img found' };
                const rect = img.getBoundingClientRect();
                const computed = window.getComputedStyle(img);
                return {
                    label: "''' + label + '''",
                    renderedWidth: rect.width,
                    renderedHeight: rect.height,
                    aspectRatio: rect.width / rect.height,
                    cssHeight: computed.height,
                    cssWidth: computed.width,
                    classes: img.className,
                    parentHeight: parent ? parent.getBoundingClientRect().height : null,
                    headerHeight: header ? header.getBoundingClientRect().height : null,
                    headerInnerHeight: headerInner ? headerInner.getBoundingClientRect().height : null
                };
            })()
            ''',
            'returnByValue': True
        })
        print(f"--- {label} ---")
        print(json.dumps(eval_res.get('result', {}).get('value', {}), indent=2))

    ws.close()
finally:
    proc.terminate()
