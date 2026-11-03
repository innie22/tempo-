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
user_data_dir = tempfile.mkdtemp(prefix="tempo_inspect_comm_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9346

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,1200"
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

    # 1. URmode inspection
    eval_js("window.TempoMode.setMode('emergency');")
    time.sleep(1.5)

    urmode_comm = eval_js("""
        (() => {
            const el = document.querySelector('[data-tempo-ui="urgent-posts"]');
            if (!el) return null;
            const rect = el.getBoundingClientRect();
            const cs = window.getComputedStyle(el);
            const header = el.querySelector('.flex.items-center.justify-between');
            const hRect = header ? header.getBoundingClientRect() : null;
            const hCs = header ? window.getComputedStyle(header) : null;
            const titleEl = el.querySelector('h3');
            const titleCs = titleEl ? window.getComputedStyle(titleEl) : null;
            const btnEl = el.querySelector('button');
            const btnCs = btnEl ? window.getComputedStyle(btnEl) : null;
            const postCards = Array.from(el.querySelectorAll('#urgent-community-posts-list > div')).map(p => {
                const pCs = window.getComputedStyle(p);
                const pRect = p.getBoundingClientRect();
                return {
                    tag: p.tagName,
                    classes: p.className,
                    width: pRect.width,
                    height: pRect.height,
                    bgColor: pCs.backgroundColor,
                    border: `${pCs.borderWidth} ${pCs.borderStyle} ${pCs.borderColor}`,
                    borderRadius: pCs.borderRadius,
                    padding: `${pCs.paddingTop} ${pCs.paddingRight} ${pCs.paddingBottom} ${pCs.paddingLeft}`,
                    htmlSnippet: p.outerHTML.slice(0, 300)
                };
            });

            return {
                classes: el.className,
                styleAttr: el.getAttribute('style'),
                width: rect.width,
                height: rect.height,
                bgColor: cs.backgroundColor,
                border: `${cs.borderWidth} ${cs.borderStyle} ${cs.borderColor}`,
                borderRadius: cs.borderRadius,
                padding: `${cs.paddingTop} ${cs.paddingRight} ${cs.paddingBottom} ${cs.paddingLeft}`,
                title: titleEl ? titleEl.textContent.trim() : null,
                titleFont: titleCs ? `${titleCs.fontSize} / ${titleCs.lineHeight} ${titleCs.fontWeight} ${titleCs.color}` : null,
                btnText: btnEl ? btnEl.textContent.trim() : null,
                btnStyles: btnCs ? {
                    bg: btnCs.backgroundColor,
                    color: btnCs.color,
                    padding: `${btnCs.paddingTop} ${btnCs.paddingRight} ${btnCs.paddingBottom} ${btnCs.paddingLeft}`,
                    borderRadius: btnCs.borderRadius,
                    fontSize: btnCs.fontSize,
                    fontWeight: btnCs.fontWeight
                } : null,
                postCardsCount: postCards.length,
                postCards: postCards
            };
        })()
    """)
    print("URmode Community Card Inspection:")
    print(json.dumps(urmode_comm, indent=2))

    # Take screenshot of URmode community card
    ss_urmode = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "urmode_comm_card_current.png"), "wb") as f:
        f.write(base64.b64decode(ss_urmode["data"]))

    # 2. Rmode inspection
    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(1.5)

    rmode_comm = eval_js("""
        (() => {
            const el = document.querySelector('[data-tempo-ui="recovery-community"]');
            if (!el) return null;
            const rect = el.getBoundingClientRect();
            const cs = window.getComputedStyle(el);
            const parent = el.parentElement;
            const pRect = parent ? parent.getBoundingClientRect() : null;
            const titleEl = el.querySelector('h4, h3');
            const titleCs = titleEl ? window.getComputedStyle(titleEl) : null;
            const btnEl = el.querySelector('button');
            const btnCs = btnEl ? window.getComputedStyle(btnEl) : null;
            const postCards = Array.from(el.querySelectorAll('#recovery-community-posts-list > div')).map(p => {
                const pCs = window.getComputedStyle(p);
                const pRect = p.getBoundingClientRect();
                return {
                    tag: p.tagName,
                    classes: p.className,
                    width: pRect.width,
                    height: pRect.height,
                    bgColor: pCs.backgroundColor,
                    border: `${pCs.borderWidth} ${pCs.borderStyle} ${pCs.borderColor}`,
                    borderRadius: pCs.borderRadius,
                    padding: `${pCs.paddingTop} ${pCs.paddingRight} ${pCs.paddingBottom} ${pCs.paddingLeft}`,
                    htmlSnippet: p.outerHTML.slice(0, 300)
                };
            });

            return {
                classes: el.className,
                styleAttr: el.getAttribute('style'),
                width: rect.width,
                height: rect.height,
                parentWidth: pRect ? pRect.width : null,
                bgColor: cs.backgroundColor,
                border: `${cs.borderWidth} ${cs.borderStyle} ${cs.borderColor}`,
                borderRadius: cs.borderRadius,
                padding: `${cs.paddingTop} ${cs.paddingRight} ${cs.paddingBottom} ${cs.paddingLeft}`,
                title: titleEl ? titleEl.textContent.trim() : null,
                titleFont: titleCs ? `${titleCs.fontSize} / ${titleCs.lineHeight} ${titleCs.fontWeight} ${titleCs.color}` : null,
                btnText: btnEl ? btnEl.textContent.trim() : null,
                btnStyles: btnCs ? {
                    bg: btnCs.backgroundColor,
                    color: btnCs.color,
                    padding: `${btnCs.paddingTop} ${btnCs.paddingRight} ${btnCs.paddingBottom} ${btnCs.paddingLeft}`,
                    borderRadius: btnCs.borderRadius,
                    fontSize: btnCs.fontSize,
                    fontWeight: btnCs.fontWeight
                } : null,
                postCardsCount: postCards.length,
                postCards: postCards
            };
        })()
    """)
    print("\nRmode Community Card Inspection:")
    print(json.dumps(rmode_comm, indent=2))

    ss_rmode = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "rmode_comm_card_current.png"), "wb") as f:
        f.write(base64.b64decode(ss_rmode["data"]))

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
