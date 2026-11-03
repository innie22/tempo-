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

user_data_dir = tempfile.mkdtemp(prefix='tempo_h1_opt_')
port = 9622
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

    # Option 1: 1-line headline, perfectly vertically centered in card
    # Headline is centered vertically in the card: top = 50%, -translate-y-1/2 or margin
    send('Runtime.evaluate', {
        'expression': '''
        (() => {
            const card = document.querySelector('[data-tempo-ui="entry-welcome-card"]');
            card.className = "bg-[#FEFAF4] border border-[#EAE4DF] rounded-3xl sm:rounded-[32px] p-6 sm:p-7 sm:pb-7 shadow-[0_4px_20px_rgba(74,69,65,0.06)] flex flex-col justify-between flex-none lg:h-[307.22px] min-h-[190px] sm:min-h-[205px] relative";
            card.innerHTML = `
                <div>
                    <span class="text-sm sm:text-base font-bold text-[#DE8662] block tracking-wide">
                        Welcome to Tempo
                    </span>
                </div>

                <div class="my-auto py-1">
                    <h1 class="text-[35px] sm:text-[41px] lg:text-[47px] font-bold text-[#4A4541] tracking-[-0.035em] leading-[1.15] whitespace-nowrap">
                        What do you need right now?
                    </h1>
                </div>

                <div class="pt-1">
                    <button type="button"
                            id="btn-hero-figure-start"
                            onclick="if (window.TempoApp && typeof window.TempoApp.openRoutingModal === 'function') { window.TempoApp.openRoutingModal(); } else if (window.TempoMode && typeof window.TempoMode.openHelpSelectionModal === 'function') { window.TempoMode.openHelpSelectionModal(); } else { const m = document.getElementById('modal-routing-selection'); if (m) { m.classList.remove('hidden'); document.body.classList.add('overflow-hidden'); } }"
                            class="px-6 py-3 rounded-2xl bg-[#D28C74] hover:bg-[#C27C64] text-white font-bold text-sm sm:text-base shadow-xs transition inline-flex items-center space-x-2 cursor-pointer group">
                        <span>Help me figure out where to start</span>
                        <span class="group-hover:translate-x-1 transition-transform">→</span>
                    </button>
                </div>
            `;
        })()
        '''
    })
    time.sleep(0.3)
    shot1 = send('Page.captureScreenshot', {
        'format': 'png',
        'clip': {'x': 40, 'y': 80, 'width': 1200, 'height': 580, 'scale': 1}
    })
    with open(os.path.join(artifact_dir, 'headline_opt1_oneline.png'), 'wb') as f:
        f.write(base64.b64decode(shot1['data']))
    print('Saved option 1 (1 line)')

    # Check option 1 vertical centering
    eval_opt1 = send('Runtime.evaluate', {
        'expression': '''
        (() => {
            const card = document.querySelector('[data-tempo-ui="entry-welcome-card"]');
            const h1 = card.querySelector('h1');
            const cardRect = card.getBoundingClientRect();
            const h1Rect = h1.getBoundingClientRect();
            return {
                cardHeight: cardRect.height,
                cardCenterY: cardRect.top + cardRect.height / 2,
                h1CenterY: h1Rect.top + h1Rect.height / 2,
                diff: (h1Rect.top + h1Rect.height / 2) - (cardRect.top + cardRect.height / 2),
                h1Width: h1Rect.width,
                cardWidth: cardRect.width
            };
        })()
        ''',
        'returnByValue': True
    })
    print('Opt 1 centering:', eval_opt1.get('result', {}).get('value', {}))

    # Option 2: 2-line headline, vertically centered
    send('Runtime.evaluate', {
        'expression': '''
        (() => {
            const h1 = document.querySelector('[data-tempo-ui="entry-welcome-card"] h1');
            h1.className = "text-[35px] sm:text-[41px] lg:text-[47px] font-bold text-[#4A4541] tracking-tight leading-[1.12]";
        })()
        '''
    })
    time.sleep(0.3)
    shot2 = send('Page.captureScreenshot', {
        'format': 'png',
        'clip': {'x': 40, 'y': 80, 'width': 1200, 'height': 580, 'scale': 1}
    })
    with open(os.path.join(artifact_dir, 'headline_opt2_twolines.png'), 'wb') as f:
        f.write(base64.b64decode(shot2['data']))
    print('Saved option 2 (2 lines)')

    eval_opt2 = send('Runtime.evaluate', {
        'expression': '''
        (() => {
            const card = document.querySelector('[data-tempo-ui="entry-welcome-card"]');
            const h1 = card.querySelector('h1');
            const cardRect = card.getBoundingClientRect();
            const h1Rect = h1.getBoundingClientRect();
            return {
                cardHeight: cardRect.height,
                cardCenterY: cardRect.top + cardRect.height / 2,
                h1CenterY: h1Rect.top + h1Rect.height / 2,
                diff: (h1Rect.top + h1Rect.height / 2) - (cardRect.top + cardRect.height / 2),
                h1Width: h1Rect.width,
                h1Height: h1Rect.height
            };
        })()
        ''',
        'returnByValue': True
    })
    print('Opt 2 centering:', eval_opt2.get('result', {}).get('value', {}))

    ws.close()
finally:
    proc.terminate()
