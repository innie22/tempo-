"""
TEMPO REGRESSION TEST SUITE: URGENT PLAN (EPLAN) PRODUCT CONTRACT
File: test_urgent_plan_contract.py

Validates the frozen development contract for Urgent Plan:
- Internal plan type remains 'emergency' (never persisted as 'urgent')
- Existing saved plan compatibility
- Shared task identity across modules (TempoPlanStore, TempoEmergencyFlow, TempoPlanWorkspace, TempoFocusZone)
- No task duplication between modes or operations
- Completion status continuity across references
- Subtask and estimate attachment integrity
- Authoritative execution order without silent reranking
- Stale-plan non-destructive handling (no silent rescheduling or dropping)
- Plan Workspace dynamic editing capabilities (user data is NOT frozen)
"""

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

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_plan_contract_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9232
    
    cmd = [
        edge_path,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "http://localhost:8000/"
    ]
    
    log(f"Launching Edge on port {port}...")
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
            
        log(f"Connected to CDP: {ws_url}")
        ws = websocket.create_connection(ws_url)
        
        msg_id = 1
        def send_command(method, params=None):
            nonlocal msg_id
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
                    ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined' && typeof window.TempoPlanWorkspace !== 'undefined'")
                    if ready:
                        eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("Application failed to become ready")

        log("Waiting for page and scripts ready...")
        wait_for_ready()

        # =====================================================================
        # CONTRACT CHECK 1: plan_type Invariant & Compatibility
        # =====================================================================
        log("\n--- CONTRACT CHECK 1: plan_type Invariant & Saved Plan Compatibility ---")
        type_check = eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

                const sampleLegacyPlan = {
                    id: 'plan_legacy_compat_1',
                    planId: 'plan_legacy_compat_1',
                    planType: 'emergency',
                    title: 'Urgent Plan',
                    plannedTasks: [
                        {
                            dayDate: today,
                            startTime: '09:00 AM',
                            endTime: '10:00 AM',
                            task: {
                                id: 'task-compat-1',
                                name: 'Calculus Assignment',
                                durationMinutes: 60,
                                durationLabel: '1 hr',
                                hasDeadline: true,
                                deadlineDate: today,
                                deadlineTime: '17:00',
                                completed: false,
                                subtasks: [{ id: 's1', title: 'Part A', completed: false }]
                            }
                        }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, blocks: [{ start: '09:00', end: '17:00' }] }]
                };
                sampleLegacyPlan.tasks = sampleLegacyPlan.plannedTasks.map(pt => pt.task);

                // Save to store
                await window.TempoPlanStore.saveActivePlan('emergency', sampleLegacyPlan);
                const loaded = window.TempoPlanStore.getActivePlan('emergency');

                // Try invalid plan_type
                const hasUrgentType = window.TempoPlanStore.hasActivePlan('urgent');

                return {
                    savedType: loaded ? loaded.planType : null,
                    hasEmergency: window.TempoPlanStore.hasActivePlan('emergency'),
                    hasUrgentType: Boolean(hasUrgentType),
                    taskCount: loaded && loaded.plannedTasks ? loaded.plannedTasks.length : 0,
                    taskId: loaded && loaded.plannedTasks && loaded.plannedTasks[0] ? loaded.plannedTasks[0].task.id : null
                };
            })()
        """)

        assert type_check['savedType'] == 'emergency', f"Internal planType must remain 'emergency', got: {type_check['savedType']}"
        assert type_check['hasEmergency'], "TempoPlanStore must recognize active plan under 'emergency'"
        assert not type_check['hasUrgentType'], "TempoPlanStore must NOT recognize plan_type='urgent'"
        assert type_check['taskCount'] == 1 and type_check['taskId'] == 'task-compat-1', "Legacy plan structure restored accurately"
        log("✓ plan_type remains 'emergency' (never 'urgent') and schema compatibility verified.")

        # =====================================================================
        # CONTRACT CHECK 2: Shared Task Identity & No Duplication
        # =====================================================================
        log("\n--- CONTRACT CHECK 2: Shared Task Identity & Zero Duplication ---")
        identity_check = eval_js("""
            (async () => {
                const plan = window.TempoPlanStore.getActivePlan('emergency');
                const originalTask = plan.plannedTasks[0].task;

                // Sync to emergency flow
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(plan);
                }

                // Open workspace
                window.TempoPlanWorkspace.open();
                const wsPlan = window.TempoPlanWorkspace.getActivePlan ? window.TempoPlanWorkspace.getActivePlan() : null;
                const wsTask = wsPlan && wsPlan.plannedTasks ? wsPlan.plannedTasks[0].task : null;

                // Switch to recovery and check tasks
                window.TempoMode.setMode('recovery');
                const storePlanInRecovery = window.TempoPlanStore.getActivePlan('emergency');

                // Switch back to emergency
                window.TempoMode.setMode('emergency');

                return {
                    sameId: originalTask.id === (wsTask ? wsTask.id : null),
                    sameReference: (wsTask && wsTask.id === 'task-compat-1'),
                    planTasksLength: storePlanInRecovery ? storePlanInRecovery.plannedTasks.length : 0,
                    totalTaskEntities: (storePlanInRecovery && storePlanInRecovery.tasks) ? storePlanInRecovery.tasks.length : 0
                };
            })()
        """)

        assert identity_check['sameId'] and identity_check['sameReference'], "Task ID must remain stable across store, flow, and workspace"
        assert identity_check['planTasksLength'] == 1, f"Task count must remain 1 (no duplicate creation), got: {identity_check['planTasksLength']}"
        assert identity_check['totalTaskEntities'] == 1, "Zero duplicate task entities allowed across mode switches"
        log("✓ Stable task identity and zero entity duplication verified.")

        # =====================================================================
        # CONTRACT CHECK 3: Completion Status Continuity
        # =====================================================================
        log("\n--- CONTRACT CHECK 3: Completion Status Continuity Across References ---")
        completion_check = eval_js("""
            (async () => {
                // Toggle task completion from Home
                window.TempoApp.navigateTo('today');
                window.TempoMode.renderEmodeHome();
                window.TempoMode.toggleTaskCompletion('task-compat-1');

                const storePlan = window.TempoPlanStore.getActivePlan('emergency');
                const storeCompleted = storePlan.plannedTasks[0].task.completed;

                // Check in Plan Workspace
                window.TempoPlanWorkspace.open();
                const wsPlan = window.TempoPlanWorkspace.getActivePlan();
                const wsCompleted = wsPlan.plannedTasks[0].task.completed;

                // Toggle subtask completion in workspace
                window.TempoPlanWorkspace.toggleSubtask('task-compat-1', 's1');
                const updatedPlan = window.TempoPlanStore.getActivePlan('emergency');
                const subtaskCompleted = updatedPlan.plannedTasks[0].task.subtasks[0].completed;

                return {
                    storeCompleted,
                    wsCompleted,
                    subtaskCompleted
                };
            })()
        """)

        assert completion_check['storeCompleted'] is True, "Task completion toggled from Home must update store"
        assert completion_check['wsCompleted'] is True, "Task completion must reflect in Plan Workspace without reload"
        assert completion_check['subtaskCompleted'] is True, "Subtask completion must update synchronously across references"
        log("✓ Task and subtask completion continuity across views verified.")

        # =====================================================================
        # CONTRACT CHECK 4: Execution Order Stability (No Silent Reranking)
        # =====================================================================
        log("\n--- CONTRACT CHECK 4: Execution Order Stability (No Silent Reranking) ---")
        rerank_check = eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

                const multiPlan = {
                    id: 'plan_multi_order',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: today, startTime: '09:00 AM', task: { id: 'order-1', name: 'Task Alpha', durationMinutes: 30, completed: false, subtasks: [] } },
                        { dayDate: today, startTime: '11:00 AM', task: { id: 'order-2', name: 'Task Beta', durationMinutes: 45, completed: false, subtasks: [] } },
                        { dayDate: today, startTime: '02:00 PM', task: { id: 'order-3', name: 'Task Gamma', durationMinutes: 60, completed: false, subtasks: [] } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, blocks: [{ start: '09:00', end: '18:00' }] }]
                };
                multiPlan.tasks = multiPlan.plannedTasks.map(pt => pt.task);
                await window.TempoPlanStore.saveActivePlan('emergency', multiPlan);

                // Select task Beta in Plan Workspace (simulate drawer opening)
                window.TempoPlanWorkspace.open();
                window.TempoPlanWorkspace.selectTask('order-2');

                // Update deadline of task Alpha
                window.TempoPlanWorkspace.saveTaskDeadline('order-1', today, '18:00');

                // Read order back
                const postPlan = window.TempoPlanStore.getActivePlan('emergency');
                const postIds = postPlan.plannedTasks.map(pt => pt.task.id);

                return {
                    initialOrder: ['order-1', 'order-2', 'order-3'],
                    postOrder: postIds
                };
            })()
        """)

        assert rerank_check['postOrder'] == ['order-1', 'order-2', 'order-3'], f"Plan execution order must remain authoritative and NEVER silently rerank, got: {rerank_check['postOrder']}"
        log("✓ Plan execution order is authoritative; no silent reranking verified.")

        # =====================================================================
        # CONTRACT CHECK 5: Non-Destructive Stale Plan Handling
        # =====================================================================
        log("\n--- CONTRACT CHECK 5: Non-Destructive Stale Plan Handling ---")
        stale_check = eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const yestDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
                const yesterday = `${yestDate.getFullYear()}-${pad(yestDate.getMonth() + 1)}-${pad(yestDate.getDate())}`;

                const stalePlan = {
                    id: 'plan_stale_verify',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: yesterday, startTime: '10:00 AM', task: { id: 'stale-1', name: 'Overdue Reading', durationMinutes: 45, completed: false, subtasks: [] } }
                    ],
                    tasks: [],
                    availabilityDays: []
                };
                stalePlan.tasks = stalePlan.plannedTasks.map(pt => pt.task);
                await window.TempoPlanStore.saveActivePlan('emergency', stalePlan);

                // Render Urgent Home
                window.TempoMode.setMode('emergency');
                window.TempoApp.navigateTo('today');
                window.TempoMode.renderEmodeHome();

                const emodeBox = document.getElementById('emode-home-content');
                const hasStaleNotice = emodeBox ? (emodeBox.innerText.includes("Your plan needs an update.") || emodeBox.innerText.includes("Kế hoạch của bạn cần được cập nhật.")) : false;

                // Verify task was NOT automatically rescheduled or deleted
                const currentPlan = window.TempoPlanStore.getActivePlan('emergency');
                const taskDate = currentPlan.plannedTasks[0].dayDate;
                const taskExists = currentPlan.plannedTasks[0].task.id === 'stale-1';

                return {
                    hasStaleNotice,
                    taskDate,
                    taskExists,
                    yesterday
                };
            })()
        """)

        assert stale_check['hasStaleNotice'], "Urgent Home must display SCHEDULE UPDATE NEEDED calmly"
        assert stale_check['taskExists'], "Overdue task must NOT be silently deleted"
        assert stale_check['taskDate'] == stale_check['yesterday'], f"Task date must NOT be silently modified: expected {stale_check['yesterday']}, got {stale_check['taskDate']}"
        log("✓ Non-destructive stale plan handling (no silent rescheduling or deletion) verified.")

        # =====================================================================
        # CONTRACT CHECK 6: Dynamic User Editing Allowed (User Data Not Frozen)
        # =====================================================================
        log("\n--- CONTRACT CHECK 6: Dynamic User Editing Allowed (User Data Not Frozen) ---")
        edit_check = eval_js("""
            (async () => {
                // Open Plan Workspace
                window.TempoPlanWorkspace.open();

                // Add a new task dynamically
                const addRes = window.TempoPlanWorkspace.addNewTask({
                    name: 'Newly Added Literature Review',
                    durationMinutes: 45,
                    hasDeadline: false,
                    subtasks: ['Find 3 papers', 'Draft summary']
                });

                // Read plan
                const plan = window.TempoPlanStore.getActivePlan('emergency');
                const allNames = plan.tasks.map(t => t.name);

                return {
                    addSuccess: !!addRes,
                    hasNewTask: allNames.includes('Newly Added Literature Review'),
                    totalTasks: plan.tasks.length
                };
            })()
        """)

        assert edit_check['addSuccess'] and edit_check['hasNewTask'], "User must be able to dynamically add tasks to the plan"
        assert edit_check['totalTasks'] >= 2, "New task entity successfully persisted in dynamic user plan"
        log("✓ User data remains dynamic and editable; product contract protection does not lock user data.")

        log("\n=======================================================")
        log(">>> ALL URGENT PLAN PRODUCT CONTRACT CHECKS PASSED! <<<")
        log("=======================================================")

    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    run_tests()
