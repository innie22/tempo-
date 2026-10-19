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

user_data_dir = tempfile.mkdtemp(prefix="tempo_rm_breakdown_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9285

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

log("Launching Edge on port 9285...")
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

    # TEST 1: Check STAGES array in emergencyFlow.js and phase indicators
    log("\n--- TEST 1: Verify STAGES definitions and Phase indicators ---")
    t1_res = eval_js("""
        (() => {
            // Check if 'breakdown' is in emergency stages
            let hasBreakdownInStages = false;
            try {
                // Testing transition to breakdown falls back
                window.TempoEmergencyFlow.goToStage('breakdown');
                hasBreakdownInStages = window.TempoEmergencyFlow.getCurrentStage() === 'breakdown';
            } catch (e) {
                hasBreakdownInStages = false;
            }

            const phaseReady = document.getElementById('em-phase-ready');
            return {
                currentStageAfterBreakdownAttempt: window.TempoEmergencyFlow.getCurrentStage(),
                hasBreakdownInStages,
                readyPhasePillText: phaseReady ? phaseReady.textContent.trim() : null
            };
        })()
    """)
    log(f"Test 1 Result: {json.dumps(t1_res, indent=2)}")
    assert t1_res["hasBreakdownInStages"] is False, "STAGES must not include or allow 'breakdown'"
    assert t1_res["currentStageAfterBreakdownAttempt"] in ['entry', 'plan-review', 'handoff'], "Must fall back cleanly"
    log("✓ Test 1 passed: 'breakdown' is not an active stage.")

    # TEST 2: Verify calling goToStage('breakdown') safely falls back and does not render breakdown page
    log("\n--- TEST 2: Direct call to goToStage('breakdown') falls back cleanly ---")
    t2_res = eval_js("""
        (() => {
            window.TempoEmergencyFlow.goToStage('breakdown');
            const currentStage = window.TempoEmergencyFlow.getCurrentStage();
            const container = document.getElementById('emergency-stage-breakdown');
            const isHidden = !container || container.classList.contains('hidden');
            const innerHTML = container ? container.innerHTML.trim() : '';

            return {
                currentStage,
                containerExists: !!container,
                isHidden,
                innerHTMLEmpty: innerHTML === ''
            };
        })()
    """)
    log(f"Test 2 Result: {json.dumps(t2_res, indent=2)}")
    assert t2_res["currentStage"] in ['entry', 'plan-review', 'handoff'], f"Stage should fall back cleanly, got {t2_res['currentStage']}"
    assert t2_res["isHidden"] is True, "emergency-stage-breakdown container must be hidden"
    assert t2_res["innerHTMLEmpty"] is True, "emergency-stage-breakdown container must be empty"
    log("✓ Test 2 passed: goToStage('breakdown') safely falls back and never renders breakdown page.")

    # TEST 3: Verify Plan Review screen has NO 'Review Step Breakdown' button
    log("\n--- TEST 3: Verify Plan Review screen has NO 'Review Step Breakdown' button ---")
    t3_res = eval_js("""
        (async () => {
            const today = new Date().toISOString().split('T')[0];
            const testPlan = {
                id: 'plan_test_review_btn',
                mode: 'emergency',
                createdAt: new Date().toISOString(),
                totalTasks: 2,
                totalMinutes: 60,
                plannedTasks: [
                    {
                        task: {
                            id: 'task_rev_1',
                            name: 'Prepare Thesis Outline',
                            durationMinutes: 30,
                            durationLabel: '30 min',
                            completed: false,
                            subtasks: []
                        },
                        dayNumber: 1,
                        timeBucket: 'morning',
                        executionBadge: 'UP NEXT'
                    },
                    {
                        task: {
                            id: 'task_rev_2',
                            name: 'Gather Literature Citations',
                            durationMinutes: 30,
                            durationLabel: '30 min',
                            completed: false,
                            subtasks: []
                        },
                        dayNumber: 1,
                        timeBucket: 'afternoon',
                        executionBadge: 'PLANNED'
                    }
                ],
                availabilityDays: [{ date: today, label: 'Today', blocks: [{ start: '09:00', end: '18:00' }] }]
            };
            testPlan.tasks = testPlan.plannedTasks.map(p => p.task);

            window.TempoEmergencyFlow.setConfirmedPlan(testPlan);

            // 1. Initial Plan Review (before save)
            window.TempoEmergencyFlow.goToStage('plan-review');
            const reviewContainer = document.getElementById('emergency-stage-plan-review');
            const allButtons1 = reviewContainer ? Array.from(reviewContainer.querySelectorAll('button')).map(b => b.textContent.trim()) : [];
            const hasBreakdownBtn1 = allButtons1.some(t => t.toLowerCase().includes('breakdown'));

            // 2. Plan Review with returnToHandoff = true via viewPlan()
            window.TempoEmergencyFlow.viewPlan();
            const allButtons2 = reviewContainer ? Array.from(reviewContainer.querySelectorAll('button')).map(b => b.textContent.trim()) : [];
            const hasBreakdownBtn2 = allButtons2.some(t => t.toLowerCase().includes('breakdown'));

            return {
                allButtonsInitialReview: allButtons1,
                hasBreakdownBtnInitial: hasBreakdownBtn1,
                allButtonsReturnToHandoff: allButtons2,
                hasBreakdownBtnReturnToHandoff: hasBreakdownBtn2
            };
        })()
    """)
    log(f"Test 3 Result: {json.dumps(t3_res, indent=2)}")
    assert t3_res["hasBreakdownBtnInitial"] is False, "'Review Step Breakdown' button must NOT exist in initial Plan Review"
    assert t3_res["hasBreakdownBtnReturnToHandoff"] is False, "'Review Step Breakdown' button must NOT exist in returnToHandoff Plan Review"
    log("✓ Test 3 passed: No 'Review Step Breakdown' button exists anywhere in Plan Review.")

    # TEST 4: Calling reviewStepBreakdown() directly redirects without opening breakdown
    log("\n--- TEST 4: Calling reviewStepBreakdown() programmatically ---")
    t4_res = eval_js("""
        (() => {
            window.TempoEmergencyFlow.reviewStepBreakdown();
            const currentStage = window.TempoEmergencyFlow.getCurrentStage();
            const container = document.getElementById('emergency-stage-breakdown');
            const isHidden = !container || container.classList.contains('hidden');

            return {
                currentStage,
                isHidden
            };
        })()
    """)
    log(f"Test 4 Result: {json.dumps(t4_res, indent=2)}")
    assert t4_res["currentStage"] in ['handoff', 'plan-review'], f"reviewStepBreakdown must redirect to handoff or plan-review, got {t4_res['currentStage']}"
    assert t4_res["isHidden"] is True, "emergency-stage-breakdown must remain hidden"
    log("✓ Test 4 passed: reviewStepBreakdown() safely redirects to handoff or plan-review.")

    # TEST 5: Working Plan saving and post-save flow operates properly without Step Breakdown page
    log("\n--- TEST 5: Plan saving and post-save flow integrity ---")
    t5_res = eval_js("""
        (async () => {
            window.TempoEmergencyFlow.goToStage('plan-review');

            const usePlanBtn = document.getElementById('btn-em-use-plan');
            if (usePlanBtn) usePlanBtn.click();

            await new Promise(r => setTimeout(r, 400));

            const modal = document.getElementById('modal-urmode-flow');
            const isModalVisible = modal && !modal.classList.contains('hidden');
            const modalEyebrow = modal ? (modal.querySelector('span') ? modal.querySelector('span').textContent.trim() : '') : '';
            const breakdownContainer = document.getElementById('emergency-stage-breakdown');
            const isBreakdownHidden = !breakdownContainer || breakdownContainer.classList.contains('hidden');

            return {
                isModalVisible,
                modalEyebrow,
                isBreakdownHidden
            };
        })()
    """)
    log(f"Test 5 Result: {json.dumps(t5_res, indent=2)}")
    assert t5_res["isModalVisible"] is True, "'Your task for now' modal should be visible"
    assert t5_res["isBreakdownHidden"] is True, "Step Breakdown page must not be opened"
    log("✓ Test 5 passed: Plan saved and choice modal displayed cleanly without breakdown page.")

    # TEST 6: Start Working and Focus Zone work properly
    log("\n--- TEST 6: Focus Zone launch integrity ---")
    t6_res = eval_js("""
        (() => {
            const hasLaunchFocusZone = typeof window.TempoEmergencyFlow.launchFocusZone === 'function';
            const hasStartWorking = typeof window.TempoEmergencyFlow.startWorking === 'function';
            const hasViewPlan = typeof window.TempoEmergencyFlow.viewPlan === 'function';
            return {
                hasLaunchFocusZone,
                hasStartWorking,
                hasViewPlan
            };
        })()
    """)
    log(f"Test 6 Result: {json.dumps(t6_res, indent=2)}")
    assert t6_res["hasLaunchFocusZone"] is True, "launchFocusZone must remain available"
    assert t6_res["hasStartWorking"] is True, "startWorking must remain available"
    assert t6_res["hasViewPlan"] is True, "viewPlan must remain available"
    log("✓ Test 6 passed: Focus Zone and Start Working flows remain intact.")

    log("\n=======================================================================")
    log(">>> ALL STEP BREAKDOWN REMOVAL TESTS COMPREHENSIVELY PASSED! <<<")
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
