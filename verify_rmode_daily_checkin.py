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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_rmode_checkin_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9642

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

    # Setup 4 active tracking items with percentage (Tension level) first to test slider
    eval_js("""
    (() => {
        const trackers = [
            { id: 'trk_tension', name: 'Tension level', category: 'stress_sign', check_method: 'percentage', type_color: '#D48366', is_archived: false },
            { id: 'trk_sleep', name: 'Sleep quality', category: 'supportive', check_method: 'options', options: ['Good', 'Not good'], type_color: '#166545', is_archived: false },
            { id: 'trk_focus', name: 'Focus clarity', category: 'stress_sign', check_method: 'scale', scale_range: '1-5', scale_max: 5, type_color: '#D48366', is_archived: false },
            { id: 'trk_walk', name: 'Walking break', category: 'supportive', check_method: 'quantity', quantity_unit: 'min', type_color: '#166545', is_archived: false }
        ];
        const uid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') ? window.TempoAuth.getCurrentUserId() : 'local_user';
        localStorage.setItem(`tempo_selfcheck_trackers_${uid}`, JSON.stringify(trackers));
        localStorage.setItem('tempo_selfcheck_trackers', JSON.stringify(trackers));
        localStorage.removeItem(`tempo_selfcheck_observations_${uid}`);
        localStorage.removeItem('tempo_selfcheck_observations');
        sessionStorage.removeItem('rmode_skipped_trackers');
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

    # Dismiss any onboarding modal if visible
    eval_js("""
    (() => {
        const modal = document.getElementById('modal-recovery-setup');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    })()
    """)
    time.sleep(0.3)

    # -------------------------------------------------------------
    # TEST 1: Vietnamese Mode
    # -------------------------------------------------------------
    print("\n--- TEST 1: Vietnamese Mode ---")
    data_vi = eval_js("""
    (() => {
        const modeBtn = document.querySelector('#btn-home-mode-selector span.font-extrabold')?.textContent?.trim();
        const greeting = document.querySelector('.recovery-greeting h2 span:last-child')?.textContent?.trim();
        const card = document.querySelector('[data-tempo-ui="recovery-self-check"]');
        const badge = card?.querySelector('.space-y-1 span.uppercase')?.textContent?.trim();
        const title = card?.querySelector('h3.font-heading')?.textContent?.trim();
        const streak = card?.querySelector('.space-y-1 p.italic')?.textContent?.trim();
        const sliderValEl = card?.querySelector('#rmode-slider-val');
        const selectLevel = sliderValEl?.previousElementSibling?.textContent?.trim();
        const rangeEl = card?.querySelector('#rmode-selfcheck-range');
        const saveBtn = rangeEl?.nextElementSibling?.textContent?.trim();
        const skipBtn = card?.querySelector('button[title*="Bỏ qua"]')?.textContent?.trim() || card?.querySelector('button[title*="Skip"]')?.textContent?.trim();
        const summary = card?.querySelector('.pt-1.flex.items-center.justify-between.text-xs span')?.textContent?.trim();
        const actionBtns = card?.querySelectorAll('.pt-1.flex.flex-wrap.items-center button');
        const viewBtn = actionBtns && actionBtns[0] ? actionBtns[0].textContent.trim() : '';
        const editBtn = actionBtns && actionBtns[1] ? actionBtns[1].textContent.trim() : '';
        return {
            modeBtn,
            greeting,
            badge,
            title,
            streak,
            selectLevel,
            saveBtn,
            skipBtn,
            summary,
            viewBtn,
            editBtn
        };
    })()
    """)

    print("Vietnamese Data:", json.dumps(data_vi, indent=2, ensure_ascii=False))

    assert data_vi['modeBtn'] == "Chế độ Hồi phục", f"modeBtn mismatch: {data_vi['modeBtn']}"
    assert "Chào " in data_vi['greeting'] and "hôm nay bạn thế nào?" in data_vi['greeting'], f"greeting mismatch: {data_vi['greeting']}"
    assert data_vi['badge'] == "CHECK-IN HẰNG NGÀY", f"badge mismatch: {data_vi['badge']}"
    assert data_vi['title'] == "Self-check cho hôm nay", f"title mismatch: {data_vi['title']}"
    assert data_vi['streak'] == "Chuỗi 0 ngày", f"streak mismatch: {data_vi['streak']}"
    assert data_vi['selectLevel'] == "Chọn mức độ:", f"selectLevel mismatch: {data_vi['selectLevel']}"
    assert data_vi['saveBtn'] == "Lưu", f"saveBtn mismatch: {data_vi['saveBtn']}"
    assert data_vi['skipBtn'] == "Bỏ qua", f"skipBtn mismatch: {data_vi['skipBtn']}"
    assert data_vi['summary'] == "Bạn đã check-in 0/4 mục hôm nay.", f"summary mismatch: {data_vi['summary']}"
    assert data_vi['viewBtn'] == "Xem check-in hôm nay", f"viewBtn mismatch: {data_vi['viewBtn']}"
    assert data_vi['editBtn'] == "Sửa tracking", f"editBtn mismatch: {data_vi['editBtn']}"
    print("✓ Test 1 Passed: All Vietnamese translations match exact user specs!")

    capture_screenshot("rmode_daily_checkin_vi.png")
    capture_element(".recovery-left-col", "rmode_daily_checkin_vi_closeup.png")

    # -------------------------------------------------------------
    # TEST 2: English Mode (Live Switch)
    # -------------------------------------------------------------
    print("\n--- TEST 2: English Mode (Live Switch) ---")
    eval_js("window.TempoI18n.setLanguage('en')")
    time.sleep(0.5)

    data_en = eval_js("""
    (() => {
        const modeBtn = document.querySelector('#btn-home-mode-selector span.font-extrabold')?.textContent?.trim();
        const greeting = document.querySelector('.recovery-greeting h2 span:last-child')?.textContent?.trim();
        const card = document.querySelector('[data-tempo-ui="recovery-self-check"]');
        const badge = card?.querySelector('.space-y-1 span.uppercase')?.textContent?.trim();
        const title = card?.querySelector('h3.font-heading')?.textContent?.trim();
        const streak = card?.querySelector('.space-y-1 p.italic')?.textContent?.trim();
        const sliderValEl = card?.querySelector('#rmode-slider-val');
        const selectLevel = sliderValEl?.previousElementSibling?.textContent?.trim();
        const rangeEl = card?.querySelector('#rmode-selfcheck-range');
        const saveBtn = rangeEl?.nextElementSibling?.textContent?.trim();
        const skipBtn = card?.querySelector('button[title*="Skip"]')?.textContent?.trim() || card?.querySelector('button[title*="Bỏ qua"]')?.textContent?.trim();
        const summary = card?.querySelector('.pt-1.flex.items-center.justify-between.text-xs span')?.textContent?.trim();
        const actionBtns = card?.querySelectorAll('.pt-1.flex.flex-wrap.items-center button');
        const viewBtn = actionBtns && actionBtns[0] ? actionBtns[0].textContent.trim() : '';
        const editBtn = actionBtns && actionBtns[1] ? actionBtns[1].textContent.trim() : '';
        return {
            modeBtn,
            greeting,
            badge,
            title,
            streak,
            selectLevel,
            saveBtn,
            skipBtn,
            summary,
            viewBtn,
            editBtn
        };
    })()
    """)

    print("English Data:", json.dumps(data_en, indent=2, ensure_ascii=False))

    assert data_en['modeBtn'] == "Recovery Mode", f"modeBtn mismatch: {data_en['modeBtn']}"
    assert "Hi " in data_en['greeting'] and "how are you today?" in data_en['greeting'], f"greeting mismatch: {data_en['greeting']}"
    assert data_en['badge'] == "YOUR DAILY CHECK-IN", f"badge mismatch: {data_en['badge']}"
    assert data_en['title'] == "Today’s self-check", f"title mismatch: {data_en['title']}"
    assert data_en['streak'] == "0-day streak", f"streak mismatch: {data_en['streak']}"
    assert data_en['selectLevel'] == "Select level:", f"selectLevel mismatch: {data_en['selectLevel']}"
    assert data_en['saveBtn'] == "Save", f"saveBtn mismatch: {data_en['saveBtn']}"
    assert data_en['skipBtn'] == "Skip", f"skipBtn mismatch: {data_en['skipBtn']}"
    assert data_en['summary'] == "You checked on 0/4 things today.", f"summary mismatch: {data_en['summary']}"
    assert data_en['viewBtn'] == "View today's check-in", f"viewBtn mismatch: {data_en['viewBtn']}"
    assert data_en['editBtn'] == "Edit tracking", f"editBtn mismatch: {data_en['editBtn']}"
    print("✓ Test 2 Passed: All English translations match exact user specs!")

    capture_screenshot("rmode_daily_checkin_en.png")
    capture_element(".recovery-left-col", "rmode_daily_checkin_en_closeup.png")

    # -------------------------------------------------------------
    # TEST 3: Switch back to Vietnamese
    # -------------------------------------------------------------
    print("\n--- TEST 3: Switch back to Vietnamese ---")
    eval_js("window.TempoI18n.setLanguage('vi')")
    time.sleep(0.4)

    assert eval_js("document.querySelector('#btn-home-mode-selector span.font-extrabold')?.textContent?.trim()") == "Chế độ Hồi phục"
    assert eval_js("document.querySelector('[data-tempo-ui=\"recovery-self-check\"] .space-y-1 span.uppercase')?.textContent?.trim()") == "CHECK-IN HẰNG NGÀY"
    print("✓ Test 3 Passed: Live toggle back to Vietnamese confirmed!")

    # -------------------------------------------------------------
    # TEST 4: Interactions (Skip and Save)
    # -------------------------------------------------------------
    print("\n--- TEST 4: Check-in Interactions ---")
    # Click Skip on first tracker
    eval_js("window.TempoMode.skipRmodeCurrentSelfCheck('trk_tension')")
    time.sleep(0.4)

    # Next tracker is Sleep quality (options)
    summary_after_skip = eval_js("document.querySelector('[data-tempo-ui=\"recovery-self-check\"] .pt-1.flex.items-center.justify-between.text-xs span')?.textContent?.trim()")
    print("Summary after skip:", summary_after_skip)
    assert summary_after_skip == "Bạn đã check-in 0/4 mục hôm nay."

    # Answer sleep quality
    eval_js("window.TempoMode.submitRmodeSelfCheckValue('trk_sleep', 'Good')")
    time.sleep(0.4)

    summary_after_answer = eval_js("document.querySelector('[data-tempo-ui=\"recovery-self-check\"] .pt-1.flex.items-center.justify-between.text-xs span')?.textContent?.trim()")
    print("Summary after answer 1:", summary_after_answer)
    assert summary_after_answer == "Bạn đã check-in 1/4 mục hôm nay."
    print("✓ Test 4 Passed: Check-in interactions work smoothly!")

    print("\n=== ALL DAILY CHECK-IN TESTS PASSED SUCCESSFULLY! ===")

finally:
    try:
        ws.close()
    except Exception:
        pass
    proc.kill()
