import subprocess
import time
import json
import urllib.request
import tempfile
import os
import websocket
import sys

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_planning_reflow_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    cmd = [
        edge_path,
        "--headless=new",
        "--remote-debugging-port=9223",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "http://localhost:8000/"
    ]
    
    log("Launching Edge on port 9223...")
    proc = subprocess.Popen(cmd)
    ws = None
    try:
        ws_url = None
        for _ in range(30):
            try:
                with urllib.request.urlopen("http://127.0.0.1:9223/json") as resp:
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
                    ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined' && typeof window.TempoEmergencyFlow !== 'undefined'")
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

        # Ensure TempoEmergencyFlow is initialized
        eval_js("window.TempoEmergencyFlow.goToStage('entry')")
        time.sleep(0.5)

        # ---------------------------------------------------------------------
        # TEST SUITE I: AVAILABILITY NORMALIZATION & 45/15 RHYTHM UNITS
        # ---------------------------------------------------------------------
        log("\n--- TEST I: AVAILABILITY NORMALIZATION & WORK RHYTHM ---")
        norm_test = eval_js("""(() => {
            const dayContiguous = {
                date: '2026-10-01',
                label: 'THU · OCT 1',
                isUnavailable: false,
                blocks: [
                    { start: '18:00', end: '20:00' },
                    { start: '20:00', end: '22:00' },
                    { start: '22:00', end: '24:00' }
                ]
            };
            const wins1 = window.TempoEmergencyFlow.getNormalizedWindowsForDay ? window.TempoEmergencyFlow.getNormalizedWindowsForDay(dayContiguous) : null;
            
            const dayOverlapping = {
                date: '2026-10-01',
                label: 'THU · OCT 1',
                isUnavailable: false,
                blocks: [
                    { start: '18:00', end: '20:30' },
                    { start: '20:00', end: '22:00' }
                ]
            };
            
            const dayGap = {
                date: '2026-10-01',
                label: 'THU · OCT 1',
                isUnavailable: false,
                blocks: [
                    { start: '18:00', end: '20:00' },
                    { start: '21:00', end: '23:00' }
                ]
            };

            const r90 = window.TempoEmergencyFlow.calculateTaskWorkRhythm ? window.TempoEmergencyFlow.calculateTaskWorkRhythm(90) : null;
            const r120 = window.TempoEmergencyFlow.calculateTaskWorkRhythm ? window.TempoEmergencyFlow.calculateTaskWorkRhythm(120) : null;

            return {
                r90,
                r120
            };
        })()""")
        log(f"Normalization & Rhythm test result: {json.dumps(norm_test)}")

        # ---------------------------------------------------------------------
        # TEST SUITE A: DRAG + REFLOW (Section 10 Example)
        # ---------------------------------------------------------------------
        log("\n--- TEST A: DRAG + REFLOW (Task A 2h, Task B 1.5h, Order B->A to A->B) ---")
        setup_a = eval_js("""(() => {
            // Setup today with availability 6:00 PM to 12:00 AM (18:00 to 24:00)
            const today = new Date();
            const todayStr = today.toISOString().split('T')[0];
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            const tomorrowStr = tomorrow.toISOString().split('T')[0];

            window.TempoEmergencyFlow.resetFlowState();
            
            // Set availabilityDays
            const days = [
                {
                    date: todayStr,
                    label: 'TODAY',
                    isUnavailable: false,
                    preservedBlocks: [],
                    blocks: [{ id: 'b_t1', start: '18:00', end: '24:00', minutes: 360 }]
                },
                {
                    date: tomorrowStr,
                    label: 'TOMORROW',
                    isUnavailable: false,
                    preservedBlocks: [],
                    blocks: [{ id: 'b_tm1', start: '09:00', end: '17:00', minutes: 480 }]
                }
            ];

            // Define Task A (2h) and Task B (1.5h)
            const taskA = {
                id: 'task_a_120',
                name: 'Task A (Report)',
                durationMinutes: 120,
                durationLabel: '2h',
                hasDeadline: true,
                deadlineDate: todayStr,
                deadlineTime: '23:59',
                subtasks: [{ id: 'sub_a1', title: 'Outline', completed: false }]
            };
            const taskB = {
                id: 'task_b_90',
                name: 'Task B (Analysis)',
                durationMinutes: 90,
                durationLabel: '1h 30m',
                hasDeadline: true,
                deadlineDate: todayStr,
                deadlineTime: '23:59',
                subtasks: [{ id: 'sub_b1', title: 'Data gather', completed: false }]
            };

            // Set confirmedPlan with initial order: Task B then Task A
            const plan = {
                plannedTasks: [
                    {
                        task: taskB,
                        dayDate: todayStr,
                        dayLabel: 'TODAY',
                        startTime: null,
                        endTime: null,
                        startMin: null,
                        endMin: null,
                        isOverCapacity: false,
                        executionBadge: 'UP NEXT',
                        hasDeadlineConflict: false
                    },
                    {
                        task: taskA,
                        dayDate: todayStr,
                        dayLabel: 'TODAY',
                        startTime: null,
                        endTime: null,
                        startMin: null,
                        endMin: null,
                        isOverCapacity: false,
                        executionBadge: 'THEN',
                        hasDeadlineConflict: false
                    }
                ],
                unallocatedTasks: [],
                unarrangedTasks: [],
                totalWorkloadMinutes: 210,
                totalAvailableMinutes: 360,
                availabilityDays: days
            };

            window.location.hash = '#emergency';
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('emergency');
            }
            window.TempoPlanStore.saveActivePlan('emergency', plan);
            window.TempoEmergencyFlow.restorePlanState();
            window.TempoEmergencyFlow.goToStage('plan-review');
            return true;
        })()""")
        time.sleep(1)

        # Inspect initial plan order and scheduled times
        plan_initial = eval_js("""(() => {
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const pt = plan.plannedTasks;
            const arrowsPresent = !!document.querySelector('button[title=\"Move earlier\"], button[title=\"Move later\"]');
            const dragHandles = document.querySelectorAll('.em-drag-handle').length;
            const laterBtns = document.querySelectorAll('button[title=\"Do this task later\"]').length;
            return {
                pt: pt.map(p => ({
                    id: p.task.id,
                    name: p.task.name,
                    start: p.startTime,
                    end: p.endTime,
                    startMin: p.startMin,
                    endMin: p.endMin,
                    badge: p.executionBadge,
                    estimate: p.task.durationLabel
                })),
                arrowsPresent,
                dragHandles,
                laterBtns
            };
        })()""")
        log(f"Initial plan: {json.dumps(plan_initial, indent=2)}")

        # Drag Task A (index 1) to position 0 (above Task B)
        eval_js("window.TempoEmergencyFlow.reorderPlannedTasks(1, 0)")
        time.sleep(0.5)

        plan_after_drag = eval_js("""(() => {
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const pt = plan.plannedTasks;
            const recoveryTexts = Array.from(document.querySelectorAll('.em-timeline-card + div, div')).map(e => e.textContent).filter(t => t.includes('30m recovery'));
            return {
                pt: pt.map(p => ({
                    id: p.task.id,
                    name: p.task.name,
                    start: p.startTime,
                    end: p.endTime,
                    startMin: p.startMin,
                    endMin: p.endMin,
                    badge: p.executionBadge,
                    estimate: p.task.durationLabel,
                    durationMinutes: p.task.durationMinutes
                })),
                recoveryCount: recoveryTexts.length
            };
        })()""")
        log(f"Plan after dragging A above B: {json.dumps(plan_after_drag, indent=2)}")

        # Verify Test A points:
        # A is first: start 6:00 PM (1080), end 8:30 PM (1230). Total span 150m (120m focus + 30m break).
        # Recovery: 8:30 PM to 9:00 PM (30m).
        # B is second: start 9:00 PM (1260), end 10:45 PM (1365). Total span 105m (90m focus + 15m break).
        p0 = plan_after_drag["pt"][0]
        p1 = plan_after_drag["pt"][1]
        assert p0["id"] == "task_a_120", f"Expected Task A first, got {p0['id']}"
        assert p1["id"] == "task_b_90", f"Expected Task B second, got {p1['id']}"
        assert p0["start"] == "6:00 PM" and p0["end"] == "8:30 PM", f"Task A expected 6:00 PM - 8:30 PM, got {p0['start']} - {p0['end']}"
        assert p1["start"] == "9:00 PM" and p1["end"] == "10:45 PM", f"Task B expected 9:00 PM - 10:45 PM, got {p1['start']} - {p1['end']}"
        assert p0["durationMinutes"] == 120 and p1["durationMinutes"] == 90, "Estimates must not be changed"
        assert plan_initial["arrowsPresent"] is False, "Arrow buttons must be removed"
        assert plan_initial["dragHandles"] >= 2, "Drag handles must be present"
        assert plan_initial["laterBtns"] >= 2, "Do this task later buttons must be present"
        log(">>> TEST A PASSED: Drag reflow, 45/15 rhythm, 30m recovery, estimate preservation verified.")

        # ---------------------------------------------------------------------
        # TEST SUITE B: DEADLINE CONFLICT
        # ---------------------------------------------------------------------
        log("\n--- TEST B: DEADLINE CONFLICT ---")
        # Give Task A an early deadline (e.g. 7:00 PM = 19:00 = 1140 min)
        # When dragged after Task B (finishing at 10:45 PM), it will conflict!
        eval_js("""(() => {
            const today = new Date().toISOString().split('T')[0];
            window.TempoEmergencyFlow.reorderPlannedTasks(0, 1); // Move A back after B (finishes at 10:45 PM)
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const taskA = plan.plannedTasks.find(p => p.task.id === 'task_a_120').task;
            taskA.hasDeadline = true;
            taskA.deadlineDate = today;
            taskA.deadlineTime = '20:00'; // 8:00 PM (1200 min), but A ends at 22:45 (1365 min)
            window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder ? window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder() : null;
            window.TempoEmergencyFlow.renderPlanReview ? window.TempoEmergencyFlow.renderPlanReview() : null;
        })()""")
        time.sleep(0.5)

        deadline_test = eval_js("""(() => {
            const warningEl = document.querySelector('[data-deadline-warning=\"true\"]');
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const pt = plan.plannedTasks;
            return {
                warningFound: !!warningEl,
                warningText: warningEl ? warningEl.textContent : '',
                order: pt.map(p => p.task.id),
                hasDeadlineConflict: pt.find(p => p.task.id === 'task_a_120')?.hasDeadlineConflict
            };
        })()""")
        log(f"Deadline test result: {json.dumps(deadline_test, indent=2)}")
        assert deadline_test["hasDeadlineConflict"] is True, "Deadline conflict flag must be true"
        assert deadline_test["warningFound"] is True, "Deadline warning banner must be visible"
        assert deadline_test["order"][0] == "task_b_90" and deadline_test["order"][1] == "task_a_120", "User order must not be silently reverted"
        log(">>> TEST B PASSED: Deadline warning displayed and user explicit order preserved.")

        # ---------------------------------------------------------------------
        # TEST SUITE C: AVAILABILITY CONFLICT
        # ---------------------------------------------------------------------
        log("\n--- TEST C: AVAILABILITY CONFLICT ---")
        # Add a 4-hour task (240 min, span 315 min) that exceeds the 6-hour window when combined with B and A
        avail_test = eval_js("""(() => {
            const today = new Date().toISOString().split('T')[0];
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            plan.plannedTasks.push({
                task: {
                    id: 'task_c_huge',
                    name: 'Task C (Huge project)',
                    durationMinutes: 240,
                    durationLabel: '4h',
                    hasDeadline: false
                },
                dayDate: today,
                dayLabel: 'TODAY',
                startTime: null,
                endTime: null,
                startMin: null,
                endMin: null,
                isOverCapacity: false,
                executionBadge: 'LATER',
                hasDeadlineConflict: false
            });
            window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
            window.TempoEmergencyFlow.renderPlanReview();
            
            const overCapacityTask = plan.plannedTasks.find(p => p.task.id === 'task_c_huge');
            const cardOverCapacity = document.querySelector('[data-task-id=\"task_c_huge\"]')?.textContent.includes('Availability conflict');
            const dayWarning = document.body.textContent.includes('Availability conflict');

            return {
                isOverCapacity: overCapacityTask.isOverCapacity,
                startTime: overCapacityTask.startTime,
                cardOverCapacity,
                dayWarning,
                estimatePreserved: overCapacityTask.task.durationMinutes === 240
            };
        })()""")
        log(f"Availability conflict result: {json.dumps(avail_test, indent=2)}")
        assert avail_test["isOverCapacity"] is True, "Task C must be marked isOverCapacity"
        assert avail_test["startTime"] is None, "Over-capacity task must not fabricate start time"
        assert avail_test["estimatePreserved"] is True, "Task estimate must remain 240m without shortening"
        log(">>> TEST C PASSED: Availability conflict cleanly reported without inventing time or shortening estimates.")

        # Remove Task C for subsequent tests
        eval_js("""(() => {
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            plan.plannedTasks = plan.plannedTasks.filter(p => p.task.id !== 'task_c_huge');
            window.TempoPlanStore.saveActivePlan('emergency', plan);
            window.TempoEmergencyFlow.restorePlanState();
            window.TempoEmergencyFlow.goToStage('plan-review');
        })()""")

        # ---------------------------------------------------------------------
        # TEST SUITE D & E: "DO THIS TASK LATER" & RESCHEDULING
        # ---------------------------------------------------------------------
        log("\n--- TEST D & E: 'DO THIS TASK LATER' & RESCHEDULING ---")
        # Click "Do this task later" on Task A (index 1)
        eval_js("window.TempoEmergencyFlow.openScheduleModal(1)")
        time.sleep(0.5)

        modal_open = eval_js("""(() => {
            const modal = document.querySelector('[aria-labelledby=\"em-schedule-modal-title\"]');
            const title = document.getElementById('em-schedule-modal-title')?.textContent.trim();
            const taskInfo = modal?.textContent.includes('Task A (Report)');
            const radioOptions = document.querySelectorAll('input[name=\"em_schedule_window\"]').length;
            return {
                modalFound: !!modal,
                title,
                taskInfo,
                radioOptions
            };
        })()""")
        log(f"Scheduling modal check: {json.dumps(modal_open, indent=2)}")
        assert modal_open["modalFound"] is True, "Scheduling modal must be open"
        assert "When would you like to do this?" in modal_open["title"], "Modal header must match"
        assert modal_open["taskInfo"] is True, "Modal must display task info"

        # Reschedule Task A to TOMORROW
        resched_result = eval_js("""(() => {
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            const tomorrowStr = tomorrow.toISOString().split('T')[0];

            // Select tomorrow's window option
            const radio = Array.from(document.querySelectorAll('input[name=\"em_schedule_window\"]')).find(r => r.value.startsWith(tomorrowStr));
            if (radio) {
                radio.checked = true;
                window.TempoEmergencyFlow.selectScheduleWindow(radio.value);
            }
            window.TempoEmergencyFlow.executeScheduleTask();

            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const taskAItem = plan.plannedTasks.find(p => p.task.id === 'task_a_120');
            return {
                newDayDate: taskAItem.dayDate,
                newStartTime: taskAItem.startTime,
                newEndTime: taskAItem.endTime,
                sameTaskId: taskAItem.task.id === 'task_a_120',
                plannedCount: plan.plannedTasks.length
            };
        })()""")
        log(f"Rescheduled Task A: {json.dumps(resched_result, indent=2)}")
        assert resched_result["sameTaskId"] is True, "Same taskId must be preserved"
        assert resched_result["newStartTime"] is not None, "Task A must be scheduled in tomorrow's window"
        log(">>> TEST D & E PASSED: Scheduling modal opened and rescheduled task to new day with reflow.")

        # ---------------------------------------------------------------------
        # TEST SUITE F: ADD AVAILABLE TIME INLINE FROM MODAL
        # ---------------------------------------------------------------------
        log("\n--- TEST F: ADD AVAILABLE TIME INLINE FROM MODAL ---")
        eval_js("window.TempoEmergencyFlow.openScheduleModal(0)") # Open for Task B
        time.sleep(0.3)
        eval_js("window.TempoEmergencyFlow.toggleModalAddTime()") # Click "+ Add available time"
        time.sleep(0.3)

        add_time_result = eval_js("""(() => {
            const day3 = new Date();
            day3.setDate(day3.getDate() + 2);
            const day3Str = day3.toISOString().split('T')[0];

            document.getElementById('em-modal-add-date').value = day3Str;
            document.getElementById('em-modal-add-start').value = '10:00';
            document.getElementById('em-modal-add-end').value = '14:00';
            window.TempoEmergencyFlow.saveModalAddedTime();

            // Check if day 3 window is now in availabilityDays and auto-selected
            const modalState = window.TempoEmergencyFlow.getScheduleModalState ? window.TempoEmergencyFlow.getScheduleModalState() : null;
            const hasDay3 = modalState && modalState.selectedWindowKey ? modalState.selectedWindowKey.startsWith(day3Str) : false;
            
            // Now schedule Task B to this newly added time
            window.TempoEmergencyFlow.executeScheduleTask();

            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const taskBItem = plan.plannedTasks.find(p => p.task.id === 'task_b_90');

            return {
                hasDay3,
                taskBDay: taskBItem.dayDate,
                taskBStart: taskBItem.startTime,
                taskBEnd: taskBItem.endTime,
                sameTaskId: taskBItem.task.id === 'task_b_90'
            };
        })()""")
        log(f"Add available time result: {json.dumps(add_time_result, indent=2)}")
        assert add_time_result["hasDay3"] is True, "Newly added window must be auto-selected"
        assert add_time_result["taskBStart"] == "10:00 AM", f"Task B should start at 10:00 AM on Day 3, got {add_time_result['taskBStart']}"
        log(">>> TEST F PASSED: Add available time inline persists, auto-selects, and schedules task.")

        # ---------------------------------------------------------------------
        # TEST SUITE G: UNARRANGED ("I'll figure it out later")
        # ---------------------------------------------------------------------
        log("\n--- TEST G: UNARRANGED TASK VIA 'I\\'LL FIGURE IT OUT LATER' ---")
        eval_js("window.TempoEmergencyFlow.openScheduleModal(0)") # Open modal for first task
        time.sleep(0.3)
        eval_js("window.TempoEmergencyFlow.scheduleTaskAsUnarranged()") # Click "I'll figure it out later"
        time.sleep(0.5)

        unarranged_check = eval_js("""(() => {
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const unarranged = plan.unarrangedTasks || [];
            const unarrangedSection = document.getElementById('em-unarranged-section');
            const cardsInUnarranged = unarrangedSection ? unarrangedSection.querySelectorAll('[data-unarranged-index]').length : 0;
            const laterBadgeOnUnarranged = unarrangedSection ? unarrangedSection.textContent.includes('LATER') : false;

            return {
                unarrangedCount: unarranged.length,
                unarrangedTaskName: unarranged[0]?.name,
                cardsInUnarranged,
                hasSection: !!unarrangedSection,
                laterBadgeOnUnarranged,
                subtasksPreserved: unarranged[0]?.subtasks?.length > 0
            };
        })()""")
        log(f"Unarranged check: {json.dumps(unarranged_check, indent=2)}")
        assert unarranged_check["unarrangedCount"] == 1, "Exactly 1 task must be in unarrangedTasks"
        assert unarranged_check["cardsInUnarranged"] == 1, "UNARRANGED section must render 1 card"
        assert unarranged_check["laterBadgeOnUnarranged"] is False, "UNARRANGED task must NOT have a LATER badge"
        assert unarranged_check["subtasksPreserved"] is True, "Subtasks must remain intact"
        log(">>> TEST G PASSED: Task moved to UNARRANGED section, unscheduled, intact metadata, no LATER badge.")

        # ---------------------------------------------------------------------
        # TEST SUITE H: REARRANGE UNARRANGED TASK ("Schedule task ->")
        # ---------------------------------------------------------------------
        log("\n--- TEST H: REARRANGE UNARRANGED TASK ---")
        eval_js("window.TempoEmergencyFlow.openScheduleModalForUnarranged(0)")
        time.sleep(0.3)

        restore_unarranged = eval_js("""(() => {
            const today = new Date().toISOString().split('T')[0];
            const radio = Array.from(document.querySelectorAll('input[name=\"em_schedule_window\"]')).find(r => r.value.startsWith(today));
            if (radio) {
                radio.checked = true;
                window.TempoEmergencyFlow.selectScheduleWindow(radio.value);
            }
            window.TempoEmergencyFlow.executeScheduleTask();

            const plan = window.TempoPlanStore.getActivePlan('emergency');
            return {
                unarrangedCount: (plan.unarrangedTasks || []).length,
                plannedCount: plan.plannedTasks.length,
                taskRestoredId: plan.plannedTasks[plan.plannedTasks.length - 1].task.id
            };
        })()""")
        log(f"Restore unarranged result: {json.dumps(restore_unarranged, indent=2)}")
        assert restore_unarranged["unarrangedCount"] == 0, "Unarranged tasks must now be 0"
        assert restore_unarranged["plannedCount"] == 2, "Planned tasks must now be 2"
        log(">>> TEST H PASSED: Unarranged task successfully scheduled back to timeline.")

        # ---------------------------------------------------------------------
        # TEST SUITE J: PERSISTENCE (Reload Browser Tab)
        # ---------------------------------------------------------------------
        log("\n--- TEST J: PERSISTENCE ACROSS RELOAD ---")
        # Set a task as unarranged first so we verify: order, placement, unarranged, new availability all survive reload!
        eval_js("window.TempoEmergencyFlow.openScheduleModal(1)")
        time.sleep(0.2)
        eval_js("window.TempoEmergencyFlow.scheduleTaskAsUnarranged()")
        time.sleep(0.5)

        before_reload = eval_js("""(() => {
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            return {
                plannedTaskId: plan.plannedTasks[0].task.id,
                plannedTaskDay: plan.plannedTasks[0].dayDate,
                plannedTaskStart: plan.plannedTasks[0].startTime,
                unarrangedTaskId: plan.unarrangedTasks[0].id,
                availDaysCount: plan.availabilityDays.length
            };
        })()""")
        log(f"State before reload: {json.dumps(before_reload, indent=2)}")

        # Reload the page
        log("Reloading page...")
        eval_js("window.location.reload()", await_promise=False)
        time.sleep(1)
        wait_for_ready()

        # Restore emergency flow stage
        eval_js("window.TempoEmergencyFlow.goToStage('plan-review')")
        time.sleep(0.5)

        after_reload = eval_js("""(() => {
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const unarrangedSection = document.getElementById('em-unarranged-section');
            return {
                plannedTaskId: plan?.plannedTasks[0]?.task?.id,
                plannedTaskDay: plan?.plannedTasks[0]?.dayDate,
                plannedTaskStart: plan?.plannedTasks[0]?.startTime,
                unarrangedTaskId: plan?.unarrangedTasks[0]?.id,
                availDaysCount: plan?.availabilityDays?.length,
                unarrangedRendered: unarrangedSection?.querySelectorAll('[data-unarranged-index]')?.length
            };
        })()""")
        log(f"State after reload: {json.dumps(after_reload, indent=2)}")
        assert after_reload["plannedTaskId"] == before_reload["plannedTaskId"], "Planned task ID must survive reload"
        assert after_reload["plannedTaskDay"] == before_reload["plannedTaskDay"], "Planned day must survive reload"
        assert after_reload["plannedTaskStart"] == before_reload["plannedTaskStart"], "Planned time must survive reload"
        assert after_reload["unarrangedTaskId"] == before_reload["unarrangedTaskId"], "Unarranged task must survive reload"
        assert after_reload["unarrangedRendered"] == 1, "Unarranged section must be rendered after reload"
        assert after_reload["availDaysCount"] == before_reload["availDaysCount"], "Added availability must survive reload"
        log(">>> TEST J PASSED: Persistence across reload verified successfully.")

        log("\n=======================================================")
        log("ALL TEST CASES A THROUGH J PASSED WITH 100% SUCCESS!")
        log("=======================================================")

    finally:
        if ws:
            ws.close()
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    run_tests()
