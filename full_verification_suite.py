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

user_data_dir = tempfile.mkdtemp(prefix="tempo_suite_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9999

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

    # Wait until Tempo is ready
    for _ in range(20):
        ready = eval_js("Boolean(window.TempoI18n && window.TempoMode)")
        if ready:
            print("Tempo framework fully initialized.")
            break
        time.sleep(0.5)

    print("\n=====================================================================")
    print("TEST 1: INITIALIZE VIETNAMESE EMERGENCY DASHBOARD (#today)")
    print("=====================================================================")

    vi_init = eval_js("""
    (() => {
        window.TempoI18n.setLanguage('vi');
        const todayStr = window.TempoI18n.getLocalTodayISO();
        const plan = {
            id: 'plan_test_localization',
            createdDate: todayStr,
            updatedAt: new Date().toISOString(),
            status: 'active',
            tasks: [
                {
                    id: 'task_math_exam',
                    title: 'Ôn tập Giải tích 1',
                    estimatedMinutes: 60,
                    hasDeadline: true,
                    deadlineDate: todayStr,
                    deadlineTime: '18:00',
                    scheduledDate: todayStr,
                    scheduledStart: '14:00',
                    scheduledEnd: '15:00',
                    subtasks: [
                        { id: 'sub_1', title: 'Đọc lý thuyết chuỗi', completed: false }
                    ]
                },
                {
                    id: 'task_physics_lab',
                    title: 'Báo cáo Thí nghiệm Vật lý',
                    estimatedMinutes: 45,
                    hasDeadline: true,
                    deadlineDate: todayStr,
                    deadlineTime: '20:00',
                    scheduledDate: todayStr,
                    scheduledStart: '15:30',
                    scheduledEnd: '16:15'
                }
            ],
            availability: {
                selectedDays: [todayStr],
                days: [
                    {
                        date: todayStr,
                        blocks: [{ start: '14:00', end: '18:00' }]
                    }
                ]
            }
        };

        localStorage.setItem('tempo_confirmed_plan', JSON.stringify(plan));
        localStorage.setItem('tempo_current_mode', 'emergency');
        localStorage.setItem('tempo_established_context', 'emergency');
        sessionStorage.removeItem('tempo_active_shared_tool');

        window.TempoMode.transitionContext('emergency');
        window.TempoMode.renderActiveModeHome();

        return {
            lang: window.TempoI18n.getLanguage(),
            wpTitle: document.querySelector('.urgent-working-plan-card h3')?.innerText,
            editPlanBtn: document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText,
            qrCard: document.querySelector('.urgent-card-overwhelmed h3')?.innerText,
            fnCard: document.querySelector('.urgent-card-focus-now h3')?.innerText,
            switcher: document.getElementById('nav-current-lang-label')?.innerText
        };
    })()
    """)
    print("VI Initial State:", json.dumps(vi_init, indent=2, ensure_ascii=False))

    assert "Kế hoạch làm việc của bạn" in vi_init['wpTitle']
    assert vi_init['editPlanBtn'] == "Điều chỉnh Kế hoạch"
    assert vi_init['qrCard'] == "Giải tỏa nhanh"
    assert vi_init['fnCard'] == "Tập trung ngay"
    assert vi_init['switcher'] == "VI"
    print("✓ VI Dashboard verified.")

    capture_screenshot("dashboard_vi_mode.png")

    print("\n=====================================================================")
    print("TEST 2: DYNAMIC SWITCH TO ENGLISH (EN) WITHOUT RELOAD")
    print("=====================================================================")

    en_dynamic = eval_js("""
    (() => {
        // Trigger switch via UI switcher method
        window.TempoI18n.setLanguage('en');

        return {
            lang: window.TempoI18n.getLanguage(),
            wpTitle: document.querySelector('.urgent-working-plan-card h3')?.innerText,
            editPlanBtn: document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText,
            qrCard: document.querySelector('.urgent-card-overwhelmed h3')?.innerText,
            fnCard: document.querySelector('.urgent-card-focus-now h3')?.innerText,
            switcher: document.getElementById('nav-current-lang-label')?.innerText,
            fullBody: document.body.innerText
        };
    })()
    """)
    print("EN Dynamic State:", json.dumps({k: v for k, v in en_dynamic.items() if k != 'fullBody'}, indent=2, ensure_ascii=False))

    assert "Working Plan" in en_dynamic['wpTitle'], f"Expected 'Working Plan', got: {en_dynamic['wpTitle']}"
    assert en_dynamic['editPlanBtn'] == "Edit Plan", f"Expected 'Edit Plan', got: {en_dynamic['editPlanBtn']}"
    assert en_dynamic['qrCard'] == "Quick Relief", f"Expected 'Quick Relief', got: {en_dynamic['qrCard']}"
    assert en_dynamic['fnCard'] == "Focus Now", f"Expected 'Focus Now', got: {en_dynamic['fnCard']}"
    assert en_dynamic['switcher'] == "EN", f"Expected 'EN', got: {en_dynamic['switcher']}"
    assert "Kế hoạch làm việc của bạn" not in en_dynamic['fullBody']
    assert "Điều chỉnh Kế hoạch" not in en_dynamic['fullBody']
    assert "Giải tỏa nhanh" not in en_dynamic['fullBody']
    assert "Tập trung ngay" not in en_dynamic['fullBody']
    print("✓ EN Dynamic switch verified without reload.")

    capture_screenshot("dashboard_en_mode.png")

    print("\n=====================================================================")
    print("TEST 3: DYNAMIC REVERT TO VIETNAMESE (VI) WITHOUT RELOAD")
    print("=====================================================================")

    vi_revert = eval_js("""
    (() => {
        window.TempoI18n.setLanguage('vi');

        return {
            lang: window.TempoI18n.getLanguage(),
            wpTitle: document.querySelector('.urgent-working-plan-card h3')?.innerText,
            editPlanBtn: document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText,
            qrCard: document.querySelector('.urgent-card-overwhelmed h3')?.innerText,
            fnCard: document.querySelector('.urgent-card-focus-now h3')?.innerText,
            switcher: document.getElementById('nav-current-lang-label')?.innerText
        };
    })()
    """)
    print("VI Revert State:", json.dumps(vi_revert, indent=2, ensure_ascii=False))

    assert "Kế hoạch làm việc của bạn" in vi_revert['wpTitle']
    assert vi_revert['editPlanBtn'] == "Điều chỉnh Kế hoạch"
    assert vi_revert['qrCard'] == "Giải tỏa nhanh"
    assert vi_revert['fnCard'] == "Tập trung ngay"
    assert vi_revert['switcher'] == "VI"
    print("✓ Dynamic revert to VI verified without reload.")

    print("\n=====================================================================")
    print("TEST 4: PERSISTENCE ACROSS BROWSER RELOAD IN ENGLISH")
    print("=====================================================================")

    eval_js("window.TempoI18n.setLanguage('en');")
    time.sleep(0.5)

    send_cmd("Page.reload")
    time.sleep(2)

    # Wait for reload ready
    for _ in range(20):
        ready = eval_js("Boolean(window.TempoI18n && window.TempoMode)")
        if ready:
            break
        time.sleep(0.5)

    reload_state = eval_js("""
    (() => {
        return {
            lang: window.TempoI18n.getLanguage(),
            wpTitle: document.querySelector('.urgent-working-plan-card h3')?.innerText,
            editPlanBtn: document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText,
            qrCard: document.querySelector('.urgent-card-overwhelmed h3')?.innerText,
            fnCard: document.querySelector('.urgent-card-focus-now h3')?.innerText,
            switcher: document.getElementById('nav-current-lang-label')?.innerText
        };
    })()
    """)
    print("Reload State (EN):", json.dumps(reload_state, indent=2, ensure_ascii=False))

    assert reload_state['lang'] == "en"
    assert "Working Plan" in reload_state['wpTitle']
    assert reload_state['editPlanBtn'] == "Edit Plan"
    assert reload_state['qrCard'] == "Quick Relief"
    assert reload_state['fnCard'] == "Focus Now"
    assert reload_state['switcher'] == "EN"
    print("✓ Language persistence across page reload verified.")

    capture_screenshot("dashboard_en_after_reload.png")

    print("\n=====================================================================")
    print("TEST 5: ROUTE NAVIGATION PERSISTENCE (#today -> #plan-workspace -> #today)")
    print("=====================================================================")

    route_state = eval_js("""
    (() => {
        window.TempoApp.navigateTo('plan-workspace');
        window.TempoApp.navigateTo('today');

        return {
            lang: window.TempoI18n.getLanguage(),
            wpTitle: document.querySelector('.urgent-working-plan-card h3')?.innerText,
            editPlanBtn: document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText,
            qrCard: document.querySelector('.urgent-card-overwhelmed h3')?.innerText,
            fnCard: document.querySelector('.urgent-card-focus-now h3')?.innerText,
            switcher: document.getElementById('nav-current-lang-label')?.innerText
        };
    })()
    """)
    print("Route Navigation State (EN):", json.dumps(route_state, indent=2, ensure_ascii=False))

    assert route_state['lang'] == "en"
    assert "Working Plan" in route_state['wpTitle']
    assert route_state['editPlanBtn'] == "Edit Plan"
    assert route_state['qrCard'] == "Quick Relief"
    assert route_state['fnCard'] == "Focus Now"
    print("✓ Route navigation persistence verified.")

    print("\n=====================================================================")
    print("TEST 6: RECOVERY MODE LOCALIZATION CHECK (EN & VI)")
    print("=====================================================================")

    # Test Recovery in EN
    recovery_en = eval_js("""
    (() => {
        window.TempoMode.transitionContext('recovery');
        window.TempoMode.renderActiveModeHome();

        return {
            mode: window.TempoMode.getActiveContext(),
            lang: window.TempoI18n.getLanguage(),
            wpTitle: document.querySelector('.recovery-working-plan-card h3')?.innerText,
            editPlanBtn: document.querySelector('.recovery-working-plan-card button')?.innerText,
            qrCard: document.querySelector('.recovery-card-quick-relief h3')?.innerText,
            fnCard: document.querySelector('.recovery-support-focus-now h3')?.innerText,
            switcher: document.getElementById('nav-current-lang-label')?.innerText
        };
    })()
    """)
    print("Recovery Mode EN State:", json.dumps(recovery_en, indent=2, ensure_ascii=False))

    assert recovery_en['wpTitle'] == "Working Plan"
    assert recovery_en['editPlanBtn'] == "Edit Plan"
    assert recovery_en['qrCard'] == "Quick Relief"
    assert recovery_en['fnCard'] == "Focus Now"
    assert recovery_en['switcher'] == "EN"
    print("✓ Recovery Mode EN verified.")

    capture_screenshot("recovery_dashboard_en_mode.png")

    # Test Recovery in VI
    recovery_vi = eval_js("""
    (() => {
        window.TempoI18n.setLanguage('vi');

        return {
            mode: window.TempoMode.getActiveContext(),
            lang: window.TempoI18n.getLanguage(),
            wpTitle: document.querySelector('.recovery-working-plan-card h3')?.innerText,
            editPlanBtn: document.querySelector('.recovery-working-plan-card button')?.innerText,
            qrCard: document.querySelector('.recovery-card-quick-relief h3')?.innerText,
            fnCard: document.querySelector('.recovery-support-focus-now h3')?.innerText,
            switcher: document.getElementById('nav-current-lang-label')?.innerText
        };
    })()
    """)
    print("Recovery Mode VI State:", json.dumps(recovery_vi, indent=2, ensure_ascii=False))

    assert recovery_vi['wpTitle'] == "Kế hoạch làm việc của bạn"
    assert recovery_vi['editPlanBtn'] == "Điều chỉnh Kế hoạch"
    assert recovery_vi['qrCard'] == "Giải tỏa nhanh"
    assert recovery_vi['fnCard'] == "Tập trung ngay"
    assert recovery_vi['switcher'] == "VI"
    print("✓ Recovery Mode VI verified.")

    capture_screenshot("recovery_dashboard_vi_mode.png")

    print("\n=====================================================================")
    print("ALL 6 TESTS PASSED SUCCESSFULLY WITH 100% PASS RATE!")
    print("=====================================================================")

finally:
    if ws:
        try: ws.close()
        except: pass
    proc.terminate()
    try: proc.wait(timeout=3)
    except: proc.kill()
