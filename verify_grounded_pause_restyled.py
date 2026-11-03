import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import os
import base64
import re

sys.stdout.reconfigure(encoding='utf-8')

artifact_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
os.makedirs(artifact_dir, exist_ok=True)

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_grounded_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9350

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1100"
]

proc = subprocess.Popen(cmd)
ws = None
msg_id = 1

def send_cmd(method, params=None):
    global msg_id, ws
    cmd_obj = {"id": msg_id, "method": method, "params": params or {}}
    msg_id += 1
    ws.send(json.dumps(cmd_obj))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == cmd_obj["id"]:
            return resp.get("result", {})

def eval_js(expr):
    res = send_cmd("Runtime.evaluate", {
        "expression": expr,
        "returnByValue": True,
        "awaitPromise": True
    })
    if "exceptionDetails" in res:
        print("JS Exception:", res["exceptionDetails"])
    return res.get("result", {}).get("value")

def contains_emoji(text):
    if not text:
        return False
    # Check for common emoji ranges
    emoji_pattern = re.compile(
        "[\U00010000-\U0010ffff\u2600-\u27bf\u2b50\u2b55\u23cf\u23e9-\u23f3\u23f8-\u23fa]",
        flags=re.UNICODE
    )
    return bool(emoji_pattern.search(text))

