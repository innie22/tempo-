import subprocess, json, time, urllib.request, websocket, sys
sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = r'C:\Users\YEN NHI\AppData\Local\Temp\tempo_test_mouse_clicks'
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9309

cmd = [edge_path, '--headless=new', f'--remote-debugging-port={port}', '--remote-allow-origins=*', f'--user-data-dir={user_data_dir}', '--disable-gpu', '--no-first-run', '--window-size=1440,900', 'http://127.0.0.1:8000/']
proc = subprocess.Popen(cmd)
time.sleep(2)

try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        tabs = json.loads(resp.read().decode())
        ws_url = [t for t in tabs if t.get('type') == 'page'][0]['webSocketDebuggerUrl']

    ws = websocket.create_connection(ws_url)

    msg_id = 1
    def send_cmd(method, params=None):
        global msg_id
        cmd_obj = {"id": msg_id, "method": method, "params": params or {}}
        msg_id += 1
        ws.send(json.dumps(cmd_obj))
        while True:
            resp = json.loads(ws.recv())
            if resp.get("id") == cmd_obj["id"]:
                return resp.get("result", {})

    def eval_js(expr):
        res = send_cmd("Runtime.evaluate", {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": True
        })
        return res.get("result", {}).get("value")

    eval_js("window.TempoMode.setMode('recovery')")
    time.sleep(1)

    # Scroll down to Working Plan
    eval_js("document.getElementById('recovery-working-plan').scrollIntoView()")
    time.sleep(0.5)

    cards_geom = eval_js("""(() => {
        const cards = Array.from(document.querySelectorAll('#recovery-working-plan [data-task-id]'));
        return cards.map(c => {
            const taskId = c.getAttribute('data-task-id');
            const h5 = c.querySelector('h5');
            const roleBtn = c.querySelector('[role="button"]');
            const h5Rect = h5 ? h5.getBoundingClientRect() : null;
            const btnRect = roleBtn ? roleBtn.getBoundingClientRect() : null;
            const cardRect = c.getBoundingClientRect();
            return {
                taskId,
                title: h5 ? h5.textContent.trim() : null,
                h5Rect: h5Rect ? { x: h5Rect.left + h5Rect.width/2, y: h5Rect.top + h5Rect.height/2 } : null,
                btnRect: btnRect ? { x: btnRect.left + btnRect.width/2, y: btnRect.top + btnRect.height/2 } : null,
                cardRect: { x: cardRect.left + cardRect.width/2, y: cardRect.top + cardRect.height/2 }
            };
        });
    })()""")
    print("Cards geometry:", json.dumps(cards_geom, indent=2))

    for idx, c in enumerate(cards_geom):
        print(f"\n--- Testing Card {idx}: {c['title']} ({c['taskId']}) ---")
        
        # Test 1: Click on h5
        target = c['h5Rect']
        send_cmd("Input.dispatchMouseEvent", {"type": "mousePressed", "x": target['x'], "y": target['y'], "button": "left", "clickCount": 1})
        send_cmd("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": target['x'], "y": target['y'], "button": "left", "clickCount": 1})
        time.sleep(0.3)
        modal_open = eval_js("!!document.getElementById('rmode-task-detail-modal')")
        m_title = eval_js("document.getElementById('rmode-task-modal-title') ? document.getElementById('rmode-task-modal-title').textContent.trim() : null")
        print(f"Click on H5: modalOpen={modal_open}, title={m_title}")
        if modal_open:
            eval_js("window.TempoMode.closeRmodeTaskDetailModal()")
            time.sleep(0.3)

        # Test 2: Click on card center
        target = c['btnRect']
        send_cmd("Input.dispatchMouseEvent", {"type": "mousePressed", "x": target['x'], "y": target['y'], "button": "left", "clickCount": 1})
        send_cmd("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": target['x'], "y": target['y'], "button": "left", "clickCount": 1})
        time.sleep(0.3)
        modal_open = eval_js("!!document.getElementById('rmode-task-detail-modal')")
        m_title = eval_js("document.getElementById('rmode-task-modal-title') ? document.getElementById('rmode-task-modal-title').textContent.trim() : null")
        print(f"Click on Card Center: modalOpen={modal_open}, title={m_title}")
        if modal_open:
            eval_js("window.TempoMode.closeRmodeTaskDetailModal()")
            time.sleep(0.3)

    ws.close()
finally:
    proc.kill()
