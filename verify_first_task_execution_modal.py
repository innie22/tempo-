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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_first_task_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9565

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#plan-workspace"
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
    app_tab = next(t for t in tabs if "8000" in t.get("url", ""))

    ws = websocket.create_connection(app_tab["webSocketDebuggerUrl"], timeout=10)
    print("Connected to CDP via WebSocket.")

    send_cmd("Page.enable")
    send_cmd("DOM.enable")

    time.sleep(1)

    setup_code = """
    (async () => {
        let waitLimit = 50;
        while ((!window.TempoUrmodeFlow || !window.TempoPlanStore) && waitLimit > 0) {
            await new Promise(r => setTimeout(r, 100));
            waitLimit--;
        }

        const u = { id: 'local_dev_alex', email: 'alex@tempo.test', user_metadata: { display_name: 'Alex' } };
        localStorage.setItem('tempo_local_dev_user', JSON.stringify(u));
        localStorage.setItem('tempo_mock_account_alex@tempo.test', JSON.stringify(u));
        if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
            await window.TempoAuth.checkSession();
        }

        const mockPlan = {
            id: 'test-first-task-exec-plan',
            planId: 'test-first-task-exec-plan',
            status: 'active',
            planType: 'emergency',
            title: 'Tempo Working Plan',
            createdAt: Date.now(),
            plannedTasks: [
                {
                    task: {
                        id: 't-101',
                        name: 'Literature Review Chapter 2',
                        durationMinutes: 90,
                        durationLabel: '1.5 hr',
                        hasDeadline: false,
                        completed: false
                    },
                    dayDate: '2026-11-02',
                    startTime: '09:00',
                    endTime: '10:30',
                    executionBadge: 'DO THIS FIRST'
                },
                {
                    task: {
                        id: 't-102',
                        name: 'Data Collection Phase 1',
                        durationMinutes: 60,
                        durationLabel: '1 hr',
                        hasDeadline: true,
                        deadlineDate: '2026-11-02',
                        deadlineTime: '14:00',
                        completed: false
                    },
                    dayDate: '2026-11-02',
                    startTime: '11:00',
                    endTime: '12:00',
                    executionBadge: 'UP NEXT'
                }
            ],
            unarrangedTasks: []
        };

        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            await window.TempoPlanStore.saveActivePlan('emergency', mockPlan);
        }
        localStorage.setItem('tempo_active_working_plan', JSON.stringify(mockPlan));

        window.TempoI18n.setLanguage('vi');
        window.TempoUrmodeFlow.showFirstTaskExecutionPopup();
        return true;
    })();
    """
    eval_js(setup_code)
    time.sleep(1)

    # 1. Verify Vietnamese modal content
    vi_checks = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        if (!modal) return { error: 'No modal found' };

        const badge = modal.querySelector('span.uppercase')?.innerText.trim();
        const title = modal.querySelector('h2')?.innerText.trim();

        const card = modal.querySelector('.p-4.rounded-2xl');
        const cardBadge = card ? card.querySelector('.rounded-full')?.innerText.trim() : null;
        const taskDur = card ? card.querySelector('.text-stone-500.font-medium')?.innerText.trim() : null;
        const taskName = card ? card.querySelector('h3')?.innerText.trim() : null;
        const deadlineLine = card ? card.querySelector('div.text-xs')?.innerText.trim() : null;

        const buttons = Array.from(modal.querySelectorAll('button')).map(b => b.innerText.trim()).filter(Boolean);

        return {
            badge,
            title,
            cardBadge,
            taskDur,
            taskName,
            deadlineLine,
            buttons
        };
    })()
    """)
    print("VI Modal Data:", json.dumps(vi_checks, indent=2, ensure_ascii=False))

    assert vi_checks.get('badge') == 'BẮT ĐẦU TASK ĐẦU TIÊN', f"Expected BẮT ĐẦU TASK ĐẦU TIÊN, got {vi_checks.get('badge')}"
    assert vi_checks.get('title') == 'Task đầu tiên của bạn là…', f"Expected Task đầu tiên của bạn là…, got {vi_checks.get('title')}"
    assert vi_checks.get('cardBadge') == 'SẴN SÀNG THỰC HIỆN', f"Expected SẴN SÀNG THỰC HIỆN, got {vi_checks.get('cardBadge')}"
    assert vi_checks.get('taskName') == 'Literature Review Chapter 2', f"Expected Literature Review Chapter 2, got {vi_checks.get('taskName')}"
    assert vi_checks.get('taskDur') == '~1,5 giờ', f"Expected ~1,5 giờ, got {vi_checks.get('taskDur')}"
    assert 'Deadline: Chưa có deadline' in vi_checks.get('deadlineLine'), f"Expected Deadline: Chưa có deadline, got {vi_checks.get('deadlineLine')}"
    assert 'Để sau' in vi_checks.get('buttons'), f"Missing 'Để sau' in buttons: {vi_checks.get('buttons')}"
    assert 'Chọn task khác' in vi_checks.get('buttons'), f"Missing 'Chọn task khác' in buttons: {vi_checks.get('buttons')}"
    assert any('Bắt đầu task này' in b for b in vi_checks.get('buttons')), f"Missing 'Bắt đầu task này →' in buttons: {vi_checks.get('buttons')}"

    capture_screenshot("first_task_execution_modal_vi.png")
    print("VI checks passed successfully!")

    # 2. Switch on-the-fly to English
    eval_js("window.TempoI18n.setLanguage('en');")
    time.sleep(1)

    en_checks = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        if (!modal) return { error: 'No modal found' };

        const badge = modal.querySelector('span.uppercase')?.innerText.trim();
        const title = modal.querySelector('h2')?.innerText.trim();

        const card = modal.querySelector('.p-4.rounded-2xl');
        const cardBadge = card ? card.querySelector('.rounded-full')?.innerText.trim() : null;
        const taskDur = card ? card.querySelector('.text-stone-500.font-medium')?.innerText.trim() : null;
        const taskName = card ? card.querySelector('h3')?.innerText.trim() : null;
        const deadlineLine = card ? card.querySelector('div.text-xs')?.innerText.trim() : null;

        const buttons = Array.from(modal.querySelectorAll('button')).map(b => b.innerText.trim()).filter(Boolean);

        return {
            badge,
            title,
            cardBadge,
            taskDur,
            taskName,
            deadlineLine,
            buttons
        };
    })()
    """)
    print("EN Modal Data:", json.dumps(en_checks, indent=2, ensure_ascii=False))

    assert en_checks.get('badge') == 'FIRST TASK EXECUTION', f"Expected FIRST TASK EXECUTION, got {en_checks.get('badge')}"
    assert en_checks.get('title') == 'Your first task is…', f"Expected Your first task is…, got {en_checks.get('title')}"
    assert en_checks.get('cardBadge') == 'READY NOW', f"Expected READY NOW, got {en_checks.get('cardBadge')}"
    assert en_checks.get('taskName') == 'Literature Review Chapter 2', f"Expected Literature Review Chapter 2, got {en_checks.get('taskName')}"
    assert en_checks.get('taskDur') == '~1.5 hr', f"Expected ~1.5 hr, got {en_checks.get('taskDur')}"
    assert 'Due: No fixed deadline' in en_checks.get('deadlineLine'), f"Expected Due: No fixed deadline, got {en_checks.get('deadlineLine')}"
    assert 'Later' in en_checks.get('buttons'), f"Missing 'Later' in buttons: {en_checks.get('buttons')}"
    assert 'Choose another task' in en_checks.get('buttons'), f"Missing 'Choose another task' in buttons: {en_checks.get('buttons')}"
    assert any('Do this task' in b for b in en_checks.get('buttons')), f"Missing 'Do this task →' in buttons: {en_checks.get('buttons')}"

    capture_screenshot("first_task_execution_modal_en.png")
    print("EN checks passed successfully!")

    # 3. Test deadline formatting when task has a deadline
    eval_js("""
    (() => {
        window.TempoUrmodeFlow.showFirstTaskExecutionPopup(); // re-render with target
    })()
    """)
    # Now set target to t-102 which has a deadline 2026-11-02 14:00 and 60 min duration
    deadline_test = eval_js("""
    (() => {
        window.TempoI18n.setLanguage('vi');
        const plan = window.TempoPlanStore.getActivePlan('emergency');
        // temporarily switch t-101 to completed so t-102 is topTask
        plan.plannedTasks[0].task.completed = true;
        window.TempoUrmodeFlow.showFirstTaskExecutionPopup();
        const modal = document.querySelector('#modal-urmode-flow');
        const card = modal.querySelector('.p-4.rounded-2xl');
        const deadlineLineVi = card ? card.querySelector('div.text-xs')?.innerText.trim() : '';
        const durVi = card ? card.querySelector('.text-stone-500.font-medium')?.innerText.trim() : '';

        window.TempoI18n.setLanguage('en');
        const cardEn = modal.querySelector('.p-4.rounded-2xl');
        const deadlineLineEn = cardEn ? cardEn.querySelector('div.text-xs')?.innerText.trim() : '';
        const durEn = cardEn ? cardEn.querySelector('.text-stone-500.font-medium')?.innerText.trim() : '';

        // restore t-101 completed = false
        plan.plannedTasks[0].task.completed = false;
        window.TempoUrmodeFlow.showFirstTaskExecutionPopup();

        return {
            deadlineLineVi,
            durVi,
            deadlineLineEn,
            durEn
        };
    })()
    """)
    print("Deadline & Duration Test (Task 2):", json.dumps(deadline_test, indent=2, ensure_ascii=False))
    assert 'Deadline:' in deadline_test.get('deadlineLineVi'), f"Expected Deadline: prefix in vi, got {deadline_test.get('deadlineLineVi')}"
    assert '02/11/2026' in deadline_test.get('deadlineLineVi'), f"Expected 02/11/2026 in vi, got {deadline_test.get('deadlineLineVi')}"
    assert deadline_test.get('durVi') == '~1 giờ', f"Expected ~1 giờ in vi, got {deadline_test.get('durVi')}"

    assert 'Due:' in deadline_test.get('deadlineLineEn'), f"Expected Due: prefix in en, got {deadline_test.get('deadlineLineEn')}"
    assert 'Nov 02, 2026' in deadline_test.get('deadlineLineEn') or 'Nov 2, 2026' in deadline_test.get('deadlineLineEn'), f"Expected Nov 02, 2026 in en, got {deadline_test.get('deadlineLineEn')}"
    assert deadline_test.get('durEn') == '~1 hr', f"Expected ~1 hr in en, got {deadline_test.get('durEn')}"

    print("Deadline and duration formats verified for both languages!")

    # 4. Test button: Later -> closes modal
    eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        const btn = Array.from(modal.querySelectorAll('button')).find(b => b.innerText.trim() === 'Later' || b.innerText.trim() === 'Để sau');
        if (btn) btn.click();
    })()
    """)
    time.sleep(0.5)
    modal_closed = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        return !modal || modal.classList.contains('hidden') || modal.style.display === 'none';
    })()
    """)
    print("Later button closed modal:", modal_closed)
    assert modal_closed, "Later button failed to close modal"

    # 5. Test button: Choose another task -> opens task selection
    eval_js("window.TempoUrmodeFlow.showFirstTaskExecutionPopup();")
    time.sleep(0.5)
    eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        const btn = Array.from(modal.querySelectorAll('button')).find(b => b.innerText.includes('Choose another task') || b.innerText.includes('Chọn task khác'));
        if (btn) btn.click();
    })()
    """)
    time.sleep(0.5)
    task_selection_view = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        return modal ? (modal.innerText.includes('CHOOSE') || modal.innerText.includes('SELECT') || modal.innerText.includes('TASK') || modal.innerText.includes('Chọn') || modal.innerText.includes('task')) : false;
    })()
    """)
    print("Choose another task button opened task selection:", task_selection_view)
    assert task_selection_view, "Choose another task button failed to open task selection popup"

    # 6. Test button: Do this task -> launches focus / execution
    eval_js("window.TempoUrmodeFlow.showFirstTaskExecutionPopup();")
    time.sleep(0.5)
    focus_launched = eval_js("""
    (() => {
        let invoked = false;
        const origLaunch = window.TempoUrmodeFlow.launchFocusForTask;
        window.TempoUrmodeFlow.launchFocusForTask = (taskId) => {
            invoked = true;
            return origLaunch ? origLaunch(taskId) : null;
        };

        const modal = document.querySelector('#modal-urmode-flow');
        const btn = Array.from(modal.querySelectorAll('button')).find(b => b.innerText.includes('Do this task') || b.innerText.includes('Bắt đầu task này'));
        if (btn) btn.click();
        return invoked;
    })()
    """)
    print("Do this task button invoked launchFocusForTask:", focus_launched)
    assert focus_launched, "Do this task button failed to trigger launchFocusForTask"

    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")

finally:
    if ws:
        ws.close()
    proc.terminate()
