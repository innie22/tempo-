#!/usr/bin/env python3
"""
Comprehensive automated CDP test suite for Appearance - Global Background Customization.
Tests:
1. Settings -> Appearance UI with all 11 presets and default #EAEEE8
2. Swatch selection, preview isolation, Apply button, and Reset to default
3. Global background application across URmode, Rmode, Working Plan, Self-check, Urgent Mode, About, Community, Notes
4. Persistence and user account isolation
5. Bilingual localization (EN <-> VI)
6. Screenshot captures
"""

import sys
import os
import json
import time
import subprocess
import urllib.request
import base64
import websocket

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

CDP_PORT = 9489
TARGET_URL = "http://127.0.0.1:8000/#today"
ARTIFACT_DIR = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"

def start_browser():
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    edge_binary = next((p for p in edge_paths if os.path.exists(p)), None)
    if not edge_binary:
        raise RuntimeError("Edge binary not found")

    user_data_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), f"cdp_appearance_{int(time.time())}")
    cmd = [
        edge_binary,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--headless=new",
        "--disable-gpu",
        "--window-size=1280,1200",
        TARGET_URL
    ]
    print(f"Starting Edge on port {CDP_PORT}")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.5)
    return proc

def get_ws_url():
    for _ in range(15):
        try:
            req = urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json")
            tabs = json.loads(req.read().decode())
            for t in tabs:
                if t.get("type") == "page":
                    return t["webSocketDebuggerUrl"]
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Failed to connect to CDP debugger")

def send_cdp_command(ws_url, method, params=None):
    ws = websocket.create_connection(ws_url, timeout=15)
    req_data = {
        "id": int(time.time() * 1000) % 1000000,
        "method": method,
        "params": params or {}
    }
    ws.send(json.dumps(req_data))
    while True:
        res = ws.recv()
        data = json.loads(res)
        if data.get("id") == req_data["id"]:
            ws.close()
            return data.get("result", {})

def eval_js(ws_url, expr):
    res = send_cdp_command(ws_url, "Runtime.evaluate", {
        "expression": expr,
        "returnByValue": True,
        "awaitPromise": True
    })
    if "exceptionDetails" in res:
        raise RuntimeError(f"CDP Evaluation error: {res['exceptionDetails']}")
    return res.get("result", {}).get("value")

