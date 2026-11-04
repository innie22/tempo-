# -*- coding: utf-8 -*-
import sys, json, time, subprocess, os, urllib.request, websocket
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

proc = subprocess.Popen([
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "--remote-debugging-port=9515",
    "--user-data-dir=C:\\Temp\\debug_suite6",
    "--headless=new",
    "http://127.0.0.1:8000/#explore-mental-health-tests?category=stress"
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    time.sleep(2)
    req = urllib.request.urlopen("http://127.0.0.1:9515/json")
    pages = json.loads(req.read().decode())
    page = [p for p in pages if p.get("type") == "page" and "127.0.0.1:8000" in p.get("url", "")][0]
    ws = websocket.create_connection(page['webSocketDebuggerUrl'])

    def eval_js(code):
        ws.send(json.dumps({'id': 1, 'method': 'Runtime.evaluate', 'params': {'expression': code, 'returnByValue': True, 'awaitPromise': True}}))
        raw = json.loads(ws.recv())
        return raw.get('result', {}).get('result', {}).get('value')

    eval_js("window.TempoI18n.setLanguage('en');")
    eval_js("window.TempoPAS.openTestModal();")
    eval_js("window.TempoPAS.startTest();")
    sim_answers = [4] * 18
    eval_js(f"window.TempoPAS._setTestState({{ currentStep: 'question', currentQuestionIndex: 17, answers: {json.dumps(sim_answers)}, validationError: '' }});")
    eval_js("window.TempoPAS.handleNextQuestion();")
    time.sleep(0.5)
    
    text = eval_js("document.getElementById('pas-modal-card').innerText")
    print("=== INNER TEXT ===")
    print(text)
finally:
    proc.terminate()
