# -*- coding: utf-8 -*-
import subprocess
import time
import json
import urllib.request
import websocket
import tempfile
import base64
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_entryhome_test_')
port = 9467
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
time.sleep(2.5)

try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        tabs = json.loads(resp.read().decode())
        pages = [t for t in tabs if t.get('type') == 'page' and 'localhost' in t.get('url', '')]
    ws_url = pages[0]['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)

    msg_id = 1
    def send_cmd(method, params=None):
        global msg_id
        cmd = {'id': msg_id, 'method': method, 'params': params or {}}
        msg_id += 1
        ws.send(json.dumps(cmd))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == cmd['id']:
                return resp.get('result', {})

    def eval_js(expr):
        res = send_cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
        return res.get('result', {}).get('value')

    def capture_screenshot(filename, full_page=False):
        params = {"format": "png"}
        if full_page:
            params["captureBeyondViewport"] = True
        res = send_cmd("Page.captureScreenshot", params)
        data = base64.b64decode(res.get("data", ""))
        with open(filename, "wb") as f:
            f.write(data)
        print(f"Captured screenshot: {filename} ({len(data)} bytes)")

    send_cmd('Page.enable')
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 1280,
        "height": 900,
        "deviceScaleFactor": 1,
        "mobile": False
    })

    for _ in range(30):
        if eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined'"):
            break
        time.sleep(0.5)

    print("=" * 60)
    print("VERIFYING REDESIGNED TEMPO ENTRYHOME")
    print("=" * 60)

    # 1. Ensure Neutral Entry Home (Default Mode) and English Language
    eval_js("""
        if (window.TempoAuth && typeof window.TempoAuth.setAuthLanguage === 'function') {
            window.TempoAuth.setAuthLanguage('en');
        }
        window.TempoMode.setMode('default');
    """)
    time.sleep(0.3)
    eval_js("window.TempoApp.navigateTo('today');")
    time.sleep(0.5)

    current_mode = eval_js("window.TempoMode.getMode()")
    print("1. Current Mode:", current_mode)
    assert current_mode == 'default', "Should be in default neutral mode"

    # 2. Check Visual Elements of Welcome Card
    welcome_headline = eval_js("document.querySelector('[data-tempo-ui=\"entry-welcome-card\"] h1').textContent.trim()")
    print("2a. Welcome card headline:", welcome_headline)
    assert "What do you need right now?" in welcome_headline

    welcome_tag = eval_js("document.querySelector('[data-tempo-ui=\"entry-welcome-card\"] span').textContent.trim()")
    print("2b. Welcome card tag:", welcome_tag)
    assert "Welcome to Tempo" in welcome_tag

    cta_btn_text = eval_js("document.getElementById('btn-hero-figure-start').textContent.trim()")
    print("2c. Primary CTA button text:", cta_btn_text)
    assert "Help me figure out where to start" in cta_btn_text

    # 3. Check Primary Action Cards (Quick Relief and Focus Now)
    action_cards = eval_js("""
        (() => {
            const container = document.querySelector('[data-tempo-ui=\"entry-action-cards\"]');
            if (!container) return null;
            const cards = container.children;
            return {
                count: cards.length,
                card1Label: cards[0]?.querySelector('h3')?.textContent.trim(),
                card1Bg: cards[0]?.className.includes('bg-[#DEECE5]'),
                card1Mascot: cards[0]?.querySelector('img')?.getAttribute('src'),
                card2Label: cards[1]?.querySelector('h3')?.textContent.trim(),
                card2Bg: cards[1]?.className.includes('bg-[#D29C85]'),
                card2Mascot: cards[1]?.querySelector('img')?.getAttribute('src')
            };
        })()
    """)
    print("3. Primary Action Cards:", json.dumps(action_cards, indent=2))
    assert action_cards['count'] == 2, "Must have exactly 2 action cards side by side"
    assert "Quick Relief" in action_cards['card1Label']
    assert action_cards['card1Bg'] == True
    assert "quick-relief-mascot" in action_cards['card1Mascot']
    assert "Focus Now" in action_cards['card2Label']
    assert action_cards['card2Bg'] == True
    assert "focus-now-mascot" in action_cards['card2Mascot']

    # 4. Check From the Tempo Community Panel
    community_panel = eval_js("""
        (() => {
            const panel = document.querySelector('[data-tempo-ui=\"entry-community-panel\"]');
            if (!panel) return null;
            const title = panel.querySelector('h3')?.textContent.trim();
            const seeAllBtn = document.getElementById('btn-see-all-posts')?.textContent.trim();
            const previews = document.querySelectorAll('#homepage-community-posts-list > div');
            return {
                title,
                seeAllBtn,
                previewsCount: previews.length
            };
        })()
    """)
    print("4. Community Panel:", json.dumps(community_panel, indent=2))
    assert community_panel['title'] == "From the Tempo Community"
    assert "See all" in community_panel['seeAllBtn']
    assert community_panel['previewsCount'] >= 1, "Must render real community post previews"

    # 5. Check Secondary Feature Cards Row (Self-check, Work Plan, Notes)
    secondary_cards = eval_js("""
        (() => {
            const container = document.querySelector('[data-tempo-ui=\"entry-secondary-cards\"]');
            if (!container) return null;
            const cards = container.querySelectorAll('.grid > div');
            return Array.from(cards).map(c => ({
                label: c.getAttribute('aria-label'),
                imgSrc: c.querySelector('img')?.getAttribute('src')
            }));
        })()
    """)
    print("5. Secondary Feature Cards:", json.dumps(secondary_cards, indent=2))
    assert len(secondary_cards) == 3, "Must have exactly 3 secondary cards in the row"
    assert secondary_cards[0]['label'] == "Self-check"
    assert "self-check-mascot" in secondary_cards[0]['imgSrc']
    assert secondary_cards[1]['label'] == "Work Plan"
    assert "work-plan-mascot" in secondary_cards[1]['imgSrc']
    assert secondary_cards[2]['label'] == "Notes"
    assert "notes-mascot" in secondary_cards[2]['imgSrc']

    # 6. Test Interactive Functionality of All Cards
    print("\n--- Testing Card Interactions ---")
    # 6a. Primary CTA
    eval_js("document.getElementById('btn-hero-figure-start').click();")
    time.sleep(0.3)
    modal_open = eval_js("!document.getElementById('modal-routing-selection').classList.contains('hidden')")
    print("6a. Routing modal opened by primary CTA:", modal_open)
    assert modal_open == True
    # Close modal
    eval_js("""
        document.getElementById('modal-routing-selection').classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
    """)

    # 6b. Community See All
    eval_js("document.getElementById('btn-see-all-posts').click();")
    time.sleep(0.3)
    tab_community = eval_js("window.location.hash")
    print("6b. Navigated on 'See all →':", tab_community)
    assert '#community' in tab_community

    # Return home
    eval_js("window.TempoApp.navigateTo('today');")
    time.sleep(0.3)

    # 6c. Unauthenticated Guest boundary check on Self-check
    print("6c. Testing unauthenticated guest access to Self-check (auth gate)...")
    eval_js("document.querySelector('[data-tempo-ui=\"entry-secondary-cards\"] .grid > div:nth-child(1)').click();")
    time.sleep(0.3)
    is_signin_open = eval_js("!document.getElementById('modal-signin').classList.contains('hidden')")
    print("   Sign-in modal opened for guest:", is_signin_open)
    assert is_signin_open == True, "Guest clicking protected Self-check must open sign-in modal"
    eval_js("if (window.TempoAuth) window.TempoAuth.closeModal();")
    time.sleep(0.2)

    # 6d. Authenticated User navigation for Self-check, Work Plan, Notes
    print("6d. Testing authenticated user navigation...")
    auth_res = eval_js("""
        (async () => {
            localStorage.setItem('tempo_mock_account_test_student@tempo.edu', JSON.stringify({
                password: 'password123',
                full_name: 'Test Student',
                role: 'student'
            }));
            localStorage.setItem('tempo_local_dev_user', JSON.stringify({
                id: 'local_test_user_redesign',
                email: 'test_student@tempo.edu',
                user_metadata: { full_name: 'Test Student', role: 'student' }
            }));
            if (window.TempoAuth) await window.TempoAuth.checkSession();
            return {
                authed: !!(window.TempoAuth && window.TempoAuth.getCurrentUser()),
                state: window.TempoAuth?.getAuthState()
            };
        })()
    """)
    print("   Auth setup result:", auth_res)
    assert auth_res['authed'] == True, "Mock user must be authenticated"

    eval_js("window.TempoApp.navigateTo('today');")
    time.sleep(0.3)

    # Click Self-check when authenticated
    eval_js("document.querySelector('[data-tempo-ui=\"entry-secondary-cards\"] .grid > div:nth-child(1)').click();")
    time.sleep(0.5)
    tab_check = eval_js("window.location.hash")
    print("   Authenticated navigated on 'Self-check':", tab_check)
    assert '#stress-check' in tab_check

    # Return home
    eval_js("window.TempoApp.navigateTo('today');")
    time.sleep(0.3)

    # Click Work Plan
    eval_js("document.querySelector('[data-tempo-ui=\"entry-secondary-cards\"] .grid > div:nth-child(2)').click();")
    time.sleep(0.5)
    tab_plan = eval_js("window.location.hash")
    print("   Authenticated navigated on 'Work Plan':", tab_plan)
    assert '#plan-workspace' in tab_plan

    # Return home
    eval_js("window.TempoApp.navigateTo('today');")
    time.sleep(0.3)

    # Click Notes
    eval_js("document.querySelector('[data-tempo-ui=\"entry-secondary-cards\"] .grid > div:nth-child(3)').click();")
    time.sleep(0.5)
    tab_notes = eval_js("window.location.hash")
    print("   Navigated on 'Notes':", tab_notes)
    assert '#tool-notes' in tab_notes

    # 6e. Return home, reset to guest & default mode for clean screenshots
    print("6e. Resetting to default neutral mode and guest state for visual captures...")
    eval_js("""
        (async () => {
            localStorage.removeItem('tempo_local_dev_user');
            localStorage.removeItem('tempo_mock_account_test_student@tempo.edu');
            if (window.TempoAuth) {
                await window.TempoAuth.signOut();
                window.TempoAuth.setAuthLanguage('en');
            }
            window.TempoMode.setMode('default');
            window.TempoApp.navigateTo('today');
            window.scrollTo(0, 0);
        })()
    """)
    time.sleep(0.6)

    # 7. Capture Desktop Screenshot Upper View (1280x850)
    artifact_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
    capture_screenshot(os.path.join(artifact_dir, "entryhome_redesign_desktop_1280.png"))

    # Capture lower secondary cards (matching Screenshot 2)
    eval_js("document.querySelector('[data-tempo-ui=\"entry-secondary-cards\"]').scrollIntoView({ behavior: 'instant', block: 'center' });")
    time.sleep(0.4)
    capture_screenshot(os.path.join(artifact_dir, "entryhome_redesign_lower_cards.png"))

    # Return scroll to top
    eval_js("window.scrollTo(0, 0);")
    time.sleep(0.3)

    # Capture full page desktop
    capture_screenshot(os.path.join(artifact_dir, "entryhome_redesign_fullpage.png"), full_page=True)

    # Capture tablet 768px
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 768,
        "height": 1024,
        "deviceScaleFactor": 1,
        "mobile": False
    })
    time.sleep(0.5)
    capture_screenshot(os.path.join(artifact_dir, "entryhome_redesign_tablet_768.png"))

    # Capture mobile 375px
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 375,
        "height": 812,
        "deviceScaleFactor": 2,
        "mobile": True
    })
    time.sleep(0.5)
    capture_screenshot(os.path.join(artifact_dir, "entryhome_redesign_mobile_375.png"))

    print("\nALL ENTRYHOME REDESIGN VERIFICATIONS AND SCREENSHOTS COMPLETED!")

finally:
    ws.close()
    proc.terminate()
    proc.wait()
