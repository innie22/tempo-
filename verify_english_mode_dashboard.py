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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9399

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
        res = json.loads(ws.recv())
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
    tabs_res = urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read().decode()
    tabs = json.loads(tabs_res)
    app_tabs = [t for t in tabs if "127.0.0.1:8000" in t.get("url", "") or "localhost:8000" in t.get("url", "")]
    target_tab = app_tabs[0] if app_tabs else tabs[0]
    ws_url = target_tab["webSocketDebuggerUrl"]
    ws = websocket.create_connection(ws_url)

    send_cmd("Page.enable")
    send_cmd("Runtime.enable")
    time.sleep(2)

    print("=====================================================================")
    print("STEP 1: SEED URGENT PLAN & INITIALIZE VIETNAMESE DASHBOARD")
    print("=====================================================================")

    setup_res = eval_js("""
    (() => {
        // Set language to vi first
        window.TempoI18n.setLanguage('vi');

        const todayStr = window.TempoI18n ? window.TempoI18n.getLocalTodayISO() : '2026-11-01';
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

        if (window.TempoMode) {
            window.TempoMode.transitionContext('emergency');
            window.TempoMode.renderActiveModeHome();
        }

        return {
            mode: window.TempoMode ? window.TempoMode.getActiveContext() : null,
            lang: window.TempoI18n ? window.TempoI18n.getLanguage() : null
        };
    })()
    """)
    print("Setup result:", setup_res)
    time.sleep(1)

    # Inspect VI dashboard labels
    vi_state = eval_js("""
    (() => {
        const wpTitle = document.querySelector('.urgent-working-plan-card h3')?.innerText?.trim();
        const editPlanBtn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText?.trim();
        const qrCard = document.querySelector('.urgent-card-overwhelmed h3')?.innerText?.trim();
        const fnCard = document.querySelector('.urgent-card-focus-now h3')?.innerText?.trim();
        const switcher = document.getElementById('nav-current-lang-label')?.textContent?.trim();

        return {
            wpTitle,
            editPlanBtn,
            qrCard,
            fnCard,
            switcher
        };
    })()
    """)
    print("VI Dashboard State:", vi_state)

    assert "Kế hoạch làm việc của bạn" in vi_state['wpTitle'], f"Expected 'Kế hoạch làm việc của bạn', got: {vi_state['wpTitle']}"
    assert vi_state['editPlanBtn'] == "Điều chỉnh Kế hoạch", f"Expected 'Điều chỉnh Kế hoạch', got: {vi_state['editPlanBtn']}"
    assert vi_state['qrCard'] == "Giải tỏa nhanh", f"Expected 'Giải tỏa nhanh', got: {vi_state['qrCard']}"
    assert vi_state['fnCard'] == "Tập trung ngay", f"Expected 'Tập trung ngay', got: {vi_state['fnCard']}"
    assert vi_state['switcher'] == "VI", f"Expected 'VI', got: {vi_state['switcher']}"
    print("✓ VI Dashboard verified successfully.")

    capture_screenshot("dashboard_vi_mode.png")

    print("\n=====================================================================")
    print("STEP 2: DYNAMIC SWITCH TO ENGLISH (EN) WITHOUT RELOAD")
    print("=====================================================================")

    # Switch to English
    eval_js("window.TempoI18n.setLanguage('en');")
    time.sleep(1)

    en_state = eval_js("""
    (() => {
        const wpTitle = document.querySelector('.urgent-working-plan-card h3')?.innerText?.trim();
        const editPlanBtn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText?.trim();
        const qrCard = document.querySelector('.urgent-card-overwhelmed h3')?.innerText?.trim();
        const fnCard = document.querySelector('.urgent-card-focus-now h3')?.innerText?.trim();
        const switcher = document.getElementById('nav-current-lang-label')?.textContent?.trim();
        const fullBody = document.body.innerText;

        return {
            wpTitle,
            editPlanBtn,
            qrCard,
            fnCard,
            switcher,
            hasKeHoach: fullBody.includes('Kế hoạch làm việc của bạn'),
            hasDieuChinh: fullBody.includes('Điều chỉnh Kế hoạch'),
            hasGiaiToa: fullBody.includes('Giải tỏa nhanh'),
            hasTapTrung: fullBody.includes('Tập trung ngay')
        };
    })()
    """)
    print("EN Dashboard State (Dynamic without reload):", en_state)

    assert "Working Plan" in en_state['wpTitle'], f"Expected 'Working Plan', got: {en_state['wpTitle']}"
    assert en_state['editPlanBtn'] == "Edit Plan", f"Expected 'Edit Plan', got: {en_state['editPlanBtn']}"
    assert en_state['qrCard'] == "Quick Relief", f"Expected 'Quick Relief', got: {en_state['qrCard']}"
    assert en_state['fnCard'] == "Focus Now", f"Expected 'Focus Now', got: {en_state['fnCard']}"
    assert en_state['switcher'] == "EN", f"Expected 'EN', got: {en_state['switcher']}"
    assert not en_state['hasKeHoach'], "Vietnamese 'Kế hoạch làm việc của bạn' should not exist in EN mode"
    assert not en_state['hasDieuChinh'], "Vietnamese 'Điều chỉnh Kế hoạch' should not exist in EN mode"
    assert not en_state['hasGiaiToa'], "Vietnamese 'Giải tỏa nhanh' should not exist in EN mode"
    assert not en_state['hasTapTrung'], "Vietnamese 'Tập trung ngay' should not exist in EN mode"
    print("✓ EN Dashboard dynamically updated without reload verified successfully.")

    capture_screenshot("dashboard_en_mode.png")

    print("\n=====================================================================")
    print("STEP 3: DYNAMIC REVERT BACK TO VIETNAMESE (VI) WITHOUT RELOAD")
    print("=====================================================================")

    eval_js("window.TempoI18n.setLanguage('vi');")
    time.sleep(1)

    vi_revert_state = eval_js("""
    (() => {
        const wpTitle = document.querySelector('.urgent-working-plan-card h3')?.innerText?.trim();
        const editPlanBtn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText?.trim();
        const qrCard = document.querySelector('.urgent-card-overwhelmed h3')?.innerText?.trim();
        const fnCard = document.querySelector('.urgent-card-focus-now h3')?.innerText?.trim();
        const switcher = document.getElementById('nav-current-lang-label')?.textContent?.trim();

        return {
            wpTitle,
            editPlanBtn,
            qrCard,
            fnCard,
            switcher
        };
    })()
    """)
    print("VI Reverted State:", vi_revert_state)

    assert "Kế hoạch làm việc của bạn" in vi_revert_state['wpTitle']
    assert vi_revert_state['editPlanBtn'] == "Điều chỉnh Kế hoạch"
    assert vi_revert_state['qrCard'] == "Giải tỏa nhanh"
    assert vi_revert_state['fnCard'] == "Tập trung ngay"
    assert vi_revert_state['switcher'] == "VI"
    print("✓ Dynamic revert to VI without reload verified successfully.")

    print("\n=====================================================================")
    print("STEP 4: PERSISTENCE TEST - SET EN AND RELOAD BROWSER")
    print("=====================================================================")

    eval_js("window.TempoI18n.setLanguage('en');")
    time.sleep(0.5)

    # Reload page
    send_cmd("Page.reload")
    time.sleep(2)

    persisted_en_state = eval_js("""
    (() => {
        const wpTitle = document.querySelector('.urgent-working-plan-card h3')?.innerText?.trim();
        const editPlanBtn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText?.trim();
        const qrCard = document.querySelector('.urgent-card-overwhelmed h3')?.innerText?.trim();
        const fnCard = document.querySelector('.urgent-card-focus-now h3')?.innerText?.trim();
        const switcher = document.getElementById('nav-current-lang-label')?.textContent?.trim();

        return {
            wpTitle,
            editPlanBtn,
            qrCard,
            fnCard,
            switcher
        };
    })()
    """)
    print("EN State After Reload:", persisted_en_state)

    assert "Working Plan" in persisted_en_state['wpTitle'], f"Expected 'Working Plan', got: {persisted_en_state['wpTitle']}"
    assert persisted_en_state['editPlanBtn'] == "Edit Plan", f"Expected 'Edit Plan', got: {persisted_en_state['editPlanBtn']}"
    assert persisted_en_state['qrCard'] == "Quick Relief", f"Expected 'Quick Relief', got: {persisted_en_state['qrCard']}"
    assert persisted_en_state['fnCard'] == "Focus Now", f"Expected 'Focus Now', got: {persisted_en_state['fnCard']}"
    assert persisted_en_state['switcher'] == "EN", f"Expected 'EN', got: {persisted_en_state['switcher']}"
    print("✓ Language persistence across page reload verified successfully.")

    capture_screenshot("dashboard_en_after_reload.png")

    print("\n=====================================================================")
    print("STEP 5: ROUTE CHANGE TEST - NAVIGATE TO #plan-workspace AND BACK")
    print("=====================================================================")

    eval_js("window.TempoApp.navigateTo('plan-workspace');")
    time.sleep(1)
    eval_js("window.TempoApp.navigateTo('today');")
    time.sleep(1)

    route_en_state = eval_js("""
    (() => {
        const wpTitle = document.querySelector('.urgent-working-plan-card h3')?.innerText?.trim();
        const editPlanBtn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText?.trim();
        const qrCard = document.querySelector('.urgent-card-overwhelmed h3')?.innerText?.trim();
        const fnCard = document.querySelector('.urgent-card-focus-now h3')?.innerText?.trim();
        const switcher = document.getElementById('nav-current-lang-label')?.textContent?.trim();

        return {
            wpTitle,
            editPlanBtn,
            qrCard,
            fnCard,
            switcher
        };
    })()
    """)
    print("EN State After Navigation:", route_en_state)

    assert "Working Plan" in route_en_state['wpTitle']
    assert route_en_state['editPlanBtn'] == "Edit Plan"
    assert route_en_state['qrCard'] == "Quick Relief"
    assert route_en_state['fnCard'] == "Focus Now"
    print("✓ Route navigation persistence verified successfully.")

    print("\n=====================================================================")
    print("STEP 6: RECOVERY MODE LOCALIZATION CHECK (EN & VI)")
    print("=====================================================================")

    # Switch mode to recovery in EN
    eval_js("""
    (() => {
        window.TempoMode.transitionContext('recovery');
        window.TempoMode.renderActiveModeHome();
    })()
    """)
    time.sleep(1)

    recovery_en_state = eval_js("""
    (() => {
        const wpTitle = document.querySelector('.recovery-working-plan-card h3')?.innerText?.trim();
        const editPlanBtn = document.querySelector('.recovery-working-plan-card button')?.innerText?.trim();
        const qrCard = document.querySelector('.recovery-card-quick-relief h3')?.innerText?.trim();
        const fnCard = document.querySelector('.recovery-support-focus-now h3')?.innerText?.trim();
        const switcher = document.getElementById('nav-current-lang-label')?.textContent?.trim();

        return {
            wpTitle,
            editPlanBtn,
            qrCard,
            fnCard,
            switcher
        };
    })()
    """)
    print("Recovery Mode EN State:", recovery_en_state)

    assert recovery_en_state['wpTitle'] == "Working Plan", f"Expected 'Working Plan', got: {recovery_en_state['wpTitle']}"
    assert recovery_en_state['editPlanBtn'] == "Edit Plan", f"Expected 'Edit Plan', got: {recovery_en_state['editPlanBtn']}"
    assert recovery_en_state['qrCard'] == "Quick Relief", f"Expected 'Quick Relief', got: {recovery_en_state['qrCard']}"
    assert recovery_en_state['fnCard'] == "Focus Now", f"Expected 'Focus Now', got: {recovery_en_state['fnCard']}"
    print("✓ Recovery Mode EN localization verified successfully.")

    capture_screenshot("recovery_dashboard_en_mode.png")

    # Switch to VI in Recovery mode
    eval_js("window.TempoI18n.setLanguage('vi');")
    time.sleep(1)

    recovery_vi_state = eval_js("""
    (() => {
        const wpTitle = document.querySelector('.recovery-working-plan-card h3')?.innerText?.trim();
        const editPlanBtn = document.querySelector('.recovery-working-plan-card button')?.innerText?.trim();
        const qrCard = document.querySelector('.recovery-card-quick-relief h3')?.innerText?.trim();
        const fnCard = document.querySelector('.recovery-support-focus-now h3')?.innerText?.trim();
        const switcher = document.getElementById('nav-current-lang-label')?.textContent?.trim();

        return {
            wpTitle,
            editPlanBtn,
            qrCard,
            fnCard,
            switcher
        };
    })()
    """)
    print("Recovery Mode VI State:", recovery_vi_state)

    assert recovery_vi_state['wpTitle'] == "Kế hoạch làm việc của bạn", f"Expected 'Kế hoạch làm việc của bạn', got: {recovery_vi_state['wpTitle']}"
    assert recovery_vi_state['editPlanBtn'] == "Điều chỉnh Kế hoạch", f"Expected 'Điều chỉnh Kế hoạch', got: {recovery_vi_state['editPlanBtn']}"
    assert recovery_vi_state['qrCard'] == "Giải tỏa nhanh", f"Expected 'Giải tỏa nhanh', got: {recovery_vi_state['qrCard']}"
    assert recovery_vi_state['fnCard'] == "Tập trung ngay", f"Expected 'Tập trung ngay', got: {recovery_vi_state['fnCard']}"
    print("✓ Recovery Mode VI localization verified successfully.")

    capture_screenshot("recovery_dashboard_vi_mode.png")

    print("\n=====================================================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=====================================================================")

finally:
    if ws:
        try: ws.close()
        except: pass
    proc.terminate()
    try: proc.wait(timeout=3)
    except: proc.kill()
