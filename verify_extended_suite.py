import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import sys
import base64
import os

user_data_dir = tempfile.mkdtemp(prefix='tempo_ext_test_')
port = 9445
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
time.sleep(2)

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
        if "exceptionDetails" in res:
            print("JS Exception:", res["exceptionDetails"])
        return res.get('result', {}).get('value')

    send_cmd('Page.enable')

    for _ in range(30):
        if eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoCommunity !== 'undefined'"):
            break
        time.sleep(0.5)

    print("=== EXTENDED TEST SUITE: MOBILE & UNRELATED MODES ===")

    # Test 11: Mobile responsive layout & DM flow
    print("\n[Test 11] Mobile responsiveness (viewport resize & mobile DM toggle):")
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 375,
        "height": 667,
        "deviceScaleFactor": 2,
        "mobile": True
    })
    time.sleep(0.5)
    eval_js("window.TempoApp.navigateTo('community', 'messages');")
    eval_js("""
        (() => {
            if (window.TempoAuth) {
                window.TempoAuth.getCurrentUser = () => ({ id: 'u1', email: 'mobile@tempo.edu' });
            }
            window.TempoCommunity.renderMessagesView();
        })()
    """)
    time.sleep(0.5)

    mobile_test = eval_js("""
        (() => {
            const listCol = document.getElementById('dm-conversations-column');
            const chatCol = document.getElementById('dm-chat-column');
            const mobileTabs = document.querySelector('.community-mobile-tab-btn');
            
            // Toggle to conversation detail
            window.TempoCommunity.mobileToggleConversation(true);
            const chatVisible = !chatCol.classList.contains('hidden');
            const listHidden = listCol.classList.contains('hidden');

            // Toggle back to list
            window.TempoCommunity.mobileToggleConversation(false);
            const listVisibleAfter = !listCol.classList.contains('hidden');
            const chatHiddenAfter = chatCol.classList.contains('hidden');

            return {
                hasMobileTabs: !!mobileTabs,
                chatVisible,
                listHidden,
                listVisibleAfter,
                chatHiddenAfter
            };
        })()
    """)
    print("Mobile tabs rendered:", mobile_test['hasMobileTabs'])
    print("Mobile chat detail view opens:", mobile_test['chatVisible'] and mobile_test['listHidden'])
    print("Mobile back returns to conversation list:", mobile_test['listVisibleAfter'] and mobile_test['chatHiddenAfter'])
    t11_pass = mobile_test['hasMobileTabs'] and mobile_test['chatVisible'] and mobile_test['listVisibleAfter']

    # Reset viewport
    send_cmd("Emulation.clearDeviceMetricsOverride")

    # Test 12: Unrelated Tempo tools and modes preservation
    print("\n[Test 12] Unrelated Tempo Modes & Features:")
    unrelated_test = eval_js("""
        (() => {
            const results = {};
            // About
            window.TempoApp.navigateTo('about');
            results.about = !document.getElementById('screen-about')?.classList.contains('hidden');

            // UCheck Assessments
            window.TempoApp.navigateTo('explore-mental-health-tests');
            results.ucheck = !document.getElementById('screen-explore-mental-health-tests')?.classList.contains('hidden');

            // Plan Workspace (authenticate user)
            if (window.TempoAuth) {
                window.TempoAuth.getCurrentUser = () => ({ id: 'u1', email: 'test@tempo.edu' });
                window.TempoAuth.getAuthState = () => 'authenticated';
            }
            window.TempoApp.navigateTo('plan-workspace');
            results.plan = !document.getElementById('screen-plan-workspace')?.classList.contains('hidden');

            // Check / Self-Check (authenticated)
            window.TempoApp.navigateTo('stress-check');
            results.check = !document.getElementById('screen-stress-check')?.classList.contains('hidden');

            // Return to Today
            window.TempoApp.navigateTo('today');
            results.today = !document.getElementById('screen-today')?.classList.contains('hidden');

            return results;
        })()
    """)
    print("Unrelated modes test results:", unrelated_test)
    t12_pass = all(unrelated_test.values())

    print("\nSUMMARY:")
    print("  Test 11 (Mobile responsive & DM flow):", "PASS" if t11_pass else "FAIL")
    print("  Test 12 (Unrelated Tempo modes preserved):", "PASS" if t12_pass else "FAIL")

finally:
    proc.terminate()
