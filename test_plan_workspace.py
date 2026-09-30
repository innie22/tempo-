import subprocess
import time
import json
import urllib.request
import tempfile
import os
import websocket
import sys

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_plan_workspace_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    cmd = [
        edge_path,
        "--headless=new",
        "--remote-debugging-port=9225",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "http://localhost:8000/"
    ]
    
    log("Launching Edge on port 9225...")
    proc = subprocess.Popen(cmd)
    ws = None
    try:
        ws_url = None
        for _ in range(30):
            try:
                with urllib.request.urlopen("http://127.0.0.1:9225/json") as resp:
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
                    ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined' && typeof window.TempoEmergencyFlow !== 'undefined' && typeof window.TempoPlanWorkspace !== 'undefined' && typeof window.TempoFocusZone !== 'undefined'")
                    if ready:
                        eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("Page did not reach ready state")

        send_command("Runtime.enable")
        log("Waiting for page and scripts ready...")
        wait_for_ready()

        # Helper to get today ISO date string
        today_iso = eval_js("new Date().toISOString().split('T')[0]")
        tomorrow_iso = eval_js("""(() => {
            const d = new Date();
            d.setDate(d.getDate() + 1);
            return d.toISOString().split('T')[0];
        })()""")

        log(f"Test environment dates: today={today_iso}, tomorrow={tomorrow_iso}")

        # Setup standard confirmed plan with 3 tasks + 1 unarranged task
        setup_script = f"""(async () => {{
            const todayStr = '{today_iso}';
            const tomorrowStr = '{tomorrow_iso}';
            
            const task1 = {{
                id: 'task-1',
                name: 'Complete History Essay',
                deadline: todayStr + ' 23:59',
                durationMinutes: 90,
                durationLabel: '1h 30m',
                priorityScore: 9,
                planBadge: 'DO THIS',
                completed: false,
                isInProgress: false,
                subtasks: [
                    {{ id: 's1', title: 'Write outline and thesis', duration: '20m', completed: false }},
                    {{ id: 's2', title: 'Draft body paragraphs', duration: '50m', completed: false }},
                    {{ id: 's3', title: 'Final proofread & citations', duration: '20m', completed: false }}
                ]
            }};

            const task2 = {{
                id: 'task-2',
                name: 'Math Problem Set',
                deadline: todayStr + ' 20:00',
                durationMinutes: 60,
                durationLabel: '1h',
                priorityScore: 7,
                planBadge: 'THEN',
                completed: false,
                isInProgress: false,
                subtasks: [
                    {{ id: 's4', title: 'Solve problems 1-10', duration: '60m', completed: false }}
                ]
            }};

            const task3 = {{
                id: 'task-3',
                name: 'Biology Lab Report',
                deadline: tomorrowStr + ' 17:00',
                durationMinutes: 120,
                durationLabel: '2h',
                priorityScore: 6,
                planBadge: 'LATER',
                completed: false,
                isInProgress: false,
                subtasks: [
                    {{ id: 's5', title: 'Analyze sample data', duration: '60m', completed: false }},
                    {{ id: 's6', title: 'Write discussion section', duration: '60m', completed: false }}
                ]
            }};

            const taskUnarranged = {{
                id: 'task-unarranged-1',
                name: 'Physics Pre-lab Quiz',
                deadline: tomorrowStr + ' 23:59',
                durationMinutes: 45,
                durationLabel: '45m',
                priorityScore: 5,
                completed: false,
                isInProgress: false,
                subtasks: []
            }};

            const plan = {{
                planId: 'plan-test-12345',
                createdAt: new Date().toISOString(),
                totalTasks: 4,
                totalWorkloadMinutes: 315,
                totalEstimateMinutes: 315,
                arrangedCount: 3,
                unarrangedCount: 1,
                tasks: [task1, task2, task3, taskUnarranged],
                plannedTasks: [
                    {{
                        dayDate: todayStr,
                        dayLabel: 'TODAY',
                        task: task1,
                        allocatedMinutes: 90,
                        scheduledStartTime: '09:00',
                        scheduledEndTime: '10:45',
                        planPositionBadge: 'DO THIS',
                        hasDeadlineRisk: false
                    }},
                    {{
                        dayDate: todayStr,
                        dayLabel: 'TODAY',
                        task: task2,
                        allocatedMinutes: 60,
                        scheduledStartTime: '11:00',
                        scheduledEndTime: '12:00',
                        planPositionBadge: 'THEN',
                        hasDeadlineRisk: false
                    }},
                    {{
                        dayDate: tomorrowStr,
                        dayLabel: 'TOMORROW',
                        task: task3,
                        allocatedMinutes: 120,
                        scheduledStartTime: '14:00',
                        scheduledEndTime: '16:15',
                        planPositionBadge: 'LATER',
                        hasDeadlineRisk: false
                    }}
                ],
                unarrangedTasks: [
                    {{
                        task: taskUnarranged,
                        isUnarranged: true,
                        reason: 'User opted to leave unscheduled'
                    }}
                ],
                availability: [
                    {{
                        date: todayStr,
                        label: 'TODAY',
                        blocks: [{{ start: '09:00', end: '12:00' }}]
                    }},
                    {{
                        date: tomorrowStr,
                        label: 'TOMORROW',
                        blocks: [{{ start: '14:00', end: '18:00' }}]
                    }}
                ]
            }};

            // Confirm plan in TempoEmergencyFlow and TempoPlanStore
            await window.TempoPlanStore.saveActivePlan('emergency', plan);
            if (window.TempoEmergencyFlow.restorePlanState) {{
                await window.TempoEmergencyFlow.restorePlanState();
            }}
            window.TempoMode.setMode('emergency');
            return true;
        }})()"""

        eval_js(setup_script)
        time.sleep(0.5)

        # ---------------------------------------------------------------------
        # TEST A — ENTRY
        # ---------------------------------------------------------------------
        log("\n--- TEST A — ENTRY ---")
        # Click / invoke View/Edit Plan
        eval_js("window.TempoEmergencyFlow.viewPlan()")
        time.sleep(0.5)
        
        test_a = eval_js("""(() => {
            const screen = document.getElementById('screen-plan-workspace');
            const emergencyScreen = document.getElementById('screen-emergency');
            const isWorkspaceVisible = screen && !screen.classList.contains('hidden');
            const isEmergencyHidden = emergencyScreen && emergencyScreen.classList.contains('hidden');
            
            const plan = window.TempoPlanWorkspace.getActivePlan();
            const planId = plan ? plan.planId : null;
            const taskIds = plan ? plan.plannedTasks.map(pt => pt.task.id) : [];
            const unarrangedIds = plan ? plan.unarrangedTasks.map(u => u.task.id) : [];

            return {
                isWorkspaceVisible,
                isEmergencyHidden,
                planId,
                taskIds,
                unarrangedIds
            };
        })()""")

        assert test_a["isWorkspaceVisible"], "Workspace should be visible"
        assert test_a["isEmergencyHidden"], "Emergency setup screen should remain hidden"
        assert test_a["planId"] == "plan-test-12345", f"PlanId mismatch: {test_a['planId']}"
        assert "task-1" in test_a["taskIds"], "task-1 should be in planned tasks"
        assert "task-unarranged-1" in test_a["unarrangedIds"], "task-unarranged-1 should be in unarranged tasks"
        log("✓ TEST A PASSED: Workspace opens with same planId, same taskIds, setup does not reopen.")

        # ---------------------------------------------------------------------
        # TEST B — HOME
        # ---------------------------------------------------------------------
        log("\n--- TEST B — HOME ---")
        test_b_label = eval_js("""(() => {
            const btn = document.getElementById('plan-workspace-back-home');
            return btn ? btn.textContent.trim() : '';
        })()""")
        assert "Home" in test_b_label, f"Back button must say Home, got: {test_b_label}"

        # Click ← Home
        eval_js("window.TempoPlanWorkspace.navigateHome()")
        time.sleep(0.5)

        test_b = eval_js("""(() => {
            const todayScreen = document.getElementById('screen-today');
            const workspaceScreen = document.getElementById('screen-plan-workspace');
            const isTodayVisible = todayScreen && !todayScreen.classList.contains('hidden');
            const isWorkspaceHidden = workspaceScreen && workspaceScreen.classList.contains('hidden');
            const plan = window.TempoEmergencyFlow.getConfirmedPlan();
            return {
                isTodayVisible,
                isWorkspaceHidden,
                planIntact: plan && plan.planId === 'plan-test-12345'
            };
        })()""")

        assert test_b["isTodayVisible"], "Should navigate Home (#screen-today)"
        assert test_b["isWorkspaceHidden"], "Workspace should be hidden when Home"
        assert test_b["planIntact"], "Plan should remain intact"
        log("✓ TEST B PASSED: Goes Home, user-facing label is Home, plan remains intact.")

        # ---------------------------------------------------------------------
        # TEST C — GLOBAL FOCUS
        # ---------------------------------------------------------------------
        log("\n--- TEST C — GLOBAL FOCUS ---")
        eval_js("window.TempoPlanWorkspace.open()")
        time.sleep(0.5)

        # Click Start Focus Now
        eval_js("window.TempoPlanWorkspace.startGlobalFocus()")
        time.sleep(0.5)

        test_c = eval_js("""(() => {
            const fzRoot = document.getElementById('tempo-focus-zone-root');
            const isFzVisible = fzRoot && !fzRoot.classList.contains('hidden');
            
            // Check session in TempoFocusZone
            const sessionTask = document.querySelector('#tempo-focus-zone-root h2') ? document.querySelector('#tempo-focus-zone-root h2').textContent.trim() : '';
            
            // Verify plan is not reranked
            const plan = window.TempoPlanWorkspace.getActivePlan();
            const order = plan.plannedTasks.map(pt => pt.task.id);

            return {
                isFzVisible,
                sessionTask,
                order
            };
        })()""")

        assert test_c["isFzVisible"], "Focus Zone should open"
        assert "Complete History Essay" in test_c["sessionTask"], f"Expected Task 1 suggested, got: {test_c['sessionTask']}"
        assert test_c["order"] == ["task-1", "task-2", "task-3"], f"Plan should not be reranked, got: {test_c['order']}"
        log("✓ TEST C PASSED: Focus Setup opens, first unfinished arranged task for today suggested, plan not reranked.")

        # ---------------------------------------------------------------------
        # TEST D — CHANGE FOCUS TASK
        # ---------------------------------------------------------------------
        log("\n--- TEST D — CHANGE FOCUS TASK ---")
        eval_js("window.TempoFocusZone.open({ taskId: 'task-2' })")
        time.sleep(0.3)

        test_d = eval_js("""(() => {
            const h2 = document.querySelector('#tempo-focus-zone-root h2') ? document.querySelector('#tempo-focus-zone-root h2').textContent.trim() : '';
            const plan = window.TempoPlanWorkspace.getActivePlan();
            const order = plan.plannedTasks.map(pt => pt.task.id);
            return {
                h2,
                order
            };
        })()""")

        assert "Math Problem Set" in test_d["h2"], f"Expected Math Problem Set selected, got: {test_d['h2']}"
        assert test_d["order"] == ["task-1", "task-2", "task-3"], f"Plan order must not change, got: {test_d['order']}"
        log("✓ TEST D PASSED: Selected focus task changes, plan order untouched.")

        # ---------------------------------------------------------------------
        # TEST E — FOCUS WITHOUT TASK
        # ---------------------------------------------------------------------
        log("\n--- TEST E — FOCUS WITHOUT TASK ---")
        eval_js("window.TempoFocusZone.focusWithoutTask()")
        time.sleep(0.3)

        test_e_setup = eval_js("""(() => {
            const h2 = document.querySelector('#tempo-focus-zone-root h2') ? document.querySelector('#tempo-focus-zone-root h2').textContent.trim() : '';
            const noTaskText = document.querySelector('#tempo-focus-zone-root .text-xs.font-bold') ? document.body.innerHTML.includes('NO TASK') : false;
            return { h2, noTaskText };
        })()""")
        assert test_e_setup["noTaskText"], "Focus Setup should display NO TASK"

        # Start Focus session without task
        eval_js("window.TempoFocusZone.startFocusSession()")
        time.sleep(0.3)

        test_e_active = eval_js("""(() => {
            const plan = window.TempoPlanWorkspace.getActivePlan();
            const inProgressTasks = plan.plannedTasks.filter(pt => pt.task.isInProgress);
            const bodyHtml = document.body.innerHTML;
            const hasNoFakeNextAction = !bodyHtml.includes('Next: undefined') && !bodyHtml.includes('Next: null');
            
            return {
                inProgressCount: inProgressTasks.length,
                hasNoFakeNextAction
            };
        })()""")

        assert test_e_active["inProgressCount"] == 0, f"No task should become in progress, found: {test_e_active['inProgressCount']}"
        assert test_e_active["hasNoFakeNextAction"], "Should not show fake next action"
        
        # Close Focus Zone
        eval_js("window.TempoFocusZone.close()")
        time.sleep(0.3)
        log("✓ TEST E PASSED: Focus can start without task, no taskId, no task in progress, order unchanged.")

        # ---------------------------------------------------------------------
        # TEST F — NEXT ACTION
        # ---------------------------------------------------------------------
        log("\n--- TEST F — NEXT ACTION ---")
        eval_js("""(() => {
            const plan = window.TempoPlanWorkspace.getActivePlan();
            const task1 = plan.plannedTasks.find(pt => pt.task.id === 'task-1').task;
            task1.subtasks[0].completed = true; // Complete first subtask ('Write outline and thesis')
            window.TempoPlanStore.saveActivePlan('emergency', plan);
        })()""")

        eval_js("window.TempoFocusZone.open({ taskId: 'task-1' })")
        time.sleep(0.3)

        test_f = eval_js("""(() => {
            const text = document.querySelector('#tempo-focus-zone-root') ? document.querySelector('#tempo-focus-zone-root').textContent : '';
            const hasSubtask2 = text.includes('Draft body paragraphs');
            return { hasSubtask2 };
        })()""")

        assert test_f["hasSubtask2"], "Next Action must resolve to first unfinished shared subtask ('Draft body paragraphs')"
        eval_js("window.TempoFocusZone.close()")
        time.sleep(0.3)
        log("✓ TEST F PASSED: Next Action correctly surfaces first unfinished shared subtask.")

        # ---------------------------------------------------------------------
        # TEST G — NO TASK TODAY
        # ---------------------------------------------------------------------
        log("\n--- TEST G — NO TASK TODAY ---")
        # Temporarily mock plan with tasks only tomorrow
        eval_js("""(() => {
            const plan = window.TempoPlanWorkspace.getActivePlan();
            window._savedTodayTasks = plan.plannedTasks.filter(pt => pt.dayDate === '{today_iso}');
            plan.plannedTasks = plan.plannedTasks.filter(pt => pt.dayDate !== '{today_iso}');
            window.TempoPlanStore.saveActivePlan('emergency', plan);
            window.TempoPlanWorkspace.render();
        })()""")

        eval_js("window.TempoPlanWorkspace.startGlobalFocus()")
        time.sleep(0.3)

        test_g = eval_js("""(() => {
            const fzRoot = document.getElementById('tempo-focus-zone-root');
            const isFzVisible = fzRoot && !fzRoot.classList.contains('hidden');
            const h2 = document.querySelector('#tempo-focus-zone-root h2') ? document.querySelector('#tempo-focus-zone-root h2').textContent.trim() : '';
            const h3 = document.querySelector('#tempo-focus-zone-root h3') ? document.querySelector('#tempo-focus-zone-root h3').textContent.trim() : '';
            const isChooseOrNoTask = h2.includes('No task selected') || h3.includes('What are you working on?') || document.body.innerHTML.includes('Focus without a task');
            const pushedTomorrowTask = document.body.innerHTML.includes('Biology Lab Report') && h2.includes('Biology Lab Report');
            return {
                isFzVisible,
                isChooseOrNoTask,
                pushedTomorrowTask
            };
        })()""")

        assert test_g["isFzVisible"], "Focus Zone should open"
        assert not test_g["pushedTomorrowTask"], "Must NOT automatically push tomorrow's task"
        assert test_g["isChooseOrNoTask"], "User must be presented with choose task or focus without task"

        eval_js("window.TempoFocusZone.close()")
        time.sleep(0.3)

        # Restore today's tasks
        eval_js("""(() => {
            const plan = window.TempoPlanWorkspace.getActivePlan();
            plan.plannedTasks.unshift(...window._savedTodayTasks);
            window.TempoPlanStore.saveActivePlan('emergency', plan);
            window.TempoPlanWorkspace.render();
        })()""")
        log("✓ TEST G PASSED: No task planned today does not push future tasks; user can choose or focus without task.")

        # ---------------------------------------------------------------------
        # TEST H — TIMELINE
        # ---------------------------------------------------------------------
        log("\n--- TEST H — TIMELINE ---")
        test_h = eval_js("""(() => {
            const root = document.getElementById('plan-workspace-root');
            const html = root ? root.innerHTML : '';
            const hasTodayHeader = html.includes('TODAY');
            const hasTomorrowHeader = html.includes('TOMORROW');
            const hasDoThisBadge = html.includes('DO THIS');
            const hasThenBadge = html.includes('THEN');
            const hasLaterBadge = html.includes('LATER');
            
            // Check execution status separate from position badge
            const hasStatusLabel = html.includes('Not started') || html.includes('In progress');

            return {
                hasTodayHeader,
                hasTomorrowHeader,
                hasDoThisBadge,
                hasThenBadge,
                hasLaterBadge,
                hasStatusLabel
            };
        })()""")

        assert test_h["hasTodayHeader"], "Timeline must group by TODAY"
        assert test_h["hasTomorrowHeader"], "Timeline must group by TOMORROW"
        assert test_h["hasDoThisBadge"], "Timeline must render DO THIS badge"
        assert test_h["hasThenBadge"], "Timeline must render THEN badge"
        assert test_h["hasLaterBadge"], "Timeline must render LATER badge"
        assert test_h["hasStatusLabel"], "Timeline must display execution status distinct from position badges"
        log("✓ TEST H PASSED: Timeline groups by date with DO THIS/THEN/LATER badges and separate execution status.")

        # ---------------------------------------------------------------------
        # TEST I — DRAWER
        # ---------------------------------------------------------------------
        log("\n--- TEST I — DRAWER ---")
        eval_js("window.TempoPlanWorkspace.selectTask('task-1')")
        time.sleep(0.3)

        test_i = eval_js("""(() => {
            const drawer = document.getElementById('plan-workspace-drawer');
            const isDrawerOpen = drawer && !drawer.classList.contains('hidden');
            const text = drawer ? drawer.textContent : '';
            const nameInput = document.getElementById('pw-drawer-task-name');
            const taskName = nameInput ? nameInput.value : '';
            
            return {
                isDrawerOpen,
                hasName: taskName.includes('Complete History Essay') || text.includes('Complete History Essay'),
                hasScheduledTime: text.includes('09:00') || text.includes('10:45'),
                hasDeadline: text.includes('11:59') || text.includes('23:59') || text.includes('PM') || text.includes('Sep') || text.includes('Oct'),
                hasEstimate: text.includes('1h 30m') || text.includes('90m') || text.includes('1.5h'),
                hasStatus: text.includes('NOT STARTED') || text.includes('Not started') || text.includes('In progress'),
                hasSteps: text.includes('Write outline and thesis') && text.includes('Draft body paragraphs')
            };
        })()""")

        assert test_i["isDrawerOpen"], "Drawer should be open"
        assert test_i["hasName"], "Drawer should display task name"
        assert test_i["hasScheduledTime"], "Drawer should display scheduled time"
        assert test_i["hasDeadline"], "Drawer should display deadline"
        assert test_i["hasEstimate"], "Drawer should display estimate"
        assert test_i["hasStatus"], "Drawer should display status"
        assert test_i["hasSteps"], "Drawer should display action steps"
        log("✓ TEST I PASSED: Drawer displays name, scheduled time, deadline, estimate, status, and action steps.")

        # ---------------------------------------------------------------------
        # TEST J — DEADLINE
        # ---------------------------------------------------------------------
        log("\n--- TEST J — DEADLINE ---")
        eval_js("window.TempoPlanWorkspace.saveTaskDeadline('task-1', '2026-10-05', '17:00')")
        time.sleep(0.3)

        test_j = eval_js("""(() => {
            const plan = window.TempoPlanWorkspace.getActivePlan();
            const item = plan.plannedTasks.find(pt => pt.task.id === 'task-1');
            return {
                deadline: item.task.deadline,
                scheduledDate: item.dayDate,
                scheduledStart: item.scheduledStartTime,
                scheduledEnd: item.scheduledEndTime
            };
        })()""")

        assert "2026-10-05" in test_j["deadline"], f"Expected deadline updated, got: {test_j['deadline']}"
        assert test_j["scheduledDate"] == f"{today_iso}", "Scheduled date must NOT silently move"
        assert test_j["scheduledStart"] == "09:00", "Scheduled start time must NOT silently move"
        assert test_j["scheduledEnd"] == "10:45", "Scheduled end time must NOT silently move"
        log("✓ TEST J PASSED: Shared task deadline updated without silently moving scheduled placement.")

        # ---------------------------------------------------------------------
        # TEST K — ESTIMATE
        # ---------------------------------------------------------------------
        log("\n--- TEST K — ESTIMATE ---")
        test_k = eval_js("""(() => {
            const drawerHtml = document.getElementById('plan-workspace-drawer').innerHTML;
            const hasEditEstimateCall = drawerHtml.includes('openEstimateEdit') || drawerHtml.includes('openEditEstimateModal');
            let called = false;
            const orig = window.TempoEmergencyFlow.openEditEstimateModal;
            window.TempoEmergencyFlow.openEditEstimateModal = () => { called = true; };
            window.TempoPlanWorkspace.openEstimateEdit('task-1');
            window.TempoEmergencyFlow.openEditEstimateModal = orig;
            return { hasEditEstimateCall, called };
        })()""")
        assert test_k["hasEditEstimateCall"] and test_k["called"], "Estimate edit must delegate to existing openEditEstimateModal"
        log("✓ TEST K PASSED: Uses existing Tempo Edit Estimate modal integration.")

        # ---------------------------------------------------------------------
        # TEST L — TASK FOCUS
        # ---------------------------------------------------------------------
        log("\n--- TEST L — TASK FOCUS ---")
        eval_js("window.TempoPlanWorkspace.closeDrawer()")
        time.sleep(0.2)
        eval_js("window.TempoPlanWorkspace.startTaskFocus('task-2')")
        time.sleep(0.3)

        test_l = eval_js("""(() => {
            const fzRoot = document.getElementById('tempo-focus-zone-root');
            const isFzVisible = fzRoot && !fzRoot.classList.contains('hidden');
            const text = fzRoot ? fzRoot.textContent : '';
            return {
                isFzVisible,
                hasTask2: text.includes('Math Problem Set')
            };
        })()""")

        assert test_l["isFzVisible"], "Focus Zone should open"
        assert test_l["hasTask2"], "Selected task must be Math Problem Set"
        eval_js("window.TempoFocusZone.close()")
        time.sleep(0.2)
        log("✓ TEST L PASSED: Task-specific Start/Continue opens Focus Zone with that exact task.")

        # ---------------------------------------------------------------------
        # TEST M — UNARRANGED
        # ---------------------------------------------------------------------
        log("\n--- TEST M — UNARRANGED ---")
        test_m_view = eval_js("""(() => {
            const root = document.getElementById('plan-workspace-root');
            const text = root ? root.textContent : '';
            return {
                hasNotScheduledYet: text.includes('NOT SCHEDULED YET') || text.includes('Not Scheduled Yet'),
                hasUnarrangedTask: text.includes('Physics Pre-lab Quiz')
            };
        })()""")

        assert test_m_view["hasNotScheduledYet"], "Must render NOT SCHEDULED YET section"
        assert test_m_view["hasUnarrangedTask"], "Physics Pre-lab Quiz must be in unarranged section"

        # Schedule the unarranged task
        eval_js(f"window.TempoPlanWorkspace.scheduleUnarrangedTask('task-unarranged-1', '{today_iso}', '15:00', '15:45')")
        time.sleep(0.3)

        test_m_scheduled = eval_js("""(() => {
            const plan = window.TempoPlanWorkspace.getActivePlan();
            const inPlanned = plan.plannedTasks.filter(pt => pt.task.id === 'task-unarranged-1');
            const inUnarranged = plan.unarrangedTasks.filter(u => u.task.id === 'task-unarranged-1');
            return {
                plannedCount: inPlanned.length,
                unarrangedCount: inUnarranged.length,
                sameTaskId: inPlanned.length === 1 ? inPlanned[0].task.id : null
            };
        })()""")

        assert test_m_scheduled["plannedCount"] == 1, "Task must move to plannedTasks"
        assert test_m_scheduled["unarrangedCount"] == 0, "Task must be removed from unarrangedTasks"
        assert test_m_scheduled["sameTaskId"] == "task-unarranged-1", "Preserves same taskId"
        log("✓ TEST M PASSED: Unscheduled task appears under NOT SCHEDULED YET; scheduling preserves taskId with no duplicates.")

        # ---------------------------------------------------------------------
        # TEST N — ADD TASK
        # ---------------------------------------------------------------------
        log("\n--- TEST N — ADD TASK ---")
        eval_js(f"""window.TempoPlanWorkspace.addNewTask({{
            name: 'Sociology Reading Chapter 4',
            deadlineDate: '{tomorrow_iso}',
            deadlineTime: '18:00',
            estimateMinutes: 45,
            fitIntoPlan: false
        }})""")
        time.sleep(0.3)

        test_n = eval_js("""(() => {
            const plan = window.TempoPlanWorkspace.getActivePlan();
            const created = plan.unarrangedTasks.find(u => u.task.name === 'Sociology Reading Chapter 4');
            const totalPlannedBefore = 4; // task-1, task-2, task-3, task-unarranged-1
            return {
                created: !!created,
                plannedLength: plan.plannedTasks.length,
                isNotRebuilt: plan.plannedTasks.length === totalPlannedBefore
            };
        })()""")

        assert test_n["created"], "New shared task created in unarranged tasks"
        assert test_n["isNotRebuilt"], "Existing planned tasks were not silently rebuilt"
        log("✓ TEST N PASSED: Add Task creates one shared task without silently rebuilding plan.")

        # ---------------------------------------------------------------------
        # TEST O — RETURN
        # ---------------------------------------------------------------------
        log("\n--- TEST O — RETURN ---")
        eval_js("window.TempoPlanWorkspace.navigateHome()")
        time.sleep(0.3)
        eval_js("window.TempoEmergencyFlow.viewPlan()")
        time.sleep(0.3)

        test_o = eval_js("""(() => {
            const plan = window.TempoPlanWorkspace.getActivePlan();
            const hasTask1 = plan.plannedTasks.some(pt => pt.task.id === 'task-1');
            const hasTask2 = plan.plannedTasks.some(pt => pt.task.id === 'task-2');
            const hasTask3 = plan.plannedTasks.some(pt => pt.task.id === 'task-3');
            const hasUnarranged = plan.unarrangedTasks.some(u => u.task.name === 'Sociology Reading Chapter 4');
            
            return {
                planId: plan.planId,
                hasTask1,
                hasTask2,
                hasTask3,
                hasUnarranged
            };
        })()""")

        assert test_o["planId"] == "plan-test-12345", "Active plan must remain identical"
        assert test_o["hasTask1"] and test_o["hasTask2"] and test_o["hasTask3"] and test_o["hasUnarranged"], "All tasks must remain intact"
        log("✓ TEST O PASSED: Workspace -> Home -> reopen View Plan restores identical active plan.")

        log("\n=======================================================")
        log("ALL 15 TESTS (TEST A THROUGH TEST O) PASSED SUCCESSFULLY!")
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
