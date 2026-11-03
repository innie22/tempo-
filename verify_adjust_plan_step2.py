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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_step2_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9557

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
        const u = { id: 'u1', email: 'alex@tempo.test', user_metadata: { display_name: 'Alex' } };
        localStorage.setItem('tempo_local_dev_user', JSON.stringify(u));
        localStorage.setItem('tempo_mock_account_alex@tempo.test', JSON.stringify(u));
        if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
            await window.TempoAuth.checkSession();
        }

        const tomorrowStr = (window.TempoI18n && typeof window.TempoI18n.getLocalTomorrowISO === 'function')
            ? window.TempoI18n.getLocalTomorrowISO()
            : '2026-11-02';

        const mockPlan = {
            id: 'test-working-plan-adj2',
            planId: 'test-working-plan-adj2',
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
                        deadlineDate: '2026-11-05',
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
            window.TempoPlanStore.saveActivePlan('emergency', mockPlan);
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

        // Open adjustment flow (Step 1)
        window.TempoUrmodeFlow.startAdjustmentFlow();
        // Advance to Step 2
        window.TempoUrmodeFlow.renderAdjustmentStep2Tasks();
    })()
    """
    eval_js(setup_code)
    time.sleep(1)

    # 2. Check Vietnamese Mode Step 2 Elements
    vi_checks = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow') || document.querySelector('.fixed.inset-0.z-50');
        const text = modal ? modal.innerText : '';
        const stepBadge = modal ? modal.querySelector('span.uppercase')?.innerText.trim() : '';
        const title = modal ? modal.querySelector('h2')?.innerText.trim() : '';

        // Retained tasks header leaf
        const allDivs = modal ? Array.from(modal.querySelectorAll('div')) : [];
        const retainedHeaderEl = allDivs.find(d => d.children.length === 0 && d.innerText && d.innerText.includes('CÁC TASK ĐƯỢC GIỮ LẠI'));
        const retainedHeader = retainedHeaderEl ? retainedHeaderEl.innerText.trim() : '';

        // Labels
        const dueLabels = modal ? Array.from(modal.querySelectorAll('label')).map(l => l.innerText.trim()) : [];

        // Select options for first retained task
        const firstDurSelect = modal ? modal.querySelector('select[id^="adjust-dur-"]') : null;
        const durOptions = firstDurSelect ? Array.from(firstDurSelect.options).map(o => o.text.trim()) : [];

        // Add new task section header leaf
        const addSectionHeaderEl = allDivs.find(d => d.children.length === 0 && d.innerText && d.innerText.includes('+ THÊM TASK MỚI:'));
        const addSectionHeader = addSectionHeaderEl ? addSectionHeaderEl.innerText.trim() : '';
        const nameInputPlaceholder = modal ? modal.querySelector('#adjust-new-task-name')?.placeholder : '';
        const addBtn = modal ? modal.querySelector('button[onclick*="addNewAdjustmentTask"]')?.innerText.trim() : '';

        // Bottom action buttons
        const bottomBtns = modal ? Array.from(modal.querySelectorAll('.pt-4 button')).map(b => b.innerText.trim()) : [];

        return {
            stepBadge,
            title,
            retainedHeader,
            dueLabels,
            durOptions,
            addSectionHeader,
            nameInputPlaceholder,
            addBtn,
            bottomBtns
        };
    })()
    """)
    print("VI Checks:", json.dumps(vi_checks, indent=2, ensure_ascii=False))

    # Add a new task in VI mode with 90 min duration (1,5 giờ) and deadline 2026-10-31
    eval_js("""
    (() => {
        const nameEl = document.getElementById('adjust-new-task-name');
        const dueEl = document.getElementById('adjust-new-task-due');
        const durEl = document.getElementById('adjust-new-task-dur');
        if (nameEl) nameEl.value = 'Học môn Sinh học';
        if (dueEl) dueEl.value = '2026-10-31';
        if (durEl) durEl.value = '90';
        window.TempoUrmodeFlow.addNewAdjustmentTask();
    })()
    """)
    time.sleep(0.5)

    # Also add a second new task without deadline, 30 min duration
    eval_js("""
    (() => {
        const nameEl = document.getElementById('adjust-new-task-name');
        const durEl = document.getElementById('adjust-new-task-dur');
        if (nameEl) nameEl.value = 'Đọc tài liệu tham khảo';
        if (durEl) durEl.value = '30';
        window.TempoUrmodeFlow.addNewAdjustmentTask();
    })()
    """)
    time.sleep(0.5)

    # Check newly added tasks preview
    vi_added_tasks = eval_js("""
    (() => {
        const list = document.getElementById('adjust-new-tasks-list');
        if (!list) return [];
        return Array.from(list.children).map(c => c.innerText.trim());
    })()
    """)
    print("VI Added Tasks Preview:", json.dumps(vi_added_tasks, indent=2, ensure_ascii=False))

    capture_screenshot("adjust_plan_step2_vi.png")

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
        const modal = document.querySelector('#modal-urmode-flow') || document.querySelector('.fixed.inset-0.z-50');
        const stepBadge = modal ? modal.querySelector('span.uppercase')?.innerText.trim() : '';
        const title = modal ? modal.querySelector('h2')?.innerText.trim() : '';

        // Retained tasks header leaf
        const allDivs = modal ? Array.from(modal.querySelectorAll('div')) : [];
        const retainedHeaderEl = allDivs.find(d => d.children.length === 0 && d.innerText && d.innerText.includes('RETAINED TASKS'));
        const retainedHeader = retainedHeaderEl ? retainedHeaderEl.innerText.trim() : '';

        // Labels
        const dueLabels = modal ? Array.from(modal.querySelectorAll('label')).map(l => l.innerText.trim()) : [];

        // Select options for first retained task
        const firstDurSelect = modal ? modal.querySelector('select[id^="adjust-dur-"]') : null;
        const durOptions = firstDurSelect ? Array.from(firstDurSelect.options).map(o => o.text.trim()) : [];

        // Add new task section header leaf
        const addSectionHeaderEl = allDivs.find(d => d.children.length === 0 && d.innerText && d.innerText.includes('+ ADD NEW TASK:'));
        const addSectionHeader = addSectionHeaderEl ? addSectionHeaderEl.innerText.trim() : '';
        const nameInputPlaceholder = modal ? modal.querySelector('#adjust-new-task-name')?.placeholder : '';
        const addBtn = modal ? modal.querySelector('button[onclick*="addNewAdjustmentTask"]')?.innerText.trim() : '';

        // Bottom action buttons
        const bottomBtns = modal ? Array.from(modal.querySelectorAll('.pt-4 button')).map(b => b.innerText.trim()) : [];

        // Added tasks preview in EN
        const list = document.getElementById('adjust-new-tasks-list');
        const addedTasks = list ? Array.from(list.children).map(c => c.innerText.trim()) : [];

        return {
            stepBadge,
            title,
            retainedHeader,
            dueLabels,
            durOptions,
            addSectionHeader,
            nameInputPlaceholder,
            addBtn,
            bottomBtns,
            addedTasks
        };
    })()
    """)
    print("EN Checks:", json.dumps(en_checks, indent=2, ensure_ascii=False))

    capture_screenshot("adjust_plan_step2_en.png")

    # 4. Test Navigation: Back button to Step 1
    print("\n--- Testing Navigation: Back button to Step 1 ---")
    eval_js("""
    (() => {
        window.TempoUrmodeFlow.handleAdjustmentStep2Back();
    })()
    """)
    time.sleep(0.5)

    step1_check = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow') || document.querySelector('.fixed.inset-0.z-50');
        return {
            stepBadge: modal ? modal.querySelector('span.uppercase')?.innerText.trim() : '',
            title: modal ? modal.querySelector('h2')?.innerText.trim() : ''
        };
    })()
    """)
    print("Step 1 return check:", json.dumps(step1_check, indent=2, ensure_ascii=False))

    # 5. Advance from Step 1 back to Step 2, then Step 2 Next to Step 3
    print("\n--- Testing Navigation: Step 2 to Step 3 ---")
    eval_js("""
    (() => {
        window.TempoUrmodeFlow.renderAdjustmentStep2Tasks();
    })()
    """)
    time.sleep(0.5)

    eval_js("""
    (() => {
        window.TempoUrmodeFlow.handleAdjustmentStep2Next();
    })()
    """)
    time.sleep(0.5)

    step3_check = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow') || document.querySelector('.fixed.inset-0.z-50');
        return {
            stepBadge: modal ? modal.querySelector('span.uppercase')?.innerText.trim() : '',
            title: modal ? modal.querySelector('h2')?.innerText.trim() : ''
        };
    })()
    """)
    print("Step 3 advancement check:", json.dumps(step3_check, indent=2, ensure_ascii=False))

    # Assertions
    assert vi_checks['stepBadge'] == 'BƯỚC 2/3 · ĐIỀU CHỈNH PLAN', f"VI badge mismatch: {vi_checks['stepBadge']}"
    assert vi_checks['title'] == 'Điều chỉnh thời lượng & thêm task mới', f"VI title mismatch: {vi_checks['title']}"
    assert vi_checks['retainedHeader'] == 'CÁC TASK ĐƯỢC GIỮ LẠI (3):', f"VI retainedHeader mismatch: {vi_checks['retainedHeader']}"
    assert 'Deadline:' in vi_checks['dueLabels'], f"VI dueLabels mismatch: {vi_checks['dueLabels']}"
    assert vi_checks['durOptions'] == ['15 phút', '30 phút', '45 phút', '1 giờ', '1,5 giờ', '2 giờ'], f"VI durOptions mismatch: {vi_checks['durOptions']}"
    assert vi_checks['addSectionHeader'] == '+ THÊM TASK MỚI:', f"VI addSectionHeader mismatch: {vi_checks['addSectionHeader']}"
    assert vi_checks['nameInputPlaceholder'] == 'Tên task...', f"VI nameInputPlaceholder mismatch: {vi_checks['nameInputPlaceholder']}"
    assert vi_checks['addBtn'] == 'Thêm', f"VI addBtn mismatch: {vi_checks['addBtn']}"
    assert '← Quay lại' in vi_checks['bottomBtns'], f"VI bottomBtns back mismatch: {vi_checks['bottomBtns']}"
    assert 'Tiếp theo: Đề xuất plan →' in vi_checks['bottomBtns'], f"VI bottomBtns next mismatch: {vi_checks['bottomBtns']}"

    # Verify added task formats in VI
    assert any('1,5 giờ' in t and '31/10/2026' in t for t in vi_added_tasks), f"VI added task format mismatch: {vi_added_tasks}"

    # English Assertions
    assert en_checks['stepBadge'] == 'STEP 2 OF 3 · ADJUST PLAN', f"EN badge mismatch: {en_checks['stepBadge']}"
    assert en_checks['title'] == 'Adjust estimates & add new tasks', f"EN title mismatch: {en_checks['title']}"
    assert en_checks['retainedHeader'] == 'RETAINED TASKS (3):', f"EN retainedHeader mismatch: {en_checks['retainedHeader']}"
    assert 'Due:' in en_checks['dueLabels'], f"EN dueLabels mismatch: {en_checks['dueLabels']}"
    assert en_checks['durOptions'] == ['15 min', '30 min', '45 min', '1 hr', '1.5 hr', '2 hr'], f"EN durOptions mismatch: {en_checks['durOptions']}"
    assert en_checks['addSectionHeader'] == '+ ADD NEW TASK:', f"EN addSectionHeader mismatch: {en_checks['addSectionHeader']}"
    assert en_checks['nameInputPlaceholder'] == 'Task name...', f"EN nameInputPlaceholder mismatch: {en_checks['nameInputPlaceholder']}"
    assert en_checks['addBtn'] == 'Add', f"EN addBtn mismatch: {en_checks['addBtn']}"
    assert '← Back' in en_checks['bottomBtns'], f"EN bottomBtns back mismatch: {en_checks['bottomBtns']}"
    assert 'Next: Propose plan →' in en_checks['bottomBtns'], f"EN bottomBtns next mismatch: {en_checks['bottomBtns']}"
    assert any('1.5 hr' in t and 'Oct 31, 2026' in t for t in en_checks['addedTasks']), f"EN added task format mismatch: {en_checks['addedTasks']}"

    # Navigation assertions
    assert 'STEP 1 OF 3' in step1_check['stepBadge'], f"Step 1 return mismatch: {step1_check}"
    assert 'STEP 3 OF 3' in step3_check['stepBadge'], f"Step 3 return mismatch: {step3_check}"

    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

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
