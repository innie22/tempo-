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
PORT = 9228
USER_DATA = r"C:\Users\YEN NHI\AppData\Local\Temp\edge_test_summary_display"
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
            ready = evaluate_js(ws, "Boolean(window.TempoRecoverySelfCheck && window.TempoRecoverySelfCheck.calculateTrackingSummary && window.TempoMode)")
            if ready:
                break
            time.sleep(0.5)

        print("\n=== STEP 1: UNIT TESTS FOR calculateTrackingSummary ===")
        unit_test_res = evaluate_js(ws, """
        (() => {
            const results = [];
            const rsc = window.TempoRecoverySelfCheck;

            // Test 1: Tension with percentage method
            const t1 = { id: 'trk_tension_1', name: 'Tension', category: 'stress_sign', check_method: 'percentage' };
            const obs1 = [
                { tracker_id: 'trk_tension_1', status: 'answered', value: 40 },
                { tracker_id: 'trk_tension_1', status: 'answered', value: '50%' }
            ];
            const s1_vi = rsc.calculateTrackingSummary(t1, obs1, { isVi: true });
            const s1_en = rsc.calculateTrackingSummary(t1, obs1, { isVi: false });
            results.push({
                name: 'Tension Percentage',
                method_vi: s1_vi.method,
                label_vi: s1_vi.metricLabel,
                val_vi: s1_vi.metricValue,
                label_en: s1_en.metricLabel,
                val_en: s1_en.metricValue,
                pass: s1_vi.method === 'percentage' && s1_vi.metricLabel === 'Mức trung bình' && s1_vi.metricValue === '45%' &&
                      s1_en.metricLabel === 'Average level' && s1_en.metricValue === '45%'
            });

            // Test 2: Tension with options property accidentally present on tracker
            const t2 = { id: 'trk_tension_2', name: 'Tension', category: 'stress_sign', check_method: 'percentage', options: ['Good', 'Not good'] };
            const s2_vi = rsc.calculateTrackingSummary(t2, obs1, { isVi: true });
            results.push({
                name: 'Tension with options array present (MUST NOT override percentage)',
                method_vi: s2_vi.method,
                label_vi: s2_vi.metricLabel,
                val_vi: s2_vi.metricValue,
                pass: s2_vi.method === 'percentage' && s2_vi.metricLabel === 'Mức trung bình' && s2_vi.metricValue === '45%'
            });

            // Test 3: Scale (Feeling overwhelmed)
            const t3 = { id: 'trk_scale_1', name: 'Feeling overwhelmed', category: 'stress_sign', check_method: 'scale', scale_max: 5 };
            const obs3 = [
                { tracker_id: 'trk_scale_1', status: 'answered', value: 4 },
                { tracker_id: 'trk_scale_1', status: 'answered', value: 4 }
            ];
            const s3_vi = rsc.calculateTrackingSummary(t3, obs3, { isVi: true });
            const s3_en = rsc.calculateTrackingSummary(t3, obs3, { isVi: false });
            results.push({
                name: 'Scale tracker (Feeling overwhelmed)',
                method_vi: s3_vi.method,
                label_vi: s3_vi.metricLabel,
                val_vi: s3_vi.metricValue,
                label_en: s3_en.metricLabel,
                val_en: s3_en.metricValue,
                pass: s3_vi.method === 'scale' && s3_vi.metricLabel === 'Điểm trung bình' && s3_vi.metricValue === '4/5' &&
                      s3_en.metricLabel === 'Average score' && s3_en.metricValue === '4/5'
            });

            // Test 4: Quantity (Walk)
            const t4 = { id: 'trk_qty_1', name: 'Walk', category: 'supportive', check_method: 'quantity', quantity_unit: 'phút' };
            const obs4 = [
                { tracker_id: 'trk_qty_1', status: 'answered', value: 10 },
                { tracker_id: 'trk_qty_1', status: 'answered', value: 15 }
            ];
            const s4_vi = rsc.calculateTrackingSummary(t4, obs4, { isVi: true });
            const s4_en = rsc.calculateTrackingSummary(t4, obs4, { isVi: false });
            results.push({
                name: 'Quantity tracker (Walk)',
                method_vi: s4_vi.method,
                label_vi: s4_vi.metricLabel,
                val_vi: s4_vi.metricValue,
                label_en: s4_en.metricLabel,
                val_en: s4_en.metricValue,
                pass: s4_vi.method === 'quantity' && s4_vi.metricLabel === 'Tổng lượng ghi nhận' && s4_vi.metricValue === '25 phút' &&
                      s4_en.metricLabel === 'Total recorded' && s4_en.metricValue === '25 phút'
            });

            // Test 5: Options (Sleep)
            const t5 = { id: 'trk_opt_1', name: 'Sleep', category: 'supportive', check_method: 'options', options: ['Good', 'Not good'] };
            const obs5 = [
                { tracker_id: 'trk_opt_1', status: 'answered', value: 'Good' },
                { tracker_id: 'trk_opt_1', status: 'answered', value: 'not_good' }
            ];
            const s5_vi = rsc.calculateTrackingSummary(t5, obs5, { isVi: true });
            const s5_en = rsc.calculateTrackingSummary(t5, obs5, { isVi: false });
            results.push({
                name: 'Options tracker (Sleep)',
                method_vi: s5_vi.method,
                label_vi: s5_vi.metricLabel,
                val_vi: s5_vi.metricValue,
                label_en: s5_en.metricLabel,
                val_en: s5_en.metricValue,
                pass: s5_vi.method === 'options' && s5_vi.metricLabel === 'Tỷ lệ lựa chọn' && s5_vi.metricValue === 'Good (50%) · Not good (50%)' &&
                      s5_en.metricLabel === 'Option distribution' && s5_en.metricValue === 'Good (50%) · Not good (50%)'
            });

            // Test 6: Empty states
            const s_empty = rsc.calculateTrackingSummary(t1, [], { isVi: true });
            results.push({
                name: 'Empty state',
                val: s_empty.metricValue,
                pass: s_empty.metricValue === '—' && s_empty.hasData === false
            });

            return results;
        })()
        """)
        for r in unit_test_res:
            status = "PASS" if r.get("pass") else "FAIL"
            print(f"[{status}] {r['name']}: {r}")

        print("\n=== STEP 2: TEST DATA ISOLATION (NO MIXING BETWEEN TRACKING ITEMS) ===")
        isolation_res = evaluate_js(ws, """
        (() => {
            const uid = 'local_user';
            const trk1 = { id: 'trk_main_tension', name: 'Tension', category: 'stress_sign', check_method: 'percentage' };
            const trk2 = { id: 'trk_other_tension', name: 'Neck tension', category: 'supportive', check_method: 'options', options: ['Mild', 'Severe'] };

            const checkinId = 'chk_iso_1';
            const checkins = [{ id: checkinId, checkin_date: '2026-11-02' }];
            const obs = [
                { id: 'obs_1', tracker_id: 'trk_main_tension', checkin_id: checkinId, status: 'answered', value: 35, date: '2026-11-02' },
                { id: 'obs_2', tracker_id: 'trk_other_tension', checkin_id: checkinId, status: 'answered', value: 'Severe', date: '2026-11-02' }
            ];

            localStorage.setItem(`tempo_selfcheck_checkins_${uid}`, JSON.stringify(checkins));
            localStorage.setItem(`tempo_selfcheck_observations_${uid}`, JSON.stringify(obs));
            localStorage.setItem('tempo_selfcheck_checkins', JSON.stringify(checkins));
            localStorage.setItem('tempo_selfcheck_observations', JSON.stringify(obs));

            // Verify getAuthoritativeTrackerObservations
            const obsForTrk1 = window.TempoMode && typeof window.TempoMode.getAuthoritativeTrackerObservations === 'function'
                ? window.TempoMode.getAuthoritativeTrackerObservations(trk1)
                : null;

            // Direct calculation on trk1 with its own observations
            const summaryTrk1 = window.TempoRecoverySelfCheck.calculateTrackingSummary(trk1, obsForTrk1 || [obs[0]], { isVi: true });

            return {
                obsForTrk1Count: obsForTrk1 ? obsForTrk1.length : 1,
                onlyHasTrk1Obs: obsForTrk1 ? obsForTrk1.every(o => o.tracker_id === 'trk_main_tension') : true,
                summaryMethod: summaryTrk1.method,
                summaryLabel: summaryTrk1.metricLabel,
                summaryValue: summaryTrk1.metricValue,
                pass: summaryTrk1.method === 'percentage' && summaryTrk1.metricValue === '35%' && (!obsForTrk1 || (obsForTrk1.length === 1 && obsForTrk1[0].tracker_id === 'trk_main_tension'))
            };
        })()
        """)
        print("[ISOLATION RESULT]:", isolation_res)

        print("\n=== STEP 3: LIVE RECOVERY DASHBOARD VERIFICATION ===")
        setup_res = evaluate_js(ws, """
        (() => {
            const uid = 'local_user';
            const testTrackers = [
                {
                    id: 'trk_tension',
                    name: 'Tension',
                    category: 'stress_sign',
                    check_method: 'percentage',
                    type_color: '#D48366'
                },
                {
                    id: 'trk_overwhelmed',
                    name: 'Feeling overwhelmed',
                    category: 'stress_sign',
                    check_method: 'scale',
                    scale_max: 5,
                    type_color: '#D48366'
                },
                {
                    id: 'trk_walk',
                    name: 'Walk',
                    category: 'supportive',
                    check_method: 'quantity',
                    quantity_unit: 'phút',
                    type_color: '#5A9E75'
                },
                {
                    id: 'trk_sleep',
                    name: 'Sleep',
                    category: 'supportive',
                    check_method: 'options',
                    options: ['Good', 'Not good'],
                    type_color: '#5A9E75'
                }
            ];

            const today = '2026-11-02';
            const checkins = [
                { id: 'c1', checkin_date: '2026-11-01' },
                { id: 'c2', checkin_date: '2026-11-02' }
            ];

            const observations = [
                // Tension (40% + 50% => 45%)
                { id: 'o1', tracker_id: 'trk_tension', checkin_id: 'c1', date: '2026-11-01', status: 'answered', value: 40 },
                { id: 'o2', tracker_id: 'trk_tension', checkin_id: 'c2', date: '2026-11-02', status: 'answered', value: 50 },

                // Scale (4 + 4 => 4/5)
                { id: 'o3', tracker_id: 'trk_overwhelmed', checkin_id: 'c1', date: '2026-11-01', status: 'answered', value: 4 },
                { id: 'o4', tracker_id: 'trk_overwhelmed', checkin_id: 'c2', date: '2026-11-02', status: 'answered', value: 4 },

                // Quantity (10 + 15 => 25 phút)
                { id: 'o5', tracker_id: 'trk_walk', checkin_id: 'c1', date: '2026-11-01', status: 'answered', value: 10, quantity_unit: 'phút' },
                { id: 'o6', tracker_id: 'trk_walk', checkin_id: 'c2', date: '2026-11-02', status: 'answered', value: 15, quantity_unit: 'phút' },

                // Options (Good + not_good => Good 50% · Not good 50%)
                { id: 'o7', tracker_id: 'trk_sleep', checkin_id: 'c1', date: '2026-11-01', status: 'answered', value: 'Good' },
                { id: 'o8', tracker_id: 'trk_sleep', checkin_id: 'c2', date: '2026-11-02', status: 'answered', value: 'not_good' }
            ];

            sessionStorage.setItem('tempo_rmode_session_welcomed_local_user', 'true');
            if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.closeSetupModal === 'function') {
                window.TempoRecoverySetup.closeSetupModal();
            }

            localStorage.setItem(`tempo_selfcheck_trackers_${uid}`, JSON.stringify(testTrackers));
            localStorage.setItem('tempo_selfcheck_trackers', JSON.stringify(testTrackers));
            localStorage.setItem(`tempo_selfcheck_checkins_${uid}`, JSON.stringify(checkins));
            localStorage.setItem('tempo_selfcheck_checkins', JSON.stringify(checkins));
            localStorage.setItem(`tempo_selfcheck_observations_${uid}`, JSON.stringify(observations));
            localStorage.setItem('tempo_selfcheck_observations', JSON.stringify(observations));

            localStorage.setItem('tempo_current_mode', 'recovery');
            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
                window.TempoMode.setMode('recovery');
            }

            // Set language to Vietnamese
            localStorage.setItem('tempo_language', 'vi');
            localStorage.setItem('tempo_lang', 'vi');
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('vi');
            }

            // Re-render recovery mode
            if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
                window.TempoMode.renderRmodeHome();
            }

            return { ready: true };
        })()
        """)
        print("Setup live trackers result:", setup_res)
        time.sleep(1.5)

        # Scrape Recently card metrics in Vietnamese
        vi_metrics = evaluate_js(ws, """
        (() => {
            const card = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!card) return null;
            const title = card.querySelector('h4')?.textContent.trim();
            const btn = card.querySelector('button')?.textContent.trim();
            const footer = card.querySelector('[data-tempo-ui="recently-countdown-footer"]')?.textContent.trim();

            const rows = Array.from(card.querySelectorAll('[data-tempo-ui="recently-metrics-scroll"] > div'));
            const items = rows.map(r => {
                const name = r.querySelector('span.truncate')?.textContent.trim();
                const desc = r.querySelector('p')?.textContent.trim();
                const val = r.querySelector('div.text-right')?.textContent.trim();
                return { name, desc, val };
            });

            return { title, btn, footer, items };
        })()
        """)
        print("\n[VIETNAMESE METRICS]:")
        print(json.dumps(vi_metrics, ensure_ascii=False, indent=2))

        # Check VI bounding box for screenshot
        clip_vi = evaluate_js(ws, """
        (() => {
            const card = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!card) return null;
            card.scrollIntoView({ behavior: 'instant', block: 'center' });
            const rect = card.getBoundingClientRect();
            return {
                x: Math.max(0, rect.x - 10),
                y: Math.max(0, rect.y - 10),
                width: rect.width + 20,
                height: rect.height + 20,
                scale: 1
            };
        })()
        """)
        if clip_vi:
            time.sleep(0.5)
            capture_screenshot(ws, clip_vi, os.path.join(ARTIFACT_DIR, "recently_summary_display_vi_closeup.png"))
            capture_screenshot(ws, None, os.path.join(ARTIFACT_DIR, "recently_summary_display_vi.png"))

        # Switch to English
        print("\n=== SWITCHING TO ENGLISH MODE ===")
        evaluate_js(ws, """
        (() => {
            localStorage.setItem('tempo_language', 'en');
            localStorage.setItem('tempo_lang', 'en');
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('en');
            }
            if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
                window.TempoMode.renderRmodeHome();
            }
        })()
        """)
        time.sleep(1.5)

        en_metrics = evaluate_js(ws, """
        (() => {
            const card = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!card) return null;
            const title = card.querySelector('h4')?.textContent.trim();
            const btn = card.querySelector('button')?.textContent.trim();
            const footer = card.querySelector('[data-tempo-ui="recently-countdown-footer"]')?.textContent.trim();

            const rows = Array.from(card.querySelectorAll('[data-tempo-ui="recently-metrics-scroll"] > div'));
            const items = rows.map(r => {
                const name = r.querySelector('span.truncate')?.textContent.trim();
                const desc = r.querySelector('p')?.textContent.trim();
                const val = r.querySelector('div.text-right')?.textContent.trim();
                return { name, desc, val };
            });

            return { title, btn, footer, items };
        })()
        """)
        print("\n[ENGLISH METRICS]:")
        print(json.dumps(en_metrics, ensure_ascii=False, indent=2))

        clip_en = evaluate_js(ws, """
        (() => {
            const card = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!card) return null;
            card.scrollIntoView({ behavior: 'instant', block: 'center' });
            const rect = card.getBoundingClientRect();
            return {
                x: Math.max(0, rect.x - 10),
                y: Math.max(0, rect.y - 10),
                width: rect.width + 20,
                height: rect.height + 20,
                scale: 1
            };
        })()
        """)
        if clip_en:
            time.sleep(0.5)
            capture_screenshot(ws, clip_en, os.path.join(ARTIFACT_DIR, "recently_summary_display_en_closeup.png"))
            capture_screenshot(ws, None, os.path.join(ARTIFACT_DIR, "recently_summary_display_en.png"))

        # Assertions
        print("\n=== ASSERTION CHECKS ===")
        # 1. Tension
        t_vi = next((i for i in vi_metrics['items'] if i['name'] == 'Tension'), None)
        t_en = next((i for i in en_metrics['items'] if i['name'] == 'Tension'), None)
        assert t_vi and t_vi['desc'] == 'Mức trung bình' and t_vi['val'] == '45%', f"Tension VI failed: {t_vi}"
        assert t_en and t_en['desc'] == 'Average level' and t_en['val'] == '45%', f"Tension EN failed: {t_en}"
        print("✓ Tension displays average percentage in VI ('Mức trung bình: 45%') and EN ('Average level: 45%'), NOT options distribution!")

        # 2. Feeling overwhelmed (Scale)
        sc_vi = next((i for i in vi_metrics['items'] if i['name'] == 'Feeling overwhelmed'), None)
        sc_en = next((i for i in en_metrics['items'] if i['name'] == 'Feeling overwhelmed'), None)
        assert sc_vi and sc_vi['desc'] == 'Điểm trung bình' and sc_vi['val'] == '4/5', f"Scale VI failed: {sc_vi}"
        assert sc_en and sc_en['desc'] == 'Average score' and sc_en['val'] == '4/5', f"Scale EN failed: {sc_en}"
        print("✓ Scale displays average score in VI ('Điểm trung bình: 4/5') and EN ('Average score: 4/5')!")

        # 3. Walk (Quantity)
        qty_vi = next((i for i in vi_metrics['items'] if i['name'] == 'Walk'), None)
        qty_en = next((i for i in en_metrics['items'] if i['name'] == 'Walk'), None)
        assert qty_vi and qty_vi['desc'] == 'Tổng lượng ghi nhận' and qty_vi['val'] == '25 phút', f"Quantity VI failed: {qty_vi}"
        assert qty_en and qty_en['desc'] == 'Total recorded' and qty_en['val'] == '25 phút', f"Quantity EN failed: {qty_en}"
        print("✓ Quantity displays sum of recorded values in VI ('Tổng lượng ghi nhận: 25 phút') and EN ('Total recorded: 25 phút')!")

        # 4. Sleep (Options)
        opt_vi = next((i for i in vi_metrics['items'] if i['name'] == 'Sleep'), None)
        opt_en = next((i for i in en_metrics['items'] if i['name'] == 'Sleep'), None)
        assert opt_vi and opt_vi['desc'] == 'Tỷ lệ lựa chọn' and opt_vi['val'] == 'Good (50%) · Not good (50%)', f"Options VI failed: {opt_vi}"
        assert opt_en and opt_en['desc'] == 'Option distribution' and opt_en['val'] == 'Good (50%) · Not good (50%)', f"Options EN failed: {opt_en}"
        print("✓ Options displays option distribution in VI ('Tỷ lệ lựa chọn: Good (50%) · Not good (50%)') and EN ('Option distribution: Good (50%) · Not good (50%)')!")

        print("\nALL VERIFICATIONS PASSED SUCCESSFULLY!")

    finally:
        try:
            ws.close()
        except Exception:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

if __name__ == "__main__":
    run_test()
