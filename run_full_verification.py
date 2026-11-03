import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os
import base64

sys.stdout.reconfigure(encoding='utf-8')

artifact_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
os.makedirs(artifact_dir, exist_ok=True)

user_data_dir = tempfile.mkdtemp(prefix="tempo_final_verify_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9888

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,900",
    "http://127.0.0.1:8000/#today"
]

proc = subprocess.Popen(cmd)
ws = None
msg_id = 1

def send_cmd(method, params=None):
    global msg_id, ws
    cmd_obj = {"id": msg_id, "method": method, "params": params or {}}
    msg_id += 1
    ws.send(json.dumps(cmd_obj))
    while True:
        raw_msg = ws.recv()
        res = json.loads(raw_msg)
        if res.get("id") == cmd_obj["id"]:
            return res.get("result", {})

def eval_js(expression):
    res = send_cmd("Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True
    })
    if "exceptionDetails" in res:
        print(f"JS ERROR: {res['exceptionDetails']}")
    return res.get("result", {}).get("value")

def capture_screenshot(filename):
    res = send_cmd("Page.captureScreenshot", {"format": "png"})
    if "data" in res:
        img_bytes = base64.b64decode(res["data"])
        filepath = os.path.join(artifact_dir, filename)
        with open(filepath, "wb") as f:
            f.write(img_bytes)
        print(f"Screenshot saved: {filename}")
        return filepath

