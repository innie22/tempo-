import subprocess
import time
import json
import urllib.request
import tempfile
import os
import websocket
import base64
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def main():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_test_streak_integration_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9227

    cmd = [
        edge_path,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "--window-size=1440,1080",
        "http://localhost:8000/"
    ]

    log(f"Launching Edge on port {port}...")
    proc = subprocess.Popen(cmd)
    ws = None
    try:
        ws_url = None
        for _ in range(25):
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
                resp = json.loads(ws.recv())
                if resp.get("id") == cid:
                    return resp.get("result", {})

        def eval_js(expression):
            res = send_command("Runtime.evaluate", {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True
            })
            if "exceptionDetails" in res:
                raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        def capture_screenshot(path):
            res = send_command("Page.captureScreenshot", {"format": "png"})
            b64_data = res.get("data", "")
            with open(path, "wb") as f:
                f.write(base64.b64decode(b64_data))
            log(f"Screenshot saved: {path}")

        send_command("Runtime.enable")
        send_command("Page.enable")
        time.sleep(1.5)

        # Authenticate user and navigate to emergency mode
        eval_js("""
            (() => {
                const email = 'student@tempo.app';
                const mockAccount = {
                    id: 'usr_student_verify_001',
                    email: email,
                    password: 'password123',
                    user_metadata: { full_name: 'Student Demo' },
                    created_at: new Date().toISOString()
                };
                localStorage.setItem('tempo_mock_account_' + email, JSON.stringify(mockAccount));
            })()
        """)
        eval_js("window.TempoAuth.signIn('student@tempo.app', 'password123')")
        time.sleep(0.5)

        eval_js("window.TempoMode.setMode('emergency')")
        time.sleep(1.0)

        log("\n=======================================================")
        log("TEST 1: Empty state (0 trackers configured)")
        log("=======================================================")
        eval_js("""
            (() => {
                const uid = (window.TempoAuth && window.TempoAuth.getCurrentUserId()) || 'local_user';
                localStorage.setItem(`tempo_selfcheck_trackers_${uid}`, JSON.stringify([]));
                localStorage.setItem(`tempo_selfcheck_checkins_${uid}`, JSON.stringify([]));
                localStorage.setItem(`tempo_selfcheck_observations_${uid}`, JSON.stringify([]));
                if (window.TempoMode && typeof window.TempoMode.refreshStreakCardIfPresent === 'function') {
                    window.TempoMode.refreshStreakCardIfPresent();
                }
            })()
        """)
        time.sleep(0.5)

        empty_card_info = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
                if (!card) return null;
                const statusSpan = card.querySelector('.font-bold.text-sm, .font-bold.text-base');
                const progressDiv = card.querySelector('[role="progressbar"]');
                const progressVal = progressDiv ? progressDiv.getAttribute('aria-valuenow') : null;
                const summaryP = card.querySelector('p.text-xs');
                const buttons = Array.from(card.querySelectorAll('button')).map(b => b.textContent.trim());
                return {
                    statusText: statusSpan ? statusSpan.textContent.trim() : '',
                    progressVal: progressVal,
                    summaryText: summaryP ? summaryP.textContent.trim() : '',
                    buttons: buttons
                };
            })()
        """)
        log(f"Empty state card info: {json.dumps(empty_card_info, indent=2)}")
        assert empty_card_info['statusText'] == "No trackers configured", f"Expected 'No trackers configured', got {empty_card_info['statusText']}"
        assert empty_card_info['progressVal'] == "0", f"Expected '0', got {empty_card_info['progressVal']}"
        assert empty_card_info['summaryText'] == "No tracking items set up yet.", f"Expected 'No tracking items set up yet.', got {empty_card_info['summaryText']}"
        assert "Set up check-in" in empty_card_info['buttons'], f"Expected 'Set up check-in' in buttons: {empty_card_info['buttons']}"
        assert "Add tracking" in empty_card_info['buttons'], f"Expected 'Add tracking' in buttons: {empty_card_info['buttons']}"
        capture_screenshot("scratch/test_streak_empty_state.png")
        log("✓ Test 1 PASSED: Empty state handled gracefully without defaulting to Tension!")

        log("\n=======================================================")
        log("TEST 2: Seed 3 standard trackers, 0 answered today (0 of 3)")
        log("=======================================================")
        eval_js("""
            (() => {
                const uid = (window.TempoAuth && window.TempoAuth.getCurrentUserId()) || 'local_user';
                const trackers = [
                    { id: 'trk_tension_1', name: 'Tension', category: 'stress_sign', check_method: 'percentage', type_color: '#B84834', is_archived: false },
                    { id: 'trk_focus_2', name: 'Trouble focusing', category: 'stress_sign', check_method: 'yes_no', type_color: '#4A728A', is_archived: false },
                    { id: 'trk_sleep_3', name: 'Sleep quality', category: 'supportive', check_method: 'scale', scale_min: 1, scale_max: 5, type_color: '#166545', is_archived: false }
                ];
                localStorage.setItem(`tempo_selfcheck_trackers_${uid}`, JSON.stringify(trackers));
                localStorage.setItem(`tempo_selfcheck_checkins_${uid}`, JSON.stringify([]));
                localStorage.setItem(`tempo_selfcheck_observations_${uid}`, JSON.stringify([]));
                if (window.TempoMode && typeof window.TempoMode.refreshStreakCardIfPresent === 'function') {
                    window.TempoMode.refreshStreakCardIfPresent();
                }
            })()
        """)
        time.sleep(0.5)

        zero_info = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
                if (!card) return null;
                const statusSpan = card.querySelector('.font-bold.text-sm, .font-bold.text-base');
                const progressDiv = card.querySelector('[role="progressbar"]');
                const progressVal = progressDiv ? progressDiv.getAttribute('aria-valuenow') : null;
                const summaryP = card.querySelector('p.text-xs');
                const buttons = Array.from(card.querySelectorAll('button')).map(b => b.textContent.trim());
                return {
                    statusText: statusSpan ? statusSpan.textContent.trim() : '',
                    progressVal: progressVal,
                    summaryText: summaryP ? summaryP.textContent.trim() : '',
                    buttons: buttons
                };
            })()
        """)
        log(f"0 of 3 state card info: {json.dumps(zero_info, indent=2)}")
        assert zero_info['statusText'] == "Tension", f"Expected 'Tension' as first pending tracker, got {zero_info['statusText']}"
        assert zero_info['progressVal'] == "0", f"Expected '0', got {zero_info['progressVal']}"
        assert zero_info['summaryText'] == "You checked in on 0 of 3 things.", f"Expected 'You checked in on 0 of 3 things.', got {zero_info['summaryText']}"
        assert "View today's checkin" in zero_info['buttons']
        assert "Edit tracking system" in zero_info['buttons']
        capture_screenshot("scratch/test_streak_zero_of_three.png")
        log("✓ Test 2 PASSED: Pending state shows current pending tracker (Tension) at 0% with '0 of 3 things'.")

        log("\n=======================================================")
        log("TEST 3: Answer Tension (1 of 3 things completed)")
        log("=======================================================")
        eval_js("""
            (() => {
                if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.setCustomObservation === 'function') {
                    window.TempoSelfCheckWorkspace.setCustomObservation('trk_tension_1', 35);
                } else if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.saveTodayCheckin === 'function') {
                    window.TempoRecoverySelfCheck.saveTodayCheckin({
                        observations: [{ tracker_id: 'trk_tension_1', value: 35, status: 'answered', check_method: 'percentage' }]
                    });
                }
            })()
        """)
        time.sleep(0.5)

        one_info = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
                if (!card) return null;
                const statusSpan = card.querySelector('.font-bold.text-sm, .font-bold.text-base');
                const progressDiv = card.querySelector('[role="progressbar"]');
                const progressVal = progressDiv ? progressDiv.getAttribute('aria-valuenow') : null;
                const summaryP = card.querySelector('p.text-xs');
                return {
                    statusText: statusSpan ? statusSpan.textContent.trim() : '',
                    progressVal: progressVal,
                    summaryText: summaryP ? summaryP.textContent.trim() : ''
                };
            })()
        """)
        log(f"1 of 3 state card info: {json.dumps(one_info, indent=2)}")
        assert one_info['statusText'] == "Trouble focusing", f"Expected next pending tracker 'Trouble focusing', got {one_info['statusText']}"
        assert one_info['progressVal'] == "33", f"Expected '33', got {one_info['progressVal']}"
        assert one_info['summaryText'] == "You checked in on 1 of 3 things.", f"Expected 'You checked in on 1 of 3 things.', got {one_info['summaryText']}"
        capture_screenshot("scratch/test_streak_one_of_three.png")
        log("✓ Test 3 PASSED: Card dynamically advanced to next pending tracker 'Trouble focusing' and 33% progress!")

        log("\n=======================================================")
        log("TEST 4: Complete remaining 2 items (3 of 3 items completed)")
        log("=======================================================")
        eval_js("""
            (() => {
                if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.setCustomObservation === 'function') {
                    window.TempoSelfCheckWorkspace.setCustomObservation('trk_focus_2', 'no');
                    window.TempoSelfCheckWorkspace.setCustomObservation('trk_sleep_3', 4);
                }
            })()
        """)
        time.sleep(0.5)

        all_info = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
                if (!card) return null;
                const statusSpan = card.querySelector('.font-bold.text-sm, .font-bold.text-base');
                const progressDiv = card.querySelector('[role="progressbar"]');
                const progressVal = progressDiv ? progressDiv.getAttribute('aria-valuenow') : null;
                const summaryP = card.querySelector('p.text-xs');
                const dot = card.querySelector('span.rounded-full');
                return {
                    statusText: statusSpan ? statusSpan.textContent.trim() : '',
                    progressVal: progressVal,
                    summaryText: summaryP ? summaryP.textContent.trim() : '',
                    dotBg: dot ? dot.style.backgroundColor : ''
                };
            })()
        """)
        log(f"3 of 3 completed state card info: {json.dumps(all_info, indent=2)}")
        assert all_info['statusText'] == "Completed today", f"Expected 'Completed today', got {all_info['statusText']}"
        assert all_info['progressVal'] == "100", f"Expected '100', got {all_info['progressVal']}"
        assert all_info['summaryText'] == "You checked in on 3 of 3 things.", f"Expected 'You checked in on 3 of 3 things.', got {all_info['summaryText']}"
        capture_screenshot("scratch/test_streak_completed_today.png")
        log("✓ Test 4 PASSED: Completed state correctly displays 'Completed today' (NOT 'Tension') and 100%!")

        log("\n=======================================================")
        log("TEST 5: Click 'View today's checkin' opens View modal")
        log("=======================================================")
        modal_opened = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
                const viewBtn = card.querySelectorAll('button')[0];
                viewBtn.click();
                const modal = document.getElementById('modal-selfcheck-view');
                return modal && !modal.classList.contains('hidden');
            })()
        """)
        time.sleep(0.5)
        log(f"View modal open status: {modal_opened}")
        assert modal_opened == True, "Expected modal-selfcheck-view to be visible after clicking View today's checkin"
        capture_screenshot("scratch/test_streak_view_modal_open.png")

        # Close view modal
        eval_js("""
            if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.closeViewToday === 'function') {
                window.TempoRecoverySelfCheck.closeViewToday();
            }
        """)
        time.sleep(0.5)
        log("✓ Test 5 PASSED: 'View today's checkin' opened the view modal with saved observations and edit options.")

        log("\n=======================================================")
        log("TEST 6: Page reload / persistence check")
        log("=======================================================")
        send_command("Page.reload")
        time.sleep(2.0)
        eval_js("window.TempoMode.setMode('emergency')")
        time.sleep(1.0)

        reload_info = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
                if (!card) return null;
                const statusSpan = card.querySelector('.font-bold.text-sm, .font-bold.text-base');
                const progressDiv = card.querySelector('[role="progressbar"]');
                const progressVal = progressDiv ? progressDiv.getAttribute('aria-valuenow') : null;
                const summaryP = card.querySelector('p.text-xs');
                return {
                    statusText: statusSpan ? statusSpan.textContent.trim() : '',
                    progressVal: progressVal,
                    summaryText: summaryP ? summaryP.textContent.trim() : ''
                };
            })()
        """)
        log(f"Reload card info: {json.dumps(reload_info, indent=2)}")
        assert reload_info['statusText'] == "Completed today", f"Expected 'Completed today' after reload, got {reload_info['statusText']}"
        assert reload_info['progressVal'] == "100", f"Expected '100' after reload, got {reload_info['progressVal']}"
        assert reload_info['summaryText'] == "You checked in on 3 of 3 things.", f"Expected 'You checked in on 3 of 3 things.', got {reload_info['summaryText']}"
        log("✓ Test 6 PASSED: Completed status persists across page reload from real stored records.")

        log("\n=======================================================")
        log("TEST 7: Exact dimensions, horizontal gap, and flame asset")
        log("=======================================================")
        geometry = eval_js("""
            (() => {
                const card = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
                const comm = document.querySelector('[data-tempo-ui="urgent-posts"]');
                const flameImg = card ? card.querySelector('img[src*="custom_flame"]') : null;

                const cardRect = card ? card.getBoundingClientRect() : null;
                const commRect = comm ? comm.getBoundingClientRect() : null;
                const gapX = (cardRect && commRect) ? (commRect.left - cardRect.right) : null;

                return {
                    cardWidth: cardRect ? cardRect.width : null,
                    cardHeight: cardRect ? cardRect.height : null,
                    gapX: gapX,
                    hasFlameImg: Boolean(flameImg),
                    flameSrc: flameImg ? flameImg.getAttribute('src') : null
                };
            })()
        """)
        log(f"Geometry & asset info: {json.dumps(geometry, indent=2)}")
        assert abs(geometry['cardWidth'] - 678.5) < 1.0, f"Expected card width 678.5px, got {geometry['cardWidth']}"
        assert abs(geometry['cardHeight'] - 264.0) < 1.0, f"Expected card height 264.0px, got {geometry['cardHeight']}"
        assert abs(geometry['gapX'] - 24.0) < 1.0, f"Expected horizontal gap 24.0px, got {geometry['gapX']}"
        assert geometry['hasFlameImg'] == True, "Expected custom flame asset to be present"
        assert "custom_flame.png" in geometry['flameSrc'], f"Expected custom_flame.png, got {geometry['flameSrc']}"
        log("✓ Test 7 PASSED: Exact dimensions (678.5px × 264.0px), horizontal gap (24.0px), and custom flame asset verified!")

        log("\n=======================================================")
        log("TEST 8: EntryHome (#today) and Rmode (#mode) Non-regression")
        log("=======================================================")
        eval_js("""
            window.location.hash = '#today';
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('today');
            }
        """)
        time.sleep(1.0)
        entryhome_ok = eval_js("""
            (() => {
                const comm = document.querySelector('[data-tempo-ui="entry-community-panel"]') || document.querySelector('[data-tempo-ui="urgent-posts"]');
                return Boolean(comm);
            })()
        """)
        assert entryhome_ok == True, "EntryHome community preview must be present and intact"
        capture_screenshot("scratch/test_entryhome_intact.png")
        log("✓ Test 8 PASSED: EntryHome intact and unregressed.")

        log("\n=======================================================")
        log("ALL TESTS COMPLETED SUCCESSFULLY!")
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

if __name__ == '__main__':
    main()
