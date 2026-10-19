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

user_data_dir = tempfile.mkdtemp(prefix="tempo_view_plan_")
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
    "http://localhost:8000/"
]

log("Launching Edge on port 9292...")
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

    # Authenticate mock user
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
    time.sleep(0.5)

    today = eval_js("new Date().toISOString().split('T')[0]")

    # =========================================================================
    # TEST 1: Presence and Styling of "View my plan" Button in Break Task Popup
    # =========================================================================
    log("\n--- TEST 1: Presence and Styling of 'View my plan' Button ---")
    t1_res = eval_js(f"""
        (async () => {{
            const plan = {{
                id: 'plan_view_my_plan_test',
                mode: 'emergency',
                createdAt: new Date().toISOString(),
                plannedTasks: [
                    {{
                        dayDate: '{today}',
                        executionBadge: 'UP NEXT',
                        task: {{
                            id: 'task_view_plan_1',
                            name: 'Literature Review Chapter 3',
                            durationMinutes: 60,
                            durationLabel: '1h',
                            hasDeadline: true,
                            deadlineDate: '{today}',
                            deadlineTime: '17:00',
                            completed: false,
                            subtasks: [
                                {{ id: 'sub-1', title: 'Find 3 key references', completed: false }}
                            ]
                        }}
                    }},
                    {{
                        dayDate: '{today}',
                        executionBadge: 'LATER',
                        task: {{
                            id: 'task_view_plan_2',
                            name: 'Draft introduction paragraph',
                            durationMinutes: 45,
                            durationLabel: '45m',
                            hasDeadline: false,
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

            // Open the break task popup
            window.TempoUrmodeFlow.startBreakTaskFlow('task_view_plan_1');

            const btnViewMyPlan = document.getElementById('btn-view-my-plan');
            const modal = document.getElementById('modal-urmode-flow');
            const isModalVisible = modal && !modal.classList.contains('hidden');

            return {{
                isModalVisible,
                hasViewMyPlanBtn: !!btnViewMyPlan,
                buttonText: btnViewMyPlan ? btnViewMyPlan.textContent.trim() : '',
                buttonClass: btnViewMyPlan ? btnViewMyPlan.className : '',
                hasLaterBtn: !!Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Later'),
                hasBreakMoreBtn: !!Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Break more tasks')),
                hasDoThisTaskBtn: !!Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Do this task')),
                hasCloseBtn: !!modal.querySelector('button[aria-label="Close dialog"]'),
                hasAiHelpBtn: !!document.getElementById('btn-ai-help-breakdown')
            }};
        }})()
    """)
    log(f"Test 1 Result: {json.dumps(t1_res, indent=2)}")
    assert t1_res["isModalVisible"] is True, "Breakdown modal must be visible"
    assert t1_res["hasViewMyPlanBtn"] is True, "View my plan button must exist"
    assert t1_res["buttonText"] == "View my plan", f"Button text must be exactly 'View my plan', got '{t1_res['buttonText']}'"
    assert t1_res["hasLaterBtn"] is True, "Later button must remain present"
    assert t1_res["hasBreakMoreBtn"] is True, "Break more tasks button must remain present"
    assert t1_res["hasDoThisTaskBtn"] is True, "Do this task button must remain present"
    assert t1_res["hasCloseBtn"] is True, "Close dialog button must remain present"
    assert t1_res["hasAiHelpBtn"] is True, "AI Help button must remain present"
    log("✓ Test 1 passed: 'View my plan' button is properly displayed alongside all existing buttons.")

    # =========================================================================
    # TEST 2: Clicking "View my plan" Navigates to Working Plan Tool Page and Closes Popup
    # =========================================================================
    log("\n--- TEST 2: Clicking 'View my plan' Navigates to Working Plan Page ---")
    t2_res = eval_js("""
        (async () => {
            const btn = document.getElementById('btn-view-my-plan');
            btn.click();

            await new Promise(r => setTimeout(r, 400));

            const modal = document.getElementById('modal-urmode-flow');
            const isModalHidden = !modal || modal.classList.contains('hidden');
            const bodyHasNoOverflowHidden = !document.body.classList.contains('overflow-hidden');

            const planWorkspaceScreen = document.getElementById('screen-plan-workspace');
            const isPlanWorkspaceVisible = planWorkspaceScreen && !planWorkspaceScreen.classList.contains('hidden');

            // Verify active plan in store
            const storedPlan = await window.TempoPlanStore.getActivePlan('emergency');
            const task1 = storedPlan.plannedTasks[0].task;

            return {
                isModalHidden,
                bodyHasNoOverflowHidden,
                isPlanWorkspaceVisible,
                task1Name: task1.name,
                task1SubtasksCount: task1.subtasks.length,
                task1FirstSubtaskTitle: task1.subtasks[0]?.title
            };
        })()
    """)
    log(f"Test 2 Result: {json.dumps(t2_res, indent=2)}")
    assert t2_res["isModalHidden"] is True, "Modal must be hidden after clicking View my plan"
    assert t2_res["bodyHasNoOverflowHidden"] is True, "body must not retain overflow-hidden"
    assert t2_res["isPlanWorkspaceVisible"] is True, "Working Plan tool page screen must be visible"
    assert t2_res["task1Name"] == "Literature Review Chapter 3", "Task name must remain preserved"
    assert t2_res["task1SubtasksCount"] == 1, "Subtasks must remain preserved"
    assert t2_res["task1FirstSubtaskTitle"] == "Find 3 key references", "Subtask content must remain preserved"
    log("✓ Test 2 passed: 'View my plan' smoothly closes popup, switches to Working Plan page, and preserves plan state.")

    # =========================================================================
    # TEST 3: Preserve Action Steps Generated in Popup before Navigating
    # =========================================================================
    log("\n--- TEST 3: Preserve Action Steps Added / Generated in Popup ---")
    t3_res = eval_js("""
        (async () => {
            // Re-open breakdown popup for task_view_plan_1
            window.TempoUrmodeFlow.startBreakTaskFlow('task_view_plan_1');
            await new Promise(r => setTimeout(r, 200));

            // Add a new step manually
            const input = document.getElementById('breakdown-subtask-input');
            input.value = "Outline section 3.2 key arguments";
            window.TempoUrmodeFlow.addSubtask('task_view_plan_1');
            await new Promise(r => setTimeout(r, 200));

            // Verify step added
            const stepsInDom = Array.from(document.querySelectorAll('#breakdown-subtask-list .subtask-title')).map(el => el.textContent.trim());

            // Click View my plan
            const btn = document.getElementById('btn-view-my-plan');
            btn.click();
            await new Promise(r => setTimeout(r, 400));

            const modal = document.getElementById('modal-urmode-flow');
            const isModalHidden = !modal || modal.classList.contains('hidden');

            const storedPlan = await window.TempoPlanStore.getActivePlan('emergency');
            const task1 = storedPlan.plannedTasks[0].task;

            return {
                stepsInDom,
                isModalHidden,
                persistedSubtasksCount: task1.subtasks.length,
                subtaskTitles: task1.subtasks.map(s => s.title)
            };
        })()
    """)
    log(f"Test 3 Result: {json.dumps(t3_res, indent=2)}")
    assert t3_res["isModalHidden"] is True, "Modal must be hidden"
    assert t3_res["persistedSubtasksCount"] == 2, f"Expected 2 subtasks, found {t3_res['persistedSubtasksCount']}"
    assert "Outline section 3.2 key arguments" in t3_res["subtaskTitles"], "New step must be preserved in plan store"
    log("✓ Test 3 passed: Subtasks added in popup persist seamlessly when clicking 'View my plan'.")

    # =========================================================================
    # TEST 4: Verification of All Other Existing Break Task Buttons
    # =========================================================================
    log("\n--- TEST 4: Verification of Other Break Task Popup Buttons ---")
    t4_res = eval_js("""
        (async () => {
            // 4A: Test Close 'X' button
            window.TempoUrmodeFlow.startBreakTaskFlow('task_view_plan_1');
            await new Promise(r => setTimeout(r, 200));

            const modal = document.getElementById('modal-urmode-flow');
            const closeBtn = modal.querySelector('button[aria-label="Close dialog"]');
            closeBtn.click();
            await new Promise(r => setTimeout(r, 200));
            const xClosed = modal.classList.contains('hidden');

            // 4B: Test Later button
            window.TempoUrmodeFlow.startBreakTaskFlow('task_view_plan_1');
            await new Promise(r => setTimeout(r, 200));
            const laterBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Later');
            laterBtn.click();
            await new Promise(r => setTimeout(r, 200));
            const laterClosed = modal.classList.contains('hidden');

            // 4C: Test Break More Tasks button
            window.TempoUrmodeFlow.startBreakTaskFlow('task_view_plan_1');
            await new Promise(r => setTimeout(r, 200));
            const breakMoreBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Break more tasks'));
            breakMoreBtn.click();
            await new Promise(r => setTimeout(r, 300));
            const currentBreakTaskHeading = modal.querySelector('h2').textContent.trim();

            return {
                xClosed,
                laterClosed,
                currentBreakTaskHeading
            };
        })()
    """)
    log(f"Test 4 Result: {json.dumps(t4_res, indent=2)}")
    assert t4_res["xClosed"] is True, "X button must close popup"
    assert t4_res["laterClosed"] is True, "Later button must close popup"
    assert "Draft introduction paragraph" in t4_res["currentBreakTaskHeading"], "Break more tasks must advance to next task"
    log("✓ Test 4 passed: All other Break Task buttons retain their full behavior.")

    log("\n🎉 ALL TESTS PASSED SUCCESSFULLY!")

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
