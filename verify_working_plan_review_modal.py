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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_review_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9572

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#home"
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
        print(f"JS Exception: {res['exceptionDetails']}")
    return res.get("result", {}).get("value")

def take_screenshot(filename):
    res = send_cmd("Page.captureScreenshot", {"format": "png"})
    data = base64.b64decode(res.get("data", ""))
    target_path = os.path.join(artifact_dir, filename)
    with open(target_path, "wb") as f:
        f.write(data)
    print(f"Saved screenshot: {target_path}")

try:
    targets = None
    for _ in range(30):
        try:
            req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
            targets = json.loads(req.read().decode("utf-8"))
            if targets:
                break
        except Exception:
            time.sleep(0.5)

    if not targets:
        print("Failed to connect to browser targets.")
        sys.exit(1)

    page_target = next(t for t in targets if t.get("type") == "page")
    ws_url = page_target["webSocketDebuggerUrl"]
    ws = websocket.create_connection(ws_url)

    send_cmd("Page.enable")
    send_cmd("Runtime.enable")
    time.sleep(2)

    print("Browser loaded. Setting up Working Plan with 4 distinct status tasks (Overdue, Up Next, Then, Later)...")

    setup_script = """
    (() => {
        if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
            window.TempoMode.setMode('recovery');
        }

        const task1 = {
            id: 'task-rev-1',
            name: 'Submit CS101 Assignment 3',
            hasDeadline: true,
            deadlineDate: '2020-01-01',
            deadlineTime: '23:59',
            durationMinutes: 45,
            completed: false,
            executionBadge: 'OVERDUE'
        };
        const task2 = {
            id: 'task-rev-2',
            name: 'Finish Biology Lab Draft',
            hasDeadline: true,
            deadlineDate: '2020-01-02',
            deadlineTime: '17:00',
            durationMinutes: 30,
            completed: false,
            executionBadge: 'OVERDUE'
        };
        const task3 = {
            id: 'task-rev-3',
            name: 'Read History Chapter 5',
            hasDeadline: false,
            deadlineDate: null,
            durationMinutes: 60,
            completed: false,
            executionBadge: 'UP NEXT'
        };
        const task4 = {
            id: 'task-rev-4',
            name: 'Organize Math Practice Problems',
            hasDeadline: false,
            deadlineDate: null,
            durationMinutes: 25,
            completed: false,
            executionBadge: 'THEN'
        };
        const task5 = {
            id: 'task-rev-5',
            name: 'Clean Workspace & Tidy Desk',
            hasDeadline: false,
            deadlineDate: null,
            durationMinutes: 15,
            completed: false,
            executionBadge: 'LATER'
        };

        const mockPlan = {
            id: 'plan_rev_test',
            planType: 'emergency',
            title: 'Working Plan',
            plannedTasks: [
                { dayDate: '2020-01-01', task: task1, executionBadge: 'OVERDUE' },
                { dayDate: '2020-01-02', task: task2, executionBadge: 'OVERDUE' },
                { dayDate: '2026-11-02', task: task3, executionBadge: 'UP NEXT' },
                { dayDate: '2026-11-02', task: task4, executionBadge: 'THEN' },
                { dayDate: '2026-11-02', task: task5, executionBadge: 'LATER' }
            ],
            tasks: [task1, task2, task3, task4, task5]
        };

        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            window.TempoPlanStore.saveActivePlan('emergency', mockPlan);
        }
        try {
            localStorage.setItem('tempo_confirmed_plan', JSON.stringify(mockPlan));
            localStorage.setItem('tempo_active_plan_emergency', JSON.stringify(mockPlan));
        } catch(e) {}

        return 'Plan saved with 2 overdue tasks, UP NEXT, THEN, and LATER.';
    })()
    """
    res_setup = eval_js(setup_script)
    print(res_setup)

    # 1. TEST ENGLISH MODE
    print("\n--- 1. Testing English Mode ---")
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(0.5)
    eval_js("window.TempoUrmodeFlow.showReviewSummaryPopup()")
    time.sleep(0.5)

    extract_review_data = """
    (() => {
        const modal = document.getElementById('modal-urmode-flow');
        if (!modal || modal.classList.contains('hidden')) return null;

        const badge = modal.querySelector('span.tracking-widest')?.textContent.trim();
        const title = modal.querySelector('h2.font-heading')?.textContent.trim();
        const closeBtnTitle = modal.querySelector('button[title]')?.getAttribute('title');

        const warningBanner = modal.querySelector('div.bg-amber-50');
        const overdueCountHeader = warningBanner?.querySelector('strong')?.textContent.trim();
        const overdueDesc = warningBanner?.querySelector('span:not(.text-base)')?.textContent.trim();

        const taskRows = Array.from(modal.querySelectorAll('div.max-h-64 > div, div.max-h-72 > div')).map(row => {
            const name = row.querySelector('.font-bold.truncate')?.textContent.trim();
            const metaDiv = row.querySelector('.truncate')?.parentElement?.querySelector('div:last-child');
            const metaSpans = metaDiv ? Array.from(metaDiv.querySelectorAll('span')).map(s => s.textContent.trim()) : [];
            const badges = Array.from(row.querySelectorAll('.rounded-full')).map(s => s.textContent.trim());
            return { name, metaSpans, badges };
        });

        const buttons = Array.from(modal.querySelectorAll('div.pt-4 button')).map(b => b.textContent.trim());

        return {
            badge,
            title,
            closeBtnTitle,
            overdueCountHeader,
            overdueDesc,
            taskRows,
            buttons
        };
    })()
    """
    en_data = eval_js(extract_review_data)
    print("EN Working Plan Review Data:", json.dumps(en_data, ensure_ascii=False, indent=2))

    # Assertions for English
    assert en_data["badge"] == "WORKING PLAN REVIEW", f"Badge mismatch: '{en_data['badge']}'"
    assert en_data["title"] == "Your Working Plan Summary", f"Title mismatch: '{en_data['title']}'"
    assert en_data["overdueCountHeader"] == "2 tasks overdue:", f"Overdue header mismatch: '{en_data['overdueCountHeader']}'"
    assert en_data["overdueDesc"] == "Some tasks passed their planned date or deadline. You can keep them or adjust your schedule.", f"Overdue desc mismatch: '{en_data['overdueDesc']}'"

    # Check badges on task rows: OVERDUE, UP NEXT, THEN, LATER
    badges_found = [b for row in en_data["taskRows"] for b in row["badges"]]
    print("Found badges in EN:", badges_found)
    assert "OVERDUE" in badges_found, "Missing OVERDUE badge in English"
    assert "UP NEXT" in badges_found, "Missing UP NEXT badge in English"
    assert "THEN" in badges_found, "Missing THEN badge in English"
    assert "LATER" in badges_found, "Missing LATER badge in English"

    # Check "No fixed deadline"
    no_deadline_found = any(any("No fixed deadline" in s for s in row["metaSpans"]) for row in en_data["taskRows"])
    assert no_deadline_found, "Missing 'No fixed deadline' in English meta"

    # Check buttons
    assert en_data["buttons"][0] == "Adjust my plan", f"Adjust button mismatch: '{en_data['buttons'][0]}'"
    assert en_data["buttons"][1] == "Keep the plan →", f"Keep button mismatch: '{en_data['buttons'][1]}'"
    print(">>> All English assertions PASSED!")

    take_screenshot("working_plan_review_modal_en.png")

    # 2. TEST IN-PLACE SWITCH TO VIETNAMESE (Without reload)
    print("\n--- 2. Testing In-Place Switch to Vietnamese ---")
    eval_js("window.TempoI18n.setLanguage('vi')")
    time.sleep(0.5)

    vi_data = eval_js(extract_review_data)
    print("VI Working Plan Review Data:", json.dumps(vi_data, ensure_ascii=False, indent=2))

    # Assertions for Vietnamese
    assert vi_data["badge"] == "XEM LẠI PLAN", f"Badge mismatch: '{vi_data['badge']}'"
    assert vi_data["title"] == "Tổng quan kế hoạch làm việc", f"Title mismatch: '{vi_data['title']}'"
    assert vi_data["overdueCountHeader"] == "2 task đã quá hạn:", f"Overdue header mismatch: '{vi_data['overdueCountHeader']}'"
    assert vi_data["overdueDesc"] == "Một số task đã quá ngày lên lịch hoặc deadline. Bạn có thể giữ lại hoặc điều chỉnh lịch trình.", f"Overdue desc mismatch: '{vi_data['overdueDesc']}'"

    badges_found_vi = [b for row in vi_data["taskRows"] for b in row["badges"]]
    print("Found badges in VI:", badges_found_vi)
    assert "QUÁ HẠN" in badges_found_vi, "Missing QUÁ HẠN badge in Vietnamese"
    assert "TIẾP THEO" in badges_found_vi, "Missing TIẾP THEO badge in Vietnamese"
    assert "SAU ĐÓ" in badges_found_vi, "Missing SAU ĐÓ badge in Vietnamese"
    assert "ĐỂ SAU" in badges_found_vi, "Missing ĐỂ SAU badge in Vietnamese"

    no_deadline_found_vi = any(any("Chưa có deadline" in s for s in row["metaSpans"]) for row in vi_data["taskRows"])
    assert no_deadline_found_vi, "Missing 'Chưa có deadline' in Vietnamese meta"

    assert vi_data["buttons"][0] == "Điều chỉnh plan", f"Adjust button mismatch: '{vi_data['buttons'][0]}'"
    assert vi_data["buttons"][1] == "Giữ nguyên plan →", f"Keep button mismatch: '{vi_data['buttons'][1]}'"
    print(">>> All Vietnamese assertions PASSED!")

    take_screenshot("working_plan_review_modal_vi.png")

    # 3. TEST IN-PLACE SWITCH BACK TO ENGLISH
    print("\n--- 3. Testing In-Place Switch Back to English ---")
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(0.5)

    en_data_2 = eval_js(extract_review_data)
    assert en_data_2["badge"] == "WORKING PLAN REVIEW"
    assert en_data_2["title"] == "Your Working Plan Summary"
    assert en_data_2["buttons"][0] == "Adjust my plan"
    assert en_data_2["buttons"][1] == "Keep the plan →"
    print(">>> Switch back to English PASSED!")

    # 4. TEST BUTTON ACTIONS
    print("\n--- 4. Testing Action Buttons ---")
    # Test 1: Keep the plan →
    keep_test_script = """
    (() => {
        const keepBtn = document.querySelector('#modal-urmode-flow div.pt-4 button:last-child');
        keepBtn.click();
        const modal = document.getElementById('modal-urmode-flow');
        return {
            hasTaskForNow: modal ? modal.textContent.includes('YOUR TASK FOR NOW') || modal.textContent.includes('Your task for now is') : false
        };
    })()
    """
    keep_res = eval_js(keep_test_script)
    print("Keep plan click result (opened task for now):", keep_res.get("hasTaskForNow"))
    assert keep_res.get("hasTaskForNow") is True, "Failed to navigate to Keep Plan / Task For Now popup"
    print(">>> 'Keep the plan →' button action PASSED!")

    # Re-open Review Summary modal and test: Adjust my plan
    eval_js("window.TempoUrmodeFlow.showReviewSummaryPopup()")
    time.sleep(0.5)

    adjust_test_script = """
    (() => {
        const adjustBtn = document.querySelector('#modal-urmode-flow div.pt-4 button:first-child');
        adjustBtn.click();
        const modal = document.getElementById('modal-urmode-flow');
        return {
            hasStep1Keep: modal ? modal.textContent.includes('STEP 1 OF 3') || modal.textContent.includes('Choose tasks to keep') || modal.textContent.includes('BƯỚC 1/3') : false
        };
    })()
    """
    adjust_res = eval_js(adjust_test_script)
    print("Adjust plan click result (opened step 1 adjustment):", adjust_res.get("hasStep1Keep"))
    assert adjust_res.get("hasStep1Keep") is True, "Failed to navigate to Adjust Plan Step 1"
    print(">>> 'Adjust my plan' button action PASSED!")

    print("\n==========================================")
    print("ALL TESTS AND ASSERTIONS PASSED SUCCESSFULLY (100%)!")
    print("==========================================")

finally:
    if ws:
        try:
            ws.close()
        except Exception:
            pass
    if proc:
        try:
            proc.terminate()
        except Exception:
            pass
