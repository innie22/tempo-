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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_wdm_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9501

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
    print("STEP 1: SEED URGENT PLAN (TODAY TASK DONE + TOMORROW TASK PENDING) IN VI")
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
            id: 'plan_test_work_done',
            createdDate: todayStr,
            updatedAt: new Date().toISOString(),
            status: 'active',
            tasks: [
                {
                    id: 'task_today_math',
                    title: 'Ôn tập Giải tích 1',
                    estimatedMinutes: 60,
                    completed: true,
                    hasDeadline: true,
                    deadlineDate: todayStr,
                    deadlineTime: '18:00',
                    scheduledDate: todayStr
                },
                {
                    id: 'task_tomorrow_philosophy',
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
                    startTime: '14:00',
                    endTime: '15:00',
                    task: {
                        id: 'task_today_math',
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
                    task: {
                        id: 'task_tomorrow_philosophy',
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
                    { date: todayStr, blocks: [{ start: '14:00', end: '18:00' }] },
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

    print("\n--- TEST 1: VERIFY VIETNAMESE (VI) STRINGS ---")
    vi_data = eval_js("""
    (() => {
        const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
        if (!card) return null;

        const badge = card.querySelector('.bg-emerald-700')?.innerText?.trim();
        const heading = card.querySelector('h3')?.innerText?.trim();
        const desc = card.querySelector('p.italic')?.innerText?.trim();
        const nextPlannedWorkBox = card.querySelector('.p-3\\\\.5');
        const nextWorkLabel = nextPlannedWorkBox ? nextPlannedWorkBox.querySelector('span.text-\\\\[10px\\\\]')?.innerText?.trim() : null;
        const tomorrowLabel = nextPlannedWorkBox ? nextPlannedWorkBox.querySelector('.font-bold.text-sm')?.innerText?.trim() : null;
        const tomorrowTaskName = nextPlannedWorkBox ? nextPlannedWorkBox.querySelector('p.text-\\\\[11px\\\\]')?.innerText?.trim() : null;
        const previewBtn = nextPlannedWorkBox ? nextPlannedWorkBox.querySelector('button')?.innerText?.trim() : null;
        const buttons = Array.from(card.querySelectorAll('.pt-4 button')).map(b => b.innerText.trim());

        return {
            badge,
            heading,
            desc,
            nextWorkLabel,
            tomorrowLabel,
            tomorrowTaskName,
            previewBtn,
            buttons
        };
    })()
    """)
    print("Vietnamese UI Data:", json.dumps(vi_data, ensure_ascii=False, indent=2))

    assert vi_data is not None, "Today's Work Done card/modal was not rendered!"
    assert vi_data['badge'] == 'ĐÃ HOÀN THÀNH CÔNG VIỆC HÔM NAY', f"Expected 'ĐÃ HOÀN THÀNH CÔNG VIỆC HÔM NAY', got '{vi_data['badge']}'"
    assert vi_data['heading'] == 'Vậy là hôm nay bạn đã hoàn thành mọi việc! 🎉', f"Expected 'Vậy là hôm nay bạn đã hoàn thành mọi việc! 🎉', got '{vi_data['heading']}'"
    assert vi_data['desc'] == 'Bạn đã hoàn thành các công việc hôm nay. Bạn có muốn bắt đầu trước một chút cho ngày mai hay nghỉ ngơi tại đây?', f"Expected approved description, got '{vi_data['desc']}'"
    assert vi_data['nextWorkLabel'] == 'CÔNG VIỆC TIẾP THEO:', f"Expected 'CÔNG VIỆC TIẾP THEO:', got '{vi_data['nextWorkLabel']}'"
    assert vi_data['tomorrowLabel'] == 'Ngày mai', f"Expected 'Ngày mai', got '{vi_data['tomorrowLabel']}'"
    assert vi_data['tomorrowTaskName'] == 'Tiểu luận Triết học Mác - Lênin', f"Expected dynamic task name, got '{vi_data['tomorrowTaskName']}'"
    assert vi_data['previewBtn'] == 'Xem trước kế hoạch ngày mai →', f"Expected 'Xem trước kế hoạch ngày mai →', got '{vi_data['previewBtn']}'"
    assert 'Bắt đầu công việc ngày mai →' in vi_data['buttons'], f"Expected 'Bắt đầu công việc ngày mai →' in buttons, got {vi_data['buttons']}"
    assert 'Tôi sẽ nghỉ ngơi lúc này' in vi_data['buttons'], f"Expected 'Tôi sẽ nghỉ ngơi lúc này' in buttons, got {vi_data['buttons']}"
    print(">>> ALL VIETNAMESE (VI) STRINGS MATCH APPROVED SPECIFICATION 100%!")

    capture_screenshot("work_done_modal_vi.png")

    print("\n--- TEST 2: VERIFY ACTION BUTTON BEHAVIORS ---")
    # Click Preview tomorrow
    eval_js("window.TempoMode.showTomorrowTaskInCard();")
    time.sleep(0.5)
    tomorrow_view = eval_js("""
    (() => {
        const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
        const badge = card ? card.querySelector('.bg-\\\\[\\\\#D79277\\\\]')?.innerText?.trim() : null;
        const restBtn = card ? card.querySelector('.pt-4 button:last-child')?.innerText?.trim() : null;
        return { badge, restBtn };
    })()
    """)
    print("Tomorrow preview card state:", tomorrow_view)
    assert tomorrow_view['restBtn'] == 'Tôi sẽ nghỉ ngơi lúc này', f"Expected rest button to be localized in tomorrow view, got '{tomorrow_view['restBtn']}'"

    # Click Rest for now
    eval_js("window.TempoMode.setRestingForToday(true);")
    time.sleep(0.5)
    resting_view = eval_js("""
    (() => {
        const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
        const badge = card ? card.querySelector('.bg-emerald-700')?.innerText?.trim() : null;
        const heading = card ? card.querySelector('h3')?.innerText?.trim() : null;
        const actionBtn = card ? card.querySelector('.pt-4 button:first-child')?.innerText?.trim() : null;
        return { badge, heading, actionBtn };
    })()
    """)
    print("Resting card state:", resting_view)
    assert resting_view['badge'] == 'ĐÃ HOÀN THÀNH CÔNG VIỆC HÔM NAY'
    assert resting_view['heading'] == 'Vậy là hôm nay bạn đã hoàn thành mọi việc! 🎉'
    assert resting_view['actionBtn'] == 'Bắt đầu công việc ngày mai →'

    # Reset back to overview
    eval_js("window.TempoMode.setRestingForToday(false);")
    time.sleep(0.5)
    print(">>> ACTION BUTTON BEHAVIORS VERIFIED SUCCESSFULLY!")

    print("\n--- TEST 3: DYNAMIC SWITCH TO ENGLISH (EN) WITHOUT RELOAD ---")
    eval_js("window.TempoI18n.setLanguage('en');")
    time.sleep(0.5)

    en_data = eval_js("""
    (() => {
        const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
        if (!card) return null;

        const badge = card.querySelector('.bg-emerald-700')?.innerText?.trim();
        const heading = card.querySelector('h3')?.innerText?.trim();
        const desc = card.querySelector('p.italic')?.innerText?.trim();
        const nextPlannedWorkBox = card.querySelector('.p-3\\\\.5');
        const nextWorkLabel = nextPlannedWorkBox ? nextPlannedWorkBox.querySelector('span.text-\\\\[10px\\\\]')?.innerText?.trim() : null;
        const tomorrowLabel = nextPlannedWorkBox ? nextPlannedWorkBox.querySelector('.font-bold.text-sm')?.innerText?.trim() : null;
        const tomorrowTaskName = nextPlannedWorkBox ? nextPlannedWorkBox.querySelector('p.text-\\\\[11px\\\\]')?.innerText?.trim() : null;
        const previewBtn = nextPlannedWorkBox ? nextPlannedWorkBox.querySelector('button')?.innerText?.trim() : null;
        const buttons = Array.from(card.querySelectorAll('.pt-4 button')).map(b => b.innerText.trim());

        return {
            badge,
            heading,
            desc,
            nextWorkLabel,
            tomorrowLabel,
            tomorrowTaskName,
            previewBtn,
            buttons
        };
    })()
    """)
    print("English UI Data:", json.dumps(en_data, ensure_ascii=False, indent=2))

    assert en_data['badge'] == "TODAY'S WORK DONE", f"Expected \"TODAY'S WORK DONE\", got '{en_data['badge']}'"
    assert en_data['heading'] == "You're all done for today! 🎉", f"Expected \"You're all done for today! 🎉\", got '{en_data['heading']}'"
    assert en_data['desc'] == "You've made it through today's tasks. Want to get a head start on tomorrow, or call it a day?", f"Expected English description, got '{en_data['desc']}'"
    assert en_data['nextWorkLabel'] == "NEXT PLANNED WORK:", f"Expected 'NEXT PLANNED WORK:', got '{en_data['nextWorkLabel']}'"
    assert en_data['tomorrowLabel'] == "Tomorrow", f"Expected 'Tomorrow', got '{en_data['tomorrowLabel']}'"
    assert en_data['tomorrowTaskName'] == "Tiểu luận Triết học Mác - Lênin", f"Expected dynamic task name preserved, got '{en_data['tomorrowTaskName']}'"
    assert en_data['previewBtn'] == "Preview tomorrow →", f"Expected 'Preview tomorrow →', got '{en_data['previewBtn']}'"
    assert "Let's do tomorrow's task →" in en_data['buttons'], f"Expected \"Let's do tomorrow's task →\" in buttons, got {en_data['buttons']}"
    assert "I'll rest for now" in en_data['buttons'], f"Expected \"I'll rest for now\" in buttons, got {en_data['buttons']}"
    print(">>> ALL ENGLISH (EN) STRINGS MATCH APPROVED SPECIFICATION 100%!")

    capture_screenshot("work_done_modal_en.png")

    print("\n--- TEST 4: BROWSER RELOAD PERSISTENCE (EN) ---")
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

    en_reload_data = eval_js("""
    (() => {
        const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
        if (!card) return null;

        const badge = card.querySelector('.bg-emerald-700')?.innerText?.trim();
        const heading = card.querySelector('h3')?.innerText?.trim();
        const desc = card.querySelector('p.italic')?.innerText?.trim();
        const nextPlannedWorkBox = card.querySelector('.p-3\\\\.5');
        const nextWorkLabel = nextPlannedWorkBox ? nextPlannedWorkBox.querySelector('span.text-\\\\[10px\\\\]')?.innerText?.trim() : null;
        const tomorrowLabel = nextPlannedWorkBox ? nextPlannedWorkBox.querySelector('.font-bold.text-sm')?.innerText?.trim() : null;
        const previewBtn = nextPlannedWorkBox ? nextPlannedWorkBox.querySelector('button')?.innerText?.trim() : null;
        const buttons = Array.from(card.querySelectorAll('.pt-4 button')).map(b => b.innerText.trim());

        return {
            lang: window.TempoI18n ? window.TempoI18n.getLanguage() : null,
            badge,
            heading,
            desc,
            nextWorkLabel,
            tomorrowLabel,
            previewBtn,
            buttons
        };
    })()
    """)
    print("English After Reload Data:", json.dumps(en_reload_data, ensure_ascii=False, indent=2))
    assert en_reload_data['lang'] == 'en'
    assert en_reload_data['badge'] == "TODAY'S WORK DONE"
    assert en_reload_data['heading'] == "You're all done for today! 🎉"
    assert en_reload_data['desc'] == "You've made it through today's tasks. Want to get a head start on tomorrow, or call it a day?"
    assert en_reload_data['nextWorkLabel'] == "NEXT PLANNED WORK:"
    assert en_reload_data['tomorrowLabel'] == "Tomorrow"
    assert en_reload_data['previewBtn'] == "Preview tomorrow →"
    assert "Let's do tomorrow's task →" in en_reload_data['buttons']
    assert "I'll rest for now" in en_reload_data['buttons']
    print(">>> ENGLISH (EN) PERSISTENCE VERIFIED 100% AFTER FULL PAGE RELOAD!")

    print("\n--- TEST 5: SWITCH BACK TO VIETNAMESE & RELOAD PERSISTENCE (VI) ---")
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

    vi_reload_data = eval_js("""
    (() => {
        const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
        if (!card) return null;

        const badge = card.querySelector('.bg-emerald-700')?.innerText?.trim();
        const heading = card.querySelector('h3')?.innerText?.trim();
        const desc = card.querySelector('p.italic')?.innerText?.trim();
        const nextPlannedWorkBox = card.querySelector('.p-3\\\\.5');
        const nextWorkLabel = nextPlannedWorkBox ? nextPlannedWorkBox.querySelector('span.text-\\\\[10px\\\\]')?.innerText?.trim() : null;
        const tomorrowLabel = nextPlannedWorkBox ? nextPlannedWorkBox.querySelector('.font-bold.text-sm')?.innerText?.trim() : null;
        const previewBtn = nextPlannedWorkBox ? nextPlannedWorkBox.querySelector('button')?.innerText?.trim() : null;
        const buttons = Array.from(card.querySelectorAll('.pt-4 button')).map(b => b.innerText.trim());

        return {
            lang: window.TempoI18n ? window.TempoI18n.getLanguage() : null,
            badge,
            heading,
            desc,
            nextWorkLabel,
            tomorrowLabel,
            previewBtn,
            buttons
        };
    })()
    """)
    print("Vietnamese After Reload Data:", json.dumps(vi_reload_data, ensure_ascii=False, indent=2))
    assert vi_reload_data['lang'] == 'vi'
    assert vi_reload_data['badge'] == 'ĐÃ HOÀN THÀNH CÔNG VIỆC HÔM NAY'
    assert vi_reload_data['heading'] == 'Vậy là hôm nay bạn đã hoàn thành mọi việc! 🎉'
    assert vi_reload_data['desc'] == 'Bạn đã hoàn thành các công việc hôm nay. Bạn có muốn bắt đầu trước một chút cho ngày mai hay nghỉ ngơi tại đây?'
    assert vi_reload_data['nextWorkLabel'] == 'CÔNG VIỆC TIẾP THEO:'
    assert vi_reload_data['tomorrowLabel'] == 'Ngày mai'
    assert vi_reload_data['previewBtn'] == 'Xem trước kế hoạch ngày mai →'
    assert 'Bắt đầu công việc ngày mai →' in vi_reload_data['buttons']
    assert 'Tôi sẽ nghỉ ngơi lúc này' in vi_reload_data['buttons']
    print(">>> VIETNAMESE (VI) PERSISTENCE VERIFIED 100% AFTER FULL PAGE RELOAD!")

    print("\n=====================================================================")
    print("ALL 5 TESTS PASSED WITH 100% ACCURACY!")
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
