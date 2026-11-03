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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_step1_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9585

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
time.sleep(2.5)

tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read().decode())
app_tab = next(t for t in tabs if "8000" in t.get("url", ""))
ws = websocket.create_connection(app_tab["webSocketDebuggerUrl"], timeout=10)
print("Connected to CDP via WebSocket.")

msg_id = 1
def send_cmd(method, params=None):
    global msg_id, ws
    cmd_obj = {"id": msg_id, "method": method, "params": params or {}}
    msg_id += 1
    ws.send(json.dumps(cmd_obj))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == cmd_obj["id"]:
            return r.get("result", {})

def evaluate(expr):
    global msg_id, ws
    cmd_obj = {
        "id": msg_id,
        "method": "Runtime.evaluate",
        "params": {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": True
        }
    }
    msg_id += 1
    ws.send(json.dumps(cmd_obj))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == cmd_obj["id"]:
            if "exceptionDetails" in r.get("result", {}):
                print("JS EXC:", r["result"]["exceptionDetails"])
            return r.get("result", {}).get("result", {}).get("value")

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
    send_cmd("Page.enable")
    send_cmd("DOM.enable")

    # 1. Setup dev user session
    evaluate("""
    (async () => {
        const u = { id: 'u1', email: 'alex@tempo.test', user_metadata: { display_name: 'Alex' } };
        localStorage.setItem('tempo_local_dev_user', JSON.stringify(u));
        localStorage.setItem('tempo_mock_account_alex@tempo.test', JSON.stringify(u));
        if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
            await window.TempoAuth.checkSession();
        }
    })()
    """)
    time.sleep(1)

    # Setup a plan with 3 tasks with 15 min, 60 min (1 hr), 90 min (1 hr 30 min)
    setup_res = evaluate("""
    (() => {
        localStorage.setItem('tempo_lang', 'vi');
        if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
            window.TempoI18n.setLanguage('vi');
        }

        const todayStr = '2026-11-01';
        const testPlan = {
            id: 'plan_test_step1',
            planId: 'plan_test_step1',
            planType: 'emergency',
            title: 'Tempo Working Plan',
            tasks: [
                { id: 'task_15m', name: 'Đọc tài liệu tham khảo', durationMinutes: 15, durationLabel: '15 min', status: 'pending', scheduledDate: todayStr },
                { id: 'task_60m', name: 'Viết đề cương nghiên cứu', durationMinutes: 60, durationLabel: '1 hr', status: 'pending', scheduledDate: todayStr },
                { id: 'task_90m', name: 'Làm bài tập lớn chương 3', durationMinutes: 90, durationLabel: '1 hr 30 min', status: 'pending', scheduledDate: todayStr }
            ],
            plannedTasks: [
                { task: { id: 'task_15m', name: 'Đọc tài liệu tham khảo', durationMinutes: 15, durationLabel: '15 min' }, dayDate: todayStr, startTime: '19:00', endTime: '19:15' },
                { task: { id: 'task_60m', name: 'Viết đề cương nghiên cứu', durationMinutes: 60, durationLabel: '1 hr' }, dayDate: todayStr, startTime: '19:30', endTime: '20:30' },
                { task: { id: 'task_90m', name: 'Làm bài tập lớn chương 3', durationMinutes: 90, durationLabel: '1 hr 30 min' }, dayDate: todayStr, startTime: '21:00', endTime: '22:30' }
            ],
            unarrangedTasks: [],
            availabilityDays: [
                { date: todayStr, label: 'Hôm nay', blocks: [{ id: 'b1', start: '19:00', end: '23:00' }] }
            ]
        };

        localStorage.setItem('tempo_working_plan', JSON.stringify(testPlan));
        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            window.TempoPlanStore.saveActivePlan('emergency', testPlan);
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
            window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
        }

        if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.startAdjustmentFlow === 'function') {
            window.TempoUrmodeFlow.startAdjustmentFlow();
            return true;
        }
        return false;
    })()
    """)
    print("startAdjustmentFlow triggered:", setup_res)
    time.sleep(0.5)

    # =========================================================================
    # PART 1: VERIFY VIETNAMESE (vi) MODE
    # =========================================================================
    print("\n--- PART 1: VERIFY VIETNAMESE (vi) MODE ---")
    modal_vi = evaluate("""
    (() => {
        const modal = document.getElementById('modal-urmode-flow');
        if (!modal || modal.classList.contains('hidden')) return { exists: false };

        const stepBadge = modal.querySelector('span.uppercase.tracking-widest')?.innerText?.trim();
        const heading = modal.querySelector('h2')?.innerText?.trim();
        const desc = modal.querySelector('p')?.innerText?.trim();
        const closeBtnTitle = modal.querySelector('button[aria-label]')?.getAttribute('title')?.trim();
        const cancelBtn = modal.querySelectorAll('button')[1]?.innerText?.trim();
        const nextBtn = modal.querySelectorAll('button')[2]?.innerText?.trim();

        // Task items
        const taskLabels = [...modal.querySelectorAll('label')].map(lbl => {
            const spans = lbl.querySelectorAll('span');
            const name = spans[0]?.innerText?.trim();
            const dur = spans[1]?.innerText?.trim();
            const checked = lbl.querySelector('input[type="checkbox"]')?.checked;
            return { name, dur, checked };
        });

        return {
            exists: true,
            stepBadge,
            heading,
            desc,
            closeBtnTitle,
            cancelBtn,
            nextBtn,
            taskLabels
        };
    })()
    """)
    print("modal_vi:", json.dumps(modal_vi, ensure_ascii=False, indent=2))

    assert modal_vi["exists"], "Modal is not open!"
    assert modal_vi["stepBadge"] == "BƯỚC 1/3 · ĐIỀU CHỈNH PLAN", f"stepBadge mismatch: {modal_vi['stepBadge']}"
    assert modal_vi["heading"] == "Chọn các task muốn giữ lại", f"heading mismatch: {modal_vi['heading']}"
    assert modal_vi["desc"] == "Chọn những task bạn vẫn cần hoàn thành. Bạn có thể giữ lại hoặc loại bỏ các task đã quá hạn hoặc hoàn thành.", f"desc mismatch: {modal_vi['desc']}"
    assert modal_vi["cancelBtn"] == "Hủy điều chỉnh", f"cancelBtn mismatch: {modal_vi['cancelBtn']}"
    assert modal_vi["nextBtn"] == "Tiếp theo: Điều chỉnh & thêm task →", f"nextBtn mismatch: {modal_vi['nextBtn']}"

    # Verify task durations in VI
    durations_vi = [t["dur"] for t in modal_vi["taskLabels"]]
    print("durations_vi:", durations_vi)
    assert "~15 phút" in durations_vi, f"Expected ~15 phút in {durations_vi}"
    assert "~1 giờ" in durations_vi, f"Expected ~1 giờ in {durations_vi}"
    assert "~1 giờ 30 phút" in durations_vi, f"Expected ~1 giờ 30 phút in {durations_vi}"

    capture_screenshot("adjust_plan_step1_vi.png")

    # =========================================================================
    # PART 2: TOGGLE TASK CHECKBOX STATE
    # =========================================================================
    print("\n--- PART 2: TOGGLE TASK CHECKBOX ---")
    toggle_res = evaluate("""
    (() => {
        const modal = document.getElementById('modal-urmode-flow');
        const firstCheckbox = modal.querySelector('input[type="checkbox"]');
        if (firstCheckbox) {
            firstCheckbox.click();
            return {
                clicked: true,
                newCheckedState: firstCheckbox.checked
            };
        }
        return { clicked: false };
    })()
    """)
    print("toggle_res:", toggle_res)
    assert toggle_res["clicked"] and toggle_res["newCheckedState"] is False, "Checkbox toggle failed!"

    # =========================================================================
    # PART 3: SWITCH LANGUAGE IMMEDIATELY TO ENGLISH (en)
    # =========================================================================
    print("\n--- PART 3: SWITCH TO ENGLISH (en) ---")
    evaluate("""
    (() => {
        window.TempoI18n.setLanguage('en');
    })()
    """)
    time.sleep(0.5)

    modal_en = evaluate("""
    (() => {
        const modal = document.getElementById('modal-urmode-flow');
        if (!modal || modal.classList.contains('hidden')) return { exists: false };

        const stepBadge = modal.querySelector('span.uppercase.tracking-widest')?.innerText?.trim();
        const heading = modal.querySelector('h2')?.innerText?.trim();
        const desc = modal.querySelector('p')?.innerText?.trim();
        const cancelBtn = modal.querySelectorAll('button')[1]?.innerText?.trim();
        const nextBtn = modal.querySelectorAll('button')[2]?.innerText?.trim();

        const taskLabels = [...modal.querySelectorAll('label')].map(lbl => {
            const spans = lbl.querySelectorAll('span');
            const name = spans[0]?.innerText?.trim();
            const dur = spans[1]?.innerText?.trim();
            const checked = lbl.querySelector('input[type="checkbox"]')?.checked;
            return { name, dur, checked };
        });

        return {
            exists: true,
            stepBadge,
            heading,
            desc,
            cancelBtn,
            nextBtn,
            taskLabels
        };
    })()
    """)
    print("modal_en:", json.dumps(modal_en, ensure_ascii=False, indent=2))

    assert modal_en["exists"], "Modal closed during language switch!"
    assert modal_en["stepBadge"] == "STEP 1 OF 3 · ADJUST PLAN", f"stepBadge mismatch: {modal_en['stepBadge']}"
    assert modal_en["heading"] == "Choose tasks to keep", f"heading mismatch: {modal_en['heading']}"
    assert modal_en["desc"] == "Select the tasks you still need to complete. Overdue or completed tasks can be removed or kept.", f"desc mismatch: {modal_en['desc']}"
    assert modal_en["cancelBtn"] == "Cancel adjustment", f"cancelBtn mismatch: {modal_en['cancelBtn']}"
    assert modal_en["nextBtn"] == "Next: Adjust & add tasks →", f"nextBtn mismatch: {modal_en['nextBtn']}"

    # Verify task durations in EN
    durations_en = [t["dur"] for t in modal_en["taskLabels"]]
    print("durations_en:", durations_en)
    assert "~15 min" in durations_en, f"Expected ~15 min in {durations_en}"
    assert "~1 hr" in durations_en, f"Expected ~1 hr in {durations_en}"
    assert "~1 hr 30 min" in durations_en, f"Expected ~1 hr 30 min in {durations_en}"

    # Verify toggled checkbox state was preserved across language switch
    assert modal_en["taskLabels"][0]["checked"] is False, "Toggled checkbox state was lost during language switch!"

    capture_screenshot("adjust_plan_step1_en.png")

    # =========================================================================
    # PART 4: TEST NEXT STEP NAVIGATION
    # =========================================================================
    print("\n--- PART 4: TEST NEXT STEP NAVIGATION ---")
    next_res = evaluate("""
    (() => {
        const modal = document.getElementById('modal-urmode-flow');
        const nextBtn = modal.querySelectorAll('button')[2];
        if (nextBtn) {
            nextBtn.click();
            return true;
        }
        return false;
    })()
    """)
    time.sleep(0.5)

    step2_check = evaluate("""
    (() => {
        const modal = document.getElementById('modal-urmode-flow');
        const badge = modal.querySelector('span.uppercase.tracking-widest')?.innerText?.trim();
        return {
            badge
        };
    })()
    """)
    print("step2_check:", step2_check)
    assert "STEP 2" in step2_check["badge"], f"Expected to navigate to Step 2, but got: {step2_check['badge']}"

    print("\nALL ADJUST PLAN STEP 1 VERIFICATION TESTS PASSED SUCCESSFULLY!")

finally:
    try:
        ws.close()
    except:
        pass
    proc.terminate()
