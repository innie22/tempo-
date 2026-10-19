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

user_data_dir = tempfile.mkdtemp(prefix="tempo_unify_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9260

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

log("Launching Edge on port 9260...")
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
                ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined' && typeof window.TempoEmergencyFlow !== 'undefined'")
                if ready:
                    eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        raise TimeoutError("Application failed to become ready")

    log("Waiting for application ready state...")
    wait_for_ready()

    # Sign in test user and set emergency mode
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

    # Helper date formatting
    now_dates = eval_js("""
        (() => {
            const now = new Date();
            const pad = n => String(n).padStart(2, '0');
            const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
            const pastDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 2);
            const past = `${pastDate.getFullYear()}-${pad(pastDate.getMonth() + 1)}-${pad(pastDate.getDate())}`;
            const tomorrowDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
            const tomorrow = `${tomorrowDate.getFullYear()}-${pad(tomorrowDate.getMonth() + 1)}-${pad(tomorrowDate.getDate())}`;
            return { today, past, tomorrow };
        })()
    """)
    today = now_dates["today"]
    past = now_dates["past"]
    tomorrow = now_dates["tomorrow"]

    # =========================================================================
    # SCENARIO 1: Overdue Task Action ('Mark as done' on overdue card)
    # =========================================================================
    log("\n--- SCENARIO 1: Overdue Task Action ---")
    s1_res = eval_js(f"""
        (async () => {{
            const overduePlan = {{
                id: 'plan_scenario_1',
                planType: 'emergency',
                plannedTasks: [
                    {{
                        dayDate: '{past}',
                        task: {{
                            id: 'task_s1_overdue',
                            name: 'Scenario 1 Overdue Task',
                            completed: false,
                            hasDeadline: true,
                            deadlineDate: '{past}',
                            deadlineTime: '10:00'
                        }}
                    }},
                    {{
                        dayDate: '{today}',
                        task: {{
                            id: 'task_s1_next',
                            name: 'Scenario 1 Next Task',
                            completed: false
                        }}
                    }}
                ],
                tasks: []
            }};
            overduePlan.tasks = overduePlan.plannedTasks.map(p => p.task);
            await window.TempoPlanStore.saveActivePlan('emergency', overduePlan);
            if (window.TempoEmergencyFlow.setConfirmedPlan) {{
                window.TempoEmergencyFlow.setConfirmedPlan(overduePlan);
            }}
            window.TempoMode.renderEmodeHome();

            const cardTitleBefore = document.querySelector('.urgent-card-now h3')?.innerText || '';
            const markDoneBtn = Array.from(document.querySelectorAll('.urgent-card-now button')).find(b => b.innerText.includes('Mark as done'));

            if (!markDoneBtn) throw new Error("Mark as done button not found on overdue card");

            await markDoneBtn.click();
            await new Promise(r => setTimeout(r, 400));

            const planAfter = window.TempoPlanStore.getActivePlan('emergency');
            const flowPlanAfter = window.TempoEmergencyFlow.getConfirmedPlan();
            const taskInStore = planAfter.plannedTasks.find(p => p.task.id === 'task_s1_overdue')?.task;
            const flowCompleted = window.TempoEmergencyFlow.isTaskCompleted('task_s1_overdue');

            const cardTitleAfter = document.querySelector('.urgent-card-now h3')?.innerText || '';
            const cardTextAfter = document.querySelector('.urgent-card-now')?.innerText || '';

            return {{
                cardTitleBefore,
                taskCompletedInStore: taskInStore?.completed === true,
                taskCompletedInFlow: flowCompleted === true,
                cardTitleAfter,
                isAdvancedToNextTask: cardTextAfter.includes('Scenario 1 Next Task'),
                isOverdueCardGone: !cardTextAfter.includes('This task is overdue')
            }};
        }})()
    """)
    log(f"Scenario 1 Result: {json.dumps(s1_res, indent=2)}")
    assert s1_res["taskCompletedInStore"] is True, "Task must be completed in TempoPlanStore"
    assert s1_res["taskCompletedInFlow"] is True, "Task must be completed in TempoEmergencyFlow"
    assert s1_res["isOverdueCardGone"] is True, "Overdue card warning must be gone"
    assert s1_res["isAdvancedToNextTask"] is True, "Card must advance to next eligible task"
    log("✓ Scenario 1 passed: Overdue task successfully completed, persisted, and advanced.")

    # =========================================================================
    # SCENARIO 2: Task Checkbox Action on Active Task
    # =========================================================================
    log("\n--- SCENARIO 2: Task Checkbox Action ---")
    s2_res = eval_js(f"""
        (async () => {{
            const normalPlan = {{
                id: 'plan_scenario_2',
                planType: 'emergency',
                plannedTasks: [
                    {{
                        dayDate: '{today}',
                        task: {{
                            id: 'task_s2_active',
                            name: 'Scenario 2 Active Task',
                            completed: false
                        }}
                    }},
                    {{
                        dayDate: '{today}',
                        task: {{
                            id: 'task_s2_following',
                            name: 'Scenario 2 Following Task',
                            completed: false
                        }}
                    }}
                ],
                tasks: []
            }};
            normalPlan.tasks = normalPlan.plannedTasks.map(p => p.task);
            await window.TempoPlanStore.saveActivePlan('emergency', normalPlan);
            if (window.TempoEmergencyFlow.setConfirmedPlan) {{
                window.TempoEmergencyFlow.setConfirmedPlan(normalPlan);
            }}
            window.TempoMode.renderEmodeHome();

            const checkbox = document.getElementById('task-for-now-checkbox');
            if (!checkbox) throw new Error("Task checkbox not found");

            checkbox.checked = true;
            checkbox.dispatchEvent(new Event('change'));
            await new Promise(r => setTimeout(r, 400));

            const planAfter = window.TempoPlanStore.getActivePlan('emergency');
            const flowCompleted = window.TempoEmergencyFlow.isTaskCompleted('task_s2_active');
            const taskInStore = planAfter.plannedTasks.find(p => p.task.id === 'task_s2_active')?.task;
            const cardTextAfter = document.querySelector('.urgent-card-now')?.innerText || '';

            return {{
                taskCompletedInStore: taskInStore?.completed === true,
                taskCompletedInFlow: flowCompleted === true,
                isAdvancedToFollowing: cardTextAfter.includes('Scenario 2 Following Task'),
                checkboxUncheckedForNewTask: document.getElementById('task-for-now-checkbox')?.checked === false
            }};
        }})()
    """)
    log(f"Scenario 2 Result: {json.dumps(s2_res, indent=2)}")
    assert s2_res["taskCompletedInStore"] is True, "Checkbox action must mark task completed in store"
    assert s2_res["taskCompletedInFlow"] is True, "Checkbox action must mark task completed in flow"
    assert s2_res["isAdvancedToFollowing"] is True, "Card must advance to following task"
    assert s2_res["checkboxUncheckedForNewTask"] is True, "Checkbox for newly displayed task must be unchecked"
    log("✓ Scenario 2 passed: Task checkbox marks task done and advances card cleanly.")

    # =========================================================================
    # SCENARIO 3: Consistency Across Both Actions
    # =========================================================================
    log("\n--- SCENARIO 3: Consistency Across Both Actions ---")
    s3_res = eval_js(f"""
        (async () => {{
            // Compare structure and fields of task marked completed via markOverdueTaskDone vs handleCardTaskComplete
            const dualPlan = {{
                id: 'plan_scenario_3',
                planType: 'emergency',
                plannedTasks: [
                    {{
                        dayDate: '{past}',
                        task: {{
                            id: 'task_s3_overdue',
                            name: 'Overdue Consistency Test',
                            completed: false,
                            in_progress: true,
                            hasDeadline: true,
                            deadlineDate: '{past}',
                            deadlineTime: '11:00'
                        }}
                    }},
                    {{
                        dayDate: '{today}',
                        task: {{
                            id: 'task_s3_normal',
                            name: 'Normal Consistency Test',
                            completed: false,
                            in_progress: true
                        }}
                    }}
                ],
                tasks: []
            }};
            dualPlan.tasks = dualPlan.plannedTasks.map(p => p.task);
            await window.TempoPlanStore.saveActivePlan('emergency', dualPlan);
            if (window.TempoEmergencyFlow.setConfirmedPlan) {{
                window.TempoEmergencyFlow.setConfirmedPlan(dualPlan);
            }}

            // Action A: Mark overdue task done via canonical handler
            await window.TempoMode.markOverdueTaskDone('task_s3_overdue');
            const planA = window.TempoPlanStore.getActivePlan('emergency');
            const taskA = planA.plannedTasks.find(p => p.task.id === 'task_s3_overdue')?.task;

            // Action B: Mark normal task done via canonical handler
            await window.TempoMode.setTaskCompletionStatus('task_s3_normal', true);
            const planB = window.TempoPlanStore.getActivePlan('emergency');
            const taskB = planB.plannedTasks.find(p => p.task.id === 'task_s3_normal')?.task;

            return {{
                taskA_completed: taskA.completed,
                taskA_inProgress: taskA.in_progress,
                taskB_completed: taskB.completed,
                taskB_inProgress: taskB.in_progress,
                sameCompletedType: typeof taskA.completed === typeof taskB.completed,
                identicalCompletedValue: taskA.completed === taskB.completed && taskA.completed === true,
                bothProgressCleared: taskA.in_progress === false && taskB.in_progress === false
            }};
        }})()
    """)
    log(f"Scenario 3 Result: {json.dumps(s3_res, indent=2)}")
    assert s3_res["identicalCompletedValue"] is True, "Both actions must produce identical completed: true"
    assert s3_res["bothProgressCleared"] is True, "Both actions must clear in_progress: false"
    log("✓ Scenario 3 passed: Verified identical completed data structure and persistence semantics.")

    # =========================================================================
    # SCENARIO 4: Card Advancement / Refresh
    # =========================================================================
    log("\n--- SCENARIO 4: Card Advancement / Refresh ---")
    s4_res = eval_js(f"""
        (async () => {{
            const sequencePlan = {{
                id: 'plan_scenario_4',
                planType: 'emergency',
                plannedTasks: [
                    {{ dayDate: '{today}', task: {{ id: 'seq_1', name: 'Step 1 Analysis', completed: false }} }},
                    {{ dayDate: '{today}', task: {{ id: 'seq_2', name: 'Step 2 Design', completed: false }} }},
                    {{ dayDate: '{today}', task: {{ id: 'seq_3', name: 'Step 3 Implement', completed: false }} }}
                ],
                tasks: []
            }};
            sequencePlan.tasks = sequencePlan.plannedTasks.map(p => p.task);
            await window.TempoPlanStore.saveActivePlan('emergency', sequencePlan);
            window.TempoEmergencyFlow.setConfirmedPlan(sequencePlan);
            window.TempoMode.renderEmodeHome();

            const t1 = document.querySelector('.urgent-card-now')?.innerText.includes('Step 1 Analysis');
            await window.TempoMode.setTaskCompletionStatus('seq_1', true);
            const t2 = document.querySelector('.urgent-card-now')?.innerText.includes('Step 2 Design');
            await window.TempoMode.setTaskCompletionStatus('seq_2', true);
            const t3 = document.querySelector('.urgent-card-now')?.innerText.includes('Step 3 Implement');

            return {{ t1, t2, t3 }};
        }})()
    """)
    log(f"Scenario 4 Result: {json.dumps(s4_res, indent=2)}")
    assert s4_res["t1"] and s4_res["t2"] and s4_res["t3"], "Card must advance through all sequential tasks"
    log("✓ Scenario 4 passed: Step-by-step card advancement verified.")

    # =========================================================================
    # SCENARIO 5: Persistence Across Page Reload
    # =========================================================================
    log("\n--- SCENARIO 5: Persistence Across Page Reload ---")
    eval_js(f"""
        (async () => {{
            const persistPlan = {{
                id: 'plan_scenario_5',
                planType: 'emergency',
                plannedTasks: [
                    {{ dayDate: '{today}', task: {{ id: 'persist_task_1', name: 'Task to Persist', completed: false }} }},
                    {{ dayDate: '{today}', task: {{ id: 'persist_task_2', name: 'Remaining Task', completed: false }} }}
                ],
                tasks: []
            }};
            persistPlan.tasks = persistPlan.plannedTasks.map(p => p.task);
            await window.TempoPlanStore.saveActivePlan('emergency', persistPlan);
            window.TempoEmergencyFlow.setConfirmedPlan(persistPlan);
            window.TempoMode.renderEmodeHome();
            await window.TempoMode.setTaskCompletionStatus('persist_task_1', true);
        }})()
    """)
    log("Reloading browser page...")
    send_command("Page.reload")
    wait_for_ready()

    s5_res = eval_js("""
        (async () => {
            window.TempoMode.setMode('emergency');
            window.TempoMode.renderEmodeHome();

            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const t1 = plan?.plannedTasks?.find(p => p.task.id === 'persist_task_1')?.task;
            const flowCompleted = window.TempoEmergencyFlow.isTaskCompleted('persist_task_1');
            const cardText = document.querySelector('.urgent-card-now')?.innerText || '';

            return {
                task1Completed: t1?.completed === true,
                flowCompleted: flowCompleted === true,
                cardShowsRemainingTask: cardText.includes('Remaining Task'),
                cardDoesNotShowCompletedTask: !cardText.includes('Task to Persist')
            };
        })()
    """)
    log(f"Scenario 5 Result: {json.dumps(s5_res, indent=2)}")
    assert s5_res["task1Completed"] is True, "Task must remain completed after page reload"
    assert s5_res["flowCompleted"] is True, "EmergencyFlow must retain completion status after reload"
    assert s5_res["cardShowsRemainingTask"] is True, "UI must display the next unfinished task after reload"
    log("✓ Scenario 5 passed: Persistence across page reload fully verified.")

    # =========================================================================
    # SCENARIO 6: Error Handling and Rollback
    # =========================================================================
    log("\n--- SCENARIO 6: Error Handling and Rollback ---")
    s6_res = eval_js(f"""
        (async () => {{
            const failPlan = {{
                id: 'plan_scenario_6',
                planType: 'emergency',
                plannedTasks: [
                    {{ dayDate: '{today}', task: {{ id: 'fail_task_1', name: 'Rollback Candidate Task', completed: false }} }}
                ],
                tasks: []
            }};
            failPlan.tasks = failPlan.plannedTasks.map(p => p.task);
            await window.TempoPlanStore.saveActivePlan('emergency', failPlan);
            window.TempoEmergencyFlow.setConfirmedPlan(failPlan);
            window.TempoMode.renderEmodeHome();

            // Intercept saveActivePlan to simulate persistence failure
            const originalSave = window.TempoPlanStore.saveActivePlan;
            window.TempoPlanStore.saveActivePlan = async () => {{
                throw new Error("Disk quota exceeded / simulated database write failure");
            }};

            let caughtError = null;
            let resultSuccess = true;
            try {{
                resultSuccess = await window.TempoMode.setTaskCompletionStatus('fail_task_1', true, {{ source: 'test' }});
            }} catch (e) {{
                caughtError = String(e);
            }}

            // Restore original save function
            window.TempoPlanStore.saveActivePlan = originalSave;

            const planAfter = window.TempoPlanStore.getActivePlan('emergency');
            const taskAfter = planAfter?.plannedTasks?.find(p => p.task.id === 'fail_task_1')?.task;
            const flowCompleted = window.TempoEmergencyFlow.isTaskCompleted('fail_task_1');

            // Check toasts to ensure no false success was emitted
            const appToastText = document.getElementById('app-toast')?.textContent || '';
            const otherToasts = Array.from(document.querySelectorAll('.toast, [role="alert"]')).map(el => el.innerText || '');
            const allToastTexts = [appToastText, ...otherToasts];

            const hasFalseSuccess = allToastTexts.some(t => t.includes('Task marked as completed') || t.includes('Overdue task marked as completed'));
            const hasFailureNotification = allToastTexts.some(t => t.includes('Could not update task') || t.includes('Failed to save') || t.includes('Please try again'));

            return {{
                resultSuccess,
                taskAfterCompleted: taskAfter?.completed,
                flowCompleted,
                hasFalseSuccess,
                hasFailureNotification,
                appToastText,
                allToastTexts
            }};
        }})()
    """)
    log(f"Scenario 6 Result: {json.dumps(s6_res, indent=2)}")
    assert s6_res["resultSuccess"] is False, "Operation must return false on persistence failure"
    assert s6_res["taskAfterCompleted"] is False, "Task completed flag must roll back to false"
    assert s6_res["flowCompleted"] is False, "Flow completed flag must roll back to false"
    assert s6_res["hasFalseSuccess"] is False, "No false success toast must be shown"
    assert s6_res["hasFailureNotification"] is True, "Clean failure notification must be displayed to user"
    log("✓ Scenario 6 passed: Rollback safely restored state, no false success toast shown.")

    # =========================================================================
    # SCENARIO 7: Clear Task Distinction (Clearing without marking completed)
    # =========================================================================
    log("\n--- SCENARIO 7: Clear Task Distinction ---")
    s7_res = eval_js(f"""
        (async () => {{
            const clearPlan = {{
                id: 'plan_scenario_7',
                planType: 'emergency',
                plannedTasks: [
                    {{
                        dayDate: '{past}',
                        task: {{
                            id: 'task_to_clear',
                            name: 'Overdue Task to Clear',
                            completed: false,
                            hasDeadline: true,
                            deadlineDate: '{past}',
                            deadlineTime: '08:00'
                        }}
                    }},
                    {{
                        dayDate: '{today}',
                        task: {{
                            id: 'task_to_keep',
                            name: 'Remaining Plan Task',
                            completed: false
                        }}
                    }}
                ],
                tasks: []
            }};
            clearPlan.tasks = clearPlan.plannedTasks.map(p => p.task);
            await window.TempoPlanStore.saveActivePlan('emergency', clearPlan);
            window.TempoEmergencyFlow.setConfirmedPlan(clearPlan);
            window.TempoMode.renderEmodeHome();

            // Call clearOverdueTask
            window.confirm = () => true;
            await window.TempoMode.clearOverdueTask('task_to_clear');

            const planAfter = window.TempoPlanStore.getActivePlan('emergency');
            const clearedFromPlan = !planAfter.plannedTasks.some(p => p.task.id === 'task_to_clear');
            const flowCleared = !window.TempoEmergencyFlow.getConfirmedPlan()?.plannedTasks?.some(p => p.task.id === 'task_to_clear');
            const wasMarkedCompleted = window.TempoEmergencyFlow.isTaskCompleted('task_to_clear');
            const cardText = document.querySelector('.urgent-card-now')?.innerText || '';

            return {{
                clearedFromPlan,
                flowCleared,
                wasMarkedCompleted,
                cardShowsRemainingTask: cardText.includes('Remaining Plan Task')
            }};
        }})()
    """)
    log(f"Scenario 7 Result: {json.dumps(s7_res, indent=2)}")
    assert s7_res["clearedFromPlan"] is True, "Task must be cleared from plan"
    assert s7_res["flowCleared"] is True, "Task must be cleared from flow plan"
    assert s7_res["wasMarkedCompleted"] is False, "Cleared task must NOT be marked as completed"
    assert s7_res["cardShowsRemainingTask"] is True, "Card must refresh to show remaining plan task"
    log("✓ Scenario 7 passed: Clear task removes task without marking it completed.")

    # =========================================================================
    # SCENARIO 8: Completion of Final Task (TODAY_COMPLETE / PLAN_COMPLETE)
    # =========================================================================
    log("\n--- SCENARIO 8: Completion of Final Task ---")
    s8_res = eval_js(f"""
        (async () => {{
            // Part A: TODAY_COMPLETE (today's tasks done, but tomorrow has a task)
            const todayPlan = {{
                id: 'plan_scenario_8a',
                planType: 'emergency',
                plannedTasks: [
                    {{ dayDate: '{today}', task: {{ id: 'today_last', name: 'Last Today Task', completed: false }} }},
                    {{ dayDate: '{tomorrow}', task: {{ id: 'tomorrow_task', name: 'Future Task', completed: false }} }}
                ],
                tasks: []
            }};
            todayPlan.tasks = todayPlan.plannedTasks.map(p => p.task);
            await window.TempoPlanStore.saveActivePlan('emergency', todayPlan);
            window.TempoEmergencyFlow.setConfirmedPlan(todayPlan);
            window.TempoMode.renderEmodeHome();

            await window.TempoMode.setTaskCompletionStatus('today_last', true);
            const stateTodayComplete = window.TempoMode.getActiveHomeState();
            const cardTodayComplete = document.querySelector('.urgent-card-now')?.innerText || '';

            // Part B: PLAN_COMPLETE (all tasks across entire plan done)
            await window.TempoMode.setTaskCompletionStatus('tomorrow_task', true);
            const statePlanComplete = window.TempoMode.getActiveHomeState();
            const cardPlanComplete = document.querySelector('.urgent-card-now')?.innerText || '';

            return {{
                stateTodayComplete,
                cardTodayCompleteHasCheckmark: cardTodayComplete.includes("You're all done for today") || cardTodayComplete.includes("TODAY'S WORK DONE") || cardTodayComplete.includes("through today's tasks"),
                statePlanComplete,
                cardPlanCompleteHasDone: cardPlanComplete.includes('ĐÃ XONG') || cardPlanComplete.includes('You did it') || cardPlanComplete.includes('Your Urgent Plan is complete')
            }};
        }})()
    """)
    log(f"Scenario 8 Result: {json.dumps(s8_res, indent=2)}")
    assert s8_res["stateTodayComplete"] == "TODAY_COMPLETE", "State must transition to TODAY_COMPLETE"
    assert s8_res["statePlanComplete"] == "PLAN_COMPLETE", "State must transition to PLAN_COMPLETE"
    assert s8_res["cardPlanCompleteHasDone"] is True, "Card must render completion celebration"
    log("✓ Scenario 8 passed: Clean transition to TODAY_COMPLETE and PLAN_COMPLETE verified.")

    # =========================================================================
    # SCENARIO 9: Concurrency / Rapid Clicks
    # =========================================================================
    log("\n--- SCENARIO 9: Concurrency / Rapid Repeated Clicks ---")
    s9_res = eval_js(f"""
        (async () => {{
            const rapidPlan = {{
                id: 'plan_scenario_9',
                planType: 'emergency',
                plannedTasks: [
                    {{ dayDate: '{today}', task: {{ id: 'rapid_task', name: 'Rapid Click Task', completed: false }} }}
                ],
                tasks: []
            }};
            rapidPlan.tasks = rapidPlan.plannedTasks.map(p => p.task);
            await window.TempoPlanStore.saveActivePlan('emergency', rapidPlan);
            window.TempoEmergencyFlow.setConfirmedPlan(rapidPlan);
            window.TempoMode.renderEmodeHome();

            // Simulate 5 rapid simultaneous clicks/invocations
            const promises = [
                window.TempoMode.setTaskCompletionStatus('rapid_task', true),
                window.TempoMode.setTaskCompletionStatus('rapid_task', true),
                window.TempoMode.setTaskCompletionStatus('rapid_task', true),
                window.TempoMode.setTaskCompletionStatus('rapid_task', true),
                window.TempoMode.setTaskCompletionStatus('rapid_task', true)
            ];

            const results = await Promise.all(promises);
            const planAfter = window.TempoPlanStore.getActivePlan('emergency');
            const task = planAfter.plannedTasks[0].task;

            return {{
                results,
                taskCompleted: task.completed,
                noCorruption: typeof task.completed === 'boolean'
            }};
        }})()
    """)
    log(f"Scenario 9 Result: {json.dumps(s9_res, indent=2)}")
    assert s9_res["taskCompleted"] is True, "Task must end up completed"
    assert s9_res["noCorruption"] is True, "Task state must remain valid boolean without corruption"
    log("✓ Scenario 9 passed: Concurrency and rapid clicks safely handled.")

    log("\n=======================================================================")
    log(">>> ALL 9 TASK COMPLETION SCENARIOS COMPREHENSIVELY VERIFIED & PASSED! <<<")
    log("=======================================================================")

finally:
    if ws:
        try:
            ws.close()
        except Exception:
            pass
    proc.terminate()
