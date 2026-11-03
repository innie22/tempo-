import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.parse
from websocket import create_connection

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PORT = 9430
USER_DATA = r"C:\Users\YEN NHI\AppData\Local\Temp\edge_test_wp_fix"
ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"

def start_edge():
    cmd = [
        EDGE_PATH,
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={USER_DATA}",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--disable-fre",
        "--disable-sync",
        "--no-default-browser-check",
        "--window-size=1280,2400",
        "http://127.0.0.1:8000/#recovery"
    ]
    return subprocess.Popen(cmd)

def send_cdp(ws, method, params=None, msg_id=[1]):
    m = {"id": msg_id[0], "method": method, "params": params or {}}
    msg_id[0] += 1
    ws.send(json.dumps(m))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == m["id"]:
            return resp

def evaluate_js(ws, expr):
    res = send_cdp(ws, "Runtime.evaluate", {
        "expression": expr,
        "returnByValue": True,
        "awaitPromise": True
    })
    if "exceptionDetails" in res.get("result", {}):
        print("JS Exception:", res["result"]["exceptionDetails"])
    if "result" in res and "result" in res["result"]:
        return res["result"]["result"].get("value")
    return None

def capture_screenshot(ws, clip, file_path):
    params = {"format": "png"}
    if clip:
        params["clip"] = clip
    res = send_cdp(ws, "Page.captureScreenshot", params)
    if "result" in res and "data" in res["result"]:
        import base64
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(res["result"]["data"]))
        print(f"Saved screenshot: {file_path}")

