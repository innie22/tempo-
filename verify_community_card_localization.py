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

user_data_dir = tempfile.mkdtemp(prefix='tempo_comm_card_')
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

artifacts_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"

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

    print("=== Step 1: Default / Entry Home Dashboard ===")
    time.sleep(1)

    # 1.1 VI in default mode
    evaluate("window.TempoI18n.setLanguage('vi'); window.TempoApp.navigateTo('today');")
    time.sleep(0.5)

    vi_h3 = evaluate("document.getElementById('btn-see-all-posts')?.parentElement?.querySelector('h3')?.textContent?.trim()")
    vi_btn = evaluate("document.getElementById('btn-see-all-posts')?.textContent?.replace(/\\s+/g, ' ')?.trim()")
    print(f"[Default VI] Heading: '{vi_h3}', Button: '{vi_btn}'")
    assert vi_h3 == 'Cộng đồng Tempo', f"Expected 'Cộng đồng Tempo', got '{vi_h3}'"
    assert vi_btn == 'Xem tất cả →', f"Expected 'Xem tất cả →', got '{vi_btn}'"
    capture_screenshot(os.path.join(artifacts_dir, "community_card_default_vi.png"))

    # 1.2 EN in default mode
    evaluate("window.TempoI18n.setLanguage('en');")
    time.sleep(0.5)

    en_h3 = evaluate("document.getElementById('btn-see-all-posts')?.parentElement?.querySelector('h3')?.textContent?.trim()")
    en_btn = evaluate("document.getElementById('btn-see-all-posts')?.textContent?.replace(/\\s+/g, ' ')?.trim()")
    print(f"[Default EN] Heading: '{en_h3}', Button: '{en_btn}'")
    assert en_h3 == 'From the Tempo Community', f"Expected 'From the Tempo Community', got '{en_h3}'"
    assert en_btn == 'View all →', f"Expected 'View all →', got '{en_btn}'"
    capture_screenshot(os.path.join(artifacts_dir, "community_card_default_en.png"))

    print("\n=== Step 2: Urgent Mode Dashboard ===")
    # 2.1 Urgent Mode EN
    evaluate("window.TempoMode.setMode('emergency');")
    time.sleep(0.5)

    urg_en_h3 = evaluate("document.getElementById('btn-see-all-posts-urgent')?.parentElement?.querySelector('h3')?.textContent?.trim()")
    urg_en_btn = evaluate("document.getElementById('btn-see-all-posts-urgent')?.textContent?.replace(/\\s+/g, ' ')?.trim()")
    print(f"[Urgent EN] Heading: '{urg_en_h3}', Button: '{urg_en_btn}'")
    assert urg_en_h3 == 'From the Tempo Community', f"Expected 'From the Tempo Community', got '{urg_en_h3}'"
    assert urg_en_btn == 'View all →', f"Expected 'View all →', got '{urg_en_btn}'"
    assert 'Xem tất cả' not in urg_en_btn, "No Vietnamese text allowed in English Urgent Mode!"
    capture_screenshot(os.path.join(artifacts_dir, "community_card_urgent_en.png"))

    # 2.2 Urgent Mode VI
    evaluate("window.TempoI18n.setLanguage('vi');")
    time.sleep(0.5)

    urg_vi_h3 = evaluate("document.getElementById('btn-see-all-posts-urgent')?.parentElement?.querySelector('h3')?.textContent?.trim()")
    urg_vi_btn = evaluate("document.getElementById('btn-see-all-posts-urgent')?.textContent?.replace(/\\s+/g, ' ')?.trim()")
    print(f"[Urgent VI] Heading: '{urg_vi_h3}', Button: '{urg_vi_btn}'")
    assert urg_vi_h3 == 'Cộng đồng Tempo', f"Expected 'Cộng đồng Tempo', got '{urg_vi_h3}'"
    assert urg_vi_btn == 'Xem tất cả →', f"Expected 'Xem tất cả →', got '{urg_vi_btn}'"
    capture_screenshot(os.path.join(artifacts_dir, "community_card_urgent_vi.png"))

    print("\n=== Step 3: Recovery Mode Dashboard ===")
    # 3.1 Recovery Mode VI
    evaluate("window.TempoMode.setMode('recovery');")
    time.sleep(0.5)

    rec_vi_h3 = evaluate("document.getElementById('btn-see-all-posts-recovery')?.parentElement?.querySelector('h3')?.textContent?.trim()")
    rec_vi_btn = evaluate("document.getElementById('btn-see-all-posts-recovery')?.textContent?.replace(/\\s+/g, ' ')?.trim()")
    print(f"[Recovery VI] Heading: '{rec_vi_h3}', Button: '{rec_vi_btn}'")
    assert rec_vi_h3 == 'Cộng đồng Tempo', f"Expected 'Cộng đồng Tempo', got '{rec_vi_h3}'"
    assert rec_vi_btn == 'Xem tất cả →', f"Expected 'Xem tất cả →', got '{rec_vi_btn}'"
    capture_screenshot(os.path.join(artifacts_dir, "community_card_recovery_vi.png"))

    # 3.2 Recovery Mode EN
    evaluate("window.TempoI18n.setLanguage('en');")
    time.sleep(0.5)

    rec_en_h3 = evaluate("document.getElementById('btn-see-all-posts-recovery')?.parentElement?.querySelector('h3')?.textContent?.trim()")
    rec_en_btn = evaluate("document.getElementById('btn-see-all-posts-recovery')?.textContent?.replace(/\\s+/g, ' ')?.trim()")
    print(f"[Recovery EN] Heading: '{rec_en_h3}', Button: '{rec_en_btn}'")
    assert rec_en_h3 == 'From the Tempo Community', f"Expected 'From the Tempo Community', got '{rec_en_h3}'"
    assert rec_en_btn == 'View all →', f"Expected 'View all →', got '{rec_en_btn}'"
    capture_screenshot(os.path.join(artifacts_dir, "community_card_recovery_en.png"))

    print("\n=== Step 4: Rapid Switching Verification ===")
    for lang, expected_btn, expected_h3 in [('vi', 'Xem tất cả →', 'Cộng đồng Tempo'), ('en', 'View all →', 'From the Tempo Community'), ('vi', 'Xem tất cả →', 'Cộng đồng Tempo'), ('en', 'View all →', 'From the Tempo Community')]:
        evaluate(f"window.TempoI18n.setLanguage('{lang}');")
        time.sleep(0.2)
        cur_btn = evaluate("document.getElementById('btn-see-all-posts-recovery')?.textContent?.replace(/\\s+/g, ' ')?.trim()")
        cur_h3 = evaluate("document.getElementById('btn-see-all-posts-recovery')?.parentElement?.querySelector('h3')?.textContent?.trim()")
        assert cur_btn == expected_btn, f"Expected '{expected_btn}', got '{cur_btn}'"
        assert cur_h3 == expected_h3, f"Expected '{expected_h3}', got '{cur_h3}'"
    print("Rapid language switching verified smoothly without page refresh!")

    print("\n=== Step 5: Button Click Navigation ===")
    evaluate("document.getElementById('btn-see-all-posts-recovery').click();")
    time.sleep(0.5)
    comm_vis = evaluate("!document.getElementById('screen-community').classList.contains('hidden')")
    today_vis = evaluate("!document.getElementById('screen-today').classList.contains('hidden')")
    comm_hash = evaluate("window.location.hash")
    print(f"After click: Community visible={comm_vis}, Today visible={today_vis}, Hash={comm_hash}")
    assert comm_vis is True, "Should have navigated to Community screen!"
    assert today_vis is False, "Today screen should be hidden!"

    print("\nALL 5 TEST SUITES PASSED WITH 100% SUCCESS!")

finally:
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        proc.kill()
