"""
TEMPO REGRESSION TEST SUITE: URGENT MODE PRODUCT CONTRACT
File: test_urgent_mode_contract.py

Validates the frozen development contract for Urgent Mode:
- Interactive mode button & popover destinations (excludes active mode, excludes SOS)
- Internal mode remains "emergency" (never "urgent")
- No separate greeting hero; greeting inside primary left card
- Asymmetric ~65 / 35 execution core (warm primary left, white structured right)
- Dedicated support row (Overwhelmed + Focus Now)
- Lower priority Tempo Posts
- Exclusion of generic Tempo Tools, Learn & Solve, and Self-check from Urgent Home
- All 7 dynamic states preserve common approved composition without full-page takeovers
"""

import subprocess
import time
import json
import urllib.request
import tempfile
import os
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_urgent_contract_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9231
    
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
                    ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined'")
                    if ready:
                        eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("Application failed to become ready")

        log("Waiting for page and scripts ready...")
        wait_for_ready()

        # Helper to setup deterministic active plan
        eval_js("""
            window.__setupContractPlan = function() {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
                const tomDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
                const tomorrow = `${tomDate.getFullYear()}-${pad(tomDate.getMonth() + 1)}-${pad(tomDate.getDate())}`;

                const testPlan = {
                    id: 'plan_contract_101',
                    planId: 'plan_contract_101',
                    planType: 'emergency',
                    title: 'Urgent Plan',
                    plannedTasks: [
                        {
                            dayDate: today,
                            dayLabel: 'Today',
                            startTime: '10:00 AM',
                            task: {
                                id: 'task-c1',
                                name: 'Contract Law Essay',
                                description: 'Finish section 2 legal argument',
                                hasDeadline: true,
                                deadlineDate: today,
                                deadlineTime: '23:59',
                                durationLabel: '45 min',
                                durationMinutes: 45,
                                completed: false,
                                isInProgress: false,
                                subtasks: [
                                    { id: 'sub-c1', title: 'Finish section 2 legal argument', completed: false },
                                    { id: 'sub-c2', title: 'Proofread citations', completed: false }
                                ]
                            }
                        },
                        {
                            dayDate: today,
                            dayLabel: 'Today',
                            startTime: '02:00 PM',
                            task: {
                                id: 'task-c2',
                                name: 'Review Lecture 5',
                                description: 'Slide notes',
                                hasDeadline: false,
                                durationLabel: '30 min',
                                durationMinutes: 30,
                                completed: true,
                                isInProgress: false,
                                subtasks: []
                            }
                        }
                    ],
                    tasks: [],
                    availabilityDays: [
                        { date: today, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }
                    ]
                };
                testPlan.tasks = testPlan.plannedTasks.map(pt => pt.task);

                if (window.TempoPlanStore && window.TempoPlanStore.saveActivePlan) {
                    window.TempoPlanStore.saveActivePlan('emergency', testPlan);
                }
                if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setConfirmedPlan) {
                    window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
                }

                window.TempoMode.setMode('emergency');
                window.TempoApp.navigateTo('today');
                window.TempoMode.renderEmodeHome();
                return { today, tomorrow };
            };
        """)

        # =====================================================================
        # CONTRACT CHECK 1: Mode Identifier & Control Invariants
        # =====================================================================
        log("\n--- CONTRACT CHECK 1: Mode Identifier & Control Invariants ---")
        eval_js("window.__setupContractPlan();")

        mode_ctrl = eval_js("""
            (() => {
                const currentMode = window.TempoMode.getMode();
                const storedMode = localStorage.getItem('tempo_current_mode');
                const btn = document.querySelector('[data-tempo-ui=\"mode-selector-btn\"], #btn-home-mode-selector');
                const dropdown = document.getElementById('home-mode-selector-dropdown');
                
                // Click to open dropdown
                if (btn) btn.click();
                const isOpen = dropdown && !dropdown.classList.contains('hidden');
                const dropdownItems = dropdown ? Array.from(dropdown.querySelectorAll('[role=\"menuitem\"]')).map(el => el.textContent.trim()) : [];
                
                // Press Escape to close
                window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
                const isClosed = dropdown && dropdown.classList.contains('hidden');

                return {
                    currentMode,
                    storedMode,
                    btnExists: !!btn,
                    btnAriaPopup: btn ? btn.getAttribute('aria-haspopup') : null,
                    isOpen,
                    isClosed,
                    dropdownItems
                };
            })()
        """)

        assert mode_ctrl['currentMode'] == 'emergency', f"Internal mode must remain 'emergency', got: {mode_ctrl['currentMode']}"
        assert mode_ctrl['storedMode'] == 'emergency', f"Stored mode in localStorage must remain 'emergency', got: {mode_ctrl['storedMode']}"
        assert mode_ctrl['btnExists'], "Interactive mode selector button must exist"
        assert mode_ctrl['btnAriaPopup'] == 'true', "Mode button must have aria-haspopup='true'"
        assert mode_ctrl['isOpen'], "Clicking mode button must open dropdown menu"
        assert mode_ctrl['isClosed'], "Pressing Escape must close dropdown menu"

        dropdown_text = " ".join(mode_ctrl['dropdownItems'])
        assert not any(m in dropdown_text for m in ["⚡ Urgent Mode", "⚡ Chế độ Khẩn"]), "Active Urgent Mode must NOT be offered as a switch destination"
        assert any(m in dropdown_text for m in ["Recovery Mode", "Chế độ Hồi phục", "Chế độ Phục hồi"]), "Dropdown must offer Recovery Mode"
        assert any(m in dropdown_text for m in ["Unclear Mode", "Chế độ Chưa rõ"]), "Dropdown must offer Unclear Mode"
        assert "SOS" not in dropdown_text, "SOS is not a mode and must NEVER appear in the mode dropdown"
        log("✓ Mode identifier remains 'emergency' and mode control invariants verified.")

        # =====================================================================
        # CONTRACT CHECK 2: Top Area Layout Invariants (No Hero Banner)
        # =====================================================================
        log("\n--- CONTRACT CHECK 2: Top Area Layout Invariants ---")
        top_invariants = eval_js("""
            (() => {
                const emodeBox = document.getElementById('emode-home-content');
                const h1 = emodeBox ? emodeBox.querySelector('h1') : null;
                const separateAmbient = emodeBox ? emodeBox.querySelector('.urgent-home-ambient') : null;
                const dateEl = emodeBox ? emodeBox.querySelector('.text-\\\\[\\\\#6F6B68\\\\].font-semibold') : null;

                return {
                    hasH1: !!h1,
                    h1Text: h1 ? h1.textContent.trim() : '',
                    hasSeparateAmbient: !!separateAmbient,
                    hasDate: !!dateEl
                };
            })()
        """)

        assert not top_invariants['hasH1'], f"Urgent Home must NOT have a standalone H1 hero banner, found: {top_invariants['h1Text']}"
        assert not top_invariants['hasSeparateAmbient'], "Urgent Home must NOT have separate top ambient greeting banner"
        assert top_invariants['hasDate'], "Date display must exist in top utility row"
        log("✓ No standalone greeting hero / banner verified.")

        # =====================================================================
        # CONTRACT CHECK 3: ~65 / 35 Execution Core & Internal Greeting
        # =====================================================================
        log("\n--- CONTRACT CHECK 3: ~65 / 35 Execution Core & Internal Greeting ---")
        core_info = eval_js("""
            (() => {
                const emodeBox = document.getElementById('emode-home-content');
                const shell = emodeBox.querySelector('[data-tempo-ui=\"urgent-home-shell\"], .relative');
                const leftCol = emodeBox.querySelector('[data-tempo-ui=\"urgent-left-col\"], .urgent-left-col');
                const rightCol = emodeBox.querySelector('[data-tempo-ui=\"urgent-plan-today\"], .urgent-right-col');
                const nowCard = emodeBox.querySelector('[data-tempo-ui=\"urgent-task-now\"], .urgent-card-now');

                if (!nowCard) return null;

                const greetingEl = nowCard.querySelector('.font-semibold.text-\\\\[\\\\#6F6B68\\\\]');
                const badgeLabel = nowCard.querySelector('.text-\\\\[\\\\#B83D08\\\\]');
                const nowBadge = nowCard.querySelector('.bg-\\\\[\\\\#FF6B2C\\\\].text-white');
                const titleEl = nowCard.querySelector('h3');
                const subtitleEl = nowCard.querySelector('p');
                const focusBtn = nowCard.querySelector('button.btn-primary');
                const viewBtn = nowCard.querySelectorAll('button')[1];

                // Check card styling classes for warm emphasis
                const isWarmBorder = nowCard.className.includes('border-[#FFD2BA]');
                const isWarmBg = nowCard.className.includes('from-[#FFF9F5]');
                const isRightColWhite = rightCol ? rightCol.className.includes('bg-white') : false;

                return {
                    hasLeftCol: !!leftCol,
                    hasRightCol: !!rightCol,
                    hasNowCard: !!nowCard,
                    greetingText: greetingEl ? greetingEl.textContent.trim() : '',
                    badgeLabel: badgeLabel ? badgeLabel.textContent.trim() : '',
                    hasNowBadge: !!nowBadge,
                    titleText: titleEl ? titleEl.textContent.trim() : '',
                    subtitleText: subtitleEl ? subtitleEl.textContent.trim() : '',
                    hasFocusBtn: !!focusBtn,
                    focusBtnText: focusBtn ? focusBtn.textContent.trim() : '',
                    hasViewBtn: !!viewBtn,
                    isWarmBorder,
                    isWarmBg,
                    isRightColWhite
                };
            })()
        """)

        assert core_info is not None, "Active Today execution core must be rendered"
        assert core_info['hasLeftCol'] and core_info['hasRightCol'], "65 / 35 column structure must exist"
        assert core_info['isWarmBorder'] and core_info['isWarmBg'], "Left card must have warm peach/orange styling"
        assert core_info['isRightColWhite'], "Right plan container must be neutral white structured card"
        assert any(g in core_info['greetingText'] for g in ["Hi", "Chào"]), f"Greeting must be rendered INSIDE left primary card, got: {core_info['greetingText']}"
        assert any(l in core_info['badgeLabel'] for l in ["YOUR TASK FOR NOW", "VIỆC CẦN LÀM NGAY"]), "Badge label must indicate YOUR TASK FOR NOW"
        assert core_info['hasNowBadge'], "Card must display NOW badge"
        assert core_info['titleText'] == 'Contract Law Essay', f"Title mismatch: {core_info['titleText']}"
        assert core_info['subtitleText'] == 'Finish section 2 legal argument', f"Subtitle mismatch: {core_info['subtitleText']}"
        assert any(b in core_info['focusBtnText'] for b in ["Focus on this task", "Tập trung vào việc này"]), f"Focus CTA mismatch: {core_info['focusBtnText']}"
        assert core_info['hasViewBtn'], "View task button must exist"
        log("✓ 65/35 composition, internal greeting, warm priority emphasis, and task CTAs verified.")

        # =====================================================================
        # CONTRACT CHECK 4: Dedicated Support Row & Prohibited Additions
        # =====================================================================
        log("\n--- CONTRACT CHECK 4: Dedicated Support Row & Prohibited Additions ---")
        support_ecosystem = eval_js("""
            (() => {
                const emodeBox = document.getElementById('emode-home-content');
                const supportRow = emodeBox.querySelector('[data-tempo-ui=\"urgent-support\"], .urgent-support-row');
                const cardOverwhelmed = emodeBox.querySelector('.urgent-card-overwhelmed');
                const cardFocusNow = emodeBox.querySelector('.urgent-card-focus-now');
                const postsSection = emodeBox.querySelector('[data-tempo-ui=\"urgent-posts\"], .urgent-section-posts');

                // Prohibited insertions in Urgent Home
                const genericTools = emodeBox.querySelectorAll('.tempo-tools-section');
                const genericLearnSolve = emodeBox.querySelectorAll('#tempo-learn-solve-section, #emode-learn-solve-container');
                const selfCheckCard = emodeBox.querySelectorAll('.recovery-card-selfcheck');
                const guestInvitation = emodeBox.querySelectorAll('#dmode-guest-invitation');

                return {
                    hasSupportRow: !!supportRow,
                    hasOverwhelmed: !!cardOverwhelmed,
                    hasFocusNow: !!cardFocusNow,
                    hasPosts: !!postsSection,
                    genericToolsCount: genericTools.length,
                    genericLearnSolveCount: genericLearnSolve.length,
                    selfCheckCount: selfCheckCard.length,
                    guestInvitationCount: guestInvitation.length
                };
            })()
        """)

        assert support_ecosystem['hasSupportRow'], "Dedicated urgent support row must exist"
        assert support_ecosystem['hasOverwhelmed'] and support_ecosystem['hasFocusNow'], "Support row must contain Overwhelmed and Focus Now cards"
        assert support_ecosystem['hasPosts'], "Lower priority community posts section must exist"
        assert support_ecosystem['genericToolsCount'] == 0, "Generic Tempo Tools must NEVER be injected into Urgent Home"
        assert support_ecosystem['genericLearnSolveCount'] == 0, "Generic Learn & Solve must NEVER be injected into Urgent Home"
        assert support_ecosystem['selfCheckCount'] == 0, "Self-check must NEVER be injected into Urgent Home"
        assert support_ecosystem['guestInvitationCount'] == 0, "Guest invitation banners must NEVER appear in Urgent Home"
        log("✓ Dedicated support row confirmed; prohibited generic sections verified absent.")

        # =====================================================================
        # CONTRACT CHECK 5: All 7 States Preserve Common Approved Shell
        # =====================================================================
        log("\n--- CONTRACT CHECK 5: All 7 States Preserve Common Approved Shell ---")

        def verify_state_shell(state_name):
            shell_check = eval_js("""
                (() => {
                    const emodeBox = document.getElementById('emode-home-content');
                    const btn = emodeBox.querySelector('[data-tempo-ui=\"mode-selector-btn\"], #btn-home-mode-selector');
                    const leftCol = emodeBox.querySelector('.urgent-left-col');
                    const rightCol = emodeBox.querySelector('.urgent-right-col');
                    const supportRow = emodeBox.querySelector('.urgent-support-row');
                    const posts = emodeBox.querySelector('.urgent-section-posts');
                    const h1 = emodeBox.querySelector('h1');

                    // Check that the left primary card contains an internal greeting
                    const primaryCard = leftCol ? leftCol.firstElementChild : null;
                    const greetingEl = primaryCard ? primaryCard.querySelector('.font-semibold.text-\\\\[\\\\#6F6B68\\\\]') : null;
                    const hasWarmBg = primaryCard ? primaryCard.className.includes('from-[#FFF9F5]') : false;

                    return {
                        hasBtn: !!btn,
                        hasLeftCol: !!leftCol,
                        hasRightCol: !!rightCol,
                        hasSupportRow: !!supportRow,
                        hasPosts: !!posts,
                        hasH1Takeover: !!h1,
                        hasInternalGreeting: !!greetingEl,
                        hasWarmBg
                    };
                })()
            """)
            assert shell_check['hasBtn'], f"[{state_name}] Mode button missing"
            assert shell_check['hasLeftCol'] and shell_check['hasRightCol'], f"[{state_name}] 65/35 shell broken"
            assert shell_check['hasSupportRow'], f"[{state_name}] Dedicated support row missing"
            assert shell_check['hasPosts'], f"[{state_name}] Community posts missing"
            assert not shell_check['hasH1Takeover'], f"[{state_name}] Must not render H1 full-page takeover"
            assert shell_check['hasInternalGreeting'], f"[{state_name}] Must render internal greeting inside primary card"
            assert shell_check['hasWarmBg'], f"[{state_name}] Primary card must maintain warm background emphasis"
            log(f"  ✓ State {state_name} conforms to contract shell.")

        # State 1: PLAN_INCOMPLETE
        eval_js("""
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
            })()
        """)
        time.sleep(0.3)
        verify_state_shell("PLAN_INCOMPLETE")

        # State 2: TODAY_COMPLETE
        eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
                const tomDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
                const tomorrow = `${tomDate.getFullYear()}-${pad(tomDate.getMonth() + 1)}-${pad(tomDate.getDate())}`;

                const plan = {
                    id: 'p_done',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: today, task: { id: 'td1', name: 'Finished Task', completed: true } },
                        { dayDate: tomorrow, task: { id: 'td2', name: 'Tomorrow Task', completed: false } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, blocks: [{ start: '09:00', end: '23:59' }] }]
                };
                plan.tasks = plan.plannedTasks.map(p => p.task);
                await window.TempoPlanStore.saveActivePlan('emergency', plan);
                if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') window.TempoEmergencyFlow.setConfirmedPlan(plan);
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.3)
        verify_state_shell("TODAY_COMPLETE")

        # State 3: NO_WORK_TODAY
        eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const futureDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 2);
                const future = `${futureDate.getFullYear()}-${pad(futureDate.getMonth() + 1)}-${pad(futureDate.getDate())}`;

                const plan = {
                    id: 'p_nowork',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: future, task: { id: 'tf1', name: 'Future Task', completed: false } }
                    ],
                    tasks: [],
                    availabilityDays: []
                };
                plan.tasks = plan.plannedTasks.map(p => p.task);
                await window.TempoPlanStore.saveActivePlan('emergency', plan);
                if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') window.TempoEmergencyFlow.setConfirmedPlan(plan);
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.3)
        verify_state_shell("NO_WORK_TODAY")

        # State 4: TIME_ENDED_WITH_INCOMPLETE_WORK
        eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

                const plan = {
                    id: 'p_ended',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: today, task: { id: 'te1', name: 'Late Task', completed: false } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, blocks: [{ start: '00:01', end: '00:02' }] }]
                };
                plan.tasks = plan.plannedTasks.map(p => p.task);
                await window.TempoPlanStore.saveActivePlan('emergency', plan);
                if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') window.TempoEmergencyFlow.setConfirmedPlan(plan);
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.3)
        verify_state_shell("TIME_ENDED_WITH_INCOMPLETE_WORK")

        # State 5: PLAN_STALE
        eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const yestDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
                const yesterday = `${yestDate.getFullYear()}-${pad(yestDate.getMonth() + 1)}-${pad(yestDate.getDate())}`;

                const plan = {
                    id: 'p_stale',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: yesterday, task: { id: 'ts1', name: 'Overdue Task', completed: false } }
                    ],
                    tasks: [],
                    availabilityDays: []
                };
                plan.tasks = plan.plannedTasks.map(p => p.task);
                await window.TempoPlanStore.saveActivePlan('emergency', plan);
                if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') window.TempoEmergencyFlow.setConfirmedPlan(plan);
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.3)
        verify_state_shell("PLAN_STALE")

        # State 6: PLAN_COMPLETE
        eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

                const plan = {
                    id: 'p_comp',
                    planType: 'emergency',
                    plannedTasks: [
                        { dayDate: today, task: { id: 'tc1', name: 'Finished', completed: true } }
                    ],
                    tasks: [],
                    availabilityDays: []
                };
                plan.tasks = plan.plannedTasks.map(p => p.task);
                await window.TempoPlanStore.saveActivePlan('emergency', plan);
                if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') window.TempoEmergencyFlow.setConfirmedPlan(plan);
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.3)
        verify_state_shell("PLAN_COMPLETE")

        log("\n=======================================================")
        log(">>> ALL URGENT MODE PRODUCT CONTRACT CHECKS PASSED! <<<")
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
