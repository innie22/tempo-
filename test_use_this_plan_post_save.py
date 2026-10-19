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

user_data_dir = tempfile.mkdtemp(prefix="tempo_use_plan_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9270

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

log("Launching Edge on port 9270...")
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
    # SEQUENCE 1: Working Plan Setup -> Click "Use this plan" -> Task without steps
    # =========================================================================
    log("\n--- SEQUENCE 1: Setup Flow -> Click 'Use this plan' (Task without steps) ---")
    s1_res = eval_js(f"""
        (async () => {{
            window.TempoEmergencyFlow.startFreshPlan();
            window.TempoApp.navigateTo('emergency');

            // Setup a fresh plan with 1 task (no subtasks)
            const planDraft = {{
                id: 'plan_seq1',
                planType: 'emergency',
                plannedTasks: [
                    {{
                        dayDate: '{today}',
                        dayLabel: 'Today',
                        startTime: '10:00 AM',
                        endTime: '11:00 AM',
                        executionBadge: 'UP NEXT',
                        task: {{
                            id: 'task_physics_final',
                            name: 'Physics Final Problem Set',
                            durationMinutes: 60,
                            completed: false,
                            subtasks: []
                        }}
                    }}
                ],
                unallocatedTasks: [],
                unarrangedTasks: [],
                tasks: [],
                availabilityDays: [{{ date: '{today}', label: 'Today', blocks: [{{ start: '09:00', end: '18:00' }}] }}]
            }};
            planDraft.tasks = planDraft.plannedTasks.map(p => p.task);

            window.TempoEmergencyFlow.setConfirmedPlan(planDraft);
            window.TempoEmergencyFlow.goToStage('plan-review');

            await new Promise(r => setTimeout(r, 200));

            // Verify 'Use this plan' button is present
            const usePlanBtn = document.getElementById('btn-em-use-plan');
            if (!usePlanBtn) throw new Error("'Use this plan' button not found in plan-review");

            const btnTextBefore = usePlanBtn.innerText.trim();

            // Click 'Use this plan'
            await usePlanBtn.click();
            await new Promise(r => setTimeout(r, 300));

            // Check if plan is saved in store
            const activePlan = window.TempoPlanStore.getActivePlan('emergency');
            const isPlanSaved = !!activePlan && activePlan.plannedTasks?.[0]?.task?.id === 'task_physics_final';

            // Check if breakdown screen is shown
            const emBreakdownStage = document.getElementById('emergency-stage-breakdown');
            const isBreakdownStageVisible = emBreakdownStage && !emBreakdownStage.classList.contains('hidden');

            // Check 'Your task for now' modal
            const modal = document.getElementById('modal-urmode-flow');
            const isModalVisible = modal && !modal.classList.contains('hidden');
            const modalEyebrow = modal?.querySelector('span.text-xs.font-extrabold')?.innerText || '';
            const modalHeading = modal?.querySelector('h2')?.innerText || '';
            const modalText = modal?.innerText || '';
            const buttons = Array.from(modal?.querySelectorAll('button') || []).map(b => b.innerText.trim());

            return {{
                btnTextBefore,
                isPlanSaved,
                isBreakdownStageVisible,
                isModalVisible,
                modalEyebrow,
                modalHeading,
                hasTaskName: modalText.includes('Physics Final Problem Set'),
                hasBreakdownQuestion: modalText.includes('Would you like to break down this task into smaller steps?'),
                hasBreakTaskBtn: buttons.some(b => b.includes('Break down task')),
                hasNoStartWorkingBtn: buttons.some(b => b.includes('No, start working')),
                buttons
            }};
        }})()
    """)
    log(f"Sequence 1 Result:\n{json.dumps(s1_res, indent=2)}")
    assert "Use this plan" in s1_res["btnTextBefore"], "Button must be 'Use this plan'"
    assert s1_res["isPlanSaved"] is True, "Plan must be successfully saved in TempoPlanStore"
    assert s1_res["isBreakdownStageVisible"] is False, "Breakdown stage MUST NOT be visible after clicking 'Use this plan'"
    assert s1_res["isModalVisible"] is True, "'Your task for now' popup must appear"
    assert "PLAN CONFIRMED & SAVED" in s1_res["modalEyebrow"], "Eyebrow must be 'PLAN CONFIRMED & SAVED'"
    assert "Your task for now" in s1_res["modalHeading"], "Heading must be 'Your task for now'"
    assert s1_res["hasTaskName"] is True, "Must display the task name in highlight card"
    assert s1_res["hasBreakdownQuestion"] is True, "Must ask 'Would you like to break down this task into smaller steps?'"
    assert s1_res["hasBreakTaskBtn"] is True, "Must offer 'Break down task →' choice"
    assert s1_res["hasNoStartWorkingBtn"] is True, "Must offer 'No, start working' choice"
    log("✓ Sequence 1 passed: Clicking 'Use this plan' saves the plan and displays the choice popup first without opening breakdown.")

    # =========================================================================
    # SEQUENCE 1 Part 2: User explicitly chooses "Break down task →"
    # =========================================================================
    log("\n--- SEQUENCE 1 (Part 2): Click 'Break down task →' explicitly ---")
    s1_part2 = eval_js("""
        (async () => {
            const modal = document.getElementById('modal-urmode-flow');
            const breakBtn = Array.from(modal.querySelectorAll('button')).find(b => b.innerText.includes('Break down task'));
            if (!breakBtn) throw new Error("'Break down task →' button not found");

            await breakBtn.click();
            await new Promise(r => setTimeout(r, 200));

            const heading = modal?.querySelector('h2')?.innerText || '';
            const subtaskList = document.getElementById('breakdown-subtask-list');

            // Add an action step
            const input = document.getElementById('breakdown-subtask-input');
            input.value = 'Derive formula for kinetic energy (15 min)';
            window.TempoUrmodeFlow.addSubtask('task_physics_final');
            await new Promise(r => setTimeout(r, 200));

            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const subtasks = plan.plannedTasks[0].task.subtasks;

            return {
                heading,
                isBreakdownPopup: heading.includes('Break down: Physics Final Problem Set'),
                subtaskCount: subtasks.length,
                subtaskTitle: subtasks[0]?.title
            };
        })()
    """)
    log(f"Sequence 1 Part 2 Result:\n{json.dumps(s1_part2, indent=2)}")
    assert s1_part2["isBreakdownPopup"] is True, "Breakdown editor must open upon explicit user choice"
    assert s1_part2["subtaskCount"] == 1, "Added step must be saved"
    assert s1_part2["subtaskTitle"] == "Derive formula for kinetic energy (15 min)", "Step title must match"
    log("✓ Sequence 1 Part 2 passed: Breakdown editor opened ONLY upon explicit user choice, and action steps added correctly.")

    # =========================================================================
    # SEQUENCE 2: Working Plan with existing action steps -> Click "Use this plan"
    # =========================================================================
    log("\n--- SEQUENCE 2: Setup Flow with Existing Steps -> 'Use this plan' ---")
    s2_res = eval_js(f"""
        (async () => {{
            window.TempoEmergencyFlow.startFreshPlan();
            window.TempoApp.navigateTo('emergency');

            const planWithSteps = {{
                id: 'plan_seq2_existing_steps',
                planType: 'emergency',
                plannedTasks: [
                    {{
                        dayDate: '{today}',
                        dayLabel: 'Today',
                        startTime: '02:00 PM',
                        endTime: '03:30 PM',
                        executionBadge: 'UP NEXT',
                        task: {{
                            id: 'task_english_thesis',
                            name: 'English Thesis Essay',
                            durationMinutes: 90,
                            completed: false,
                            subtasks: [
                                {{ id: 'sub_en_1', title: 'Outline primary arguments', durationMinutes: 30, completed: false }},
                                {{ id: 'sub_en_2', title: 'Draft introduction paragraph', durationMinutes: 30, completed: false }}
                            ]
                        }}
                    }}
                ],
                unallocatedTasks: [],
                unarrangedTasks: [],
                tasks: [],
                availabilityDays: [{{ date: '{today}', label: 'Today', blocks: [{{ start: '09:00', end: '18:00' }}] }}]
            }};
            planWithSteps.tasks = planWithSteps.plannedTasks.map(p => p.task);

            window.TempoEmergencyFlow.setConfirmedPlan(planWithSteps);
            window.TempoEmergencyFlow.goToStage('plan-review');

            await new Promise(r => setTimeout(r, 200));

            const usePlanBtn = document.getElementById('btn-em-use-plan');
            if (!usePlanBtn) throw new Error("'Use this plan' button not found");

            await usePlanBtn.click();
            await new Promise(r => setTimeout(r, 300));

            const modal = document.getElementById('modal-urmode-flow');
            const isModalVisible = modal && !modal.classList.contains('hidden');
            const modalText = modal?.innerText || '';
            const cardText = modal?.querySelector('.border-2')?.innerText || '';
            const buttons = Array.from(modal?.querySelectorAll('button') || []).map(b => b.innerText.trim());

            return {{
                isModalVisible,
                hasTaskName: cardText.includes('English Thesis Essay'),
                hasStep1: cardText.includes('Outline primary arguments'),
                hasStep2: cardText.includes('Draft introduction paragraph'),
                hasBreakdownQuestion: modalText.includes('Would you like to break down this task into smaller steps?'),
                hasBreakTaskBtn: buttons.some(b => b.includes('Break down task')),
                hasNoStartWorkingBtn: buttons.some(b => b.includes('No, start working')),
                buttons
            }};
        }})()
    """)
    log(f"Sequence 2 Result:\n{json.dumps(s2_res, indent=2)}")
    assert s2_res["isModalVisible"] is True, "Modal must be visible after 'Use this plan'"
    assert s2_res["hasTaskName"] is True, "Task name must be shown in highlight card"
    assert s2_res["hasStep1"] and s2_res["hasStep2"], "Existing steps must be displayed in highlight card"
    assert s2_res["hasBreakdownQuestion"] is True, "Must explicitly ask breakdown question even if steps already exist"
    assert s2_res["hasBreakTaskBtn"] is True, "Must offer 'Break down task →'"
    assert s2_res["hasNoStartWorkingBtn"] is True, "Must offer 'No, start working'"
    log("✓ Sequence 2 passed: Task with existing steps preserves steps in highlight card and presents explicit choice.")

    # =========================================================================
    # SEQUENCE 2 Part 2: Choose "No, start working" -> Opens Start Working WITHOUT breakdown
    # =========================================================================
    log("\n--- SEQUENCE 2 (Part 2): Click 'No, start working' ---")
    s2_part2 = eval_js("""
        (async () => {
            const modal = document.getElementById('modal-urmode-flow');
            const noBtn = Array.from(modal.querySelectorAll('button')).find(b => b.innerText.includes('No, start working'));
            if (!noBtn) throw new Error("'No, start working' button not found");

            await noBtn.click();
            await new Promise(r => setTimeout(r, 200));

            const heading = modal?.querySelector('h2')?.innerText || '';
            const text = modal?.innerText || '';
            const buttons = Array.from(modal.querySelectorAll('button')).map(b => b.innerText.trim());

            // Check that breakdown was never entered
            const hasBreakdownList = !!document.getElementById('breakdown-subtask-list');

            return {
                heading,
                isStartWorking: heading.includes('Start working on your plan?'),
                hasBreakdownList,
                hasYesStartWorkingBtn: buttons.some(b => b.includes('Yes, start working'))
            };
        })()
    """)
    log(f"Sequence 2 Part 2 Result:\n{json.dumps(s2_part2, indent=2)}")
    assert s2_part2["isStartWorking"] is True, "Must open 'Start working on your plan?'"
    assert s2_part2["hasBreakdownList"] is False, "Breakdown list must NOT be rendered when choosing 'No, start working'"
    assert s2_part2["hasYesStartWorkingBtn"] is True, "Must offer 'Yes, start working →' button"
    log("✓ Sequence 2 Part 2 passed: 'No, start working' transitioned directly to Start Working without entering breakdown.")

    # =========================================================================
    # SEQUENCE 3: Reopen Breakdown Flow with Existing Steps -> Safely Preserved
    # =========================================================================
    log("\n--- SEQUENCE 3: Reopen Breakdown Flow -> Verify Steps Preserved and Editable ---")
    s3_res = eval_js("""
        (async () => {
            // Reopen task for now popup
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            window.TempoUrmodeFlow.showTaskForNowPopupAfterSave(plan);
            await new Promise(r => setTimeout(r, 200));

            const modal = document.getElementById('modal-urmode-flow');
            const breakBtn = Array.from(modal.querySelectorAll('button')).find(b => b.innerText.includes('Break down task'));
            await breakBtn.click();
            await new Promise(r => setTimeout(r, 200));

            const subtaskList = document.getElementById('breakdown-subtask-list');
            const stepItems = Array.from(subtaskList?.children || []).map(el => el.innerText.trim());

            const planInStore = window.TempoPlanStore.getActivePlan('emergency');
            const subtasks = planInStore.plannedTasks[0].task.subtasks;

            return {
                renderedStepCount: stepItems.length,
                renderedMatches: stepItems.some(t => t.includes('Outline primary arguments')) &&
                                 stepItems.some(t => t.includes('Draft introduction paragraph')),
                subtasksInStoreCount: subtasks.length,
                originalIdsPreserved: subtasks[0].id === 'sub_en_1' && subtasks[1].id === 'sub_en_2',
                noDuplicates: subtasks.length === 2
            };
        })()
    """)
    log(f"Sequence 3 Result:\n{json.dumps(s3_res, indent=2)}")
    assert s3_res["renderedStepCount"] == 2, f"Expected 2 rendered steps, got {s3_res['renderedStepCount']}"
    assert s3_res["renderedMatches"] is True, "Rendered steps must match existing titles"
    assert s3_res["originalIdsPreserved"] is True, "Original subtask IDs must remain intact"
    assert s3_res["noDuplicates"] is True, "Existing steps must not be duplicated"
    log("✓ Sequence 3 passed: Reopening breakdown flow safely preserved existing steps without duplication or ID changes.")

    # =========================================================================
    # SEQUENCE 4: End-to-End Working Plan Setup -> "Use this plan" -> X close
    # =========================================================================
    log("\n--- SEQUENCE 4: Complete Working Plan Setup End-to-End ---")
    s4_res = eval_js(f"""
        (async () => {{
            window.TempoEmergencyFlow.startFreshPlan();
            window.TempoApp.navigateTo('emergency');

            const fullPlan = {{
                id: 'full_setup_capstone_plan',
                planType: 'emergency',
                plannedTasks: [
                    {{
                        dayDate: '{today}',
                        dayLabel: 'Today',
                        startTime: '09:00 AM',
                        endTime: '10:30 AM',
                        executionBadge: 'UP NEXT',
                        task: {{
                            id: 'task_capstone_1',
                            name: 'Full Setup Capstone Presentation',
                            durationMinutes: 90,
                            completed: false,
                            subtasks: []
                        }}
                    }},
                    {{
                        dayDate: '{today}',
                        dayLabel: 'Today',
                        startTime: '11:00 AM',
                        endTime: '12:00 PM',
                        executionBadge: 'THEN',
                        task: {{
                            id: 'task_capstone_2',
                            name: 'Chemistry Problem Set 4',
                            durationMinutes: 60,
                            completed: false,
                            subtasks: []
                        }}
                    }}
                ],
                unallocatedTasks: [],
                unarrangedTasks: [],
                tasks: [],
                availabilityDays: [{{ date: '{today}', label: 'Today', blocks: [{{ start: '09:00', end: '18:00' }}] }}]
            }};
            fullPlan.tasks = fullPlan.plannedTasks.map(p => p.task);
            window.TempoEmergencyFlow.setConfirmedPlan(fullPlan);
            window.TempoEmergencyFlow.goToStage('plan-review');
            await new Promise(r => setTimeout(r, 200));

            // We should now be in plan-review
            const currentStage = window.TempoEmergencyFlow.getCurrentStage();
            const usePlanBtn = document.getElementById('btn-em-use-plan');
            if (!usePlanBtn) throw new Error("'Use this plan' button not found at end of setup");

            // Click 'Use this plan'
            await usePlanBtn.click();
            await new Promise(r => setTimeout(r, 300));

            // Check post-save state
            const planInStore = window.TempoPlanStore.getActivePlan('emergency');
            const emBreakdownStage = document.getElementById('emergency-stage-breakdown');
            const isBreakdownStageVisible = emBreakdownStage && !emBreakdownStage.classList.contains('hidden');

            const modal = document.getElementById('modal-urmode-flow');
            const isModalVisible = modal && !modal.classList.contains('hidden');
            const modalText = modal?.innerText || '';
            const buttons = Array.from(modal?.querySelectorAll('button') || []).map(b => b.innerText.trim());

            // Test X close button
            const closeBtn = modal?.querySelector('button[aria-label="Close dialog"]');
            if (closeBtn) await closeBtn.click();
            await new Promise(r => setTimeout(r, 200));

            const isModalClosed = modal ? modal.classList.contains('hidden') : true;

            return {{
                currentStage,
                isPlanSaved: !!planInStore,
                isBreakdownStageVisible,
                isModalVisible,
                hasTaskName: modalText.includes('Full Setup Capstone'),
                hasBreakdownQuestion: modalText.includes('Would you like to break down this task into smaller steps?'),
                hasBreakTaskBtn: buttons.some(b => b.includes('Break down task')),
                hasNoStartWorkingBtn: buttons.some(b => b.includes('No, start working')),
                isModalClosed
            }};
        }})()
    """)
    log(f"Sequence 4 Result:\n{json.dumps(s4_res, indent=2)}")
    assert s4_res["currentStage"] == "plan-review", f"Must reach plan-review, got {s4_res['currentStage']}"
    assert s4_res["isPlanSaved"] is True, "Plan must be saved in store upon clicking 'Use this plan'"
    assert s4_res["isBreakdownStageVisible"] is False, "Breakdown stage MUST NOT open automatically"
    assert s4_res["isModalVisible"] is True, "'Your task for now' popup must appear first"
    assert s4_res["hasBreakdownQuestion"] is True, "Must ask breakdown question"
    assert s4_res["hasBreakTaskBtn"] is True, "Must offer 'Break down task →'"
    assert s4_res["hasNoStartWorkingBtn"] is True, "Must offer 'No, start working'"
    assert s4_res["isModalClosed"] is True, "Clicking X must close the popup and return to dashboard"
    log("✓ Sequence 4 passed: Complete end-to-end setup flow verified through 'Use this plan' to X close.")

    log("\n=======================================================================")
    log(">>> ALL 'USE THIS PLAN' POST-SAVE FLOW TESTS COMPREHENSIVELY PASSED! <<<")
    log("=======================================================================")

finally:
    if ws:
        try:
            ws.close()
        except Exception:
            pass
    proc.terminate()
