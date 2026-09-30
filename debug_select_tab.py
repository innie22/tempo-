import subprocess, time, json, urllib.request, tempfile, websocket, sys
sys.stdout.reconfigure(encoding='utf-8')

user_data_dir = tempfile.mkdtemp(prefix='tempo_debug_')
edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
port = 9265

proc = subprocess.Popen([
    edge_path, '--headless=new', f'--remote-debugging-port={port}',
    '--remote-allow-origins=*', f'--user-data-dir={user_data_dir}',
    '--disable-gpu', '--no-first-run', 'http://localhost:8000/'
])
time.sleep(2)
try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/json') as resp:
        tabs = json.loads(resp.read().decode())
        ws_url = tabs[0]['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url, timeout=5)
    
    def eval_js(expr):
        ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'returnByValue': True, 'awaitPromise': True}}))
        while True:
            res = json.loads(ws.recv())
            if res.get('id') == 1:
                return res.get('result', {}).get('result', {}).get('value')
    
    time.sleep(1)
    eval_js('window.TempoMode.setMode("emergency"); window.TempoMode.renderEmodeHome();')
    print('Initial query count:', eval_js('document.querySelectorAll("#tempo-learn-solve-section").length'))
    eval_js('window.TempoLearnSolve.selectTab("learn");')
    print('After selectTab query count:', eval_js('document.querySelectorAll("#tempo-learn-solve-section").length'))
    res = eval_js("""
    (() => {
        const sections = Array.from(document.querySelectorAll('#tempo-learn-solve-section'));
        return sections.map(s => {
            const learnCard = s.querySelector('div[onclick*="selectTab(\\'learn\\')"]');
            const topics = s.querySelectorAll('button[onclick*="openTopic"]');
            return {
                parent: s.parentElement ? (s.parentElement.id || s.parentElement.className) : null,
                classes: learnCard ? learnCard.className : null,
                topicCount: topics.length
            };
        });
    })()
    """)
    print('Sections info:', json.dumps(res, indent=2))
finally:
    proc.terminate()
