# -*- coding: utf-8 -*-
import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_typo_test_')
port = 9655
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

    # Test fine-tuning the classes on card
    send('Runtime.evaluate', {
        'expression': '''
        (() => {
            const card = document.querySelector('[data-tempo-ui="entry-welcome-card"]');
            if (!card) return;

            // Welcome label div: on desktop translate down 10px
            const labelDiv = card.children[0];
            labelDiv.className = "lg:translate-y-[10px]";

            const labelSpan = labelDiv.querySelector('span');
            labelSpan.className = "text-[24px] sm:text-[26px] font-bold text-[#D99E87] block tracking-wide";

            // Headline div: move up 5px on desktop (baseline was 229.19px, target 224.19px)
            const h1Div = card.children[1];
            h1Div.className = "my-auto lg:translate-y-[3.5px] py-1";

            const h1 = h1Div.querySelector('h1');
            h1.className = "text-[35px] sm:text-[41px] lg:text-[47px] font-bold text-[#726D69] tracking-[-0.035em] leading-[1.15] lg:whitespace-nowrap";
        })()
        '''
    })
    time.sleep(0.3)

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
                if (!card || !label || !h1) return { error: 'Not found' };

                const labelRect = label.getBoundingClientRect();
                const h1Rect = h1.getBoundingClientRect();
                const csLabel = window.getComputedStyle(label);
                const csH1 = window.getComputedStyle(h1);

                return {
                    label: "''' + label + '''",
                    welcome: {
                        fontSize: csLabel.fontSize,
                        color: csLabel.color,
                        top: labelRect.top,
                        bottom: labelRect.bottom,
                        height: labelRect.height
                    },
                    headline: {
                        fontSize: csH1.fontSize,
                        color: csH1.color,
                        top: h1Rect.top,
                        bottom: h1Rect.bottom,
                        height: h1Rect.height
                    },
                    gapToHeadline: h1Rect.top - labelRect.bottom,
                    gapToBtn: btn ? (btn.getBoundingClientRect().top - h1Rect.bottom) : null,
                    overflow: card.scrollHeight > card.clientHeight
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
