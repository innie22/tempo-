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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_post_save_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9563

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

    # 1. Setup seed user and plan with top task having deadline 2026-11-02
    setup_code = """
    (async () => {
        const u = { id: 'local_dev_alex', email: 'alex@tempo.test', user_metadata: { display_name: 'Alex' } };
        localStorage.setItem('tempo_local_dev_user', JSON.stringify(u));
        localStorage.setItem('tempo_mock_account_alex@tempo.test', JSON.stringify(u));
        if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
            await window.TempoAuth.checkSession();
        }

        const tomorrowStr = '2026-11-02';

        const mockPlan = {
            id: 'test-post-save-plan',
            planId: 'test-post-save-plan',
            status: 'active',
            planType: 'emergency',
            title: 'Tempo Working Plan',
            createdAt: Date.now(),
            plannedTasks: [
                {
                    task: {
                        id: 'task-lead',
                        name: 'Literature Review Chapter 2',
                        deadlineDate: '2026-11-02',
                        deadlineTime: '14:00',
                        hasDeadline: true,
                        durationMinutes: 90,
                        durationLabel: '1.5h',
                        completed: false,
                        subtasks: []
                    },
                    dayDate: tomorrowStr,
                    startTime: '09:00',
                    endTime: '10:30',
                    executionBadge: 'DO THIS FIRST'
                }
            ],
            unarrangedTasks: [],
            availabilityDays: [
                { date: tomorrowStr, label: 'Tomorrow', blocks: [{ start: '08:00', end: '18:00', minutes: 600 }] }
            ]
        };
        mockPlan.tasks = mockPlan.plannedTasks.map(pt => pt.task);

        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            await window.TempoPlanStore.saveActivePlan('emergency', mockPlan);
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
            window.TempoEmergencyFlow.setConfirmedPlan(mockPlan);
        }
        localStorage.setItem('tempo_working_plan', JSON.stringify(mockPlan));

        window.TempoApp.navigateTo('plan-workspace');
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
            window.TempoPlanWorkspace.render();
        }

        // Set to Vietnamese mode
        window.TempoI18n.setLanguage('vi');

        // Trigger Plan Confirmed & Saved modal
        window.TempoUrmodeFlow.showTaskForNowPopupAfterSave(mockPlan);
    })()
    """
    eval_js(setup_code)
    time.sleep(1)

    # 2. Check Vietnamese Mode Elements
    vi_checks = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        const stepBadge = modal ? modal.querySelector('span.uppercase')?.innerText.trim() : '';
        const title = modal ? modal.querySelector('h2')?.innerText.trim() : '';

        // Highlight card elements
        const card = modal ? modal.querySelector('.p-4.rounded-2xl') : null;
        const cardBadge = card ? card.querySelector('span.rounded-full')?.innerText.trim() : '';
        const durText = card ? card.querySelector('.text-stone-500.font-medium')?.innerText.trim() : '';
        const taskName = card ? card.querySelector('h3')?.innerText.trim() : '';
        const dueSpan = card ? Array.from(card.querySelectorAll('span')).find(s => s.innerText && (s.innerText.includes('Deadline') || s.innerText.includes('Due'))) : null;
        const dueText = dueSpan ? dueSpan.innerText.trim() : '';

        // Question elements
        const questionTitle = modal ? modal.querySelector('h4')?.innerText.trim() : '';
        const questionDesc = modal ? modal.querySelector('p.text-xs.text-stone-500')?.innerText.trim() : '';

        // Buttons
        const bottomBtns = modal ? Array.from(modal.querySelectorAll('.pt-4 button')).map(b => b.innerText.trim()) : [];

        return {
            stepBadge,
            title,
            cardBadge,
            durText,
            taskName,
            dueText,
            questionTitle,
            questionDesc,
            bottomBtns
        };
    })()
    """)
    print("VI Checks Post-Save Modal:", json.dumps(vi_checks, indent=2, ensure_ascii=False))

    capture_screenshot("plan_confirmed_saved_modal_vi.png")

    # 3. Switch to English Mode on the fly
    print("\n--- Testing On-the-Fly Language Switch to English ---")
    eval_js("""
    (() => {
        window.TempoI18n.setLanguage('en');
    })()
    """)
    time.sleep(0.5)

    en_checks = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        const stepBadge = modal ? modal.querySelector('span.uppercase')?.innerText.trim() : '';
        const title = modal ? modal.querySelector('h2')?.innerText.trim() : '';

        // Highlight card elements
        const card = modal ? modal.querySelector('.p-4.rounded-2xl') : null;
        const cardBadge = card ? card.querySelector('span.rounded-full')?.innerText.trim() : '';
        const durText = card ? card.querySelector('.text-stone-500.font-medium')?.innerText.trim() : '';
        const taskName = card ? card.querySelector('h3')?.innerText.trim() : '';
        const dueSpan = card ? Array.from(card.querySelectorAll('span')).find(s => s.innerText && (s.innerText.includes('Deadline') || s.innerText.includes('Due'))) : null;
        const dueText = dueSpan ? dueSpan.innerText.trim() : '';

        // Question elements
        const questionTitle = modal ? modal.querySelector('h4')?.innerText.trim() : '';
        const questionDesc = modal ? modal.querySelector('p.text-xs.text-stone-500')?.innerText.trim() : '';

        // Buttons
        const bottomBtns = modal ? Array.from(modal.querySelectorAll('.pt-4 button')).map(b => b.innerText.trim()) : [];

        return {
            stepBadge,
            title,
            cardBadge,
            durText,
            taskName,
            dueText,
            questionTitle,
            questionDesc,
            bottomBtns
        };
    })()
    """)
    print("EN Checks Post-Save Modal:", json.dumps(en_checks, indent=2, ensure_ascii=False))

    capture_screenshot("plan_confirmed_saved_modal_en.png")

    # 4. Test Task with NO fixed deadline
    print("\n--- Testing Task with No Fixed Deadline ---")
    eval_js("""
    (() => {
        const noDeadlinePlan = {
            id: 'test-no-deadline-plan',
            planType: 'emergency',
            plannedTasks: [
                {
                    task: {
                        id: 'task-nodeadline',
                        name: 'Prepare Lab Safety Checklist',
                        hasDeadline: false,
                        deadlineDate: null,
                        durationMinutes: 45,
                        durationLabel: '45m',
                        completed: false
                    }
                }
            ]
        };
        noDeadlinePlan.tasks = noDeadlinePlan.plannedTasks.map(pt => pt.task);
        window.TempoI18n.setLanguage('vi');
        window.TempoUrmodeFlow.showTaskForNowPopupAfterSave(noDeadlinePlan);
    })()
    """)
    time.sleep(0.5)

    no_deadline_vi = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        const card = modal ? modal.querySelector('.p-4.rounded-2xl') : null;
        const dueSpan = card ? Array.from(card.querySelectorAll('span')).find(s => s.innerText && (s.innerText.includes('Deadline') || s.innerText.includes('Due'))) : null;
        return dueSpan ? dueSpan.innerText.trim() : null;
    })()
    """)
    print("VI No-deadline text:", no_deadline_vi)

    eval_js("""
    (() => {
        window.TempoI18n.setLanguage('en');
    })()
    """)
    time.sleep(0.5)

    no_deadline_en = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        const card = modal ? modal.querySelector('.p-4.rounded-2xl') : null;
        const dueSpan = card ? Array.from(card.querySelectorAll('span')).find(s => s.innerText && (s.innerText.includes('Deadline') || s.innerText.includes('Due'))) : null;
        return dueSpan ? dueSpan.innerText.trim() : null;
    })()
    """)
    print("EN No-deadline text:", no_deadline_en)

    # 5. Test Button Actions
    print("\n--- Testing Button 1: 'No, start working' ---")
    btn1_result = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        const btn1 = modal ? modal.querySelectorAll('.pt-4 button')[0] : null;
        if (btn1) {
            btn1.click();
            return true;
        }
        return false;
    })()
    """)
    time.sleep(0.5)
    print("Button 1 clicked:", btn1_result)

    print("\n--- Testing Button 2: 'Break down task →' ---")
    btn2_result = eval_js("""
    (() => {
        // Re-open post save modal
        const testPlan = {
            id: 'test-bd-plan',
            planType: 'emergency',
            plannedTasks: [
                {
                    task: {
                        id: 'task-for-breakdown',
                        name: 'Literature Review Chapter 2',
                        hasDeadline: true,
                        deadlineDate: '2026-11-02',
                        durationMinutes: 90
                    }
                }
            ]
        };
        testPlan.tasks = testPlan.plannedTasks.map(pt => pt.task);
        window.TempoUrmodeFlow.showTaskForNowPopupAfterSave(testPlan);

        const modal = document.querySelector('#modal-urmode-flow');
        const btn2 = modal ? modal.querySelectorAll('.pt-4 button')[1] : null;
        if (btn2) {
            btn2.click();
            // Should transition to step breakdown
            const newModal = document.querySelector('#modal-urmode-flow');
            return {
                clicked: true,
                newTitle: newModal ? (newModal.querySelector('h2') || newModal.querySelector('h3'))?.innerText.trim() : ''
            };
        }
        return { clicked: false };
    })()
    """)
    time.sleep(0.5)
    print("Button 2 clicked result:", json.dumps(btn2_result, indent=2, ensure_ascii=False))

    # Assertions
    # VI Assertions
    assert vi_checks['stepBadge'] == 'PLAN ĐÃ ĐƯỢC XÁC NHẬN & LƯU', f"VI stepBadge mismatch: {vi_checks['stepBadge']}"
    assert vi_checks['title'] == 'Task tiếp theo của bạn', f"VI title mismatch: {vi_checks['title']}"
    assert vi_checks['cardBadge'] == 'ƯU TIÊN LÀM TRƯỚC', f"VI cardBadge mismatch: {vi_checks['cardBadge']}"
    assert vi_checks['durText'] == '~1,5 giờ', f"VI durText mismatch: {vi_checks['durText']}"
    assert vi_checks['taskName'] == 'Literature Review Chapter 2', f"VI taskName mismatch: {vi_checks['taskName']}"
    assert 'Deadline: 02/11/2026' in vi_checks['dueText'], f"VI dueText mismatch: {vi_checks['dueText']}"
    assert vi_checks['questionTitle'] == 'Bạn có muốn chia nhỏ task này thành các bước dễ thực hiện hơn không?', f"VI questionTitle mismatch: {vi_checks['questionTitle']}"
    assert vi_checks['questionDesc'] == 'Chia task lớn thành những bước nhỏ từ 10–15 phút giúp bạn dễ bắt đầu hơn và tránh cảm giác quá tải.', f"VI questionDesc mismatch: {vi_checks['questionDesc']}"
    assert vi_checks['bottomBtns'] == ['Không, bắt đầu làm', 'Chia nhỏ task →'], f"VI bottomBtns mismatch: {vi_checks['bottomBtns']}"

    # EN Assertions
    assert en_checks['stepBadge'] == 'PLAN CONFIRMED & SAVED', f"EN stepBadge mismatch: {en_checks['stepBadge']}"
    assert en_checks['title'] == 'Your task for now', f"EN title mismatch: {en_checks['title']}"
    assert en_checks['cardBadge'] == 'DO THIS FIRST', f"EN cardBadge mismatch: {en_checks['cardBadge']}"
    assert en_checks['durText'] == '~1.5 hr', f"EN durText mismatch: {en_checks['durText']}"
    assert en_checks['taskName'] == 'Literature Review Chapter 2', f"EN taskName mismatch: {en_checks['taskName']}"
    assert 'Due: Nov 02, 2026' in en_checks['dueText'], f"EN dueText mismatch: {en_checks['dueText']}"
    assert en_checks['questionTitle'] == 'Would you like to break down this task into smaller steps?', f"EN questionTitle mismatch: {en_checks['questionTitle']}"
    assert en_checks['questionDesc'] == 'Breaking big tasks into 10–15 min steps prevents freeze and makes starting effortless.', f"EN questionDesc mismatch: {en_checks['questionDesc']}"
    assert en_checks['bottomBtns'] == ['No, start working', 'Break down task →'], f"EN bottomBtns mismatch: {en_checks['bottomBtns']}"

    # No deadline assertions
    assert 'Deadline: Chưa có deadline' in no_deadline_vi, f"VI no-deadline mismatch: {no_deadline_vi}"
    assert 'Due: No fixed deadline' in no_deadline_en, f"EN no-deadline mismatch: {no_deadline_en}"

    # Button actions assertions
    assert btn1_result is True, "Button 1 click failed"
    assert btn2_result['clicked'] is True, "Button 2 click failed"

    print("\nALL POST-SAVE MODAL VERIFICATIONS PASSED SUCCESSFULLY!")

finally:
    if ws:
        try:
            ws.close()
        except:
            pass
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except:
        proc.kill()
