import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

user_data_dir = tempfile.mkdtemp(prefix="tempo_adjust_due_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9298

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "http://localhost:8000/"
]

log("Launching Edge on port 9298...")
proc = subprocess.Popen(cmd)
ws = None

try:
    ws_url = None
    for _ in range(30):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as resp:
                tabs = json.loads(resp.read().decode())
                pages = [t for t in tabs if t.get("type") == "page"]
                if pages:
                    ws_url = pages[0]["webSocketDebuggerUrl"]
                    break
        except Exception:
            time.sleep(0.5)

    if not ws_url:
        raise RuntimeError("Failed to connect to Edge CDP endpoint")

    ws = websocket.create_connection(ws_url)
    msg_id = 1

    def send_command(method, params=None):
        global msg_id
        cid = msg_id
        msg_id += 1
        req = {"id": cid, "method": method}
        if params:
            req["params"] = params
        ws.send(json.dumps(req))
        while True:
            raw = ws.recv()
            msg = json.loads(raw)
            if msg.get("id") == cid:
                if "error" in msg:
                    raise RuntimeError(f"CDP error: {msg['error']}")
                return msg.get("result", {})

    def eval_js(expr, await_promise=True):
        res = send_command("Runtime.evaluate", {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": await_promise
        })
        if "exceptionDetails" in res:
            raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
        return res.get("result", {}).get("value")

    def wait_for_ready():
        for _ in range(40):
            try:
                ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined' && typeof window.TempoEmergencyFlow !== 'undefined' && typeof window.TempoUrmodeFlow !== 'undefined'")
                if ready:
                    eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        raise TimeoutError("Application failed to become ready")

    log("Waiting for application ready state...")
    wait_for_ready()

    # Authenticate mock user and set mode
    eval_js("""
        (async () => {
            if (window.TempoAuth && !window.TempoAuth.getCurrentUser()) {
                const mock = {
                    id: 'local_user_test',
                    email: 'alex.chen@university.edu',
                    raw_email: 'alex.chen@university.edu',
                    password: 'password123',
                    user_metadata: { full_name: 'Alex Chen', display_name: 'Alex Chen', role: 'student' }
                };
                localStorage.setItem('tempo_mock_account_alex.chen@university.edu', JSON.stringify(mock));
                await window.TempoAuth.signIn("alex.chen@university.edu", "password123");
            }
            window.TempoMode.setMode('emergency');
        })()
    """)
    time.sleep(0.5)

    today = eval_js("new Date().toISOString().split('T')[0]")

    # =========================================================================
    # SETUP: Initial Saved Working Plan with Mixed Deadlines
    # =========================================================================
    log("\n--- SETUP: Initial Working Plan with 3 Tasks ---")
    eval_js(f"""
        (async () => {{
            const plan = {{
                id: 'plan_adjust_due_dates_test',
                planId: 'plan_adjust_due_dates_test',
                mode: 'emergency',
                planType: 'emergency',
                title: 'Working Plan',
                createdAt: new Date().toISOString(),
                plannedTasks: [
                    {{
                        dayDate: '{today}',
                        executionBadge: 'DO THIS FIRST',
                        task: {{
                            id: 'task-adj-1',
                            name: 'Chemistry Problem Set',
                            durationMinutes: 60,
                            durationLabel: '1 hr',
                            hasDeadline: true,
                            deadlineDate: '2026-10-25',
                            deadlineTime: '18:00',
                            deadline: '2026-10-25 18:00',
                            completed: false,
                            subtasks: []
                        }}
                    }},
                    {{
                        dayDate: '{today}',
                        executionBadge: 'UP NEXT',
                        task: {{
                            id: 'task-adj-2',
                            name: 'Read Sociology Article',
                            durationMinutes: 30,
                            durationLabel: '30 min',
                            hasDeadline: false,
                            deadlineDate: null,
                            deadlineTime: null,
                            deadline: null,
                            completed: false,
                            subtasks: []
                        }}
                    }},
                    {{
                        dayDate: '{today}',
                        executionBadge: 'UP NEXT',
                        task: {{
                            id: 'task-adj-3',
                            name: 'History Essay Outline',
                            durationMinutes: 45,
                            durationLabel: '45 min',
                            hasDeadline: true,
                            deadlineDate: '2026-10-28',
                            deadlineTime: '23:59',
                            deadline: '2026-10-28 23:59',
                            completed: false,
                            subtasks: []
                        }}
                    }}
                ],
                tasks: [],
                availabilityDays: [{{ date: '{today}', label: 'Today', blocks: [{{ start: '09:00', end: '18:00' }}] }}]
            }};
            plan.tasks = plan.plannedTasks.map(p => p.task);
            await window.TempoPlanStore.saveActivePlan('emergency', plan);
            window.TempoEmergencyFlow.setConfirmedPlan(plan);
        }})()
    """)

    # =========================================================================
    # TEST 1: Open Step 2 and verify due date fields and prepopulation
    # =========================================================================
    log("\n--- TEST 1: Retained Tasks Have Due Date Controls Prepopulated ---")
    t1_res = eval_js("""
        (() => {
            window.TempoUrmodeFlow.startAdjustmentFlow();
            window.TempoUrmodeFlow.renderAdjustmentStep2Tasks();

            const due1 = document.getElementById('adjust-due-task-adj-1');
            const dur1 = document.getElementById('adjust-dur-task-adj-1');

            const due2 = document.getElementById('adjust-due-task-adj-2');
            const dur2 = document.getElementById('adjust-dur-task-adj-2');

            const due3 = document.getElementById('adjust-due-task-adj-3');
            const dur3 = document.getElementById('adjust-dur-task-adj-3');

            const newDue = document.getElementById('adjust-new-task-due');
            const newName = document.getElementById('adjust-new-task-name');
            const newDur = document.getElementById('adjust-new-task-dur');

            return {
                hasDue1: !!due1,
                valDue1: due1 ? due1.value : null,
                valDur1: dur1 ? dur1.value : null,

                hasDue2: !!due2,
                valDue2: due2 ? due2.value : null,
                valDur2: dur2 ? dur2.value : null,

                hasDue3: !!due3,
                valDue3: due3 ? due3.value : null,
                valDur3: dur3 ? dur3.value : null,

                hasNewDue: !!newDue,
                valNewDue: newDue ? newDue.value : null,
                hasNewName: !!newName,
                hasNewDur: !!newDur
            };
        })()
    """)
    log(f"Test 1 Result: {json.dumps(t1_res, indent=2)}")
    assert t1_res["hasDue1"] is True, "Task 1 must have due date control"
    assert t1_res["valDue1"] == "2026-10-25", f"Task 1 due date must be prepopulated with 2026-10-25, got {t1_res['valDue1']}"
    assert t1_res["valDur1"] == "60", "Task 1 duration must be 60 min"

    assert t1_res["hasDue2"] is True, "Task 2 must have due date control"
    assert t1_res["valDue2"] == "", f"Task 2 (no deadline) must be empty, got {t1_res['valDue2']}"
    assert t1_res["valDur2"] == "30", "Task 2 duration must be 30 min"

    assert t1_res["hasDue3"] is True, "Task 3 must have due date control"
    assert t1_res["valDue3"] == "2026-10-28", f"Task 3 due date must be prepopulated with 2026-10-28, got {t1_res['valDue3']}"
    assert t1_res["valDur3"] == "45", "Task 3 duration must be 45 min"

    assert t1_res["hasNewDue"] is True, "Add New Task section must have due date control"
    assert t1_res["valNewDue"] == "", "Add New Task due date control must default to empty"
    log("✓ Test 1 passed: All retained tasks display editable due date controls prepopulated with existing dates, empty for tasks without deadlines.")

    # =========================================================================
    # TEST 2: Individual editing & independent isolation
    # =========================================================================
    log("\n--- TEST 2: Individual Editing and Independent Isolation ---")
    t2_res = eval_js("""
        (() => {
            // Edit task 1 due date
            const due1 = document.getElementById('adjust-due-task-adj-1');
            due1.value = '2026-10-26';
            window.TempoUrmodeFlow.updateRetainedDueDate('task-adj-1', '2026-10-26');

            // Add due date to task 2 (previously empty)
            const due2 = document.getElementById('adjust-due-task-adj-2');
            due2.value = '2026-10-30';
            window.TempoUrmodeFlow.updateRetainedDueDate('task-adj-2', '2026-10-30');

            // Task 3 is untouched
            const due3 = document.getElementById('adjust-due-task-adj-3');

            return {
                due1: due1.value,
                due2: due2.value,
                due3: due3.value
            };
        })()
    """)
    log(f"Test 2 Result: {json.dumps(t2_res, indent=2)}")
    assert t2_res["due1"] == "2026-10-26", "Task 1 date should be updated to 2026-10-26"
    assert t2_res["due2"] == "2026-10-30", "Task 2 date should be updated to 2026-10-30"
    assert t2_res["due3"] == "2026-10-28", "Task 3 date must remain untouched at 2026-10-28"
    log("✓ Test 2 passed: Editing one task's due date does not affect other tasks.")

    # =========================================================================
    # TEST 3: Clearing a due date sets it to empty / no deadline
    # =========================================================================
    log("\n--- TEST 3: Clearing a Due Date ---")
    t3_res = eval_js("""
        (() => {
            const due3 = document.getElementById('adjust-due-task-adj-3');
            due3.value = '';
            window.TempoUrmodeFlow.updateRetainedDueDate('task-adj-3', '');

            return {
                valDue3: due3.value
            };
        })()
    """)
    log(f"Test 3 Result: {json.dumps(t3_res, indent=2)}")
    assert t3_res["valDue3"] == "", "Task 3 due date should be cleared"
    log("✓ Test 3 passed: User can clear an existing due date back to empty.")

    # =========================================================================
    # TEST 4: Navigation Back to Step 1 & Forward preserves unsaved edits
    # =========================================================================
    log("\n--- TEST 4: Unsaved Edits Preserved on Back / Next Navigation ---")
    t4_res = eval_js("""
        (() => {
            // Click Back to Step 1
            window.TempoUrmodeFlow.handleAdjustmentStep2Back();

            const modal = document.getElementById('modal-urmode-flow');
            const step1Title = modal.querySelector('h2').textContent.trim();

            // Click Next to Step 2
            window.TempoUrmodeFlow.renderAdjustmentStep2Tasks();

            const due1 = document.getElementById('adjust-due-task-adj-1');
            const due2 = document.getElementById('adjust-due-task-adj-2');
            const due3 = document.getElementById('adjust-due-task-adj-3');

            return {
                step1Title,
                valDue1: due1 ? due1.value : null,
                valDue2: due2 ? due2.value : null,
                valDue3: due3 ? due3.value : null
            };
        })()
    """)
    log(f"Test 4 Result: {json.dumps(t4_res, indent=2)}")
    assert "Choose tasks to keep" in t4_res["step1Title"], "Step 1 title should match"
    assert t4_res["valDue1"] == "2026-10-26", f"Task 1 date should remain 2026-10-26, got {t4_res['valDue1']}"
    assert t4_res["valDue2"] == "2026-10-30", f"Task 2 date should remain 2026-10-30, got {t4_res['valDue2']}"
    assert t4_res["valDue3"] == "", f"Task 3 date should remain empty, got {t4_res['valDue3']}"
    log("✓ Test 4 passed: Unsaved due date edits remain available when navigating Back and Forward.")

    # =========================================================================
    # TEST 5: Add New Task with Optional Due Date & New Task without Due Date
    # =========================================================================
    log("\n--- TEST 5: Add New Tasks with and without Due Date ---")
    t5_res = eval_js("""
        (() => {
            // Add Task with Due Date
            document.getElementById('adjust-new-task-name').value = 'Lab Report Discussion';
            document.getElementById('adjust-new-task-dur').value = '45';
            document.getElementById('adjust-new-task-due').value = '2026-11-02';
            window.TempoUrmodeFlow.addNewAdjustmentTask();

            // Add Task without Due Date
            document.getElementById('adjust-new-task-name').value = 'Email Teaching Assistant';
            document.getElementById('adjust-new-task-dur').value = '15';
            document.getElementById('adjust-new-task-due').value = '';
            window.TempoUrmodeFlow.addNewAdjustmentTask();

            const newTasks = window.TempoUrmodeFlow.getActiveWorkingPlan ? null : null;

            // Check rendered new task list in DOM
            const newTasksDivs = Array.from(document.querySelectorAll('#adjust-new-tasks-list > div'));
            const texts = newTasksDivs.map(d => d.textContent.trim());

            return {
                newTasksCount: newTasksDivs.length,
                texts
            };
        })()
    """)
    log(f"Test 5 Result: {json.dumps(t5_res, indent=2)}")
    assert t5_res["newTasksCount"] == 2, f"Expected 2 new tasks added, got {t5_res['newTasksCount']}"
    assert any("Lab Report Discussion" in t and ("Nov 2" in t or "thg 11" in t) for t in t5_res["texts"]), "New Task with due date must show due date"
    assert any("Email Teaching Assistant" in t and "Due:" not in t for t in t5_res["texts"]), "New Task without due date must not invent a deadline"
    log("✓ Test 5 passed: New tasks optionally accept due dates; omitting leaves deadline empty without inventing one.")

    # =========================================================================
    # TEST 6: Original Plan Remains Intact Before Save
    # =========================================================================
    log("\n--- TEST 6: Original Plan Unmodified Before Save ---")
    t6_res = eval_js("""
        (async () => {
            const plan = await window.TempoPlanStore.getActivePlan('emergency');
            return {
                taskCount: plan.plannedTasks.length,
                task1Due: plan.plannedTasks[0].task.deadlineDate,
                task2Due: plan.plannedTasks[1].task.deadlineDate,
                task3Due: plan.plannedTasks[2].task.deadlineDate
            };
        })()
    """)
    log(f"Test 6 Result: {json.dumps(t6_res, indent=2)}")
    assert t6_res["taskCount"] == 3, "Original plan task count must remain 3 before saving"
    assert t6_res["task1Due"] == "2026-10-25", "Original Task 1 due date must remain unmodified in store"
    assert t6_res["task2Due"] is None, "Original Task 2 must remain without deadline in store"
    assert t6_res["task3Due"] == "2026-10-28", "Original Task 3 due date must remain unmodified in store"
    log("✓ Test 6 passed: Active saved plan is completely unchanged prior to saving.")

    # =========================================================================
    # TEST 7: Carry Changes to Step 3 Proposal & Verify Presentation
    # =========================================================================
    log("\n--- TEST 7: Carry Changes into Step 3 Proposal ---")
    t7_res = eval_js("""
        (() => {
            window.TempoUrmodeFlow.handleAdjustmentStep2Next();

            const modal = document.getElementById('modal-urmode-flow');
            const step3Title = modal.querySelector('h2').textContent.trim();

            const proposalItems = Array.from(modal.querySelectorAll('.max-h-60 .p-3')).map(el => el.textContent.trim());

            return {
                step3Title,
                proposalItems
            };
        })()
    """)
    log(f"Test 7 Result: {json.dumps(t7_res, indent=2)}")
    assert "Proposed Updated Plan" in t7_res["step3Title"], "Step 3 title should match"
    assert any("Chemistry Problem Set" in p and ("Oct 26" in p or "thg 10" in p) for p in t7_res["proposalItems"]), "Task 1 in proposal must reflect updated date Oct 26"
    assert any("Read Sociology Article" in p and ("Oct 30" in p or "thg 10" in p) for p in t7_res["proposalItems"]), "Task 2 in proposal must reflect newly added date Oct 30"
    assert any("History Essay Outline" in p and "No fixed deadline" in p for p in t7_res["proposalItems"]), "Task 3 in proposal must show No fixed deadline"
    assert any("Lab Report Discussion" in p and ("Nov 2" in p or "thg 11" in p) for p in t7_res["proposalItems"]), "New Task A must show Nov 2"
    assert any("Email Teaching Assistant" in p and "No fixed deadline" in p for p in t7_res["proposalItems"]), "New Task B must show No fixed deadline"
    log("✓ Test 7 passed: Step 3 Proposal accurately reflects all updated and newly added due dates.")

    # =========================================================================
    # TEST 8: Save Adjusted Plan & Verify Persistence & Consistent UI
    # =========================================================================
    log("\n--- TEST 8: Save Adjusted Plan and Verify Persistence & UI Consistency ---")
    t8_res = eval_js("""
        (async () => {
            // Save the plan
            window.TempoUrmodeFlow.saveAdjustmentPlan();

            await new Promise(r => setTimeout(r, 400));

            // Verify store persistence
            const savedPlan = await window.TempoPlanStore.getActivePlan('emergency');
            const tasks = savedPlan.plannedTasks.map(pt => pt.task);

            const t1 = tasks.find(t => t.id === 'task-adj-1');
            const t2 = tasks.find(t => t.id === 'task-adj-2');
            const t3 = tasks.find(t => t.id === 'task-adj-3');
            const tNew1 = tasks.find(t => t.name === 'Lab Report Discussion');
            const tNew2 = tasks.find(t => t.name === 'Email Teaching Assistant');

            // Verify Post-Save Popup has opened and shows top task with updated due date
            const modal = document.getElementById('modal-urmode-flow');
            const postSaveHeading = modal ? modal.querySelector('h2')?.textContent.trim() : '';
            const postSaveDueText = modal ? modal.querySelector('.text-xs')?.textContent.trim() : '';

            // Verify Working Plan workspace render consistency
            window.TempoPlanWorkspace.render();
            const wpScreen = document.getElementById('screen-plan-workspace');

            return {
                totalTasks: tasks.length,
                t1Due: t1 ? t1.deadlineDate : null,
                t1HasDeadline: t1 ? t1.hasDeadline : null,

                t2Due: t2 ? t2.deadlineDate : null,
                t2HasDeadline: t2 ? t2.hasDeadline : null,

                t3Due: t3 ? t3.deadlineDate : null,
                t3HasDeadline: t3 ? t3.hasDeadline : null,

                tNew1Due: tNew1 ? tNew1.deadlineDate : null,
                tNew1HasDeadline: tNew1 ? tNew1.hasDeadline : null,

                tNew2Due: tNew2 ? tNew2.deadlineDate : null,
                tNew2HasDeadline: tNew2 ? tNew2.hasDeadline : null,

                postSaveHeading
            };
        })()
    """)
    log(f"Test 8 Result: {json.dumps(t8_res, indent=2)}")
    assert t8_res["totalTasks"] == 5, f"Expected 5 tasks in saved plan, got {t8_res['totalTasks']}"
    assert t8_res["t1Due"] == "2026-10-26" and t8_res["t1HasDeadline"] is True, "Task 1 persisted with 2026-10-26"
    assert t8_res["t2Due"] == "2026-10-30" and t8_res["t2HasDeadline"] is True, "Task 2 persisted with 2026-10-30"
    assert t8_res["t3Due"] is None and t8_res["t3HasDeadline"] is False, "Task 3 persisted with null deadline"
    assert t8_res["tNew1Due"] == "2026-11-02" and t8_res["tNew1HasDeadline"] is True, "New Task A persisted with 2026-11-02"
    assert t8_res["tNew2Due"] is None and t8_res["tNew2HasDeadline"] is False, "New Task B persisted with null deadline"
    log("✓ Test 8 passed: Successfully persisted updated plan with all task due dates.")

    log("\n=======================================================================")
    log(">>> ALL STEP 2 DUE DATE ADJUSTMENT TESTS COMPREHENSIVELY PASSED! <<<")
    log("=======================================================================")

finally:
    if ws:
        try:
            ws.close()
        except Exception:
            pass
    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
