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
    user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_btn_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9345
    
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

        # Set up Urgent Mode in English for exact label comparison
        eval_js("""
            (() => {
                if (window.TempoI18n) window.TempoI18n.setLanguage('en');
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
                const testPlan = {
                    id: 'plan_urgent_verify', planId: 'plan_urgent_verify', planType: 'emergency', title: 'Urgent Plan',
                    plannedTasks: [
                        { dayDate: today, dayLabel: 'Today', startTime: '10:00 AM', endTime: '11:00 AM', executionBadge: 'DO THIS FIRST',
                          task: { id: 'task-u1', name: 'Marketing Report', description: 'Finish competitor analysis section', hasDeadline: true, deadlineDate: today, deadlineTime: '22:00', durationLabel: '45 min', durationMinutes: 45, completed: false, isInProgress: true, subtasks: [{}, {}, {}] } }
                    ],
                    tasks: [],
                    availabilityDays: [{ date: today, label: 'Today', blocks: [{ start: '09:00', end: '23:59', minutes: 840 }] }]
                };
                testPlan.tasks = testPlan.plannedTasks.map(pt => pt.task);
                window.TempoPlanStore.saveActivePlan('emergency', testPlan);
                window.TempoEmergencyFlow.setConfirmedPlan(testPlan);
                window.TempoEmergencyFlow.restorePlanState();
                window.TempoMode.setMode('emergency');
            })()
        """)
        time.sleep(1)

        btn_metrics = eval_js("""
            (() => {
                const btn = document.getElementById('btn-home-mode-selector');
                if (!btn) return null;
                const bcr = btn.getBoundingClientRect();
                const cs = window.getComputedStyle(btn);
                const spans = Array.from(btn.querySelectorAll('span'));
                
                return {
                    renderedWidth: bcr.width,
                    renderedHeight: bcr.height,
                    backgroundColor: cs.backgroundColor,
                    borderColor: cs.borderColor,
                    borderWidth: cs.borderWidth,
                    borderRadius: cs.borderRadius,
                    color: cs.color,
                    fontSize: cs.fontSize,
                    fontWeight: cs.fontWeight,
                    boxShadow: cs.boxShadow,
                    display: cs.display,
                    alignItems: cs.alignItems,
                    textContent: btn.textContent.trim(),
                    spanCount: spans.length,
                    spanDetails: spans.map(s => {
                        const sbcr = s.getBoundingClientRect();
                        const scs = window.getComputedStyle(s);
                        return {
                            text: s.textContent,
                            color: scs.color,
                            fontSize: scs.fontSize,
                            width: sbcr.width,
                            height: sbcr.height,
                            top: sbcr.top - bcr.top
                        };
                    })
                };
            })()
        """)
        print("BUTTON METRICS (English):", json.dumps(btn_metrics, indent=2))

        # Check dropdown interaction
        dd_test = eval_js("""
            (() => {
                const btn = document.getElementById('btn-home-mode-selector');
                const dd = document.getElementById('home-mode-selector-dropdown');
                const initialHidden = dd.classList.contains('hidden');
                
                btn.click();
                const opened = !dd.classList.contains('hidden');
                
                window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
                const closed = dd.classList.contains('hidden');
                
                return { initialHidden, opened, closed };
            })()
        """)
        print("DROPDOWN INTERACTION TEST:", json.dumps(dd_test, indent=2))
        assert dd_test['opened'], "Clicking button must open mode dropdown"
        assert dd_test['closed'], "Escape must close mode dropdown"

        # Capture button close-up clip
        btn_box = eval_js("""
            (() => {
                const btn = document.getElementById('btn-home-mode-selector');
                const bcr = btn.getBoundingClientRect();
                return {
                    x: Math.max(0, bcr.x - 20),
                    y: Math.max(0, bcr.y - 10),
                    width: bcr.width + 40,
                    height: bcr.height + 20
                };
            })()
        """)
        
        shot_btn = send_command("Page.captureScreenshot", {
            "format": "png",
            "clip": {
                "x": btn_box["x"],
                "y": btn_box["y"],
                "width": btn_box["width"],
                "height": btn_box["height"],
                "scale": 2
            }
        })
        with open(os.path.join(ARTIFACT_DIR, "urmode_button_refined_verified.png"), "wb") as f:
            f.write(base64.b64decode(shot_btn["data"]))

        # Also capture top dashboard screenshot
        top_shot = send_command("Page.captureScreenshot", {"format": "png"})
        with open(os.path.join(ARTIFACT_DIR, "urmode_live_desktop_top.png"), "wb") as f:
            f.write(base64.b64decode(top_shot["data"]))

        print("\nBUTTON VERIFICATION PASSED SUCCESSFULLY!")

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
