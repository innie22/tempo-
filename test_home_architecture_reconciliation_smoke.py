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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_recon_")
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
    
    log(f"Launching Edge on port {port}...")
    proc = subprocess.Popen(cmd)
    ws = None
    try:
        ws_url = None
        for _ in range(30):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as resp:
                    tabs = json.loads(resp.read().decode())
                    pages = [t for t in tabs if t.get("type") == "page" and "localhost:8000" in t.get("url", "")]
                    if not pages:
                        pages = [t for t in tabs if t.get("type") == "page"]
                    if pages:
                        ws_url = pages[0].get("webSocketDebuggerUrl")
                        break
            except Exception:
                time.sleep(0.5)
        
        if not ws_url:
            raise RuntimeError("Could not connect to browser WebSocket debugging URL.")
        
        log(f"Connected to CDP: {ws_url}")
        ws = websocket.create_connection(ws_url, timeout=10)
        req_id = 0
        
        def send_eval(expression):
            nonlocal req_id
            req_id += 1
            msg = {
                "id": req_id,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": expression,
                    "returnByValue": True,
                    "awaitPromise": True
                }
            }
            ws.send(json.dumps(msg))
            while True:
                res = json.loads(ws.recv())
                if res.get("id") == req_id:
                    result = res.get("result", {})
                    if "exceptionDetails" in result:
                        raise RuntimeError(f"JS Exception: {result['exceptionDetails']}")
                    return result.get("result", {}).get("value")

        def wait_for_ready():
            for _ in range(50):
                try:
                    ready = send_eval("Boolean(window.TempoMode && window.TempoTools && window.TempoLearnSolve && window.TempoFocusZone && window.TempoApp)")
                    if ready:
                        return True
                except Exception:
                    pass
                time.sleep(0.2)
            return False

        if not wait_for_ready():
            raise RuntimeError("Timeout waiting for application to initialize.")
        
        log("App initialized with TempoMode and core modules loaded.\n")

        # =========================================================================
        # PART 1: DEFAULT HOME ARCHITECTURE RECONCILIATION
        # =========================================================================
        log("=== PART 1: DEFAULT HOME ARCHITECTURE RECONCILIATION ===")
        send_eval("window.TempoMode.setMode('default');")
        time.sleep(0.5)

        # 1.1 Verify No 'Default Mode' Badge or Hero Takeover
        dmode_info = send_eval("""
            (() => {
                const dmodeBox = document.getElementById('dmode-home-content');
                const switchBar = document.getElementById('dmode-mode-switch-bar');
                const yourDay = document.getElementById('dmode-your-day');
                const guestInvitation = document.getElementById('dmode-guest-invitation');
                const tools = dmodeBox.querySelector('.tempo-tools-section');
                const learnSolve = dmodeBox.querySelector('#tempo-learn-solve-section');
                const posts = dmodeBox.querySelector('#homepage-community-posts-list');
                const shellBadge = document.getElementById('mode-indicator-shell');

                return {
                    dmodeBoxVisible: !dmodeBox.classList.contains('hidden'),
                    hasSwitchBar: Boolean(switchBar),
                    switchBarText: switchBar ? switchBar.innerText.trim() : '',
                    hasYourDay: Boolean(yourDay),
                    yourDayText: yourDay ? yourDay.innerText.trim() : '',
                    hasGuestInvitation: Boolean(guestInvitation),
                    hasTools: Boolean(tools),
                    hasLearnSolve: Boolean(learnSolve),
                    hasPosts: Boolean(posts),
                    isShellBadgeHidden: shellBadge ? shellBadge.classList.contains('hidden') : true,
                    headerText: dmodeBox.querySelector('h2') ? dmodeBox.querySelector('h2').innerText.trim() : ''
                };
            })()
        """)

        assert dmode_info["dmodeBoxVisible"], "Default Home box must be visible."
        assert dmode_info["isShellBadgeHidden"], "Navbar mode badge must be hidden in Default mode (no Default badge)."
        assert not ("Default Mode" in dmode_info["headerText"]), "Default Home header must NOT say 'Default Mode'."
        assert dmode_info["hasSwitchBar"], "Default Home must contain #dmode-mode-switch-bar near the top."
        assert "Need a different kind of support?" in dmode_info["switchBarText"], "Switch bar must ask 'Need a different kind of support?'."
        assert "Change mode" in dmode_info["switchBarText"], "Switch bar must offer 'Change mode →'."
        assert dmode_info["hasYourDay"], "Default Home must render Your Day continuity section."
        assert "Nothing planned for today." in dmode_info["yourDayText"], "Unplanned/guest Your Day should say 'Nothing planned for today.'."
        assert "+ Add a task" in dmode_info["yourDayText"], "Unplanned Your Day should have '+ Add a task' button."
        assert dmode_info["hasGuestInvitation"], "Guest should see subtle account invitation banner."
        assert dmode_info["hasTools"], "Default Home must include shared Tempo Tools."
        assert dmode_info["hasLearnSolve"], "Default Home must include shared Learn & Solve."
        assert dmode_info["hasPosts"], "Default Home must include Tempo Posts."
        log("✓ 1.1 Default Home guest layout & mode-switch entry verified.")

        # 1.2 Verify Mode Switch Bar Modal Interactions & Options
        send_eval("window.TempoMode.openChangeModeModal();")
        time.sleep(0.3)
        modal_info = send_eval("""
            (() => {
                const modal = document.getElementById('modal-change-mode');
                const optEmergency = document.getElementById('change-mode-opt-emergency');
                const optRecovery = document.getElementById('change-mode-opt-recovery');
                const optUnclear = document.getElementById('change-mode-opt-unclear');
                const optDefault = document.getElementById('change-mode-opt-default');
                const footerBtn = document.getElementById('change-mode-footer-btn');

                return {
                    isOpen: !modal.classList.contains('hidden'),
                    emergencyVisible: !optEmergency.classList.contains('hidden'),
                    recoveryVisible: !optRecovery.classList.contains('hidden'),
                    unclearVisible: !optUnclear.classList.contains('hidden'),
                    defaultVisible: !optDefault.classList.contains('hidden'),
                    footerText: footerBtn ? footerBtn.innerText.trim() : ''
                };
            })()
        """)
        assert modal_info["isOpen"], "Change mode modal must be open."
        assert modal_info["emergencyVisible"], "⚡ Urgent Mode option must be visible."
        assert modal_info["recoveryVisible"], "🌱 Recovery Mode option must be visible."
        assert modal_info["unclearVisible"], "🧭 Unclear Mode option must be visible."
        assert not modal_info["defaultVisible"], "☕ Default Option must be hidden when already in Default mode."
        assert "Stay in Default Tempo" in modal_info["footerText"], "Footer button should say 'Stay in Default Tempo'."
        log("✓ 1.2 Change Mode modal accurately displays Urgent, Recovery, Unclear destinations (Default hidden).")

        # 1.3 Verify Guest Auth Gating via selectModeOption
        send_eval("window.TempoMode.selectModeOption('emergency');")
        time.sleep(0.4)
        gate_info = send_eval("""
            (() => {
                const modalChange = document.getElementById('modal-change-mode');
                const modalSignIn = document.getElementById('modal-signin');
                const pendingMode = window.TempoMode.getPendingMode();
                const currentMode = window.TempoMode.getMode();

                return {
                    changeModalClosed: modalChange.classList.contains('hidden'),
                    signInModalOpen: !modalSignIn.classList.contains('hidden'),
                    pendingMode: pendingMode,
                    currentMode: currentMode
                };
            })()
        """)
        assert gate_info["changeModalClosed"], "Change mode modal must close upon option selection."
        assert gate_info["signInModalOpen"], "Sign In modal must open for unauthenticated guest."
        assert gate_info["pendingMode"] == "emergency", "Pending mode must be set to 'emergency'."
        assert gate_info["currentMode"] == "default", "User must NOT enter mode before authentication."
        log("✓ 1.3 Guest mode change request correctly preserves auth gate and pending mode.")

        # Close signin modal
        send_eval("if (window.TempoAuth) window.TempoAuth.closeModal();")
        time.sleep(0.2)

        # 1.4 Verify Authenticated User Experience with Work
        log("\n--- Checking Authenticated Default Home (Active & Completed Work) ---")
        send_eval("""
            (async () => {
                // Register / authenticate user via TempoAuth
                await window.TempoAuth.register('Alex Rivera', 'alex.rivera@university.edu', 'pass123');
                // Ensure Default mode is active for Default Home testing
                window.TempoMode.setMode('default');
                // Mock active plan with today tasks
                const nowObj = new Date();
                const todayStr = `${nowObj.getFullYear()}-${String(nowObj.getMonth() + 1).padStart(2, '0')}-${String(nowObj.getDate()).padStart(2, '0')}`;
                const samplePlan = {
                    id: 'test_plan_recon',
                    plannedTasks: [
                        {
                            taskId: 'task_1',
                            dayDate: todayStr,
                            dayLabel: 'Today',
                            scheduledStartTime: '10:00 AM',
                            task: { id: 'task_1', name: 'Literature Review Paper', durationMinutes: 60, completed: false, isInProgress: true }
                        },
                        {
                            taskId: 'task_2',
                            dayDate: todayStr,
                            dayLabel: 'Today',
                            scheduledStartTime: '02:00 PM',
                            task: { id: 'task_2', name: 'Draft Summary Deck', durationMinutes: 30, completed: false }
                        }
                    ]
                };
                samplePlan.tasks = samplePlan.plannedTasks.map(pt => pt.task);
                samplePlan.availabilityDays = [
                    { date: todayStr, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }
                ];
                await window.TempoPlanStore.saveActivePlan('emergency', samplePlan);
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(samplePlan);
                }
                if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.savePlan === 'function') {
                    window.TempoPlanWorkspace.savePlan(samplePlan);
                }
                window.TempoMode.renderDmodeHome();
                return true;
            })()
        """)
        time.sleep(0.4)

        auth_dmode = send_eval("""
            (() => {
                const yourDay = document.getElementById('dmode-your-day');
                const rows = yourDay ? yourDay.querySelectorAll('.bg-white.border') : [];
                const guestInvitation = document.getElementById('dmode-guest-invitation');
                return {
                    greeting: document.querySelector('#dmode-home-content h2') ? document.querySelector('#dmode-home-content h2').innerText.trim() : '',
                    rowCount: rows.length,
                    hasGuestInvitation: Boolean(guestInvitation),
                    firstTaskTitle: rows[0] ? rows[0].innerText : ''
                };
            })()
        """)
        assert "Hi, Alex 👋" in auth_dmode["greeting"], "Greeting should address authenticated user by first name."
        assert auth_dmode["rowCount"] >= 2, "Active tasks must be rendered in Your Day."
        assert not auth_dmode["hasGuestInvitation"], "Authenticated user must NOT see guest invitation banner."
        log("✓ 1.4 Authenticated user with active work renders personal task list seamlessly.")

        # Complete all tasks and verify completed state
        send_eval("""
            (async () => {
                const plan = window.TempoPlanStore.getActivePlan('emergency');
                plan.plannedTasks.forEach(pt => { pt.task.completed = true; pt.task.isInProgress = false; });
                await window.TempoPlanStore.saveActivePlan('emergency', plan);
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(plan);
                }
                window.TempoMode.renderDmodeHome();
                return true;
            })()
        """)
        time.sleep(0.3)
        completed_info = send_eval("""
            (() => {
                const yourDay = document.getElementById('dmode-your-day');
                return {
                    text: yourDay ? yourDay.innerText : ''
                };
            })()
        """)
        assert "You're done with what was planned for today." in completed_info["text"], "Completed work state must show compact check message."
        log("✓ 1.5 Authenticated completed work state verified.")

        # =========================================================================
        # PART 2: URGENT HOME STABLE SHELL & ALL 7 STATES RECONCILIATION
        # =========================================================================
        log("\n=== PART 2: URGENT HOME STABLE SHELL & 7 STATES RECONCILIATION ===")
        send_eval("window.TempoMode.setMode('emergency');")
        time.sleep(0.5)

        # Helper to check Urgent Home Restored 65/35 Execution Shell elements
        def check_urgent_shell():
            return send_eval("""
                (() => {
                    const emodeBox = document.getElementById('emode-home-content');
                    const header = emodeBox.querySelector('#btn-home-mode-selector');
                    const supportRow = emodeBox.querySelector('.urgent-support-row');
                    const cardOverwhelmed = emodeBox.querySelector('.urgent-card-overwhelmed');
                    const cardFocusNow = emodeBox.querySelector('.urgent-card-focus-now');
                    const rightCol = emodeBox.querySelector('.urgent-right-col');
                    const sharedTools = emodeBox.querySelector('.tempo-tools-section');
                    const sharedLearnSolve = emodeBox.querySelector('#emode-learn-solve-container');
                    const posts = emodeBox.querySelector('#urgent-community-posts-list');
                    
                    const toolsCount = emodeBox.querySelectorAll('.tempo-tools-section').length;
                    const learnSolveCount = emodeBox.querySelectorAll('#emode-learn-solve-container').length;
                    const postsCount = emodeBox.querySelectorAll('#urgent-community-posts-list').length;

                    return {
                        hasHeader: Boolean(header),
                        headerText: header ? header.innerText.trim() : '',
                        hasSupportRow: Boolean(supportRow),
                        hasCardOverwhelmed: Boolean(cardOverwhelmed),
                        hasCardFocusNow: Boolean(cardFocusNow),
                        hasRightCol: Boolean(rightCol),
                        hasTools: Boolean(sharedTools),
                        hasLearnSolve: Boolean(sharedLearnSolve),
                        hasPosts: Boolean(posts),
                        toolsCount,
                        learnSolveCount,
                        postsCount
                    };
                })()
            """)

        def verify_urgent_shell(shell, state_name):
            assert shell["hasHeader"], f"[{state_name}] Shell header must be present."
            assert "Urgent Mode" in shell["headerText"], f"[{state_name}] Shell header must show Urgent Mode."
            assert shell["hasSupportRow"] and shell["hasCardOverwhelmed"] and shell["hasCardFocusNow"], f"[{state_name}] Dedicated Urgent support row (Overwhelmed + Focus Now) must be present."
            assert shell["hasRightCol"], f"[{state_name}] Right-hand execution plan column must be present in 65/35 workspace."
            assert not shell["hasTools"] and shell["toolsCount"] == 0, f"[{state_name}] Generic Tempo Tools must NOT be injected into Urgent Mode."
            assert not shell["hasLearnSolve"] and shell["learnSolveCount"] == 0, f"[{state_name}] Learn & Solve must NOT be injected into Urgent Mode."
            assert shell["hasPosts"] and shell["postsCount"] == 1, f"[{state_name}] Expected exactly 1 Posts section, got {shell['postsCount']}"

        # 2.1 State A: PLAN_INCOMPLETE
        log("\n--- Checking State A: PLAN_INCOMPLETE ---")
        send_eval("""
            (async () => {
                await window.TempoPlanStore.archiveActivePlan('emergency');
                window.TempoPlanStore.clearInMemoryCache();
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(null);
                }
                if (window.TempoEmergencyFlow) {
                    window.TempoEmergencyFlow.getCurrentStage = () => 'reality-check';
                }
                window.TempoMode.renderEmodeHome();
                return true;
            })()
        """)
        time.sleep(0.4)
        shell = check_urgent_shell()
        verify_urgent_shell(shell, "PLAN_INCOMPLETE")
        
        inc_card = send_eval("""
            (() => {
                const emodeBox = document.getElementById('emode-home-content');
                return {
                    hasResumeText: emodeBox.innerText.includes("You're still setting up your plan."),
                    hasContinueBtn: emodeBox.innerText.includes("Continue building my plan"),
                    hasSwitchBtn: emodeBox.innerText.includes("Switch mode")
                };
            })()
        """)
        assert inc_card["hasResumeText"], "Incomplete state must show setup message."
        assert inc_card["hasContinueBtn"], "Incomplete state must have 'Continue building my plan'."
        assert inc_card["hasSwitchBtn"], "Incomplete state must have 'Switch mode'."
        log("✓ 2.1 State PLAN_INCOMPLETE renders compact primary card inside stable shell without duplicate lower ecosystem.")

        # 2.2 State B: ACTIVE_TODAY
        log("\n--- Checking State B: ACTIVE_TODAY ---")
        send_eval("""
            (async () => {
                const nowObj = new Date();
                const todayStr = `${nowObj.getFullYear()}-${String(nowObj.getMonth() + 1).padStart(2, '0')}-${String(nowObj.getDate()).padStart(2, '0')}`;
                const samplePlan = {
                    id: 'active_plan',
                    plannedTasks: [
                        {
                            taskId: 't_active',
                            dayDate: todayStr,
                            dayLabel: 'Today',
                            startTime: '10:00 AM',
                            task: { id: 't_active', name: 'Write Introduction Section', durationMinutes: 45, completed: false, isInProgress: true }
                        }
                    ]
                };
                samplePlan.tasks = samplePlan.plannedTasks.map(pt => pt.task);
                samplePlan.availabilityDays = [{ date: todayStr, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }];
                await window.TempoPlanStore.saveActivePlan('emergency', samplePlan);
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(samplePlan);
                }
                window.TempoMode.renderEmodeHome();
                return true;
            })()
        """)
        time.sleep(0.4)
        shell = check_urgent_shell()
        verify_urgent_shell(shell, "ACTIVE_TODAY")
        active_card = send_eval("""
            (() => {
                const emodeBox = document.getElementById('emode-home-content');
                const taskNow = emodeBox.querySelector('.urgent-card-now');
                const planToday = emodeBox.querySelector('.urgent-right-col');
                return {
                    hasTaskNow: Boolean(taskNow),
                    hasPlanToday: Boolean(planToday),
                    taskNowText: taskNow ? taskNow.innerText : ''
                };
            })()
        """)
        assert active_card["hasTaskNow"], "Active today must have 'YOUR TASK FOR NOW' card."
        assert active_card["hasPlanToday"], "Active today must have 'Your plan for today' column."
        assert "Write Introduction Section" in active_card["taskNowText"], "Task for now must show task name."
        log("✓ 2.2 State ACTIVE_TODAY renders 2-column execution core inside stable shell.")

        # 2.3 State C: TODAY_COMPLETE
        log("\n--- Checking State C: TODAY_COMPLETE ---")
        send_eval("""
            (async () => {
                const nowObj = new Date();
                const todayStr = `${nowObj.getFullYear()}-${String(nowObj.getMonth() + 1).padStart(2, '0')}-${String(nowObj.getDate()).padStart(2, '0')}`;
                const tomObj = new Date();
                tomObj.setDate(tomObj.getDate() + 1);
                const tomStr = `${tomObj.getFullYear()}-${String(tomObj.getMonth() + 1).padStart(2, '0')}-${String(tomObj.getDate()).padStart(2, '0')}`;
                const samplePlan = {
                    id: 'today_complete_plan',
                    plannedTasks: [
                        {
                            taskId: 't_done',
                            dayDate: todayStr,
                            dayLabel: 'Today',
                            task: { id: 't_done', name: 'Task Finished', completed: true }
                        },
                        {
                            taskId: 't_tom',
                            dayDate: tomStr,
                            dayLabel: 'Tomorrow',
                            startTime: '09:00 AM',
                            task: { id: 't_tom', name: 'Tomorrow Task', completed: false }
                        }
                    ]
                };
                samplePlan.tasks = samplePlan.plannedTasks.map(pt => pt.task);
                await window.TempoPlanStore.saveActivePlan('emergency', samplePlan);
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(samplePlan);
                }
                window.TempoMode.renderEmodeHome();
                return true;
            })()
        """)
        time.sleep(0.4)
        shell = check_urgent_shell()
        verify_urgent_shell(shell, "TODAY_COMPLETE")
        tc_card = send_eval("""
            (() => {
                const emodeBox = document.getElementById('emode-home-content');
                return {
                    hasDoneText: emodeBox.innerText.includes("You're done for today."),
                    hasProtectRest: emodeBox.innerText.includes("Protect your rest.")
                };
            })()
        """)
        assert tc_card["hasDoneText"], "Today complete must show 'You're done for today.'."
        log("✓ 2.3 State TODAY_COMPLETE renders compact card inside stable shell.")

        # 2.4 State D: NO_WORK_TODAY
        log("\n--- Checking State D: NO_WORK_TODAY ---")
        send_eval("""
            (async () => {
                const tomObj = new Date();
                tomObj.setDate(tomObj.getDate() + 2);
                const futureStr = `${tomObj.getFullYear()}-${String(tomObj.getMonth() + 1).padStart(2, '0')}-${String(tomObj.getDate()).padStart(2, '0')}`;
                const samplePlan = {
                    id: 'no_work_plan',
                    plannedTasks: [
                        {
                            taskId: 't_future',
                            dayDate: futureStr,
                            dayLabel: 'Friday',
                            task: { id: 't_future', name: 'Future Task', completed: false }
                        }
                    ]
                };
                samplePlan.tasks = samplePlan.plannedTasks.map(pt => pt.task);
                await window.TempoPlanStore.saveActivePlan('emergency', samplePlan);
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(samplePlan);
                }
                window.TempoMode.renderEmodeHome();
                return true;
            })()
        """)
        time.sleep(0.4)
        shell = check_urgent_shell()
        verify_urgent_shell(shell, "NO_WORK_TODAY")
        nwt_card = send_eval("""
            (() => {
                const emodeBox = document.getElementById('emode-home-content');
                return {
                    hasNoWorkText: emodeBox.innerText.includes("Nothing planned for today."),
                    hasContinuesOn: emodeBox.innerText.includes("Your Urgent Plan continues on")
                };
            })()
        """)
        assert nwt_card["hasNoWorkText"], "No work today must show 'Nothing planned for today.'."
        assert nwt_card["hasContinuesOn"], "No work today must show 'Your Urgent Plan continues on'."
        log("✓ 2.4 State NO_WORK_TODAY renders compact card inside stable shell.")

        # 2.5 State E: TIME_ENDED_WITH_INCOMPLETE_WORK
        log("\n--- Checking State E: TIME_ENDED_WITH_INCOMPLETE_WORK ---")
        send_eval("""
            (async () => {
                const nowObj = new Date();
                const todayStr = `${nowObj.getFullYear()}-${String(nowObj.getMonth() + 1).padStart(2, '0')}-${String(nowObj.getDate()).padStart(2, '0')}`;
                const samplePlan = {
                    id: 'time_ended_plan',
                    availabilityDays: [
                        {
                            date: todayStr,
                            blocks: [{ start: '00:01', end: '00:02' }] // Past end time
                        }
                    ],
                    plannedTasks: [
                        {
                            taskId: 't_late',
                            dayDate: todayStr,
                            task: { id: 't_late', name: 'Unfinished Assignment', completed: false, hasDeadline: true, deadlineDate: todayStr }
                        }
                    ]
                };
                samplePlan.tasks = samplePlan.plannedTasks.map(pt => pt.task);
                await window.TempoPlanStore.saveActivePlan('emergency', samplePlan);
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(samplePlan);
                }
                window.TempoMode.renderEmodeHome();
                return true;
            })()
        """)
        time.sleep(0.4)
        shell = check_urgent_shell()
        verify_urgent_shell(shell, "TIME_ENDED_WITH_INCOMPLETE_WORK")
        te_card = send_eval("""
            (() => {
                const emodeBox = document.getElementById('emode-home-content');
                return {
                    hasTimeEndedText: emodeBox.innerText.includes("Your planned work time for today has ended."),
                    hasStopBtn: emodeBox.innerText.includes("Stop for today"),
                    hasKeepBtn: emodeBox.innerText.includes("Keep working")
                };
            })()
        """)
        assert te_card["hasTimeEndedText"], "Time ended state must show 'Your planned work time for today has ended.'."
        assert te_card["hasStopBtn"], "Time ended state must have 'Stop for today'."
        assert te_card["hasKeepBtn"], "Time ended state must have 'Keep working'."
        log("✓ 2.5 State TIME_ENDED_WITH_INCOMPLETE_WORK renders compact card inside stable shell.")

        # 2.6 State F: PLAN_STALE
        log("\n--- Checking State F: PLAN_STALE ---")
        send_eval("""
            (async () => {
                // Task from yesterday incomplete
                const yestObj = new Date();
                yestObj.setDate(yestObj.getDate() - 1);
                const yestStr = `${yestObj.getFullYear()}-${String(yestObj.getMonth() + 1).padStart(2, '0')}-${String(yestObj.getDate()).padStart(2, '0')}`;
                const samplePlan = {
                    id: 'stale_plan',
                    plannedTasks: [
                        {
                            taskId: 't_stale',
                            dayDate: yestStr,
                            dayLabel: 'Yesterday',
                            task: { id: 't_stale', name: 'Overdue Project Milestone', completed: false }
                        }
                    ]
                };
                samplePlan.tasks = samplePlan.plannedTasks.map(pt => pt.task);
                await window.TempoPlanStore.saveActivePlan('emergency', samplePlan);
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(samplePlan);
                }
                window.TempoMode.renderEmodeHome();
                return true;
            })()
        """)
        time.sleep(0.4)
        shell = check_urgent_shell()
        verify_urgent_shell(shell, "PLAN_STALE")
        stale_card = send_eval("""
            (() => {
                const emodeBox = document.getElementById('emode-home-content');
                return {
                    hasStaleText: emodeBox.innerText.includes("Your plan needs an update."),
                    hasReviewBtn: emodeBox.innerText.includes("Review & update plan →"),
                    hasDismissBtn: emodeBox.innerText.includes("Dismiss for now")
                };
            })()
        """)
        assert stale_card["hasStaleText"], "Plan stale state must show 'Your plan needs an update.'."
        assert stale_card["hasReviewBtn"], "Plan stale state must have 'Review & update plan →'."
        assert stale_card["hasDismissBtn"], "Plan stale state must have 'Dismiss for now'."
        log("✓ 2.6 State PLAN_STALE renders compact card inside stable shell.")

        # 2.7 State G: PLAN_COMPLETE
        log("\n--- Checking State G: PLAN_COMPLETE ---")
        send_eval("""
            (async () => {
                const nowObj = new Date();
                const todayStr = `${nowObj.getFullYear()}-${String(nowObj.getMonth() + 1).padStart(2, '0')}-${String(nowObj.getDate()).padStart(2, '0')}`;
                const samplePlan = {
                    id: 'all_done_plan',
                    plannedTasks: [
                        {
                            taskId: 't_all_done',
                            dayDate: todayStr,
                            task: { id: 't_all_done', name: 'Comprehensive Final Project', completed: true }
                        }
                    ]
                };
                samplePlan.tasks = samplePlan.plannedTasks.map(pt => pt.task);
                await window.TempoPlanStore.saveActivePlan('emergency', samplePlan);
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(samplePlan);
                }
                window.TempoMode.renderEmodeHome();
                return true;
            })()
        """)
        time.sleep(0.4)
        shell = check_urgent_shell()
        verify_urgent_shell(shell, "PLAN_COMPLETE")
        pc_card = send_eval("""
            (() => {
                const emodeBox = document.getElementById('emode-home-content');
                return {
                    hasPlanCompleteText: emodeBox.innerText.includes("Your Urgent Plan is complete."),
                    hasShiftBtn: emodeBox.innerText.includes("Shift to Recovery Mode →"),
                    hasStayBtn: emodeBox.innerText.includes("Stay in Urgent Mode")
                };
            })()
        """)
        assert pc_card["hasPlanCompleteText"], "Plan complete must show 'Your Urgent Plan is complete.'."
        assert pc_card["hasShiftBtn"], "Plan complete must recommend shifting to Recovery Mode."
        assert pc_card["hasStayBtn"], "Plan complete must allow staying in Urgent Mode."
        log("✓ 2.7 State PLAN_COMPLETE renders compact card inside stable shell.")

        log("\n=======================================================")
        log(">>> ALL HOME ARCHITECTURE RECONCILIATION TESTS PASSED! <<<")
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
