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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_scroll_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9400
    
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

        def capture_full_page(filename):
            res = send_command("Page.captureScreenshot", {"format": "png"})
            with open(os.path.join(ARTIFACT_DIR, filename), "wb") as f:
                f.write(base64.b64decode(res["data"]))
            print(f"Captured full page: {filename}")

        for _ in range(40):
            try:
                ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined'")
                if ready:
                    break
            except Exception:
                pass
            time.sleep(0.5)

        eval_js("if (window.TempoI18n) window.TempoI18n.setLanguage('en');")

        # -------------------------------------------------------------
        # 1. EMPTY / SETUP IN PROGRESS STATE
        # -------------------------------------------------------------
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
                window.TempoMode.setMode('emergency');
                window.TempoApp.navigateTo('today');
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.4)
        m_empty = eval_js("""
            (() => {
                const card = document.querySelector('.urgent-working-plan-card');
                const r = card.getBoundingClientRect();
                return { width: r.width, height: r.height };
            })()
        """)
        print("Empty state card dimensions:", m_empty)
        assert abs(m_empty['height'] - 388) <= 1, f"Empty card height must be 388px, got {m_empty['height']}"
        capture_element('.urgent-working-plan-card', "working_plan_empty_fixed_verified.png")

        # -------------------------------------------------------------
        # 2. SHORT TASK LIST (1 Task)
        # -------------------------------------------------------------
        eval_js("""
            (() => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
                const testPlan = {
                    id: 'plan_urgent_1', planId: 'plan_urgent_1', planType: 'emergency', title: 'Urgent Plan',
                    plannedTasks: [
                        { dayDate: today, dayLabel: 'Today', startTime: '10:00 AM', endTime: '11:00 AM', executionBadge: 'DO THIS FIRST',
                          task: { id: 'task-u1', name: 'Marketing Research', description: 'Subtask 1: Literature Review', hasDeadline: true, deadlineDate: '2026-10-17', deadlineTime: '21:00', durationLabel: '2h 30m', durationMinutes: 150, completed: false, isInProgress: true, subtasks: [{ title: 'Subtask 1: Literature Review', completed: false }] } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }]
                };
                testPlan.tasks = testPlan.plannedTasks.map(pt => pt.task);
                window.TempoPlanStore.saveActivePlan('emergency', testPlan);
                window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
                window.TempoEmergencyFlow.restorePlanState();
                window.TempoMode.setMode('emergency');
                window.TempoApp.navigateTo('today');
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.4)
        m_short = eval_js("""
            (() => {
                const card = document.querySelector('.urgent-working-plan-card');
                const scroll = document.querySelector('.urgent-working-plan-tasks-scroll');
                const r = card.getBoundingClientRect();
                return {
                    width: r.width,
                    height: r.height,
                    scrollClientHeight: scroll.clientHeight,
                    scrollScrollHeight: scroll.scrollHeight,
                    isScrollable: scroll.scrollHeight > scroll.clientHeight
                };
            })()
        """)
        print("Short list card dimensions:", m_short)
        assert abs(m_short['height'] - 388) <= 1, f"Short list card height must be 388px, got {m_short['height']}"
        assert not m_short['isScrollable'], "Short list should fit naturally without vertical scrollbar overflow"
        capture_element('.urgent-working-plan-card', "working_plan_short_list_verified.png")

        # -------------------------------------------------------------
        # 3. LONG TASK LIST (6 Tasks) - Fixed Card Height & Scrollable List
        # -------------------------------------------------------------
        eval_js("""
            (() => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
                const testPlan = {
                    id: 'plan_urgent_6', planId: 'plan_urgent_6', planType: 'emergency', title: 'Urgent Plan',
                    plannedTasks: [
                        { dayDate: today, task: { id: 't1', name: 'Task 1: Marketing Research', hasDeadline: true, deadlineDate: today, deadlineTime: '10:00', completed: false, isInProgress: true, subtasks: [] } },
                        { dayDate: today, task: { id: 't2', name: 'Task 2: Literature Review Notes', hasDeadline: true, deadlineDate: today, deadlineTime: '12:00', completed: false, isInProgress: false, subtasks: [] } },
                        { dayDate: today, task: { id: 't3', name: 'Task 3: Draft Section A Findings', hasDeadline: false, completed: false, isInProgress: false, subtasks: [] } },
                        { dayDate: today, task: { id: 't4', name: 'Task 4: Review Statistical Tables', hasDeadline: false, completed: false, isInProgress: false, subtasks: [] } },
                        { dayDate: today, task: { id: 't5', name: 'Task 5: Bibliography & Citations', hasDeadline: true, deadlineDate: today, deadlineTime: '18:00', completed: false, isInProgress: false, subtasks: [] } },
                        { dayDate: today, task: { id: 't6', name: 'Task 6: Final Proofreading & Submission', hasDeadline: true, deadlineDate: today, deadlineTime: '21:00', completed: false, isInProgress: false, subtasks: [] } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }]
                };
                testPlan.tasks = testPlan.plannedTasks.map(pt => pt.task);
                window.TempoPlanStore.saveActivePlan('emergency', testPlan);
                window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
                window.TempoEmergencyFlow.restorePlanState();
                window.TempoMode.setMode('emergency');
                window.TempoApp.navigateTo('today');
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.4)

        m_long_top = eval_js("""
            (() => {
                const card = document.querySelector('.urgent-working-plan-card');
                const scroll = document.querySelector('.urgent-working-plan-tasks-scroll');
                const header = card.querySelector('.shrink-0');
                const rCard = card.getBoundingClientRect();
                const rHeader = header.getBoundingClientRect();
                const items = card.querySelectorAll('.urgent-timeline-item');
                return {
                    cardWidth: rCard.width,
                    cardHeight: rCard.height,
                    headerTop: rHeader.top,
                    headerHeight: rHeader.height,
                    scrollClientHeight: scroll.clientHeight,
                    scrollScrollHeight: scroll.scrollHeight,
                    isScrollable: scroll.scrollHeight > scroll.clientHeight,
                    itemCount: items.length,
                    scrollTop: scroll.scrollTop
                };
            })()
        """)
        print("Long list card dimensions (at top):", m_long_top)
        assert abs(m_long_top['cardHeight'] - 388) <= 1, f"Long list card height must stay at 388px! Got {m_long_top['cardHeight']}"
        assert m_long_top['isScrollable'], "Long list must be vertically scrollable"
        assert m_long_top['itemCount'] == 6, "All 6 tasks must be rendered in the DOM without truncation"
        capture_element('.urgent-working-plan-card', "working_plan_long_list_top_verified.png")
        capture_full_page("urmode_live_desktop_with_scrollable_plan.png")

        # Now scroll the task list down to view the bottom tasks
        eval_js("""
            (() => {
                const scroll = document.querySelector('.urgent-working-plan-tasks-scroll');
                scroll.scrollTop = scroll.scrollHeight;
            })()
        """)
        time.sleep(0.3)

        m_long_scrolled = eval_js("""
            (() => {
                const card = document.querySelector('.urgent-working-plan-card');
                const scroll = document.querySelector('.urgent-working-plan-tasks-scroll');
                const header = card.querySelector('.shrink-0');
                const rCard = card.getBoundingClientRect();
                const rHeader = header.getBoundingClientRect();
                const lastItem = card.querySelectorAll('.urgent-timeline-item')[5];
                const rLastItem = lastItem.getBoundingClientRect();
                return {
                    cardHeight: rCard.height,
                    headerTop: rHeader.top,
                    headerHeight: rHeader.height,
                    scrollTop: scroll.scrollTop,
                    lastItemText: lastItem.querySelector('h4').textContent.trim(),
                    lastItemVisibleInCard: rLastItem.top >= rCard.top && rLastItem.bottom <= rCard.bottom + 5
                };
            })()
        """)
        print("Long list card dimensions (scrolled to bottom):", m_long_scrolled)
        assert abs(m_long_scrolled['cardHeight'] - 388) <= 1, f"Card height must stay 388px while scrolling! Got {m_long_scrolled['cardHeight']}"
        assert m_long_scrolled['headerTop'] == m_long_top['headerTop'], "Header must remain completely stationary while list scrolls!"
        assert m_long_scrolled['scrollTop'] > 0, "Task list must have scrolled vertically"
        assert m_long_scrolled['lastItemVisibleInCard'], "Last task (Task 6) must be visible in the card when scrolled to bottom"
        capture_element('.urgent-working-plan-card', "working_plan_long_list_bottom_verified.png")

        print("\nAll Working Plan scroll invariants verified successfully!")

    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass
        try:
            proc.terminate()
        except Exception:
            pass

if __name__ == '__main__':
    main()
