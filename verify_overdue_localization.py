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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_overdue_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9505

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
    print("STEP 1: SEED PLAN WITH AN OVERDUE TASK IN VIETNAMESE (VI)")
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
        const overdueDateStr = '2026-10-31';

        const plan = {
            id: 'plan_test_overdue',
            createdDate: overdueDateStr,
            updatedAt: new Date().toISOString(),
            status: 'active',
            tasks: [
                {
                    id: 'task_overdue_1',
                    title: 'Báo cáo tổng kết dự án',
                    name: 'Báo cáo tổng kết dự án',
                    estimatedMinutes: 60,
                    completed: false,
                    hasDeadline: true,
                    deadlineDate: overdueDateStr,
                    deadlineTime: '17:00',
                    scheduledDate: overdueDateStr
                }
            ],
            plannedTasks: [
                {
                    id: 'pt_overdue_1',
                    dayDate: overdueDateStr,
                    startTime: '14:00',
                    endTime: '16:00',
                    task: {
                        id: 'task_overdue_1',
                        title: 'Báo cáo tổng kết dự án',
                        name: 'Báo cáo tổng kết dự án',
                        estimatedMinutes: 60,
                        completed: false,
                        hasDeadline: true,
                        deadlineDate: overdueDateStr,
                        deadlineTime: '17:00'
                    }
                }
            ],
            availability: {
                selectedDays: [overdueDateStr, todayStr],
                days: [
                    { date: overdueDateStr, blocks: [{ start: '14:00', end: '18:00' }] },
                    { date: todayStr, blocks: [{ start: '09:00', end: '17:00' }] }
                ]
            }
        };

        localStorage.setItem('tempo_confirmed_plan', JSON.stringify(plan));
        localStorage.setItem('tempo_confirmed_plan_dev_user_1', JSON.stringify(plan));
        localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
        localStorage.setItem('tempo_plan_workspace_plan_dev_user_1', JSON.stringify(plan));
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

        return { mode: 'emergency', lang: window.TempoI18n ? window.TempoI18n.getLanguage() : null };
    })()
    """)
    print("Seed result:", seed_res)

    time.sleep(1)

    print("\n--- TEST 1: VERIFY OVERDUE TASK UI IN VIETNAMESE (VI) ---")
    card_info_vi = eval_js("""
    (() => {
        const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
        if (!card) return { found: false };

        // 1. Status heading
        const headingBadge = card.querySelector('.bg-amber-600.text-white');
        const headingText = headingBadge ? headingBadge.textContent.trim() : null;

        // 2. Main overdue message
        const titleEl = card.querySelector('h3.font-heading');
        const titleText = titleEl ? titleEl.textContent.trim() : null;

        // 3. Supporting description
        const descEl = card.querySelector('p.italic');
        const descText = descEl ? descEl.textContent.trim() : null;

        // 4. OVERDUE badge
        const overdueBadge = card.querySelector('.bg-amber-100.text-amber-800');
        const badgeText = overdueBadge ? overdueBadge.textContent.trim() : null;

        // 5 & 6. Info box row (Scheduled date & Deadline)
        const infoRow = card.querySelector('.bg-white\\\\/90 .text-stone-500');
        const infoSpans = infoRow ? Array.from(infoRow.querySelectorAll('span')).map(s => s.textContent.trim()) : [];

        // 7. Clear this task button
        const clearBtn = card.querySelector('button[onclick*="promptClearOverdueTask"]');
        const clearText = clearBtn ? clearBtn.textContent.trim() : null;

        // 8. Mark as done button
        const doneBtn = card.querySelector('button[onclick*="markOverdueTaskDone"] span:last-child');
        const doneText = doneBtn ? doneBtn.textContent.trim() : null;

        // 9. Edit task button
        const editBtn = card.querySelector('button[onclick*="selectTask"] span:last-child');
        const editText = editBtn ? editBtn.textContent.trim() : null;

        return {
            found: true,
            headingText,
            titleText,
            descText,
            badgeText,
            infoSpans,
            clearText,
            doneText,
            editText
        };
    })()
    """)

    print("Vietnamese Overdue Card Info:", json.dumps(card_info_vi, indent=2, ensure_ascii=False))

    # Assert Vietnamese copy matches approved strings
    assert card_info_vi["found"], "Overdue task card not found!"
    assert card_info_vi["headingText"] == "TASK TRỄ DEADLINE", f"Expected 'TASK TRỄ DEADLINE', got '{card_info_vi['headingText']}'"
    assert card_info_vi["titleText"] == "Task này đã trễ Deadline", f"Expected 'Task này đã trễ Deadline', got '{card_info_vi['titleText']}'"
    assert card_info_vi["descText"] == "Task này đã trễ deadline. Bạn muốn xóa, đánh dấu hoàn thành hay cập nhật lại?", f"Expected approved desc, got '{card_info_vi['descText']}'"
    assert card_info_vi["badgeText"] == "TRỄ DEADLINE", f"Expected 'TRỄ DEADLINE', got '{card_info_vi['badgeText']}'"
    assert any("Ngày lên lịch:" in s and "31/10/2026" in s for s in card_info_vi["infoSpans"]), f"Expected scheduled date in infoSpans: {card_info_vi['infoSpans']}"
    assert any("Deadline:" in s and "31/10/2026" in s for s in card_info_vi["infoSpans"]), f"Expected deadline in infoSpans: {card_info_vi['infoSpans']}"
    assert card_info_vi["clearText"] == "Xóa task này", f"Expected 'Xóa task này', got '{card_info_vi['clearText']}'"
    assert card_info_vi["doneText"] == "Hoàn thành", f"Expected 'Hoàn thành', got '{card_info_vi['doneText']}'"
    assert card_info_vi["editText"] == "Chỉnh sửa task", f"Expected 'Chỉnh sửa task', got '{card_info_vi['editText']}'"
    print(">>> PASS: All 9 Vietnamese strings match approved translations perfectly!")

    capture_screenshot("overdue_task_ui_vi.png")

    print("\n--- TEST 2: SWITCH TO ENGLISH (EN) DYNAMICALLY ---")
    eval_js("window.TempoI18n.setLanguage('en');")
    time.sleep(1)

    card_info_en = eval_js("""
    (() => {
        const card = document.querySelector('[data-tempo-ui="urgent-task-now"]');
        if (!card) return { found: false };

        const headingBadge = card.querySelector('.bg-amber-600.text-white');
        const headingText = headingBadge ? headingBadge.textContent.trim() : null;

        const titleEl = card.querySelector('h3.font-heading');
        const titleText = titleEl ? titleEl.textContent.trim() : null;

        const descEl = card.querySelector('p.italic');
        const descText = descEl ? descEl.textContent.trim() : null;

        const overdueBadge = card.querySelector('.bg-amber-100.text-amber-800');
        const badgeText = overdueBadge ? overdueBadge.textContent.trim() : null;

        const infoRow = card.querySelector('.bg-white\\\\/90 .text-stone-500');
        const infoSpans = infoRow ? Array.from(infoRow.querySelectorAll('span')).map(s => s.textContent.trim()) : [];

        const clearBtn = card.querySelector('button[onclick*="promptClearOverdueTask"]');
        const clearText = clearBtn ? clearBtn.textContent.trim() : null;

        const doneBtn = card.querySelector('button[onclick*="markOverdueTaskDone"] span:last-child');
        const doneText = doneBtn ? doneBtn.textContent.trim() : null;

        const editBtn = card.querySelector('button[onclick*="selectTask"] span:last-child');
        const editText = editBtn ? editBtn.textContent.trim() : null;

        return {
            found: true,
            headingText,
            titleText,
            descText,
            badgeText,
            infoSpans,
            clearText,
            doneText,
            editText
        };
    })()
    """)

    print("English Overdue Card Info:", json.dumps(card_info_en, indent=2, ensure_ascii=False))

    # Assert English copy matches approved strings
    assert card_info_en["found"], "Overdue task card not found in EN!"
    assert card_info_en["headingText"] == "TASK OVERDUE", f"Expected 'TASK OVERDUE', got '{card_info_en['headingText']}'"
    assert card_info_en["titleText"] == "This task is overdue", f"Expected 'This task is overdue', got '{card_info_en['titleText']}'"
    assert card_info_en["descText"] == "Looks like this task has passed its due date. Would you like to clear it, mark it as done, or update it?", f"Expected approved desc, got '{card_info_en['descText']}'"
    assert card_info_en["badgeText"] == "OVERDUE", f"Expected 'OVERDUE', got '{card_info_en['badgeText']}'"
    assert any("Scheduled:" in s and "Oct 31, 2026" in s for s in card_info_en["infoSpans"]), f"Expected scheduled date in infoSpans: {card_info_en['infoSpans']}"
    assert any("Deadline:" in s and "Oct 31, 2026" in s for s in card_info_en["infoSpans"]), f"Expected deadline in infoSpans: {card_info_en['infoSpans']}"
    assert card_info_en["clearText"] == "Clear this task", f"Expected 'Clear this task', got '{card_info_en['clearText']}'"
    assert card_info_en["doneText"] == "Mark as done", f"Expected 'Mark as done', got '{card_info_en['doneText']}'"
    assert card_info_en["editText"] == "Edit task", f"Expected 'Edit task', got '{card_info_en['editText']}'"
    print(">>> PASS: All 9 English strings match approved translations perfectly!")

    capture_screenshot("overdue_task_ui_en.png")

    print("\n--- TEST 3: FULL PAGE RELOAD PERSISTENCE (EN & VI) ---")
    send_cmd("Page.reload")
    time.sleep(2)

    en_reload_heading = eval_js("document.querySelector('[data-tempo-ui=\"urgent-task-now\"] .bg-amber-600.text-white')?.textContent.trim()")
    print("EN Reload Heading:", en_reload_heading)
    assert en_reload_heading == "TASK OVERDUE", f"Expected 'TASK OVERDUE' after reload, got '{en_reload_heading}'"

    eval_js("window.TempoI18n.setLanguage('vi');")
    time.sleep(0.5)
    send_cmd("Page.reload")
    time.sleep(2)

    vi_reload_heading = eval_js("document.querySelector('[data-tempo-ui=\"urgent-task-now\"] .bg-amber-600.text-white')?.textContent.trim()")
    print("VI Reload Heading:", vi_reload_heading)
    assert vi_reload_heading == "TASK TRỄ DEADLINE", f"Expected 'TASK TRỄ DEADLINE' after reload, got '{vi_reload_heading}'"
    print(">>> PASS: Full reload persistence verified in both EN and VI!")

    print("\n--- TEST 4: PLAN WORKSPACE OVERDUE BADGES ---")
    eval_js("window.TempoApp.navigateTo('plan-workspace');")
    time.sleep(1)

    # In VI
    pw_vi_badge = eval_js("""
    (() => {
        const badges = Array.from(document.querySelectorAll('.bg-amber-100.text-amber-800')).map(b => b.textContent.trim());
        return badges;
    })()
    """)
    print("Plan Workspace Badges (VI):", pw_vi_badge)
    assert "TRỄ DEADLINE" in pw_vi_badge, f"Expected 'TRỄ DEADLINE' badge in Plan Workspace, got {pw_vi_badge}"

    # In EN
    eval_js("window.TempoI18n.setLanguage('en');")
    time.sleep(1)
    pw_en_badge = eval_js("""
    (() => {
        const badges = Array.from(document.querySelectorAll('.bg-amber-100.text-amber-800')).map(b => b.textContent.trim());
        return badges;
    })()
    """)
    print("Plan Workspace Badges (EN):", pw_en_badge)
    assert "OVERDUE" in pw_en_badge, f"Expected 'OVERDUE' badge in Plan Workspace, got {pw_en_badge}"
    print(">>> PASS: Plan Workspace overdue badge localized cleanly in both VI and EN!")

    print("\n=====================================================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("=====================================================================")

finally:
    try:
        if ws:
            ws.close()
    except:
        pass
    proc.terminate()
