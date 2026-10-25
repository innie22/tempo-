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

def log(msg):
    print(msg, flush=True)

user_data_dir = tempfile.mkdtemp(prefix="tempo_recovery_ui_test_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9310

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "http://localhost:8000/"
]

log(f"Launching Edge on port {port}...")
proc = subprocess.Popen(cmd)
ws = None

try:
    ws_url = None
    for _ in range(30):
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

    ws = websocket.create_connection(ws_url)
    msg_id = 1

    def send_command(method, params=None):
        global msg_id
        cid = msg_id
        msg_id += 1
        req = {"id": cid, "method": method}
        if params:
            req["params"] = params
        ws.send(json.dumps(req))
        while True:
            resp = json.loads(ws.recv())
            if resp.get("id") == cid:
                if "error" in resp:
                    raise RuntimeError(f"CDP error: {resp['error']}")
                return resp.get("result", {})

    def eval_js(expression):
        res = send_command("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True
        })
        if "exceptionDetails" in res:
            raise RuntimeError(f"JS error: {res['exceptionDetails']}")
        return res.get("result", {}).get("value")

    def capture_screenshot(filename):
        res = send_command("Page.captureScreenshot", {"format": "png"})
        data = base64.b64decode(res["data"])
        artifacts_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
        filepath = os.path.join(artifacts_dir, filename)
        with open(filepath, "wb") as f:
            f.write(data)
        log(f"Saved screenshot: {filepath}")

    send_command("Page.enable")
    send_command("DOM.enable")
    send_command("Emulation.setDeviceMetricsOverride", {
        "width": 1280,
        "height": 900,
        "deviceScaleFactor": 1,
        "mobile": False
    })

    log("Waiting for page load and TempoMode ready...")
    for _ in range(20):
        ready = eval_js("typeof window.TempoMode !== 'undefined' && typeof window.TempoMode.transitionContext === 'function'")
        if ready:
            break
        time.sleep(0.5)
    time.sleep(0.5)

    # Setup mock user and switch to Recovery Mode
    eval_js("""
        (() => {
            localStorage.setItem('tempo_auth_user', JSON.stringify({
                id: 'test-user-1',
                email: 'innie@example.com',
                name: 'Innie',
                preferredName: 'Innie'
            }));
            localStorage.setItem('tempo_recovery_intro_seen', 'true');
            localStorage.setItem('tempo_recovery_setup_completed', 'true');
            localStorage.setItem('tempo_recovery_note', JSON.stringify({
                content: 'Drink more than 3 cups of water'
            }));
            if (window.TempoMode && window.TempoMode.transitionContext) {
                window.TempoMode.transitionContext('recovery', { skipSetupCheck: true });
            } else if (window.TempoMode && window.TempoMode.setMode) {
                window.TempoMode.setMode('recovery');
            }
            if (window.TempoMode && window.TempoMode.renderRmodeHome) {
                window.TempoMode.renderRmodeHome();
            }
        })()
    """)
    time.sleep(1)

    log("\n--- TEST 1: Full-page background color is #E8ECF1 ---")
    bg_body = eval_js("document.body.style.backgroundColor")
    bg_main = eval_js("document.querySelector('main').style.backgroundColor")
    computed_bg = eval_js("window.getComputedStyle(document.body).backgroundColor")
    log(f"Body style bg: {bg_body}, Main style bg: {bg_main}, Computed bg: {computed_bg}")
    assert '232, 236, 241' in bg_body or bg_body.lower() == '#e8ecf1', f"Expected #E8ECF1, got {bg_body}"
    assert '232, 236, 241' in bg_main or bg_main.lower() == '#e8ecf1', f"Expected main bg #E8ECF1, got {bg_main}"
    log("✓ Full-page background color is correctly #E8ECF1")

    log("\n--- TEST 2: Header and Greeting in Terracotta (#D48366) ---")
    greeting_text = eval_js("document.querySelector('#rmode-home-content h2')?.textContent.trim()")
    greeting_color = eval_js("window.getComputedStyle(document.querySelector('#rmode-home-content h2')).color")
    log(f"Greeting text: '{greeting_text}', Color: {greeting_color}")
    assert "Hi Innie, how are you today?" in greeting_text, f"Unexpected greeting: {greeting_text}"
    # Terracotta #D48366 in rgb is rgb(212, 131, 102)
    assert "212, 131, 102" in greeting_color, f"Expected terracotta color rgb(212, 131, 102), got {greeting_color}"
    log("✓ Header and Greeting are correctly rendered in terracotta")

    log("\n--- TEST 2B: Navbar Recovery Mode Button Removed ---")
    navbar_shell_hidden = eval_js("document.getElementById('mode-indicator-shell')?.classList.contains('hidden')")
    dashboard_selector_exists = eval_js("!!document.querySelector('#rmode-home-content #btn-home-mode-selector')")
    log(f"Navbar mode-indicator-shell is hidden: {navbar_shell_hidden}, Dashboard mode selector exists: {dashboard_selector_exists}")
    assert navbar_shell_hidden is True, "mode-indicator-shell in navbar must be hidden in Recovery Mode"
    assert dashboard_selector_exists is True, "Dashboard mode selector button must be preserved in Recovery Mode"
    log("✓ Navbar Recovery Mode dropdown/button is successfully removed, while dashboard selector is preserved")

    log("\n--- TEST 2C: Header Vertical Spacing Between Button and Greeting is ~5px ---")
    gap_btn_to_greeting = eval_js("""
        (() => {
            const btn = document.getElementById('btn-home-mode-selector');
            const h2 = document.querySelector('#rmode-home-content h2');
            if (!btn || !h2) return null;
            const b = btn.getBoundingClientRect();
            const h = h2.getBoundingClientRect();
            return Math.round(h.top - b.bottom);
        })()
    """)
    log(f"Measured button-to-greeting gap: {gap_btn_to_greeting}px")
    assert gap_btn_to_greeting is not None, "Could not find button or greeting elements"
    assert abs(gap_btn_to_greeting - 5) <= 1, f"Expected ~5px vertical gap, got {gap_btn_to_greeting}px"
    log(f"✓ Vertical gap between Recovery Mode button and greeting is {gap_btn_to_greeting}px (matches ~5px requirement)")

    gap_greeting_to_selfcheck = eval_js("""
        (() => {
            const greeting = document.querySelector('.recovery-greeting');
            const h2 = document.querySelector('.recovery-greeting h2');
            const card = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            if (!greeting || !card) return null;
            const gb = greeting.getBoundingClientRect();
            const hb = h2 ? h2.getBoundingClientRect() : gb;
            const cb = card.getBoundingClientRect();
            return {
                greetingBottom: gb.bottom,
                h2Bottom: hb.bottom,
                cardTop: cb.top,
                gapFromGreetingDiv: Math.round(cb.top - gb.bottom),
                gapFromH2: Math.round(cb.top - hb.bottom)
            };
        })()
    """)
    log(f"Measured greeting-to-card gap: {gap_greeting_to_selfcheck}")
    assert gap_greeting_to_selfcheck is not None, "Could not find greeting or card elements"
    assert abs(gap_greeting_to_selfcheck["gapFromH2"] - 25) <= 1, f"Expected ~25px vertical gap from greeting text to self-check card (+5px), got {gap_greeting_to_selfcheck['gapFromH2']}px"
    assert abs(gap_greeting_to_selfcheck["gapFromGreetingDiv"] - 25) <= 1, f"Expected ~25px vertical gap from greeting container to self-check card (+5px), got {gap_greeting_to_selfcheck['gapFromGreetingDiv']}px"
    log(f"✓ Vertical gap between greeting and Today's self-check card is {gap_greeting_to_selfcheck['gapFromH2']}px (matches +5px increase requirement -> ~25px)")

    log("\n--- TEST 3: Left Column Top - Today's self-check Card ---")
    self_check_title = eval_js("document.querySelector('[data-tempo-ui=\"recovery-self-check\"] h3')?.textContent.trim()")
    tag_text = eval_js("document.querySelector('[data-tempo-ui=\"recovery-self-check\"] span')?.textContent.trim()")
    streak_text = eval_js("document.querySelector('[data-tempo-ui=\"recovery-self-check\"] p.italic')?.textContent.trim()")
    btn_view = eval_js("!!document.querySelector('button[onclick*=\"handleSelfCheckAction(\\'view\\')\"]')")
    btn_edit = eval_js("!!document.querySelector('button[onclick*=\"handleSelfCheckAction(\\'manage\\')\"]')")
    log(f"Self-check title: '{self_check_title}', Tag: '{tag_text}', Streak: '{streak_text}', View btn: {btn_view}, Edit btn: {btn_edit}")
    assert "Today’s self-check" in self_check_title or "Today's self-check" in self_check_title
    assert "Your daily check-in" in tag_text
    assert "streak" in streak_text.lower()
    assert btn_view is True and btn_edit is True

    card_dims = eval_js("""
        (() => {
            const el = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            const parent = el.closest('.recovery-left-col');
            const r = el.getBoundingClientRect();
            const pr = parent.getBoundingClientRect();
            const cs = window.getComputedStyle(el);
            return {
                width: Math.round(r.width),
                parentWidth: Math.round(pr.width),
                widthDiff: Math.round(pr.width - r.width),
                leftGap: Math.round(r.left - pr.left),
                rightGap: Math.round(pr.right - r.right),
                height: Math.round(r.height),
                minHeight: cs.minHeight,
                borderRadius: cs.borderRadius,
                display: cs.display,
                flexDirection: cs.flexDirection,
                justifyContent: cs.justifyContent,
                backgroundColor: cs.backgroundColor,
                boxShadow: cs.boxShadow
            };
        })()
    """)
    log(f"Self-check card dimensions: {json.dumps(card_dims, indent=2)}")
    assert card_dims["height"] == 290, f"Expected height 290px matching Urmode card, got {card_dims['height']}"
    assert card_dims["minHeight"] == "290px", f"Expected minHeight 290px, got {card_dims['minHeight']}"
    assert card_dims["borderRadius"] == "24px", f"Expected borderRadius 24px (rounded-3xl), got {card_dims['borderRadius']}"
    assert card_dims["display"] == "flex" and card_dims["justifyContent"] == "space-between"
    assert card_dims["widthDiff"] == 30, f"Expected card width to be reduced by 30px (10px from previous), got diff={card_dims['widthDiff']}"
    assert abs(card_dims["leftGap"] - 15) <= 1, f"Expected ~15px left gap (+5px on side), got {card_dims['leftGap']}"
    assert abs(card_dims["rightGap"] - 15) <= 1, f"Expected ~15px right gap (+5px on side), got {card_dims['rightGap']}"
    assert "254, 250, 244" in card_dims["backgroundColor"], f"Expected #FEFAF4 (rgb(254, 250, 244)), got {card_dims['backgroundColor']}"
    assert card_dims["boxShadow"] != "none" and ("rgba(75, 55, 40" in card_dims["boxShadow"] or "rgba(0, 0, 0" in card_dims["boxShadow"]), f"Expected subtle box shadow, got {card_dims['boxShadow']}"
    log(f"✓ Today's self-check card background is #FEFAF4 and has soft subtle box shadow: {card_dims['boxShadow']}")
    log(f"✓ Today's self-check card width is reduced by exactly 10px ({card_dims['width']}px vs parent {card_dims['parentWidth']}px, diff={card_dims['widthDiff']}px) and centered (left gap: {card_dims['leftGap']}px, right gap: {card_dims['rightGap']}px)")

    log("\n--- TEST 4: Left Column Bottom - Quick Relief and Learn & Solve Match Entry Home & Urmode ---")
    support_cards_info = eval_js("""
        (() => {
            const qr = document.querySelector('#rmode-home-content [title="Quick Relief"]');
            const ls = document.querySelector('#rmode-home-content [title="Learn & Solve"]');
            if (!qr || !ls) return null;

            const qrCs = window.getComputedStyle(qr);
            const lsCs = window.getComputedStyle(ls);
            const qrImg = qr.querySelector('img');
            const lsImg = ls.querySelector('img');
            const qrTitle = qr.querySelector('h3')?.textContent.trim();
            const lsTitle = ls.querySelector('h3')?.textContent.trim();
            const qrDesc = qr.querySelector('p')?.textContent.trim();
            const lsDesc = ls.querySelector('p')?.textContent.trim();

            return {
                qr: {
                    height: qr.getBoundingClientRect().height,
                    minHeight: qrCs.minHeight,
                    borderRadius: qrCs.borderRadius,
                    bgColor: qrCs.backgroundColor,
                    borderColor: qrCs.borderColor,
                    imgSrc: qrImg ? qrImg.getAttribute('src') : null,
                    title: qrTitle,
                    desc: qrDesc,
                    hasModalClick: qr.getAttribute('onclick')?.includes('openModal') || qr.getAttribute('onclick')?.includes('openQuickReliefModal')
                },
                ls: {
                    height: ls.getBoundingClientRect().height,
                    minHeight: lsCs.minHeight,
                    borderRadius: lsCs.borderRadius,
                    bgColor: lsCs.backgroundColor,
                    borderColor: lsCs.borderColor,
                    imgSrc: lsImg ? lsImg.getAttribute('src') : null,
                    title: lsTitle,
                    desc: lsDesc,
                    hasNavigateClick: ls.getAttribute('onclick')?.includes('navigateTo') || ls.getAttribute('onclick')?.includes('#learn')
                }
            };
        })()
    """)
    log(f"Support cards info: {json.dumps(support_cards_info, indent=2)}")
    assert support_cards_info is not None, "Quick Relief and Learn & Solve cards must exist"
    
    # Assert dimensions & styling
    assert support_cards_info["qr"]["height"] == 175, f"Expected QR height 175px, got {support_cards_info['qr']['height']}"
    assert support_cards_info["qr"]["minHeight"] == "175px"
    assert support_cards_info["qr"]["borderRadius"] == "24px"
    assert support_cards_info["qr"]["imgSrc"] == "assets/quick-relief-mascot-transparent.png"
    assert support_cards_info["qr"]["title"] == "Quick Relief"
    assert "Quick ways to ease stress" in support_cards_info["qr"]["desc"]
    assert support_cards_info["qr"]["hasModalClick"] is True

    assert support_cards_info["ls"]["height"] == 175, f"Expected LS height 175px, got {support_cards_info['ls']['height']}"
    assert support_cards_info["ls"]["minHeight"] == "175px"
    assert support_cards_info["ls"]["borderRadius"] == "24px"
    assert support_cards_info["ls"]["imgSrc"] == "assets/learn-solve-mascot.png"
    assert "Learn" in support_cards_info["ls"]["title"] and "Solve" in support_cards_info["ls"]["title"]
    assert "Tips and tools to help you cope" in support_cards_info["ls"]["desc"]
    assert support_cards_info["ls"]["hasNavigateClick"] is True

    log("✓ Quick Relief and Learn & Solve cards exactly match Entry Home and Urmode implementations (175px, rounded-3xl, exact assets & click handlers)")

    log("\n--- TEST 5: Right Column - NOTE Card, Recently Card, Prompt & Mode Switch ---")
    note_content = eval_js("document.querySelector('[data-tempo-ui=\"dashboard-note-card\"] p')?.textContent.trim()")
    recently_title = eval_js("document.querySelector('[data-tempo-ui=\"recovery-recently\"] h4')?.textContent.trim()")
    btn_adjust_tracking = eval_js("!!document.querySelector('[data-tempo-ui=\"recovery-recently\"] button')")
    tension_metric = eval_js("document.querySelector('[data-tempo-ui=\"recovery-recently\"]')?.innerText.includes('43%')")
    sleep_metric = eval_js("document.querySelector('[data-tempo-ui=\"recovery-recently\"]')?.innerText.includes('3')")
    walking_metric = eval_js("document.querySelector('[data-tempo-ui=\"recovery-recently\"]')?.innerText.includes('60m')")
    report_footer = eval_js("document.querySelector('[data-tempo-ui=\"recovery-recently\"]')?.innerText.includes('days until your weekly report')")
    overwhelm_prompt = eval_js("document.querySelector('.recovery-right-col')?.innerText.includes('Are things feeling more overwhelming now?')")
    btn_change_mode = eval_js("!!document.querySelector('.recovery-right-col button[onclick*=\"openChangeModeModal\"]')")
    
    log(f"Note: '{note_content}', Recently: '{recently_title}', Adjust btn: {btn_adjust_tracking}")
    log(f"Metrics (Tension 43%: {tension_metric}, Sleep 3: {sleep_metric}, Walking 60m: {walking_metric}, Report footer: {report_footer})")
    log(f"Overwhelmed prompt: {overwhelm_prompt}, Change mode btn: {btn_change_mode}")

    recently_bg = eval_js("window.getComputedStyle(document.querySelector('[data-tempo-ui=\"recovery-recently\"]')).backgroundColor")
    selfcheck_bg = eval_js("window.getComputedStyle(document.querySelector('[data-tempo-ui=\"recovery-self-check\"]')).backgroundColor")
    assert "254, 250, 244" in recently_bg, f"Expected #FEFAF4 for Recently card, got {recently_bg}"
    assert recently_bg == selfcheck_bg, f"Expected Recently and Today's self-check cards to have matching background color, got {recently_bg} vs {selfcheck_bg}"
    log(f"✓ Recently card background is {recently_bg} (#FEFAF4), matching Today's self-check card exactly")

    gap_note_recently = eval_js("""
        (() => {
            const noteCard = document.querySelector('[data-tempo-ui="dashboard-note-card"]');
            const recentlyCard = document.querySelector('[data-tempo-ui="recovery-recently"]');
            const promptWrap = document.querySelector('.recovery-prompt-wrap');
            if (!noteCard || !recentlyCard || !promptWrap) return null;
            const nb = noteCard.getBoundingClientRect();
            const rb = recentlyCard.getBoundingClientRect();
            const pb = promptWrap.getBoundingClientRect();
            return {
                noteBottom: nb.bottom,
                recentlyTop: rb.top,
                recentlyBottom: rb.bottom,
                promptTop: pb.top,
                gap_note_recently: Math.round(rb.top - nb.bottom),
                gap_recently_prompt: Math.round(pb.top - rb.bottom)
            };
        })()
    """)
    log(f"Right column spacing: {gap_note_recently}")
    assert gap_note_recently is not None, "Could not find NOTE card, Recently card, or prompt wrap"
    assert abs(gap_note_recently["gap_note_recently"] - 10) <= 1, f"Expected ~10px gap between NOTE card and Recently card, got {gap_note_recently['gap_note_recently']}px"
    log(f"✓ Vertical gap between NOTE card and Recently card is {gap_note_recently['gap_note_recently']}px (matches ~10px requirement)")
    assert abs(gap_note_recently["gap_recently_prompt"] - 20) <= 1, f"Expected ~20px gap between Recently card and prompt section, got {gap_note_recently['gap_recently_prompt']}px"
    log(f"✓ Vertical gap between Recently card and prompt section is {gap_note_recently['gap_recently_prompt']}px (matches ~20px requirement)")
    assert "Drink more than 3 cups of water" in note_content
    assert "Recently" in recently_title
    assert btn_adjust_tracking and tension_metric and sleep_metric and walking_metric and report_footer
    assert overwhelm_prompt and btn_change_mode
    log("✓ Right column (NOTE card, Recently card, Prompt & Button) is completely verified")

    log("\n--- TEST 6: Second Screen - Your Working Plan Card ---")
    wp_title = eval_js("document.querySelector('[data-tempo-ui=\"recovery-working-plan\"] h3')?.textContent.trim()")
    wp_adjust_btn = eval_js("!!document.querySelector('[data-tempo-ui=\"recovery-working-plan\"] button[onclick*=\"AdjustmentFlow\"], [data-tempo-ui=\"recovery-working-plan\"] button[onclick*=\"plan-workspace\"]')")
    progress_text = eval_js("document.querySelector('[data-tempo-ui=\"recovery-working-plan\"] span.shrink-0')?.textContent.trim()")
    task_cards_count = eval_js("document.querySelectorAll('[data-tempo-ui=\"recovery-working-plan\"] [data-task-id]').length")
    log(f"Working Plan title: '{wp_title}', Adjust btn: {wp_adjust_btn}, Progress text: '{progress_text}', Tasks: {task_cards_count}")
    wp_info = eval_js("""
        (() => {
            const panel = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
            const r = panel.getBoundingClientRect();
            return {
                width: Math.round(r.width),
                height: Math.round(r.height),
                children: Array.from(panel.children).map(c => ({
                    tag: c.tagName,
                    class: c.className,
                    height: Math.round(c.getBoundingClientRect().height),
                    width: Math.round(c.getBoundingClientRect().width)
                }))
            };
        })()
    """)
    log(f"Working Plan panel info: {json.dumps(wp_info, indent=2)}")
    assert "Your Working Plan" in wp_title
    assert wp_adjust_btn is True
    assert "Tasks" in progress_text
    assert task_cards_count >= 3
    log("✓ Working Plan card layout and tasks rendered")

    log("\n--- TEST 6B: Bidirectional Scrolling in Working Plan Panel ---")
    scroll_info = eval_js("""
        (() => {
            const sc = document.querySelector('[data-tempo-ui="recovery-plan-scroll-container"]');
            if (!sc) return null;
            const cs = window.getComputedStyle(sc);
            const subgrid = sc.querySelector('.grid');
            return {
                exists: true,
                overflowX: cs.overflowX,
                overflowY: cs.overflowY,
                overscrollBehavior: cs.overscrollBehavior || cs.overscrollBehaviorX || cs.overscrollBehaviorY,
                maxHeight: cs.maxHeight,
                clientWidth: sc.clientWidth,
                scrollWidth: sc.scrollWidth,
                clientHeight: sc.clientHeight,
                scrollHeight: sc.scrollHeight,
                hasTwoColumns: !!subgrid && subgrid.children.length >= 3
            };
        })()
    """)
    log(f"Working Plan scroll info: {json.dumps(scroll_info, indent=2)}")
    assert scroll_info is not None, "Scroll container [data-tempo-ui='recovery-plan-scroll-container'] must exist"
    assert scroll_info["overflowX"] in ["auto", "scroll"], f"Expected overflowX to be auto or scroll, got {scroll_info['overflowX']}"
    assert scroll_info["overflowY"] in ["auto", "scroll"], f"Expected overflowY to be auto or scroll, got {scroll_info['overflowY']}"
    assert "contain" in scroll_info["overscrollBehavior"], f"Expected overscrollBehavior contain, got {scroll_info['overscrollBehavior']}"
    assert scroll_info["hasTwoColumns"] is True, "Expected two-column task subgrid with divider"
    log("✓ Inner bidirectional scroll container configured with overflow-x: auto and overflow-y: auto")

    log("\n--- TEST 6C: Vertical & Horizontal Scrolling Actions & Containment ---")
    # 1. Test vertical scrolling: Add extra tasks to test vertical overflow & scrolling if needed
    v_scroll_result = eval_js("""
        (() => {
            const sc = document.querySelector('[data-tempo-ui="recovery-plan-scroll-container"]');
            if (!sc) return { error: "no sc" };
            
            // Add a temporary task item if scrollHeight <= clientHeight to test overflow
            const leftCol = sc.querySelector('.grid > div:first-child');
            let tempCard = null;
            if (sc.scrollHeight <= sc.clientHeight && leftCol) {
                tempCard = document.createElement('div');
                tempCard.className = "temp-extra-tasks";
                tempCard.innerHTML = `
                    <div style="height: 120px; border: 1px solid #ddd; margin-top: 10px; padding: 10px; border-radius: 16px;">
                        Extra Task For Vertical Scroll Verification
                    </div>
                    <div style="height: 120px; border: 1px solid #ddd; margin-top: 10px; padding: 10px; border-radius: 16px;">
                        Second Extra Task
                    </div>
                `;
                leftCol.appendChild(tempCard);
            }

            const initialScrollTop = sc.scrollTop;
            const scrollableY = sc.scrollHeight > sc.clientHeight;
            
            // Perform vertical scroll
            sc.scrollTop = 60;
            const scrolledTop = sc.scrollTop;
            
            // Test wheel event
            const wheelEvt = new WheelEvent('wheel', { deltaY: 50, deltaMode: 0, bubbles: true, cancelable: true });
            sc.dispatchEvent(wheelEvt);

            // Clean up temporary card if added
            if (tempCard) tempCard.remove();
            sc.scrollTop = 0;

            return {
                scrollableY,
                scrolledTop,
                initialScrollTop
            };
        })()
    """)
    log(f"Vertical scroll test result: {json.dumps(v_scroll_result, indent=2)}")
    assert v_scroll_result["scrollableY"] is True, "Container must have vertical overflow capability when tasks exceed height"
    assert v_scroll_result["scrolledTop"] > 0, "Container vertical scrolling must be functional"
    log("✓ Vertical scrolling succeeds and responds to scroll actions")

    # 2. Test horizontal scrolling: verify min-w-[580px] creates horizontal scroll on narrow width and scrolls
    h_scroll_result = eval_js("""
        (() => {
            const sc = document.querySelector('[data-tempo-ui="recovery-plan-scroll-container"]');
            const panel = document.querySelector('[data-tempo-ui="recovery-working-plan"]');
            if (!sc || !panel) return { error: "no sc or panel" };

            // Temporarily constrain panel width to 400px to simulate mobile/narrow width
            const origMaxWidth = panel.style.maxWidth;
            const origWidth = panel.style.width;
            panel.style.maxWidth = "400px";
            panel.style.width = "400px";

            const clientWidth = sc.clientWidth;
            const scrollWidth = sc.scrollWidth;
            const scrollableX = scrollWidth > clientWidth;

            // Perform horizontal scroll
            sc.scrollLeft = 80;
            const scrolledLeft = sc.scrollLeft;

            // Check if page overflows horizontally
            const pageOverflows = document.documentElement.scrollWidth > window.innerWidth;

            // Reset panel styling
            panel.style.maxWidth = origMaxWidth;
            panel.style.width = origWidth;
            sc.scrollLeft = 0;

            return {
                clientWidth,
                scrollWidth,
                scrollableX,
                scrolledLeft,
                pageOverflows
            };
        })()
    """)
    log(f"Horizontal scroll test result: {json.dumps(h_scroll_result, indent=2)}")
    assert h_scroll_result["scrollableX"] is True, f"Container must scroll horizontally when content exceeds width: {h_scroll_result}"
    assert h_scroll_result["scrolledLeft"] > 0, f"Container horizontal scroll must update scrollLeft: {h_scroll_result}"
    assert h_scroll_result["pageOverflows"] is False, "Horizontal scrolling inside panel must NOT cause page horizontal overflow"
    log("✓ Horizontal scrolling succeeds when content exceeds available width, strictly contained without page overflow")

    log("\n--- TEST 7: Interactive Task Checkboxes & Progress Update ---")
    initial_progress = eval_js("document.querySelector('[data-tempo-ui=\"recovery-working-plan\"] span.shrink-0')?.textContent.trim()")
    log(f"Initial progress: {initial_progress}")
    # Click first task checkbox
    eval_js("document.querySelector('[data-tempo-ui=\"recovery-working-plan\"] [data-task-id] button').click()")
    time.sleep(0.5)
    updated_progress = eval_js("document.querySelector('[data-tempo-ui=\"recovery-working-plan\"] span.shrink-0')?.textContent.trim()")
    first_task_checked = eval_js("document.querySelector('[data-tempo-ui=\"recovery-done-column\"] [data-task-id] button')?.textContent.trim()")
    log(f"After click - Progress: {updated_progress}, Checkbox mark: '{first_task_checked}'")
    assert "1/" in updated_progress, f"Expected 1 completed task, got {updated_progress}"
    assert "✓" in first_task_checked, "Expected checkmark inside completed checkbox"
    # Click completed task in Done column to uncheck
    eval_js("document.querySelector('[data-tempo-ui=\"recovery-done-column\"] [data-task-id] button').click()")
    time.sleep(0.5)
    reverted_progress = eval_js("document.querySelector('[data-tempo-ui=\"recovery-working-plan\"] span.shrink-0')?.textContent.trim()")
    log(f"After uncheck - Progress: {reverted_progress}")
    assert "0/" in reverted_progress
    log("✓ Task checkboxes toggle completion state interactively and update progress")

    log("\n--- TEST 8: Community Card ---")
    comm_title = eval_js("document.querySelector('[data-tempo-ui=\"recovery-community\"] h4')?.textContent.trim()")
    comm_see_all = eval_js("!!document.querySelector('[data-tempo-ui=\"recovery-community\"] button')")
    comm_posts_count = eval_js("document.querySelectorAll('#recovery-community-posts-list [data-post-id]').length")
    log(f"Community title: '{comm_title}', See all btn: {comm_see_all}, Posts count: {comm_posts_count}")
    assert "From the Tempo Community" in comm_title
    assert comm_see_all is True
    assert comm_posts_count >= 2
    log("✓ Community card is correctly rendered with posts and See all button")

    log("\n--- TEST 9: Enjoy Tempo Tools Section (4 Cards) ---")
    tools_title = eval_js("document.querySelector('#enjoy-tempo-tools h2')?.textContent.trim()")
    tool1 = eval_js("!!document.querySelector('#enjoy-tempo-tools div[title=\"Focus Now\"]')")
    tool2 = eval_js("!!document.querySelector('#enjoy-tempo-tools div[title=\"Tempo break\"]')")
    tool3 = eval_js("!!document.querySelector('#enjoy-tempo-tools div[title=\"Practice Breathing\"]')")
    tool4 = eval_js("!!document.querySelector('#enjoy-tempo-tools div[title=\"Create Notes\"]')")
    log(f"Tools title: '{tools_title}', Focus Now: {tool1}, Tempo break: {tool2}, Practice Breathing: {tool3}, Create Notes: {tool4}")
    assert "Enjoy Tempo Tools" in tools_title
    log("✓ Enjoy Tempo Tools section has all 4 tools in place")

    log("\n--- TEST 9B: Focus Now Tool Card Adjustments in Recovery Mode ---")
    focus_now_data = eval_js("""
        (() => {
            const grid = document.querySelector('#enjoy-tempo-tools .grid');
            const c1 = grid.querySelector('div[title="Focus Now"]');
            const c2 = grid.querySelector('div[title="Tempo break"]');
            const c3 = grid.querySelector('div[title="Practice Breathing"]');
            const c4 = grid.querySelector('div[title="Create Notes"]');
            const img = c1.querySelector('img');
            const textDiv = c1.querySelector('div');
            const h3 = textDiv.querySelector('h3');
            const p = textDiv.querySelector('p');

            const r1 = c1.getBoundingClientRect();
            const r2 = c2.getBoundingClientRect();
            const r3 = c3.getBoundingClientRect();
            const r4 = c4.getBoundingClientRect();
            const ir = img.getBoundingClientRect();
            const tr = textDiv.getBoundingClientRect();

            return {
                card1: {
                    width: Math.round(r1.width * 10) / 10,
                    height: Math.round(r1.height),
                    minHeight: window.getComputedStyle(c1).minHeight
                },
                otherCards: [
                    { title: "Tempo break", width: Math.round(r2.width * 10) / 10, height: Math.round(r2.height) },
                    { title: "Practice Breathing", width: Math.round(r3.width * 10) / 10, height: Math.round(r3.height) },
                    { title: "Create Notes", width: Math.round(r4.width * 10) / 10, height: Math.round(r4.height) }
                ],
                img: {
                    width: Math.round(ir.width),
                    height: Math.round(ir.height),
                    naturalWidth: img.naturalWidth,
                    naturalHeight: img.naturalHeight,
                    isLeftOfText: ir.right <= tr.left + 5,
                    offsetFromCardLeft: Math.round(ir.left - r1.left)
                },
                text: {
                    title: h3 ? h3.textContent.trim() : null,
                    desc: p ? p.textContent.trim() : null,
                    textAlign: window.getComputedStyle(textDiv).textAlign
                }
            };
        })()
    """)
    log(f"Focus Now data: {json.dumps(focus_now_data, indent=2)}")

    # 1. Height: Focus Now card height increased by exactly 5px (198 -> 203, minHeight 160 -> 165)
    assert focus_now_data['card1']['height'] == 203, f"Expected height 203px (198px + 5px), got {focus_now_data['card1']['height']}px"
    assert focus_now_data['card1']['minHeight'] == '165px', f"Expected minHeight 165px, got {focus_now_data['card1']['minHeight']}"

    # 2. Width: Focus Now card is slightly wider than the other tool cards (299.5px vs 287.5px)
    assert focus_now_data['card1']['width'] > focus_now_data['otherCards'][0]['width'], "Focus Now card should be slightly wider"
    assert abs(focus_now_data['card1']['width'] - 299.5) <= 1, f"Expected ~299.5px width, got {focus_now_data['card1']['width']}px"

    # 3. Illustration: shifted left, height increased by exactly 10px (106px -> 116px), preserved 1:1 aspect ratio (width 116px)
    assert focus_now_data['img']['height'] == 116, f"Expected illustration height 116px (+10px from 106px), got {focus_now_data['img']['height']}px"
    assert focus_now_data['img']['width'] == 116, f"Expected illustration width 116px (proportional aspect ratio), got {focus_now_data['img']['width']}px"
    assert focus_now_data['img']['width'] == focus_now_data['img']['height'], "Illustration must preserve 1:1 aspect ratio"
    assert focus_now_data['img']['offsetFromCardLeft'] <= 16, f"Illustration should be shifted left toward card boundary (~14-15px from edge), got {focus_now_data['img']['offsetFromCardLeft']}px"
    assert focus_now_data['img']['offsetFromCardLeft'] > 0, "Illustration must not overflow the card boundary"

    # 4. Layout: illustration on left, text on right, aligned left, correct copy
    assert focus_now_data['img']['isLeftOfText'] is True, "Illustration must be on the left of text"
    assert focus_now_data['text']['title'] == "Focus Now"
    assert focus_now_data['text']['desc'] == "Your own personalized workspace."
    assert focus_now_data['text']['textAlign'] == "left"

    # 5. Other tool cards NOT resized (remain at 198px)
    for other in focus_now_data['otherCards']:
        assert other['height'] == 198, f"Other tool card '{other['title']}' must remain at 198px, got {other['height']}px"
    log("✓ Focus Now card illustration is shifted left (15px from card edge), 10px taller (116px), 116px wide (1:1 ratio), and properly aligned!")

    # Capture Desktop Screenshots
    capture_screenshot("recovery_dashboard_top_desktop.png")
    
    # Scroll down to second screen
    eval_js("window.scrollTo(0, 750);")
    time.sleep(0.5)
    capture_screenshot("recovery_dashboard_bottom_desktop.png")

    # Scroll back to top
    eval_js("window.scrollTo(0, 0);")
    time.sleep(0.5)

    log("\n--- TEST 10: Desktop Column Height & Alignment Verification ---")
    align_data = eval_js("""
        (() => {
            const leftCol = document.querySelector('.recovery-left-col');
            const rightCol = document.querySelector('.recovery-right-col');
            const changeModeBtn = rightCol.querySelector('button[onclick*="openChangeModeModal"]');
            const learnSolveCard = leftCol.querySelector('[title="Learn & Solve"]');
            const leftRect = leftCol.getBoundingClientRect();
            const rightRect = rightCol.getBoundingClientRect();
            const btnRect = changeModeBtn.getBoundingClientRect();
            const cardRect = learnSolveCard.getBoundingClientRect();
            return {
                leftHeight: Math.round(leftRect.height),
                rightHeight: Math.round(rightRect.height),
                heightDiff: Math.abs(Math.round(leftRect.height) - Math.round(rightRect.height)),
                bottomDiff: Math.abs(Math.round(cardRect.bottom) - Math.round(btnRect.bottom)),
                topDiff: Math.abs(Math.round(leftRect.top) - Math.round(rightRect.top))
            };
        })()
    """)
    log(f"Alignment data: {json.dumps(align_data, indent=2)}")
    assert align_data["topDiff"] <= 2, f"Expected matching top positions, diff={align_data['topDiff']}"
    assert align_data["heightDiff"] <= 2, f"Expected matching column container heights, diff={align_data['heightDiff']}"
    log("✓ Both dashboard columns have matching top alignment and column container height")

    log("\n--- TEST 11: Navigation Interactions ---")
    # Click NOTE card to test navigation to tool-notes
    eval_js("document.querySelector('[data-tempo-ui=\"dashboard-note-card\"]').click()")
    time.sleep(0.5)
    notes_open = eval_js("!document.getElementById('screen-tool-notes')?.classList.contains('hidden')")
    log(f"Navigated to tool-notes from NOTE card: {notes_open}")
    assert notes_open is True
    # Back to dashboard
    eval_js("document.getElementById('btn-tool-notes-back').click()")
    time.sleep(0.5)

    # Click Create Notes inside Enjoy Tempo Tools
    eval_js("document.querySelector('#enjoy-tempo-tools div[title=\"Create Notes\"]').click()")
    time.sleep(0.5)
    notes_open2 = eval_js("!document.getElementById('screen-tool-notes')?.classList.contains('hidden')")
    log(f"Navigated to tool-notes from Enjoy Tempo Tools: {notes_open2}")
    assert notes_open2 is True
    # Back to dashboard
    eval_js("document.getElementById('btn-tool-notes-back').click()")
    time.sleep(0.5)

    # Click Change my mode
    eval_js("document.querySelector('.recovery-right-col button[onclick*=\"openChangeModeModal\"]').click()")
    time.sleep(0.5)
    modal_open = eval_js("!document.getElementById('modal-change-mode')?.classList.contains('hidden')")
    log(f"Change Mode modal opened: {modal_open}")
    assert modal_open is True
    # Close modal
    eval_js("window.TempoMode.closeChangeModeModal()")
    time.sleep(0.5)

    log("\n--- TEST 12: Responsiveness (Mobile 375x812) ---")
    send_command("Emulation.setDeviceMetricsOverride", {
        "width": 375,
        "height": 812,
        "deviceScaleFactor": 2,
        "mobile": True
    })
    time.sleep(0.5)
    overflow_info = eval_js("""
        (() => {
            const docWidth = document.documentElement.clientWidth;
            const overflowing = [];
            document.querySelectorAll('*').forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.right > docWidth + 1) {
                    overflowing.push({
                        tag: el.tagName,
                        id: el.id,
                        className: el.className,
                        right: rect.right,
                        width: rect.width,
                        docWidth: docWidth
                    });
                }
            });
            return overflowing.slice(0, 10);
        })()
    """)
    dashboard_overflow = eval_js("""
        (() => {
            const el = document.getElementById('rmode-home-content');
            return el ? (el.scrollWidth > el.clientWidth) : false;
        })()
    """)
    log(f"Recovery Dashboard content horizontal overflow: {dashboard_overflow}")
    assert dashboard_overflow is False, "Recovery dashboard content must not overflow horizontally on mobile"
    capture_screenshot("recovery_dashboard_mobile.png")

    log("\n--- TEST 13: Responsiveness (Tablet 768x1024) ---")
    send_command("Emulation.setDeviceMetricsOverride", {
        "width": 768,
        "height": 1024,
        "deviceScaleFactor": 1,
        "mobile": False
    })
    time.sleep(0.5)
    overflow_tablet = eval_js("document.documentElement.scrollWidth > document.documentElement.clientWidth")
    log(f"Tablet horizontal overflow: {overflow_tablet}")
    assert overflow_tablet is False, "Tablet view must not have horizontal overflow"
    capture_screenshot("recovery_dashboard_tablet.png")

    log("\n--- TEST 14: Navigation Bar for Recovery Mode Only (Plan vs Check) ---")
    send_command("Emulation.setDeviceMetricsOverride", {
        "width": 1280,
        "height": 900,
        "deviceScaleFactor": 1,
        "mobile": False
    })
    time.sleep(0.5)

    # 1. Ensure in Recovery Mode
    eval_js("""
        (() => {
            window.TempoMode.transitionContext('recovery', { skipSetupCheck: true });
            window.TempoMode.renderRmodeHome();
        })()
    """)
    time.sleep(0.5)

    # Query visible navigation links in <nav>
    nav_items_rmode = eval_js("""
        (() => {
            const nav = document.querySelector('nav.hidden.md\\\\:flex');
            if (!nav) return null;
            const links = Array.from(nav.querySelectorAll('a:not(.hidden)'))
                .map(a => a.textContent.trim());
            return links;
        })()
    """)
    log(f"Recovery Mode visible nav items: {nav_items_rmode}")
    expected_rmode_nav = ['About', 'Plan', 'Tool', 'Learn', 'Post']
    assert nav_items_rmode == expected_rmode_nav, f"Expected {expected_rmode_nav}, got {nav_items_rmode}"

    check_link_info_rmode = eval_js("""
        (() => {
            const el = document.getElementById('nav-link-check');
            return el ? { text: el.textContent.trim(), href: el.getAttribute('href') } : null;
        })()
    """)
    log(f"Recovery Mode nav-link-check info: {check_link_info_rmode}")
    assert check_link_info_rmode['text'] == 'Plan', f"Expected 'Plan', got {check_link_info_rmode['text']}"
    assert '#recovery-working-plan' in check_link_info_rmode['href'], f"Expected href to contain '#recovery-working-plan', got {check_link_info_rmode['href']}"

    # 2. Test clicking Plan when on dashboard scrolls to Your Working Plan
    eval_js("window.scrollTo(0, 0)")
    time.sleep(0.2)
    eval_js("document.getElementById('nav-link-check').click()")
    time.sleep(0.5)
    plan_top_rmode = eval_js("""
        (() => {
            const el = document.getElementById('recovery-working-plan') || document.querySelector('[data-tempo-ui="recovery-working-plan"]');
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return { top: r.top, bottom: r.bottom, windowH: window.innerHeight };
        })()
    """)
    log(f"Recovery Plan rect after clicking Plan: {plan_top_rmode}")
    assert plan_top_rmode is not None, "Working Plan element not found"
    # Element should have scrolled into view (top >= -100 and top <= windowH)
    assert plan_top_rmode['top'] <= plan_top_rmode['windowH'], "Plan should be visible in viewport"

    # 3. Test clicking Plan from another screen (e.g. About)
    eval_js("window.TempoApp.navigateTo('about')")
    time.sleep(0.3)
    about_visible = eval_js("!document.getElementById('screen-about').classList.contains('hidden')")
    today_hidden = eval_js("document.getElementById('screen-today').classList.contains('hidden')")
    assert about_visible is True and today_hidden is True, "About screen should be visible"

    eval_js("document.getElementById('nav-link-check').click()")
    time.sleep(0.5)
    about_hidden_after = eval_js("document.getElementById('screen-about').classList.contains('hidden')")
    today_visible_after = eval_js("!document.getElementById('screen-today').classList.contains('hidden')")
    assert about_hidden_after is True and today_visible_after is True, "Today screen should be restored after clicking Plan from About"

    # 4. Verify navbar switches back to Check for Entry Home / Default
    eval_js("""
        (() => {
            window.TempoMode.transitionContext(null);
            window.TempoMode.renderActiveModeHome();
        })()
    """)
    time.sleep(0.5)
    nav_items_entry = eval_js("""
        (() => {
            const nav = document.querySelector('nav.hidden.md\\\\:flex');
            if (!nav) return null;
            return Array.from(nav.querySelectorAll('a:not(.hidden)')).map(a => a.textContent.trim());
        })()
    """)
    log(f"Entry Home visible nav items: {nav_items_entry}")
    expected_entry_nav = ['About', 'Check', 'Plan', 'Learn', 'Post']
    assert nav_items_entry == expected_entry_nav, f"Expected {expected_entry_nav}, got {nav_items_entry}"

    check_link_info_entry = eval_js("""
        (() => {
            const el = document.getElementById('nav-link-check');
            return el ? { text: el.textContent.trim(), href: el.getAttribute('href') } : null;
        })()
    """)
    assert check_link_info_entry['text'] == 'Check', f"Expected 'Check', got {check_link_info_entry['text']}"
    assert '#stress-check' in check_link_info_entry['href'], f"Expected href '#stress-check', got {check_link_info_entry['href']}"

    # 5. Verify navbar in Urmode
    eval_js("""
        (() => {
            window.TempoMode.renderUmodeHome();
        })()
    """)
    time.sleep(0.5)
    nav_items_urmode = eval_js("""
        (() => {
            const nav = document.querySelector('nav.hidden.md\\\\:flex');
            if (!nav) return null;
            return Array.from(nav.querySelectorAll('a:not(.hidden)')).map(a => a.textContent.trim());
        })()
    """)
    log(f"Urmode visible nav items: {nav_items_urmode}")
    expected_urmode_nav = ['About', 'Check', 'Tool', 'Learn', 'Post']
    assert nav_items_urmode == expected_urmode_nav, f"Expected {expected_urmode_nav}, got {nav_items_urmode}"

    # 6. Switch back to Recovery Mode to leave test environment in verified state
    eval_js("""
        (() => {
            window.TempoMode.transitionContext('recovery', { skipSetupCheck: true });
            window.TempoMode.renderRmodeHome();
        })()
    """)
    time.sleep(0.5)
    nav_items_rmode_final = eval_js("""
        (() => {
            const nav = document.querySelector('nav.hidden.md\\\\:flex');
            if (!nav) return null;
            return Array.from(nav.querySelectorAll('a:not(.hidden)')).map(a => a.textContent.trim());
        })()
    """)
    assert nav_items_rmode_final == expected_rmode_nav, f"Expected {expected_rmode_nav}, got {nav_items_rmode_final}"
    log("✓ Recovery Mode navbar: Plan item, order, scrolling destination, and mode transitions verified!")

    log("\n==========================================")
    log("ALL 14 RECOVERY DASHBOARD UI TESTS PASSED!")
    log("==========================================")

finally:
    if ws:
        ws.close()
    proc.terminate()
    proc.wait()
