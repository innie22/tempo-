import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os
import base64

sys.stdout.reconfigure(encoding='utf-8')

artifact_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
os.makedirs(artifact_dir, exist_ok=True)

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_recently_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9643

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "--window-size=1440,1100",
    "http://127.0.0.1:8000/#recovery"
]

proc = subprocess.Popen(cmd)
time.sleep(3.0)

try:
    req = urllib.request.urlopen(f"http://127.0.0.1:{port}/json")
    targets = json.loads(req.read().decode("utf-8"))
    page_target = [t for t in targets if t.get("type") == "page" and "127.0.0.1" in t.get("url", "")][0]
    ws = websocket.create_connection(page_target["webSocketDebuggerUrl"])

    msg_id = 1
    def send_cmd(method, params=None):
        global msg_id, ws
        cmd_obj = {"id": msg_id, "method": method, "params": params or {}}
        msg_id += 1
        ws.send(json.dumps(cmd_obj))
        while True:
            raw = ws.recv()
            res = json.loads(raw)
            if res.get("id") == cmd_obj["id"]:
                return res.get("result", {})

    def eval_js(expression):
        res = send_cmd("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True
        })
        if "exceptionDetails" in res:
            print("JS Exception:", res["exceptionDetails"])
        return res.get("result", {}).get("value")

    def capture_screenshot(filename):
        res = send_cmd("Page.captureScreenshot", {"format": "png"})
        data = res.get("data", "")
        filepath = os.path.join(artifact_dir, filename)
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(data))
        print(f"  [Screenshot] Saved: {filepath}")
        return filepath

    def capture_element(selector, filename):
        rect = eval_js(f"""
        (() => {{
            const el = document.querySelector('{selector}');
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return {{ x: Math.max(0, r.x - 10), y: Math.max(0, r.y - 10), width: r.width + 20, height: r.height + 20 }};
        }})()
        """)
        if not rect:
            print(f"Element not found for {selector}")
            return
        clip = {
            "x": rect["x"],
            "y": rect["y"],
            "width": rect["width"],
            "height": rect["height"],
            "scale": 1
        }
        res = send_cmd("Page.captureScreenshot", {"format": "png", "clip": clip})
        data = res.get("data", "")
        filepath = os.path.join(artifact_dir, filename)
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(data))
        print(f"  [Screenshot] Saved cropped: {filepath}")
        return filepath

    print("Waiting for page scripts...")
    for _ in range(20):
        ready = eval_js("document.readyState === 'complete' && !!window.TempoMode && !!window.TempoI18n")
        if ready:
            break
        time.sleep(0.5)

    # Setup trackers and authoritative observations
    eval_js("""
    (() => {
        const trackers = [
            { id: 'trk_tension', name: 'Tension', category: 'stress_sign', check_method: 'percentage', type_color: '#D48366', is_archived: false },
            { id: 'trk_sleep', name: 'Sleep', category: 'supportive', check_method: 'options', options: ['Good', 'Not good'], type_color: '#5A9E75', is_archived: false },
            { id: 'trk_walk', name: 'Walk', category: 'supportive', check_method: 'quantity', quantity_unit: 'min', type_color: '#5A9E75', is_archived: false },
            { id: 'trk_custom', name: 'Đọc sách', category: 'supportive', check_method: 'quantity', quantity_unit: 'trang', type_color: '#7B9688', is_archived: false }
        ];

        const todayStr = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTodayDateStr === 'function')
            ? window.TempoRecoverySelfCheck.getTodayDateStr()
            : new Date().toISOString().split('T')[0];

        const observations = [
            { id: 'obs_1', tracker_id: 'trk_tension', date: todayStr, value: 50, status: 'answered', check_method: 'percentage' },
            { id: 'obs_2', tracker_id: 'trk_sleep', date: todayStr, value: 'Good', status: 'answered', check_method: 'options' },
            { id: 'obs_3', tracker_id: 'trk_walk', date: todayStr, value: 25, status: 'answered', check_method: 'quantity', quantity_unit: 'min' },
            { id: 'obs_4', tracker_id: 'trk_custom', date: todayStr, value: 15, status: 'answered', check_method: 'quantity', quantity_unit: 'trang' }
        ];

        const uid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') ? window.TempoAuth.getCurrentUserId() : 'local_user';
        localStorage.setItem(`tempo_selfcheck_trackers_${uid}`, JSON.stringify(trackers));
        localStorage.setItem('tempo_selfcheck_trackers', JSON.stringify(trackers));
        localStorage.setItem(`tempo_selfcheck_observations_${uid}`, JSON.stringify(observations));
        localStorage.setItem('tempo_selfcheck_observations', JSON.stringify(observations));
        sessionStorage.setItem(`tempo_rmode_session_welcomed_${uid}`, 'true');
        sessionStorage.setItem('tempo_rmode_session_welcomed_local_user', 'true');
        if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.closeSetupModal === 'function') {
            window.TempoRecoverySetup.closeSetupModal();
        }
        window.TempoMode.setMode('recovery');
        window.TempoI18n.setLanguage('vi');
        window.TempoMode.renderRmodeHome();
    })()
    """)
    time.sleep(0.8)

    # -------------------------------------------------------------
    # TEST 1: Vietnamese Mode
    # -------------------------------------------------------------
    print("\n--- TEST 1: Vietnamese Mode ---")
    data_vi = eval_js("""
    (() => {
        const card = document.querySelector('[data-tempo-ui="recovery-recently"]');
        const header = card?.querySelector('h4.font-heading')?.textContent?.trim();
        const adjustBtn = card?.querySelector('.shrink-0 button')?.textContent?.trim();
        const footer = card?.querySelector('[data-tempo-ui="recently-countdown-footer"]')?.textContent?.trim();
        
        const metricRows = Array.from(card?.querySelectorAll('[data-tempo-ui="recently-metrics-scroll"] > div') || []);
        const metrics = metricRows.map(row => {
            const name = row.querySelector('.flex.items-center.space-x-2 span:last-child')?.textContent?.trim();
            const desc = row.querySelector('p.text-xs')?.textContent?.trim();
            const val = row.querySelector('.text-base.font-extrabold')?.textContent?.trim();
            return { name, desc, val };
        });

        return {
            header,
            adjustBtn,
            footer,
            metrics
        };
    })()
    """)

    print("Vietnamese Recently Card Data:", json.dumps(data_vi, indent=2, ensure_ascii=False))

    assert data_vi['header'] == "Gần đây", f"Header mismatch: {data_vi['header']}"
    assert data_vi['adjustBtn'] == "Chỉnh sửa tracking", f"AdjustBtn mismatch: {data_vi['adjustBtn']}"
    assert "Báo cáo tuần sẽ sẵn sàng trong" in data_vi['footer'] and "ngày nữa." in data_vi['footer'], f"Footer mismatch: {data_vi['footer']}"

    # Verify metrics
    metrics = {m['name']: m for m in data_vi['metrics']}
    print("Metrics mapped:", metrics)

    assert metrics['Tension']['desc'] == "Mức căng thẳng trung bình", f"Tension desc: {metrics['Tension']['desc']}"
    assert metrics['Tension']['val'] == "50%"

    assert metrics['Sleep']['desc'] == "Số đêm ngủ ngon", f"Sleep desc: {metrics['Sleep']['desc']}"
    assert metrics['Sleep']['val'] == "1"

    assert metrics['Walk']['desc'] == "Thời gian đi bộ", f"Walk desc: {metrics['Walk']['desc']}"
    assert "25" in metrics['Walk']['val']

    assert metrics['Đọc sách']['desc'] == "Số lần ghi nhận", f"Custom logged desc: {metrics['Đọc sách']['desc']}"
    assert "15 trang" in metrics['Đọc sách']['val']

    print("✓ Test 1 Passed: All Vietnamese Recently labels and dynamic values match exact user specifications!")

    capture_screenshot("recently_card_vi.png")
    capture_element('[data-tempo-ui="recovery-recently"]', "recently_card_vi_closeup.png")

    # -------------------------------------------------------------
    # TEST 2: English Mode (Live Switch)
    # -------------------------------------------------------------
    print("\n--- TEST 2: English Mode (Live Switch) ---")
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(0.5)

    data_en = eval_js("""
    (() => {
        const card = document.querySelector('[data-tempo-ui="recovery-recently"]');
        const header = card?.querySelector('h4.font-heading')?.textContent?.trim();
        const adjustBtn = card?.querySelector('.shrink-0 button')?.textContent?.trim();
        const footer = card?.querySelector('[data-tempo-ui="recently-countdown-footer"]')?.textContent?.trim();
        
        const metricRows = Array.from(card?.querySelectorAll('[data-tempo-ui="recently-metrics-scroll"] > div') || []);
        const metrics = metricRows.map(row => {
            const name = row.querySelector('.flex.items-center.space-x-2 span:last-child')?.textContent?.trim();
            const desc = row.querySelector('p.text-xs')?.textContent?.trim();
            const val = row.querySelector('.text-base.font-extrabold')?.textContent?.trim();
            return { name, desc, val };
        });

        return {
            header,
            adjustBtn,
            footer,
            metrics
        };
    })()
    """)

    print("English Recently Card Data:", json.dumps(data_en, indent=2, ensure_ascii=False))

    assert data_en['header'] == "Recently", f"Header mismatch: {data_en['header']}"
    assert data_en['adjustBtn'] == "Adjust Tracking", f"AdjustBtn mismatch: {data_en['adjustBtn']}"
    assert "until your weekly report." in data_en['footer'], f"Footer mismatch: {data_en['footer']}"

    metrics_en = {m['name']: m for m in data_en['metrics']}

    assert metrics_en['Tension']['desc'] == "Your average tension level is", f"Tension desc: {metrics_en['Tension']['desc']}"
    assert metrics_en['Tension']['val'] == "50%"

    assert metrics_en['Sleep']['desc'] == "Nights of Quality Sleep", f"Sleep desc: {metrics_en['Sleep']['desc']}"
    assert metrics_en['Sleep']['val'] == "1"

    assert metrics_en['Walk']['desc'] == "You have walked for", f"Walk desc: {metrics_en['Walk']['desc']}"
    assert "25" in metrics_en['Walk']['val']

    assert metrics_en['Đọc sách']['desc'] == "You have logged", f"Custom logged desc: {metrics_en['Đọc sách']['desc']}"
    assert "15 trang" in metrics_en['Đọc sách']['val']

    print("✓ Test 2 Passed: All English Recently labels match exact specifications!")

    capture_screenshot("recently_card_en.png")
    capture_element('[data-tempo-ui="recovery-recently"]', "recently_card_en_closeup.png")

    # -------------------------------------------------------------
    # TEST 3: Switch back to Vietnamese
    # -------------------------------------------------------------
    print("\n--- TEST 3: Switch back to Vietnamese ---")
    eval_js("window.TempoI18n.setLanguage('vi')")
    time.sleep(0.4)

    assert eval_js("document.querySelector('[data-tempo-ui=\"recovery-recently\"] h4.font-heading')?.textContent?.trim()") == "Gần đây"
    assert eval_js("document.querySelector('[data-tempo-ui=\"recovery-recently\"] .shrink-0 button')?.textContent?.trim()") == "Chỉnh sửa tracking"
    print("✓ Test 3 Passed: Dynamic toggle back to Vietnamese confirmed!")

    print("\n=== ALL RECENTLY CARD TESTS PASSED SUCCESSFULLY! ===")

finally:
    try:
        ws.close()
    except Exception:
        pass
    proc.kill()
