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
PORT = 9225
USER_DATA = r"C:\Users\YEN NHI\AppData\Local\Temp\edge_test_tracking_summary"
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
    data = res["result"]["data"]
    import base64
    with open(file_path, "wb") as f:
        f.write(base64.b64decode(data))
    print(f"Captured screenshot to: {file_path}")

def run_tests():
    proc = start_edge()
    time.sleep(2)
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json")
        tabs = json.loads(req.read().decode())
        page_tabs = [t for t in tabs if t.get("type") == "page"]
        ws_url = page_tabs[0]["webSocketDebuggerUrl"]
        ws = create_connection(ws_url)

        # Wait for page to finish loading scripts
        for _ in range(30):
            ready = evaluate_js(ws, "document.readyState === 'complete' && !!window.TempoRecoverySelfCheck && !!window.TempoMode")
            if ready:
                break
            time.sleep(0.5)

        # 1. Unit Tests for calculateTrackingSummary
        test_script = """
        (() => {
            const results = {};
            const fn = window.TempoRecoverySelfCheck.calculateTrackingSummary;
            const lblFn = window.TempoRecoverySelfCheck.getTrackingMethodSummaryLabel;

            // 1. Percentage
            const trkPct = { id: 't_pct', name: 'Tension', check_method: 'percentage' };
            const obsPct = [{ status: 'answered', value: 40 }, { status: 'answered', value: 60 }];
            results.pctVi = fn(trkPct, obsPct, { isVi: true });
            results.pctEn = fn(trkPct, obsPct, { isVi: false });

            // 2. Scale
            const trkScale = { id: 't_scale', name: 'Overwhelmed', check_method: 'scale', scale_max: 5 };
            const obsScale = [{ status: 'answered', value: 3 }, { status: 'answered', value: 4 }, { status: 'answered', value: 5 }];
            results.scaleVi = fn(trkScale, obsScale, { isVi: true });
            results.scaleEn = fn(trkScale, obsScale, { isVi: false });

            // 2b. Scale non-integer
            const obsScaleNonInt = [{ status: 'answered', value: 3 }, { status: 'answered', value: 4 }];
            results.scaleNonInt = fn(trkScale, obsScaleNonInt, { isVi: false });

            // 3. Quantity
            const trkQty1 = { id: 't_qty1', name: 'Đi bộ', check_method: 'quantity', quantity_unit: 'phút' };
            const obsQty1 = [{ status: 'answered', value: 10 }, { status: 'answered', value: 15 }];
            results.qtyVi = fn(trkQty1, obsQty1, { isVi: true });
            results.qtyEn = fn(trkQty1, obsQty1, { isVi: false });

            const trkQty2 = { id: 't_qty2', name: 'Water', check_method: 'quantity', quantity_unit: 'glasses' };
            const obsQty2 = [{ status: 'answered', value: 3 }, { status: 'answered', value: 5 }];
            results.qtyCustom = fn(trkQty2, obsQty2, { isVi: false });

            // 4. Options
            const trkOpt = { id: 't_opt', name: 'Giấc ngủ', check_method: 'options', options: ['Good', 'Not good'] };
            const obsOpt = [
                { status: 'answered', value: 'Good' },
                { status: 'answered', value: 'Good' },
                { status: 'answered', value: 'Good' },
                { status: 'answered', value: 'Good' },
                { status: 'answered', value: 'Good' },
                { status: 'answered', value: 'Not good' },
                { status: 'answered', value: 'Not good' }
            ];
            results.optVi = fn(trkOpt, obsOpt, { isVi: true });
            results.optEn = fn(trkOpt, obsOpt, { isVi: false });

            // 5. Yes / No
            const trkYesNo = { id: 't_yn', name: 'Went outside', check_method: 'yes_no' };
            const obsYesNo = [
                { status: 'answered', value: 'yes' },
                { status: 'answered', value: 'yes' },
                { status: 'answered', value: 'yes' },
                { status: 'answered', value: 'yes' },
                { status: 'answered', value: 'no' }
            ];
            results.yesNoVi = fn(trkYesNo, obsYesNo, { isVi: true });
            results.yesNoEn = fn(trkYesNo, obsYesNo, { isVi: false });

            // 6. Empty Dataset
            results.emptyPct = fn(trkPct, [], { isVi: true });
            results.emptyScale = fn(trkScale, [], { isVi: true });
            results.emptyQty = fn(trkQty1, [], { isVi: true });
            results.emptyOpt = fn(trkOpt, [], { isVi: true });
            results.emptyYesNo = fn(trkYesNo, [], { isVi: true });

            return results;
        })()
        """
        unit_res = evaluate_js(ws, test_script)
        print("=== Unit Test Results ===")
        print("Percentage (VI):", unit_res["pctVi"])
        print("Percentage (EN):", unit_res["pctEn"])
        print("Scale (VI):", unit_res["scaleVi"])
        print("Scale (EN):", unit_res["scaleEn"])
        print("Scale non-int:", unit_res["scaleNonInt"])
        print("Quantity (VI):", unit_res["qtyVi"])
        print("Quantity (EN):", unit_res["qtyEn"])
        print("Quantity custom:", unit_res["qtyCustom"])
        print("Options (VI):", unit_res["optVi"])
        print("Options (EN):", unit_res["optEn"])
        print("Yes/No (VI):", unit_res["yesNoVi"])
        print("Yes/No (EN):", unit_res["yesNoEn"])
        print("Empty (VI):", unit_res["emptyOpt"])

        assert unit_res["pctVi"]["metricLabel"] == "Mức trung bình", "Pct VI label mismatch"
        assert unit_res["pctEn"]["metricLabel"] == "Average level", "Pct EN label mismatch"
        assert unit_res["pctVi"]["metricValue"] == "50%", "Pct value mismatch"

        assert unit_res["scaleVi"]["metricLabel"] == "Điểm trung bình", "Scale VI label mismatch"
        assert unit_res["scaleEn"]["metricLabel"] == "Average score", "Scale EN label mismatch"
        assert unit_res["scaleVi"]["metricValue"] == "4/5", "Scale value mismatch"
        assert unit_res["scaleNonInt"]["metricValue"] == "3.5/5", "Scale non-int value mismatch"

        assert unit_res["qtyVi"]["metricLabel"] == "Tổng lượng ghi nhận", "Qty VI label mismatch"
        assert unit_res["qtyEn"]["metricLabel"] == "Total recorded", "Qty EN label mismatch"
        assert unit_res["qtyVi"]["metricValue"] == "25 phút", "Qty VI value mismatch"
        assert unit_res["qtyCustom"]["metricValue"] == "8 glasses", "Qty custom value mismatch"

        assert unit_res["optVi"]["metricLabel"] == "Tỷ lệ lựa chọn", "Opt VI label mismatch"
        assert unit_res["optEn"]["metricLabel"] == "Option distribution", "Opt EN label mismatch"
        assert unit_res["optVi"]["metricValue"] == "Good (71%) · Not good (29%)", "Opt value mismatch"

        assert unit_res["yesNoVi"]["metricLabel"] == "Tỷ lệ phản hồi", "YesNo VI label mismatch"
        assert unit_res["yesNoEn"]["metricLabel"] == "Response distribution", "YesNo EN label mismatch"
        assert unit_res["yesNoVi"]["metricValue"] == "Có – 80% (4/5), Không – 20% (1/5)", "YesNo VI value mismatch"
        assert unit_res["yesNoEn"]["metricValue"] == "Yes – 80% (4/5), No – 20% (1/5)", "YesNo EN value mismatch"

        assert unit_res["emptyOpt"]["metricLabel"] == "Tỷ lệ lựa chọn", "Empty Opt label mismatch"
        assert unit_res["emptyOpt"]["metricValue"] == "—", "Empty Opt value mismatch"
        print("ALL UNIT TESTS PASSED!\n")

        # 2. UI Test on Rmode Dashboard Recently Card
        setup_ui_script = """
        (() => {
            sessionStorage.setItem('tempo_rmode_session_welcomed_local_user', 'true');
            if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.closeSetupModal === 'function') {
                window.TempoRecoverySetup.closeSetupModal();
            }

            const today = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTodayDateStr === 'function')
                ? window.TempoRecoverySelfCheck.getTodayDateStr()
                : new Date().toISOString().slice(0, 10);

            // Configure trackers covering: percentage, scale, quantity, options, yes_no
            const trackers = [
                { id: 'trk_pct', name: 'Tension', category: 'stress_sign', check_method: 'percentage', type_color: '#D48366' },
                { id: 'trk_scale', name: 'Overwhelmed', category: 'stress_sign', check_method: 'scale', scale_max: 5, type_color: '#D48366' },
                { id: 'trk_qty', name: 'Đi bộ', category: 'supportive', check_method: 'quantity', quantity_unit: 'phút', type_color: '#5A9E75' },
                { id: 'trk_opt', name: 'Giấc ngủ', category: 'supportive', check_method: 'options', options: ['Good', 'Not good'], type_color: '#5A9E75' },
                { id: 'trk_yn', name: 'Went outside', category: 'supportive', check_method: 'yes_no', type_color: '#5A9E75' },
                { id: 'trk_empty', name: 'Đọc sách', category: 'neutral', check_method: 'quantity', quantity_unit: 'trang', type_color: '#7B9688' }
            ];

            const observations = [
                // Tension (percentage): 40, 60 -> avg 50%
                { id: 'obs_1', tracker_id: 'trk_pct', date: '2026-10-30', status: 'answered', value: 40, check_method: 'percentage' },
                { id: 'obs_2', tracker_id: 'trk_pct', date: today, status: 'answered', value: 60, check_method: 'percentage' },

                // Overwhelmed (scale): 3, 5 -> avg 4/5
                { id: 'obs_3', tracker_id: 'trk_scale', date: '2026-10-30', status: 'answered', value: 3, check_method: 'scale' },
                { id: 'obs_4', tracker_id: 'trk_scale', date: today, status: 'answered', value: 5, check_method: 'scale' },

                // Đi bộ (quantity): 10, 15 -> total 25 phút
                { id: 'obs_5', tracker_id: 'trk_qty', date: '2026-10-30', status: 'answered', value: 10, quantity_unit: 'phút', check_method: 'quantity' },
                { id: 'obs_6', tracker_id: 'trk_qty', date: today, status: 'answered', value: 15, quantity_unit: 'phút', check_method: 'quantity' },

                // Giấc ngủ (options): 2 Good, 1 Not good -> Good – 66.7% (2/3), Not good – 33.3% (1/3)
                { id: 'obs_7', tracker_id: 'trk_opt', date: '2026-10-30', status: 'answered', value: 'Good', check_method: 'options' },
                { id: 'obs_8', tracker_id: 'trk_opt', date: '2026-10-31', status: 'answered', value: 'Not good', check_method: 'options' },
                { id: 'obs_9', tracker_id: 'trk_opt', date: today, status: 'answered', value: 'Good', check_method: 'options' },

                // Went outside (yes_no): 2 yes, 1 no -> Có – 66.7% (2/3), Không – 33.3% (1/3)
                { id: 'obs_10', tracker_id: 'trk_yn', date: '2026-10-30', status: 'answered', value: 'yes', check_method: 'yes_no' },
                { id: 'obs_11', tracker_id: 'trk_yn', date: '2026-10-31', status: 'answered', value: 'no', check_method: 'yes_no' },
                { id: 'obs_12', tracker_id: 'trk_yn', date: today, status: 'answered', value: 'yes', check_method: 'yes_no' }

                // trk_empty has no observations
            ];

            const checkins = [
                { id: 'chk_1', checkin_date: '2026-10-30', status: 'completed' },
                { id: 'chk_2', checkin_date: '2026-10-31', status: 'completed' },
                { id: 'chk_3', checkin_date: today, status: 'completed' }
            ];

            const uid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function')
                ? (window.TempoAuth.getCurrentUserId() || 'local_user')
                : 'local_user';

            localStorage.setItem(`tempo_selfcheck_trackers_${uid}`, JSON.stringify(trackers));
            localStorage.setItem('tempo_selfcheck_trackers', JSON.stringify(trackers));
            localStorage.setItem(`tempo_selfcheck_checkins_${uid}`, JSON.stringify(checkins));
            localStorage.setItem('tempo_selfcheck_checkins', JSON.stringify(checkins));
            localStorage.setItem(`tempo_selfcheck_observations_${uid}`, JSON.stringify(observations));
            localStorage.setItem('tempo_selfcheck_observations', JSON.stringify(observations));

            // Set language to Vietnamese and mode to recovery
            localStorage.setItem('tempo_current_mode', 'recovery');
            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
                window.TempoMode.setMode('recovery');
            }
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('vi');
            }
            if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
                window.TempoMode.renderRmodeHome();
            }

            return true;
        })()
        """
        evaluate_js(ws, setup_ui_script)
        time.sleep(1)

        # Inspect Recently card in VI
        inspect_vi_script = """
        (() => {
            const card = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!card) return null;
            const rows = Array.from(card.querySelectorAll('[data-tempo-ui="recently-metrics-scroll"] > div'));
            return rows.map(r => {
                const name = r.querySelector('.truncate')?.textContent?.trim();
                const desc = r.querySelector('p')?.textContent?.trim();
                const val = r.querySelector('.text-right')?.textContent?.trim();
                return { name, desc, val };
            });
        })()
        """
        rows_vi = evaluate_js(ws, inspect_vi_script)
        print("=== Recently Card (VI) ===")
        for r in rows_vi:
            print(f"- {r['name']} | Label: {r['desc']} | Value: {r['val']}")

        # Verify VI expectations
        assert any(r['name'] == 'Tension' and r['desc'] == 'Mức trung bình' and r['val'] == '50%' for r in rows_vi), "Tension VI failed"
        assert any(r['name'] == 'Overwhelmed' and r['desc'] == 'Điểm trung bình' and r['val'] == '4/5' for r in rows_vi), "Overwhelmed VI failed"
        assert any(r['name'] == 'Đi bộ' and r['desc'] == 'Tổng lượng ghi nhận' and r['val'] == '25 phút' for r in rows_vi), "Đi bộ VI failed"
        assert any(r['name'] == 'Giấc ngủ' and r['desc'] == 'Tỷ lệ lựa chọn' and 'Good (67%)' in r['val'] and 'Not good (33%)' in r['val'] for r in rows_vi), "Giấc ngủ VI failed"
        assert any(r['name'] == 'Went outside' and r['desc'] == 'Tỷ lệ phản hồi' and 'Có – 66.7%' in r['val'] and 'Không – 33.3%' in r['val'] for r in rows_vi), "Went outside VI failed"
        assert any(r['name'] == 'Đọc sách' and r['desc'] == 'Tổng lượng ghi nhận' and r['val'] == '—' for r in rows_vi), "Đọc sách Empty VI failed"

        # Capture VI closeup
        box_vi = evaluate_js(ws, """
        (() => {
            const el = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return { x: r.left, y: r.top, width: r.width, height: r.height, scale: 1 };
        })()
        """)
        capture_screenshot(ws, box_vi, os.path.join(ARTIFACT_DIR, "recently_card_standardized_vi_closeup.png"))

        # Switch live to EN
        evaluate_js(ws, """
        (() => {
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('en');
            }
            if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
                window.TempoMode.renderActiveModeHome();
            }
        })()
        """)
        time.sleep(1)

        rows_en = evaluate_js(ws, inspect_vi_script)
        print("\n=== Recently Card (EN) ===")
        for r in rows_en:
            print(f"- {r['name']} | Label: {r['desc']} | Value: {r['val']}")

        assert any(r['name'] == 'Tension' and r['desc'] == 'Average level' and r['val'] == '50%' for r in rows_en), "Tension EN failed"
        assert any(r['name'] == 'Overwhelmed' and r['desc'] == 'Average score' and r['val'] == '4/5' for r in rows_en), "Overwhelmed EN failed"
        assert any(r['name'] == 'Đi bộ' and r['desc'] == 'Total recorded' and '25' in r['val'] for r in rows_en), "Đi bộ EN failed"
        assert any(r['name'] == 'Giấc ngủ' and r['desc'] == 'Option distribution' and 'Good (67%)' in r['val'] and 'Not good (33%)' in r['val'] for r in rows_en), "Giấc ngủ EN failed"
        assert any(r['name'] == 'Went outside' and r['desc'] == 'Response distribution' and 'Yes – 66.7%' in r['val'] and 'No – 33.3%' in r['val'] for r in rows_en), "Went outside EN failed"
        assert any(r['name'] == 'Đọc sách' and r['desc'] == 'Total recorded' and r['val'] == '—' for r in rows_en), "Đọc sách Empty EN failed"

        # Capture EN closeup
        box_en = evaluate_js(ws, """
        (() => {
            const el = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return { x: r.left, y: r.top, width: r.width, height: r.height, scale: 1 };
        })()
        """)
        capture_screenshot(ws, box_en, os.path.join(ARTIFACT_DIR, "recently_card_standardized_en_closeup.png"))

        # Scroll down in recently card and capture bottom items
        evaluate_js(ws, """
        (() => {
            const sc = document.querySelector('[data-tempo-ui="recently-metrics-scroll"]');
            if (sc) sc.scrollTop = sc.scrollHeight;
        })()
        """)
        time.sleep(0.5)
        capture_screenshot(ws, box_en, os.path.join(ARTIFACT_DIR, "recently_card_standardized_en_scrolled.png"))

        # Switch back to VI and capture scrolled VI
        evaluate_js(ws, """
        (() => {
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('vi');
            }
            if (window.TempoMode && typeof window.TempoMode.renderActiveModeHome === 'function') {
                window.TempoMode.renderActiveModeHome();
            }
            const sc = document.querySelector('[data-tempo-ui="recently-metrics-scroll"]');
            if (sc) sc.scrollTop = sc.scrollHeight;
        })()
        """)
        time.sleep(0.5)
        capture_screenshot(ws, box_en, os.path.join(ARTIFACT_DIR, "recently_card_standardized_vi_scrolled.png"))

        # Switch back to VI and open Self-check workspace
        evaluate_js(ws, """
        (() => {
            if (window.TempoAuth) {
                window.TempoAuth.getCurrentUser = () => ({ id: 'local_user', email: 'test@tempo.com' });
                window.TempoAuth.getAuthState = () => 'authenticated';
            }
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('vi');
            }
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('stress-check');
            }
        })()
        """)
        time.sleep(1.5)

        stress_check_rows = evaluate_js(ws, """
        (() => {
            const cards = Array.from(document.querySelectorAll('[data-tracker-id]'));
            return cards.map(c => {
                const name = c.querySelector('h3')?.textContent?.trim();
                const summaryRow = c.querySelector('.pt-2 .flex');
                const label = summaryRow?.querySelector('span:first-child')?.textContent?.trim();
                const val = summaryRow?.querySelector('span:last-child')?.textContent?.trim();
                return { name, label, val };
            }).filter(x => x.name && x.label);
        })()
        """)
        print("\n=== Self-Check Workspace Trackers List (VI) ===")
        print("Raw stress_check_rows:", stress_check_rows)
        for r in (stress_check_rows or []):
            print(f"- {r['name']} | Label: {r['label']} | Value: {r['val']}")

        # Verify Stress-Check Workspace labels
        assert any(('Tension' in r['name'] or 'Căng thẳng' in r['name']) and r['label'] == 'Mức trung bình' for r in (stress_check_rows or [])), "Stress-check Tension failed"
        assert any(r['name'] == 'Overwhelmed' and r['label'] == 'Điểm trung bình' for r in (stress_check_rows or [])), "Stress-check Overwhelmed failed"
        assert any(r['name'] == 'Đi bộ' and r['label'] == 'Tổng lượng ghi nhận' for r in (stress_check_rows or [])), "Stress-check Đi bộ failed"
        assert any(r['name'] == 'Giấc ngủ' and r['label'] == 'Tỷ lệ lựa chọn' for r in (stress_check_rows or [])), "Stress-check Giấc ngủ failed"
        assert any(r['name'] == 'Went outside' and r['label'] == 'Tỷ lệ phản hồi' for r in (stress_check_rows or [])), "Stress-check Went outside failed"
        assert any(r['name'] == 'Đọc sách' and r['label'] == 'Tổng lượng ghi nhận' for r in (stress_check_rows or [])), "Stress-check Đọc sách failed"

        print("\nALL RECOVERY & SELF-CHECK VERIFICATIONS PASSED SUCCESSFULLY!")

    finally:
        try:
            ws.close()
        except:
            pass
        proc.terminate()

if __name__ == "__main__":
    run_tests()
