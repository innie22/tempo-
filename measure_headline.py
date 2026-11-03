# -*- coding: utf-8 -*-
import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_headline_measure_')
port = 9588
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
                const card = document.querySelector('[data-tempo-ui="entry-welcome-card"]');
                const label = card ? card.querySelector('span') : null;
                const h1 = card ? card.querySelector('h1') : null;
                const btn = card ? card.querySelector('button') : null;
                if (!card || !h1) return { error: 'Not found' };

                const cardRect = card.getBoundingClientRect();
                const labelRect = label ? label.getBoundingClientRect() : null;
                const h1Rect = h1.getBoundingClientRect();
                const btnRect = btn ? btn.getBoundingClientRect() : null;
                const csH1 = window.getComputedStyle(h1);

                const cardCenterY = cardRect.top + cardRect.height / 2;
                const h1CenterY = h1Rect.top + h1Rect.height / 2;

                return {
                    label: "''' + label + '''",
                    h1Text: h1.innerText.trim(),
                    fontSize: csH1.fontSize,
                    lineHeight: csH1.lineHeight,
                    classes: h1.className,
                    cardHeight: cardRect.height,
                    cardTop: cardRect.top,
                    cardCenterY: cardCenterY,
                    h1Top: h1Rect.top,
                    h1Height: h1Rect.height,
                    h1CenterY: h1CenterY,
                    distanceFromCardCenter: h1CenterY - cardCenterY,
                    labelBottom: labelRect ? labelRect.bottom : null,
                    gapToLabel: labelRect ? (h1Rect.top - labelRect.bottom) : null,
                    btnTop: btnRect ? btnRect.top : null,
                    gapToBtn: btnRect ? (btnRect.top - h1Rect.bottom) : null
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
