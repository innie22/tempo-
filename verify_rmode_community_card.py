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

user_data_dir = tempfile.mkdtemp(prefix="tempo_verify_rmode_comm_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9347

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

def take_element_screenshot(selector, file_name):
    # Scroll into view
    eval_js(f"""
        (() => {{
            const el = document.querySelector('{selector}');
            if (el) el.scrollIntoView({{ behavior: 'instant', block: 'center' }});
        }})()
    """)
    time.sleep(0.4)
    res = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, file_name), "wb") as f:
        f.write(base64.b64decode(res["data"]))
    print(f"Captured screenshot: {file_name}")

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

    # 1. Switch to Rmode (Recovery)
    print("\n--- Test 1: Switch to Recovery Mode ---")
    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(1.5)
    mode = eval_js("window.TempoMode.getMode()")
    assert mode == 'recovery', f"Expected recovery, got {mode}"
    print("Mode is recovery.")

    # 2. Inspect Rmode Community Card
    print("\n--- Test 2: Rmode Community Card Visual Properties ---")
    card_info = eval_js("""
        (() => {
            const card = document.querySelector('[data-tempo-ui="recovery-community"]');
            if (!card) return null;
            const cs = window.getComputedStyle(card);
            const rect = card.getBoundingClientRect();
            const iconImg = card.querySelector('img[alt="Community"]');
            const title = card.querySelector('h3');
            const titleCs = title ? window.getComputedStyle(title) : null;
            const seeAllBtn = document.getElementById('btn-see-all-posts-recovery');
            const btnCs = seeAllBtn ? window.getComputedStyle(seeAllBtn) : null;
            const postCards = Array.from(card.querySelectorAll('#recovery-community-posts-list > div')).map(p => {
                const pCs = window.getComputedStyle(p);
                const authorEl = p.querySelector('h4');
                const contentEl = p.querySelector('p');
                const tags = Array.from(p.querySelectorAll('span[class*="rounded-full"]')).map(t => t.textContent.trim());
                const thumbs = Array.from(p.querySelectorAll('.grid img')).map(img => img.src);
                const bookmarkBtn = p.querySelector('button[title*="Bookmark"], button[aria-label*="Bookmark"]');
                return {
                    author: authorEl ? authorEl.textContent.trim() : null,
                    content: contentEl ? contentEl.textContent.trim() : null,
                    tags: tags,
                    thumbsCount: thumbs.length,
                    hasBookmark: !!bookmarkBtn,
                    bgColor: pCs.backgroundColor,
                    borderRadius: pCs.borderRadius,
                    border: `${pCs.borderWidth} ${pCs.borderStyle} ${pCs.borderColor}`
                };
            });

            return {
                found: true,
                bgColor: cs.backgroundColor,
                border: `${cs.borderWidth} ${cs.borderStyle} ${cs.borderColor}`,
                borderRadius: cs.borderRadius,
                padding: `${cs.paddingTop} ${cs.paddingRight} ${cs.paddingBottom} ${cs.paddingLeft}`,
                width: rect.width,
                height: rect.height,
                hasCommunityIcon: !!iconImg,
                title: title ? title.textContent.trim() : null,
                titleColor: titleCs ? titleCs.color : null,
                titleFontSize: titleCs ? titleCs.fontSize : null,
                titleFontWeight: titleCs ? titleCs.fontWeight : null,
                hasSeeAllBtn: !!seeAllBtn,
                btnBg: btnCs ? btnCs.backgroundColor : null,
                btnColor: btnCs ? btnCs.color : null,
                postCount: postCards.length,
                posts: postCards
            };
        })()
    """)
    print("Rmode Community Card data:", json.dumps(card_info, indent=2))
    assert card_info['found'] is True, "Rmode Community card not found!"
    assert card_info['bgColor'] == 'rgb(254, 250, 244)', f"Expected #FEFAF4, got {card_info['bgColor']}"
    assert card_info['borderRadius'] == '32px', f"Expected 32px, got {card_info['borderRadius']}"
    assert card_info['padding'] == '20px 20px 20px 20px', f"Expected 20px padding, got {card_info['padding']}"
    assert card_info['hasCommunityIcon'] is True, "Missing circular community icon!"
    assert card_info['title'] == 'From the Tempo Community', f"Unexpected title {card_info['title']}"
    assert card_info['titleFontSize'] == '18px', f"Expected 18px title font size, got {card_info['titleFontSize']}"
    assert card_info['hasSeeAllBtn'] is True, "Missing 'See all →' button!"
    assert card_info['postCount'] == 2, f"Expected 2 post cards, got {card_info['postCount']}"

    # Check post 1
    p1 = card_info['posts'][0]
    assert p1['author'] == 'FPT Bá khí', f"Expected FPT Bá khí, got {p1['author']}"
    assert 'mental health' in p1['tags'], "Missing 'mental health' tag in post 1"
    assert p1['hasBookmark'] is True, "Missing bookmark button in post 1"
    assert p1['bgColor'] == 'rgb(246, 240, 235)', f"Expected #F6F0EB post bg, got {p1['bgColor']}"
    assert p1['borderRadius'] == '24px', f"Expected 24px post radius, got {p1['borderRadius']}"

    # Check post 2 (with thumbnails)
    p2 = card_info['posts'][1]
    assert p2['author'] == 'Temposocute', f"Expected Temposocute, got {p2['author']}"
    assert p2['thumbsCount'] == 4, f"Expected 4 thumbnail attachments in post 2, got {p2['thumbsCount']}"
    assert p2['bgColor'] == 'rgb(246, 240, 235)', f"Expected #F6F0EB post bg, got {p2['bgColor']}"

    # Take screenshot of Rmode community card on desktop
    take_element_screenshot('[data-tempo-ui="recovery-community"]', "rmode_community_card_desktop.png")
    take_element_screenshot('.recovery-plan-comm-grid', "rmode_plan_and_community_row.png")

    # 3. Test See all → navigation
    print("\n--- Test 3: 'See all →' Button Navigation ---")
    eval_js("""
        (() => {
            const btn = document.getElementById('btn-see-all-posts-recovery');
            if (btn) btn.click();
        })()
    """)
    time.sleep(1.0)
    is_comm_visible = eval_js("!document.getElementById('view-community')?.classList.contains('hidden')")
    print(f"Community page visible: {is_comm_visible}")
    assert is_comm_visible is True, "Failed to navigate to Community page!"
    take_element_screenshot('#view-community', "rmode_community_see_all_navigated.png")

    # Return to recovery mode
    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(1.0)

    # 4. Test Post Card Click Navigation
    print("\n--- Test 4: Post Card Click Navigation ---")
    eval_js("""
        (() => {
            const postCard = document.querySelector('#recovery-community-posts-list > div');
            if (postCard) postCard.click();
        })()
    """)
    time.sleep(1.0)
    is_comm_visible2 = eval_js("!document.getElementById('view-community')?.classList.contains('hidden')")
    assert is_comm_visible2 is True, "Failed to navigate to Community page on card click!"
    print("Post card click successfully navigated to Community posts.")

    # Return to recovery mode
    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(1.0)

    # 5. Test Like & Bookmark interaction inside Rmode Community card
    print("\n--- Test 5: Like Interaction ---")
    likes_before = eval_js("""
        (() => {
            const likeSpan = document.querySelector('#recovery-community-posts-list > div span.cursor-pointer');
            return likeSpan ? parseInt(likeSpan.textContent.replace('♡', '').trim(), 10) : null;
        })()
    """)
    print("Likes before:", likes_before)
    eval_js("""
        (() => {
            const likeSpan = document.querySelector('#recovery-community-posts-list > div span.cursor-pointer');
            if (likeSpan) likeSpan.click();
        })()
    """)
    time.sleep(0.5)
    likes_after = eval_js("""
        (() => {
            const likeSpan = document.querySelector('#recovery-community-posts-list > div span.cursor-pointer');
            return likeSpan ? parseInt(likeSpan.textContent.replace('♡', '').trim(), 10) : null;
        })()
    """)
    print("Likes after:", likes_after)
    assert likes_after == likes_before + 1, f"Expected {likes_before + 1}, got {likes_after}"

    # 6. Test Responsive Layout: Mobile (375px)
    print("\n--- Test 6: Mobile (375px) Responsive Layout ---")
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 375,
        "height": 812,
        "deviceScaleFactor": 2,
        "mobile": True
    })
    time.sleep(0.5)
    mobile_card_rect = eval_js("""
        (() => {
            const el = document.querySelector('[data-tempo-ui="recovery-community"]');
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return { width: r.width, height: r.height };
        })()
    """)
    print("Mobile card rect:", mobile_card_rect)
    assert mobile_card_rect['width'] > 300, "Mobile card width issue!"
    take_element_screenshot('[data-tempo-ui="recovery-community"]', "rmode_community_card_mobile_375.png")

    # Reset emulation to desktop
    send_cmd("Emulation.clearDeviceMetricsOverride")
    time.sleep(0.5)

    # 7. Untouched Verification: URmode Community Card
    print("\n--- Test 7: Untouched URmode Community Card ---")
    eval_js("window.TempoMode.setMode('emergency');")
    time.sleep(1.2)
    ur_card = eval_js("""
        (() => {
            const card = document.querySelector('[data-tempo-ui="urgent-posts"]');
            if (!card) return null;
            const cs = window.getComputedStyle(card);
            const posts = card.querySelectorAll('#urgent-community-posts-list > div').length;
            return {
                found: true,
                bgColor: cs.backgroundColor,
                borderRadius: cs.borderRadius,
                postCount: posts
            };
        })()
    """)
    print("URmode card check:", json.dumps(ur_card, indent=2))
    assert ur_card['found'] is True, "URmode community card missing!"
    assert ur_card['postCount'] == 2, "URmode post count changed!"
    take_element_screenshot('[data-tempo-ui="urgent-posts"]', "urmode_community_card_verified_untouched.png")

    # 8. Rmode Working Plan Task Modal Regression Check
    print("\n--- Test 8: Rmode Working Plan Regression Check ---")
    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(1.0)
    eval_js("window.TempoMode.openRmodeTaskDetailModal('task-marketing-research');")
    time.sleep(0.5)
    rmode_modal_open = eval_js("!!document.getElementById('rmode-task-detail-modal')")
    assert rmode_modal_open is True, "Rmode task detail modal failed to open!"
    eval_js("window.TempoMode.closeRmodeTaskDetailModal();")
    print("Rmode task detail modal opens and closes normally.")

    print("\n==================================================")
    print("ALL TESTS PASSED! RMODE COMMUNITY CARD PERFECT!")
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
