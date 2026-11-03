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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_recurrence_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9580

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

    # 1. Setup dev user session and ensure plan workspace is mounted
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

    # =========================================================================
    # PART 1: TEST COPY TO TOMORROW IN VIETNAMESE MODE
    # =========================================================================
    print("\n--- PART 1: TEST COPY TO TOMORROW (VI) ---")
    
    evaluate("""
    (() => {
        localStorage.setItem('tempo_lang', 'vi');
        if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
            window.TempoI18n.setLanguage('vi');
        }

        const now = new Date();
        const pad = n => String(n).padStart(2, '0');
        const todayStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
        const tomorrowObj = new Date(now.getTime() + 86400000);
        const tomorrowStr = `${tomorrowObj.getFullYear()}-${pad(tomorrowObj.getMonth() + 1)}-${pad(tomorrowObj.getDate())}`;

        const testPlan = {
            id: 'plan_test_copy',
            planId: 'plan_test_copy',
            planType: 'emergency',
            title: 'Tempo Working Plan',
            tasks: [
                { id: 't1', title: 'Task 1', duration: 60, status: 'pending', scheduledDate: todayStr }
            ],
            plannedTasks: [
                {
                    task: { id: 't1', title: 'Task 1', duration: 60, status: 'pending' },
                    dayDate: todayStr,
                    startTime: '19:00',
                    endTime: '20:00'
                }
            ],
            unarrangedTasks: [],
            availabilityDays: [
                {
                    date: todayStr,
                    label: 'Hôm nay',
                    isUnavailable: false,
                    blocks: [
                        { id: 'b_today_1', start: '19:00', end: '21:00' },
                        { id: 'b_today_2', start: '21:30', end: '23:30' }
                    ]
                },
                {
                    date: tomorrowStr,
                    label: 'Ngày mai',
                    isUnavailable: false,
                    blocks: [
                        { id: 'b_tom_pre', start: '09:00', end: '11:00' }
                    ]
                }
            ],
            recurringAvailabilityRules: []
        };

        localStorage.setItem('tempo_working_plan', JSON.stringify(testPlan));
        localStorage.setItem('tempo_availability_days', JSON.stringify(testPlan.availabilityDays));
        localStorage.removeItem('tempo_availability_recurring_rules');

        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            window.TempoPlanStore.saveActivePlan('emergency', testPlan);
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
            window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
        }

        if (window.TempoPlanWorkspace) {
            window.TempoPlanWorkspace.render();
            window.TempoPlanWorkspace.openAdjustAvailabilityModal();
        }
    })()
    """)
    time.sleep(0.5)

    btn_copy_info = evaluate("""
    (() => {
        const btn = document.getElementById('btn-copy-to-tomorrow');
        return {
            exists: !!btn,
            text: btn ? btn.innerText.trim() : null,
            title: btn ? btn.getAttribute('title') : null
        };
    })()
    """)
    print("btn_copy_info (VI):", json.dumps(btn_copy_info, ensure_ascii=False))
    assert btn_copy_info["exists"], "btn-copy-to-tomorrow not found!"
    assert "Sao chép sang ngày mai" in btn_copy_info["text"], f"Unexpected text: {btn_copy_info['text']}"

    # Click Copy to Tomorrow
    evaluate("""
    (() => {
        const btn = document.getElementById('btn-copy-to-tomorrow');
        if (btn) btn.click();
    })()
    """)
    time.sleep(0.5)

    # Verify tomorrow's blocks
    check_tomorrow = evaluate("""
    (() => {
        const now = new Date();
        const tomorrowObj = new Date(now.getTime() + 86400000);
        const pad = n => String(n).padStart(2, '0');
        const tomorrowStr = `${tomorrowObj.getFullYear()}-${pad(tomorrowObj.getMonth() + 1)}-${pad(tomorrowObj.getDate())}`;

        const plan = JSON.parse(localStorage.getItem('tempo_working_plan'));
        const tomorrow = plan.availabilityDays.find(d => d.date === tomorrowStr);
        return {
            tomorrowStr: tomorrowStr,
            blocks: tomorrow ? tomorrow.blocks : []
        };
    })()
    """)
    print("Tomorrow blocks after copy:", json.dumps(check_tomorrow, ensure_ascii=False))
    assert len(check_tomorrow["blocks"]) == 3, f"Expected 3 blocks tomorrow, got {len(check_tomorrow['blocks'])}"
    times = [(b["start"], b["end"]) for b in check_tomorrow["blocks"]]
    assert ("09:00", "11:00") in times, "Pre-existing 09:00-11:00 slot missing!"
    assert ("19:00", "21:00") in times, "Copied 19:00-21:00 slot missing!"
    assert ("21:30", "23:30") in times, "Copied 21:30-23:30 slot missing!"

    # Test deduplication on repeated click
    evaluate("""
    (() => {
        const btn = document.getElementById('btn-copy-to-tomorrow');
        if (btn) btn.click();
    })()
    """)
    time.sleep(0.3)
    check_dedup = evaluate("""
    (() => {
        const now = new Date();
        const tomorrowObj = new Date(now.getTime() + 86400000);
        const pad = n => String(n).padStart(2, '0');
        const tomorrowStr = `${tomorrowObj.getFullYear()}-${pad(tomorrowObj.getMonth() + 1)}-${pad(tomorrowObj.getDate())}`;

        const plan = JSON.parse(localStorage.getItem('tempo_working_plan'));
        const tomorrow = plan.availabilityDays.find(d => d.date === tomorrowStr);
        return {
            blockCount: tomorrow ? tomorrow.blocks.length : 0
        };
    })()
    """)
    assert check_dedup["blockCount"] == 3, f"Deduplication failed: got {check_dedup['blockCount']} blocks"
    print("Deduplication verified: block count remains 3.")

    # Capture screenshot for copy to tomorrow
    capture_screenshot("availability_copy_to_tomorrow_vi.png")

    # =========================================================================
    # PART 2: TEST REPEAT WEEKLY MODAL IN VIETNAMESE MODE
    # =========================================================================
    print("\n--- PART 2: TEST REPEAT WEEKLY (VI) ---")
    
    # Open repeat weekly modal on tomorrow
    evaluate("""
    (() => {
        const now = new Date();
        const tomorrowObj = new Date(now.getTime() + 86400000);
        const pad = n => String(n).padStart(2, '0');
        const tomorrowStr = `${tomorrowObj.getFullYear()}-${pad(tomorrowObj.getMonth() + 1)}-${pad(tomorrowObj.getDate())}`;

        window.TempoPlanWorkspace.openRepeatWeeklyModal(tomorrowStr);
    })()
    """)
    time.sleep(0.5)

    modal_vi_info = evaluate("""
    (() => {
        const modal = document.getElementById('modal-repeat-weekly');
        if (!modal) return { exists: false };
        const title = modal.querySelector('h3')?.innerText?.trim();
        const cbLabel = modal.querySelector('label[for="pw-repeat-every-week"]')?.innerText?.trim();
        const startLabel = modal.querySelectorAll('label')[1]?.innerText?.trim();
        const endLabel = modal.querySelectorAll('label')[2]?.innerText?.trim();
        const cancelBtn = modal.querySelector('button[onclick*="closeRepeatWeeklyModal"]:not(.absolute)')?.innerText?.trim();
        const confirmBtn = document.getElementById('btn-confirm-repeat-weekly')?.innerText?.trim();
        return {
            exists: true,
            title,
            cbLabel,
            startLabel,
            endLabel,
            cancelBtn,
            confirmBtn
        };
    })()
    """)
    print("modal_vi_info:", json.dumps(modal_vi_info, ensure_ascii=False))
    assert modal_vi_info["exists"], "Repeat Weekly modal not rendered!"
    assert modal_vi_info["title"] == "Lặp lại hàng tuần", f"Title mismatch: {modal_vi_info['title']}"
    assert modal_vi_info["cbLabel"] == "Lặp lại mỗi tuần", f"cbLabel mismatch: {modal_vi_info['cbLabel']}"
    assert modal_vi_info["startLabel"] == "Ngày bắt đầu", f"startLabel mismatch: {modal_vi_info['startLabel']}"
    assert modal_vi_info["endLabel"] == "Ngày kết thúc (không bắt buộc)", f"endLabel mismatch: {modal_vi_info['endLabel']}"
    assert modal_vi_info["cancelBtn"] == "Hủy", f"cancelBtn mismatch: {modal_vi_info['cancelBtn']}"
    assert modal_vi_info["confirmBtn"] == "Xác nhận", f"confirmBtn mismatch: {modal_vi_info['confirmBtn']}"

    capture_screenshot("availability_repeat_weekly_modal_vi.png")

    # Confirm recurrence
    evaluate("""
    (() => {
        const btn = document.getElementById('btn-confirm-repeat-weekly');
        if (btn) btn.click();
    })()
    """)
    time.sleep(0.5)

    # Check recurring rule generated subsequent weeks
    check_recurrence_gen = evaluate("""
    (() => {
        const plan = JSON.parse(localStorage.getItem('tempo_working_plan'));
        const rules = JSON.parse(localStorage.getItem('tempo_availability_recurring_rules') || '[]');
        return {
            rulesCount: rules.length,
            rule: rules[0],
            totalDays: plan.availabilityDays.length,
            futureDaysWithRecurringBlocks: plan.availabilityDays.filter(d => 
                d.blocks && d.blocks.some(b => b.id.startsWith('b_rec_'))
            ).map(d => ({ date: d.date, blockCount: d.blocks.length }))
        };
    })()
    """)
    print("check_recurrence_gen:", json.dumps(check_recurrence_gen, ensure_ascii=False))
    assert check_recurrence_gen["rulesCount"] >= 1, "Recurring rule not saved!"
    assert len(check_recurrence_gen["futureDaysWithRecurringBlocks"]) >= 7, f"Expected at least 7 recurring future days generated, got {len(check_recurrence_gen['futureDaysWithRecurringBlocks'])}"

    # =========================================================================
    # PART 3: TEST REPEAT WEEKLY MODAL IN ENGLISH MODE
    # =========================================================================
    print("\n--- PART 3: TEST REPEAT WEEKLY & COPY (EN) ---")
    
    evaluate("""
    (() => {
        localStorage.setItem('tempo_lang', 'en');
        if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
            window.TempoI18n.setLanguage('en');
        }

        const now = new Date();
        const tomorrowObj = new Date(now.getTime() + 86400000);
        const pad = n => String(n).padStart(2, '0');
        const tomorrowStr = `${tomorrowObj.getFullYear()}-${pad(tomorrowObj.getMonth() + 1)}-${pad(tomorrowObj.getDate())}`;

        window.TempoPlanWorkspace.render();
        window.TempoPlanWorkspace.openRepeatWeeklyModal(tomorrowStr);
    })()
    """)
    time.sleep(0.5)

    modal_en_info = evaluate("""
    (() => {
        const modal = document.getElementById('modal-repeat-weekly');
        if (!modal) return { exists: false };
        const title = modal.querySelector('h3')?.innerText?.trim();
        const cbLabel = modal.querySelector('label[for="pw-repeat-every-week"]')?.innerText?.trim();
        const startLabel = modal.querySelectorAll('label')[1]?.innerText?.trim();
        const endLabel = modal.querySelectorAll('label')[2]?.innerText?.trim();
        const cancelBtn = modal.querySelector('button[onclick*="closeRepeatWeeklyModal"]:not(.absolute)')?.innerText?.trim();
        const confirmBtn = document.getElementById('btn-confirm-repeat-weekly')?.innerText?.trim();
        return {
            exists: true,
            title,
            cbLabel,
            startLabel,
            endLabel,
            cancelBtn,
            confirmBtn
        };
    })()
    """)
    print("modal_en_info:", json.dumps(modal_en_info, ensure_ascii=False))
    assert modal_en_info["exists"], "Repeat Weekly modal (EN) not rendered!"
    assert modal_en_info["title"] == "Repeat Weekly", f"Title mismatch: {modal_en_info['title']}"
    assert modal_en_info["cbLabel"] == "Repeat every week", f"cbLabel mismatch: {modal_en_info['cbLabel']}"
    assert modal_en_info["startLabel"] == "Start date", f"startLabel mismatch: {modal_en_info['startLabel']}"
    assert modal_en_info["endLabel"] == "End date (optional)", f"endLabel mismatch: {modal_en_info['endLabel']}"
    assert modal_en_info["cancelBtn"] == "Cancel", f"cancelBtn mismatch: {modal_en_info['cancelBtn']}"
    assert modal_en_info["confirmBtn"] == "Confirm", f"confirmBtn mismatch: {modal_en_info['confirmBtn']}"

    capture_screenshot("availability_repeat_weekly_modal_en.png")

    # Close modal and check Copy to Tomorrow button in EN
    evaluate("""
    (() => {
        window.TempoPlanWorkspace.closeRepeatWeeklyModal();
    })()
    """)
    time.sleep(0.3)

    btn_copy_en = evaluate("""
    (() => {
        const btn = document.getElementById('btn-copy-to-tomorrow');
        return {
            exists: !!btn,
            text: btn ? btn.innerText.trim() : null
        };
    })()
    """)
    print("btn_copy_en:", json.dumps(btn_copy_en, ensure_ascii=False))
    assert btn_copy_en["exists"], "btn-copy-to-tomorrow missing in EN!"
    assert "Copy to Tomorrow" in btn_copy_en["text"], f"Unexpected text: {btn_copy_en['text']}"

    # =========================================================================
    # PART 4: TEST DISABLE RECURRENCE
    # =========================================================================
    print("\n--- PART 4: TEST DISABLE RECURRENCE ---")
    evaluate("""
    (() => {
        const now = new Date();
        const tomorrowObj = new Date(now.getTime() + 86400000);
        const pad = n => String(n).padStart(2, '0');
        const tomorrowStr = `${tomorrowObj.getFullYear()}-${pad(tomorrowObj.getMonth() + 1)}-${pad(tomorrowObj.getDate())}`;

        window.TempoPlanWorkspace.openRepeatWeeklyModal(tomorrowStr);
    })()
    """)
    time.sleep(0.3)

    # Uncheck repeat every week and confirm
    evaluate("""
    (() => {
        const cb = document.getElementById('pw-repeat-every-week');
        if (cb) cb.checked = false;
        const btn = document.getElementById('btn-confirm-repeat-weekly');
        if (btn) btn.click();
    })()
    """)
    time.sleep(0.5)

    check_disable = evaluate("""
    (() => {
        const plan = JSON.parse(localStorage.getItem('tempo_working_plan'));
        const rules = JSON.parse(localStorage.getItem('tempo_availability_recurring_rules') || '[]');
        return {
            ruleEnabled: rules[0]?.enabled,
            recurringBlocksCount: plan.availabilityDays.reduce((acc, d) => {
                return acc + (d.blocks || []).filter(b => b.id.startsWith('b_rec_')).length;
            }, 0)
        };
    })()
    """)
    print("check_disable:", json.dumps(check_disable, ensure_ascii=False))
    assert check_disable["ruleEnabled"] is False, "Rule should be disabled!"
    assert check_disable["recurringBlocksCount"] == 0, f"Future recurring blocks should be purged, but found {check_disable['recurringBlocksCount']}"

    # =========================================================================
    # PART 5: TEST COPY WHEN TODAY HAS NO WORKING HOURS
    # =========================================================================
    print("\n--- PART 5: TEST COPY WHEN TODAY HAS NO SLOTS ---")
    toast_msg = evaluate("""
    (() => {
        const now = new Date();
        const pad = n => String(n).padStart(2, '0');
        const todayStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

        const plan = JSON.parse(localStorage.getItem('tempo_working_plan'));
        const today = plan.availabilityDays.find(d => d.date === todayStr);
        if (today) today.blocks = [];
        localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
        localStorage.setItem('tempo_availability_days', JSON.stringify(plan.availabilityDays));
        if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
            window.TempoPlanStore.saveActivePlan('emergency', plan);
        }
        if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
            window.TempoEmergencyFlow.setConfirmedPlan(plan);
        }
        window.TempoPlanWorkspace.render();
        window.TempoPlanWorkspace.openAdjustAvailabilityModal();

        let capturedToast = null;
        if (window.TempoApp) {
            window.TempoApp.showToast = msg => { capturedToast = msg; };
        }
        window.alert = msg => { capturedToast = msg; };

        const btn = document.getElementById('btn-copy-to-tomorrow');
        if (btn) btn.click();
        else window.TempoPlanWorkspace.copyTodayAvailabilityToTomorrow();
        return capturedToast;
    })()
    """)
    print("toast_msg on empty today:", toast_msg)
    assert toast_msg == "No working hours available to copy.", f"Unexpected toast message: {toast_msg}"

    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")

finally:
    try:
        ws.close()
    except:
        pass
    proc.terminate()