try:
    time.sleep(2)
    tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read().decode())
    app_tabs = [t for t in tabs if "8000" in t.get("url", "")]
    target_tab = app_tabs[0] if app_tabs else tabs[0]
    ws = websocket.create_connection(target_tab["webSocketDebuggerUrl"])

    send_cmd("Page.enable")
    send_cmd("Runtime.enable")

    # Robust wait for Tempo readiness
    is_ready = False
    for i in range(30):
        val = eval_js("Boolean(window.TempoI18n && window.TempoMode && typeof window.TempoI18n.setLanguage === 'function')")
        if val is True:
            print(f"Tempo framework fully loaded after {i * 0.5:.1f}s.")
            is_ready = True
            break
        time.sleep(0.5)

    assert is_ready, "Tempo failed to initialize within timeout"

    print("\n=====================================================================")
    print("TEST 1: VERIFY VIETNAMESE EMERGENCY DASHBOARD (#today)")
    print("=====================================================================")

    vi_res = eval_js("""
    (() => {
        window.TempoI18n.setLanguage('vi');
        window.TempoMode.transitionContext('emergency');
        window.TempoMode.renderActiveModeHome();

        const wpTitle = document.querySelector('.urgent-working-plan-card h3')?.innerText || '';
        const editPlanBtn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText || '';
        const qrCard = document.querySelector('.urgent-card-overwhelmed h3')?.innerText || '';
        const fnCard = document.querySelector('.urgent-card-focus-now h3')?.innerText || '';
        const switcher = document.getElementById('nav-current-lang-label')?.innerText || '';

        return {
            lang: window.TempoI18n.getLanguage(),
            wpTitle: wpTitle.trim(),
            editPlanBtn: editPlanBtn.trim(),
            qrCard: qrCard.trim(),
            fnCard: fnCard.trim(),
            switcher: switcher.trim()
        };
    })()
    """)
    print("VI State:", json.dumps(vi_res, indent=2, ensure_ascii=False))

    assert "Kế hoạch làm việc của bạn" in vi_res['wpTitle'], f"Unexpected wpTitle: {vi_res['wpTitle']}"
    assert vi_res['editPlanBtn'] == "Điều chỉnh Kế hoạch", f"Unexpected editPlanBtn: {vi_res['editPlanBtn']}"
    assert vi_res['qrCard'] == "Giải tỏa nhanh", f"Unexpected qrCard: {vi_res['qrCard']}"
    assert vi_res['fnCard'] == "Tập trung ngay", f"Unexpected fnCard: {vi_res['fnCard']}"
    assert vi_res['switcher'] == "VI", f"Unexpected switcher: {vi_res['switcher']}"
    print("✓ TEST 1 PASSED: Vietnamese labels rendered correctly.")

    capture_screenshot("dashboard_vi_mode.png")

    print("\n=====================================================================")
    print("TEST 2: DYNAMIC SWITCH TO ENGLISH (EN) WITHOUT RELOAD")
    print("=====================================================================")

    en_res = eval_js("""
    (() => {
        window.TempoI18n.setLanguage('en');

        const wpTitle = document.querySelector('.urgent-working-plan-card h3')?.innerText || '';
        const editPlanBtn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText || '';
        const qrCard = document.querySelector('.urgent-card-overwhelmed h3')?.innerText || '';
        const fnCard = document.querySelector('.urgent-card-focus-now h3')?.innerText || '';
        const switcher = document.getElementById('nav-current-lang-label')?.innerText || '';
        const fullBody = document.body.innerText;

        return {
            lang: window.TempoI18n.getLanguage(),
            wpTitle: wpTitle.trim(),
            editPlanBtn: editPlanBtn.trim(),
            qrCard: qrCard.trim(),
            fnCard: fnCard.trim(),
            switcher: switcher.trim(),
            hasViKeHoach: fullBody.includes('Kế hoạch làm việc của bạn'),
            hasViDieuChinh: fullBody.includes('Điều chỉnh Kế hoạch'),
            hasViGiaiToa: fullBody.includes('Giải tỏa nhanh'),
            hasViTapTrung: fullBody.includes('Tập trung ngay')
        };
    })()
    """)
    print("EN Dynamic State:", json.dumps({k: v for k, v in en_res.items() if not k.startswith('hasVi')}, indent=2, ensure_ascii=False))

    assert "Working Plan" in en_res['wpTitle'], f"Unexpected wpTitle: {en_res['wpTitle']}"
    assert en_res['editPlanBtn'] == "Edit Plan", f"Unexpected editPlanBtn: {en_res['editPlanBtn']}"
    assert en_res['qrCard'] == "Quick Relief", f"Unexpected qrCard: {en_res['qrCard']}"
    assert en_res['fnCard'] == "Focus Now", f"Unexpected fnCard: {en_res['fnCard']}"
    assert en_res['switcher'] == "EN", f"Unexpected switcher: {en_res['switcher']}"
    assert not en_res['hasViKeHoach'], "Vietnamese 'Kế hoạch làm việc của bạn' leaked into English mode"
    assert not en_res['hasViDieuChinh'], "Vietnamese 'Điều chỉnh Kế hoạch' leaked into English mode"
    assert not en_res['hasViGiaiToa'], "Vietnamese 'Giải tỏa nhanh' leaked into English mode"
    assert not en_res['hasViTapTrung'], "Vietnamese 'Tập trung ngay' leaked into English mode"
    print("✓ TEST 2 PASSED: Dynamic update to English without page reload verified.")

    capture_screenshot("dashboard_en_mode.png")

    print("\n=====================================================================")
    print("TEST 3: DYNAMIC REVERT TO VIETNAMESE (VI) WITHOUT RELOAD")
    print("=====================================================================")

    vi_revert_res = eval_js("""
    (() => {
        window.TempoI18n.setLanguage('vi');

        const wpTitle = document.querySelector('.urgent-working-plan-card h3')?.innerText || '';
        const editPlanBtn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText || '';
        const qrCard = document.querySelector('.urgent-card-overwhelmed h3')?.innerText || '';
        const fnCard = document.querySelector('.urgent-card-focus-now h3')?.innerText || '';
        const switcher = document.getElementById('nav-current-lang-label')?.innerText || '';

        return {
            lang: window.TempoI18n.getLanguage(),
            wpTitle: wpTitle.trim(),
            editPlanBtn: editPlanBtn.trim(),
            qrCard: qrCard.trim(),
            fnCard: fnCard.trim(),
            switcher: switcher.trim()
        };
    })()
    """)
    print("VI Revert State:", json.dumps(vi_revert_res, indent=2, ensure_ascii=False))

    assert "Kế hoạch làm việc của bạn" in vi_revert_res['wpTitle']
    assert vi_revert_res['editPlanBtn'] == "Điều chỉnh Kế hoạch"
    assert vi_revert_res['qrCard'] == "Giải tỏa nhanh"
    assert vi_revert_res['fnCard'] == "Tập trung ngay"
    assert vi_revert_res['switcher'] == "VI"
    print("✓ TEST 3 PASSED: Dynamic revert to Vietnamese without page reload verified.")

    print("\n=====================================================================")
    print("TEST 4: PERSISTENCE ACROSS BROWSER RELOAD IN ENGLISH")
    print("=====================================================================")

    # Switch back to English and set reload tracker flag
    eval_js("""
    (() => {
        window.TempoI18n.setLanguage('en');
        window.__reloading_test = true;
    })()
    """)
    time.sleep(0.5)

    # Reload browser page
    send_cmd("Page.reload")
    time.sleep(1)

    # Wait until new document has loaded, DOM is complete, and __reloading_test is gone
    reloaded = False
    for i in range(30):
        val = eval_js("Boolean(window.TempoI18n && window.TempoMode && document.readyState === 'complete' && window.__reloading_test === undefined)")
        if val is True:
            reloaded = True
            break
        time.sleep(0.5)

    assert reloaded, "Page reload failed to complete"

    # Check that initial state after reload preserved English
    reload_init_state = eval_js("""
    (() => {
        return {
            lang: window.TempoI18n.getLanguage(),
            switcher: document.getElementById('nav-current-lang-label')?.innerText
        };
    })()
    """)
    print("Reload Language State:", json.dumps(reload_init_state, indent=2, ensure_ascii=False))
    assert reload_init_state['lang'] == "en"
    assert reload_init_state['switcher'] == "EN"

    # Render Emergency mode dashboard and verify all 4 labels
    reload_res = eval_js("""
    (() => {
        window.TempoMode.transitionContext('emergency');
        window.TempoMode.renderActiveModeHome();

        const wpTitle = document.querySelector('.urgent-working-plan-card h3')?.innerText || '';
        const editPlanBtn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText || '';
        const qrCard = document.querySelector('.urgent-card-overwhelmed h3')?.innerText || '';
        const fnCard = document.querySelector('.urgent-card-focus-now h3')?.innerText || '';
        const switcher = document.getElementById('nav-current-lang-label')?.innerText || '';

        return {
            lang: window.TempoI18n.getLanguage(),
            wpTitle: wpTitle.trim(),
            editPlanBtn: editPlanBtn.trim(),
            qrCard: qrCard.trim(),
            fnCard: fnCard.trim(),
            switcher: switcher.trim()
        };
    })()
    """)
    print("Reload Dashboard (EN):", json.dumps(reload_res, indent=2, ensure_ascii=False))

    assert reload_res['lang'] == "en"
    assert "Working Plan" in reload_res['wpTitle']
    assert reload_res['editPlanBtn'] == "Edit Plan"
    assert reload_res['qrCard'] == "Quick Relief"
    assert reload_res['fnCard'] == "Focus Now"
    assert reload_res['switcher'] == "EN"
    print("✓ TEST 4 PASSED: English state successfully persisted across browser reload.")

    capture_screenshot("dashboard_en_after_reload.png")

    print("\n=====================================================================")
    print("TEST 5: ROUTE NAVIGATION PERSISTENCE (#today -> #plan-workspace -> #today)")
    print("=====================================================================")

    route_res = eval_js("""
    (() => {
        window.TempoApp.navigateTo('plan-workspace');
        window.TempoApp.navigateTo('today');

        const wpTitle = document.querySelector('.urgent-working-plan-card h3')?.innerText || '';
        const editPlanBtn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText || '';
        const qrCard = document.querySelector('.urgent-card-overwhelmed h3')?.innerText || '';
        const fnCard = document.querySelector('.urgent-card-focus-now h3')?.innerText || '';
        const switcher = document.getElementById('nav-current-lang-label')?.innerText || '';

        return {
            lang: window.TempoI18n.getLanguage(),
            wpTitle: wpTitle.trim(),
            editPlanBtn: editPlanBtn.trim(),
            qrCard: qrCard.trim(),
            fnCard: fnCard.trim(),
            switcher: switcher.trim()
        };
    })()
    """)
    print("Route State (EN):", json.dumps(route_res, indent=2, ensure_ascii=False))

    assert route_res['lang'] == "en"
    assert "Working Plan" in route_res['wpTitle']
    assert route_res['editPlanBtn'] == "Edit Plan"
    assert route_res['qrCard'] == "Quick Relief"
    assert route_res['fnCard'] == "Focus Now"
    print("✓ TEST 5 PASSED: Language state preserved across route navigation.")

    print("\n=====================================================================")
    print("TEST 6: RECOVERY MODE LOCALIZATION CHECK (EN & VI)")
    print("=====================================================================")

    # Test Recovery Mode in English
    rec_en_res = eval_js("""
    (() => {
        window.TempoMode.transitionContext('recovery');
        window.TempoMode.renderActiveModeHome();

        const wpTitle = document.querySelector('.recovery-working-plan-card h3')?.innerText || '';
        const editPlanBtn = document.querySelector('.recovery-working-plan-card button')?.innerText || '';
        const qrCard = document.querySelector('.recovery-card-quick-relief h3')?.innerText || '';
        const fnCard = document.querySelector('.recovery-support-focus-now h3')?.innerText || '';
        const switcher = document.getElementById('nav-current-lang-label')?.innerText || '';

        return {
            mode: window.TempoMode.getActiveContext(),
            lang: window.TempoI18n.getLanguage(),
            wpTitle: wpTitle.trim(),
            editPlanBtn: editPlanBtn.trim(),
            qrCard: qrCard.trim(),
            fnCard: fnCard.trim(),
            switcher: switcher.trim()
        };
    })()
    """)
    print("Recovery Mode (EN):", json.dumps(rec_en_res, indent=2, ensure_ascii=False))

    assert rec_en_res['wpTitle'] == "Working Plan"
    assert rec_en_res['editPlanBtn'] == "Edit Plan"
    assert rec_en_res['qrCard'] == "Quick Relief"
    assert rec_en_res['fnCard'] == "Focus Now"
    assert rec_en_res['switcher'] == "EN"
    print("✓ Recovery Mode EN verified.")

    capture_screenshot("recovery_dashboard_en_mode.png")

    # Test Recovery Mode in Vietnamese
    rec_vi_res = eval_js("""
    (() => {
        window.TempoI18n.setLanguage('vi');

        const wpTitle = document.querySelector('.recovery-working-plan-card h3')?.innerText || '';
        const editPlanBtn = document.querySelector('.recovery-working-plan-card button')?.innerText || '';
        const qrCard = document.querySelector('.recovery-card-quick-relief h3')?.innerText || '';
        const fnCard = document.querySelector('.recovery-support-focus-now h3')?.innerText || '';
        const switcher = document.getElementById('nav-current-lang-label')?.innerText || '';

        return {
            mode: window.TempoMode.getActiveContext(),
            lang: window.TempoI18n.getLanguage(),
            wpTitle: wpTitle.trim(),
            editPlanBtn: editPlanBtn.trim(),
            qrCard: qrCard.trim(),
            fnCard: fnCard.trim(),
            switcher: switcher.trim()
        };
    })()
    """)
    print("Recovery Mode (VI):", json.dumps(rec_vi_res, indent=2, ensure_ascii=False))

    assert rec_vi_res['wpTitle'] == "Kế hoạch làm việc của bạn"
    assert rec_vi_res['editPlanBtn'] == "Điều chỉnh Kế hoạch"
    assert rec_vi_res['qrCard'] == "Giải tỏa nhanh"
    assert rec_vi_res['fnCard'] == "Tập trung ngay"
    assert rec_vi_res['switcher'] == "VI"
    print("✓ Recovery Mode VI verified.")

    capture_screenshot("recovery_dashboard_vi_mode.png")

    print("\n=====================================================================")
    print("SUCCESS: ALL 6 TESTS PASSED WITH 100% SUCCESS RATE!")
    print("=====================================================================")

finally:
    if ws:
        try: ws.close()
        except: pass
    proc.terminate()
    try: proc.wait(timeout=3)
    except: proc.kill()
