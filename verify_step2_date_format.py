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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_date_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9558

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
            id: 'test-working-plan-date',
            planId: 'test-working-plan-date',
            status: 'active',
            planType: 'emergency',
            title: 'Tempo Working Plan',
            createdAt: Date.now(),
            plannedTasks: [
                {
                    task: {
                        id: 't-1',
                        name: 'Literature Review Chapter 2',
                        deadlineDate: '2026-11-02',
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
                        deadlineDate: '2026-10-31',
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
        const inp1 = document.getElementById('adjust-due-t-1');
        const inp2 = document.getElementById('adjust-due-t-2');
        const inp3 = document.getElementById('adjust-due-t-3');
        const newDue = document.getElementById('adjust-new-task-due');

        return {
            inp1_val: inp1 ? inp1.value : null,
            inp1_placeholder: inp1 ? inp1.placeholder : null,
            inp1_iso: inp1 ? inp1.dataset.iso : null,

            inp2_val: inp2 ? inp2.value : null,
            inp2_placeholder: inp2 ? inp2.placeholder : null,

            inp3_val: inp3 ? inp3.value : null,
            inp3_placeholder: inp3 ? inp3.placeholder : null,
            inp3_iso: inp3 ? inp3.dataset.iso : null,

            newDue_val: newDue ? newDue.value : null,
            newDue_placeholder: newDue ? newDue.placeholder : null
        };
    })()
    """)
    print("VI Date Inputs Check:", json.dumps(vi_checks, indent=2, ensure_ascii=False))

    # Add a new task in VI mode with date "02/11/2026"
    eval_js("""
    (() => {
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
    })()
    """)
    time.sleep(0.5)

    vi_added_tasks = eval_js("""
    (() => {
        const list = document.getElementById('adjust-new-tasks-list');
        if (!list) return [];
        return Array.from(list.children).map(c => c.innerText.trim());
    })()
    """)
    print("VI Added Tasks Preview:", json.dumps(vi_added_tasks, indent=2, ensure_ascii=False))

    capture_screenshot("adjust_plan_step2_date_vi.png")

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
        const inp1 = document.getElementById('adjust-due-t-1');
        const inp2 = document.getElementById('adjust-due-t-2');
        const inp3 = document.getElementById('adjust-due-t-3');
        const newDue = document.getElementById('adjust-new-task-due');

        const list = document.getElementById('adjust-new-tasks-list');
        const addedTasks = list ? Array.from(list.children).map(c => c.innerText.trim()) : [];

        return {
            inp1_val: inp1 ? inp1.value : null,
            inp1_placeholder: inp1 ? inp1.placeholder : null,
            inp1_iso: inp1 ? inp1.dataset.iso : null,

            inp2_val: inp2 ? inp2.value : null,
            inp2_placeholder: inp2 ? inp2.placeholder : null,

            inp3_val: inp3 ? inp3.value : null,
            inp3_placeholder: inp3 ? inp3.placeholder : null,
            inp3_iso: inp3 ? inp3.dataset.iso : null,

            newDue_val: newDue ? newDue.value : null,
            newDue_placeholder: newDue ? newDue.placeholder : null,

            addedTasks
        };
    })()
    """)
    print("EN Date Inputs Check:", json.dumps(en_checks, indent=2, ensure_ascii=False))

    capture_screenshot("adjust_plan_step2_date_en.png")

    # 4. Test Picker Event on Task 2
    print("\n--- Testing Native Picker change event on Task 2 ---")
    picker_test = eval_js("""
    (() => {
        // Change picker on t-2 to 2026-11-02
        window.TempoUrmodeFlow.handleStep2PickerChange('t-2', '2026-11-02');
        const inp2 = document.getElementById('adjust-due-t-2');
        return {
            en_val: inp2 ? inp2.value : null,
            en_iso: inp2 ? inp2.dataset.iso : null
        };
    })()
    """)
    print("Picker test in EN:", json.dumps(picker_test, indent=2, ensure_ascii=False))

    # Switch back to VI and check Task 2 format
    picker_vi_test = eval_js("""
    (() => {
        window.TempoI18n.setLanguage('vi');
        const inp2 = document.getElementById('adjust-due-t-2');
        return {
            vi_val: inp2 ? inp2.value : null,
            vi_iso: inp2 ? inp2.dataset.iso : null
        };
    })()
    """)
    print("Picker test switched to VI:", json.dumps(picker_vi_test, indent=2, ensure_ascii=False))

    # 5. Test saving and reopening across steps
    print("\n--- Testing Navigation to Step 3 and back ---")
    nav_test = eval_js("""
    (() => {
        window.TempoUrmodeFlow.handleAdjustmentStep2Next();
        // Return to Step 2
        window.TempoUrmodeFlow.renderAdjustmentStep2Tasks();
        const inp1 = document.getElementById('adjust-due-t-1');
        const inp2 = document.getElementById('adjust-due-t-2');
        return {
            inp1_val: inp1 ? inp1.value : null,
            inp2_val: inp2 ? inp2.value : null
        };
    })()
    """)
    print("Reopened Step 2 check (VI):", json.dumps(nav_test, indent=2, ensure_ascii=False))

    # Assertions
    # VI Assertions
    assert vi_checks['inp1_val'] == '02/11/2026', f"VI inp1_val mismatch: {vi_checks['inp1_val']}"
    assert vi_checks['inp1_placeholder'] == 'dd/mm/yyyy', f"VI inp1_placeholder mismatch: {vi_checks['inp1_placeholder']}"
    assert vi_checks['inp1_iso'] == '2026-11-02', f"VI inp1_iso mismatch: {vi_checks['inp1_iso']}"

    assert vi_checks['inp2_val'] == '', f"VI inp2_val mismatch: {vi_checks['inp2_val']}"
    assert vi_checks['inp2_placeholder'] == 'dd/mm/yyyy', f"VI inp2_placeholder mismatch: {vi_checks['inp2_placeholder']}"

    assert vi_checks['inp3_val'] == '31/10/2026', f"VI inp3_val mismatch: {vi_checks['inp3_val']}"
    assert vi_checks['newDue_placeholder'] == 'dd/mm/yyyy', f"VI newDue_placeholder mismatch: {vi_checks['newDue_placeholder']}"

    assert any('Deadline: 02/11/2026' in t for t in vi_added_tasks), f"VI added task preview mismatch: {vi_added_tasks}"

    # EN Assertions
    assert en_checks['inp1_val'] == 'Nov 02, 2026', f"EN inp1_val mismatch: {en_checks['inp1_val']}"
    assert en_checks['inp1_placeholder'] == 'MMM DD, YYYY', f"EN inp1_placeholder mismatch: {en_checks['inp1_placeholder']}"
    assert en_checks['inp1_iso'] == '2026-11-02', f"EN inp1_iso mismatch: {en_checks['inp1_iso']}"

    assert en_checks['inp2_placeholder'] == 'MMM DD, YYYY', f"EN inp2_placeholder mismatch: {en_checks['inp2_placeholder']}"
    assert en_checks['inp3_val'] == 'Oct 31, 2026', f"EN inp3_val mismatch: {en_checks['inp3_val']}"
    assert en_checks['newDue_placeholder'] == 'MMM DD, YYYY', f"EN newDue_placeholder mismatch: {en_checks['newDue_placeholder']}"

    assert any('Due: Nov 02, 2026' in t for t in en_checks['addedTasks']), f"EN added task preview mismatch: {en_checks['addedTasks']}"

    # Picker assertions
    assert picker_test['en_val'] == 'Nov 02, 2026' and picker_test['en_iso'] == '2026-11-02', f"Picker EN mismatch: {picker_test}"
    assert picker_vi_test['vi_val'] == '02/11/2026' and picker_vi_test['vi_iso'] == '2026-11-02', f"Picker VI mismatch: {picker_vi_test}"

    # Reopening assertions
    assert nav_test['inp1_val'] == '02/11/2026' and nav_test['inp2_val'] == '02/11/2026', f"Reopened Step 2 mismatch: {nav_test}"

    print("\nALL DATE FORMAT VERIFICATIONS PASSED SUCCESSFULLY!")

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
