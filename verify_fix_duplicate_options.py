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
PORT = 9227
USER_DATA = r"C:\Users\YEN NHI\AppData\Local\Temp\edge_test_duplicate_options"
ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"

def start_edge():
    cmd = [
        EDGE_PATH,
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={USER_DATA}",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1280,1000",
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

def run_test():
    print("Starting Edge on port", PORT)
    proc = start_edge()
    time.sleep(2)

    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json")
        tabs = json.loads(req.read().decode())
        page_tabs = [t for t in tabs if t.get("type") == "page"]
        target = page_tabs[0] if page_tabs else tabs[0]
        ws_url = target["webSocketDebuggerUrl"]
        print("Connecting to CDP target:", target.get("url"))
        ws = create_connection(ws_url)

        send_cdp(ws, "Page.enable")
        send_cdp(ws, "Runtime.enable")
        time.sleep(1)

        for _ in range(20):
            ready = evaluate_js(ws, "Boolean(window.TempoRecoverySelfCheck && window.TempoRecoverySelfCheck.calculateTrackingSummary)")
            if ready:
                break
            time.sleep(0.5)

        # 1. Unit Tests for calculateTrackingSummary option deduplication & formatting
        print("\n=== 1. Unit Tests: calculateTrackingSummary ===")
        unit_results = evaluate_js(ws, """
        (() => {
            const fn = window.TempoRecoverySelfCheck.calculateTrackingSummary;

            // Scenario A: User prompt exact scenario
            // Sleep tracker with observations:
            // 5 'Good', 4 'Not good', 1 'not_good' (total 10)
            const trkSleep = { id: 'trk_sleep', name: 'Sleep', check_method: 'options', options: ['Good', 'Not good'] };
            const obsSleep = [
                { status: 'answered', value: 'Good' },
                { status: 'answered', value: 'Good' },
                { status: 'answered', value: 'Good' },
                { status: 'answered', value: 'Good' },
                { status: 'answered', value: 'Good' },
                { status: 'answered', value: 'Not good' },
                { status: 'answered', value: 'Not good' },
                { status: 'answered', value: 'Not good' },
                { status: 'answered', value: 'Not good' },
                { status: 'answered', value: 'not_good' }
            ];
            const resSleep = fn(trkSleep, obsSleep, { isVi: false });

            // Scenario B: Vietnamese Sleep tracker
            // 3 'Tốt', 2 'Chưa tốt', 1 'not_good' (total 6) -> 3 Tốt (50%), 3 Chưa tốt (50%)
            const trkSleepVi = { id: 'trk_sleep_vi', name: 'Giấc ngủ', check_method: 'options', options: ['Tốt', 'Chưa tốt'] };
            const obsSleepVi = [
                { status: 'answered', value: 'Tốt' },
                { status: 'answered', value: 'Tốt' },
                { status: 'answered', value: 'Tốt' },
                { status: 'answered', value: 'Chưa tốt' },
                { status: 'answered', value: 'Chưa tốt' },
                { status: 'answered', value: 'not_good' }
            ];
            const resSleepVi = fn(trkSleepVi, obsSleepVi, { isVi: true });

            // Scenario C: Custom distinct options (should remain separate)
            // ['High', 'Medium', 'Low']
            const trkCustom = { id: 'trk_custom', name: 'Mood', check_method: 'options', options: ['High', 'Medium', 'Low'] };
            const obsCustom = [
                { status: 'answered', value: 'High' },
                { status: 'answered', value: 'high' },
                { status: 'answered', value: 'Medium' },
                { status: 'answered', value: 'medium' },
                { status: 'answered', value: 'Low' },
                { status: 'answered', value: 'low' }
            ];
            const resCustom = fn(trkCustom, obsCustom, { isVi: false });

            // Scenario D: Legacy data where options array was null on Sleep tracker
            const trkLegacySleep = { id: 'trk_leg_sleep', name: 'Sleep', check_method: 'options', options: null };
            const obsLegacySleep = [
                { status: 'answered', value: 'Good' },
                { status: 'answered', value: 'not_good' }
            ];
            const resLegacySleep = fn(trkLegacySleep, obsLegacySleep, { isVi: false });

            return { resSleep, resSleepVi, resCustom, resLegacySleep };
        })()
        """)

        print("Unit test Sleep (EN):", unit_results["resSleep"])
        assert unit_results["resSleep"]["metricValue"] == "Good (50%) · Not good (50%)", \
            f"Expected 'Good (50%) · Not good (50%)', got: {unit_results['resSleep']['metricValue']}"
        print("✓ Sleep (EN) correctly aggregated Not good (4) + not_good (1) into 50% and formatted as 'Good (50%) · Not good (50%)'!")

        print("Unit test Sleep (VI):", unit_results["resSleepVi"])
        assert unit_results["resSleepVi"]["metricValue"] == "Tốt (50%) · Chưa tốt (50%)", \
            f"Expected 'Tốt (50%) · Chưa tốt (50%)', got: {unit_results['resSleepVi']['metricValue']}"
        print("✓ Sleep (VI) correctly aggregated Chưa tốt (2) + not_good (1) into 50% and formatted as 'Tốt (50%) · Chưa tốt (50%)'!")

        print("Unit test Custom distinct options:", unit_results["resCustom"])
        assert unit_results["resCustom"]["metricValue"] == "High (33%) · Medium (33%) · Low (33%)", \
            f"Expected 'High (33%) · Medium (33%) · Low (33%)', got: {unit_results['resCustom']['metricValue']}"
        print("✓ Genuinely distinct custom options remain separate and preserved!")

        print("Unit test Legacy Sleep with null options:", unit_results["resLegacySleep"])
        assert unit_results["resLegacySleep"]["metricValue"] == "Good (50%) · Not good (50%)", \
            f"Expected 'Good (50%) · Not good (50%)', got: {unit_results['resLegacySleep']['metricValue']}"
        print("✓ Legacy Sleep data handled safely without duplicate options!")

        # 2. UI Test on Recently Card in live application
        print("\n=== 2. UI Test: Live Recently Card ===")
        evaluate_js(ws, """
        (() => {
            sessionStorage.setItem('tempo_rmode_session_welcomed_local_user', 'true');
            if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.closeSetupModal === 'function') {
                window.TempoRecoverySetup.closeSetupModal();
            }

            const today = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTodayDateStr === 'function')
                ? window.TempoRecoverySelfCheck.getTodayDateStr()
                : new Date().toISOString().slice(0, 10);

            const uid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function')
                ? (window.TempoAuth.getCurrentUserId() || 'local_user')
                : 'local_user';

            // Configure trackers
            const trackers = [
                { id: 'trk_sleep_live', name: 'Sleep', category: 'supportive', check_method: 'options', options: ['Good', 'Not good'], type_color: '#5A9E75' },
                { id: 'trk_tension_live', name: 'Tension', category: 'stress_sign', check_method: 'percentage', type_color: '#D48366' },
                { id: 'trk_mood_live', name: 'Mood', category: 'supportive', check_method: 'options', options: ['Good', 'Neutral', 'Low'], type_color: '#166545' }
            ];

            // Observations with historical mix on 10 distinct dates:
            // 5 'Good', 4 'Not good', 1 'not_good' (total 10)
            const observations = [
                { id: 'o1', tracker_id: 'trk_sleep_live', date: '2026-10-24', status: 'answered', value: 'Good', check_method: 'options' },
                { id: 'o2', tracker_id: 'trk_sleep_live', date: '2026-10-25', status: 'answered', value: 'Good', check_method: 'options' },
                { id: 'o3', tracker_id: 'trk_sleep_live', date: '2026-10-26', status: 'answered', value: 'Good', check_method: 'options' },
                { id: 'o4', tracker_id: 'trk_sleep_live', date: '2026-10-27', status: 'answered', value: 'Good', check_method: 'options' },
                { id: 'o5', tracker_id: 'trk_sleep_live', date: '2026-10-28', status: 'answered', value: 'Good', check_method: 'options' },
                { id: 'o6', tracker_id: 'trk_sleep_live', date: '2026-10-29', status: 'answered', value: 'Not good', check_method: 'options' },
                { id: 'o7', tracker_id: 'trk_sleep_live', date: '2026-10-30', status: 'answered', value: 'Not good', check_method: 'options' },
                { id: 'o8', tracker_id: 'trk_sleep_live', date: '2026-10-31', status: 'answered', value: 'Not good', check_method: 'options' },
                { id: 'o9', tracker_id: 'trk_sleep_live', date: '2026-11-01', status: 'answered', value: 'Not good', check_method: 'options' },
                { id: 'o10', tracker_id: 'trk_sleep_live', date: today, status: 'answered', value: 'not_good', check_method: 'options' },

                // Tension
                { id: 'o11', tracker_id: 'trk_tension_live', date: today, status: 'answered', value: 45, check_method: 'percentage' },

                // Mood: 2 Good, 2 Neutral, 1 Low (total 5) -> 40%, 40%, 20%
                { id: 'o12', tracker_id: 'trk_mood_live', date: '2026-10-29', status: 'answered', value: 'Good', check_method: 'options' },
                { id: 'o13', tracker_id: 'trk_mood_live', date: '2026-10-30', status: 'answered', value: 'Good', check_method: 'options' },
                { id: 'o14', tracker_id: 'trk_mood_live', date: '2026-10-31', status: 'answered', value: 'Neutral', check_method: 'options' },
                { id: 'o15', tracker_id: 'trk_mood_live', date: '2026-11-01', status: 'answered', value: 'Neutral', check_method: 'options' },
                { id: 'o16', tracker_id: 'trk_mood_live', date: today, status: 'answered', value: 'Low', check_method: 'options' }
            ];

            localStorage.setItem(`tempo_selfcheck_trackers_${uid}`, JSON.stringify(trackers));
            localStorage.setItem('tempo_selfcheck_trackers', JSON.stringify(trackers));
            localStorage.setItem(`tempo_selfcheck_observations_${uid}`, JSON.stringify(observations));
            localStorage.setItem('tempo_selfcheck_observations', JSON.stringify(observations));

            localStorage.setItem('tempo_current_mode', 'recovery');
            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
                window.TempoMode.setMode('recovery');
            }
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('en');
            }
            if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
                window.TempoMode.renderRmodeHome();
            }
        })()
        """)
        time.sleep(1)

        # Inspect Recently card in English mode
        recently_en = evaluate_js(ws, """
        (() => {
            const card = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!card) return null;
            const items = Array.from(card.querySelectorAll('.flex.items-start.justify-between')).map(el => {
                const nameEl = el.querySelector('.truncate');
                const descEl = el.querySelector('p');
                const valEl = el.querySelector('.text-right');
                return {
                    name: nameEl ? nameEl.textContent.trim() : '',
                    desc: descEl ? descEl.textContent.trim() : '',
                    val: valEl ? valEl.textContent.trim() : ''
                };
            });
            return items;
        })()
        """)

        print("Recently Card items in English mode:")
        for it in recently_en or []:
            print(f"  Tracker: {it['name']} | Label: {it['desc']} | Value: {it['val']}")

        sleep_item_en = next((i for i in (recently_en or []) if i['name'] == 'Sleep'), None)
        assert sleep_item_en, "Expected 'Sleep' item in Recently card"
        assert sleep_item_en['val'] == "Good (50%) · Not good (50%)", \
            f"Expected 'Good (50%) · Not good (50%)', got: {sleep_item_en['val']}"
        assert "not_good" not in sleep_item_en['val'], "Internal identifier 'not_good' should not appear!"
        assert "/" not in sleep_item_en['val'], "Denominators should not appear in Options display!"
        print("✓ Recently Card Sleep item verified: 'Good (50%) · Not good (50%)'!")

        mood_item_en = next((i for i in (recently_en or []) if i['name'] == 'Mood'), None)
        assert mood_item_en, "Expected 'Mood' item in Recently card"
        assert mood_item_en['val'] == "Good (40%) · Neutral (40%) · Low (20%)", \
            f"Expected 'Good (40%) · Neutral (40%) · Low (20%)', got: {mood_item_en['val']}"
        print("✓ Recently Card Mood item verified: 'Good (40%) · Neutral (40%) · Low (20%)'!")

        # Capture closeup screenshot of Recently Card in English mode
        clip_recently_en = evaluate_js(ws, """
        (() => {
            const el = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return { x: r.x, y: r.y, width: r.width, height: r.height, scale: 1 };
        })()
        """)
        if clip_recently_en:
            capture_screenshot(ws, clip_recently_en, os.path.join(ARTIFACT_DIR, "recently_card_dedup_options_en.png"))

        # Switch to Vietnamese mode
        evaluate_js(ws, """
        (() => {
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('vi');
            }
            if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
                window.TempoMode.renderRmodeHome();
            }
        })()
        """)
        time.sleep(0.5)

        recently_vi = evaluate_js(ws, """
        (() => {
            const card = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!card) return null;
            const items = Array.from(card.querySelectorAll('.flex.items-start.justify-between')).map(el => {
                const nameEl = el.querySelector('.truncate');
                const descEl = el.querySelector('p');
                const valEl = el.querySelector('.text-right');
                return {
                    name: nameEl ? nameEl.textContent.trim() : '',
                    desc: descEl ? descEl.textContent.trim() : '',
                    val: valEl ? valEl.textContent.trim() : ''
                };
            });
            return items;
        })()
        """)

        print("\nRecently Card items in Vietnamese mode:")
        for it in recently_vi or []:
            print(f"  Tracker: {it['name']} | Label: {it['desc']} | Value: {it['val']}")

        sleep_item_vi = next((i for i in (recently_vi or []) if i['name'] == 'Sleep'), None)
        assert sleep_item_vi, "Expected 'Sleep' item in Recently card"
        assert sleep_item_vi['val'] == "Good (50%) · Not good (50%)", \
            f"Expected 'Good (50%) · Not good (50%)', got: {sleep_item_vi['val']}"
        assert sleep_item_vi['desc'] == "Tỷ lệ lựa chọn", \
            f"Expected 'Tỷ lệ lựa chọn', got: {sleep_item_vi['desc']}"
        print("✓ Recently Card Sleep item in Vietnamese mode verified: 'Good (50%) · Not good (50%)' with label 'Tỷ lệ lựa chọn'!")

        # Capture closeup screenshot of Recently Card in Vietnamese mode
        clip_recently_vi = evaluate_js(ws, """
        (() => {
            const el = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return { x: r.x, y: r.y, width: r.width, height: r.height, scale: 1 };
        })()
        """)
        if clip_recently_vi:
            capture_screenshot(ws, clip_recently_vi, os.path.join(ARTIFACT_DIR, "recently_card_dedup_options_vi.png"))

        # Verify raw historical data in localStorage has NOT been modified or deleted
        raw_check = evaluate_js(ws, """
        (() => {
            const uid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function')
                ? (window.TempoAuth.getCurrentUserId() || 'local_user')
                : 'local_user';
            const raw = localStorage.getItem(`tempo_selfcheck_observations_${uid}`);
            const list = JSON.parse(raw);
            const o10 = list.find(o => o.id === 'o10');
            const o9 = list.find(o => o.id === 'o9');
            return {
                totalCount: list.length,
                o10Value: o10 ? o10.value : null,
                o9Value: o9 ? o9.value : null
            };
        })()
        """)
        print("\nRaw data verification in localStorage:", raw_check)
        assert raw_check["totalCount"] == 16, f"Expected 16 raw observations, found {raw_check['totalCount']}"
        assert raw_check["o10Value"] == "not_good", f"Expected raw observation 'not_good' preserved, found {raw_check['o10Value']}"
        assert raw_check["o9Value"] == "Not good", f"Expected raw observation 'Not good' preserved, found {raw_check['o9Value']}"
        print("✓ Raw historical check-in records strictly preserved without data loss or overwriting!")

        print("\n=======================================================")
        print("ALL DUPLICATE OPTIONS FIX VERIFICATION CHECKS PASSED!")
        print("=======================================================")

    finally:
        try:
            ws.close()
        except Exception:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    run_test()