def run_tests():
    print("Starting Edge on port", PORT)
    proc = start_edge()
    time.sleep(2)

    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json")
        tabs = json.loads(req.read().decode())
        page_tabs = [t for t in tabs if t.get("type") == "page" and "8000" in t.get("url", "")]
        target = page_tabs[0] if page_tabs else [t for t in tabs if t.get("type") == "page"][0]
        ws_url = target["webSocketDebuggerUrl"]
        print("Connecting to CDP target:", target.get("url"))
        ws = create_connection(ws_url)

        send_cdp(ws, "Page.enable")
        send_cdp(ws, "Runtime.enable")
        time.sleep(1)

        for _ in range(20):
            ready = evaluate_js(ws, "Boolean(window.TempoAuth && window.TempoMode && window.TempoPlanStore)")
            if ready:
                break
            time.sleep(0.5)

        print("\n=== TEST 1: New Account with No Working Plan in Rmode Dashboard ===")
        # Register a brand new user and sign in
        setup_user = evaluate_js(ws, """
            (async () => {
                // Clear any stored state for clean account test
                localStorage.clear();
                sessionStorage.clear();
                
                const email = 'newuser_clean@fpt.edu.vn';
                const pass = 'Password123!';
                const name = 'Clean Student';
                
                // Register and Sign in
                await window.TempoAuth.register(name, email, pass);
                await window.TempoAuth.signIn(email, pass);
                
                // Ensure in Recovery Mode
                window.TempoMode.setMode('recovery');
                window.TempoApp.navigateTo('recovery-mode');
                if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.handleCase1Later === 'function') {
                    window.TempoRecoverySetup.handleCase1Later();
                }
                window.TempoMode.renderRmodeHome();
                
                const user = window.TempoAuth.getCurrentUser();
                return {
                    signedIn: !!user,
                    email: user ? user.email : null,
                    mode: window.TempoMode.getMode()
                };
            })()
        """)
        print("User setup status:", setup_user)
        time.sleep(0.5)

        # Inspect Rmode Working Plan card
        wp_status = evaluate_js(ws, """
            (() => {
                const wpCard = document.getElementById('recovery-working-plan') || document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                if (!wpCard) return { exists: false };
                
                const text = wpCard.innerText || '';
                const has67 = text.includes('67%');
                const hasMarketingResearch = text.includes('Marketing Research');
                const hasEventProposal = text.includes('Event Proposal');
                const hasEditVideo = text.includes('Edit Video');
                const hasOverdueWarning = text.includes('TRỄ DEADLINE') || text.includes('OVERDUE') || text.includes('TASK QUÁ LỊCH');
                const hasEmptyState = text.includes('Bạn chưa có Kế hoạch làm việc') || text.includes('No Working Plan yet');
                const hasCreateBtn = text.includes('Tạo plan') || text.includes('Create Plan') || text.includes('Tạo Kế hoạch làm việc');
                const taskCards = wpCard.querySelectorAll('.recovery-task-card-group, [data-task-id]');
                const progressBars = wpCard.querySelectorAll('[class*="bg-[#D79277]"]');
                
                const rect = wpCard.getBoundingClientRect();
                return {
                    exists: true,
                    text: text,
                    has67,
                    hasMarketingResearch,
                    hasEventProposal,
                    hasEditVideo,
                    hasOverdueWarning,
                    hasEmptyState,
                    hasCreateBtn,
                    taskCardCount: taskCards.length,
                    progressBarCount: progressBars.length,
                    clip: { x: Math.max(0, rect.x), y: Math.max(0, rect.y), width: rect.width, height: rect.height, scale: 1 }
                };
            })()
        """)
        print("Working Plan card status in clean account:", json.dumps(wp_status, indent=2))
        assert wp_status["exists"] == True, "Working plan card must exist in Rmode"
        assert wp_status["has67"] == False, "Must NOT show 67% progress"
        assert wp_status["hasMarketingResearch"] == False, "Must NOT show dummy Marketing Research task"
        assert wp_status["hasEventProposal"] == False, "Must NOT show dummy Event Proposal task"
        assert wp_status["hasEditVideo"] == False, "Must NOT show dummy Edit Video task"
        assert wp_status["hasOverdueWarning"] == False, "Must NOT show fabricated overdue warning"
        assert wp_status["taskCardCount"] == 0, "Must have 0 task cards"
        assert wp_status["hasEmptyState"] == True, "Must show supportive empty state"
        assert wp_status["hasCreateBtn"] == True, "Must provide voluntary Create Plan button"

        capture_screenshot(ws, wp_status["clip"], os.path.join(ARTIFACT_DIR, "rmode_wp_clean_account_vi.png"))
        print("✓ TEST 1 PASSED: Brand-new account displays 0 tasks, 0 fabricated progress, and clean empty state!")

        print("\n=== TEST 2: Language Switching (English) for Clean Account ===")
        evaluate_js(ws, "window.TempoI18n.setLanguage('en'); window.TempoMode.renderRmodeHome();")
        time.sleep(0.5)

        wp_en_status = evaluate_js(ws, """
            (() => {
                const wpCard = document.getElementById('recovery-working-plan');
                const text = wpCard ? (wpCard.innerText || '') : '';
                const rect = wpCard ? wpCard.getBoundingClientRect() : { x: 0, y: 0, width: 0, height: 0 };
                return {
                    hasEnTitle: text.includes('No Working Plan yet'),
                    hasEnCreateBtn: text.includes('Create Plan') || text.includes('Create a Working Plan'),
                    has67: text.includes('67%'),
                    taskCardCount: wpCard ? wpCard.querySelectorAll('.recovery-task-card-group, [data-task-id]').length : 0,
                    clip: { x: Math.max(0, rect.x), y: Math.max(0, rect.y), width: rect.width, height: rect.height, scale: 1 }
                };
            })()
        """)
        print("Working Plan status in EN mode:", wp_en_status)
        assert wp_en_status["hasEnTitle"] == True, "Must show 'No Working Plan yet' in EN"
        assert wp_en_status["hasEnCreateBtn"] == True, "Must show Create Plan in EN"
        assert wp_en_status["has67"] == False, "Must NOT show 67% in EN"
        assert wp_en_status["taskCardCount"] == 0, "Must have 0 tasks in EN"

        capture_screenshot(ws, wp_en_status["clip"], os.path.join(ARTIFACT_DIR, "rmode_wp_clean_account_en.png"))
        print("✓ TEST 2 PASSED: English empty state rendered cleanly!")

        # Reset language to Vietnamese
        evaluate_js(ws, "window.TempoI18n.setLanguage('vi'); window.TempoMode.renderRmodeHome();")
        time.sleep(0.5)

        print("\n=== TEST 3: Account with a Legitimate Working Plan (Case 2) ===")
        # Save a legitimate plan for this user (2 tasks, 1 completed)
        save_legit_plan = evaluate_js(ws, """
            (async () => {
                const todayStr = '2026-11-02';
                const legitimatePlan = {
                    id: 'plan_legit_user',
                    planId: 'plan_legit_user',
                    title: 'Kế hoạch học tập cá nhân',
                    plannedTasks: [
                        {
                            id: 'user-task-defense',
                            dayDate: todayStr,
                            dayLabel: 'Hôm nay',
                            startTime: '09:00',
                            endTime: '10:30',
                            executionBadge: 'Now',
                            task: {
                                id: 'user-task-defense',
                                name: 'Chuẩn bị slide báo cáo Đồ án',
                                deadlineDate: '2026-11-15',
                                deadlineTime: '17:00',
                                completed: false,
                                subtasks: [
                                    { id: 'sub-1', title: 'Slide mở đầu', completed: false }
                                ]
                            }
                        },
                        {
                            id: 'user-task-survey',
                            dayDate: todayStr,
                            dayLabel: 'Hôm nay',
                            startTime: '14:00',
                            endTime: '15:00',
                            executionBadge: 'Then',
                            task: {
                                id: 'user-task-survey',
                                name: 'Gửi khảo sát người dùng thực tế',
                                deadlineDate: '2026-11-10',
                                deadlineTime: '21:00',
                                completed: true,
                                subtasks: []
                            }
                        }
                    ]
                };
                
                await window.TempoPlanStore.saveActivePlan('emergency', legitimatePlan);
                await window.TempoPlanStore.saveActivePlan('recovery', legitimatePlan);
                if (window.TempoEmergencyFlow) {
                    window.TempoEmergencyFlow.setConfirmedPlan(legitimatePlan);
                }
                window.TempoMode.renderRmodeHome();
                return true;
            })()
        """)
        print("Saved legitimate plan:", save_legit_plan)
        time.sleep(0.5)

        legit_status = evaluate_js(ws, """
            (() => {
                const wpCard = document.getElementById('recovery-working-plan');
                const text = wpCard ? (wpCard.innerText || '') : '';
                const taskCards = wpCard ? wpCard.querySelectorAll('.recovery-task-card-group, [data-task-id]') : [];
                const hasTask1 = text.includes('Chuẩn bị slide báo cáo Đồ án');
                const hasTask2 = text.includes('Gửi khảo sát người dùng thực tế');
                const has50Percent = text.includes('50%') || text.includes('1/2 task');
                const hasOverdue = text.includes('TRỄ DEADLINE');
                const hasEditBtn = text.includes('Sửa plan');
                
                const rect = wpCard.getBoundingClientRect();
                return {
                    taskCardCount: taskCards.length,
                    hasTask1,
                    hasTask2,
                    has50Percent,
                    hasOverdue,
                    hasEditBtn,
                    clip: { x: Math.max(0, rect.x), y: Math.max(0, rect.y), width: rect.width, height: rect.height, scale: 1 }
                };
            })()
        """)
        print("Legitimate Working Plan status:", json.dumps(legit_status, indent=2))
        assert legit_status["taskCardCount"] == 2, "Must show exactly 2 tasks"
        assert legit_status["hasTask1"] == True, "Must show legitimate task 1"
        assert legit_status["hasTask2"] == True, "Must show legitimate task 2"
        assert legit_status["has50Percent"] == True, "Must display 1/2 task (50%)"
        assert legit_status["hasOverdue"] == False, "Must NOT show overdue because deadlines are in the future"
        assert legit_status["hasEditBtn"] == True, "Must show 'Sửa plan' button"

        capture_screenshot(ws, legit_status["clip"], os.path.join(ARTIFACT_DIR, "rmode_wp_legitimate_account_vi.png"))
        print("✓ TEST 3 PASSED: Case 2 accurately displays real user tasks and 50% completion progress!")

        print("\n=== TEST 4: Account Isolation (User A's tasks NEVER leak to User B) ===")
        isolation_status = evaluate_js(ws, """
            (async () => {
                // Sign out Clean Student
                window.TempoAuth.handleSignOut();
                
                // Register a new independent user
                const emailOther = 'user_other@fpt.edu.vn';
                const passOther = 'Password123!';
                const nameOther = 'Independent Student';
                
                await window.TempoAuth.register(nameOther, emailOther, passOther);
                await window.TempoAuth.signIn(emailOther, passOther);
                
                window.TempoMode.setMode('recovery');
                window.TempoApp.navigateTo('recovery-mode');
                window.TempoMode.renderRmodeHome();
                
                const wpCard = document.getElementById('recovery-working-plan');
                const text = wpCard ? (wpCard.innerText || '') : '';
                const taskCards = wpCard ? wpCard.querySelectorAll('.recovery-task-card-group, [data-task-id]') : [];
                
                return {
                    newUser: window.TempoAuth.getCurrentUser() ? window.TempoAuth.getCurrentUser().email : null,
                    taskCardCount: taskCards.length,
                    hasPreviousUserTask: text.includes('Chuẩn bị slide báo cáo Đồ án'),
                    hasEmptyState: text.includes('Bạn chưa có Kế hoạch làm việc'),
                    has67: text.includes('67%'),
                    has50: text.includes('50%')
                };
            })()
        """)
        print("Isolation test status:", json.dumps(isolation_status, indent=2))
        assert isolation_status["taskCardCount"] == 0, "New user must have 0 tasks"
        assert isolation_status["hasPreviousUserTask"] == False, "Previous user tasks must NOT leak to new user"
        assert isolation_status["hasEmptyState"] == True, "New user must see empty state"
        assert isolation_status["has67"] == False, "No fabricated progress"
        assert isolation_status["has50"] == False, "No previous progress"
        print("✓ TEST 4 PASSED: Account isolation verified! Tasks do not leak across sessions or accounts!")

        print("\n=== TEST 5: Mode Switching does NOT generate unauthorized tasks ===")
        mode_switch_status = evaluate_js(ws, """
            (() => {
                // Switch to Urgent mode and back to Recovery mode
                window.TempoMode.setMode('emergency');
                window.TempoMode.setMode('recovery');
                window.TempoApp.navigateTo('recovery-mode');
                window.TempoMode.renderRmodeHome();
                
                const wpCard = document.getElementById('recovery-working-plan');
                const text = wpCard ? (wpCard.innerText || '') : '';
                const taskCards = wpCard ? wpCard.querySelectorAll('.recovery-task-card-group, [data-task-id]') : [];
                
                return {
                    taskCardCount: taskCards.length,
                    hasEmptyState: text.includes('Bạn chưa có Kế hoạch làm việc'),
                    has67: text.includes('67%'),
                    hasMarketing: text.includes('Marketing Research')
                };
            })()
        """)
        print("Mode switch test status:", json.dumps(mode_switch_status, indent=2))
        assert mode_switch_status["taskCardCount"] == 0, "Must maintain 0 tasks after mode switch"
        assert mode_switch_status["hasEmptyState"] == True, "Must maintain empty state"
        assert mode_switch_status["has67"] == False, "Must NOT show 67%"
        assert mode_switch_status["hasMarketing"] == False, "Must NOT show dummy marketing research"
        print("✓ TEST 5 PASSED: Mode switching never auto-generates tasks!")

        print("\n=======================================================")
        print("ALL CRITICAL WORKING PLAN INVESTIGATION & FIX TESTS PASSED (100%)")
        print("=======================================================")

    finally:
        try:
            ws.close()
        except:
            pass
        proc.kill()

if __name__ == '__main__':
    run_tests()
