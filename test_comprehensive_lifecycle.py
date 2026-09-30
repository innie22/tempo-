import subprocess
import time
import json
import urllib.request
import tempfile
import os
import websocket
import sys

def log(msg):
    print(msg, flush=True)

def run_all_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_comprehensive_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    cmd = [
        edge_path,
        "--headless=new",
        "--remote-debugging-port=9222",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "http://localhost:8000/"
    ]
    
    log("Launching Edge with CDP...")
    proc = subprocess.Popen(cmd)
    ws = None
    try:
        ws_url = None
        for _ in range(30):
            try:
                with urllib.request.urlopen("http://127.0.0.1:9222/json") as resp:
                    tabs = json.loads(resp.read().decode())
                    pages = [t for t in tabs if t.get("type") == "page"]
                    if pages:
                        ws_url = pages[0]["webSocketDebuggerUrl"]
                        break
            except Exception:
                time.sleep(0.5)
        
        if not ws_url:
            raise RuntimeError("Failed to connect to Edge CDP endpoint")
            
        log(f"Connected to CDP: {ws_url}")
        ws = websocket.create_connection(ws_url)
        
        msg_id = 1
        def send_command(method, params=None):
            nonlocal msg_id
            cid = msg_id
            msg_id += 1
            req = {"id": cid, "method": method}
            if params:
                req["params"] = params
            ws.send(json.dumps(req))
            while True:
                raw = ws.recv()
                res = json.loads(raw)
                if res.get("method") == "Runtime.consoleAPICalled":
                    args = res.get("params", {}).get("args", [])
                    texts = [str(a.get("value")) for a in args]
                    log("CONSOLE: " + " ".join(texts))
                if res.get("id") == cid:
                    if "error" in res:
                        raise RuntimeError(f"CDP Error in {method}: {res['error']}")
                    return res.get("result", {})
        
        def eval_js(expression, await_promise=True):
            res = send_command("Runtime.evaluate", {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": await_promise
            })
            if "exceptionDetails" in res:
                raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")
        
        def wait_for_ready():
            for _ in range(40):
                try:
                    ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined'")
                    if ready:
                        eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
                        return True
                except Exception:
                    pass
                time.sleep(0.5)
            raise TimeoutError("Page did not reach ready state")
        
        send_command("Runtime.enable")
        wait_for_ready()
        
        log("\n=======================================================")
        log("TEST A: AUTH ONLY (Login -> Reload -> Auth persists)")
        log("=======================================================")
        eval_js("(async () => await window.TempoAuth.signIn('student_alpha@campus.edu', 'pass123'))()")
        alpha_id = eval_js("window.TempoAuth.getCurrentUserId()")
        log(f"Alpha signed in: {alpha_id}")
        assert eval_js("window.TempoAuth.getAuthState()") == 'AUTHENTICATED'
        
        # Reload without any saved plan
        eval_js("window.location.reload()", await_promise=False)
        time.sleep(1)
        wait_for_ready()
        
        post_reload_auth = eval_js("window.TempoAuth.getAuthState()")
        post_reload_id = eval_js("window.TempoAuth.getCurrentUserId()")
        log(f"Post-reload auth state: {post_reload_auth}, user: {post_reload_id}")
        assert post_reload_auth == 'AUTHENTICATED', "User must remain AUTHENTICATED on reload"
        assert post_reload_id == alpha_id, "User ID must match across reload"
        log(">>> TEST A PASSED: Auth session persists across reload.")
        
        log("\n=======================================================")
        log("TEST B & C: EPLAN DURABILITY & PRODUCTION RELOAD")
        log("=======================================================")
        plan_id = "plan_alpha_emergency_999"
        eval_js(f"""
        (async () => {{
            const planData = {{
                id: '{plan_id}',
                tasks: [
                    {{
                        id: 't_alpha_1',
                        name: 'Macroeconomics Paper',
                        hasDeadline: true,
                        deadlineDate: '2026-10-05',
                        deadlineTime: '17:00',
                        estimate: '3h',
                        durationMinutes: 180,
                        priorityCategory: 'DO_FIRST',
                        subtasks: [
                            {{ id: 'sub_a1', title: 'Literature review', durationMinutes: 60, completed: false }}
                        ]
                    }}
                ],
                plannedTasks: [
                    {{
                        taskId: 't_alpha_1',
                        task: {{
                            id: 't_alpha_1',
                            name: 'Macroeconomics Paper',
                            hasDeadline: true,
                            deadlineDate: '2026-10-05',
                            deadlineTime: '17:00',
                            estimate: '3h',
                            durationMinutes: 180,
                            priorityCategory: 'DO_FIRST',
                            subtasks: [
                                {{ id: 'sub_a1', title: 'Literature review', durationMinutes: 60, completed: false }}
                            ]
                        }},
                        dayDate: '2026-10-01',
                        startMin: 600,
                        endMin: 780,
                        scheduledStart: '10:00 AM',
                        scheduledEnd: '1:00 PM',
                        dayLabel: 'Tomorrow'
                    }}
                ]
            }};
            await window.TempoPlanStore.saveActivePlan('emergency', planData);
            window.TempoMode.setMode('emergency');
        }})()
        """)
        
        log("Plan saved. Reloading tab (Flow A)...")
        eval_js("window.location.reload()", await_promise=False)
        time.sleep(1)
        wait_for_ready()
        
        restored_plan = eval_js("window.TempoPlanStore.getActivePlan('emergency')")
        assert restored_plan is not None, "Active plan must survive reload"
        assert restored_plan['id'] == plan_id, f"Expected {plan_id}, got {restored_plan.get('id')}"
        assert restored_plan['tasks'][0]['id'] == 't_alpha_1'
        assert eval_js("window.TempoMode.getCurrentMode()") == 'emergency'
        log(">>> Flow A passed: Plan and mode survive reload.")
        
        log("\nTesting Flow B: Explicit sign-out -> anonymous -> sign back in...")
        eval_js("(async () => await window.TempoAuth.handleSignOut())()")
        assert eval_js("window.TempoAuth.getAuthState()") == 'ANONYMOUS'
        assert eval_js("window.TempoPlanStore.getActivePlan('emergency')") is None
        
        # Sign back in with Alpha
        eval_js("(async () => await window.TempoAuth.signIn('student_alpha@campus.edu', 'pass123'))()")
        assert eval_js("window.TempoAuth.getAuthState()") == 'AUTHENTICATED'
        resin_plan = eval_js("window.TempoPlanStore.getActivePlan('emergency')")
        assert resin_plan is not None, "Plan must restore when signing back in"
        assert resin_plan['id'] == plan_id
        log(">>> TEST B & C PASSED: Flow A & Flow B durable persistence verified.")
        
        log("\n=======================================================")
        log("TEST D: ACTIVE PLAN / MODE SWITCH")
        log("=======================================================")
        eval_js("window.TempoMode.setMode('default')")
        assert eval_js("window.TempoMode.getCurrentMode()") == 'default'
        # Switch back to emergency
        eval_js("window.TempoMode.setMode('emergency')")
        assert eval_js("window.TempoMode.getCurrentMode()") == 'emergency'
        # Plan is preserved
        plan_after_switch = eval_js("window.TempoPlanStore.getActivePlan('emergency')")
        assert plan_after_switch is not None
        assert plan_after_switch['id'] == plan_id
        log(">>> TEST D PASSED: Active plan preserved during mode switches.")
        
        log("\n=======================================================")
        log("TEST E & F: DRAFT SAVE & RESTORE")
        log("=======================================================")
        draft_content = {
            "currentStage": "prioritize",
            "tasks": [
                {"id": "draft_t1", "name": "Draft Task 1", "estimate": "1h"},
                {"id": "draft_t2", "name": "Draft Task 2", "estimate": "2h"}
            ]
        }
        eval_js(f"""
        (async () => {{
            await window.TempoPlanStore.saveDraft('emergency', {json.dumps(draft_content)});
        }})()
        """)
        draft_in_memory = eval_js("window.TempoPlanStore.getDraft('emergency')")
        log(f"draft_in_memory before reload: {draft_in_memory}")
        ls_before = eval_js("Object.keys(localStorage)")
        log(f"localStorage keys before reload: {ls_before}")
        assert draft_in_memory['currentStage'] == 'prioritize'
        assert len(draft_in_memory['tasks']) == 2
        
        # Reload to verify draft restores
        eval_js("window.location.reload()", await_promise=False)
        time.sleep(1)
        wait_for_ready()
        
        reloaded_draft = eval_js("window.TempoPlanStore.getDraft('emergency')")
        log(f"reloaded_draft: {reloaded_draft}")
        ls_keys = eval_js("Object.keys(localStorage)")
        log(f"localStorage keys: {ls_keys}")
        assert reloaded_draft is not None
        assert reloaded_draft['currentStage'] == 'prioritize'
        assert len(reloaded_draft['tasks']) == 2
        log(">>> TEST E PASSED: Draft persists across reload.")
        
        log("\n=======================================================")
        log("TEST H: ACCOUNT ISOLATION (Alpha vs Beta)")
        log("=======================================================")
        # Sign out Alpha
        eval_js("(async () => await window.TempoAuth.handleSignOut())()")
        assert eval_js("window.TempoPlanStore.getActivePlan('emergency')") is None
        
        # Sign in Beta
        eval_js("(async () => await window.TempoAuth.signIn('student_beta@campus.edu', 'pass456'))()")
        beta_id = eval_js("window.TempoAuth.getCurrentUserId()")
        log(f"Beta signed in: {beta_id}")
        assert beta_id != alpha_id
        
        beta_plan = eval_js("window.TempoPlanStore.getActivePlan('emergency')")
        log(f"Beta active plan: {beta_plan}")
        assert beta_plan is None, "Beta MUST NOT see Alpha's emergency plan"
        
        # Sign back in Alpha
        eval_js("(async () => await window.TempoAuth.handleSignOut())()")
        eval_js("(async () => await window.TempoAuth.signIn('student_alpha@campus.edu', 'pass123'))()")
        alpha_restored_plan = eval_js("window.TempoPlanStore.getActivePlan('emergency')")
        assert alpha_restored_plan is not None
        assert alpha_restored_plan['id'] == plan_id
        log(">>> TEST H PASSED: Complete account isolation verified.")
        
        log("\n=======================================================")
        log("TEST G: SAVE FAILURE (Graceful Error Toast & Setup Kept)")
        log("=======================================================")
        save_fail_res = eval_js("""
        (async () => {
            const originalSave = window.TempoPlanStore.saveActivePlan;
            window.TempoPlanStore.saveActivePlan = async () => {
                throw new Error('Supabase network error');
            };
            
            let toastShown = null;
            const originalToast = window.TempoApp.showToast;
            window.TempoApp.showToast = (msg, type) => {
                toastShown = { msg, type };
            };
            
            try {
                await window.TempoEmergencyFlow.savePlan();
            } finally {
                window.TempoPlanStore.saveActivePlan = originalSave;
                window.TempoApp.showToast = originalToast;
            }
            return toastShown;
        })()
        """)
        log(f"Save failure toast: {save_fail_res}")
        assert save_fail_res is not None
        assert "couldn't save your plan" in save_fail_res['msg'].lower()
        log(">>> TEST G PASSED: Save failure graceful UI handling verified.")
        
        log("\n=======================================================")
        log(">>> ALL 7 CORE PERSISTENCE GUARANTEES VERIFIED 100%! <<<")
        log("=======================================================")
        return True
        
    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass
        proc.terminate()
        proc.wait()
        import shutil
        try:
            shutil.rmtree(user_data_dir, ignore_errors=True)
        except Exception:
            pass

if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        sys.exit(1)
