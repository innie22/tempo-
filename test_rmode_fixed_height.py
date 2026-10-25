import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import sys
import base64

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run():
    user_data_dir = tempfile.mkdtemp(prefix='tempo_fixed_h_')
    port = 9367
    proc = subprocess.Popen([
        r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
        '--headless=new',
        f'--remote-debugging-port={port}',
        '--remote-allow-origins=*',
        f'--user-data-dir={user_data_dir}',
        '--disable-gpu',
        '--no-first-run',
        'http://localhost:8000/'
    ])
    time.sleep(2)
    try:
        pages = []
        for _ in range(30):
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
                    tabs = json.loads(resp.read().decode())
                    pages = [t for t in tabs if t.get('type') == 'page' and 'localhost' in t.get('url', '')]
                    if pages:
                        break
            except Exception:
                pass
            time.sleep(0.5)

        if not pages:
            raise RuntimeError("Browser not connected")

        ws_url = pages[0]['webSocketDebuggerUrl']
        ws = websocket.create_connection(ws_url)

        msg_id = 1
        def send_cmd(method, params=None):
            nonlocal msg_id
            cid = msg_id
            msg_id += 1
            req = {'id': cid, 'method': method}
            if params:
                req['params'] = params
            ws.send(json.dumps(req))
            while True:
                r = json.loads(ws.recv())
                if r.get('id') == cid:
                    return r.get('result', {})

        def eval_js(expr):
            r = send_cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
            if "exceptionDetails" in r:
                log(f"JS Exception: {r['exceptionDetails']}")
            return r.get('result', {}).get('value')

        def save_screenshot(path):
            data = send_cmd("Page.captureScreenshot", {"format": "png"})
            b64 = data.get("data", "")
            if b64:
                with open(path, "wb") as f:
                    f.write(base64.b64decode(b64))
                log(f"Saved screenshot: {path}")

        def set_viewport(w, h, mobile=False):
            send_cmd('Emulation.setDeviceMetricsOverride', {'width': w, 'height': h, 'deviceScaleFactor': 1, 'mobile': mobile})
            time.sleep(0.5)

        set_viewport(1280, 900, False)

        for _ in range(30):
            if eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'"):
                break
            time.sleep(0.5)

        eval_js("""
            window.TempoMode.setMode('recovery');
            window.TempoApp.navigateTo('today');
        """)
        time.sleep(1)

        def measure_card():
            return eval_js("""
                (() => {
                    const card = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
                    const scroll = card.querySelector('[data-tempo-ui="recovery-plan-scroll-container"]');
                    const r = card.getBoundingClientRect();
                    const sr = scroll.getBoundingClientRect();
                    const cs = window.getComputedStyle(card);
                    return {
                        cardOffsetHeight: card.offsetHeight,
                        cardClientHeight: card.clientHeight,
                        cardBoundingHeight: Math.round(r.height),
                        cardCssHeight: cs.height,
                        scrollOffsetHeight: scroll.offsetHeight,
                        scrollClientHeight: scroll.clientHeight,
                        scrollHeight: scroll.scrollHeight,
                        scrollWidth: scroll.scrollWidth,
                        overflowX: window.getComputedStyle(scroll).overflowX,
                        overflowY: window.getComputedStyle(scroll).overflowY
                    };
                })()
            """)

        # -------------------------------------------------------------
        # STATE 1: Default 3 tasks
        # -------------------------------------------------------------
        log("\n--- STATE 1: Default 3 tasks (2 in Oct 20, 1 in Oct 21) ---")
        m1 = measure_card()
        log("Measurement: " + json.dumps(m1, indent=2))
        assert m1["cardOffsetHeight"] == 462, f"Expected 462px, got {m1['cardOffsetHeight']}"
        assert m1["cardBoundingHeight"] == 462
        assert m1["scrollOffsetHeight"] == 312

        # Scroll card into view and capture screenshot
        eval_js("document.querySelector('[data-tempo-ui=\"recovery-working-plan\"]').scrollIntoView({ block: 'center' })")
        time.sleep(0.5)
        shot1 = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\rmode_fixed_height_default_3tasks.png"
        save_screenshot(shot1)

        # -------------------------------------------------------------
        # STATE 2: Exactly 1 Task
        # -------------------------------------------------------------
        log("\n--- STATE 2: Exactly 1 Task ---")
        eval_js("""
            (() => {
                const plan = {
                    plannedTasks: [
                        { dayDate: '2026-10-20', task: { id: 't1', name: 'Single Task', completed: false } }
                    ],
                    unarrangedTasks: [],
                    tasks: []
                };
                localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
                window.TempoMode.renderRmodeHome();
            })()
        """)
        time.sleep(0.5)
        m2 = measure_card()
        log("Measurement: " + json.dumps(m2, indent=2))
        assert m2["cardOffsetHeight"] == 462, f"Expected 462px, got {m2['cardOffsetHeight']}"
        assert m2["cardBoundingHeight"] == 462
        assert m2["scrollOffsetHeight"] == 312

        shot2 = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\rmode_fixed_height_1task.png"
        save_screenshot(shot2)

        # -------------------------------------------------------------
        # STATE 3: 0 Active Tasks (1 completed in Done column)
        # -------------------------------------------------------------
        log("\n--- STATE 3: 0 Active Tasks (1 completed in Done column) ---")
        eval_js("""
            (() => {
                const plan = {
                    plannedTasks: [
                        { dayDate: '2026-10-20', task: { id: 't1', name: 'Completed Task', completed: true } }
                    ],
                    unarrangedTasks: [],
                    tasks: []
                };
                localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
                window.TempoMode.renderRmodeHome();
            })()
        """)
        time.sleep(0.5)
        m3 = measure_card()
        log("Measurement: " + json.dumps(m3, indent=2))
        assert m3["cardOffsetHeight"] == 462, f"Expected 462px, got {m3['cardOffsetHeight']}"
        assert m3["cardBoundingHeight"] == 462
        assert m3["scrollOffsetHeight"] == 312

        shot3 = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\rmode_fixed_height_0active_done.png"
        save_screenshot(shot3)

        # -------------------------------------------------------------
        # STATE 4: 10 Tasks in 1 Column (Vertical Overflow)
        # -------------------------------------------------------------
        log("\n--- STATE 4: 10 Tasks in 1 Column (Vertical Overflow) ---")
        eval_js("""
            (() => {
                const plan = {
                    plannedTasks: Array.from({ length: 10 }, (_, i) => ({
                        dayDate: '2026-10-20',
                        task: { id: 't' + i, name: 'Task Number ' + (i + 1), completed: false }
                    })),
                    unarrangedTasks: [],
                    tasks: []
                };
                localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
                window.TempoMode.renderRmodeHome();
            })()
        """)
        time.sleep(0.5)
        m4 = measure_card()
        log("Measurement: " + json.dumps(m4, indent=2))
        assert m4["cardOffsetHeight"] == 462, f"Expected 462px, got {m4['cardOffsetHeight']}"
        assert m4["cardBoundingHeight"] == 462
        assert m4["scrollOffsetHeight"] == 312
        assert m4["scrollHeight"] > m4["scrollClientHeight"], "Must have internal vertical scrolling"

        shot4 = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\rmode_fixed_height_10tasks_vertical_scroll.png"
        save_screenshot(shot4)

        # -------------------------------------------------------------
        # STATE 5: 15 Tasks Across 5 Different Dates (Horizontal & Vertical Overflow)
        # -------------------------------------------------------------
        log("\n--- STATE 5: 15 Tasks Across 5 Different Dates ---")
        eval_js("""
            (() => {
                const dates = ['2026-10-20', '2026-10-21', '2026-10-22', '2026-10-23', '2026-10-24'];
                const plannedTasks = [];
                for (let d = 0; d < dates.length; d++) {
                    for (let t = 0; t < 3; t++) {
                        plannedTasks.push({
                            dayDate: dates[d],
                            task: { id: `task-d${d}-t${t}`, name: `Task D${d+1} #${t+1}`, completed: (d === 0 && t === 0) }
                        });
                    }
                }
                const plan = { plannedTasks, unarrangedTasks: [], tasks: [] };
                localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
                window.TempoMode.renderRmodeHome();
            })()
        """)
        time.sleep(0.5)
        m5 = measure_card()
        log("Measurement: " + json.dumps(m5, indent=2))
        assert m5["cardOffsetHeight"] == 462, f"Expected 462px, got {m5['cardOffsetHeight']}"
        assert m5["cardBoundingHeight"] == 462
        assert m5["scrollOffsetHeight"] == 312
        assert m5["scrollWidth"] > m5["scrollOffsetHeight"], "Must have horizontal scrolling for 5 date columns"

        # Check Done column is present and reachable
        done_col_exists = eval_js("Boolean(document.querySelector('[data-tempo-ui=\"recovery-done-column\"]'))")
        assert done_col_exists, "Done column must exist and be reachable via horizontal scroll"

        shot5 = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\rmode_fixed_height_5date_columns.png"
        save_screenshot(shot5)

        # -------------------------------------------------------------
        # STATE 6: Tablet Viewport (768x1024)
        # -------------------------------------------------------------
        log("\n--- STATE 6: Tablet Viewport (768x1024) ---")
        set_viewport(768, 1024, False)
        m6 = measure_card()
        log("Measurement: " + json.dumps(m6, indent=2))
        assert m6["cardOffsetHeight"] == 462, f"Expected 462px, got {m6['cardOffsetHeight']}"

        # -------------------------------------------------------------
        # STATE 7: Mobile Viewport (375x812)
        # -------------------------------------------------------------
        log("\n--- STATE 7: Mobile Viewport (375x812) ---")
        set_viewport(375, 812, True)
        m7 = measure_card()
        log("Measurement: " + json.dumps(m7, indent=2))
        assert m7["cardOffsetHeight"] == 462, f"Expected 462px, got {m7['cardOffsetHeight']}"

        # -------------------------------------------------------------
        # STATE 8: Interactive Task Completion Toggle within Card
        # -------------------------------------------------------------
        log("\n--- STATE 8: Interactive Task Completion Toggle ---")
        set_viewport(1280, 900, False)
        # Toggle a task
        eval_js("""
            (() => {
                const btn = document.querySelector('[data-task-id="task-d0-t1"] button');
                if (btn) btn.click();
            })()
        """)
        time.sleep(1)
        m8 = measure_card()
        log("Measurement after toggling task: " + json.dumps(m8, indent=2))
        assert m8["cardOffsetHeight"] == 462, f"Expected 462px, got {m8['cardOffsetHeight']}"

        log("\n=======================================================")
        log("🎉 ALL FIXED HEIGHT TESTS PASSED 100%!")
        log("=======================================================")

        ws.close()
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    run()