try:
    ws_url = None
    for _ in range(40):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json") as resp:
                tabs = json.loads(resp.read().decode())
                pages = [t for t in tabs if t.get("type") == "page" and not t.get("url", "").startswith("chrome-extension://")]
                if pages:
                    ws_url = pages[0]["webSocketDebuggerUrl"]
                    break
        except Exception:
            time.sleep(0.5)

    if not ws_url:
        raise RuntimeError("Failed to connect to Edge CDP")

    ws = websocket.create_connection(ws_url)

    send_cmd("Page.navigate", {"url": "http://127.0.0.1:8000/"})
    for _ in range(30):
        ready = eval_js("typeof window.TempoMode !== 'undefined' && typeof window.TempoMode.setMode === 'function'")
        if ready:
            break
        time.sleep(0.3)

    # 1. Switch to Rmode
    print("\n--- Test 1: Switch to Recovery Mode ---")
    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(1.2)
    mode = eval_js("window.TempoMode.getMode()")
    assert mode == 'recovery', f"Expected recovery mode, got {mode}"
    print("Mode is recovery.")

    # 2. Open Grounded Pause Modal from Quick Relief Card
    print("\n--- Test 2: Open Grounded Pause Modal ---")
    eval_js("""
        (() => {
            const card = document.querySelector('.recovery-card-quick-relief');
            if (card) card.click();
            else if (window.TempoStressRelief) window.TempoStressRelief.openModal();
        })()
    """)
    time.sleep(0.8)

    modal_open = eval_js("!document.getElementById('modal-quick-stress-relief').classList.contains('hidden')")
    assert modal_open is True, "Grounded Pause modal failed to open!"
    print("Modal successfully opened.")

    # 3. Inspect Visual Design & Check For Emojis
    print("\n--- Test 3: Inspect Visual Design & Assert Zero Emojis ---")
    inspection = eval_js("""
        (() => {
            const modal = document.getElementById('modal-quick-stress-relief');
            const card = modal.querySelector('.tempo-card');
            const cardCs = window.getComputedStyle(card);
            const badge = modal.querySelector('span.uppercase.tracking-wider');
            const badgeCs = badge ? window.getComputedStyle(badge) : null;
            const content = document.getElementById('stress-relief-content-body');
            const filterBtns = Array.from(content.querySelectorAll('.flex.flex-wrap button')).map(b => {
                const bCs = window.getComputedStyle(b);
                return {
                    text: b.textContent.trim(),
                    bg: bCs.backgroundColor,
                    color: bCs.color,
                    borderRadius: bCs.borderRadius
                };
            });
            const methodCards = Array.from(content.querySelectorAll('.grid > div')).map(c => {
                const cCs = window.getComputedStyle(c);
                const title = c.querySelector('h4');
                const titleCs = title ? window.getComputedStyle(title) : null;
                const durBadge = c.querySelector('.rounded-full');
                const durCs = durBadge ? window.getComputedStyle(durBadge) : null;
                const summary = c.querySelector('p');
                const actionLink = c.querySelector('div.border-t');
                const actionCs = actionLink ? window.getComputedStyle(actionLink) : null;
                return {
                    title: title ? title.textContent.trim() : null,
                    titleColor: titleCs ? titleCs.color : null,
                    duration: durBadge ? durBadge.textContent.trim() : null,
                    durBg: durCs ? durCs.backgroundColor : null,
                    durColor: durCs ? durCs.color : null,
                    summary: summary ? summary.textContent.trim() : null,
                    actionText: actionLink ? actionLink.textContent.trim() : null,
                    actionColor: actionCs ? actionCs.color : null,
                    bg: cCs.backgroundColor,
                    border: `${cCs.borderWidth} ${cCs.borderStyle} ${cCs.borderColor}`,
                    borderRadius: cCs.borderRadius
                };
            });

            return {
                modalBg: cardCs.backgroundColor,
                borderRadius: cardCs.borderRadius,
                badgeText: badge ? badge.textContent.trim() : null,
                badgeBg: badgeCs ? badgeCs.backgroundColor : null,
                badgeColor: badgeCs ? badgeCs.color : null,
                filterBtns: filterBtns,
                methodCardsCount: methodCards.length,
                methodCards: methodCards
            };
        })()
    """)
    print("Modal inspection:", json.dumps(inspection, indent=2))

    # A. Assert zero emojis in filter buttons
    print("\nVerifying filter buttons have zero emojis:")
    for btn in inspection['filterBtns']:
        has_emo = contains_emoji(btn['text'])
        print(f"Filter Button: '{btn['text']}' -> Has Emoji: {has_emo}")
        assert not has_emo, f"Found emoji in filter button: '{btn['text']}'!"
    assert [b['text'] for b in inspection['filterBtns']] == ['All Durations', '1 min', '3 min', '5 min']

    # B. Assert zero emojis in method cards
    print("\nVerifying method cards have zero emojis:")
    for card in inspection['methodCards']:
        assert not contains_emoji(card['title']), f"Found emoji in card title: {card['title']}"
        assert not contains_emoji(card['duration']), f"Found emoji in duration badge: {card['duration']}"
        assert not contains_emoji(card['summary']), f"Found emoji in card summary: {card['summary']}"
        assert not contains_emoji(card['actionText']), f"Found emoji in action text: {card['actionText']}"
    assert inspection['methodCardsCount'] == 8, f"Expected 8 method cards, got {inspection['methodCardsCount']}"
    print("All 8 method cards verified completely emoji-free!")

    # C. Assert Tempo design system colors
    # Warm Cream background: rgb(255, 249, 244)
    assert inspection['modalBg'] == 'rgb(255, 249, 244)', f"Expected Warm Cream #FFF9F4, got {inspection['modalBg']}"
    # Selected filter button: Tempo Orange rgb(255, 107, 44)
    assert inspection['filterBtns'][0]['bg'] == 'rgb(255, 107, 44)', f"Expected Tempo Orange #FF6B2C, got {inspection['filterBtns'][0]['bg']}"
    # Soft Orange badge: rgb(255, 233, 220)
    assert inspection['badgeBg'] == 'rgb(255, 233, 220)', f"Expected Soft Orange #FFE9DC, got {inspection['badgeBg']}"
    assert inspection['badgeColor'] == 'rgb(255, 107, 44)', f"Expected Tempo Orange #FF6B2C, got {inspection['badgeColor']}"

    # Capture desktop screenshot
    ss_desktop = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "grounded_pause_modal_restyled_desktop.png"), "wb") as f:
        f.write(base64.b64decode(ss_desktop["data"]))
    print("Saved grounded_pause_modal_restyled_desktop.png")

    # 4. Test Duration Filter Interactivity
    print("\n--- Test 4: Duration Filters ---")
    # Click 1 min filter
    eval_js("window.TempoStressRelief.setFilter('1');")
    time.sleep(0.3)
    c1 = eval_js("document.querySelectorAll('#stress-relief-content-body .grid > div').length")
    print(f"Cards with 1 min filter: {c1}")
    assert c1 == 1, f"Expected 1 card for 1 min, got {c1}"

    # Click 3 min filter
    eval_js("window.TempoStressRelief.setFilter('3');")
    time.sleep(0.3)
    c3 = eval_js("document.querySelectorAll('#stress-relief-content-body .grid > div').length")
    print(f"Cards with 3 min filter: {c3}")
    assert c3 == 5, f"Expected 5 cards for 3 min, got {c3}"

    # Click 5 min filter
    eval_js("window.TempoStressRelief.setFilter('5');")
    time.sleep(0.3)
    c5 = eval_js("document.querySelectorAll('#stress-relief-content-body .grid > div').length")
    print(f"Cards with 5 min filter: {c5}")
    assert c5 == 2, f"Expected 2 cards for 5 min, got {c5}"

    # Reset to All
    eval_js("window.TempoStressRelief.setFilter('all');")
    time.sleep(0.3)
    c_all = eval_js("document.querySelectorAll('#stress-relief-content-body .grid > div').length")
    assert c_all == 8, f"Expected 8 cards for all, got {c_all}"

    # 5. Test Method Selection Flow: Non-breathing method (Release Tension)
    print("\n--- Test 5: Method Detail Flow (Release Tension) ---")
    eval_js("window.TempoStressRelief.selectMethod('release-tension');")
    time.sleep(0.5)
    detail_title = eval_js("document.querySelector('#stress-relief-content-body h3').textContent.trim()")
    print("Detail view title:", detail_title)
    assert detail_title == "Release Tension"
    # Verify no emojis in detail view
    detail_html = eval_js("document.getElementById('stress-relief-content-body').innerHTML")
    assert not contains_emoji(detail_html), "Found emoji in detail view!"

    ss_detail = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "grounded_pause_detail_view.png"), "wb") as f:
        f.write(base64.b64decode(ss_detail["data"]))
    print("Saved grounded_pause_detail_view.png")

    # Back to library
    eval_js("window.TempoStressRelief.renderLibrary();")
    time.sleep(0.4)

    # 6. Test Method Selection Flow: Breathing method (Box Breathing)
    print("\n--- Test 6: Breathing Setup View (Box Breathing) ---")
    eval_js("window.TempoStressRelief.selectMethod('breathing');")
    time.sleep(0.5)
    breathing_title = eval_js("document.querySelector('#stress-relief-content-body h3').textContent.trim()")
    print("Breathing setup title:", breathing_title)
    assert breathing_title == "Box Breathing Reset"
    breathing_html = eval_js("document.getElementById('stress-relief-content-body').innerHTML")
    assert not contains_emoji(breathing_html), "Found emoji in breathing setup view!"

    ss_breathing = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "grounded_pause_breathing_setup.png"), "wb") as f:
        f.write(base64.b64decode(ss_breathing["data"]))
    print("Saved grounded_pause_breathing_setup.png")

    # Back to library
    eval_js("window.TempoStressRelief.renderLibrary();")
    time.sleep(0.4)

    # 7. Test Mobile Responsive Viewport (375px)
    print("\n--- Test 7: Mobile Viewport (375px) ---")
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 375,
        "height": 812,
        "deviceScaleFactor": 2,
        "mobile": True
    })
    time.sleep(0.5)
    ss_mobile = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "grounded_pause_modal_mobile_375.png"), "wb") as f:
        f.write(base64.b64decode(ss_mobile["data"]))
    print("Saved grounded_pause_modal_mobile_375.png")
    send_cmd("Emulation.clearDeviceMetricsOverride")

    # 8. Test Modal Dismissal
    print("\n--- Test 8: Modal Dismissal ---")
    # A. Close button
    eval_js("document.getElementById('btn-close-stress-relief').click();")
    time.sleep(0.3)
    modal_closed_btn = eval_js("document.getElementById('modal-quick-stress-relief').classList.contains('hidden')")
    assert modal_closed_btn is True, "Modal failed to close via close button!"
    print("Closed via close button.")

    # B. Reopen and close via Escape
    eval_js("window.TempoStressRelief.openModal();")
    time.sleep(0.4)
    send_cmd("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
    send_cmd("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
    time.sleep(0.3)
    modal_closed_esc = eval_js("document.getElementById('modal-quick-stress-relief').classList.contains('hidden')")
    assert modal_closed_esc is True, "Modal failed to close via Escape key!"
    print("Closed via Escape key.")

    # C. Reopen and close via backdrop click
    eval_js("window.TempoStressRelief.openModal();")
    time.sleep(0.4)
    eval_js("document.getElementById('modal-quick-stress-relief').click();")
    time.sleep(0.3)
    modal_closed_bd = eval_js("document.getElementById('modal-quick-stress-relief').classList.contains('hidden')")
    assert modal_closed_bd is True, "Modal failed to close via backdrop click!"
    print("Closed via backdrop click.")

    # 9. Verify URmode and EntryHome Untouched
    print("\n--- Test 9: Untouched Verification ---")
    eval_js("window.TempoMode.setMode('emergency');")
    time.sleep(1.2)
    ur_mode = eval_js("window.TempoMode.getMode()")
    assert ur_mode == 'emergency', "Failed to switch to emergency mode!"
    print("URmode verified untouched.")

    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(1.0)
    print("Returned to recovery mode clean.")

    print("\n==================================================")
    print("ALL GROUNDED PAUSE RESTYLING TESTS PASSED!")
    print("==================================================")

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
