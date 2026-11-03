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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_date_enc_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9502

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1100",
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
    for _ in range(25):
        time.sleep(0.5)
        ready = eval_js("document.readyState === 'complete' && !!window.TempoMode && !!window.TempoI18n")
        if ready:
            break

    print("=====================================================================")
    print("STEP 1: SEED PLAN WITH TOMORROW TASK HAVING START TIME '14:00' IN VI")
    print("=====================================================================")

    seed_res = eval_js("""
    (async () => {
        window.TempoI18n.setLanguage('vi');

        const mockUser = { id: 'dev_user_1', email: 'dev@tempo.local', user_metadata: { full_name: 'Innie', role: 'student' } };
        localStorage.setItem('tempo_local_dev_user', JSON.stringify(mockUser));
        localStorage.setItem('tempo_mock_account_dev@tempo.local', JSON.stringify(mockUser));
        localStorage.setItem('tempo_user_established_context_dev_user_1', 'emergency');
        localStorage.setItem('tempo_established_context', 'emergency');
        localStorage.setItem('tempo_current_mode', 'emergency');

        const todayStr = window.TempoI18n ? window.TempoI18n.getLocalTodayISO() : '2026-11-01';
        const tomorrowStr = window.TempoI18n ? window.TempoI18n.getLocalTomorrowISO() : '2026-11-02';

        const plan = {
            id: 'plan_test_date_encoding',
            createdDate: todayStr,
            updatedAt: new Date().toISOString(),
            status: 'active',
            tasks: [
                {
                    id: 'task_today_1',
                    title: 'Ôn tập Giải tích 1',
                    estimatedMinutes: 60,
                    completed: true,
                    hasDeadline: true,
                    deadlineDate: todayStr,
                    deadlineTime: '18:00',
                    scheduledDate: todayStr
                },
                {
                    id: 'task_tomorrow_1',
                    title: 'Tiểu luận Triết học Mác - Lênin',
                    estimatedMinutes: 90,
                    completed: false,
                    hasDeadline: true,
                    deadlineDate: tomorrowStr,
                    deadlineTime: '21:00',
                    scheduledDate: tomorrowStr
                }
            ],
            plannedTasks: [
                {
                    id: 'pt_today_1',
                    dayDate: todayStr,
                    startTime: '10:00',
                    endTime: '11:00',
                    task: {
                        id: 'task_today_1',
                        title: 'Ôn tập Giải tích 1',
                        name: 'Ôn tập Giải tích 1',
                        estimatedMinutes: 60,
                        completed: true,
                        hasDeadline: true,
                        deadlineDate: todayStr,
                        deadlineTime: '18:00'
                    }
                },
                {
                    id: 'pt_tomorrow_1',
                    dayDate: tomorrowStr,
                    startTime: '14:00',
                    endTime: '15:30',
                    task: {
                        id: 'task_tomorrow_1',
                        title: 'Tiểu luận Triết học Mác - Lênin',
                        name: 'Tiểu luận Triết học Mác - Lênin',
                        estimatedMinutes: 90,
                        completed: false,
                        hasDeadline: true,
                        deadlineDate: tomorrowStr,
                        deadlineTime: '21:00'
                    }
                }
            ],
            availability: {
                selectedDays: [todayStr, tomorrowStr],
                days: [
                    { date: todayStr, blocks: [{ start: '10:00', end: '18:00' }] },
                    { date: tomorrowStr, blocks: [{ start: '14:00', end: '18:00' }] }
                ]
            }
        };

        localStorage.setItem('tempo_confirmed_plan', JSON.stringify(plan));
        localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
        sessionStorage.removeItem('tempo_active_shared_tool');

        if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
            await window.TempoAuth.checkSession();
        }

        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
            window.TempoEmergencyFlow.setConfirmedPlan(plan);
        }

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
    print("Seed result:", seed_res)
    time.sleep(1)

    print("\n--- TEST 1: VERIFY EXACT DATE LABEL IN VIETNAMESE (VI) ---")
    vi_date_data = eval_js("""
    (() => {
        const nextPlannedWorkBox = document.querySelector('[data-tempo-ui="urgent-task-now"] .p-3\\\\.5');
        const dateElement = nextPlannedWorkBox ? nextPlannedWorkBox.querySelector('.font-bold.text-sm') : null;
        const rawText = dateElement ? dateElement.innerText.trim() : null;
        const html = dateElement ? dateElement.innerHTML : null;

        return {
            rawText,
            html,
            hasMojibakeA: rawText ? rawText.includes('Â') : false,
            charCodes: rawText ? Array.from(rawText).map(c => ({ char: c, code: c.charCodeAt(0), hex: 'U+' + c.charCodeAt(0).toString(16).toUpperCase().padStart(4, '0') })) : []
        };
    })()
    """)
    print("Vietnamese Date Label Info:", json.dumps(vi_date_data, ensure_ascii=False, indent=2))

    # Strict Assertions for VI
    assert vi_date_data['rawText'] == 'Ngày mai · 14:00', f"Expected 'Ngày mai · 14:00', got '{vi_date_data['rawText']}'"
    assert not vi_date_data['hasMojibakeA'], f"Unintended 'Â' character detected in '{vi_date_data['rawText']}'!"
    assert vi_date_data['html'] == 'Ngày mai · 14:00', f"Expected clean HTML 'Ngày mai · 14:00', got '{vi_date_data['html']}'"
    print(">>> PASS: 'Ngày mai · 14:00' renders cleanly without any 'Â' mojibake!")

    capture_screenshot("work_done_date_encoding_vi.png")

    print("\n--- TEST 2: SWITCH TO ENGLISH (EN) WITHOUT RELOAD ---")
    eval_js("window.TempoI18n.setLanguage('en');")
    time.sleep(0.5)

    en_date_data = eval_js("""
    (() => {
        const nextPlannedWorkBox = document.querySelector('[data-tempo-ui="urgent-task-now"] .p-3\\\\.5');
        const dateElement = nextPlannedWorkBox ? nextPlannedWorkBox.querySelector('.font-bold.text-sm') : null;
        const rawText = dateElement ? dateElement.innerText.trim() : null;
        const html = dateElement ? dateElement.innerHTML : null;

        return {
            rawText,
            html,
            hasMojibakeA: rawText ? rawText.includes('Â') : false,
            charCodes: rawText ? Array.from(rawText).map(c => ({ char: c, code: c.charCodeAt(0), hex: 'U+' + c.charCodeAt(0).toString(16).toUpperCase().padStart(4, '0') })) : []
        };
    })()
    """)
    print("English Date Label Info:", json.dumps(en_date_data, ensure_ascii=False, indent=2))

    # Strict Assertions for EN
    assert en_date_data['rawText'] == 'Tomorrow · 14:00', f"Expected 'Tomorrow · 14:00', got '{en_date_data['rawText']}'"
    assert not en_date_data['hasMojibakeA'], f"Unintended 'Â' character detected in '{en_date_data['rawText']}'!"
    assert en_date_data['html'] == 'Tomorrow · 14:00', f"Expected clean HTML 'Tomorrow · 14:00', got '{en_date_data['html']}'"
    print(">>> PASS: 'Tomorrow · 14:00' renders cleanly without any 'Â' mojibake!")

    capture_screenshot("work_done_date_encoding_en.png")

    print("\n--- TEST 3: FULL PAGE RELOAD PERSISTENCE (EN & VI) ---")
    eval_js("window.__reloading_test = true;")
    send_cmd("Page.reload")
    for _ in range(30):
        time.sleep(0.5)
        ready = eval_js("document.readyState === 'complete' && !!window.TempoMode && !!window.TempoI18n && window.__reloading_test === undefined")
        if ready:
            break
    time.sleep(1)

    eval_js("""
    (async () => {
        if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
            await window.TempoAuth.checkSession();
        }
        if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
            window.TempoMode.renderActiveModeHome();
        }
    })()
    """)
    time.sleep(0.5)

    en_reload_text = eval_js("document.querySelector('[data-tempo-ui=\"urgent-task-now\"] .p-3\\\\.5 .font-bold.text-sm')?.innerText?.trim()")
    print("EN Reload text:", en_reload_text)
    assert en_reload_text == 'Tomorrow · 14:00'

    eval_js("window.TempoI18n.setLanguage('vi');")
    time.sleep(0.5)
    eval_js("window.__reloading_test = true;")
    send_cmd("Page.reload")
    for _ in range(30):
        time.sleep(0.5)
        ready = eval_js("document.readyState === 'complete' && !!window.TempoMode && !!window.TempoI18n && window.__reloading_test === undefined")
        if ready:
            break
    time.sleep(1)

    eval_js("""
    (async () => {
        if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
            await window.TempoAuth.checkSession();
        }
        if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
            window.TempoMode.renderActiveModeHome();
        }
    })()
    """)
    time.sleep(0.5)

    vi_reload_text = eval_js("document.querySelector('[data-tempo-ui=\"urgent-task-now\"] .p-3\\\\.5 .font-bold.text-sm')?.innerText?.trim()")
    print("VI Reload text:", vi_reload_text)
    assert vi_reload_text == 'Ngày mai · 14:00'
    print(">>> PASS: Both languages persist cleanly across full browser reload!")

    print("\n=====================================================================")
    print("ALL TESTS PASSED! ZERO MOJIBAKE OR DOUBLE-ENCODED CHARACTERS FOUND.")
    print("=====================================================================")

finally:
    if ws:
        try:
            ws.close()
        except Exception:
            pass
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except Exception:
        pass
