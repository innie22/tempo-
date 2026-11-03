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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_task_now_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9574

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

    print("Browser loaded. Setting up active plan with top priority task...")

    setup_script = """
    (() => {
        if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
            window.TempoMode.setMode('recovery');
        }

        const task1 = {
            id: 'task-now-1',
            name: 'Prepare Presentation Slides on Climate Action',
            hasDeadline: true,
            deadlineDate: '2026-11-10',
            deadlineTime: '14:00',
            durationMinutes: 45,
            completed: false,
            subtasks: [
                { id: 'sub-1', title: 'Outline key findings', completed: true },
                { id: 'sub-2', title: 'Design visual diagrams', completed: false }
            ]
        };

        const mockPlan = {
            id: 'plan_task_now_test',
            planType: 'emergency',
            title: 'Working Plan',
            plannedTasks: [
                { dayDate: '2026-11-10', task: task1, executionBadge: 'DO THIS FIRST' }
            ],
            tasks: [task1]
        };

        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            window.TempoPlanStore.saveActivePlan('emergency', mockPlan);
        }
        try {
            localStorage.setItem('tempo_confirmed_plan', JSON.stringify(mockPlan));
            localStorage.setItem('tempo_active_plan_emergency', JSON.stringify(mockPlan));
        } catch(e) {}

        return 'Plan saved with top priority task.';
    })()
    """
    res_setup = eval_js(setup_script)
    print(res_setup)

    # 1. TEST ENGLISH MODE
    print("\n--- 1. Testing English Mode ---")
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(0.5)
    eval_js("window.TempoUrmodeFlow.showKeepPlanTaskPopup()")
    time.sleep(0.5)

    extract_modal_data = """
    (() => {
        const modal = document.getElementById('modal-urmode-flow');
        if (!modal || modal.classList.contains('hidden')) return null;

        const badge = modal.querySelector('span.tracking-widest')?.textContent.trim();
        const heading = modal.querySelector('h2.font-heading')?.textContent.trim();
        const closeBtnTitle = modal.querySelector('button[title]')?.getAttribute('title');

        const card = modal.querySelector('.p-4.rounded-2xl');
        const priorityBadge = card?.querySelector('.rounded-full')?.textContent.trim();
        const durationText = card?.querySelector('.font-medium')?.textContent.trim();
        const taskName = card?.querySelector('h3.font-heading')?.textContent.trim();
        const dueText = card?.querySelector('div.space-x-2 span')?.textContent.trim();

        const buttons = Array.from(modal.querySelectorAll('div.pt-4 button')).map(b => b.textContent.trim());

        return {
            badge,
            heading,
            closeBtnTitle,
            priorityBadge,
            durationText,
            taskName,
            dueText,
            buttons
        };
    })()
    """
    en_data = eval_js(extract_modal_data)
    print("EN Your Task for Now Data:", json.dumps(en_data, ensure_ascii=False, indent=2))

    # Assertions for English
    assert en_data["badge"] == "YOUR TASK FOR NOW", f"Badge mismatch: '{en_data['badge']}'"
    assert en_data["heading"] == "Your task for now is…", f"Heading mismatch: '{en_data['heading']}'"
    assert en_data["priorityBadge"] == "DO THIS FIRST", f"Priority badge mismatch: '{en_data['priorityBadge']}'"
    assert "Due:" in en_data["dueText"], f"Due label mismatch: '{en_data['dueText']}'"
    assert en_data["durationText"] == "~45 min", f"Duration mismatch: '{en_data['durationText']}'"
    assert en_data["taskName"] == "Prepare Presentation Slides on Climate Action", f"Task name altered: '{en_data['taskName']}'"
    assert en_data["buttons"][0] == "Later", f"Secondary button mismatch: '{en_data['buttons'][0]}'"
    assert en_data["buttons"][1] == "Focus now →", f"Primary button mismatch: '{en_data['buttons'][1]}'"
    print(">>> All English assertions PASSED!")

    take_screenshot("your_task_for_now_modal_en.png")

    # 2. TEST IN-PLACE SWITCH TO VIETNAMESE (Without reload)
    print("\n--- 2. Testing In-Place Switch to Vietnamese ---")
    eval_js("window.TempoI18n.setLanguage('vi')")
    time.sleep(0.5)

    vi_data = eval_js(extract_modal_data)
    print("VI Your Task for Now Data:", json.dumps(vi_data, ensure_ascii=False, indent=2))

    # Assertions for Vietnamese
    assert vi_data["badge"] == "TASK HIỆN TẠI CỦA BẠN", f"Badge mismatch: '{vi_data['badge']}'"
    assert vi_data["heading"] == "Task bạn nên thực hiện lúc này là…", f"Heading mismatch: '{vi_data['heading']}'"
    assert vi_data["priorityBadge"] == "ƯU TIÊN LÀM TRƯỚC", f"Priority badge mismatch: '{vi_data['priorityBadge']}'"
    assert "Deadline:" in vi_data["dueText"], f"Deadline label mismatch: '{vi_data['dueText']}'"
    assert vi_data["durationText"] == "~45 phút", f"Duration mismatch: '{vi_data['durationText']}'"
    assert vi_data["taskName"] == "Prepare Presentation Slides on Climate Action", f"Task name altered: '{vi_data['taskName']}'"
    assert vi_data["buttons"][0] == "Để sau", f"Secondary button mismatch: '{vi_data['buttons'][0]}'"
    assert vi_data["buttons"][1] == "Tập trung ngay →", f"Primary button mismatch: '{vi_data['buttons'][1]}'"
    print(">>> All Vietnamese assertions PASSED!")

    take_screenshot("your_task_for_now_modal_vi.png")

    # 3. TEST IN-PLACE SWITCH BACK TO ENGLISH
    print("\n--- 3. Testing In-Place Switch Back to English ---")
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(0.5)

    en_data_2 = eval_js(extract_modal_data)
    assert en_data_2["badge"] == "YOUR TASK FOR NOW"
    assert en_data_2["heading"] == "Your task for now is…"
    assert en_data_2["priorityBadge"] == "DO THIS FIRST"
    assert "Due:" in en_data_2["dueText"]
    assert en_data_2["buttons"][0] == "Later"
    assert en_data_2["buttons"][1] == "Focus now →"
    print(">>> Switch back to English PASSED!")

    # 4. TEST BUTTON ACTIONS
    print("\n--- 4. Testing Action Buttons ---")
    # Test 1: Focus now → action triggers launchFocusForTask with taskId
    focus_test_script = """
    (() => {
        let focusedTaskId = null;
        const origLaunch = window.TempoUrmodeFlow.launchFocusForTask;
        window.TempoUrmodeFlow.launchFocusForTask = (id) => {
            focusedTaskId = id;
        };
        const focusBtn = document.querySelector('#modal-urmode-flow div.pt-4 button:last-child');
        focusBtn.click();
        window.TempoUrmodeFlow.launchFocusForTask = origLaunch;
        return focusedTaskId;
    })()
    """
    focused_id = eval_js(focus_test_script)
    print("Focus now clicked with taskId:", focused_id)
    assert focused_id == "task-now-1", f"Expected 'task-now-1', got '{focused_id}'"
    print(">>> 'Focus now →' button action PASSED!")

    # Re-open modal and test Later button closes modal
    eval_js("window.TempoUrmodeFlow.showKeepPlanTaskPopup()")
    time.sleep(0.5)

    later_test_script = """
    (() => {
        const laterBtn = document.querySelector('#modal-urmode-flow div.pt-4 button:first-child');
        laterBtn.click();
        const modal = document.getElementById('modal-urmode-flow');
        return modal ? modal.classList.contains('hidden') : true;
    })()
    """
    is_closed = eval_js(later_test_script)
    print("Later button clicked, modal is hidden:", is_closed)
    assert is_closed is True, "Later button did not close modal"
    print(">>> 'Later' button action PASSED!")

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
