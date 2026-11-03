# -*- coding: utf-8 -*-
import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_comm_measure_')
port = 9499
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
                const entryHome = document.querySelector('[data-tempo-ui="entry-home"]');
                const upperRow = entryHome ? entryHome.children[0] : null;
                const leftCol = upperRow ? upperRow.children[0] : null;
                const welcome = document.querySelector('[data-tempo-ui="entry-welcome-card"]');
                const actions = document.querySelector('[data-tempo-ui="entry-action-cards"]');
                const posts = document.querySelectorAll('#homepage-community-posts-list > div');
                if (!panel) return { error: 'No panel found' };
                const rect = panel.getBoundingClientRect();
                const colRect = col ? col.getBoundingClientRect() : null;
                const postRects = Array.from(posts).map((p, i) => {
                    const r = p.getBoundingClientRect();
                    const cs = window.getComputedStyle(p);
                    return {
                        index: i,
                        width: r.width,
                        height: r.height,
                        bg: cs.backgroundColor,
                        border: cs.borderColor
                    };
                });
                const panelStyle = window.getComputedStyle(panel);
                return {
                    label: "''' + label + '''",
                    panelWidth: rect.width,
                    panelHeight: rect.height,
                    panelScrollHeight: panel.scrollHeight,
                    aspectRatio: rect.width / rect.height,
                    widthToHeightRatio: rect.width / rect.height,
                    panelBg: panelStyle.backgroundColor,
                    panelBorder: panelStyle.borderColor,
                    colWidth: colRect ? colRect.width : null,
                    colHeight: colRect ? colRect.height : null,
                    leftColHeight: leftCol ? leftCol.getBoundingClientRect().height : null,
                    welcomeHeight: welcome ? welcome.getBoundingClientRect().height : null,
                    actionsHeight: actions ? actions.getBoundingClientRect().height : null,
                    postCards: postRects
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
