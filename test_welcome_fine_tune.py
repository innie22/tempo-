# -*- coding: utf-8 -*-
import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_welcome_tune_')
port = 9666
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

    # Measure baseline
    baseline = send('Runtime.evaluate', {
        'expression': '''
        (() => {
            const card = document.querySelector('[data-tempo-ui="entry-welcome-card"]');
            const label = card.querySelector('span');
            const h1 = card.querySelector('h1');
            return {
                cardHeight: card.getBoundingClientRect().height,
                labelFontSize: window.getComputedStyle(label).fontSize,
                labelTop: label.getBoundingClientRect().top,
                h1FontSize: window.getComputedStyle(h1).fontSize,
                h1Top: h1.getBoundingClientRect().top
            };
        })()
        ''',
        'returnByValue': True
    }).get('result', {}).get('value', {})

    # Apply adjustments:
    # 1. card height -10px: 297.22px
    # 2. label font size -5px: 21px
    # 3. headline font size -5px: 42px
    send('Runtime.evaluate', {
        'expression': '''
        (() => {
            const card = document.querySelector('[data-tempo-ui="entry-welcome-card"]');
            card.style.height = '297.22px';

            const label = card.querySelector('span');
            label.style.fontSize = '21px';

            const h1 = card.querySelector('h1');
            h1.style.fontSize = '42px';
        })()
        '''
    })
    time.sleep(0.3)

    updated = send('Runtime.evaluate', {
        'expression': '''
        (() => {
            const card = document.querySelector('[data-tempo-ui="entry-welcome-card"]');
            const label = card.querySelector('span');
            const h1 = card.querySelector('h1');
            const btn = card.querySelector('button');
            const cardRect = card.getBoundingClientRect();
            const labelRect = label.getBoundingClientRect();
            const h1Rect = h1.getBoundingClientRect();
            const btnRect = btn.getBoundingClientRect();
            return {
                cardHeight: cardRect.height,
                cardWidth: cardRect.width,
                labelFontSize: window.getComputedStyle(label).fontSize,
                labelTop: labelRect.top,
                h1FontSize: window.getComputedStyle(h1).fontSize,
                h1Top: h1Rect.top,
                h1Bottom: h1Rect.bottom,
                gapToLabel: h1Rect.top - labelRect.bottom,
                gapToBtn: btnRect.top - h1Rect.bottom,
                overflow: card.scrollHeight > card.clientHeight,
                cardScrollHeight: card.scrollHeight,
                cardClientHeight: card.clientHeight
            };
        })()
        ''',
        'returnByValue': True
    }).get('result', {}).get('value', {})

    print("Baseline:", json.dumps(baseline, indent=2))
    print("Updated:", json.dumps(updated, indent=2))

    ws.close()
finally:
    proc.terminate()
