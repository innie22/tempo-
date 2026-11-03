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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_task_sel_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9566

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
            id: 'test-task-selection-plan',
            planId: 'test-task-selection-plan',
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
                        completed: false
                    },
                    dayDate: '2026-11-02',
                    startTime: '11:00',
                    endTime: '12:00',
                    executionBadge: 'UP NEXT'
                },
                {
                    task: {
                        id: 't-103',
                        name: 'Draft Introduction Section',
                        durationMinutes: 30,
                        durationLabel: '30 min',
                        completed: false
                    },
                    dayDate: '2026-11-02',
                    startTime: '14:00',
                    endTime: '14:30',
                    executionBadge: 'UP NEXT'
                },
                {
                    task: {
                        id: 't-104',
                        name: 'Send Progress Email',
                        durationMinutes: 15,
                        durationLabel: '15 min',
                        completed: false
                    },
                    dayDate: '2026-11-02',
                    startTime: '15:00',
                    endTime: '15:15',
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
        window.TempoUrmodeFlow.showTaskSelectionPopup();
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
        const backBtn = modal.querySelector('div.pt-4 button')?.innerText.trim();

        const taskRows = Array.from(modal.querySelectorAll('.max-h-64 > div')).map(row => {
            const name = row.querySelector('.truncate')?.innerText.trim();
            const dur = row.querySelector('.text-stone-500')?.innerText.trim();
            const selBtn = row.querySelector('.rounded-full')?.innerText.trim();
            return { name, dur, selBtn };
        });

        return {
            badge,
            title,
            backBtn,
            taskRows
        };
    })()
    """)
    print("VI Modal Data:", json.dumps(vi_checks, indent=2, ensure_ascii=False))

    assert vi_checks.get('badge') == 'CHỌN TASK', f"Expected CHỌN TASK, got {vi_checks.get('badge')}"
    assert vi_checks.get('title') == 'Chọn task bạn muốn thực hiện', f"Expected Chọn task bạn muốn thực hiện, got {vi_checks.get('title')}"
    assert vi_checks.get('backBtn') == 'Quay lại', f"Expected Quay lại, got {vi_checks.get('backBtn')}"

    expected_vi_durs = ['~1,5 giờ', '~1 giờ', '~30 phút', '~15 phút']
    assert len(vi_checks.get('taskRows', [])) == 4, f"Expected 4 task rows, got {len(vi_checks.get('taskRows', []))}"
    for i, row in enumerate(vi_checks['taskRows']):
        assert row['dur'] == expected_vi_durs[i], f"Row {i} dur expected {expected_vi_durs[i]}, got {row['dur']}"
        assert row['selBtn'] == 'Chọn →', f"Row {i} button expected Chọn →, got {row['selBtn']}"

    capture_screenshot("task_selection_modal_vi.png")
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
        const backBtn = modal.querySelector('div.pt-4 button')?.innerText.trim();

        const taskRows = Array.from(modal.querySelectorAll('.max-h-64 > div')).map(row => {
            const name = row.querySelector('.truncate')?.innerText.trim();
            const dur = row.querySelector('.text-stone-500')?.innerText.trim();
            const selBtn = row.querySelector('.rounded-full')?.innerText.trim();
            return { name, dur, selBtn };
        });

        return {
            badge,
            title,
            backBtn,
            taskRows
        };
    })()
    """)
    print("EN Modal Data:", json.dumps(en_checks, indent=2, ensure_ascii=False))

    assert en_checks.get('badge') == 'TASK SELECTION', f"Expected TASK SELECTION, got {en_checks.get('badge')}"
    assert en_checks.get('title') == 'Select a task to work on', f"Expected Select a task to work on, got {en_checks.get('title')}"
    assert en_checks.get('backBtn') == 'Back', f"Expected Back, got {en_checks.get('backBtn')}"

    expected_en_durs = ['~1.5 hr', '~1 hr', '~30 min', '~15 min']
    assert len(en_checks.get('taskRows', [])) == 4, f"Expected 4 task rows, got {len(en_checks.get('taskRows', []))}"
    for i, row in enumerate(en_checks['taskRows']):
        assert row['dur'] == expected_en_durs[i], f"Row {i} dur expected {expected_en_durs[i]}, got {row['dur']}"
        assert row['selBtn'] == 'Select →', f"Row {i} button expected Select →, got {row['selBtn']}"

    capture_screenshot("task_selection_modal_en.png")
    print("EN checks passed successfully!")

    # 3. Test Back action
    eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        const btn = modal.querySelector('div.pt-4 button');
        if (btn) btn.click();
    })()
    """)
    time.sleep(0.5)
    first_task_view = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        return modal ? (modal.innerText.includes('FIRST TASK EXECUTION') || modal.innerText.includes('Your first task is')) : false;
    })()
    """)
    print("Back button returned to first task execution view:", first_task_view)
    assert first_task_view, "Back button failed to return to first task execution view"

    # 4. Re-open task selection and test Select ->
    eval_js("window.TempoUrmodeFlow.showTaskSelectionPopup();")
    time.sleep(0.5)
    eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        // Click on row 2 (t-102: Data Collection Phase 1)
        const row2 = modal.querySelectorAll('.max-h-64 > div')[1];
        if (row2) row2.click();
    })()
    """)
    time.sleep(0.5)
    selected_task_view = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        const hasTitle = modal ? (modal.innerText.includes('FIRST TASK EXECUTION') || modal.innerText.includes('Your first task is')) : false;
        const hasTask2 = modal ? modal.innerText.includes('Data Collection Phase 1') : false;
        return hasTitle && hasTask2;
    })()
    """)
    print("Selecting Task 2 opened first task execution for Task 2:", selected_task_view)
    assert selected_task_view, "Selecting task failed to update and open first task execution modal"

    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")

finally:
    if ws:
        ws.close()
    proc.terminate()
