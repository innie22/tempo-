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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_greeting_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9320
    
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

        for _ in range(40):
            try:
                ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined' && typeof window.TempoEmergencyFlow !== 'undefined'")
                if ready:
                    break
            except Exception:
                pass
            time.sleep(0.5)

        # 1. TEST PERSONALIZED GREETING WITH AUTHENTICATED USER (e.g. Innie)
        eval_js("""
            (() => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
                const testPlan = {
                    id: 'plan_urgent_verify', planId: 'plan_urgent_verify', planType: 'emergency', title: 'Urgent Plan',
                    plannedTasks: [
                        { dayDate: today, dayLabel: 'Today', startTime: '10:00 AM', endTime: '11:00 AM', executionBadge: 'DO THIS FIRST',
                          task: { id: 'task-u1', name: 'Marketing Research', description: 'Subtask 1: Literature Review', hasDeadline: true, deadlineDate: today, deadlineTime: '21:00', durationLabel: '2h 30m', durationMinutes: 150, completed: false, isInProgress: true, subtasks: [{ id: 's1', title: 'Subtask 1: Literature Review', completed: false }] } },
                        { dayDate: today, dayLabel: 'Today', startTime: '02:00 PM', endTime: '03:00 PM', executionBadge: 'THEN',
                          task: { id: 'task-u2', name: 'Event Proposal', description: 'Prepare outline', hasDeadline: false, durationLabel: '45 min', durationMinutes: 45, completed: false, isInProgress: false, subtasks: [] } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }]
                };
                testPlan.tasks = testPlan.plannedTasks.map(pt => pt.task);
                window.TempoPlanStore.saveActivePlan('emergency', testPlan);
                window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
                window.TempoEmergencyFlow.restorePlanState();

                // Mock authenticated user profile: Innie
                if (window.TempoAuth) {
                    window.TempoAuth.getCurrentProfile = () => ({
                        display_name: 'Innie',
                        full_name: 'Innie Nguyen',
                        email: 'innie@example.com'
                    });
                }
                window.TempoMode.setMode('emergency');
            })()
        """)
        time.sleep(1)

        auth_check = eval_js("""
            (() => {
                const emodeBox = document.getElementById('emode-home-content');
                const greetingH = emodeBox ? emodeBox.querySelector('.text-2xl.sm\\\\:text-\\\\[28px\\\\]') : null;
                const nowCard = document.querySelector('.urgent-card-now');
                const internalGreeting = nowCard ? nowCard.querySelector('.font-semibold.text-\\\\[\\\\#6F6B68\\\\]') : null;
                const orangeNowBadge = nowCard ? nowCard.querySelector('.bg-\\\\[\\\\#FF6B2C\\\\].text-white') : null;
                const taskLabel = nowCard ? nowCard.querySelector('.rounded-full.bg-\\\\[\\\\#D79277\\\\].text-white') : null;
                const taskTitle = nowCard ? nowCard.querySelector('h3') : null;
                const subtask = nowCard ? nowCard.querySelector('p.italic') : null;
                const cardBg = nowCard ? window.getComputedStyle(nowCard).backgroundColor : null;
                const cardBorder = nowCard ? window.getComputedStyle(nowCard).border : null;

                // Check timeline item "Now" badge is preserved
                const timelineNowBadge = document.querySelector('.urgent-timeline-item .bg-\\\\[\\\\#FFE9DC\\\\]');

                return {
                    headingText: greetingH ? greetingH.textContent.trim() : null,
                    hasInternalGreeting: !!internalGreeting,
                    internalGreetingText: internalGreeting ? internalGreeting.textContent.trim() : null,
                    hasOrangeNowBadge: !!orangeNowBadge,
                    taskLabelText: taskLabel ? taskLabel.textContent.trim() : null,
                    taskTitleText: taskTitle ? taskTitle.textContent.trim() : null,
                    subtaskText: subtask ? subtask.textContent.trim() : null,
                    cardBg,
                    cardBorder,
                    hasTimelineNowBadge: !!timelineNowBadge
                };
            })()
        """)
        print("AUTHENTICATED CHECK (Innie):", json.dumps(auth_check, indent=2))

        shot_auth = send_command("Page.captureScreenshot", {"format": "png"})
        auth_shot_path = os.path.join(ARTIFACT_DIR, "urmode_authenticated_greeting_verified.png")
        with open(auth_shot_path, "wb") as f:
            f.write(base64.b64decode(shot_auth["data"]))
        print(f"Saved: {auth_shot_path}")

        # 2. TEST FALLBACK GREETING (Unauthenticated / Null display name)
        eval_js("""
            (() => {
                if (window.TempoAuth) {
                    window.TempoAuth.getCurrentProfile = () => null;
                    window.TempoAuth.getCurrentUser = () => null;
                }
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.5)

        fallback_check = eval_js("""
            (() => {
                const emodeBox = document.getElementById('emode-home-content');
                const greetingH = emodeBox ? emodeBox.querySelector('.text-2xl.sm\\\\:text-\\\\[28px\\\\]') : null;
                return {
                    headingText: greetingH ? greetingH.textContent.trim() : null
                };
            })()
        """)
        print("FALLBACK CHECK (Unauthenticated):", json.dumps(fallback_check, indent=2))

        shot_fallback = send_command("Page.captureScreenshot", {"format": "png"})
        fallback_shot_path = os.path.join(ARTIFACT_DIR, "urmode_fallback_greeting_verified.png")
        with open(fallback_shot_path, "wb") as f:
            f.write(base64.b64decode(shot_fallback["data"]))
        print(f"Saved: {fallback_shot_path}")

        # Also update urmode_live_desktop_top.png and urmode_live_desktop_full.png with authenticated user
        eval_js("""
            (() => {
                if (window.TempoAuth) {
                    window.TempoAuth.getCurrentProfile = () => ({
                        display_name: 'Innie',
                        full_name: 'Innie Nguyen',
                        email: 'innie@example.com'
                    });
                }
                window.TempoMode.renderEmodeHome();
            })()
        """)
        time.sleep(0.5)
        top_shot = send_command("Page.captureScreenshot", {"format": "png"})
        with open(os.path.join(ARTIFACT_DIR, "urmode_live_desktop_top.png"), "wb") as f:
            f.write(base64.b64decode(top_shot["data"]))

        full_shot = send_command("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": True})
        with open(os.path.join(ARTIFACT_DIR, "urmode_live_desktop_full.png"), "wb") as f:
            f.write(base64.b64decode(full_shot["data"]))

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
