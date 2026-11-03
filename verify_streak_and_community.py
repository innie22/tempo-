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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_streak_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9498

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1200",
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
    print("STEP 1: SEED URGENT PLAN, 3 SELF-CHECK TRACKERS & VIETNAMESE (VI) LOCALE")
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
        localStorage.setItem('tempo_selfcheck_streak_count', '3');
        localStorage.setItem('tempo_selfcheck_streak_count_dev_user_1', '3');

        // Seed 3 trackers
        const trackers = [
            { id: 'trk_tension', name: 'Mức độ căng cơ', category: 'stress_sign', check_method: 'percentage', status: 'active', archived: false },
            { id: 'trk_headache', name: 'Đau đầu âm ỉ', category: 'stress_sign', check_method: 'percentage', status: 'active', archived: false },
            { id: 'trk_walk', name: 'Đi dạo hít thở', category: 'supportive', check_method: 'percentage', status: 'active', archived: false }
        ];
        localStorage.setItem('tempo_selfcheck_trackers_dev_user_1', JSON.stringify(trackers));
        localStorage.setItem('tempo_selfcheck_trackers_local_user', JSON.stringify(trackers));
        localStorage.setItem('tempo_selfcheck_trackers', JSON.stringify(trackers));

        // Clear observations
        const todayStr = window.TempoI18n ? window.TempoI18n.getLocalTodayISO() : '2026-11-01';
        localStorage.removeItem(`tempo_selfcheck_obs_dev_user_1_${todayStr}`);
        localStorage.removeItem(`tempo_selfcheck_obs_${todayStr}`);
        localStorage.removeItem('tempo_selfcheck_checkins_dev_user_1');
        localStorage.removeItem('tempo_selfcheck_checkins_local_user');
        localStorage.removeItem('tempo_selfcheck_checkins');
        localStorage.removeItem('tempo_selfcheck_observations_dev_user_1');
        localStorage.removeItem('tempo_selfcheck_observations_local_user');
        localStorage.removeItem('tempo_selfcheck_observations');
        sessionStorage.removeItem('tempo_umode_skipped_trackers');

        const plan = {
            id: 'plan_test_streak',
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
                    scheduledEnd: '15:00'
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
                        deadlineTime: '18:00'
                    }
                }
            ],
            availability: {
                selectedDays: [todayStr],
                days: [{ date: todayStr, blocks: [{ start: '14:00', end: '18:00' }] }]
            }
        };

        localStorage.setItem('tempo_confirmed_plan', JSON.stringify(plan));
        sessionStorage.removeItem('tempo_active_shared_tool');

        if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
            await window.TempoAuth.checkSession();
        }

        if (window.TempoMode) {
            window.TempoMode.transitionContext('emergency');
            window.TempoMode.renderActiveModeHome();
        }

        return {
            uid: window.TempoAuth ? window.TempoAuth.getCurrentUserId() : null,
            mode: window.TempoMode ? window.TempoMode.getActiveContext() : null,
            lang: window.TempoI18n ? window.TempoI18n.getLanguage() : null
        };
    })()
    """)
    print("Seed result:", seed_res)
    time.sleep(1)

    # Scroll down to ensure both streak card and community section are visible
    eval_js("""
    (() => {
        const streakEl = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
        if (streakEl) {
            streakEl.scrollIntoView({ behavior: 'instant', block: 'center' });
        }
    })()
    """)
    time.sleep(0.5)

    print("\n--- TEST 1: VERIFY VIETNAMESE (VI) STRINGS ---")
    vi_data = eval_js("""
    (() => {
        const streakCard = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
        const streakHeading = streakCard ? streakCard.querySelector('h3')?.innerText?.trim() : null;
        const streakSummary = streakCard ? streakCard.querySelector('[data-tempo-ui="streak-card-summary"]')?.innerText?.trim() : null;
        const streakSkipBtn = streakCard ? streakCard.querySelector('[data-tempo-ui="streak-card-skip-btn"]')?.innerText?.trim() : null;
        const streakSaveBtn = streakCard ? streakCard.querySelector('#btn-umode-save-percentage')?.innerText?.trim() : null;
        const streakBtn1 = streakCard ? streakCard.querySelector('[data-tempo-ui="streak-card-btn1"]')?.innerText?.trim() : null;
        const streakBtn2 = streakCard ? streakCard.querySelector('[data-tempo-ui="streak-card-btn2"]')?.innerText?.trim() : null;

        const commSection = document.querySelector('[data-tempo-ui="urgent-posts"]');
        const commHeading = commSection ? commSection.querySelector('h3')?.innerText?.trim() : null;
        const commTimeStamps = Array.from(document.querySelectorAll('#urgent-community-posts-list span.text-xs.text-\\\\[\\\\#8E8A85\\\\]')).map(el => el.innerText.trim());

        return {
            streakHeading,
            streakSummary,
            streakSkipBtn,
            streakSaveBtn,
            streakBtn1,
            streakBtn2,
            commHeading,
            commTimeStamps
        };
    })()
    """)
    print("Vietnamese UI Data:", json.dumps(vi_data, ensure_ascii=False, indent=2))

    # Assertions for VI
    assert vi_data['streakHeading'] == 'Chuỗi Self-check 🔥', f"Expected 'Chuỗi Self-check 🔥', got {vi_data['streakHeading']}"
    assert vi_data['streakSummary'] == 'Bạn đã check 0/3 mục hôm nay.', f"Expected 'Bạn đã check 0/3 mục hôm nay.', got {vi_data['streakSummary']}"
    assert vi_data['streakSkipBtn'] == 'Bỏ qua', f"Expected 'Bỏ qua', got {vi_data['streakSkipBtn']}"
    assert vi_data['streakSaveBtn'] == 'Lưu', f"Expected 'Lưu', got {vi_data['streakSaveBtn']}"
    assert vi_data['streakBtn1'] == 'Xem check-in hôm nay', f"Expected 'Xem check-in hôm nay', got {vi_data['streakBtn1']}"
    assert vi_data['streakBtn2'] == 'Sửa tracking', f"Expected 'Sửa tracking', got {vi_data['streakBtn2']}"
    assert vi_data['commHeading'] == 'Cộng đồng Tempo', f"Expected 'Cộng đồng Tempo', got {vi_data['commHeading']}"
    assert '2 giờ trước' in vi_data['commTimeStamps'], f"Expected '2 giờ trước' in timestamps, got {vi_data['commTimeStamps']}"
    assert '5 giờ trước' in vi_data['commTimeStamps'], f"Expected '5 giờ trước' in timestamps, got {vi_data['commTimeStamps']}"
    print(">>> ALL VIETNAMESE (VI) STRINGS MATCH 100%!")

    capture_screenshot("streak_community_vi.png")

    print("\n--- TEST 2: DYNAMIC CHECK-IN COUNT UPDATE (0/3 -> 1/3) ---")
    update_res = eval_js("""
    (() => {
        // Confirm percentage on current tracker
        if (window.TempoMode && typeof window.TempoMode.confirmUmodePercentage === 'function') {
            window.TempoMode.confirmUmodePercentage('trk_tension');
        }
        const streakCard = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
        const summary = streakCard ? streakCard.querySelector('[data-tempo-ui="streak-card-summary"]')?.innerText?.trim() : null;
        return { summary };
    })()
    """)
    print("After check-in 1 tracker:", update_res)
    assert update_res['summary'] == 'Bạn đã check 1/3 mục hôm nay.', f"Expected 'Bạn đã check 1/3 mục hôm nay.', got {update_res['summary']}"
    print(">>> DYNAMIC CHECK-IN COUNT SUCCESSFULLY UPDATED TO 1/3 IN VIETNAMESE!")

    print("\n--- TEST 3: DYNAMIC SWITCH TO ENGLISH (EN) WITHOUT RELOAD ---")
    eval_js("window.TempoI18n.setLanguage('en');")
    time.sleep(0.5)

    en_data = eval_js("""
    (() => {
        const streakCard = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
        const streakHeading = streakCard ? streakCard.querySelector('h3')?.innerText?.trim() : null;
        const streakSummary = streakCard ? streakCard.querySelector('[data-tempo-ui="streak-card-summary"]')?.innerText?.trim() : null;
        const streakSkipBtn = streakCard ? streakCard.querySelector('[data-tempo-ui="streak-card-skip-btn"]')?.innerText?.trim() : null;
        const streakSaveBtn = streakCard ? streakCard.querySelector('#btn-umode-save-percentage')?.innerText?.trim() : null;
        const streakBtn1 = streakCard ? streakCard.querySelector('[data-tempo-ui="streak-card-btn1"]')?.innerText?.trim() : null;
        const streakBtn2 = streakCard ? streakCard.querySelector('[data-tempo-ui="streak-card-btn2"]')?.innerText?.trim() : null;

        const commSection = document.querySelector('[data-tempo-ui="urgent-posts"]');
        const commHeading = commSection ? commSection.querySelector('h3')?.innerText?.trim() : null;
        const commTimeStamps = Array.from(document.querySelectorAll('#urgent-community-posts-list span.text-xs.text-\\\\[\\\\#8E8A85\\\\]')).map(el => el.innerText.trim());

        return {
            streakHeading,
            streakSummary,
            streakSkipBtn,
            streakSaveBtn,
            streakBtn1,
            streakBtn2,
            commHeading,
            commTimeStamps
        };
    })()
    """)
    print("English UI Data:", json.dumps(en_data, ensure_ascii=False, indent=2))

    # Assertions for EN
    print("EN Summary text:", en_data['streakSummary'])
    print("EN Heading text:", en_data['streakHeading'])
    print("EN Comm Heading text:", en_data['commHeading'])
    assert en_data['streakHeading'] == 'Your Self-check Streak 🔥', f"Expected 'Your Self-check Streak 🔥', got {en_data['streakHeading']}"
    assert en_data['streakSummary'] == 'You checked in on 1 of 3 things.', f"Expected 'You checked in on 1 of 3 things.', got {en_data['streakSummary']}"
    assert en_data['streakSkipBtn'] == 'Skip', f"Expected 'Skip', got {en_data['streakSkipBtn']}"
    assert en_data['streakSaveBtn'] == 'Save', f"Expected 'Save', got {en_data['streakSaveBtn']}"
    assert en_data['streakBtn1'] == "View today's checkin", f"Expected 'View today\'s checkin', got {en_data['streakBtn1']}"
    assert en_data['streakBtn2'] == 'Edit tracking system', f"Expected 'Edit tracking system', got {en_data['streakBtn2']}"
    assert en_data['commHeading'] == 'From the Tempo Community', f"Expected 'From the Tempo Community', got {en_data['commHeading']}"
    assert '2 hours ago' in en_data['commTimeStamps'], f"Expected '2 hours ago' in timestamps, got {en_data['commTimeStamps']}"
    assert '5 hours ago' in en_data['commTimeStamps'], f"Expected '5 hours ago' in timestamps, got {en_data['commTimeStamps']}"
    print(">>> ALL ENGLISH (EN) STRINGS MATCH 100% AFTER IMMEDIATE SWITCH!")

    capture_screenshot("streak_community_en.png")

    # Debug what is stored in localStorage before reload
    debug_storage = eval_js("""
    (() => {
        return {
            uid: window.TempoAuth ? window.TempoAuth.getCurrentUserId() : null,
            dev_chk: localStorage.getItem('tempo_selfcheck_checkins_dev_user_1'),
            dev_obs: localStorage.getItem('tempo_selfcheck_observations_dev_user_1'),
            local_chk: localStorage.getItem('tempo_selfcheck_checkins_local_user'),
            local_obs: localStorage.getItem('tempo_selfcheck_observations_local_user'),
            fallback_chk: localStorage.getItem('tempo_selfcheck_checkins'),
            fallback_obs: localStorage.getItem('tempo_selfcheck_observations')
        };
    })()
    """)
    print("Storage before reload:", json.dumps(debug_storage, indent=2))

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
        const streakEl = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
        if (streakEl) {
            streakEl.scrollIntoView({ behavior: 'instant', block: 'center' });
        }
    })()
    """)
    time.sleep(0.5)

    en_reload_data = eval_js("""
    (() => {
        const streakCard = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
        const streakHeading = streakCard ? streakCard.querySelector('h3')?.innerText?.trim() : null;
        const streakSummary = streakCard ? streakCard.querySelector('[data-tempo-ui="streak-card-summary"]')?.innerText?.trim() : null;
        const streakSkipBtn = streakCard ? streakCard.querySelector('[data-tempo-ui="streak-card-skip-btn"]')?.innerText?.trim() : null;
        const streakSaveBtn = streakCard ? streakCard.querySelector('#btn-umode-save-percentage')?.innerText?.trim() : null;
        const streakBtn1 = streakCard ? streakCard.querySelector('[data-tempo-ui="streak-card-btn1"]')?.innerText?.trim() : null;
        const streakBtn2 = streakCard ? streakCard.querySelector('[data-tempo-ui="streak-card-btn2"]')?.innerText?.trim() : null;

        const commSection = document.querySelector('[data-tempo-ui="urgent-posts"]');
        const commHeading = commSection ? commSection.querySelector('h3')?.innerText?.trim() : null;
        const commTimeStamps = Array.from(document.querySelectorAll('#urgent-community-posts-list span.text-xs.text-\\\\[\\\\#8E8A85\\\\]')).map(el => el.innerText.trim());

        return {
            lang: window.TempoI18n ? window.TempoI18n.getLanguage() : null,
            streakHeading,
            streakSummary,
            streakSkipBtn,
            streakSaveBtn,
            streakBtn1,
            streakBtn2,
            commHeading,
            commTimeStamps
        };
    })()
    """)
    print("English After Reload Data:", json.dumps(en_reload_data, ensure_ascii=False, indent=2))
    debug_reload_storage = eval_js("""
    (() => {
        return {
            uid: window.TempoAuth ? window.TempoAuth.getCurrentUserId() : null,
            dev_chk: localStorage.getItem('tempo_selfcheck_checkins_dev_user_1'),
            dev_obs: localStorage.getItem('tempo_selfcheck_observations_dev_user_1'),
            local_chk: localStorage.getItem('tempo_selfcheck_checkins_local_user'),
            local_obs: localStorage.getItem('tempo_selfcheck_observations_local_user'),
            fallback_chk: localStorage.getItem('tempo_selfcheck_checkins'),
            fallback_obs: localStorage.getItem('tempo_selfcheck_observations'),
            activeContext: window.TempoMode ? window.TempoMode.getActiveContext() : null,
            todayCheckin: window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTodayCheckin === 'function' ? window.TempoRecoverySelfCheck.getTodayCheckin() : null
        };
    })()
    """)
    print("Storage after reload:", json.dumps(debug_reload_storage, indent=2))
    assert en_reload_data['lang'] == 'en', f"Expected lang 'en', got {en_reload_data['lang']}"
    assert en_reload_data['streakHeading'] == 'Your Self-check Streak 🔥'
    assert en_reload_data['streakSummary'] == 'You checked in on 1 of 3 things.'
    assert en_reload_data['streakSkipBtn'] == 'Skip'
    assert en_reload_data['streakSaveBtn'] == 'Save'
    assert en_reload_data['streakBtn1'] == "View today's checkin"
    assert en_reload_data['streakBtn2'] == 'Edit tracking system'
    assert en_reload_data['commHeading'] == 'From the Tempo Community'
    assert '2 hours ago' in en_reload_data['commTimeStamps']
    assert '5 hours ago' in en_reload_data['commTimeStamps']
    print(">>> ENGLISH (EN) PERSISTENCE VERIFIED 100% AFTER FULL PAGE RELOAD!")

    print("\n--- TEST 5: SWITCH BACK TO VIETNAMESE & RELOAD PERSISTENCE ---")
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
        const streakEl = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
        if (streakEl) {
            streakEl.scrollIntoView({ behavior: 'instant', block: 'center' });
        }
    })()
    """)
    time.sleep(0.5)

    vi_reload_data = eval_js("""
    (() => {
        const streakCard = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
        const streakHeading = streakCard ? streakCard.querySelector('h3')?.innerText?.trim() : null;
        const streakSummary = streakCard ? streakCard.querySelector('[data-tempo-ui="streak-card-summary"]')?.innerText?.trim() : null;
        const streakSkipBtn = streakCard ? streakCard.querySelector('[data-tempo-ui="streak-card-skip-btn"]')?.innerText?.trim() : null;
        const streakSaveBtn = streakCard ? streakCard.querySelector('#btn-umode-save-percentage')?.innerText?.trim() : null;
        const streakBtn1 = streakCard ? streakCard.querySelector('[data-tempo-ui="streak-card-btn1"]')?.innerText?.trim() : null;
        const streakBtn2 = streakCard ? streakCard.querySelector('[data-tempo-ui="streak-card-btn2"]')?.innerText?.trim() : null;

        const commSection = document.querySelector('[data-tempo-ui="urgent-posts"]');
        const commHeading = commSection ? commSection.querySelector('h3')?.innerText?.trim() : null;
        const commTimeStamps = Array.from(document.querySelectorAll('#urgent-community-posts-list span.text-xs.text-\\\\[\\\\#8E8A85\\\\]')).map(el => el.innerText.trim());

        return {
            lang: window.TempoI18n ? window.TempoI18n.getLanguage() : null,
            streakHeading,
            streakSummary,
            streakSkipBtn,
            streakSaveBtn,
            streakBtn1,
            streakBtn2,
            commHeading,
            commTimeStamps
        };
    })()
    """)
    print("Vietnamese After Reload Data:", json.dumps(vi_reload_data, ensure_ascii=False, indent=2))
    assert vi_reload_data['lang'] == 'vi', f"Expected lang 'vi', got {vi_reload_data['lang']}"
    assert vi_reload_data['streakHeading'] == 'Chuỗi Self-check 🔥'
    assert vi_reload_data['streakSummary'] == 'Bạn đã check 1/3 mục hôm nay.'
    assert vi_reload_data['streakSkipBtn'] == 'Bỏ qua'
    assert vi_reload_data['streakSaveBtn'] == 'Lưu'
    assert vi_reload_data['streakBtn1'] == 'Xem check-in hôm nay'
    assert vi_reload_data['streakBtn2'] == 'Sửa tracking'
    assert vi_reload_data['commHeading'] == 'Cộng đồng Tempo'
    assert '2 giờ trước' in vi_reload_data['commTimeStamps']
    assert '5 giờ trước' in vi_reload_data['commTimeStamps']
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
