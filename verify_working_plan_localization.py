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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_plan_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9550

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

    # 1. Setup seed user and plan
    setup_code = """
    (async () => {
        // Authenticate user
        const u = { id: 'u1', email: 'alex@tempo.test', user_metadata: { display_name: 'Alex' } };
        localStorage.setItem('tempo_local_dev_user', JSON.stringify(u));
        localStorage.setItem('tempo_mock_account_alex@tempo.test', JSON.stringify(u));
        if (window.TempoAuth && typeof window.TempoAuth.checkSession === 'function') {
            await window.TempoAuth.checkSession();
        }

        const tomorrowStr = (window.TempoI18n && typeof window.TempoI18n.getLocalTomorrowISO === 'function')
            ? window.TempoI18n.getLocalTomorrowISO()
            : (() => {
                const d = new Date();
                d.setDate(d.getDate() + 1);
                return d.toISOString().split('T')[0];
            })();

        const mockPlan = {
            id: 'test-working-plan-1',
            planId: 'test-working-plan-1',
            status: 'active',
            planType: 'emergency',
            title: 'Tempo Working Plan',
            createdAt: Date.now(),
            plannedTasks: [
                {
                    task: {
                        id: 't-1',
                        name: 'Literature Review Chapter 2',
                        deadlineDate: tomorrowStr,
                        deadlineTime: '14:00',
                        hasDeadline: true,
                        durationLabel: '2h',
                        userLabel: 'Now',
                        priorityCategory: 'DO_FIRST',
                        completed: false,
                        subtasks: [
                            { id: 'st-1', title: 'Read methodology section', completed: false },
                            { id: 'st-2', title: 'Summarize key findings', completed: false }
                        ]
                    },
                    dayDate: tomorrowStr,
                    startTime: '09:00',
                    endTime: '11:00',
                    executionBadge: 'Now'
                },
                {
                    task: {
                        id: 't-2',
                        name: 'Submit Weekly Progress Report',
                        hasDeadline: false,
                        durationLabel: '45m',
                        userLabel: 'Later',
                        priorityCategory: 'LATER',
                        completed: false,
                        subtasks: []
                    },
                    dayDate: tomorrowStr,
                    startTime: '14:00',
                    endTime: '14:45',
                    executionBadge: 'Later'
                },
                {
                    task: {
                        id: 't-3',
                        name: 'Prepare Lab Safety Checklist',
                        deadlineDate: tomorrowStr,
                        deadlineTime: '10:00',
                        hasDeadline: true,
                        durationLabel: '1h',
                        userLabel: 'Later',
                        completed: true,
                        completedAt: Date.now() - 3600000,
                        subtasks: [
                            { id: 'st-3', title: 'Check equipment status', completed: true }
                        ]
                    },
                    dayDate: tomorrowStr,
                    startTime: '08:00',
                    endTime: '09:00',
                    executionBadge: 'Later'
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
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.renderWorkspace === 'function') {
            window.TempoPlanWorkspace.renderWorkspace();
        } else if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
            window.TempoPlanWorkspace.render();
        }
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.selectTask === 'function') {
            window.TempoPlanWorkspace.selectTask('t-1');
        }
    })()
    """
    eval_js(setup_code)
    time.sleep(1)

    # 2. Test Vietnamese Mode
    eval_js("""
    (() => {
        window.TempoI18n.setLanguage('vi');
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
            window.TempoPlanWorkspace.render();
            window.TempoPlanWorkspace.selectTask('t-1');
        }
    })()
    """)
    time.sleep(1)

    vi_checks = eval_js("""
    (() => {
        const results = {};
        
        // Return home button
        const backBtn = document.getElementById('plan-workspace-back-home');
        results.returnHome = backBtn ? backBtn.innerText.replace(/\\s+/g, ' ').trim() : null;
        
        // Header Toolbar CTAs
        const ctaButtons = Array.from(document.querySelectorAll('[data-tempo-ui="tempo-working-plan"] button'))
            .map(b => b.innerText.trim());
        results.ctaButtons = ctaButtons;

        // Progress counter
        const counterEl = document.querySelector('[data-tempo-ui="tasks-progress-counter"]');
        results.progressCounter = counterEl ? counterEl.innerText.trim() : null;

        // Task List Date Heading
        const dateHeadings = Array.from(document.querySelectorAll('#plan-workspace-task-list h3'))
            .map(h => h.innerText.trim());
        results.dateHeadings = dateHeadings;

        // Badges in Task List
        const badges = Array.from(document.querySelectorAll('#plan-workspace-task-list [data-label-menu-container] button'))
            .map(b => b.innerText.replace(/\\s+/g, ' ').trim());
        results.badges = badges;

        // Subtasks text in Task List
        const subtaskDivs = Array.from(document.querySelectorAll('#plan-workspace-task-list div'))
            .map(d => d.innerText.trim())
            .filter(t => t.includes('subtask') || t.includes('Subtask'));
        results.subtaskDivs = subtaskDivs;

        // Completed Section
        const doneHeading = document.querySelector('[data-tempo-ui="done-section"] h3');
        results.doneSectionHeading = doneHeading ? doneHeading.innerText.replace(/\\s+/g, ' ').trim() : null;

        // Task Detail Panel
        const detailCard = document.querySelector('[data-tempo-ui="selected-task-card"]');
        if (detailCard) {
            results.detailButtons = Array.from(detailCard.querySelectorAll('button')).map(b => b.innerText.replace(/\\s+/g, ' ').trim());
            results.detailText = detailCard.innerText;
        }

        return results;
    })()
    """)
    print("\n--- VIETNAMESE VERIFICATION RESULTS ---")
    print("Return Home:", vi_checks.get('returnHome'))
    print("Progress Counter:", vi_checks.get('progressCounter'))
    print("Date Headings:", vi_checks.get('dateHeadings'))
    print("Badges:", vi_checks.get('badges'))
    print("Subtask rows in list:", vi_checks.get('subtaskDivs'))
    print("Done Section Heading:", vi_checks.get('doneSectionHeading'))
    print("Detail Buttons:", vi_checks.get('detailButtons'))

    # Verify VI requirements
    assert "← Về trang chủ" in vi_checks.get('returnHome', ''), f"Return Home mismatch in VI: {vi_checks.get('returnHome')}"
    assert "Thêm task" in vi_checks.get('ctaButtons', []), "Thêm task not found in CTA buttons"
    assert "Thêm thời gian làm việc" in vi_checks.get('ctaButtons', []), "Thêm thời gian làm việc not found in CTA buttons"
    assert "Điều chỉnh plan" in vi_checks.get('ctaButtons', []), "Điều chỉnh plan not found in CTA buttons"
    assert "Xóa plan" in vi_checks.get('ctaButtons', []), "Xóa plan not found in CTA buttons"
    assert "task" in vi_checks.get('progressCounter', ''), f"Progress counter missing 'task' in VI: {vi_checks.get('progressCounter')}"
    assert any("Ngày mai" in h for h in vi_checks.get('dateHeadings', [])), f"Ngày mai heading not found in {vi_checks.get('dateHeadings')}"
    assert any("Làm ngay" in b for b in vi_checks.get('badges', [])), f"Làm ngay badge not found in {vi_checks.get('badges')}"
    assert "Đã hoàn thành" in vi_checks.get('doneSectionHeading', ''), f"Đã hoàn thành not found in done section heading: {vi_checks.get('doneSectionHeading')}"
    
    # Check subtasks row format
    assert any("0/2 subtask" in s for s in vi_checks.get('subtaskDivs', [])), f"0/2 subtask not found in {vi_checks.get('subtaskDivs')}"

    # Check detail panel buttons in VI
    detail_btns = vi_checks.get('detailButtons', [])
    assert any("Sửa deadline" in b for b in detail_btns), f"Sửa deadline not found in {detail_btns}"
    assert any("Chia nhỏ task" in b for b in detail_btns), f"+ Chia nhỏ task not found in {detail_btns}"
    assert any("Thêm ghi chú" in b for b in detail_btns), f"+ Thêm ghi chú not found in {detail_btns}"
    assert any("Hoàn thành" in b for b in detail_btns), f"Hoàn thành not found in {detail_btns}"
    assert any("Làm task" in b for b in detail_btns), f"Làm task not found in {detail_btns}"
    assert any("Đổi lịch" in b for b in detail_btns), f"Đổi lịch not found in {detail_btns}"
    assert any("Xóa task này" in b for b in detail_btns), f"Xóa task này not found in {detail_btns}"

    # Verify task with no deadline displays 'Chưa có deadline'
    eval_js("window.TempoPlanWorkspace.selectTask('t-2');")
    time.sleep(0.5)
    t2_text = eval_js("document.querySelector('[data-tempo-ui=\"selected-task-card\"]').innerText")
    assert "Chưa có deadline" in t2_text, f"'Chưa có deadline' not found for task without deadline: {t2_text}"

    # Re-select t-1 and take screenshot
    eval_js("window.TempoPlanWorkspace.selectTask('t-1');")
    time.sleep(0.5)
    capture_screenshot("working_plan_vi.png")

    # 3. Test English Mode
    eval_js("""
    (() => {
        window.TempoI18n.setLanguage('en');
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
            window.TempoPlanWorkspace.render();
            window.TempoPlanWorkspace.selectTask('t-1');
        }
    })()
    """)
    time.sleep(1)

    en_checks = eval_js("""
    (() => {
        const results = {};
        
        // Return home button
        const backBtn = document.getElementById('plan-workspace-back-home');
        results.returnHome = backBtn ? backBtn.innerText.replace(/\\s+/g, ' ').trim() : null;
        
        // Header Toolbar CTAs
        const ctaButtons = Array.from(document.querySelectorAll('[data-tempo-ui="tempo-working-plan"] button'))
            .map(b => b.innerText.trim());
        results.ctaButtons = ctaButtons;

        // Progress counter
        const counterEl = document.querySelector('[data-tempo-ui="tasks-progress-counter"]');
        results.progressCounter = counterEl ? counterEl.innerText.trim() : null;

        // Task List Date Heading
        const dateHeadings = Array.from(document.querySelectorAll('#plan-workspace-task-list h3'))
            .map(h => h.innerText.trim());
        results.dateHeadings = dateHeadings;

        // Badges in Task List
        const badges = Array.from(document.querySelectorAll('#plan-workspace-task-list [data-label-menu-container] button'))
            .map(b => b.innerText.replace(/\\s+/g, ' ').trim());
        results.badges = badges;

        // Subtasks text in Task List
        const subtaskDivs = Array.from(document.querySelectorAll('#plan-workspace-task-list div'))
            .map(d => d.innerText.trim())
            .filter(t => t.includes('subtask') || t.includes('Subtask'));
        results.subtaskDivs = subtaskDivs;

        // Completed Section
        const doneHeading = document.querySelector('[data-tempo-ui="done-section"] h3');
        results.doneSectionHeading = doneHeading ? doneHeading.innerText.replace(/\\s+/g, ' ').trim() : null;

        // Task Detail Panel
        const detailCard = document.querySelector('[data-tempo-ui="selected-task-card"]');
        if (detailCard) {
            results.detailButtons = Array.from(detailCard.querySelectorAll('button')).map(b => b.innerText.replace(/\\s+/g, ' ').trim());
            results.detailText = detailCard.innerText;
        }

        return results;
    })()
    """)
    print("\n--- ENGLISH VERIFICATION RESULTS ---")
    print("Return Home:", en_checks.get('returnHome'))
    print("Progress Counter:", en_checks.get('progressCounter'))
    print("Date Headings:", en_checks.get('dateHeadings'))
    print("Badges:", en_checks.get('badges'))
    print("Subtask rows in list:", en_checks.get('subtaskDivs'))
    print("Done Section Heading:", en_checks.get('doneSectionHeading'))
    print("Detail Buttons:", en_checks.get('detailButtons'))

    # Verify EN requirements
    assert "Return Home" in en_checks.get('returnHome', ''), f"Return Home mismatch in EN: {en_checks.get('returnHome')}"
    assert "Add task" in en_checks.get('ctaButtons', []), "Add task not found in CTA buttons"
    assert "Add availability" in en_checks.get('ctaButtons', []), "Add availability not found in CTA buttons"
    assert "Adjust Plan" in en_checks.get('ctaButtons', []), "Adjust Plan not found in CTA buttons"
    assert "Delete my plan" in en_checks.get('ctaButtons', []), "Delete my plan not found in CTA buttons"
    assert "Tasks" in en_checks.get('progressCounter', ''), f"Progress counter missing 'Tasks' in EN: {en_checks.get('progressCounter')}"
    assert any("Tomorrow" in h for h in en_checks.get('dateHeadings', [])), f"Tomorrow heading not found in {en_checks.get('dateHeadings')}"
    assert any("Do now" in b for b in en_checks.get('badges', [])), f"Do now badge not found in {en_checks.get('badges')}"
    assert "Completed" in en_checks.get('doneSectionHeading', ''), f"Completed not found in done section heading: {en_checks.get('doneSectionHeading')}"

    # Check subtasks row format
    assert any("0/2 Subtasks" in s for s in en_checks.get('subtaskDivs', [])), f"0/2 Subtasks not found in {en_checks.get('subtaskDivs')}"

    # Check detail panel buttons in EN
    en_detail_btns = en_checks.get('detailButtons', [])
    assert any("Edit deadline" in b for b in en_detail_btns), f"Edit deadline not found in {en_detail_btns}"
    assert any("Break down task" in b for b in en_detail_btns), f"Break down task not found in {en_detail_btns}"
    assert any("+ Add note" in b for b in en_detail_btns), f"+ Add note not found in {en_detail_btns}"
    assert any("Mark as done" in b for b in en_detail_btns), f"Mark as done not found in {en_detail_btns}"
    assert any("Focus now" in b for b in en_detail_btns), f"Focus now not found in {en_detail_btns}"
    assert any("Reschedule" in b for b in en_detail_btns), f"Reschedule not found in {en_detail_btns}"
    assert any("Clear this task" in b for b in en_detail_btns), f"Clear this task not found in {en_detail_btns}"

    # Verify task with no deadline displays 'No deadline'
    eval_js("window.TempoPlanWorkspace.selectTask('t-2');")
    time.sleep(0.5)
    t2_text_en = eval_js("document.querySelector('[data-tempo-ui=\"selected-task-card\"]').innerText")
    assert "No deadline" in t2_text_en, f"'No deadline' not found for task without deadline: {t2_text_en}"

    # Re-select t-1 and take screenshot
    eval_js("window.TempoPlanWorkspace.selectTask('t-1');")
    time.sleep(0.5)
    capture_screenshot("working_plan_en.png")

    print("\nALL WORKING PLAN LOCALIZATION TESTS PASSED SUCCESSFULLY!")

finally:
    if ws:
        try:
            ws.close()
        except:
            pass
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except:
        pass
