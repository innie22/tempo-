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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_modal_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9570

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

    print("Browser loaded. Setting up tests with active plan containing overdue task...")

    setup_script = """
    (() => {
        if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
            window.TempoMode.setMode('recovery');
        }

        const overdueTask = {
            id: 'task-overdue-test',
            name: 'Prepare Quarterly Audit Report',
            hasDeadline: true,
            deadlineDate: '2020-01-01',
            deadlineTime: '09:00',
            durationMinutes: 45,
            completed: false,
            subtasks: []
        };
        const mockPlan = {
            id: 'plan_overdue_test',
            planType: 'emergency',
            title: 'Working Plan',
            plannedTasks: [
                {
                    dayDate: '2020-01-01',
                    dayLabel: 'Past Date',
                    task: overdueTask
                }
            ],
            tasks: [overdueTask]
        };

        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            window.TempoPlanStore.saveActivePlan('emergency', mockPlan);
        }
        try {
            localStorage.setItem('tempo_confirmed_plan', JSON.stringify(mockPlan));
            localStorage.setItem('tempo_active_plan_emergency', JSON.stringify(mockPlan));
        } catch(e) {}

        return window.TempoUrmodeFlow.determinePlanCase();
    })()
    """
    detected_case = eval_js(setup_script)
    print(f"Naturally detected plan case: {detected_case}")
    assert detected_case == "PLAN_WITH_OVERDUE", f"Expected PLAN_WITH_OVERDUE, got {detected_case}"

    # 1. TEST ENGLISH MODE
    print("\n--- 1. Testing English Mode ---")
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(0.5)
    eval_js("window.TempoUrmodeFlow.showResetPopup()")
    time.sleep(0.5)

    extract_modal_text = """
    (() => {
        const modal = document.getElementById('modal-urmode-flow');
        if (!modal || modal.classList.contains('hidden')) return null;
        
        const badge = modal.querySelector('span.tracking-widest')?.textContent.trim();
        const title = modal.querySelector('h2.font-heading')?.textContent.trim();
        const body = modal.querySelector('div.space-y-2 p')?.textContent.trim();
        const bullets = Array.from(modal.querySelectorAll('div.space-y-2 div span'))
            .map(s => s.textContent.trim())
            .filter(t => t && t !== '•');
        const secondaryBtn = modal.querySelector('div.pt-4 button:first-child')?.textContent.trim();
        const primaryBtn = modal.querySelector('div.pt-4 button:last-child')?.textContent.trim();
        const closeBtnTitle = modal.querySelector('button[title]')?.getAttribute('title');

        return {
            badge,
            title,
            body,
            bullets,
            secondaryBtn,
            primaryBtn,
            closeBtnTitle
        };
    })()
    """
    en_modal_data = eval_js(extract_modal_text)
    print("EN Modal Data:", json.dumps(en_modal_data, ensure_ascii=False, indent=2))

    assert en_modal_data["badge"] == "PLAN UPDATE NEEDED"
    assert en_modal_data["title"] == "Review and reset your Working Plan"
    assert en_modal_data["body"] == "You have tasks with overdue deadlines that need your attention. Take a quick reset to calm down, or review your tasks and adjust your schedule."
    assert any("2 min box breathing" in b for b in en_modal_data["bullets"])
    assert "Grounds focus" in en_modal_data["bullets"]
    assert "No rush" in en_modal_data["bullets"]
    assert en_modal_data["secondaryBtn"] == "Review your plan"
    assert en_modal_data["primaryBtn"] == "Yes, take a quick reset →"
    print(">>> All English assertions PASSED!")

    take_screenshot("plan_update_needed_modal_en.png")

    # 2. TEST IN-PLACE SWITCH TO VIETNAMESE
    print("\n--- 2. Testing In-Place Switch to Vietnamese ---")
    eval_js("window.TempoI18n.setLanguage('vi')")
    time.sleep(0.5)

    vi_modal_data = eval_js(extract_modal_text)
    print("VI Modal Data:", json.dumps(vi_modal_data, ensure_ascii=False, indent=2))

    assert vi_modal_data["badge"] == "PLAN CẦN ĐƯỢC CẬP NHẬT"
    assert vi_modal_data["title"] == "Xem lại và điều chỉnh plan của bạn"
    assert vi_modal_data["body"] == "Bạn có một số task đã quá deadline cần được xem lại. Hãy dành chút thời gian để lấy lại bình tĩnh, hoặc xem lại các task và điều chỉnh lịch trình của mình nhé."
    assert any("Tập thở trong 2 phút" in b for b in vi_modal_data["bullets"])
    assert "Giúp bạn lấy lại sự tập trung" in vi_modal_data["bullets"]
    assert "Không cần vội" in vi_modal_data["bullets"]
    assert vi_modal_data["secondaryBtn"] == "Xem lại plan"
    assert vi_modal_data["primaryBtn"] == "Có, tôi muốn lấy lại bình tĩnh một chút →"
    print(">>> All Vietnamese assertions PASSED!")

    take_screenshot("plan_update_needed_modal_vi.png")

    # 3. TEST IN-PLACE SWITCH BACK TO ENGLISH
    print("\n--- 3. Testing In-Place Switch Back to English ---")
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(0.5)

    en_modal_data_2 = eval_js(extract_modal_text)
    assert en_modal_data_2["badge"] == "PLAN UPDATE NEEDED"
    assert en_modal_data_2["title"] == "Review and reset your Working Plan"
    assert en_modal_data_2["secondaryBtn"] == "Review your plan"
    print(">>> Switch back to English PASSED!")

    # 4. TEST BUTTON ACTIONS
    print("\n--- 4. Testing Button Actions ---")
    # Click secondary button "Review your plan"
    click_secondary_script = """
    (() => {
        const secBtn = document.querySelector('#modal-urmode-flow div.pt-4 button:first-child');
        secBtn.click();
        const modal = document.getElementById('modal-urmode-flow');
        return {
            text: modal ? modal.textContent : '',
            hasSummaryHeader: modal ? modal.textContent.includes('WORKING PLAN REVIEW') : false
        };
    })()
    """
    sec_result = eval_js(click_secondary_script)
    print("Secondary click result (opened summary):", sec_result.get("hasSummaryHeader"))
    assert sec_result.get("hasSummaryHeader") is True, f"Failed to open Working Plan Review: {sec_result}"
    print(">>> 'Review your plan' button action PASSED!")

    # Re-open modal and test primary button "Yes, take a quick reset →"
    eval_js("window.TempoUrmodeFlow.showResetPopup()")
    time.sleep(0.5)
    click_primary_script = """
    (() => {
        let calledBreathing = false;
        if (!window.TempoStressRelief) window.TempoStressRelief = {};
        const origBreathing = window.TempoStressRelief.openBreathing;
        window.TempoStressRelief.openBreathing = (opts) => {
            calledBreathing = true;
            if (opts && typeof opts.onReady === 'function') opts.onReady();
        };
        const primBtn = document.querySelector('#modal-urmode-flow div.pt-4 button:last-child');
        primBtn.click();
        window.TempoStressRelief.openBreathing = origBreathing;
        const modal = document.getElementById('modal-urmode-flow');
        return {
            calledBreathing,
            isReadyModal: modal ? modal.textContent.includes('Are you ready?') || modal.textContent.includes('GROUNDED CHECKPOINT') : false
        };
    })()
    """
    prim_result = eval_js(click_primary_script)
    print("Primary click result (invoked breathing & checkpoint):", prim_result)
    assert prim_result.get("calledBreathing") is True, "Failed to invoke quick reset / breathing flow"
    print(">>> 'Yes, take a quick reset' button action PASSED!")

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
