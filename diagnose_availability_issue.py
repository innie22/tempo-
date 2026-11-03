import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_diag_avail_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9292

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

    print("--- 1. INITIAL INSPECTION ---")
    info = eval_js("""
    (() => {
        const plan = window.TempoPlanWorkspace ? window.TempoPlanWorkspace.getActivePlan() : null;
        const efPlan = window.TempoEmergencyFlow ? window.TempoEmergencyFlow.getConfirmedPlan() : null;
        const efAvail = window.TempoEmergencyFlow ? window.TempoEmergencyFlow.getAvailabilityDays() : null;
        return {
            today: window.TempoI18n ? window.TempoI18n.getLocalTodayISO() : null,
            tomorrow: window.TempoI18n ? window.TempoI18n.getLocalTomorrowISO() : null,
            hasPlan: !!plan,
            plannedTasksCount: plan && plan.plannedTasks ? plan.plannedTasks.length : 0,
            planAvailabilityDays: plan ? plan.availabilityDays : null,
            efConfirmedPlanAvailabilityDays: efPlan ? efPlan.availabilityDays : null,
            efAvailabilityDays: efAvail,
            tasks: plan && plan.plannedTasks ? plan.plannedTasks.map(pt => ({
                id: pt.task?.id,
                name: pt.task?.name,
                dayDate: pt.dayDate,
                startTime: pt.startTime,
                endTime: pt.endTime,
                hasDeadline: pt.task?.hasDeadline,
                deadlineDate: pt.task?.deadlineDate
            })) : []
        };
    })()
    """)
    print("Initial Info:")
    print(json.dumps(info, indent=2, ensure_ascii=False))

    first_task_id = info['tasks'][0]['id'] if info['tasks'] else None
    print(f"\nTarget Task ID for reschedule: {first_task_id}")

    print("\n--- 2. OPEN RESCHEDULE MODAL ---")
    eval_js(f"window.TempoPlanWorkspace.openRescheduleModal('{first_task_id}')")
    time.sleep(0.5)

    modal_state = eval_js("""
    (() => {
        const modal = document.querySelector('.fixed.inset-0.z-50');
        const slots = Array.from(document.querySelectorAll('input[name="pw_reschedule_day"]')).map(el => ({
            value: el.value,
            date: el.getAttribute('data-date'),
            start: el.getAttribute('data-start'),
            end: el.getAttribute('data-end'),
            checked: el.checked
        }));
        return {
            hasModal: !!modal,
            slots: slots
        };
    })()
    """)
    print("Modal State on Open:")
    print(json.dumps(modal_state, indent=2, ensure_ascii=False))

    print("\n--- 3. ADD AVAILABILITY SLOT: 2026-11-02, 14:00 - 16:00 ---")
    eval_js("window.TempoPlanWorkspace.toggleRescheduleAddTime(true)")
    time.sleep(0.3)
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
    eval_js("window.TempoPlanWorkspace.saveRescheduleAvailability()")
    time.sleep(0.5)

    post_save_state = eval_js("""
    (() => {
        const plan = window.TempoPlanWorkspace.getActivePlan();
        const efPlan = window.TempoEmergencyFlow ? window.TempoEmergencyFlow.getConfirmedPlan() : null;
        const efAvail = window.TempoEmergencyFlow ? window.TempoEmergencyFlow.getAvailabilityDays() : null;
        const slots = Array.from(document.querySelectorAll('input[name="pw_reschedule_day"]')).map(el => ({
            value: el.value,
            date: el.getAttribute('data-date'),
            start: el.getAttribute('data-start'),
            end: el.getAttribute('data-end'),
            checked: el.checked
        }));
        return {
            planAvailabilityDays: plan ? plan.availabilityDays : null,
            efConfirmedPlanAvailabilityDays: efPlan ? efPlan.availabilityDays : null,
            efAvailabilityDays: efAvail,
            slots: slots
        };
    })()
    """)
    print("Post-Save State:")
    print(json.dumps(post_save_state, indent=2, ensure_ascii=False))

    print("\n--- 4. EXECUTE RESCHEDULE TO 2026-11-02 ---")
    # Click radio for 2026-11-02 or execute
    eval_js(f"""
    (() => {{
        const radio = document.querySelector('input[data-date="2026-11-02"]');
        if (radio) {{
            const date = radio.getAttribute('data-date');
            const slotId = radio.getAttribute('data-slot-id');
            const start = radio.getAttribute('data-start');
            const end = radio.getAttribute('data-end');
            window.TempoPlanWorkspace.selectRescheduleSlot(date, slotId, start, end);
        }}
    }})()
    """)
    resched_res = eval_js(f"window.TempoPlanWorkspace.executeReschedule('{first_task_id}')")
    time.sleep(1)

    post_resched = eval_js(f"""
    (() => {{
        const plan = window.TempoPlanWorkspace.getActivePlan();
        const targetPt = plan && plan.plannedTasks ? plan.plannedTasks.find(pt => pt.task?.id === '{first_task_id}') : null;
        
        // Check headings rendered on the page
        const dayHeadings = Array.from(document.querySelectorAll('h3, h4, .font-heading, span')).map(el => el.textContent.trim()).filter(t => t.includes('2026'));
        
        return {{
            targetTask: targetPt ? {{
                id: targetPt.task?.id,
                name: targetPt.task?.name,
                dayDate: targetPt.dayDate,
                dayLabel: targetPt.dayLabel,
                startTime: targetPt.startTime,
                endTime: targetPt.endTime,
                taskScheduledDate: targetPt.task?.scheduledDate,
                taskDayDate: targetPt.task?.dayDate
            }} : null,
            planAvailabilityDays: plan ? plan.availabilityDays : null,
            sampleHeadings: dayHeadings.slice(0, 10)
        }};
    }})()
    """)
    print("Post-Reschedule State:")
    print(json.dumps(post_resched, indent=2, ensure_ascii=False))

    print("\n--- 5. REOPEN RESCHEDULE MODAL ---")
    eval_js(f"window.TempoPlanWorkspace.openRescheduleModal('{first_task_id}')")
    time.sleep(0.5)

    reopen_state = eval_js("""
    (() => {
        const slots = Array.from(document.querySelectorAll('input[name="pw_reschedule_day"]')).map(el => ({
            value: el.value,
            date: el.getAttribute('data-date'),
            start: el.getAttribute('data-start'),
            end: el.getAttribute('data-end'),
            checked: el.checked
        }));
        return {
            slots: slots
        };
    })()
    """)
    print("Reopen Modal State:")
    print(json.dumps(reopen_state, indent=2, ensure_ascii=False))

    print("\n--- 6. PAGE RELOAD INSPECTION ---")
    send_cmd("Page.reload")
    time.sleep(2)

    reload_state = eval_js(f"""
    (() => {{
        const plan = window.TempoPlanWorkspace ? window.TempoPlanWorkspace.getActivePlan() : null;
        const efPlan = window.TempoEmergencyFlow ? window.TempoEmergencyFlow.getConfirmedPlan() : null;
        const efAvail = window.TempoEmergencyFlow ? window.TempoEmergencyFlow.getAvailabilityDays() : null;
        const targetPt = plan && plan.plannedTasks ? plan.plannedTasks.find(pt => pt.task?.id === '{first_task_id}') : null;
        return {{
            targetTask: targetPt ? {{
                id: targetPt.task?.id,
                name: targetPt.task?.name,
                dayDate: targetPt.dayDate,
                startTime: targetPt.startTime,
                endTime: targetPt.endTime,
                taskScheduledDate: targetPt.task?.scheduledDate
            }} : null,
            planAvailabilityDays: plan ? plan.availabilityDays : null,
            efConfirmedPlanAvailabilityDays: efPlan ? efPlan.availabilityDays : null,
            efAvailabilityDays: efAvail
        }};
    }})()
    """)
    print("Reload State:")
    print(json.dumps(reload_state, indent=2, ensure_ascii=False))

finally:
    if ws:
        ws.close()
    proc.terminate()
