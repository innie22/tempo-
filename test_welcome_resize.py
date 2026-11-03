# -*- coding: utf-8 -*-
import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_welcome_test_')
port = 9555
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

    test_res = send('Runtime.evaluate', {
        'expression': '''
        (() => {
            const card = document.querySelector('[data-tempo-ui="entry-welcome-card"]');
            if (!card) return { error: 'No card found' };

            const baselineRect = card.getBoundingClientRect();
            const baselineHeight = baselineRect.height;
            const targetHeight = baselineHeight - 20;

            // Apply updates
            card.style.backgroundColor = '#FEFAF4';
            card.style.boxShadow = '0 4px 20px rgba(74, 69, 65, 0.06)';
            card.style.height = targetHeight + 'px';
            card.style.flex = 'none';

            // Check inner spacing
            card.style.padding = '28px 32px 32px 32px';

            const newRect = card.getBoundingClientRect();
            const cs = window.getComputedStyle(card);
            const overflow = card.scrollHeight > card.clientHeight;

            return {
                baselineHeight,
                targetHeight,
                renderedHeight: newRect.height,
                renderedWidth: newRect.width,
                originalWidth: baselineRect.width,
                widthDelta: newRect.width - baselineRect.width,
                heightDelta: newRect.height - baselineHeight,
                topPosition: newRect.top,
                originalTop: baselineRect.top,
                leftPosition: newRect.left,
                originalLeft: baselineRect.left,
                cardBg: cs.backgroundColor,
                cardShadow: cs.boxShadow,
                cardBorder: cs.borderColor,
                cardRadius: cs.borderRadius,
                overflow: overflow,
                scrollHeight: card.scrollHeight,
                clientHeight: card.clientHeight
            };
        })()
        ''',
        'returnByValue': True
    })

    print(json.dumps(test_res.get('result', {}).get('value', {}), indent=2))
    ws.close()
finally:
    proc.terminate()
