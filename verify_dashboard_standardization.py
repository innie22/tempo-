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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_std_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9496

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1050",
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

    # Wait for page ready
    for _ in range(20):
        time.sleep(0.5)
        ready = eval_js("document.readyState === 'complete' && !!window.TempoMode && !!window.TempoI18n")
        if ready:
            break

    print("=====================================================================")
    print("STEP 1: SEED URGENT PLAN & INITIALIZE VIETNAMESE (VI) DASHBOARD")
    print("=====================================================================")

    setup_res = eval_js("""
    (() => {
        // Set language to vi first
        window.TempoI18n.setLanguage('vi');

        const mockUser = { id: 'dev_user_1', email: 'dev@tempo.local', user_metadata: { full_name: 'Innie', role: 'student' } };
        localStorage.setItem('tempo_local_dev_user', JSON.stringify(mockUser));
        localStorage.setItem('tempo_mock_account_dev@tempo.local', JSON.stringify(mockUser));
        localStorage.setItem('tempo_user_established_context_dev_user_1', 'emergency');
        localStorage.setItem('tempo_established_context', 'emergency');
        localStorage.setItem('tempo_current_mode', 'emergency');

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
            plannedTasks: [
                {
                    id: 'pt_1',
                    dayDate: todayStr,
                    startTime: '14:00',
                    endTime: '15:00',
                    task: {
                        id: 'task_math_exam',
                        title: 'Ôn tập Giải tích 1',
                        estimatedMinutes: 60,
                        hasDeadline: true,
                        deadlineDate: todayStr,
                        deadlineTime: '18:00',
                        subtasks: [{ id: 'sub_1', title: 'Đọc lý thuyết chuỗi', completed: false }]
                    }
                },
                {
                    id: 'pt_2',
                    dayDate: todayStr,
                    startTime: '15:30',
                    endTime: '16:15',
                    task: {
                        id: 'task_physics_lab',
                        title: 'Báo cáo Thí nghiệm Vật lý',
                        estimatedMinutes: 45,
                        hasDeadline: true,
                        deadlineDate: todayStr,
                        deadlineTime: '20:00'
                    }
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
    vi_elements = eval_js("""
    (() => {
        const wpTitleElem = document.querySelector('.urgent-working-plan-card h3');
        const wpTitle = wpTitleElem?.innerText?.trim();
        const wpTitleHTML = wpTitleElem?.innerHTML?.trim();
        const editPlanBtn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText?.trim();
        const qrCard = document.querySelector('.urgent-card-overwhelmed h3')?.innerText?.trim();
        const fnCard = document.querySelector('.urgent-card-focus-now h3')?.innerText?.trim();
        const transitionQuestion = document.querySelector('[data-tempo-ui="mode-transition-prompt"] p')?.innerText?.trim() || '';
        const changeModeText = document.querySelector('[data-tempo-ui="change-mode-btn"]')?.innerText?.trim() || '';
        const switcher = document.getElementById('nav-current-lang-label')?.textContent?.trim();

        return {
            wpTitle,
            wpTitleHTML,
            editPlanBtn,
            qrCard,
            fnCard,
            transitionQuestion,
            changeModeText,
            switcher
        };
    })()
    """)
    print("\n[VI Dashboard State]:")
    for k, v in vi_elements.items():
        print(f"  {k}: {v}")

    # Validate against Approved UI Translations:
    # 1. Working Plan heading: Working Plan (visible) & Kế hoạch làm việc của bạn (sr-only)
    assert "Working Plan" in vi_elements['wpTitle'], f"Expected 'Working Plan' in visible text, got: {vi_elements['wpTitle']}"
    assert "Kế hoạch làm việc của bạn" in vi_elements['wpTitleHTML'], f"Expected 'Kế hoạch làm việc của bạn' in sr-only HTML, got: {vi_elements['wpTitleHTML']}"
    # 2. Edit Plan button: Sửa plan
    assert vi_elements['editPlanBtn'] == "Sửa plan", f"Expected 'Sửa plan', got: {vi_elements['editPlanBtn']}"
    # 3. Quick Relief card: Thư giãn
    assert vi_elements['qrCard'] == "Thư giãn", f"Expected 'Thư giãn', got: {vi_elements['qrCard']}"
    # 4. Focus Now card: Tập trung
    assert vi_elements['fnCard'] == "Tập trung", f"Expected 'Tập trung', got: {vi_elements['fnCard']}"
    # 5. Mode transition question: Mọi thứ đã đỡ gấp gáp hơn?
    assert vi_elements['transitionQuestion'] == "Mọi thứ đã đỡ gấp gáp hơn?", f"Expected 'Mọi thứ đã đỡ gấp gáp hơn?', got: {vi_elements['transitionQuestion']}"
    # 6. Change mode button: Chuyển chế độ
    assert vi_elements['changeModeText'] == "Chuyển chế độ", f"Expected 'Chuyển chế độ', got: {vi_elements['changeModeText']}"
    assert vi_elements['switcher'] == "VI", f"Expected 'VI', got: {vi_elements['switcher']}"

    print(">>> PASS: All 6 elements verified in Vietnamese mode!")
    capture_screenshot("dashboard_vi_standardized.png")

    print("\n=====================================================================")
    print("STEP 2: DYNAMIC SWITCH TO ENGLISH (EN) WITHOUT RELOAD")
    print("=====================================================================")

    # Switch to English dynamically via UI toggle/setLanguage
    eval_js("window.TempoI18n.setLanguage('en');")
    time.sleep(1)

    en_elements = eval_js("""
    (() => {
        const wpTitleElem = document.querySelector('.urgent-working-plan-card h3');
        const wpTitle = wpTitleElem?.innerText?.trim();
        const wpTitleHTML = wpTitleElem?.innerHTML?.trim();
        const editPlanBtn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText?.trim();
        const qrCard = document.querySelector('.urgent-card-overwhelmed h3')?.innerText?.trim();
        const fnCard = document.querySelector('.urgent-card-focus-now h3')?.innerText?.trim();
        const transitionQuestion = document.querySelector('[data-tempo-ui="mode-transition-prompt"] p')?.innerText?.trim() || '';
        const changeModeText = document.querySelector('[data-tempo-ui="change-mode-btn"]')?.innerText?.trim() || '';
        const switcher = document.getElementById('nav-current-lang-label')?.textContent?.trim();

        return {
            wpTitle,
            wpTitleHTML,
            editPlanBtn,
            qrCard,
            fnCard,
            transitionQuestion,
            changeModeText,
            switcher
        };
    })()
    """)
    print("\n[EN Dashboard State (Immediate without reload)]:")
    for k, v in en_elements.items():
        print(f"  {k}: {v}")

    # Validate against Approved UI Translations:
    # 1. Working Plan heading: Working Plan
    assert "Working Plan" in en_elements['wpTitle'], f"Expected 'Working Plan', got: {en_elements['wpTitle']}"
    # 2. Edit Plan button: Edit Plan
    assert en_elements['editPlanBtn'] == "Edit Plan", f"Expected 'Edit Plan', got: {en_elements['editPlanBtn']}"
    # 3. Quick Relief card: Quick Relief
    assert en_elements['qrCard'] == "Quick Relief", f"Expected 'Quick Relief', got: {en_elements['qrCard']}"
    # 4. Focus Now card: Focus Now
    assert en_elements['fnCard'] == "Focus Now", f"Expected 'Focus Now', got: {en_elements['fnCard']}"
    # 5. Mode transition question: Are things feeling less urgent now?
    assert en_elements['transitionQuestion'] == "Are things feeling less urgent now?", f"Expected 'Are things feeling less urgent now?', got: {en_elements['transitionQuestion']}"
    # 6. Change mode button: Change my mode
    assert en_elements['changeModeText'] == "Change my mode", f"Expected 'Change my mode', got: {en_elements['changeModeText']}"
    assert en_elements['switcher'] == "EN", f"Expected 'EN', got: {en_elements['switcher']}"

    print(">>> PASS: All 6 elements verified immediately in English mode (Zero reload)!")
    capture_screenshot("dashboard_en_standardized.png")

    print("\n=====================================================================")
    print("STEP 3: PERSISTENCE ACROSS FULL BROWSER RELOAD (EN)")
    print("=====================================================================")

    # Set reload flag and reload page
    eval_js("window.__reloading_test = true;")
    send_cmd("Page.reload")
    
    # Wait for page reload to finish
    for _ in range(30):
        time.sleep(0.5)
        ready = eval_js("document.readyState === 'complete' && !!window.TempoI18n && !!window.TempoMode && window.__reloading_test === undefined")
        if ready:
            break
    time.sleep(1)

    en_reload_elements = eval_js("""
    (() => {
        const wpTitleElem = document.querySelector('.urgent-working-plan-card h3');
        const wpTitle = wpTitleElem?.innerText?.trim();
        const wpTitleHTML = wpTitleElem?.innerHTML?.trim();
        const editPlanBtn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText?.trim();
        const qrCard = document.querySelector('.urgent-card-overwhelmed h3')?.innerText?.trim();
        const fnCard = document.querySelector('.urgent-card-focus-now h3')?.innerText?.trim();
        const transitionQuestion = document.querySelector('[data-tempo-ui="mode-transition-prompt"] p')?.innerText?.trim() || '';
        const changeModeText = document.querySelector('[data-tempo-ui="change-mode-btn"]')?.innerText?.trim() || '';
        const switcher = document.getElementById('nav-current-lang-label')?.textContent?.trim();

        return {
            wpTitle,
            wpTitleHTML,
            editPlanBtn,
            qrCard,
            fnCard,
            transitionQuestion,
            changeModeText,
            switcher
        };
    })()
    """)
    print("\n[EN Dashboard State After Browser Reload]:")
    for k, v in en_reload_elements.items():
        print(f"  {k}: {v}")

    assert "Working Plan" in en_reload_elements['wpTitle']
    assert en_reload_elements['editPlanBtn'] == "Edit Plan"
    assert en_reload_elements['qrCard'] == "Quick Relief"
    assert en_reload_elements['fnCard'] == "Focus Now"
    assert en_reload_elements['transitionQuestion'] == "Are things feeling less urgent now?"
    assert en_reload_elements['changeModeText'] == "Change my mode"
    assert en_reload_elements['switcher'] == "EN"
    print(">>> PASS: English preference and translations persisted across browser reload!")

    print("\n=====================================================================")
    print("STEP 4: ROUTE NAVIGATION PERSISTENCE (#today -> #plan-workspace -> #today)")
    print("=====================================================================")

    eval_js("window.location.hash = '#plan-workspace';")
    time.sleep(1)
    eval_js("window.location.hash = '#today';")
    time.sleep(1)

    nav_elements = eval_js("""
    (() => {
        const wpTitleElem = document.querySelector('.urgent-working-plan-card h3');
        const wpTitle = wpTitleElem?.innerText?.trim();
        const editPlanBtn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText?.trim();
        const qrCard = document.querySelector('.urgent-card-overwhelmed h3')?.innerText?.trim();
        const fnCard = document.querySelector('.urgent-card-focus-now h3')?.innerText?.trim();
        const transitionQuestion = document.querySelector('[data-tempo-ui="mode-transition-prompt"] p')?.innerText?.trim() || '';
        const changeModeText = document.querySelector('[data-tempo-ui="change-mode-btn"]')?.innerText?.trim() || '';

        return {
            wpTitle,
            editPlanBtn,
            qrCard,
            fnCard,
            transitionQuestion,
            changeModeText
        };
    })()
    """)
    print("\n[Dashboard State After Route Navigation]:")
    for k, v in nav_elements.items():
        print(f"  {k}: {v}")

    assert "Working Plan" in nav_elements['wpTitle']
    assert nav_elements['editPlanBtn'] == "Edit Plan"
    assert nav_elements['qrCard'] == "Quick Relief"
    assert nav_elements['fnCard'] == "Focus Now"
    assert nav_elements['transitionQuestion'] == "Are things feeling less urgent now?"
    assert nav_elements['changeModeText'] == "Change my mode"
    print(">>> PASS: English mode preserved across client route navigation!")

    print("\n=====================================================================")
    print("STEP 5: DYNAMIC SWITCH BACK TO VIETNAMESE (VI) WITHOUT RELOAD")
    print("=====================================================================")

    eval_js("window.TempoI18n.setLanguage('vi');")
    time.sleep(1)

    vi_revert_elements = eval_js("""
    (() => {
        const wpTitleElem = document.querySelector('.urgent-working-plan-card h3');
        const wpTitle = wpTitleElem?.innerText?.trim();
        const wpTitleHTML = wpTitleElem?.innerHTML?.trim();
        const editPlanBtn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText?.trim();
        const qrCard = document.querySelector('.urgent-card-overwhelmed h3')?.innerText?.trim();
        const fnCard = document.querySelector('.urgent-card-focus-now h3')?.innerText?.trim();
        const transitionQuestion = document.querySelector('[data-tempo-ui="mode-transition-prompt"] p')?.innerText?.trim() || '';
        const changeModeText = document.querySelector('[data-tempo-ui="change-mode-btn"]')?.innerText?.trim() || '';
        const switcher = document.getElementById('nav-current-lang-label')?.textContent?.trim();

        return {
            wpTitle,
            wpTitleHTML,
            editPlanBtn,
            qrCard,
            fnCard,
            transitionQuestion,
            changeModeText,
            switcher
        };
    })()
    """)
    print("\n[VI Dashboard State After Dynamic Switch Back]:")
    for k, v in vi_revert_elements.items():
        print(f"  {k}: {v}")

    assert "Working Plan" in vi_revert_elements['wpTitle']
    assert "Kế hoạch làm việc của bạn" in vi_revert_elements['wpTitleHTML']
    assert vi_revert_elements['editPlanBtn'] == "Sửa plan"
    assert vi_revert_elements['qrCard'] == "Thư giãn"
    assert vi_revert_elements['fnCard'] == "Tập trung"
    assert vi_revert_elements['transitionQuestion'] == "Mọi thứ đã đỡ gấp gáp hơn?"
    assert vi_revert_elements['changeModeText'] == "Chuyển chế độ"
    assert vi_revert_elements['switcher'] == "VI"
    print(">>> PASS: Dynamically switched back to Vietnamese without reload!")

    print("\n=====================================================================")
    print("STEP 6: PERSISTENCE ACROSS FULL BROWSER RELOAD (VI)")
    print("=====================================================================")

    eval_js("window.__reloading_test = true;")
    send_cmd("Page.reload")
    
    for _ in range(30):
        time.sleep(0.5)
        ready = eval_js("document.readyState === 'complete' && !!window.TempoI18n && !!window.TempoMode && window.__reloading_test === undefined")
        if ready:
            break
    time.sleep(1)

    vi_reload_elements = eval_js("""
    (() => {
        const wpTitleElem = document.querySelector('.urgent-working-plan-card h3');
        const wpTitle = wpTitleElem?.innerText?.trim();
        const wpTitleHTML = wpTitleElem?.innerHTML?.trim();
        const editPlanBtn = document.querySelector('.urgent-working-plan-card button span:last-child')?.innerText?.trim();
        const qrCard = document.querySelector('.urgent-card-overwhelmed h3')?.innerText?.trim();
        const fnCard = document.querySelector('.urgent-card-focus-now h3')?.innerText?.trim();
        const transitionQuestion = document.querySelector('[data-tempo-ui="mode-transition-prompt"] p')?.innerText?.trim() || '';
        const changeModeText = document.querySelector('[data-tempo-ui="change-mode-btn"]')?.innerText?.trim() || '';
        const switcher = document.getElementById('nav-current-lang-label')?.textContent?.trim();

        return {
            wpTitle,
            wpTitleHTML,
            editPlanBtn,
            qrCard,
            fnCard,
            transitionQuestion,
            changeModeText,
            switcher
        };
    })()
    """)
    print("\n[VI Dashboard State After Reload]:")
    for k, v in vi_reload_elements.items():
        print(f"  {k}: {v}")

    assert "Working Plan" in vi_reload_elements['wpTitle']
    assert "Kế hoạch làm việc của bạn" in vi_reload_elements['wpTitleHTML']
    assert vi_reload_elements['editPlanBtn'] == "Sửa plan"
    assert vi_reload_elements['qrCard'] == "Thư giãn"
    assert vi_reload_elements['fnCard'] == "Tập trung"
    assert vi_reload_elements['transitionQuestion'] == "Mọi thứ đã đỡ gấp gáp hơn?"
    assert vi_reload_elements['changeModeText'] == "Chuyển chế độ"
    assert vi_reload_elements['switcher'] == "VI"
    print(">>> PASS: Vietnamese preference and translations persisted across browser reload!")

    print("\n=====================================================================")
    print("STEP 7: RECOVERY MODE STANDARDIZATION CHECK")
    print("=====================================================================")

    eval_js("""
    (() => {
        localStorage.setItem('tempo_user_established_context_dev_user_1', 'recovery');
        localStorage.setItem('tempo_current_mode', 'recovery');
        localStorage.setItem('tempo_established_context', 'recovery');
        window.TempoMode.transitionContext('recovery');
        window.TempoMode.renderActiveModeHome();
    })()
    """)
    time.sleep(1)

    rec_elements = eval_js("""
    (() => {
        const wpTitle = document.querySelector('#recovery-working-plan h3')?.innerText?.trim();
        const wpTitleHTML = document.querySelector('#recovery-working-plan h3')?.innerHTML?.trim();
        const editPlanBtn = document.querySelector('#recovery-working-plan button span:last-child')?.innerText?.trim();
        const qrCard = document.querySelector('.recovery-card-quick-relief h3')?.innerText?.trim();
        const fnCard = document.querySelector('.recovery-support-focus-now h3')?.innerText?.trim();
        const changeModeBtn = document.querySelector('.recovery-prompt-wrap button')?.innerText?.trim();

        return {
            wpTitle,
            wpTitleHTML,
            editPlanBtn,
            qrCard,
            fnCard,
            changeModeText: changeModeBtn
        };
    })()
    """)
    print("\n[Recovery Mode State in VI]:")
    for k, v in rec_elements.items():
        print(f"  {k}: {v}")

    assert "Working Plan" in rec_elements['wpTitle']
    assert rec_elements['editPlanBtn'] == "Sửa plan"
    assert rec_elements['qrCard'] == "Thư giãn"
    assert rec_elements['fnCard'] == "Tập trung"
    assert rec_elements['changeModeText'] == "Chuyển chế độ"
    print(">>> PASS: Recovery mode elements match standardized translations!")

    print("\n=====================================================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=====================================================================")

finally:
    if ws:
        try: ws.close()
        except: pass
    if proc:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except:
            proc.kill()
