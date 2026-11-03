import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix="tempo_inspect_urmode_")
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
port = 9273

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

    eval_js("window.TempoMode.setMode('emergency');")
    time.sleep(0.5)

    def inspect_viewport(vp_name):
        return eval_js(f"""
            (() => {{
                const vp = {{
                    innerWidth: window.innerWidth,
                    innerHeight: window.innerHeight,
                    devicePixelRatio: window.devicePixelRatio
                }};
                const parent = document.querySelector('[data-tempo-ui="urgent-support"]');
                const qr = parent ? parent.querySelector('[title="Quick Relief"]') : null;
                const fn = parent ? parent.querySelector('[title="Focus Now"]') : null;

                const getMetrics = (el) => {{
                    if (!el) return null;
                    const r = el.getBoundingClientRect();
                    const cs = window.getComputedStyle(el);
                    return {{
                        tagName: el.tagName.toLowerCase(),
                        className: el.className,
                        id: el.id,
                        rect: {{
                            x: r.x,
                            y: r.y,
                            width: r.width,
                            height: r.height,
                            top: r.top,
                            right: r.right,
                            bottom: r.bottom,
                            left: r.left
                        }},
                        computed: {{
                            width: cs.width,
                            height: cs.height,
                            minWidth: cs.minWidth,
                            maxWidth: cs.maxWidth,
                            minHeight: cs.minHeight,
                            maxHeight: cs.maxHeight,
                            boxSizing: cs.boxSizing,
                            display: cs.display,
                            padding: cs.padding,
                            paddingTop: cs.paddingTop,
                            paddingRight: cs.paddingRight,
                            paddingBottom: cs.paddingBottom,
                            paddingLeft: cs.paddingLeft,
                            margin: cs.margin,
                            marginTop: cs.marginTop,
                            marginRight: cs.marginRight,
                            marginBottom: cs.marginBottom,
                            marginLeft: cs.marginLeft,
                            borderWidth: cs.borderWidth,
                            borderRadius: cs.borderRadius,
                            gridTemplateColumns: cs.gridTemplateColumns,
                            gridTemplateRows: cs.gridTemplateRows,
                            gap: cs.gap,
                            rowGap: cs.rowGap,
                            columnGap: cs.columnGap,
                            alignItems: cs.alignItems,
                            justifyContent: cs.justifyContent,
                            justifyItems: cs.justifyItems,
                            alignContent: cs.alignContent
                        }},
                        inlineStyle: el.getAttribute('style') || ''
                    }};
                }};

                const parentMetrics = getMetrics(parent);
                const qrMetrics = getMetrics(qr);
                const fnMetrics = getMetrics(fn);

                let gapBetween = null;
                if (qrMetrics && fnMetrics) {{
                    gapBetween = fnMetrics.rect.left - qrMetrics.rect.right;
                }}

                return {{
                    viewportName: '{vp_name}',
                    viewport: vp,
                    parent: parentMetrics,
                    quickRelief: qrMetrics,
                    focusNow: fnMetrics,
                    gapBetweenCards: gapBetween
                }};
            }})()
        """)

    print("=== DESKTOP 1440x900 ===")
    res_1440 = inspect_viewport("desktop_1440x900")
    print(json.dumps(res_1440, indent=2))

    # Also test at 1024x768 desktop breakpoint
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 1024,
        "height": 768,
        "deviceScaleFactor": 1,
        "mobile": False
    })
    time.sleep(0.3)
    print("\n=== DESKTOP 1024x768 ===")
    res_1024 = inspect_viewport("desktop_1024x768")
    print(json.dumps(res_1024, indent=2))

    # Also test at 640px (sm breakpoint boundary)
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 640,
        "height": 800,
        "deviceScaleFactor": 1,
        "mobile": False
    })
    time.sleep(0.3)
    print("\n=== TABLET 640px (sm boundary) ===")
    res_640 = inspect_viewport("tablet_640px")
    print(json.dumps(res_640, indent=2))

    # Also test at 375px (mobile breakpoint)
    send_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 375,
        "height": 812,
        "deviceScaleFactor": 1,
        "mobile": True
    })
    time.sleep(0.3)
    print("\n=== MOBILE 375px ===")
    res_375 = inspect_viewport("mobile_375px")
    print(json.dumps(res_375, indent=2))

finally:
    if ws: ws.close()
    proc.terminate()
    proc.wait()
