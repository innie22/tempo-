import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_test_focus_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9271

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

    res = eval_js("""
        (() => {
            const row = document.querySelector('.recovery-support-row');
            const learnSolveCard = row.children[1];
            const originalRect = learnSolveCard.getBoundingClientRect();
            
            // Build Focus Now card HTML with min-h-[175px] h-[175px]
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = `
                <div onclick="if (window.TempoFocusZone && window.TempoFocusZone.openQuickEntry) { window.TempoFocusZone.openQuickEntry(); } else if (window.TempoTriage && window.TempoTriage.launchFocusMode) { window.TempoTriage.launchFocusMode(); }"
                     role="button"
                     tabindex="0"
                     aria-label="Focus Now"
                     onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); this.click(); }"
                     class="bg-[#D29C85] border border-[#4A4541]/20 rounded-3xl p-6 sm:p-7 flex items-center justify-between min-h-[175px] h-[175px] shadow-xs hover:shadow-md transition cursor-pointer group relative overflow-hidden"
                     title="Focus Now">
                    <img src="assets/focus-now-mascot.png"
                         alt="Focus Now"
                         class="h-24 sm:h-28 w-auto object-contain shrink-0 select-none pointer-events-none -ml-2 group-hover:scale-105 transition-transform" />
                    <div class="pl-2 z-10 flex-1 min-w-0 text-right sm:text-left">
                        <h3 class="text-2xl sm:text-[26px] font-bold text-white leading-tight mb-1.5">
                            Focus Now
                        </h3>
                        <p class="text-xs sm:text-sm text-white/90 leading-snug">
                            Your own personalized workspace.
                        </p>
                    </div>
                </div>
            `;
            const focusCard = tempDiv.firstElementChild;
            row.replaceChild(focusCard, learnSolveCard);

            const qrRect = row.children[0].getBoundingClientRect();
            const fnRect = row.children[1].getBoundingClientRect();

            return {
                originalLearnSolveRect: {
                    x: originalRect.x,
                    y: originalRect.y,
                    width: originalRect.width,
                    height: originalRect.height
                },
                newFocusNowRect: {
                    x: fnRect.x,
                    y: fnRect.y,
                    width: fnRect.width,
                    height: fnRect.height
                },
                quickReliefRect: {
                    x: qrRect.x,
                    y: qrRect.y,
                    width: qrRect.width,
                    height: qrRect.height
                },
                heightMatch: fnRect.height === originalRect.height,
                widthMatch: fnRect.width === originalRect.width,
                topAligned: fnRect.y === qrRect.y,
                gap: fnRect.x - (qrRect.x + qrRect.width)
            };
        })()
    """)
    print(json.dumps(res, indent=2))

finally:
    if ws: ws.close()
    proc.terminate()
    proc.wait()
