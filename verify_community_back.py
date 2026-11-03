import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import base64
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_comm_nav_')
port = 9461
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
    if not pages:
        raise Exception("No active page found")
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
                if 'error' in resp:
                    raise Exception(f"CDP Error in {method}: {resp['error']}")
                return resp.get('result', {})

    def evaluate(expr):
        res = send_cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
        if 'exceptionDetails' in res:
            raise Exception(f"JS Exception: {res['exceptionDetails']}")
        return res.get('result', {}).get('value')

    def capture_screenshot(path):
        res = send_cmd('Page.captureScreenshot', {'format': 'png'})
        img_data = base64.b64decode(res['data'])
        with open(path, 'wb') as f:
            f.write(img_data)
        print(f"Screenshot saved to: {path}")

    # Set viewport
    send_cmd('Emulation.setDeviceMetricsOverride', {
        'width': 1280,
        'height': 900,
        'deviceScaleFactor': 1,
        'mobile': False
    })

    print("Step 1: Checking initial page load...")
    time.sleep(1)

    # 1. Test VI community back button
    evaluate("window.TempoI18n.setLanguage('vi'); window.TempoApp.navigateTo('community');")
    time.sleep(0.5)

    vi_label = evaluate("document.getElementById('community-back-label').textContent.trim()")
    vi_btn_text = evaluate("document.getElementById('btn-community-back').textContent.replace(/\\s+/g, ' ').trim()")
    vi_btn_title = evaluate("document.getElementById('btn-community-back').getAttribute('title')")
    vi_btn_aria = evaluate("document.getElementById('btn-community-back').getAttribute('aria-label')")

    print(f"[VI] community-back-label: '{vi_label}'")
    print(f"[VI] btn-community-back normalized text: '{vi_btn_text}'")
    print(f"[VI] btn-community-back title: '{vi_btn_title}'")
    print(f"[VI] btn-community-back aria-label: '{vi_btn_aria}'")

    assert vi_label == 'Về Dashboard', f"Expected 'Về Dashboard', got '{vi_label}'"
    assert vi_btn_text == '← Về Dashboard', f"Expected '← Về Dashboard', got '{vi_btn_text}'"
    assert vi_btn_title == '← Về Dashboard', f"Expected '← Về Dashboard', got '{vi_btn_title}'"
    assert vi_btn_aria == '← Về Dashboard', f"Expected '← Về Dashboard', got '{vi_btn_aria}'"

    # Check tabs in VI
    for tab in ['announcement', 'tips', 'learn', 'posts', 'messages']:
        evaluate(f"window.TempoCommunity.selectTab('{tab}')")
        time.sleep(0.2)
        lbl = evaluate("document.getElementById('community-back-label').textContent.trim()")
        assert lbl == 'Về Dashboard', f"Tab {tab} expected 'Về Dashboard', got '{lbl}'"
    print("All tabs in VI preserve 'Về Dashboard'.")

    artifacts_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
    capture_screenshot(os.path.join(artifacts_dir, "community_back_vi.png"))

    # 2. Test EN community back button
    evaluate("window.TempoI18n.setLanguage('en');")
    time.sleep(0.5)

    en_label = evaluate("document.getElementById('community-back-label').textContent.trim()")
    en_btn_text = evaluate("document.getElementById('btn-community-back').textContent.replace(/\\s+/g, ' ').trim()")
    en_btn_title = evaluate("document.getElementById('btn-community-back').getAttribute('title')")
    en_btn_aria = evaluate("document.getElementById('btn-community-back').getAttribute('aria-label')")

    print(f"[EN] community-back-label: '{en_label}'")
    print(f"[EN] btn-community-back normalized text: '{en_btn_text}'")
    print(f"[EN] btn-community-back title: '{en_btn_title}'")
    print(f"[EN] btn-community-back aria-label: '{en_btn_aria}'")

    assert en_label == 'Return to Dashboard', f"Expected 'Return to Dashboard', got '{en_label}'"
    assert en_btn_text == '← Return to Dashboard', f"Expected '← Return to Dashboard', got '{en_btn_text}'"
    assert en_btn_title == '← Return to Dashboard', f"Expected '← Return to Dashboard', got '{en_btn_title}'"
    assert en_btn_aria == '← Return to Dashboard', f"Expected '← Return to Dashboard', got '{en_btn_aria}'"

    # Check tabs in EN
    for tab in ['announcement', 'tips', 'learn', 'posts', 'messages']:
        evaluate(f"window.TempoCommunity.selectTab('{tab}')")
        time.sleep(0.2)
        lbl = evaluate("document.getElementById('community-back-label').textContent.trim()")
        assert lbl == 'Return to Dashboard', f"Tab {tab} expected 'Return to Dashboard', got '{lbl}'"
    print("All tabs in EN preserve 'Return to Dashboard'.")

    capture_screenshot(os.path.join(artifacts_dir, "community_back_en.png"))

    # 3. Test clicking back button navigates to Dashboard
    print("Step 3: Clicking back button from Community...")
    evaluate("document.getElementById('btn-community-back').click()")
    time.sleep(0.5)

    current_hash = evaluate("window.location.hash")
    today_hidden = evaluate("document.getElementById('screen-today').classList.contains('hidden')")
    comm_hidden = evaluate("document.getElementById('screen-community').classList.contains('hidden')")
    emergency_hidden = evaluate("document.getElementById('screen-emergency').classList.contains('hidden')")

    print(f"Hash after click: {current_hash}")
    print(f"screen-today hidden: {today_hidden}")
    print(f"screen-community hidden: {comm_hidden}")
    print(f"screen-emergency hidden: {emergency_hidden}")

    assert today_hidden is False, "screen-today should be visible!"
    assert comm_hidden is True, "screen-community should be hidden!"
    assert emergency_hidden is True, "screen-emergency should be hidden!"
    assert current_hash == '#today', f"Expected hash '#today', got '{current_hash}'"

    capture_screenshot(os.path.join(artifacts_dir, "community_navigated_dashboard.png"))

    # 4. Test entering Community from Emergency Mode / Support
    print("Step 4: Testing Community navigation from Emergency Support / Mode...")
    evaluate("window.TempoMode.setMode('emergency'); window.TempoApp.navigateTo('emergency');")
    time.sleep(0.5)
    em_check = evaluate("document.getElementById('screen-emergency').classList.contains('hidden')")
    print(f"In Emergency flow: screen-emergency hidden={em_check}")

    # Now navigate to Community
    evaluate("window.TempoApp.navigateTo('community');")
    time.sleep(0.5)

    label_from_em = evaluate("document.getElementById('community-back-label').textContent.trim()")
    btn_from_em = evaluate("document.getElementById('btn-community-back').textContent.replace(/\\s+/g, ' ').trim()")
    print(f"Label when entered from Emergency: '{label_from_em}', full: '{btn_from_em}'")
    assert label_from_em in ['Return to Dashboard', 'Về Dashboard']
    assert 'Emergency' not in label_from_em and 'Emergency' not in btn_from_em
    assert 'Urgent' not in label_from_em and 'Urgent' not in btn_from_em

    # Click back button
    evaluate("document.getElementById('btn-community-back').click()")
    time.sleep(0.5)

    em_after = evaluate("document.getElementById('screen-emergency').classList.contains('hidden')")
    today_after = evaluate("document.getElementById('screen-today').classList.contains('hidden')")
    comm_after = evaluate("document.getElementById('screen-community').classList.contains('hidden')")
    hash_after = evaluate("window.location.hash")

    print(f"After return: hash={hash_after}, screen-today hidden={today_after}, screen-emergency hidden={em_after}, screen-community hidden={comm_after}")
    assert today_after is False, "Should be on screen-today (Dashboard)!"
    assert em_after is True, "Must NOT navigate to screen-emergency!"
    assert comm_after is True, "screen-community should be hidden!"
    assert hash_after == '#today', f"Expected hash '#today', got '{hash_after}'"

    # 5. Test entering Community from Recovery Mode
    print("Step 5: Testing Community navigation from Recovery Mode...")
    evaluate("window.TempoMode.setMode('recovery'); window.TempoApp.navigateTo('community');")
    time.sleep(0.5)

    label_from_rec = evaluate("document.getElementById('community-back-label').textContent.trim()")
    assert 'Recovery' not in label_from_rec

    evaluate("document.getElementById('btn-community-back').click()")
    time.sleep(0.5)
    today_rec = evaluate("document.getElementById('screen-today').classList.contains('hidden')")
    assert today_rec is False, "Should be on screen-today (Dashboard)!"

    # 6. Test switching language dynamically while in Community
    print("Step 6: Testing dynamic language switching while remaining in Community...")
    evaluate("window.TempoApp.navigateTo('community');")
    time.sleep(0.3)
    evaluate("window.TempoI18n.setLanguage('vi');")
    time.sleep(0.3)
    lbl_vi = evaluate("document.getElementById('community-back-label').textContent.trim()")
    btn_vi = evaluate("document.getElementById('btn-community-back').textContent.replace(/\\s+/g, ' ').trim()")
    assert lbl_vi == 'Về Dashboard'
    assert btn_vi == '← Về Dashboard'

    evaluate("window.TempoI18n.setLanguage('en');")
    time.sleep(0.3)
    lbl_en = evaluate("document.getElementById('community-back-label').textContent.trim()")
    btn_en = evaluate("document.getElementById('btn-community-back').textContent.replace(/\\s+/g, ' ').trim()")
    assert lbl_en == 'Return to Dashboard'
    assert btn_en == '← Return to Dashboard'

    print("ALL TESTS PASSED WITH 100% SUCCESS!")

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        proc.kill()
