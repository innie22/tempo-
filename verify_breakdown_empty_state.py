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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_breakdown_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9567

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
            id: 'test-breakdown-plan',
            planId: 'test-breakdown-plan',
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
                        completed: false,
                        subtasks: []
                    },
                    dayDate: '2026-11-02',
                    startTime: '09:00',
                    endTime: '10:30',
                    executionBadge: 'DO THIS FIRST'
                }
            ],
            unarrangedTasks: []
        };

        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            await window.TempoPlanStore.saveActivePlan('emergency', mockPlan);
        }
        localStorage.setItem('tempo_active_working_plan', JSON.stringify(mockPlan));

        window.TempoI18n.setLanguage('vi');
        window.TempoUrmodeFlow.renderBreakTaskPopup('t-101');
        return true;
    })();
    """
    eval_js(setup_code)
    time.sleep(1)

    # 1. Verify Vietnamese empty-state text
    vi_empty = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        if (!modal) return { error: 'No modal found' };
        const emptyEl = modal.querySelector('#breakdown-subtask-list > div');
        return emptyEl ? emptyEl.innerText.trim() : null;
    })()
    """)
    print("VI Empty State Text:", vi_empty)

    expected_vi = "Chưa có bước thực hiện nào. Hãy thêm bước đầu tiên bên dưới hoặc chọn ✨ AI hỗ trợ."
    assert vi_empty == expected_vi, f"Expected '{expected_vi}', got '{vi_empty}'"

    capture_screenshot("breakdown_task_empty_vi.png")
    print("VI empty state test passed successfully!")

    # 2. Switch on-the-fly to English
    eval_js("window.TempoI18n.setLanguage('en');")
    time.sleep(1)

    en_empty = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        if (!modal) return { error: 'No modal found' };
        const emptyEl = modal.querySelector('#breakdown-subtask-list > div');
        return emptyEl ? emptyEl.innerText.trim() : null;
    })()
    """)
    print("EN Empty State Text:", en_empty)

    expected_en = "No action steps added yet. Add your first step below or click ✨ AI Help."
    assert en_empty == expected_en, f"Expected '{expected_en}', got '{en_empty}'"

    capture_screenshot("breakdown_task_empty_en.png")
    print("EN empty state test passed successfully!")

    # 3. Test removing a subtask returns the empty state in current language
    eval_js("""
    (() => {
        const input = document.getElementById('breakdown-subtask-input');
        if (input) input.value = 'Temporary Step';
        window.TempoUrmodeFlow.addSubtask('t-101');
    })()
    """)
    time.sleep(0.5)

    has_subtask = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        return modal ? modal.innerText.includes('Temporary Step') : false;
    })()
    """)
    print("Added subtask visible:", has_subtask)
    assert has_subtask, "Failed to add manual subtask"

    # Remove the subtask
    eval_js("""
    (() => {
        const plan = window.TempoPlanStore.getActivePlan('emergency');
        const subtask = plan.plannedTasks[0].task.subtasks[0];
        window.TempoUrmodeFlow.removeSubtask('t-101', subtask.id);
    })()
    """)
    time.sleep(0.5)

    re_empty = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        const emptyEl = modal ? modal.querySelector('#breakdown-subtask-list > div') : null;
        return emptyEl ? emptyEl.innerText.trim() : null;
    })()
    """)
    print("Re-empty State Text in EN:", re_empty)
    assert re_empty == expected_en, f"Expected '{expected_en}', got '{re_empty}'"

    # Switch back to VI and verify re-empty state
    eval_js("window.TempoI18n.setLanguage('vi');")
    time.sleep(0.5)
    re_empty_vi = eval_js("""
    (() => {
        const modal = document.querySelector('#modal-urmode-flow');
        const emptyEl = modal ? modal.querySelector('#breakdown-subtask-list > div') : null;
        return emptyEl ? emptyEl.innerText.trim() : null;
    })()
    """)
    print("Re-empty State Text in VI:", re_empty_vi)
    assert re_empty_vi == expected_vi, f"Expected '{expected_vi}', got '{re_empty_vi}'"

    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")

finally:
    if ws:
        ws.close()
    proc.terminate()
