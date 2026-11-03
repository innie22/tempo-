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

user_data_dir = tempfile.mkdtemp(prefix="tempo_inspect_grounded_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9349

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

    # Switch to Rmode
    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(1.0)

    # Click Quick Relief card to open Grounded Pause modal
    eval_js("""
        (() => {
            const card = document.querySelector('.recovery-card-quick-relief');
            if (card) card.click();
            else if (window.TempoStressRelief) window.TempoStressRelief.openModal();
        })()
    """)
    time.sleep(1.0)

    # Inspect modal
    modal_info = eval_js("""
        (() => {
            const modal = document.getElementById('modal-quick-stress-relief');
            if (!modal) return null;
            const isVisible = !modal.classList.contains('hidden');
            const card = modal.querySelector('.tempo-card');
            const cardCs = card ? window.getComputedStyle(card) : null;
            const topHeader = modal.querySelector('.border-b');
            const topBadge = topHeader ? topHeader.querySelector('span') : null;
            const content = document.getElementById('stress-relief-content-body');
            const subtitle = content ? content.querySelector('span') : null;
            const h3 = content ? content.querySelector('h3') : null;
            const desc = content ? content.querySelector('p') : null;
            const filterBtns = Array.from(content.querySelectorAll('.flex.flex-wrap.items-center.gap-2 button')).map(b => ({
                text: b.textContent.trim(),
                className: b.className
            }));
            const methodCards = Array.from(content.querySelectorAll('.grid > div')).map(c => {
                const title = c.querySelector('h4');
                const duration = c.querySelector('.rounded-full');
                const emoji = c.querySelector('.text-lg');
                const summary = c.querySelector('p');
                const link = c.querySelector('.pt-2 span');
                return {
                    title: title ? title.textContent.trim() : null,
                    duration: duration ? duration.textContent.trim() : null,
                    emoji: emoji ? emoji.textContent.trim() : null,
                    summary: summary ? summary.textContent.trim() : null,
                    linkText: link ? link.textContent.trim() : null
                };
            });

            return {
                isVisible: isVisible,
                topBadge: topBadge ? topBadge.textContent.trim() : null,
                subtitle: subtitle ? subtitle.textContent.trim() : null,
                h3: h3 ? h3.textContent.trim() : null,
                desc: desc ? desc.textContent.trim() : null,
                filterBtns: filterBtns,
                methodCardsCount: methodCards.length,
                methodCards: methodCards
            };
        })()
    """)
    print("Modal inspection:", json.dumps(modal_info, indent=2))

    # Take screenshot of current modal
    ss = send_cmd("Page.captureScreenshot", {"format": "png"})
    with open(os.path.join(artifact_dir, "grounded_pause_modal_before.png"), "wb") as f:
        f.write(base64.b64decode(ss["data"]))
    print("Captured grounded_pause_modal_before.png")

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
