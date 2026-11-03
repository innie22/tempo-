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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_step3_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9560

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

    # 1. Setup seed user and plan with 3 tasks
    setup_code = """
    (async () => {
        const u = { id: 'local_dev_alex', email: 'alex@tempo.test', user_metadata: { display_name: 'Alex' } };
        localStorage.setItem('tempo_local_dev_user', JSON.stringify(u));
        localStorage.setItem('tempo_mock_account_alex@tempo.test', JSON.stringify(u));
        if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
            await window.TempoAuth.checkSession();
        }

        const tomorrowStr = (window.TempoI18n && typeof window.TempoI18n.getLocalTomorrowISO === 'function')
            ? window.TempoI18n.getLocalTomorrowISO()
            : '2026-11-02';

        const mockPlan = {
            id: 'test-working-plan-step3',
            planId: 'test-working-plan-step3',
            status: 'active',
            planType: 'emergency',
            title: 'Tempo Working Plan',
            createdAt: Date.now(),
            plannedTasks: [
                {
                    task: {
                        id: 't-1',
                        name: 'Literature Review Chapter 2',
                        deadlineDate: '2026-10-31',
                        deadlineTime: '14:00',
                        hasDeadline: true,
                        durationMinutes: 60,
                        durationLabel: '1h',
                        completed: false,
                        subtasks: []
                    },
                    dayDate: tomorrowStr,
                    startTime: '09:00',
                    endTime: '10:00'
                },
                {
                    task: {
                        id: 't-2',
                        name: 'Submit Weekly Progress Report',
                        hasDeadline: false,
                        deadlineDate: null,
                        durationMinutes: 45,
                        durationLabel: '45m',
                        completed: false,
                        subtasks: []
                    },
                    dayDate: tomorrowStr,
                    startTime: '10:30',
                    endTime: '11:15'
                },
                {
                    task: {
                        id: 't-3',
                        name: 'Prepare Lab Safety Checklist',
                        deadlineDate: '2026-11-02',
                        deadlineTime: '17:00',
                        hasDeadline: true,
                        durationMinutes: 90,
                        durationLabel: '1.5h',
                        completed: false,
                        subtasks: []
                    },
                    dayDate: tomorrowStr,
                    startTime: '13:00',
                    endTime: '14:30'
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

        // Complete flow: Step 1 -> Step 2 (add task) -> Step 3
        window.TempoUrmodeFlow.startAdjustmentFlow();
        window.TempoUrmodeFlow.renderAdjustmentStep2Tasks();

        // Add a new task in Step 2: "Chemistry Study", 90 min (1.5h), due 2026-11-02
        const nameEl = document.getElementById('adjust-new-task-name');
        const dueEl = document.getElementById('adjust-new-task-due');
        const durEl = document.getElementById('adjust-new-task-dur');
        if (nameEl) nameEl.value = 'Chemistry Study';
        if (dueEl) {
            dueEl.value = '02/11/2026';
            window.TempoUrmodeFlow.handleStep2NewTaskDateInput(dueEl);
        }
        if (durEl) durEl.value = '90';
        window.TempoUrmodeFlow.addNewAdjustmentTask();

        // Advance to Step 3
        window.TempoUrmodeFlow.handleAdjustmentStep2Next();
    })()
    """
    eval_js(setup_code)
    time.sleep(1)

    # 2. Check Vietnamese Mode Step 3 Elements
    vi_checks = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow') || document.querySelector('.fixed.inset-0.z-50');
        const stepBadge = modal ? modal.querySelector('span.uppercase')?.innerText.trim() : '';
        const title = modal ? modal.querySelector('h2')?.innerText.trim() : '';
        const desc = modal ? modal.querySelector('p')?.innerText.trim() : '';

        // Tasks in proposal list
        const taskCards = modal ? Array.from(modal.querySelectorAll('.max-h-60 > div')) : [];
        const tasksData = taskCards.map(c => {
            const taskTitle = c.querySelector('.truncate')?.innerText.trim();
            const metaDiv = Array.from(c.querySelectorAll('div')).find(d => d.innerText && (d.innerText.includes('Deadline') || d.innerText.includes('Due') || d.innerText.includes('cố định') || d.innerText.includes('fixed')));
            const metaText = metaDiv ? metaDiv.innerText.trim() : '';
            const badge = c.querySelector('span.rounded-full')?.innerText.trim();
            return {
                title: taskTitle,
                meta: metaText,
                badge: badge
            };
        });

        const bottomBtns = modal ? Array.from(modal.querySelectorAll('.pt-4 button')).map(b => b.innerText.trim()) : [];

        return {
            stepBadge,
            title,
            desc,
            tasksData,
            bottomBtns
        };
    })()
    """)
    print("VI Checks Step 3:", json.dumps(vi_checks, indent=2, ensure_ascii=False))

    capture_screenshot("adjust_plan_step3_vi.png")

    # 3. Switch to English Mode on the fly
    print("\n--- Testing On-the-Fly Language Switch to English in Step 3 ---")
    eval_js("""
    (() => {
        window.TempoI18n.setLanguage('en');
    })()
    """)
    time.sleep(0.5)

    en_checks = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow') || document.querySelector('.fixed.inset-0.z-50');
        const stepBadge = modal ? modal.querySelector('span.uppercase')?.innerText.trim() : '';
        const title = modal ? modal.querySelector('h2')?.innerText.trim() : '';
        const desc = modal ? modal.querySelector('p')?.innerText.trim() : '';

        // Tasks in proposal list
        const taskCards = modal ? Array.from(modal.querySelectorAll('.max-h-60 > div')) : [];
        const tasksData = taskCards.map(c => {
            const taskTitle = c.querySelector('.truncate')?.innerText.trim();
            const metaDiv = Array.from(c.querySelectorAll('div')).find(d => d.innerText && (d.innerText.includes('Deadline') || d.innerText.includes('Due') || d.innerText.includes('cố định') || d.innerText.includes('fixed')));
            const metaText = metaDiv ? metaDiv.innerText.trim() : '';
            const badge = c.querySelector('span.rounded-full')?.innerText.trim();
            return {
                title: taskTitle,
                meta: metaText,
                badge: badge
            };
        });

        const bottomBtns = modal ? Array.from(modal.querySelectorAll('.pt-4 button')).map(b => b.innerText.trim()) : [];

        return {
            stepBadge,
            title,
            desc,
            tasksData,
            bottomBtns
        };
    })()
    """)
    print("EN Checks Step 3:", json.dumps(en_checks, indent=2, ensure_ascii=False))

    capture_screenshot("adjust_plan_step3_en.png")

    # 4. Test Navigation: Back button to Step 2
    print("\n--- Testing Navigation: Back button to Step 2 ---")
    eval_js("""
    (() => {
        window.TempoUrmodeFlow.renderAdjustmentStep2Tasks();
    })()
    """)
    time.sleep(0.5)

    step2_check = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow') || document.querySelector('.fixed.inset-0.z-50');
        return {
            stepBadge: modal ? modal.querySelector('span.uppercase')?.innerText.trim() : '',
            title: modal ? modal.querySelector('h2')?.innerText.trim() : ''
        };
    })()
    """)
    print("Step 2 return check:", json.dumps(step2_check, indent=2, ensure_ascii=False))

    # Advance back to Step 3
    eval_js("""
    (() => {
        window.TempoUrmodeFlow.handleAdjustmentStep2Next();
    })()
    """)
    time.sleep(0.5)

    # 5. Test Save updated plan functionality
    print("\n--- Testing Save updated plan ---")
    save_result = eval_js("""
    (() => {
        window.TempoUrmodeFlow.saveAdjustmentPlan();
        const confirmed = window.TempoEmergencyFlow ? window.TempoEmergencyFlow.getConfirmedPlan() : null;
        return {
            hasConfirmedPlan: Boolean(confirmed),
            taskCount: confirmed && confirmed.plannedTasks ? confirmed.plannedTasks.length : 0,
            taskTitles: confirmed && confirmed.plannedTasks ? confirmed.plannedTasks.map(pt => pt.task.name) : []
        };
    })()
    """)
    print("Save updated plan check:", json.dumps(save_result, indent=2, ensure_ascii=False))

    # Assertions
    # VI Assertions
    assert vi_checks['stepBadge'] == 'BƯỚC 3/3 · XÁC NHẬN PLAN MỚI', f"VI stepBadge mismatch: {vi_checks['stepBadge']}"
    assert vi_checks['title'] == 'Plan mới được đề xuất', f"VI title mismatch: {vi_checks['title']}"
    assert vi_checks['desc'] == 'Đây là kế hoạch làm việc đã được điều chỉnh. Kế hoạch ban đầu sẽ được giữ nguyên cho đến khi bạn xác nhận và lưu thay đổi.', f"VI desc mismatch: {vi_checks['desc']}"
    assert vi_checks['bottomBtns'] == ['← Quay lại', 'Lưu Plan mới →'], f"VI bottomBtns mismatch: {vi_checks['bottomBtns']}"

    # Check tasks in VI
    # Task 1: First task -> LÀM ĐẦU TIÊN, Deadline: 31/10/2026 • ~1 giờ
    t1_vi = vi_checks['tasksData'][0]
    assert t1_vi['badge'] == 'LÀM ĐẦU TIÊN', f"Task 1 badge mismatch: {t1_vi['badge']}"
    assert 'Deadline: 31/10/2026' in t1_vi['meta'] and '~1 giờ' in t1_vi['meta'], f"Task 1 meta mismatch: {t1_vi['meta']}"

    # Task 2: No deadline -> TIẾP THEO, Chưa có deadline cố định • ~45 phút
    t2_vi = vi_checks['tasksData'][1]
    assert t2_vi['badge'] == 'TIẾP THEO', f"Task 2 badge mismatch: {t2_vi['badge']}"
    assert 'Chưa có deadline cố định' in t2_vi['meta'] and '~45 phút' in t2_vi['meta'], f"Task 2 meta mismatch: {t2_vi['meta']}"

    # Task 3: Retained task 3 -> TIẾP THEO, Deadline: 02/11/2026 • ~1,5 giờ
    t3_vi = vi_checks['tasksData'][2]
    assert t3_vi['badge'] == 'TIẾP THEO', f"Task 3 badge mismatch: {t3_vi['badge']}"
    assert 'Deadline: 02/11/2026' in t3_vi['meta'] and '~1,5 giờ' in t3_vi['meta'], f"Task 3 meta mismatch: {t3_vi['meta']}"

    # Task 4: Added task -> TIẾP THEO, Deadline: 02/11/2026 • ~1,5 giờ
    t4_vi = vi_checks['tasksData'][3]
    assert t4_vi['badge'] == 'TIẾP THEO', f"Task 4 badge mismatch: {t4_vi['badge']}"
    assert 'Deadline: 02/11/2026' in t4_vi['meta'] and '~1,5 giờ' in t4_vi['meta'], f"Task 4 meta mismatch: {t4_vi['meta']}"

    # EN Assertions
    assert en_checks['stepBadge'] == 'STEP 3 OF 3 · CONFIRM UPDATED PLAN', f"EN stepBadge mismatch: {en_checks['stepBadge']}"
    assert en_checks['title'] == 'Proposed Updated Plan', f"EN title mismatch: {en_checks['title']}"
    assert en_checks['desc'] == 'Here is your updated working plan. Your original plan is preserved until you confirm and save.', f"EN desc mismatch: {en_checks['desc']}"
    assert en_checks['bottomBtns'] == ['← Back', 'Save updated plan →'], f"EN bottomBtns mismatch: {en_checks['bottomBtns']}"

    # Check tasks in EN
    t1_en = en_checks['tasksData'][0]
    assert t1_en['badge'] == 'DO THIS FIRST', f"Task 1 EN badge mismatch: {t1_en['badge']}"
    assert 'Due: Oct 31, 2026' in t1_en['meta'] and '~1 hr' in t1_en['meta'], f"Task 1 EN meta mismatch: {t1_en['meta']}"

    t2_en = en_checks['tasksData'][1]
    assert t2_en['badge'] == 'UP NEXT', f"Task 2 EN badge mismatch: {t2_en['badge']}"
    assert 'No fixed deadline' in t2_en['meta'] and '~45 min' in t2_en['meta'], f"Task 2 EN meta mismatch: {t2_en['meta']}"

    t3_en = en_checks['tasksData'][2]
    assert t3_en['badge'] == 'UP NEXT', f"Task 3 EN badge mismatch: {t3_en['badge']}"
    assert 'Due: Nov 02, 2026' in t3_en['meta'] and '~1.5 hr' in t3_en['meta'], f"Task 3 EN meta mismatch: {t3_en['meta']}"

    t4_en = en_checks['tasksData'][3]
    assert t4_en['badge'] == 'UP NEXT', f"Task 4 EN badge mismatch: {t4_en['badge']}"
    assert 'Due: Nov 02, 2026' in t4_en['meta'] and '~1.5 hr' in t4_en['meta'], f"Task 4 EN meta mismatch: {t4_en['meta']}"

    # Return check
    assert 'STEP 2 OF 3' in step2_check['stepBadge'], f"Step 2 return mismatch: {step2_check}"

    # Save check
    assert save_result['hasConfirmedPlan'] is True, "Confirmed plan was not saved"
    assert save_result['taskCount'] == 4, f"Expected 4 planned tasks, got: {save_result['taskCount']}"
    assert 'Chemistry Study' in save_result['taskTitles'], f"Newly added task not in saved plan: {save_result['taskTitles']}"

    print("\nALL STEP 3 VERIFICATIONS PASSED SUCCESSFULLY!")

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
