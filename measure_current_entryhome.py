# -*- coding: utf-8 -*-
import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_measure_')
port = 9470
proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={port}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--disable-gpu',
    '--no-first-run',
    'http://localhost:8000/'
])
time.sleep(2.5)

try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        tabs = json.loads(resp.read().decode())
        pages = [t for t in tabs if t.get('type') == 'page' and 'localhost' in t.get('url', '')]
    ws_url = pages[0]['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)

    msg_id = 1
    def send_cmd(method, params=None):
        global msg_id
        cmd = {'id': msg_id, 'method': method, 'params': params or {}}
        msg_id += 1
        ws.send(json.dumps(cmd))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == cmd['id']:
                return resp.get('result', {})

    def eval_js(expr):
        res = send_cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
        return res.get('result', {}).get('value')

    send_cmd('Page.enable')
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 1280,
        "height": 900,
        "deviceScaleFactor": 1,
        "mobile": False
    })

    for _ in range(30):
        if eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'"):
            break
        time.sleep(0.5)

    eval_js("""
        if (window.TempoAuth && typeof window.TempoAuth.setAuthLanguage === 'function') {
            window.TempoAuth.setAuthLanguage('en');
        }
        window.TempoMode.setMode('default');
        window.TempoApp.navigateTo('today');
    """)
    time.sleep(0.5)

    measurements = eval_js("""
        (() => {
            const logo = document.querySelector('#brand-logo-container img');
            const welcome = document.querySelector('[data-tempo-ui="entry-welcome-card"]');
            const actionCards = document.querySelector('[data-tempo-ui="entry-action-cards"]');
            const qrCard = actionCards?.children[0];
            const fnCard = actionCards?.children[1];
            const commPanel = document.querySelector('[data-tempo-ui="entry-community-panel"]');
            const commCards = document.querySelectorAll('#homepage-community-posts-list > div');

            return {
                logo: logo ? { width: logo.offsetWidth, height: logo.offsetHeight, className: logo.className } : null,
                welcome: welcome ? { width: welcome.offsetWidth, height: welcome.offsetHeight, className: welcome.className } : null,
                quickRelief: qrCard ? { width: qrCard.offsetWidth, height: qrCard.offsetHeight, className: qrCard.className } : null,
                focusNow: fnCard ? { width: fnCard.offsetWidth, height: fnCard.offsetHeight, className: fnCard.className } : null,
                communityPanel: commPanel ? { width: commPanel.offsetWidth, height: commPanel.offsetHeight } : null,
                communityCardsCount: commCards.length,
                commCard1: commCards[0] ? { height: commCards[0].offsetHeight, border: window.getComputedStyle(commCards[0]).borderColor } : null
            };
        })()
    """)

    print("CURRENT BASELINE MEASUREMENTS:")
    print(json.dumps(measurements, indent=2))

finally:
    ws.close()
    proc.terminate()
    proc.wait()