def capture_screenshot(ws_url, path, clip=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    params = {"format": "png"}
    if clip:
        params["clip"] = clip
    res = send_cdp_command(ws_url, "Page.captureScreenshot", params)
    img_bytes = base64.b64decode(res["data"])
    with open(path, "wb") as f:
        f.write(img_bytes)
    print(f"Captured screenshot: {os.path.basename(path)}")

def run_tests():
    proc = start_browser()
    ws_url = get_ws_url()

    try:
        print("\n=== STARTING APPEARANCE CUSTOMIZATION CDP TEST SUITE ===")
        # Wait for app components to be loaded
        loaded = False
        for _ in range(20):
            try:
                res = eval_js(ws_url, "typeof window.TempoI18n !== 'undefined' && typeof window.TempoApp !== 'undefined' && typeof window.TempoTheme !== 'undefined'")
                if res:
                    loaded = True
                    break
            except Exception:
                pass
            time.sleep(0.5)
        assert loaded, "App scripts failed to load in time"
        print("App components loaded successfully.")

        # Navigate to Settings tab
        eval_js(ws_url, """
        (function() {
            window.TempoI18n.setLanguage('vi');
            window.TempoApp.navigateTo('personal-space', 'settings');
            window.TempoPersonalSpace.selectTab('settings');
        })()
        """)
        time.sleep(0.5)

        # -------------------------------------------------------------
        # TEST 1: VERIFY 11 COLOR PRESETS & DEFAULT #EAEEE8
        # -------------------------------------------------------------
        print("\n--- TEST 1: VERIFY APPEARANCE SETTINGS UI & 11 PRESETS ---")
        t1_data = eval_js(ws_url, """
        (function() {
            const groupHeading = document.getElementById('appearance-group-heading')?.innerText?.trim();
            const title = document.getElementById('appearance-title')?.innerText?.trim();
            const desc = document.getElementById('appearance-description')?.innerText?.trim();
            const activeName = document.getElementById('appearance-active-name')?.innerText?.trim();
            const previewLabel = document.getElementById('appearance-preview-label')?.innerText?.trim();
            const btnReset = document.getElementById('btn-appearance-reset')?.innerText?.trim();
            const btnApply = document.getElementById('btn-appearance-apply')?.innerText?.trim();
            
            const swatches = Array.from(document.querySelectorAll('.appearance-swatch-btn')).map(b => ({
                hex: b.getAttribute('data-bg-hex'),
                id: b.getAttribute('data-bg-id'),
                name: b.querySelector('.truncate')?.innerText?.trim(),
                isDefault: b.innerText.includes('Mặc định') || b.innerText.includes('Default'),
                hasSelectedBadge: !b.querySelector('.appearance-swatch-badge')?.classList.contains('hidden')
            }));

            const presetsFromApi = window.TempoTheme.getPresets();
            const currentColor = window.TempoTheme.getCurrentColor();

            return {
                groupHeading,
                title,
                desc,
                activeName,
                previewLabel,
                btnReset,
                btnApply,
                swatchesCount: swatches.length,
                swatches,
                presetsCount: presetsFromApi.length,
                currentColor
            };
        })()
        """)

        print(f"Group Heading: {t1_data['groupHeading']}")
        print(f"Title: {t1_data['title']}")
        print(f"Description: {t1_data['desc']}")
        print(f"Active Name: {t1_data['activeName']}")
        print(f"Swatches Count: {t1_data['swatchesCount']}")
        print(f"Current Color: {t1_data['currentColor']}")

        assert t1_data['groupHeading'] == "GIAO DIỆN", f"Expected GIAO DIỆN, got {t1_data['groupHeading']}"
        assert t1_data['title'] == "Màu nền", f"Expected Màu nền, got {t1_data['title']}"
        assert "Lựa chọn màu nền phù hợp" in t1_data['desc'], f"Desc mismatch: {t1_data['desc']}"
        assert t1_data['swatchesCount'] == 11, f"Expected 11 swatches, got {t1_data['swatchesCount']}"
        assert t1_data['presetsCount'] == 11, f"Expected 11 presets from API, got {t1_data['presetsCount']}"
        assert t1_data['currentColor'] == "#EAEEE8", f"Default color must be #EAEEE8, got {t1_data['currentColor']}"

        # Verify all 11 colors present
        expected_presets = [
            ("Sage Green", "#8EA695"),
            ("Dusty Blue", "#94B0BD"),
            ("Warm Blush", "#ECC9BA"),
            ("Soft Sage", "#D5E1D8"),
            ("Soft Blue", "#D1DEE4"),
            ("Warm Cream", "#F5EDE3"),
            ("Pale Pink", "#FDDBD8"),
            ("Blush Cream", "#FCE8E1"),
            ("Soft Beige", "#FAEDDB"),
            ("Cloud Blue", "#E7EDF0"),
            ("Mist Green", "#EAEEE8")
        ]
        found_hexes = [s['hex'].upper() for s in t1_data['swatches']]
        for name, hexcode in expected_presets:
            assert hexcode.upper() in found_hexes, f"Missing preset {name} ({hexcode})"

        # Default Mist Green check
        mist_swatch = next(s for s in t1_data['swatches'] if s['hex'].upper() == "#EAEEE8")
        assert mist_swatch['isDefault'], "Mist Green must be labeled as Default"
        print("✓ Test 1 Passed: Appearance settings UI & all 11 presets accurately verified!")

        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "appearance_settings_vi.png"))

        # -------------------------------------------------------------
        # TEST 2: SELECTION INTERACTION & PREVIEW ISOLATION
        # -------------------------------------------------------------
        print("\n--- TEST 2: SWATCH SELECTION & PREVIEW ISOLATION ---")
        t2_step1 = eval_js(ws_url, """
        (function() {
            // Select Dusty Blue (#94B0BD)
            const dustyBtn = document.querySelector('.appearance-swatch-btn[data-bg-hex="#94B0BD"]');
            if (dustyBtn) dustyBtn.click();

            // Re-query updated DOM element after re-render
            const updatedDustyBtn = document.querySelector('.appearance-swatch-btn[data-bg-hex="#94B0BD"]');
            const previewBg = window.getComputedStyle(document.getElementById('appearance-preview-box')).backgroundColor;
            const bodyBg = window.getComputedStyle(document.body).backgroundColor;
            const selectedHexInApi = window.TempoTheme.getSelectedColor();
            const currentHexInApi = window.TempoTheme.getCurrentColor();

            const dustyBadgeVisible = !updatedDustyBtn?.querySelector('.appearance-swatch-badge')?.classList.contains('hidden');
            const dustyBadgeText = updatedDustyBtn?.querySelector('.appearance-swatch-badge')?.innerText?.trim();

            return {
                previewBg,
                bodyBg,
                selectedHexInApi,
                currentHexInApi,
                dustyBadgeVisible,
                dustyBadgeText
            };
        })()
        """)

        print(f"Preview Box Background: {t2_step1['previewBg']}")
        print(f"Global Body Background: {t2_step1['bodyBg']}")
        print(f"Selected Hex: {t2_step1['selectedHexInApi']}")
        print(f"Current Global Hex: {t2_step1['currentHexInApi']}")

        # rgb(148, 176, 189) is #94B0BD
        assert "148, 176, 189" in t2_step1['previewBg'], f"Expected preview box rgb(148, 176, 189), got {t2_step1['previewBg']}"
        # Body background must NOT be changed yet! It must still be #EAEEE8 (rgb(234, 238, 232))
        assert "234, 238, 232" in t2_step1['bodyBg'], f"Global body background should NOT change on selection alone! Got: {t2_step1['bodyBg']}"
        assert t2_step1['selectedHexInApi'] == "#94B0BD", f"Selected hex should be #94B0BD, got {t2_step1['selectedHexInApi']}"
        assert t2_step1['currentHexInApi'] == "#EAEEE8", f"Current hex should still be #EAEEE8, got {t2_step1['currentHexInApi']}"
        assert t2_step1['dustyBadgeVisible'], "Selected swatch must have visible badge"
        assert t2_step1['dustyBadgeText'] == "Đang chọn", f"Expected 'Đang chọn', got {t2_step1['dustyBadgeText']}"

        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "appearance_settings_vi_selected_preview.png"))
        print("✓ Verified preview updates without immediately changing global application background!")

        # Now click Apply
        print("\nClicking Apply button...")
        t2_step2 = eval_js(ws_url, """
        (function() {
            document.getElementById('btn-appearance-apply').click();
            const bodyBg = window.getComputedStyle(document.body).backgroundColor;
            const currentHexInApi = window.TempoTheme.getCurrentColor();
            const activeName = document.getElementById('appearance-active-name')?.innerText?.trim();

            return {
                bodyBg,
                currentHexInApi,
                activeName
            };
        })()
        """)
        print(f"Post-Apply Body Background: {t2_step2['bodyBg']}")
        print(f"Post-Apply Current Hex: {t2_step2['currentHexInApi']}")
        print(f"Active Badge Name: {t2_step2['activeName']}")

        assert "148, 176, 189" in t2_step2['bodyBg'], f"Global body background must now be #94B0BD, got: {t2_step2['bodyBg']}"
        assert t2_step2['currentHexInApi'] == "#94B0BD", f"Current hex must be #94B0BD, got: {t2_step2['currentHexInApi']}"
        assert t2_step2['activeName'] == "Dusty Blue", f"Active badge must be Dusty Blue, got: {t2_step2['activeName']}"
        print("✓ Test 2 Passed: Swatch selection, preview isolation, and Apply commit verified!")

        # -------------------------------------------------------------
        # TEST 3: RESET TO DEFAULT BUTTON
        # -------------------------------------------------------------
        print("\n--- TEST 3: RESET TO DEFAULT BUTTON ---")
        t3_data = eval_js(ws_url, """
        (function() {
            document.getElementById('btn-appearance-reset').click();
            const bodyBg = window.getComputedStyle(document.body).backgroundColor;
            const currentHex = window.TempoTheme.getCurrentColor();
            const selectedHex = window.TempoTheme.getSelectedColor();
            const activeName = document.getElementById('appearance-active-name')?.innerText?.trim();
            const mistBtn = document.querySelector('.appearance-swatch-btn[data-bg-hex="#EAEEE8"]');
            const mistBadgeVisible = !mistBtn.querySelector('.appearance-swatch-badge')?.classList.contains('hidden');

            return {
                bodyBg,
                currentHex,
                selectedHex,
                activeName,
                mistBadgeVisible
            };
        })()
        """)

        print(f"Post-Reset Body Background: {t3_data['bodyBg']}")
        print(f"Current Hex: {t3_data['currentHex']}")
        print(f"Active Badge Name: {t3_data['activeName']}")

        assert "234, 238, 232" in t3_data['bodyBg'], f"Body background should reset to #EAEEE8, got {t3_data['bodyBg']}"
        assert t3_data['currentHex'] == "#EAEEE8", f"Current hex should reset to #EAEEE8, got {t3_data['currentHex']}"
        assert t3_data['selectedHex'] == "#EAEEE8", f"Selected hex should reset to #EAEEE8, got {t3_data['selectedHex']}"
        assert t3_data['activeName'] == "Mist Green", f"Active badge should be Mist Green, got {t3_data['activeName']}"
        assert t3_data['mistBadgeVisible'], "Mist Green swatch should have Selected badge visible"
        print("✓ Test 3 Passed: Reset to default button restored #EAEEE8 cleanly!")

        # -------------------------------------------------------------
        # TEST 4: GLOBAL APPLICATION ACROSS ENTIRE TEMPO APPLICATION
        # -------------------------------------------------------------
        print("\n--- TEST 4: GLOBAL APPLICATION ACROSS ALL PAGES ---")
        # Apply Sage Green (#8EA695) - rgb(142, 166, 149)
        eval_js(ws_url, """
        (function() {
            window.TempoTheme.setSelectedColor('#8EA695');
            window.TempoTheme.applySelectedColor();
        })()
        """)
        time.sleep(0.3)

        pages_to_test = [
            ("today", "Today / Entry Home"),
            ("recovery-mode", "Rmode Dashboard"),
            ("unclear-mode", "URmode Dashboard"),
            ("plan-workspace", "Working Plan"),
            ("stress-check", "Self-check / Strack"),
            ("about", "About"),
            ("community", "Community"),
            ("tool-notes", "Notes")
        ]

        # rgb(142, 166, 149) is #8EA695
        for tab_id, name in pages_to_test:
            eval_js(ws_url, f"window.TempoApp.navigateTo('{tab_id}')")
            time.sleep(0.3)
            bg_data = eval_js(ws_url, """
            (function() {
                const bodyBg = window.getComputedStyle(document.body).backgroundColor;
                const headerBg = window.getComputedStyle(document.querySelector('header.entry-header')).backgroundColor;
                const card = document.querySelector('.tempo-card, .bg-white');
                const cardBg = card ? window.getComputedStyle(card).backgroundColor : null;
                return { bodyBg, headerBg, cardBg };
            })()
            """)
            print(f"  [{name}] Body Bg: {bg_data['bodyBg']} | Header Bg: {bg_data['headerBg']} | Card Bg: {bg_data['cardBg']}")
            assert "142, 166, 149" in bg_data['bodyBg'], f"Page {name} body background mismatch: {bg_data['bodyBg']}"
            assert "142, 166, 149" in bg_data['headerBg'], f"Page {name} header background mismatch: {bg_data['headerBg']}"
            if bg_data['cardBg']:
                # Cards must stay white (rgb(255, 255, 255))
                assert "255, 255, 255" in bg_data['cardBg'], f"Card surface was modified on {name}: {bg_data['cardBg']}"

        # Capture screenshots on Working Plan, Rmode Dashboard, Community
        eval_js(ws_url, "window.TempoApp.navigateTo('plan-workspace')")
        time.sleep(0.3)
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "global_bg_working_plan.png"))

        eval_js(ws_url, "window.TempoApp.navigateTo('recovery-mode')")
        time.sleep(0.3)
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "global_bg_rmode_dashboard.png"))

        eval_js(ws_url, "window.TempoApp.navigateTo('community')")
        time.sleep(0.3)
        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "global_bg_community.png"))

        print("✓ Test 4 Passed: Global background applied consistently across all application pages while preserving white card surfaces!")

        # -------------------------------------------------------------
        # TEST 5: PERSISTENCE & USER ACCOUNT ISOLATION
        # -------------------------------------------------------------
        print("\n--- TEST 5: PERSISTENCE & USER ACCOUNT ISOLATION ---")
        t5_data = eval_js(ws_url, """
        (async function() {
            // 1. Set User A color to Warm Blush (#ECC9BA)
            const userA_id = 'user_alpha_test_123';
            localStorage.setItem('tempo_background_color_' + userA_id, '#ECC9BA');

            // 2. Load User A
            window.TempoTheme.loadUserTheme(userA_id);
            const userA_color = window.TempoTheme.getCurrentColor();

            // 3. User B is a newly registered user with NO saved preference
            const userB_id = 'user_beta_clean_456';
            window.TempoTheme.loadUserTheme(userB_id);
            const userB_color = window.TempoTheme.getCurrentColor();

            // 4. Switch back to User A
            window.TempoTheme.loadUserTheme(userA_id);
            const userA_restored = window.TempoTheme.getCurrentColor();

            return {
                userA_color,
                userB_color,
                userA_restored
            };
        })()
        """)

        print(f"User A initial: {t5_data['userA_color']}")
        print(f"User B clean default: {t5_data['userB_color']}")
        print(f"User A restored: {t5_data['userA_restored']}")

        assert t5_data['userA_color'] == "#ECC9BA", f"Expected #ECC9BA for User A, got {t5_data['userA_color']}"
        assert t5_data['userB_color'] == "#EAEEE8", f"User B without preference MUST receive default #EAEEE8, got {t5_data['userB_color']}"
        assert t5_data['userA_restored'] == "#ECC9BA", f"User A preference must restore #ECC9BA, got {t5_data['userA_restored']}"
        print("✓ Test 5 Passed: User preferences persist and are strictly isolated between accounts without sharing!")

        # -------------------------------------------------------------
        # TEST 6: BILINGUAL LOCALIZATION (EN <-> VI)
        # -------------------------------------------------------------
        print("\n--- TEST 6: BILINGUAL LOCALIZATION (EN <-> VI) ---")
        eval_js(ws_url, """
        (function() {
            window.TempoApp.navigateTo('personal-space', 'settings');
            window.TempoPersonalSpace.selectTab('settings');
            window.TempoI18n.setLanguage('en');
        })()
        """)
        time.sleep(0.4)

        en_data = eval_js(ws_url, """
        (function() {
            return {
                groupHeading: document.getElementById('appearance-group-heading')?.innerText?.trim(),
                title: document.getElementById('appearance-title')?.innerText?.trim(),
                desc: document.getElementById('appearance-description')?.innerText?.trim(),
                previewLabel: document.getElementById('appearance-preview-label')?.innerText?.trim(),
                btnReset: document.getElementById('btn-appearance-reset')?.innerText?.trim(),
                btnApply: document.getElementById('btn-appearance-apply')?.innerText?.trim(),
                activeLabel: document.getElementById('appearance-active-label')?.innerText?.trim(),
                selectedBadgeText: document.querySelector('.appearance-swatch-badge:not(.hidden)')?.innerText?.trim(),
                defaultTag: document.querySelector('.appearance-swatch-btn[data-bg-hex="#EAEEE8"] .rounded')?.innerText?.trim()
            };
        })()
        """)

        print("English Appearance UI:", json.dumps(en_data, indent=2))
        assert en_data['groupHeading'] == "APPEARANCE", f"Expected 'APPEARANCE', got {en_data['groupHeading']}"
        assert en_data['title'] == "Background Color", f"Expected 'Background Color', got {en_data['title']}"
        assert en_data['desc'] == "Choose a background color for your Tempo experience.", f"Desc mismatch: {en_data['desc']}"
        assert en_data['previewLabel'] == "PREVIEW", f"Expected 'PREVIEW', got {en_data['previewLabel']}"
        assert en_data['btnReset'] == "Reset to default", f"Expected 'Reset to default', got {en_data['btnReset']}"
        assert en_data['btnApply'] == "Apply", f"Expected 'Apply', got {en_data['btnApply']}"
        assert en_data['activeLabel'] == "Active:", f"Expected 'Active:', got {en_data['activeLabel']}"
        assert en_data['selectedBadgeText'] == "Selected", f"Expected 'Selected', got {en_data['selectedBadgeText']}"
        assert en_data['defaultTag'] == "Default", f"Expected 'Default', got {en_data['defaultTag']}"

        capture_screenshot(ws_url, os.path.join(ARTIFACT_DIR, "appearance_settings_en.png"))

        # Switch back to Vietnamese
        eval_js(ws_url, "window.TempoI18n.setLanguage('vi')")
        time.sleep(0.4)

        vi_data = eval_js(ws_url, """
        (function() {
            return {
                groupHeading: document.getElementById('appearance-group-heading')?.innerText?.trim(),
                title: document.getElementById('appearance-title')?.innerText?.trim(),
                btnReset: document.getElementById('btn-appearance-reset')?.innerText?.trim(),
                btnApply: document.getElementById('btn-appearance-apply')?.innerText?.trim(),
                selectedBadgeText: document.querySelector('.appearance-swatch-badge:not(.hidden)')?.innerText?.trim(),
                defaultTag: document.querySelector('.appearance-swatch-btn[data-bg-hex="#EAEEE8"] .rounded')?.innerText?.trim()
            };
        })()
        """)
        assert vi_data['groupHeading'] == "GIAO DIỆN", f"Expected 'GIAO DIỆN', got {vi_data['groupHeading']}"
        assert vi_data['title'] == "Màu nền", f"Expected 'Màu nền', got {vi_data['title']}"
        assert vi_data['btnReset'] == "Đặt lại mặc định", f"Expected 'Đặt lại mặc định', got {vi_data['btnReset']}"
        assert vi_data['btnApply'] == "Áp dụng", f"Expected 'Áp dụng', got {vi_data['btnApply']}"
        assert vi_data['selectedBadgeText'] == "Đang chọn", f"Expected 'Đang chọn', got {vi_data['selectedBadgeText']}"
        assert vi_data['defaultTag'] == "Mặc định", f"Expected 'Mặc định', got {vi_data['defaultTag']}"

        print("✓ Test 6 Passed: Complete bilingual switching between English and Vietnamese verified!")

        # Reset back to default Mist Green
        eval_js(ws_url, "window.TempoTheme.resetToDefault()")

        print("\n=======================================================")
        print("ALL APPEARANCE CUSTOMIZATION TESTS PASSED (100%)!")
        print("=======================================================")

    finally:
        proc.terminate()

if __name__ == "__main__":
    run_tests()
