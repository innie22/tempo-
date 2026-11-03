import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys
import base64
import os

sys.stdout.reconfigure(encoding='utf-8')

artifact_dir = r"C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6"
user_data_dir = tempfile.mkdtemp(prefix="tempo_test_rmode_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9282

cmd = [
    edge_path,
    "--headless=new",
    f"--remote-debugging-port={port}",
    "--remote-allow-origins=*",
    f"--user-data-dir={user_data_dir}",
    "--disable-gpu",
    "--no-first-run",
    "--window-size=1440,900",
    "http://localhost:8000/"
]

proc = subprocess.Popen(cmd)
ws = None
msg_id = 1

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

    ws = websocket.create_connection(ws_url)

    def send_cmd(method, params=None):
        global msg_id
        cid = msg_id
        msg_id += 1
        ws.send(json.dumps({"id": cid, "method": method, "params": params or {}}))
        while True:
            resp = json.loads(ws.recv())
            if resp.get("id") == cid:
                return resp.get("result", {})

    def eval_js(expr):
        res = send_cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
        if "exceptionDetails" in res:
            raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
        return res.get("result", {}).get("value")

    send_cmd("Runtime.enable")
    time.sleep(1)

    def wait_for_ready():
        for _ in range(30):
            try:
                res = eval_js("Boolean(window.TempoAuth && window.TempoMode && window.TempoApp)")
                if res is True:
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        raise TimeoutError("Tempo was not initialized.")

    wait_for_ready()

    eval_js("""
        (async () => {
            const mock = {
                id: 'local_user_test',
                email: 'test@tempo.edu',
                raw_email: 'test@tempo.edu',
                password: 'password123',
                user_metadata: { full_name: 'Innietest', display_name: 'Innietest', role: 'student' }
            };
            localStorage.setItem('tempo_mock_account_test@tempo.edu', JSON.stringify(mock));
            if (window.TempoAuth) {
                await window.TempoAuth.signIn("test@tempo.edu", "password123");
            }
        })()
    """)
    time.sleep(1)

    eval_js("window.TempoMode.setMode('recovery');")
    time.sleep(0.5)

    def save_screenshot(filename, clip=None):
        params = {"format": "png"}
        if clip:
            params["clip"] = clip
        res = send_cmd("Page.captureScreenshot", params)
        data = base64.b64decode(res["data"])
        filepath = os.path.join(artifact_dir, filename)
        with open(filepath, "wb") as f:
            f.write(data)
        print(f"Saved screenshot: {filepath} ({len(data)} bytes)")

    # Simulate Option 1: Mascots with h-24 sm:h-28 (112px)
    opt1_metrics = eval_js("""
        (() => {
            const row = document.querySelector('.recovery-support-row');
            const selfCheck = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            
            row.className = 'flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-5 w-full recovery-support-row';
            row.style.maxWidth = '100%';
            row.style.marginLeft = 'auto';
            row.style.marginRight = 'auto';

            const qr = row.querySelector('[title="Quick Relief"]');
            const fn = row.querySelector('[title="Focus Now"]');

            // Remove subtitles
            const qrP = qr.querySelector('p');
            if (qrP) qrP.remove();
            const fnP = fn.querySelector('p');
            if (fnP) fnP.remove();

            [qr, fn].forEach(c => {
                c.style.width = '334.92px';
                c.style.minWidth = '334.92px';
                c.style.maxWidth = '334.92px';
                c.style.height = '100px';
                c.style.minHeight = '100px';
                c.style.maxHeight = '100px';
                c.style.boxSizing = 'border-box';
                c.style.flexShrink = '0';
                c.classList.remove('overflow-hidden', 'min-h-[155px]', 'sm:min-h-[165px]', 'min-h-[175px]', 'h-[175px]', 'p-6', 'sm:p-7');
                c.classList.add('overflow-visible', 'px-2.5', 'py-3.5', 'sm:px-2', 'sm:py-4', 'flex', 'items-center', 'justify-center');
            });

            // Adjust internal flex inside QR and FN
            const qrInner = qr.querySelector('div');
            if (qrInner) {
                qrInner.className = 'flex items-center justify-center gap-2 sm:gap-2.5';
                qrInner.style.transform = 'translateX(10px)';
            }
            const qrH3 = qr.querySelector('h3');
            if (qrH3) {
                qrH3.className = 'text-[29px] sm:text-[31px] font-bold text-[#6D8A7E] leading-tight whitespace-nowrap mb-0';
            }

            const fnInner = fn.querySelector('div');
            if (fnInner) {
                fnInner.className = 'flex items-center justify-center gap-2 sm:gap-2.5';
                fnInner.style.transform = 'translateX(-10px)';
            }
            const fnH3 = fn.querySelector('h3');
            if (fnH3) {
                fnH3.className = 'text-[29px] sm:text-[31px] font-bold text-white leading-tight whitespace-nowrap mb-0';
            }

            const rSelfCheck = selfCheck.getBoundingClientRect();
            const rQr = qr.getBoundingClientRect();
            const rFn = fn.getBoundingClientRect();
            const qrMascot = qr.querySelector('img').getBoundingClientRect();
            const fnMascot = fn.querySelector('img').getBoundingClientRect();

            const centerSelfCheck = rSelfCheck.left + rSelfCheck.width / 2;
            const centerCombinedCards = (rQr.left + rFn.right) / 2;

            return {
                centerSelfCheck,
                centerCombinedCards,
                diffCenter: Math.abs(centerSelfCheck - centerCombinedCards),
                qr: { width: rQr.width, height: rQr.height, mascot: { w: qrMascot.width, h: qrMascot.height } },
                fn: { width: rFn.width, height: rFn.height, mascot: { w: fnMascot.width, h: fnMascot.height } },
                gap: rFn.left - rQr.right
            };
        })()
    """)

    print("OPT 1 METRICS (112px mascots, centered flex):", json.dumps(opt1_metrics, indent=2))

    clip_closeup = eval_js("""
        (() => {
            const row = document.querySelector('.recovery-support-row');
            const selfCheck = document.querySelector('[data-tempo-ui="recovery-self-check"]');
            const rRow = row.getBoundingClientRect();
            const rSelfCheck = selfCheck.getBoundingClientRect();

            const top = Math.max(0, rSelfCheck.bottom - 40);
            const bottom = rRow.bottom + 40;
            const left = Math.max(0, rSelfCheck.left - 20);
            const right = rSelfCheck.right + 20;

            return {
                x: left,
                y: top,
                width: right - left,
                height: bottom - top,
                scale: 1
            };
        })()
    """)
    save_screenshot("rmode_cards_sim_112px.png", clip_closeup)

finally:
    if ws: ws.close()
    proc.terminate()
    proc.wait()
