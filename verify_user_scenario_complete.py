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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_user_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9296

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,900",
    "http://127.0.0.1:8000/#tool-workplan"
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
        print(f"Screenshot saved: {filepath}")

try:
    time.sleep(2)
    tabs_res = urllib.request.urlopen(f"http://127.0.0.1:{port}/json").read().decode()
    tabs = json.loads(tabs_res)
    app_tabs = [t for t in tabs if "127.0.0.1:8000" in t.get("url", "") or "localhost:8000" in t.get("url", "")]
    target_tab = app_tabs[0] if app_tabs else tabs[0]
    ws_url = target_tab["webSocketDebuggerUrl"]
    ws = websocket.create_connection(ws_url)

    send_cmd("Page.enable")
    send_cmd("Runtime.enable")
    time.sleep(2)

    print("=====================================================================")
    print("STEP 1: INSPECT INITIAL STATE & OPEN RESCHEDULE MODAL FOR TASK")
    print("=====================================================================")
    init_state = eval_js("""
    (() => {
        const plan = window.TempoPlanWorkspace.getActivePlan();
        const firstPt = plan && plan.plannedTasks && plan.plannedTasks[0];
        return {
            today: window.TempoI18n ? window.TempoI18n.getLocalTodayISO() : null,
            tomorrow: window.TempoI18n ? window.TempoI18n.getLocalTomorrowISO() : null,
            targetTaskId: firstPt ? firstPt.task?.id : null,
            targetTaskName: firstPt ? firstPt.task?.name : null,
            targetTaskDay: firstPt ? firstPt.dayDate : null,
            targetTaskStart: firstPt ? firstPt.startTime : null,
            targetTaskEnd: firstPt ? firstPt.endTime : null,
            availabilityDaysCount: plan && plan.availabilityDays ? plan.availabilityDays.length : 0,
            availabilityDates: plan && plan.availabilityDays ? plan.availabilityDays.map(d => d.date) : []
        };
    })()
    """)
    print("Initial State:", json.dumps(init_state, indent=2, ensure_ascii=False))
    task_id = init_state["targetTaskId"]
    assert task_id, "Target task ID must exist!"

    # Open modal
    eval_js(f"window.TempoPlanWorkspace.openRescheduleModal('{task_id}')")
    time.sleep(0.8)

    slots_step1 = eval_js("""
    (() => {
        return Array.from(document.querySelectorAll('input[name="pw_reschedule_day"]')).map(el => ({
            value: el.value,
            date: el.getAttribute('data-date'),
            start: el.getAttribute('data-start'),
            end: el.getAttribute('data-end'),
            checked: el.checked
        }));
    })()
    """)
    print("Modal Available Slots on Open:", json.dumps(slots_step1, indent=2, ensure_ascii=False))
    capture_screenshot("step1_reschedule_modal_opened.png")

    print("\n=====================================================================")
    print("STEP 2: ADD NEW AVAILABILITY SLOT (2026-11-02, 14:00 - 16:00)")
    print("=====================================================================")
    eval_js("window.TempoPlanWorkspace.toggleRescheduleAddTime(true)")
    time.sleep(0.5)

    eval_js("""
    (() => {
        const d = document.getElementById('pw-resched-avail-date');
        const s = document.getElementById('pw-resched-avail-start');
        const e = document.getElementById('pw-resched-avail-end');
        if (d) d.value = '2026-11-02';
        if (s) s.value = '14:00';
        if (e) e.value = '16:00';
    })()
    """)
    time.sleep(0.5)
    capture_screenshot("step2_reschedule_form_filled.png")

    print("\n=====================================================================")
    print("STEP 3: CLICK 'Lưu thời gian làm việc' (SAVE AVAILABILITY)")
    print("=====================================================================")
    eval_js("window.TempoPlanWorkspace.saveRescheduleAvailability()")
    time.sleep(0.8)

    post_save_slots = eval_js("""
    (() => {
        return Array.from(document.querySelectorAll('input[name="pw_reschedule_day"]')).map(el => ({
            value: el.value,
            date: el.getAttribute('data-date'),
            start: el.getAttribute('data-start'),
            end: el.getAttribute('data-end'),
            checked: el.checked
        }));
    })()
    """)
    print("Slots after Save Availability:", json.dumps(post_save_slots, indent=2, ensure_ascii=False))
    capture_screenshot("step3_availability_saved_and_selected.png")

    nov2_slot = [s for s in post_save_slots if s["date"] == "2026-11-02" and s["start"] == "14:00"]
    assert len(nov2_slot) > 0, "November 2 slot must exist in modal slots after saving!"
    assert nov2_slot[0]["checked"], "November 2 slot should be selected automatically after saving!"

    print("\n=====================================================================")
    print("STEP 4: CLICK 'Lên lịch' (EXECUTE RESCHEDULE TO NOV 2)")
    print("=====================================================================")
    eval_js(f"window.TempoPlanWorkspace.executeReschedule('{task_id}')")
    time.sleep(1.2)

    post_resched_info = eval_js(f"""
    (() => {{
        const plan = window.TempoPlanWorkspace.getActivePlan();
        const pt = plan.plannedTasks.find(p => p.task?.id === '{task_id}');
        
        // Find which group in DOM contains the task
        const taskRow = document.querySelector('[data-task-row="{task_id}"]');
        let headingText = null;
        if (taskRow) {{
            // Traverse up to find container and its preceding h3
            let p = taskRow.parentElement;
            while (p && !headingText) {{
                const h = p.querySelector('h3.font-heading');
                if (h) headingText = h.textContent.trim();
                p = p.parentElement;
            }}
        }}
        
        const timeSlotEl = taskRow ? taskRow.querySelector('.w-16, .w-20') : null;
        const timeSlotText = timeSlotEl ? timeSlotEl.textContent.replace(/\\s+/g, ' ').trim() : null;

        return {{
            plannedDate: pt ? pt.dayDate : null,
            plannedDayLabel: pt ? pt.dayLabel : null,
            startTime: pt ? pt.startTime : null,
            endTime: pt ? pt.endTime : null,
            taskScheduledDate: pt ? pt.task?.scheduledDate : null,
            domHeading: headingText,
            domTimeSlot: timeSlotText
        }};
    }})()
    """)
    print("Working Plan Post-Reschedule Info:", json.dumps(post_resched_info, indent=2, ensure_ascii=False))
    capture_screenshot("step4_task_rescheduled_under_nov2.png")

    assert post_resched_info["plannedDate"] == "2026-11-02", f"Task MUST be scheduled for 2026-11-02! Got: {post_resched_info['plannedDate']}"
    assert "02/11/2026" in (post_resched_info["domHeading"] or ""), f"DOM Heading MUST contain 02/11/2026! Got: {post_resched_info['domHeading']}"
    print(f"SUCCESS: Task is properly rendered under '{post_resched_info['domHeading']}' with time '{post_resched_info['domTimeSlot']}'!")

    print("\n=====================================================================")
    print("STEP 5: REOPEN RESCHEDULE MODAL")
    print("=====================================================================")
    eval_js(f"window.TempoPlanWorkspace.openRescheduleModal('{task_id}')")
    time.sleep(0.8)

    reopen_slots = eval_js("""
    (() => {
        return Array.from(document.querySelectorAll('input[name="pw_reschedule_day"]')).map(el => ({
            value: el.value,
            date: el.getAttribute('data-date'),
            start: el.getAttribute('data-start'),
            end: el.getAttribute('data-end'),
            checked: el.checked
        }));
    })()
    """)
    print("Slots on Reopen:", json.dumps(reopen_slots, indent=2, ensure_ascii=False))
    capture_screenshot("step5_reopened_modal_with_nov2_slot.png")

    has_nov1 = any(s["date"] == "2026-11-01" for s in reopen_slots)
    has_nov2 = any(s["date"] == "2026-11-02" for s in reopen_slots)
    nov2_reopened = [s for s in reopen_slots if s["date"] == "2026-11-02" and s["start"] == "14:00"]

    assert has_nov2, "November 2 slot MUST be present when modal is reopened!"
    assert has_nov1, "November 1 slot MUST also be present!"
    assert len(nov2_reopened) > 0 and nov2_reopened[0]["checked"], "November 2 slot MUST be pre-selected for the rescheduled task!"
    print("SUCCESS: Both November 1 and November 2 slots exist, and November 2 slot is selected!")

    print("\n=====================================================================")
    print("STEP 6: PAGE RELOAD & PERSISTENCE VERIFICATION")
    print("=====================================================================")
    send_cmd("Page.navigate", {"url": "http://127.0.0.1:8000/#tool-workplan"})
    time.sleep(3.0)

    reload_state = eval_js(f"""
    (() => {{
        const plan = window.TempoPlanWorkspace.getActivePlan();
        const pt = plan.plannedTasks.find(p => p.task?.id === '{task_id}');
        
        const taskRow = document.querySelector('[data-task-row="{task_id}"]');
        let headingText = null;
        if (taskRow) {{
            let p = taskRow.parentElement;
            while (p && !headingText) {{
                const h = p.querySelector('h3.font-heading');
                if (h) headingText = h.textContent.trim();
                p = p.parentElement;
            }}
        }}

        return {{
            plannedDate: pt ? pt.dayDate : null,
            startTime: pt ? pt.startTime : null,
            endTime: pt ? pt.endTime : null,
            domHeading: headingText,
            availDates: plan.availabilityDays.map(d => d.date)
        }};
    }})()
    """)
    print("Reload State:", json.dumps(reload_state, indent=2, ensure_ascii=False))
    capture_screenshot("step6_persisted_after_reload.png")

    assert reload_state["plannedDate"] == "2026-11-02", f"Task date must persist after reload! Got: {reload_state['plannedDate']}"
    assert "02/11/2026" in (reload_state["domHeading"] or ""), f"Task must still be under 02/11/2026 after reload! Got: {reload_state['domHeading']}"
    assert "2026-11-02" in reload_state["availDates"], "November 2 availability must persist after reload!"
    print("ALL ASSERTIONS PASSED PERFECTLY!")

finally:
    if ws:
        ws.close()
    proc.terminate()
