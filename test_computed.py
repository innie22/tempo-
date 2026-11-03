import json, urllib.request, websocket

CDP_PORT = 9460
try:
    with urllib.request.urlopen(f'http://127.0.0.1:{CDP_PORT}/json') as resp:
        tabs = json.loads(resp.read().decode())
    pages = [t for t in tabs if t.get('type') == 'page' and '127.0.0.1' in t.get('url', '')]
    ws = websocket.create_connection(pages[0]['webSocketDebuggerUrl'])

    expr = """
        (() => {
            const s = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
            const n = document.querySelector('[data-tempo-ui="lower-create-notes"]');
            const p = s.parentElement;
            const csS = window.getComputedStyle(s);
            const csN = window.getComputedStyle(n);
            const csP = window.getComputedStyle(p);
            const rS = s.getBoundingClientRect();
            const rN = n.getBoundingClientRect();
            const rP = p.getBoundingClientRect();
            return {
                parent: { left: rP.left, right: rP.right, width: rP.width, display: csP.display },
                streak: { left: rS.left, right: rS.right, width: rS.width, alignSelf: csS.alignSelf, marginLeft: csS.marginLeft, marginRight: csS.marginRight },
                notes: { left: rN.left, right: rN.right, width: rN.width, alignSelf: csN.alignSelf, marginLeft: csN.marginLeft, marginRight: csN.marginRight }
            };
        })()
    """
    ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True}}))
    print(ws.recv())
except Exception as e:
    print("Error:", e)
