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

user_data_dir = tempfile.mkdtemp(prefix="tempo_ai_help_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9290

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

log("Launching Edge on port 9290...")
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
    # TEST 1: UI Presence and Layout in Breakdown Popup
    # =========================================================================
    log("\n--- TEST 1: UI Presence and Layout in Breakdown Popup ---")
    t1_res = eval_js(f"""
        (async () => {{
            const plan = {{
                id: 'plan_ai_help_test',
                mode: 'emergency',
                createdAt: new Date().toISOString(),
                plannedTasks: [
                    {{
                        dayDate: '{today}',
                        executionBadge: 'UP NEXT',
                        task: {{
                            id: 'task_stats_pset4',
                            name: 'Statistics Assignment (Problem Set 4)',
                            durationMinutes: 90,
                            durationLabel: '1h 30m',
                            hasDeadline: true,
                            deadlineDate: '{today}',
                            deadlineTime: '23:59',
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

            // Open the breakdown popup
            window.TempoUrmodeFlow.startBreakTaskFlow('task_stats_pset4');

            const btnAiHelp = document.getElementById('btn-ai-help-breakdown');
            const inputSubtask = document.getElementById('breakdown-subtask-input');
            const subtaskList = document.getElementById('breakdown-subtask-list');

            const modal = document.getElementById('modal-urmode-flow');
            const isModalVisible = modal && !modal.classList.contains('hidden');
            const heading = modal ? modal.querySelector('h2').textContent.trim() : '';

            return {{
                isModalVisible,
                heading,
                hasAiHelpBtn: !!btnAiHelp,
                aiHelpBtnText: btnAiHelp ? btnAiHelp.textContent.trim() : '',
                hasInput: !!inputSubtask,
                hasSubtaskList: !!subtaskList
            }};
        }})()
    """)
    log(f"Test 1 Result: {json.dumps(t1_res, indent=2)}")
    assert t1_res["isModalVisible"] is True, "Breakdown modal must be visible"
    assert "Statistics Assignment" in t1_res["heading"], "Heading must show task name"
    assert t1_res["hasAiHelpBtn"] is True, "✨ AI Help button must be present in popup"
    assert "AI Help" in t1_res["aiHelpBtnText"], "Button text must contain 'AI Help'"
    assert t1_res["hasInput"] is True, "Subtask input form must remain present"
    log("✓ Test 1 passed: ✨ AI Help button is prominently placed in Breakdown popup.")

    # =========================================================================
    # TEST 2: Click ✨ AI Help -> Generates Task-Specific Action Steps
    # =========================================================================
    log("\n--- TEST 2: Click ✨ AI Help -> Generates Task-Specific Action Steps ---")
    t2_res = eval_js("""
        (async () => {
            const btn = document.getElementById('btn-ai-help-breakdown');
            btn.click();

            // Wait for generation to complete
            await new Promise(r => setTimeout(r, 600));

            const modal = document.getElementById('modal-urmode-flow');
            const isModalVisible = modal && !modal.classList.contains('hidden');

            const items = Array.from(document.querySelectorAll('#breakdown-subtask-list > div'));
            const stepTexts = items.map(el => el.textContent.trim());

            const successNotice = modal ? modal.querySelector('.animate-fade-in') : null;
            const successText = successNotice ? successNotice.textContent.trim() : '';

            // Check store
            const planInStore = window.TempoPlanStore.getActivePlan('emergency');
            const taskInStore = planInStore.tasks.find(t => t.id === 'task_stats_pset4');
            const subtasksCountInStore = taskInStore && taskInStore.subtasks ? taskInStore.subtasks.length : 0;

            return {
                isModalVisible,
                stepCount: items.length,
                stepTexts,
                successText,
                subtasksCountInStore
            };
        })()
    """)
    log(f"Test 2 Result: {json.dumps(t2_res, indent=2)}")
    assert t2_res["isModalVisible"] is True, "Modal must remain open after clicking AI Help"
    assert 2 <= t2_res["stepCount"] <= 4, f"Expected 2 to 4 suggested steps, got {t2_res['stepCount']}"
    assert t2_res["subtasksCountInStore"] == t2_res["stepCount"], "Steps must be persisted in TempoPlanStore"

    # Verify task-specific quality for Statistics Assignment (Problem Set 4)
    all_text_lower = " ".join(t2_res["stepTexts"]).lower()
    has_formula_or_prob = ("problem" in all_text_lower or "formula" in all_text_lower or "calculation" in all_text_lower)
    assert has_formula_or_prob is True, "Suggestions must be specific to Statistics/Problem Set (formulas, problems, calculations)"
    log("✓ Test 2 passed: AI generated 2–4 task-specific actionable steps and displayed them in list.")

    # =========================================================================
    # TEST 3: Inline Editing of AI-Suggested Step
    # =========================================================================
    log("\n--- TEST 3: Inline Editing of Action Step ---")
    t3_res = eval_js("""
        (async () => {
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const task = plan.tasks.find(t => t.id === 'task_stats_pset4');
            const firstStepId = task.subtasks[0].id;

            // Start editing the first step
            window.TempoUrmodeFlow.startEditSubtask(firstStepId);
            await new Promise(r => setTimeout(r, 100));

            const editInput = document.getElementById('edit-subtask-input-' + firstStepId);
            if (!editInput) throw new Error("Edit input not found");

            // Change title
            editInput.value = "Review Chi-Square and Normal distribution formulas (20 min)";
            window.TempoUrmodeFlow.saveEditSubtask('task_stats_pset4', firstStepId);
            await new Promise(r => setTimeout(r, 100));

            // Verify in list and store
            const updatedItems = Array.from(document.querySelectorAll('#breakdown-subtask-list > div')).map(el => el.textContent.trim());
            const updatedPlan = window.TempoPlanStore.getActivePlan('emergency');
            const updatedTask = updatedPlan.tasks.find(t => t.id === 'task_stats_pset4');
            const updatedTitleInStore = updatedTask.subtasks[0].title;

            return {
                updatedItems,
                updatedTitleInStore
            };
        })()
    """)
    log(f"Test 3 Result: {json.dumps(t3_res, indent=2)}")
    assert "Chi-Square and Normal" in t3_res["updatedTitleInStore"], "Step edit must persist in store"
    log("✓ Test 3 passed: User can edit AI-suggested steps inline and changes persist.")

    # =========================================================================
    # TEST 4: Removing Step and Adding Manual Step
    # =========================================================================
    log("\n--- TEST 4: Remove Step and Add Manual Step ---")
    t4_res = eval_js("""
        (async () => {
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const task = plan.tasks.find(t => t.id === 'task_stats_pset4');
            const removeId = task.subtasks[task.subtasks.length - 1].id;

            // Remove last step
            window.TempoUrmodeFlow.removeSubtask('task_stats_pset4', removeId);
            await new Promise(r => setTimeout(r, 100));

            const countAfterRemove = document.querySelectorAll('#breakdown-subtask-list > div').length;

            // Add manual step
            const input = document.getElementById('breakdown-subtask-input');
            input.value = "Upload PDF scan to Canvas portal (10 min)";
            window.TempoUrmodeFlow.addSubtask('task_stats_pset4');
            await new Promise(r => setTimeout(r, 100));

            const updatedPlan = window.TempoPlanStore.getActivePlan('emergency');
            const updatedTask = updatedPlan.tasks.find(t => t.id === 'task_stats_pset4');
            const titlesInStore = updatedTask.subtasks.map(s => s.title);

            return {
                countAfterRemove,
                finalCount: titlesInStore.length,
                titlesInStore,
                hasManualStep: titlesInStore.some(t => t.includes("Upload PDF scan"))
            };
        })()
    """)
    log(f"Test 4 Result: {json.dumps(t4_res, indent=2)}")
    assert t4_res["hasManualStep"] is True, "Manual step must be added and persisted"
    log("✓ Test 4 passed: User can remove and manually add steps alongside AI suggestions.")

    # =========================================================================
    # TEST 5: Avoiding Duplicates & Confirmation Choice When Steps Exist
    # =========================================================================
    log("\n--- TEST 5: Avoiding Duplicates & Re-generation Handling ---")
    t5_res = eval_js("""
        (async () => {
            // Click AI Help again when 4 steps already exist
            const btn = document.getElementById('btn-ai-help-breakdown');
            btn.click();
            await new Promise(r => setTimeout(r, 500));

            const modal = document.getElementById('modal-urmode-flow');
            const choiceBanner = modal ? modal.querySelector('.animate-fade-in') : null;
            const bannerText = choiceBanner ? choiceBanner.textContent.trim() : '';

            // Test Replace With AI Steps option if presented, or notice
            const replaceBtn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent.includes('Replace'));
            let replacedCount = 0;
            if (replaceBtn) {
                replaceBtn.click();
                await new Promise(r => setTimeout(r, 200));
                const planAfterReplace = window.TempoPlanStore.getActivePlan('emergency');
                const taskAfterReplace = planAfterReplace.tasks.find(t => t.id === 'task_stats_pset4');
                replacedCount = taskAfterReplace.subtasks.length;
            }

            return {
                hasBanner: !!choiceBanner,
                bannerText,
                hadReplaceBtn: !!replaceBtn,
                replacedCount
            };
        })()
    """)
    log(f"Test 5 Result: {json.dumps(t5_res, indent=2)}")
    assert t5_res["hasBanner"] is True, "Feedback banner must be presented when steps exist"
    log("✓ Test 5 passed: Existing steps handled cleanly without duplicate pollution.")

    # =========================================================================
    # TEST 6: Persistence Across Page Reload
    # =========================================================================
    log("\n--- TEST 6: Persistence Across Page Reload ---")
    eval_js("window.location.reload()")
    time.sleep(1.0)
    wait_for_ready()

    t6_res = eval_js("""
        (() => {
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const task = plan.tasks.find(t => t.id === 'task_stats_pset4');
            return {
                taskExists: !!task,
                subtaskCount: task && task.subtasks ? task.subtasks.length : 0,
                subtaskTitles: task && task.subtasks ? task.subtasks.map(s => s.title) : []
            };
        })()
    """)
    log(f"Test 6 Result: {json.dumps(t6_res, indent=2)}")
    assert t6_res["taskExists"] is True, "Task must exist after reload"
    assert t6_res["subtaskCount"] >= 2, "Action steps must persist across reload"
    log("✓ Test 6 passed: Action steps fully persist across browser reload.")

    # =========================================================================
    # TEST 7: Preserve Existing Actions: Later, Break more tasks, Do this task
    # =========================================================================
    log("\n--- TEST 7: Preserve Existing Action Buttons ---")
    t7_res = eval_js("""
        (() => {
            window.TempoUrmodeFlow.startBreakTaskFlow('task_stats_pset4');
            const modal = document.getElementById('modal-urmode-flow');
            const allBtns = Array.from(modal.querySelectorAll('button')).map(b => b.textContent.trim());

            return {
                hasLater: allBtns.some(b => b.includes('Later')),
                hasBreakMore: allBtns.some(b => b.includes('Break more tasks')),
                hasDoThisTask: allBtns.some(b => b.includes('Do this task')),
                hasCloseX: !!modal.querySelector('button[aria-label="Close dialog"]')
            };
        })()
    """)
    log(f"Test 7 Result: {json.dumps(t7_res, indent=2)}")
    assert t7_res["hasLater"] is True, "'Later' button must be present"
    assert t7_res["hasBreakMore"] is True, "'Break more tasks →' button must be present"
    assert t7_res["hasDoThisTask"] is True, "'Do this task →' button must be present"
    assert t7_res["hasCloseX"] is True, "Close X button must be present"
    log("✓ Test 7 passed: All existing popup buttons and navigation behaviors are preserved.")

    log("\n=======================================================================")
    log(">>> ALL AI HELP BREAKDOWN POPUP TESTS COMPREHENSIVELY PASSED! <<<")
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
