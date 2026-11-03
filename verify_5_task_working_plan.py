import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import base64
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"

def main():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_5_tasks_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9410
    
    cmd = [
        edge_path,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "--window-size=1440,900",
        "http://localhost:8000/"
    ]
    
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
            raise RuntimeError("Failed to connect to CDP")
            
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

        def capture_element(selector, filename):
            box = eval_js(f"""
                (() => {{
                    const el = document.querySelector('{selector}');
                    if (!el) return null;
                    const r = el.getBoundingClientRect();
                    return {{ x: r.left, y: r.top, width: r.width, height: r.height }};
                }})()
            """)
            if not box:
                print(f"Could not find element {selector}")
                return
            clip = {
                "x": box["x"],
                "y": box["y"],
                "width": box["width"],
                "height": box["height"],
                "scale": 1
            }
            res = send_command("Page.captureScreenshot", {"clip": clip, "format": "png"})
            with open(os.path.join(ARTIFACT_DIR, filename), "wb") as f:
                f.write(base64.b64decode(res["data"]))
            print(f"Captured: {filename} ({box['width']}x{box['height']})")

        for _ in range(40):
            try:
                ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined' && typeof window.TempoEmergencyFlow !== 'undefined'")
                if ready:
                    break
            except Exception:
                pass
            time.sleep(0.5)

        # -------------------------------------------------------------
        # 1. SETUP 5-TASK PLAN (2 Tasks Today, 3 Tasks Tomorrow)
        # -------------------------------------------------------------
        print("\n--- SETTING UP USER PLAN WITH 5 TASKS (2 TODAY, 3 TOMORROW) ---")
        eval_js("""
            (() => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
                const tomDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
                const tomorrow = `${tomDate.getFullYear()}-${pad(tomDate.getMonth() + 1)}-${pad(tomDate.getDate())}`;

                const fiveTaskPlan = {
                    id: 'plan_user_5_tasks',
                    planId: 'plan_user_5_tasks',
                    planType: 'emergency',
                    title: 'Urgent Mode Plan',
                    plannedTasks: [
                        {
                            dayDate: today,
                            dayLabel: 'Today',
                            startTime: '10:00 AM',
                            endTime: '11:30 AM',
                            executionBadge: 'DO THIS FIRST',
                            task: {
                                id: 'task-5-1',
                                name: 'Marketing Report Final Analysis',
                                description: 'Finish competitor analysis section',
                                hasDeadline: true,
                                deadlineDate: today,
                                deadlineTime: '22:00',
                                durationLabel: '1h 30m',
                                durationMinutes: 90,
                                completed: false,
                                isInProgress: true,
                                subtasks: [
                                    { id: 'sub-1', title: 'Competitor benchmarking', completed: true },
                                    { id: 'sub-2', title: 'Market share graph', completed: false }
                                ]
                            }
                        },
                        {
                            dayDate: today,
                            dayLabel: 'Today',
                            startTime: '02:00 PM',
                            endTime: '02:45 PM',
                            executionBadge: 'THEN',
                            task: {
                                id: 'task-5-2',
                                name: 'Read Biology Chapter 4',
                                description: 'Read pages 120-145 and review summary',
                                hasDeadline: false,
                                durationLabel: '45 min',
                                durationMinutes: 45,
                                completed: true,
                                isInProgress: false,
                                subtasks: []
                            }
                        },
                        {
                            dayDate: tomorrow,
                            dayLabel: 'Tomorrow',
                            startTime: '09:00 AM',
                            endTime: '10:00 AM',
                            executionBadge: 'DO THIS FIRST',
                            task: {
                                id: 'task-5-3',
                                name: 'Prepare Presentation Slides',
                                description: 'Create 5 slides with key insights',
                                hasDeadline: true,
                                deadlineDate: tomorrow,
                                deadlineTime: '15:00',
                                durationLabel: '1 hr',
                                durationMinutes: 60,
                                completed: false,
                                isInProgress: false,
                                subtasks: []
                            }
                        },
                        {
                            dayDate: tomorrow,
                            dayLabel: 'Tomorrow',
                            startTime: '10:30 AM',
                            endTime: '11:45 AM',
                            executionBadge: 'THEN',
                            task: {
                                id: 'task-5-4',
                                name: 'Statistics Lab Writeup',
                                description: 'Calculate confidence intervals and write conclusions',
                                hasDeadline: false,
                                durationLabel: '1h 15m',
                                durationMinutes: 75,
                                completed: false,
                                isInProgress: false,
                                subtasks: []
                            }
                        },
                        {
                            dayDate: tomorrow,
                            dayLabel: 'Tomorrow',
                            startTime: '02:00 PM',
                            endTime: '03:00 PM',
                            executionBadge: 'LATER',
                            task: {
                                id: 'task-5-5',
                                name: 'Weekly Reflection & Synthesis',
                                description: 'Write one-page reflection on project deliverables',
                                hasDeadline: false,
                                durationLabel: '1 hr',
                                durationMinutes: 60,
                                completed: false,
                                isInProgress: false,
                                subtasks: []
                            }
                        }
                    ],
                    tasks: [],
                    availabilityDays: [
                        { date: today, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] },
                        { date: tomorrow, label: 'Tomorrow', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }
                    ]
                };
                fiveTaskPlan.tasks = fiveTaskPlan.plannedTasks.map(pt => pt.task);

                window.TempoPlanStore.saveActivePlan('emergency', fiveTaskPlan);
                window.TempoEmergencyFlow.setConfirmedPlan(fiveTaskPlan);
                window.TempoEmergencyFlow.restorePlanState();
                window.TempoMode.setMode('emergency');
                window.TempoApp.navigateTo('today');
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.5)

        # -------------------------------------------------------------
        # 2. VERIFY INITIAL RENDER (ALL 5 TASKS, 1 OF 5 COMPLETED, FIXED 388px)
        # -------------------------------------------------------------
        metrics = eval_js("""
            (() => {
                const card = document.querySelector('.urgent-working-plan-card');
                const scroll = document.querySelector('.urgent-working-plan-tasks-scroll');
                const header = card ? card.querySelector('.shrink-0') : null;
                const progressTextEl = card ? card.querySelector('.shrink-0 .text-\\\\[\\\\#6F6B68\\\\].font-medium') : null;
                const percentEl = card ? card.querySelector('.shrink-0 .font-bold.text-\\\\[\\\\#202124\\\\]') : null;
                const items = card ? card.querySelectorAll('.urgent-timeline-item') : [];

                const itemData = [];
                items.forEach(el => {
                    const h4 = el.querySelector('h4');
                    const badge = el.querySelector('span[class*=\"rounded-full\"]');
                    const isDone = h4 ? h4.classList.contains('line-through') : false;
                    itemData.push({
                        title: h4 ? h4.textContent.trim() : '',
                        isDone,
                        badge: badge ? badge.textContent.trim() : ''
                    });
                });

                const bcr = card.getBoundingClientRect();
                const bcrHeader = header.getBoundingClientRect();

                return {
                    cardHeight: bcr.height,
                    cardWidth: bcr.width,
                    headerHeight: bcrHeader.height,
                    headerTop: bcrHeader.top,
                    progressText: progressTextEl ? progressTextEl.textContent.trim() : '',
                    percentageText: percentEl ? percentEl.textContent.trim() : '',
                    taskCount: items.length,
                    itemData,
                    scrollClientHeight: scroll.clientHeight,
                    scrollScrollHeight: scroll.scrollHeight,
                    isScrollable: scroll.scrollHeight > scroll.clientHeight,
                    scrollTop: scroll.scrollTop
                };
            })()
        """)
        print("Initial 5-task Working Plan Metrics:", json.dumps(metrics, indent=2))

        # Check total task count is 5
        assert metrics['taskCount'] == 5, f"Expected exactly 5 tasks rendered, got {metrics['taskCount']}"
        print("✓ Verified all 5 tasks are rendered in the working plan.")

        # Check progress text indicates 1 of 5 completed
        assert any(p in metrics['progressText'] for p in ["1 of 5 completed", "1/5 hoàn thành", "1/5 đã hoàn thành"]), f"Progress text should be '1 of 5 completed', got: {metrics['progressText']}"
        assert metrics['percentageText'] == '20%', f"Percentage should be 20%, got {metrics['percentageText']}"
        print("✓ Verified progress summary accurately counts complete plan (1 of 5 completed, 20%).")

        # Check task order and status badges
        assert metrics['itemData'][0]['title'] == 'Marketing Report Final Analysis' and metrics['itemData'][0]['badge'] in ['NOW', 'ĐANG LÀM', 'Đang làm']
        assert metrics['itemData'][1]['title'] == 'Read Biology Chapter 4' and metrics['itemData'][1]['isDone'] and metrics['itemData'][1]['badge'] in ['Completed', 'Đã xong', 'Đã hoàn thành', 'Hoàn thành']
        assert metrics['itemData'][2]['title'] == 'Prepare Presentation Slides' and metrics['itemData'][2]['badge'] in ['UP NEXT', 'TIẾP THEO', 'Tiếp theo']
        assert metrics['itemData'][3]['title'] == 'Statistics Lab Writeup' and metrics['itemData'][3]['badge'] in ['UP NEXT', 'TIẾP THEO', 'Tiếp theo']
        assert metrics['itemData'][4]['title'] == 'Weekly Reflection & Synthesis' and metrics['itemData'][4]['badge'] in ['UP NEXT', 'TIẾP THEO', 'Tiếp theo']
        print("✓ Verified task order and badges ('NOW', 'Completed', 'UP NEXT' across all 5 tasks).")

        # Check card height fixed at 388px
        assert abs(metrics['cardHeight'] - 388.0) <= 1.0, f"Card height must be 388px, got {metrics['cardHeight']}"
        assert metrics['isScrollable'], "5 tasks should exceed the viewport height of the scroll container"
        print("✓ Verified outer card height is fixed at exactly 388px and task list is scrollable.")

        capture_element('.urgent-working-plan-card', "working_plan_5_tasks_scroll_top.png")

        # -------------------------------------------------------------
        # 3. SCROLL TO BOTTOM AND VERIFY STATIONARY HEADER & TASK 5 VISIBILITY
        # -------------------------------------------------------------
        print("\n--- SCROLLING TO BOTTOM ---")
        scroll_res = eval_js("""
            (() => {
                const card = document.querySelector('.urgent-working-plan-card');
                const scroll = document.querySelector('.urgent-working-plan-tasks-scroll');
                const header = card.querySelector('.shrink-0');
                const beforeHeaderTop = header.getBoundingClientRect().top;

                scroll.scrollTop = scroll.scrollHeight;
                const afterHeaderTop = header.getBoundingClientRect().top;
                const items = card.querySelectorAll('.urgent-timeline-item');
                const lastItem = items[items.length - 1];
                const rLast = lastItem.getBoundingClientRect();
                const rScroll = scroll.getBoundingClientRect();

                const isLastVisible = rLast.bottom <= rScroll.bottom + 5 && rLast.top >= rScroll.top - 5;

                return {
                    beforeHeaderTop,
                    afterHeaderTop,
                    headerStationary: Math.abs(beforeHeaderTop - afterHeaderTop) < 0.5,
                    scrollTop: scroll.scrollTop,
                    lastTaskTitle: lastItem.querySelector('h4').textContent.trim(),
                    isLastVisible,
                    cardHeight: card.getBoundingClientRect().height
                };
            })()
        """)
        print("Scroll-to-bottom metrics:", json.dumps(scroll_res, indent=2))
        assert scroll_res['headerStationary'], "Header and progress section must remain completely stationary when scrolling"
        assert abs(scroll_res['cardHeight'] - 388.0) <= 1.0, f"Card height must remain 388px while scrolled, got {scroll_res['cardHeight']}"
        assert scroll_res['lastTaskTitle'] == 'Weekly Reflection & Synthesis', "Last task must be Task 5"
        print("✓ Header remained stationary and Task 5 is accessible via scrolling.")

        capture_element('.urgent-working-plan-card', "working_plan_5_tasks_scroll_bottom.png")

        # -------------------------------------------------------------
        # 4. TOGGLE TASK 5 COMPLETION AND VERIFY PROGRESS UPDATES
        # -------------------------------------------------------------
        print("\n--- TOGGLING TASK 5 COMPLETION ---")
        toggled_metrics = eval_js("""
            (() => {
                // Click task-5-5 to toggle completion
                window.TempoMode.toggleTaskCompletion('task-5-5');
                const card = document.querySelector('.urgent-working-plan-card');
                const progressTextEl = card.querySelector('.shrink-0 .text-\\\\[\\\\#6F6B68\\\\].font-medium');
                const percentEl = card.querySelector('.shrink-0 .font-bold.text-\\\\[\\\\#202124\\\\]');
                const items = card.querySelectorAll('.urgent-timeline-item');
                const lastItem = items[items.length - 1];
                const h4 = lastItem.querySelector('h4');
                const badge = lastItem.querySelector('span[class*=\"rounded-full\"]');

                return {
                    cardHeight: card.getBoundingClientRect().height,
                    progressText: progressTextEl ? progressTextEl.textContent.trim() : '',
                    percentageText: percentEl ? percentEl.textContent.trim() : '',
                    isLastDone: h4 ? h4.classList.contains('line-through') : false,
                    lastBadge: badge ? badge.textContent.trim() : ''
                };
            })()
        """)
        print("After toggling Task 5:", json.dumps(toggled_metrics, indent=2))
        assert any(p in toggled_metrics['progressText'] for p in ["2 of 5 completed", "2/5 hoàn thành", "2/5 đã hoàn thành"]), f"Expected 2 of 5 completed, got: {toggled_metrics['progressText']}"
        assert toggled_metrics['percentageText'] == '40%', f"Expected 40%, got: {toggled_metrics['percentageText']}"
        assert toggled_metrics['isLastDone'], "Task 5 should have strikethrough"
        assert toggled_metrics['lastBadge'] in ['Completed', 'Đã xong', 'Đã hoàn thành', 'Hoàn thành'], f"Task 5 badge should be Completed, got: {toggled_metrics['lastBadge']}"
        assert abs(toggled_metrics['cardHeight'] - 388.0) <= 1.0, "Card height must stay 388px after dynamic update"
        print("✓ Dynamic update verified: progress counter updated to 2 of 5 completed (40%), Task 5 marked completed.")

        capture_element('.urgent-working-plan-card', "working_plan_5_tasks_toggled.png")

        # Capture full live desktop screenshot
        shot_full = send_command("Page.captureScreenshot", {"format": "png"})
        with open(os.path.join(ARTIFACT_DIR, "urmode_live_desktop_with_5_task_plan.png"), "wb") as f:
            f.write(base64.b64decode(shot_full["data"]))
        print("Captured full page: urmode_live_desktop_with_5_task_plan.png")

        print("\n=======================================================")
        print(">>> ALL 5-TASK WORKING PLAN VERIFICATION CHECKS PASSED! <<<")
        print("=======================================================")

    finally:
        proc.terminate()

if __name__ == '__main__':
    main()
