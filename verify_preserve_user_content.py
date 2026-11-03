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
PORT = 9226
USER_DATA = r"C:\Users\YEN NHI\AppData\Local\Temp\edge_test_preserve_ugc"
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

        print("\n--- 1. Setting up Test Environment & User Trackers ---")
        setup_res = evaluate_js(ws, """
        (async () => {
            sessionStorage.setItem('tempo_rmode_session_welcomed_local_user', 'true');
            if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.closeSetupModal === 'function') {
                window.TempoRecoverySetup.closeSetupModal();
            }

            const uid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function')
                ? (window.TempoAuth.getCurrentUserId() || 'local_user')
                : 'local_user';

            // Set up test trackers with custom names in both Vietnamese and English
            // 1. "Giấc ngủ" (created in Vietnamese, options ['Ngon', 'Dở'])
            // 2. "Sleep" (created in English, options ['Restful', 'Restless'])
            // 3. "Căng thẳng" (created in Vietnamese, percentage)
            // 4. "Tension" (created in English, percentage)
            // 5. "Đi bộ" (created in Vietnamese, quantity)
            // 6. "Thiền định" (custom type_label: "Sức khỏe tinh thần", options ['Tốt', 'Chưa tốt'])
            
            const todayStr = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTodayDateStr === 'function')
                ? window.TempoRecoverySelfCheck.getTodayDateStr()
                : new Date().toISOString().split('T')[0];

            const testTrackers = [
                {
                    id: 'trk_giac_ngu',
                    user_id: uid,
                    name: 'Giấc ngủ',
                    category: 'supportive',
                    type_id: 'supportive',
                    type_label: 'Yếu tố hỗ trợ',
                    type_color: '#5A9E75',
                    check_method: 'options',
                    options: ['Ngon', 'Dở'],
                    is_archived: false
                },
                {
                    id: 'trk_sleep_en',
                    user_id: uid,
                    name: 'Sleep',
                    category: 'supportive',
                    type_id: 'supportive',
                    type_label: 'Supportive habit',
                    type_color: '#5A9E75',
                    check_method: 'options',
                    options: ['Restful', 'Restless'],
                    is_archived: false
                },
                {
                    id: 'trk_cang_thang',
                    user_id: uid,
                    name: 'Căng thẳng',
                    category: 'stress_sign',
                    type_id: 'stress_sign',
                    type_label: 'Dấu hiệu căng thẳng',
                    type_color: '#D48366',
                    check_method: 'percentage',
                    is_archived: false
                },
                {
                    id: 'trk_tension_en',
                    user_id: uid,
                    name: 'Tension',
                    category: 'stress_sign',
                    type_id: 'stress_sign',
                    type_label: 'Sign of stress',
                    type_color: '#D48366',
                    check_method: 'percentage',
                    is_archived: false
                },
                {
                    id: 'trk_di_bo',
                    user_id: uid,
                    name: 'Đi bộ',
                    category: 'supportive',
                    type_id: 'supportive',
                    type_label: 'Thói quen hỗ trợ',
                    type_color: '#166545',
                    check_method: 'quantity',
                    quantity_unit: 'bước',
                    is_archived: false
                },
                {
                    id: 'trk_custom_mental',
                    user_id: uid,
                    name: 'Thiền định',
                    category: 'supportive',
                    type_id: 'type_mental_health',
                    type_label: 'Sức khỏe tinh thần',
                    type_color: '#859B8B',
                    check_method: 'options',
                    options: ['Tốt', 'Chưa tốt'],
                    is_archived: false
                }
            ];

            const testObservations = [
                {
                    id: 'obs_1',
                    user_id: uid,
                    tracker_id: 'trk_giac_ngu',
                    date: todayStr,
                    check_method: 'options',
                    value: 'Ngon',
                    status: 'answered'
                },
                {
                    id: 'obs_2',
                    user_id: uid,
                    tracker_id: 'trk_sleep_en',
                    date: todayStr,
                    check_method: 'options',
                    value: 'Restful',
                    status: 'answered'
                },
                {
                    id: 'obs_3',
                    user_id: uid,
                    tracker_id: 'trk_cang_thang',
                    date: todayStr,
                    check_method: 'percentage',
                    value: 40,
                    status: 'answered'
                },
                {
                    id: 'obs_4',
                    user_id: uid,
                    tracker_id: 'trk_tension_en',
                    date: todayStr,
                    check_method: 'percentage',
                    value: 55,
                    status: 'answered'
                },
                {
                    id: 'obs_5',
                    user_id: uid,
                    tracker_id: 'trk_di_bo',
                    date: todayStr,
                    check_method: 'quantity',
                    value: 3000,
                    status: 'answered'
                },
                {
                    id: 'obs_6',
                    user_id: uid,
                    tracker_id: 'trk_custom_mental',
                    date: todayStr,
                    check_method: 'options',
                    value: 'Tốt',
                    status: 'answered'
                }
            ];

            // Save Recovery Note reflection items
            const noteData = {
                user_id: uid,
                items: [
                    { id: 'item_1', type: 'warning_sign', text: 'Cảm thấy khó tập trung khi làm việc dài' },
                    { id: 'item_2', type: 'reminder', text: 'Hít thở sâu 3 lần trước khi bắt đầu nhiệm vụ mới' },
                    { id: 'item_3', type: 'support_person', text: 'Bác sĩ Nam', metadata: { relationship: 'Tư vấn tâm lý' } }
                ]
            };

            localStorage.setItem(`tempo_selfcheck_trackers_${uid}`, JSON.stringify(testTrackers));
            localStorage.setItem('tempo_selfcheck_trackers', JSON.stringify(testTrackers));
            localStorage.setItem(`tempo_selfcheck_observations_${uid}`, JSON.stringify(testObservations));
            localStorage.setItem('tempo_selfcheck_observations', JSON.stringify(testObservations));
            localStorage.setItem(`tempo_recovery_note_${uid}`, JSON.stringify(noteData));
            localStorage.setItem('tempo_recovery_note', JSON.stringify(noteData));

            return { ok: true, trackerCount: testTrackers.length };
        })()
        """)
        print("Setup result:", setup_res)

        print("\n--- 2. Testing English Interface Mode (lang = 'en') ---")
        evaluate_js(ws, """
        (async () => {
            localStorage.setItem('tempo_current_mode', 'recovery');
            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
                window.TempoMode.setMode('recovery');
            }
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('en');
            } else {
                localStorage.setItem('tempo_lang', 'en');
                localStorage.setItem('tempo_language', 'en');
            }
            if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
                window.TempoMode.renderRmodeHome();
            }
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.render === 'function') {
                window.TempoSelfCheckWorkspace.render();
            }
        })()
        """)
        time.sleep(1)

        # Verify Recently Card in English mode
        recently_en = evaluate_js(ws, """
        (() => {
            const card = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!card) return { found: false };
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
            return { found: true, items };
        })()
        """)
        print("Recently Card items in English mode:")
        for item in recently_en.get("items", []):
            print(f"  Name: '{item['name']}', Desc: '{item['desc']}', Val: '{item['val']}'")

        # In English mode:
        # - "Giấc ngủ" must remain "Giấc ngủ"
        # - "Sleep" must remain "Sleep"
        # - "Căng thẳng" must remain "Căng thẳng"
        # - "Tension" must remain "Tension"
        # - "Đi bộ" must remain "Đi bộ"
        # - "Thiền định" must remain "Thiền định"
        # - Option distribution for "Giấc ngủ" must use ['Ngon', 'Dở']
        names_in_en = [it['name'] for it in recently_en.get("items", [])]
        assert "Giấc ngủ" in names_in_en, f"Expected 'Giấc ngủ' to remain in EN, found: {names_in_en}"
        assert "Sleep" in names_in_en, f"Expected 'Sleep' to remain in EN, found: {names_in_en}"
        assert "Căng thẳng" in names_in_en, f"Expected 'Căng thẳng' to remain in EN, found: {names_in_en}"
        assert "Tension" in names_in_en, f"Expected 'Tension' to remain in EN, found: {names_in_en}"
        assert "Đi bộ" in names_in_en, f"Expected 'Đi bộ' to remain in EN, found: {names_in_en}"
        assert "Thiền định" in names_in_en, f"Expected 'Thiền định' to remain in EN, found: {names_in_en}"
        print("✓ All tracker names correctly preserved in Recently Card under English mode!")

        # Verify Self-check Workspace (Full screen) in English mode
        evaluate_js(ws, """
        (() => {
            if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                window.TempoMode.openStrack('open');
            } else if (window.TempoMode && typeof window.TempoMode.showScreen === 'function') {
                window.TempoMode.showScreen('stress-check');
            }
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.render === 'function') {
                window.TempoSelfCheckWorkspace.render();
            }
        })()
        """)
        time.sleep(1)

        workspace_en = evaluate_js(ws, """
        (() => {
            const root = document.getElementById('self-check-workspace-root');
            if (!root) return { found: false };
            const trackerRows = Array.from(root.querySelectorAll('[data-tracker-id]')).map(row => {
                const titleEl = row.querySelector('h3');
                return titleEl ? titleEl.textContent.trim() : '';
            }).filter(Boolean);
            return { found: true, trackerRows };
        })()
        """)
        print("Self-check Workspace trackers in English mode:", workspace_en.get("trackerRows"))
        ws_names_en = workspace_en.get("trackerRows", [])
        assert "Giấc ngủ" in ws_names_en, f"Expected 'Giấc ngủ' in workspace, found: {ws_names_en}"
        assert "Sleep" in ws_names_en, f"Expected 'Sleep' in workspace, found: {ws_names_en}"
        assert "Căng thẳng" in ws_names_en, f"Expected 'Căng thẳng' in workspace, found: {ws_names_en}"
        assert "Tension" in ws_names_en, f"Expected 'Tension' in workspace, found: {ws_names_en}"
        assert "Đi bộ" in ws_names_en, f"Expected 'Đi bộ' in workspace, found: {ws_names_en}"
        print("✓ All tracker names correctly preserved in Self-check Workspace under English mode!")

        # Verify Full-check Calendar Modal in English mode for "Giấc ngủ"
        fc_modal_en = evaluate_js(ws, """
        (() => {
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.openFullCheckPlaceholder === 'function') {
                window.TempoSelfCheckWorkspace.openFullCheckPlaceholder('trk_giac_ngu');
            }
            const modal = document.getElementById('modal-selfcheck-fullcheck');
            if (!modal || modal.classList.contains('hidden')) return { open: false };
            const titleEl = modal.querySelector('h2');
            return {
                open: true,
                title: titleEl ? titleEl.textContent.trim() : ''
            };
        })()
        """)
        print("Full-check Modal for 'trk_giac_ngu' in English mode:", fc_modal_en)
        assert fc_modal_en.get("title") == "Giấc ngủ", f"Expected title 'Giấc ngủ', got: {fc_modal_en.get('title')}"
        print("✓ Full-check Modal preserved Vietnamese name 'Giấc ngủ' in English interface!")

        # Close Full-check modal
        evaluate_js(ws, """
        (() => {
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.closeFullCheckPlaceholder === 'function') {
                window.TempoSelfCheckWorkspace.closeFullCheckPlaceholder();
            }
        })()
        """)

        # Verify Monthly Overview Modal in English mode for "Giấc ngủ"
        mo_modal_en = evaluate_js(ws, """
        (() => {
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.openMonthlyOverview === 'function') {
                window.TempoSelfCheckWorkspace.openMonthlyOverview('trk_giac_ngu');
            }
            const modal = document.getElementById('modal-selfcheck-monthly-overview');
            if (!modal || modal.classList.contains('hidden')) return { open: false };
            const titleEl = modal.querySelector('h2');
            return {
                open: true,
                title: titleEl ? titleEl.textContent.trim() : ''
            };
        })()
        """)
        print("Monthly Overview Modal for 'trk_giac_ngu' in English mode:", mo_modal_en)
        assert mo_modal_en.get("title") == "Giấc ngủ", f"Expected title 'Giấc ngủ', got: {mo_modal_en.get('title')}"
        print("✓ Monthly Overview Modal preserved Vietnamese name 'Giấc ngủ' in English interface!")

        # Close overview modal and return to workspace
        evaluate_js(ws, """
        (() => {
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.closeMonthlyOverview === 'function') {
                window.TempoSelfCheckWorkspace.closeMonthlyOverview(true);
            }
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.closeFullCheckPlaceholder === 'function') {
                window.TempoSelfCheckWorkspace.closeFullCheckPlaceholder();
            }
        })()
        """)

        # Verify Step 2 & Step 3 Review of Recovery Setup in English mode
        setup_step2_en = evaluate_js(ws, """
        (() => {
            if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.open === 'function') {
                window.TempoRecoverySetup.open();
                window.TempoRecoverySetup.startAdjustmentFlow();
            }
            const modal = document.getElementById('modal-recovery-setup');
            if (!modal || modal.classList.contains('hidden')) return { open: false, debug: 'hidden or missing' };
            const items = Array.from(modal.querySelectorAll('.rounded-2xl.border')).map(el => {
                const nameEl = el.querySelector('h4');
                const catDescEl = Array.from(el.querySelectorAll('span')).find(s => (s.className || '').includes('text-[11px]'));
                return {
                    name: nameEl ? nameEl.textContent.trim() : '',
                    desc: catDescEl ? catDescEl.textContent.trim() : ''
                };
            }).filter(i => i.name);
            return { open: true, items };
        })()
        """)
        print("Recovery Setup Step 2 items in English mode:", setup_step2_en)
        print("Recovery Setup Step 2 items in English mode:")
        for it in setup_step2_en.get("items", []):
            print(f"  Name: '{it['name']}', Desc: '{it['desc']}'")
        
        # Check custom options & type_label in Step 2:
        # "Giấc ngủ" has options ['Ngon', 'Dở'] -> desc should have "Options (Ngon, Dở)"
        # "Thiền định" has type_label "Sức khỏe tinh thần" -> desc should contain "Sức khỏe tinh thần"
        giac_ngu_step2 = next((i for i in setup_step2_en.get("items", []) if "Giấc ngủ" in i['name']), None)
        assert giac_ngu_step2, "Expected 'Giấc ngủ' item in Step 2 setup"
        assert "Ngon, Dở" in giac_ngu_step2['desc'], f"Expected custom options 'Ngon, Dở' in desc, got: {giac_ngu_step2['desc']}"
        
        thien_dinh_step2 = next((i for i in setup_step2_en.get("items", []) if "Thiền định" in i['name']), None)
        assert thien_dinh_step2, "Expected 'Thiền định' item in Step 2 setup"
        assert "Sức khỏe tinh thần" in thien_dinh_step2['desc'], f"Expected custom type 'Sức khỏe tinh thần' in desc, got: {thien_dinh_step2['desc']}"
        print("✓ Recovery Setup Step 2 preserved custom options ('Ngon, Dở') and custom type ('Sức khỏe tinh thần') in English interface!")

        # Close setup modal
        evaluate_js(ws, """
        (() => {
            if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.close === 'function') {
                window.TempoRecoverySetup.close();
            }
        })()
        """)

        # Capture screenshot of workspace in English mode with Vietnamese UGC
        evaluate_js(ws, """
        (() => {
            if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                window.TempoMode.openStrack('open');
            } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('stress-check');
            }
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.render === 'function') {
                window.TempoSelfCheckWorkspace.render();
            }
        })()
        """)
        time.sleep(0.5)
        clip_en = evaluate_js(ws, """
        (() => {
            const el = document.getElementById('screen-stress-check') || document.getElementById('self-check-workspace-root');
            if (!el) return null;
            const r = el.getBoundingClientRect();
            if (r.width <= 0 || r.height <= 0) return null;
            return { x: r.x, y: r.y, width: r.width, height: Math.min(r.height, 900), scale: 1 };
        })()
        """)
        print("clip_en:", clip_en)
        if clip_en:
            capture_screenshot(ws, clip_en, os.path.join(ARTIFACT_DIR, "ugc_preserved_en_ui.png"))

        print("\n--- 3. Testing Vietnamese Interface Mode (lang = 'vi') ---")
        evaluate_js(ws, """
        (async () => {
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('vi');
            } else {
                localStorage.setItem('tempo_lang', 'vi');
                localStorage.setItem('tempo_language', 'vi');
            }
            if (window.TempoMode && typeof window.TempoMode.init === 'function') {
                window.TempoMode.init();
            }
            if (window.TempoMode && typeof window.TempoMode.showScreen === 'function') {
                window.TempoMode.showScreen('recovery');
            }
        })()
        """)
        time.sleep(1)

        # Verify Recently Card in Vietnamese mode
        recently_vi = evaluate_js(ws, """
        (() => {
            const card = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!card) return { found: false };
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
            return { found: true, items };
        })()
        """)
        print("Recently Card items in Vietnamese mode:")
        for item in recently_vi.get("items", []):
            print(f"  Name: '{item['name']}', Desc: '{item['desc']}', Val: '{item['val']}'")

        # In Vietnamese mode:
        # - "Sleep" must remain "Sleep" (NOT translated to "Giấc ngủ")
        # - "Tension" must remain "Tension" (NOT translated to "Căng thẳng")
        # - "Giấc ngủ" must remain "Giấc ngủ"
        # - "Căng thẳng" must remain "Căng thẳng"
        # - "Đi bộ" must remain "Đi bộ"
        # - "Thiền định" must remain "Thiền định"
        # - "Restful" and "Ngon" options must remain
        names_in_vi = [it['name'] for it in recently_vi.get("items", [])]
        assert "Sleep" in names_in_vi, f"Expected 'Sleep' to remain in VI, found: {names_in_vi}"
        assert "Tension" in names_in_vi, f"Expected 'Tension' to remain in VI, found: {names_in_vi}"
        assert "Giấc ngủ" in names_in_vi, f"Expected 'Giấc ngủ' to remain in VI, found: {names_in_vi}"
        assert "Căng thẳng" in names_in_vi, f"Expected 'Căng thẳng' to remain in VI, found: {names_in_vi}"
        assert "Đi bộ" in names_in_vi, f"Expected 'Đi bộ' to remain in VI, found: {names_in_vi}"
        assert "Thiền định" in names_in_vi, f"Expected 'Thiền định' to remain in VI, found: {names_in_vi}"
        print("✓ All tracker names (English and Vietnamese) correctly preserved in Recently Card under Vietnamese mode!")

        # Verify Daily Check-in card in Vietnamese mode
        daily_vi = evaluate_js(ws, """
        (() => {
            const card = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            if (!card) return { found: false };
            const trackerNameEl = card.querySelector('.space-y-2 .truncate') || card.querySelector('.truncate');
            return {
                found: true,
                currentTrackerName: trackerNameEl ? trackerNameEl.textContent.trim() : ''
            };
        })()
        """)
        print("Daily checkin current tracker name in Vietnamese mode:", daily_vi)
        assert daily_vi.get("currentTrackerName") in ["Giấc ngủ", "Sleep", "Căng thẳng", "Tension", "Đi bộ", "Thiền định"], \
            f"Unexpected tracker name in daily checkin: {daily_vi.get('currentTrackerName')}"
        print("✓ Daily checkin preserves user tracker name verbatim!")

        # Verify Self-check Workspace (Full screen) in Vietnamese mode
        evaluate_js(ws, """
        (() => {
            if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                window.TempoMode.openStrack('open');
            } else if (window.TempoMode && typeof window.TempoMode.showScreen === 'function') {
                window.TempoMode.showScreen('stress-check');
            }
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.render === 'function') {
                window.TempoSelfCheckWorkspace.render();
            }
        })()
        """)
        time.sleep(1)

        workspace_vi = evaluate_js(ws, """
        (() => {
            const root = document.getElementById('self-check-workspace-root');
            if (!root) return { found: false };
            const trackerRows = Array.from(root.querySelectorAll('[data-tracker-id]')).map(row => {
                const titleEl = row.querySelector('h3');
                return titleEl ? titleEl.textContent.trim() : '';
            }).filter(Boolean);
            return { found: true, trackerRows };
        })()
        """)
        print("Self-check Workspace trackers in Vietnamese mode:", workspace_vi.get("trackerRows"))
        ws_names_vi = workspace_vi.get("trackerRows", [])
        assert "Sleep" in ws_names_vi, f"Expected 'Sleep' to remain in workspace in VI mode, found: {ws_names_vi}"
        assert "Tension" in ws_names_vi, f"Expected 'Tension' to remain in workspace in VI mode, found: {ws_names_vi}"
        assert "Giấc ngủ" in ws_names_vi, f"Expected 'Giấc ngủ' to remain in workspace in VI mode, found: {ws_names_vi}"
        assert "Căng thẳng" in ws_names_vi, f"Expected 'Căng thẳng' to remain in workspace in VI mode, found: {ws_names_vi}"
        assert "Đi bộ" in ws_names_vi, f"Expected 'Đi bộ' to remain in workspace in VI mode, found: {ws_names_vi}"
        print("✓ All tracker names correctly preserved in Self-check Workspace under Vietnamese mode!")

        # Verify Full-check Calendar Modal in Vietnamese mode for English tracker "Sleep"
        fc_modal_vi = evaluate_js(ws, """
        (() => {
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.openFullCheckPlaceholder === 'function') {
                window.TempoSelfCheckWorkspace.openFullCheckPlaceholder('trk_sleep_en');
            }
            const modal = document.getElementById('modal-selfcheck-fullcheck');
            if (!modal || modal.classList.contains('hidden')) return { open: false };
            const titleEl = modal.querySelector('h2');
            return {
                open: true,
                title: titleEl ? titleEl.textContent.trim() : ''
            };
        })()
        """)
        print("Full-check Modal for 'trk_sleep_en' in Vietnamese mode:", fc_modal_vi)
        assert fc_modal_vi.get("title") == "Sleep", f"Expected title 'Sleep', got: {fc_modal_vi.get('title')}"
        print("✓ Full-check Modal preserved English name 'Sleep' in Vietnamese interface!")

        # Close Full-check modal
        evaluate_js(ws, """
        (() => {
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.closeFullCheckPlaceholder === 'function') {
                window.TempoSelfCheckWorkspace.closeFullCheckPlaceholder();
            }
        })()
        """)

        # Verify Step 2 & Step 3 Review of Recovery Setup in Vietnamese mode
        setup_step2_vi = evaluate_js(ws, """
        (() => {
            if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.open === 'function') {
                window.TempoRecoverySetup.open();
                window.TempoRecoverySetup.startAdjustmentFlow();
            }
            const modal = document.getElementById('modal-recovery-setup');
            if (!modal || modal.classList.contains('hidden')) return { open: false };
            const items = Array.from(modal.querySelectorAll('.rounded-2xl.border')).map(el => {
                const nameEl = el.querySelector('h4');
                const catDescEl = Array.from(el.querySelectorAll('span')).find(s => (s.className || '').includes('text-[11px]'));
                return {
                    name: nameEl ? nameEl.textContent.trim() : '',
                    desc: catDescEl ? catDescEl.textContent.trim() : ''
                };
            }).filter(i => i.name);
            return { open: true, items };
        })()
        """)
        print("Recovery Setup Step 2 items in Vietnamese mode:")
        for it in setup_step2_vi.get("items", []):
            print(f"  Name: '{it['name']}', Desc: '{it['desc']}'")

        # Check that English tracker "Sleep" has options "Restful, Restless" in Vietnamese mode:
        sleep_step2 = next((i for i in setup_step2_vi.get("items", []) if "Sleep" in i['name']), None)
        assert sleep_step2, "Expected 'Sleep' item in Step 2 setup"
        assert "Restful, Restless" in sleep_step2['desc'], f"Expected custom options 'Restful, Restless' in desc, got: {sleep_step2['desc']}"
        print("✓ Recovery Setup Step 2 preserved custom options ('Restful, Restless') in Vietnamese interface!")

        # Close setup modal
        evaluate_js(ws, """
        (() => {
            if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.close === 'function') {
                window.TempoRecoverySetup.close();
            }
        })()
        """)

        # Verify Recovery Notice Modal in Vietnamese mode and English mode
        notice_res = evaluate_js(ws, """
        (() => {
            if (window.TempoRecoveryNote && typeof window.TempoRecoveryNote.openViewModal === 'function') {
                window.TempoRecoveryNote.openViewModal();
            }
            const modal = document.getElementById('modal-recovery-note-view');
            if (!modal || modal.classList.contains('hidden')) return { open: false };
            const container = document.getElementById('recovery-note-view-content');
            const items = container ? Array.from(container.querySelectorAll('li')).map(li => li.textContent.trim()) : [];
            return { open: true, items };
        })()
        """)
        print("Recovery Notice Modal items in Vietnamese mode:", notice_res.get("items"))
        notice_items = notice_res.get("items", [])
        assert any("Cảm thấy khó tập trung" in it for it in notice_items), "Expected user warning sign text"
        assert any("Hít thở sâu 3 lần" in it for it in notice_items), "Expected user reminder text"
        assert any("Bác sĩ Nam" in it for it in notice_items), "Expected user support person text"
        assert any("Tư vấn tâm lý" in it for it in notice_items), "Expected user relationship text"
        print("✓ Recovery Notice items preserved user-created text and notes verbatim!")

        # Close notice modal
        evaluate_js(ws, """
        (() => {
            if (window.TempoRecoveryNote && typeof window.TempoRecoveryNote.closeViewModal === 'function') {
                window.TempoRecoveryNote.closeViewModal();
            }
        })()
        """)

        # Check storage persistence: ensure stored trackers in localStorage have NOT been translated
        storage_check = evaluate_js(ws, """
        (() => {
            const uid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function')
                ? (window.TempoAuth.getCurrentUserId() || 'local_user')
                : 'local_user';
            const raw = localStorage.getItem(`tempo_selfcheck_trackers_${uid}`) || localStorage.getItem('tempo_selfcheck_trackers');
            if (!raw) return { ok: false, error: 'No stored trackers' };
            const list = JSON.parse(raw);
            return {
                ok: true,
                names: list.map(t => t.name)
            };
        })()
        """)
        print("Stored tracker names in localStorage:", storage_check.get("names"))
        stored_names = storage_check.get("names", [])
        assert "Giấc ngủ" in stored_names, "Stored tracker 'Giấc ngủ' was modified or lost!"
        assert "Sleep" in stored_names, "Stored tracker 'Sleep' was modified or lost!"
        assert "Căng thẳng" in stored_names, "Stored tracker 'Căng thẳng' was modified or lost!"
        assert "Tension" in stored_names, "Stored tracker 'Tension' was modified or lost!"
        assert "Đi bộ" in stored_names, "Stored tracker 'Đi bộ' was modified or lost!"
        assert "Thiền định" in stored_names, "Stored tracker 'Thiền định' was modified or lost!"
        print("✓ Storage integrity verified: zero translation or modification of user-created stored records!")

        # Capture screenshot of workspace in Vietnamese mode with English UGC
        evaluate_js(ws, """
        (() => {
            if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                window.TempoMode.openStrack('open');
            } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('stress-check');
            }
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.render === 'function') {
                window.TempoSelfCheckWorkspace.render();
            }
        })()
        """)
        time.sleep(0.5)
        clip_vi = evaluate_js(ws, """
        (() => {
            const el = document.getElementById('screen-stress-check') || document.getElementById('self-check-workspace-root');
            if (!el) return null;
            const r = el.getBoundingClientRect();
            if (r.width <= 0 || r.height <= 0) return null;
            return { x: r.x, y: r.y, width: r.width, height: Math.min(r.height, 900), scale: 1 };
        })()
        """)
        print("clip_vi:", clip_vi)
        if clip_vi:
            capture_screenshot(ws, clip_vi, os.path.join(ARTIFACT_DIR, "ugc_preserved_vi_ui.png"))

        # Also capture Recently card closeup in both modes
        evaluate_js(ws, """
        (() => {
            if (window.TempoMode && typeof window.TempoMode.showScreen === 'function') {
                window.TempoMode.showScreen('recovery');
            }
            if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
                window.TempoMode.renderRmodeHome();
            }
        })()
        """)
        time.sleep(0.5)
        clip_recently = evaluate_js(ws, """
        (() => {
            const el = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!el) return null;
            const r = el.getBoundingClientRect();
            if (r.width <= 0 || r.height <= 0) return null;
            return { x: r.x, y: r.y, width: r.width, height: r.height, scale: 1 };
        })()
        """)
        print("clip_recently (VI):", clip_recently)
        if clip_recently:
            capture_screenshot(ws, clip_recently, os.path.join(ARTIFACT_DIR, "recently_card_ugc_vi.png"))

        evaluate_js(ws, """
        (() => {
            if (window.TempoI18n && typeof window.TempoI18n.setLanguage === 'function') {
                window.TempoI18n.setLanguage('en');
            }
            if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
                window.TempoMode.renderRmodeHome();
            }
        })()
        """)
        time.sleep(0.5)
        clip_recently_en = evaluate_js(ws, """
        (() => {
            const el = document.querySelector('[data-tempo-ui="recovery-recently"]');
            if (!el) return null;
            const r = el.getBoundingClientRect();
            if (r.width <= 0 || r.height <= 0) return null;
            return { x: r.x, y: r.y, width: r.width, height: r.height, scale: 1 };
        })()
        """)
        print("clip_recently (EN):", clip_recently_en)
        if clip_recently_en:
            capture_screenshot(ws, clip_recently_en, os.path.join(ARTIFACT_DIR, "recently_card_ugc_en.png"))

        print("\n=======================================================")
        print("ALL UGC PRESERVATION VERIFICATION CHECKS PASSED!")
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
