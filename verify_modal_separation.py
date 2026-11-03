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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_modals_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9598

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

    # 1. Setup dev user session and active plan
    evaluate("""
    (async () => {
        const u = { id: 'u1', email: 'alex@tempo.test', user_metadata: { display_name: 'Alex' } };
        localStorage.setItem('tempo_local_dev_user', JSON.stringify(u));
        localStorage.setItem('tempo_mock_account_alex@tempo.test', JSON.stringify(u));
        if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
            await window.TempoAuth.checkSession();
        }

        localStorage.setItem('tempo_lang', 'vi');
        if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
            window.TempoI18n.setLanguage('vi');
        }

        const todayStr = '2026-11-01';
        const testPlan = {
            id: 'plan_test_sep',
            planId: 'plan_test_sep',
            planType: 'emergency',
            title: 'Tempo Working Plan',
            tasks: [
                { id: 't1', name: 'Thesis Literature Review', durationMinutes: 60, status: 'pending', scheduledDate: todayStr },
                { id: 't2', name: 'Methodology Outline', durationMinutes: 90, status: 'pending', scheduledDate: todayStr }
            ],
            plannedTasks: [
                { task: { id: 't1', name: 'Thesis Literature Review', durationMinutes: 60 }, dayDate: todayStr, startTime: '19:00', endTime: '20:00' },
                { task: { id: 't2', name: 'Methodology Outline', durationMinutes: 90 }, dayDate: todayStr, startTime: '20:30', endTime: '22:00' }
            ],
            unarrangedTasks: [],
            availabilityDays: [
                { date: todayStr, label: 'Hôm nay', blocks: [{ id: 'b1', start: '19:00', end: '23:00' }] }
            ]
        };

        localStorage.setItem('tempo_working_plan', JSON.stringify(testPlan));
        localStorage.setItem('tempo_availability_days', JSON.stringify(testPlan.availabilityDays));
        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            window.TempoPlanStore.saveActivePlan('emergency', testPlan);
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
            window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
        }

        window.location.hash = '#plan-workspace';
        window.TempoPlanWorkspace.render();
    })()
    """)
    time.sleep(1)

    # =========================================================================
    # TEST A: CLICK "ADD AVAILABILITY" BUTTON
    # =========================================================================
    print("\n--- TEST A: CLICK ADD AVAILABILITY ---")
    avail_click = evaluate("""
    (() => {
        const btns = [...document.querySelectorAll('button')];
        const availBtn = btns.find(b => b.innerText.includes('Thêm thời gian làm việc') || b.innerText.includes('Add availability'));
        if (availBtn) {
            availBtn.click();
            return true;
        }
        return false;
    })()
    """)
    time.sleep(0.5)

    status_a = evaluate("""
    (() => {
        const modalContainer = document.querySelector('#plan-workspace-root .fixed');
        const h3 = modalContainer ? modalContainer.querySelector('h3') : null;
        const urmodeModal = document.getElementById('modal-urmode-flow');
        const isUrmodeOpen = urmodeModal && !urmodeModal.classList.contains('hidden');

        return {
            availModalOpen: !!modalContainer,
            modalTitle: h3 ? h3.innerText.trim() : null,
            urmodeStep1Open: isUrmodeOpen
        };
    })()
    """)
    print("Status after clicking Add availability:", json.dumps(status_a, ensure_ascii=False, indent=2))
    assert status_a["availModalOpen"], "Availability modal did not open!"
    assert "Thời gian làm việc của bạn" in status_a["modalTitle"] or "Your available time" in status_a["modalTitle"], f"Wrong title: {status_a['modalTitle']}"
    assert not status_a["urmodeStep1Open"], "Adjust Plan modal should NOT be open!"

    capture_screenshot("fix_add_availability_modal.png")

    # Close availability modal
    evaluate("""
    (() => {
        window.TempoPlanWorkspace.closeAdjustAvailabilityModal();
    })()
    """)
    time.sleep(0.3)

    closed_check = evaluate("""
    (() => {
        const modalContainer = document.querySelector('#plan-workspace-root .fixed');
        return !modalContainer;
    })()
    """)
    assert closed_check, "Availability modal did not close!"
    print("Availability modal closed cleanly.")

    # =========================================================================
    # TEST B: CLICK "ADJUST PLAN" BUTTON
    # =========================================================================
    print("\n--- TEST B: CLICK ADJUST PLAN ---")
    adjust_click = evaluate("""
    (() => {
        const btns = [...document.querySelectorAll('button')];
        const adjustBtn = btns.find(b => b.innerText.includes('Điều chỉnh plan') || b.innerText.includes('Adjust Plan'));
        if (adjustBtn) {
            adjustBtn.click();
            return true;
        }
        return false;
    })()
    """)
    time.sleep(0.5)

    status_b = evaluate("""
    (() => {
        const modalContainer = document.querySelector('#plan-workspace-root .fixed');
        const h3 = modalContainer ? modalContainer.querySelector('h3') : null;
        const urmodeModal = document.getElementById('modal-urmode-flow');
        const isUrmodeOpen = urmodeModal && !urmodeModal.classList.contains('hidden');
        const step1Badge = urmodeModal ? urmodeModal.querySelector('span.uppercase.tracking-widest')?.innerText?.trim() : null;
        const heading = urmodeModal ? urmodeModal.querySelector('h2')?.innerText?.trim() : null;

        return {
            availModalTitle: h3 ? h3.innerText.trim() : null,
            urmodeStep1Open: isUrmodeOpen,
            step1Badge,
            heading
        };
    })()
    """)
    print("Status after clicking Adjust Plan:", json.dumps(status_b, ensure_ascii=False, indent=2))
    assert status_b["urmodeStep1Open"], "Adjust Plan Step 1 modal did not open!"
    assert status_b["step1Badge"] == "BƯỚC 1/3 · ĐIỀU CHỈNH PLAN", f"Wrong badge: {status_b['step1Badge']}"
    assert status_b["heading"] == "Chọn các task muốn giữ lại", f"Wrong heading: {status_b['heading']}"
    assert status_b["availModalTitle"] is None or "Thời gian làm việc của bạn" not in status_b["availModalTitle"], "Availability modal opened when Adjust Plan was clicked!"

    capture_screenshot("fix_adjust_plan_step1_modal.png")

    # Close Adjust Plan modal
    evaluate("""
    (() => {
        const modal = document.getElementById('modal-urmode-flow');
        const cancelBtn = modal ? modal.querySelectorAll('button')[1] : null;
        if (cancelBtn) cancelBtn.click();
    })()
    """)
    time.sleep(0.3)

    closed_b = evaluate("""
    (() => {
        const urmodeModal = document.getElementById('modal-urmode-flow');
        return urmodeModal.classList.contains('hidden');
    })()
    """)
    assert closed_b, "Adjust Plan modal did not close on cancel!"
    print("Adjust Plan modal closed cleanly.")

    # =========================================================================
    # TEST C: INTERLEAVING TEST
    # =========================================================================
    print("\n--- TEST C: REPEATED INTERLEAVING TESTS ---")
    for i in range(2):
        print(f"Cycle {i+1}:")
        # 1. Click Add availability
        evaluate("""
        (() => {
            const btns = [...document.querySelectorAll('button')];
            const btn = btns.find(b => b.innerText.includes('Thêm thời gian làm việc') || b.innerText.includes('Add availability'));
            if (btn) btn.click();
        })()
        """)
        time.sleep(0.2)
        chk_a = evaluate("!!document.querySelector('#plan-workspace-root .fixed') && document.getElementById('modal-urmode-flow')?.classList.contains('hidden') === true")
        print(f"  Add availability opened properly: {chk_a}")
        evaluate("window.TempoPlanWorkspace.closeAdjustAvailabilityModal()")
        time.sleep(0.2)

        # 2. Click Adjust Plan
        evaluate("""
        (() => {
            const btns = [...document.querySelectorAll('button')];
            const btn = btns.find(b => b.innerText.includes('Điều chỉnh plan') || b.innerText.includes('Adjust Plan'));
            if (btn) btn.click();
        })()
        """)
        time.sleep(0.2)
        badge = evaluate("document.getElementById('modal-urmode-flow')?.querySelector('span.uppercase.tracking-widest')?.innerText?.trim()")
        print(f"  Adjust Plan opened Step 1 properly: {badge}")
        assert badge == "BƯỚC 1/3 · ĐIỀU CHỈNH PLAN"
        evaluate("window.TempoUrmodeFlow.closeModal('plan-workspace')")
        time.sleep(0.2)

    print("\nALL VERIFICATION TESTS FOR SEPARATE WORKFLOWS PASSED!")

finally:
    try:
        ws.close()
    except:
        pass
    proc.terminate()
