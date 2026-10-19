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

user_data_dir = tempfile.mkdtemp(prefix="tempo_breakdown_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9265

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

log("Launching Edge on port 9265...")
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
                    user_metadata: {
                        full_name: 'Alex Chen',
                        display_name: 'Alex Chen',
                        role: 'student'
                    }
                };
                localStorage.setItem('tempo_mock_account_alex.chen@university.edu', JSON.stringify(mock));
                await window.TempoAuth.signIn("alex.chen@university.edu", "password123");
            }
            window.TempoMode.setMode('emergency');
        })()
    """)

    today = eval_js("new Date().toISOString().split('T')[0]")

    # =========================================================================
    # SCENARIO 1: Task with action steps saved -> No duplicate breakdown prompt
    # =========================================================================
    log("\n--- SCENARIO 1: Task With Action Steps Saved (Case A) ---")
    s1_res = eval_js(f"""
        (async () => {{
            const planWithSteps = {{
                id: 'plan_with_steps',
                planType: 'emergency',
                plannedTasks: [
                    {{
                        dayDate: '{today}',
                        startTime: '09:00 AM',
                        task: {{
                            id: 'task_broken_down',
                            name: 'Literature Review Synthesis',
                            durationMinutes: 60,
                            completed: false,
                            subtasks: [
                                {{ id: 'sub_1', title: 'Search Google Scholar for 3 articles', durationMinutes: 20, completed: false }},
                                {{ id: 'sub_2', title: 'Extract thesis citations into table', durationMinutes: 25, completed: false }},
                                {{ id: 'sub_3', title: 'Write introductory synthesis summary', durationMinutes: 15, completed: false }}
                            ]
                        }}
                    }},
                    {{
                        dayDate: '{today}',
                        startTime: '11:00 AM',
                        task: {{
                            id: 'task_2_unbroken',
                            name: 'Math Homework Problem Set',
                            durationMinutes: 45,
                            completed: false,
                            subtasks: []
                        }}
                    }}
                ],
                tasks: []
            }};
            planWithSteps.tasks = planWithSteps.plannedTasks.map(pt => pt.task);
            await window.TempoPlanStore.saveActivePlan('emergency', planWithSteps);
            window.TempoEmergencyFlow.setConfirmedPlan(planWithSteps);

            // Trigger post-save popup
            window.TempoUrmodeFlow.showTaskForNowPopupAfterSave(planWithSteps);
            await new Promise(r => setTimeout(r, 200));

            const modal = document.getElementById('modal-urmode-flow');
            const isVisible = modal && !modal.classList.contains('hidden');
            const eyebrow = modal?.querySelector('span.text-xs.font-extrabold')?.innerText || '';
            const heading = modal?.querySelector('h2')?.innerText || '';
            const cardText = modal?.querySelector('.border-2')?.innerText || '';
            const modalText = modal?.innerText || '';
            const buttons = Array.from(modal?.querySelectorAll('button') || []).map(b => b.innerText.trim());

            return {{
                isVisible,
                eyebrow,
                heading,
                hasTaskName: cardText.includes('Literature Review Synthesis'),
                hasStep1: cardText.includes('Search Google Scholar for 3 articles'),
                hasStep2: cardText.includes('Extract thesis citations into table'),
                hasStep3: cardText.includes('Write introductory synthesis summary'),
                hasBreakdownQuestion: modalText.includes('Would you like to break down this task into smaller steps?'),
                hasBreakdownButton: buttons.some(b => b.includes('Break down task')),
                hasNoStartWorkingButton: buttons.some(b => b.includes('No, start working')),
                buttons
            }};
        }})()
    """)
    log(f"Scenario 1 Result:\n{json.dumps(s1_res, indent=2)}")
    assert s1_res["isVisible"] is True, "Your task for now popup must appear"
    assert "PLAN CONFIRMED & SAVED" in s1_res["eyebrow"], f"Expected 'PLAN CONFIRMED & SAVED', got {s1_res['eyebrow']}"
    assert "Your task for now" in s1_res["heading"], f"Expected 'Your task for now', got {s1_res['heading']}"
    assert s1_res["hasTaskName"] is True, "Task name must be rendered in highlight card"
    assert s1_res["hasStep1"] and s1_res["hasStep2"] and s1_res["hasStep3"], "All concrete action steps must be displayed in card"
    assert s1_res["hasBreakdownQuestion"] is True, "Must explicitly ask whether to break down task even if steps exist"
    assert s1_res["hasBreakdownButton"] is True, "Must provide 'Break down task →' choice"
    assert s1_res["hasNoStartWorkingButton"] is True, "Must provide 'No, start working' choice"
    log("✓ Scenario 1 (Part 1) passed: Prompt and choices are explicitly shown for task with existing action steps.")

    # Scenario 1 Part 2: Enter breakdown flow and verify existing steps are safely preserved and editable
    s1_breakdown_res = eval_js("""
        (async () => {
            const modal = document.getElementById('modal-urmode-flow');
            const breakBtn = Array.from(modal.querySelectorAll('button')).find(b => b.innerText.includes('Break down task'));
            if (!breakBtn) throw new Error("'Break down task →' button not found");

            await breakBtn.click();
            await new Promise(r => setTimeout(r, 200));

            const heading = modal?.querySelector('h2')?.innerText || '';
            const subtaskList = document.getElementById('breakdown-subtask-list');
            const stepItems = Array.from(subtaskList?.children || []).map(el => el.innerText.trim());

            // Test adding a step
            const input = document.getElementById('breakdown-subtask-input');
            input.value = 'Review professor guidelines (10 min)';
            window.TempoUrmodeFlow.addSubtask('task_broken_down');
            await new Promise(r => setTimeout(r, 200));

            const planAfterAdd = window.TempoPlanStore.getActivePlan('emergency');
            const subtasksAfterAdd = planAfterAdd.plannedTasks[0].task.subtasks;

            // Test removing the added step
            const addedSubtask = subtasksAfterAdd.find(s => s.title === 'Review professor guidelines (10 min)');
            if (addedSubtask) {
                window.TempoUrmodeFlow.removeSubtask('task_broken_down', addedSubtask.id);
                await new Promise(r => setTimeout(r, 200));
            }

            const planAfterRemove = window.TempoPlanStore.getActivePlan('emergency');
            const finalSubtasks = planAfterRemove.plannedTasks[0].task.subtasks;

            return {
                heading,
                initialRenderedStepCount: stepItems.length,
                initialStepsMatch: stepItems.some(t => t.includes('Search Google Scholar')) &&
                                   stepItems.some(t => t.includes('Extract thesis citations')) &&
                                   stepItems.some(t => t.includes('Write introductory synthesis')),
                countAfterAdd: subtasksAfterAdd.length,
                countAfterRemove: finalSubtasks.length,
                originalSubtaskIdsPreserved: finalSubtasks[0].id === 'sub_1' && finalSubtasks[1].id === 'sub_2' && finalSubtasks[2].id === 'sub_3'
            };
        })()
    """)
    log(f"Scenario 1 Breakdown Flow Result:\n{json.dumps(s1_breakdown_res, indent=2)}")
    assert "Break down: Literature Review Synthesis" in s1_breakdown_res["heading"], "Must enter breakdown popup for selected task"
    assert s1_breakdown_res["initialRenderedStepCount"] == 3, f"Expected 3 steps initially, got {s1_breakdown_res['initialRenderedStepCount']}"
    assert s1_breakdown_res["initialStepsMatch"] is True, "All existing steps must be rendered in breakdown popup"
    assert s1_breakdown_res["countAfterAdd"] == 4, "Adding a step must increase step count without duplication"
    assert s1_breakdown_res["countAfterRemove"] == 3, "Removing step must restore original step count"
    assert s1_breakdown_res["originalSubtaskIdsPreserved"] is True, "Original subtask IDs must remain unchanged"
    log("✓ Scenario 1 (Part 2) passed: Existing steps safely preserved, reviewed, and edited in breakdown flow.")

    # =========================================================================
    # SCENARIO 2: Task without action steps saved -> Optional breakdown available
    # =========================================================================
    log("\n--- SCENARIO 2: Task Without Action Steps (Case B) ---")
    s2_res = eval_js(f"""
        (async () => {{
            const planNoSteps = {{
                id: 'plan_no_steps',
                planType: 'emergency',
                plannedTasks: [
                    {{
                        dayDate: '{today}',
                        startTime: '09:00 AM',
                        task: {{
                            id: 'task_needs_breakdown',
                            name: 'Chemistry Lab Report Writing',
                            durationMinutes: 90,
                            completed: false,
                            subtasks: []
                        }}
                    }}
                ],
                tasks: []
            }};
            planNoSteps.tasks = planNoSteps.plannedTasks.map(pt => pt.task);
            await window.TempoPlanStore.saveActivePlan('emergency', planNoSteps);
            window.TempoEmergencyFlow.setConfirmedPlan(planNoSteps);

            // Trigger post-save popup
            window.TempoUrmodeFlow.showTaskForNowPopupAfterSave(planNoSteps);
            await new Promise(r => setTimeout(r, 200));

            const modal = document.getElementById('modal-urmode-flow');
            const isVisible = modal && !modal.classList.contains('hidden');
            const heading = modal?.querySelector('h2')?.innerText || '';
            const modalText = modal?.innerText || '';
            const buttons = Array.from(modal?.querySelectorAll('button') || []).map(b => b.innerText.trim());

            return {{
                isVisible,
                heading,
                hasBreakdownQuestion: modalText.includes('Would you like to break down this task into smaller steps?'),
                hasBreakdownButton: buttons.some(b => b.includes('Break down task')),
                hasNoStartWorkingButton: buttons.some(b => b.includes('No, start working')),
                buttons
            }};
        }})()
    """)
    log(f"Scenario 2 Result:\n{json.dumps(s2_res, indent=2)}")
    assert s2_res["isVisible"] is True, "Your task for now popup must appear"
    assert s2_res["hasBreakdownQuestion"] is True, "Must present optional breakdown question for task without steps"
    assert s2_res["hasBreakdownButton"] is True, "Must provide 'Break down task →' choice"
    assert s2_res["hasNoStartWorkingButton"] is True, "Must provide 'No, start working' choice"
    log("✓ Scenario 2 passed: Task without action steps preserves the optional breakdown prompt.")

    # =========================================================================
    # SCENARIO 3: Choose not to break down task -> Start-working flow continues
    # =========================================================================
    log("\n--- SCENARIO 3: Choose Not to Break Down Task ---")
    s3_res = eval_js("""
        (async () => {
            // Find 'No, start working' button and click it
            const modal = document.getElementById('modal-urmode-flow');
            const noBtn = Array.from(modal.querySelectorAll('button')).find(b => b.innerText.includes('No, start working'));
            if (!noBtn) throw new Error("'No, start working' button not found");

            await noBtn.click();
            await new Promise(r => setTimeout(r, 200));

            const newEyebrow = modal?.querySelector('span.text-xs.font-extrabold')?.innerText || '';
            const newHeading = modal?.querySelector('h2')?.innerText || '';
            const text = modal?.innerText || '';

            return {
                newEyebrow,
                newHeading,
                isStartWorkingPopup: newHeading.includes('Start working on your plan?'),
                hasFirstTaskMention: text.includes('First task: Chemistry Lab Report Writing'),
                hasYesStartWorkingBtn: Array.from(modal.querySelectorAll('button')).some(b => b.innerText.includes('Yes, start working'))
            };
        })()
    """)
    log(f"Scenario 3 Result:\n{json.dumps(s3_res, indent=2)}")
    assert s3_res["isStartWorkingPopup"] is True, "Must transition to 'Start working on your plan?'"
    assert s3_res["hasFirstTaskMention"] is True, "Must display first task in start working popup"
    assert s3_res["hasYesStartWorkingBtn"] is True, "Must have 'Yes, start working →' button"
    log("✓ Scenario 3 passed: Choosing not to break down smoothly transitions to start-working flow.")

    # =========================================================================
    # SCENARIO 4: Steps remain persisted after page reload
    # =========================================================================
    log("\n--- SCENARIO 4: Persistence Across Page Reload ---")
    eval_js(f"""
        (async () => {{
            const persistentPlan = {{
                id: 'plan_persist_steps',
                planType: 'emergency',
                plannedTasks: [
                    {{
                        dayDate: '{today}',
                        startTime: '10:00 AM',
                        task: {{
                            id: 'task_persisted_steps',
                            name: 'Biology Final Project',
                            durationMinutes: 120,
                            completed: false,
                            subtasks: [
                                {{ id: 'sub_bio_1', title: 'Prepare sample slides', durationMinutes: 30, completed: false }},
                                {{ id: 'sub_bio_2', title: 'Record microscope observations', durationMinutes: 45, completed: false }},
                                {{ id: 'sub_bio_3', title: 'Plot graph of cell growth data', durationMinutes: 30, completed: false }},
                                {{ id: 'sub_bio_4', title: 'Draft discussion section', durationMinutes: 15, completed: false }}
                            ]
                        }}
                    }}
                ],
                tasks: []
            }};
            persistentPlan.tasks = persistentPlan.plannedTasks.map(pt => pt.task);
            await window.TempoPlanStore.saveActivePlan('emergency', persistentPlan);
            window.TempoEmergencyFlow.setConfirmedPlan(persistentPlan);
        }})()
    """)

    log("Reloading browser page...")
    send_command("Page.reload")
    wait_for_ready()

    s4_res = eval_js("""
        (async () => {
            window.TempoMode.setMode('emergency');
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const task = plan?.plannedTasks?.[0]?.task;
            const subtasks = task?.subtasks || [];

            return {
                taskName: task?.name,
                subtaskCount: subtasks.length,
                subtaskTitles: subtasks.map(s => s.title),
                subtaskDurations: subtasks.map(s => s.durationMinutes),
                preservedOrder: subtasks[0]?.id === 'sub_bio_1' && subtasks[1]?.id === 'sub_bio_2' && subtasks[2]?.id === 'sub_bio_3' && subtasks[3]?.id === 'sub_bio_4'
            };
        })()
    """)
    log(f"Scenario 4 Result:\n{json.dumps(s4_res, indent=2)}")
    assert s4_res["subtaskCount"] == 4, f"Expected 4 subtasks, got {s4_res['subtaskCount']}"
    assert s4_res["preservedOrder"] is True, "Subtask IDs and ordering must be strictly preserved"
    assert s4_res["subtaskTitles"][0] == "Prepare sample slides", "Subtask titles must match"
    log("✓ Scenario 4 passed: Existing steps remain intact and correctly ordered after reload.")

    # =========================================================================
    # SCENARIO 5: Saving or revisiting flow does not duplicate steps
    # =========================================================================
    log("\n--- SCENARIO 5: Saving or Revisiting Does Not Duplicate Steps ---")
    s5_res = eval_js("""
        (async () => {
            const planBefore = window.TempoPlanStore.getActivePlan('emergency');
            const initialCount = planBefore.plannedTasks[0].task.subtasks.length;

            // Trigger showTaskForNowPopupAfterSave again
            window.TempoUrmodeFlow.showTaskForNowPopupAfterSave(planBefore);
            await new Promise(r => setTimeout(r, 200));

            // Re-save plan
            await window.TempoPlanStore.saveActivePlan('emergency', planBefore);

            // Re-open breakdown popup for this task
            window.TempoUrmodeFlow.renderBreakTaskPopup('task_persisted_steps');
            await new Promise(r => setTimeout(r, 200));

            const planAfter = window.TempoPlanStore.getActivePlan('emergency');
            const finalCount = planAfter.plannedTasks[0].task.subtasks.length;
            const renderedCount = document.querySelectorAll('#breakdown-subtask-list > div').length;

            return {
                initialCount,
                finalCount,
                renderedCount,
                noDuplication: initialCount === finalCount && initialCount === renderedCount
            };
        })()
    """)
    log(f"Scenario 5 Result:\n{json.dumps(s5_res, indent=2)}")
    assert s5_res["noDuplication"] is True, "Subtasks must not duplicate when revisiting or saving"
    log("✓ Scenario 5 passed: Saving or revisiting flow never creates duplicate action steps.")

    # =========================================================================
    # SCENARIO 6: Remaining post-save task flow behaves correctly
    # =========================================================================
    log("\n--- SCENARIO 6: Remaining Post-Save Flow Execution ---")
    s6_res = eval_js("""
        (async () => {
            // From breakdown, click 'Do this task →'
            let focusOpened = false;
            const origFocus = window.TempoFocusZone ? window.TempoFocusZone.open : null;
            if (window.TempoFocusZone) {
                window.TempoFocusZone.open = (args) => { focusOpened = true; };
            }

            // Test showFirstTaskExecutionPopup -> Do this task
            window.TempoUrmodeFlow.showFirstTaskExecutionPopup();
            await new Promise(r => setTimeout(r, 200));

            const modal = document.getElementById('modal-urmode-flow');
            const executionHeading = modal?.querySelector('h2')?.innerText || '';
            const executionCard = modal?.querySelector('.border-2')?.innerText || '';

            // Click 'Do this task →'
            const doTaskBtn = Array.from(modal.querySelectorAll('button')).find(b => b.innerText.includes('Do this task'));
            if (doTaskBtn) {
                await doTaskBtn.click();
            }

            // Restore origFocus
            if (window.TempoFocusZone && origFocus) {
                window.TempoFocusZone.open = origFocus;
            }

            return {
                executionHeading,
                hasTaskInExecutionCard: executionCard.includes('Biology Final Project'),
                hasStepsListed: executionCard.includes('Prepare sample slides'),
                focusTriggered: focusOpened
            };
        })()
    """)
    log(f"Scenario 6 Result:\n{json.dumps(s6_res, indent=2)}")
    assert "Your first task is…" in s6_res["executionHeading"], f"Expected 'Your first task is…', got {s6_res['executionHeading']}"
    assert s6_res["hasTaskInExecutionCard"] is True, "First task card must show task name"
    assert s6_res["hasStepsListed"] is True, "First task card must show action steps"
    assert s6_res["focusTriggered"] is True, "Do this task must successfully launch focus flow"
    log("✓ Scenario 6 passed: Post-save flow behaves correctly through task execution.")

    log("\n=======================================================================")
    log(">>> ALL 6 TASK BREAKDOWN SCENARIOS COMPREHENSIVELY VERIFIED & PASSED! <<<")
    log("=======================================================================")

finally:
    if ws:
        try:
            ws.close()
        except Exception:
            pass
    proc.terminate()
