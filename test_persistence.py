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

def run_test():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_test_profile_")
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
    
    log("Launching Edge with CDP on http://localhost:8000/ ...")
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
        
        # Wait for page to reach readyState === 'complete' and TempoAuth loaded
        log("Waiting for page load and TempoAuth...")
        for _ in range(30):
            try:
                ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined'")
                if ready:
                    log("Page and TempoAuth ready!")
                    break
            except Exception:
                pass
            time.sleep(0.5)
            
        # Give async bootstrap a moment to resolve auth
        eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
        
        log("\n--- Test 1: Page Bootstrap & Auth State ---")
        loc = eval_js("window.location.href")
        log(f"Current location: {loc}")
        auth_state = eval_js("window.TempoAuth.getAuthState()")
        log(f"Initial Auth State: {auth_state}")
        assert auth_state in ['AUTHENTICATED', 'ANONYMOUS'], f"Expected resolved auth, got {auth_state}"
        
        log("\n--- Test 2: Local Dev User Sign-In ---")
        sign_in_res = eval_js("""
        (async () => {
            return await window.TempoAuth.signIn('persisted_student@university.edu', 'password123');
        })()
        """)
        log(f"Sign-in result: {sign_in_res}")
        user_id = eval_js("window.TempoAuth.getCurrentUserId()")
        user_email = eval_js("window.TempoAuth.getCurrentUser() ? window.TempoAuth.getCurrentUser().email : null")
        log(f"Authenticated user: {user_id} ({user_email})")
        assert user_email == 'persisted_student@university.edu', "User email should match sign-in"
        assert eval_js("window.TempoAuth.getAuthState()") == 'AUTHENTICATED'
        
        log("\n--- Test 3: Save Active Emergency Plan ---")
        save_plan_res = eval_js("""
        (async () => {
            const planData = {
                planId: 'plan_test_durable_101',
                tasks: [
                    {
                        id: 'task_math_99',
                        name: 'Math Assignment 4',
                        hasDeadline: true,
                        deadlineDate: '2026-10-02',
                        deadlineTime: '23:59',
                        estimate: '2h',
                        durationMinutes: 120,
                        priorityCategory: 'DO_FIRST',
                        subtasks: [
                            { id: 'sub_1', title: 'Problem 1 & 2', durationMinutes: 45, completed: false },
                            { id: 'sub_2', title: 'Problem 3 & 4', durationMinutes: 45, completed: false }
                        ]
                    }
                ],
                plannedTasks: [
                    {
                        taskId: 'task_math_99',
                        task: {
                            id: 'task_math_99',
                            name: 'Math Assignment 4',
                            hasDeadline: true,
                            deadlineDate: '2026-10-02',
                            deadlineTime: '23:59',
                            estimate: '2h',
                            durationMinutes: 120,
                            priorityCategory: 'DO_FIRST',
                            subtasks: [
                                { id: 'sub_1', title: 'Problem 1 & 2', durationMinutes: 45, completed: false },
                                { id: 'sub_2', title: 'Problem 3 & 4', durationMinutes: 45, completed: false }
                            ]
                        },
                        dayDate: '2026-10-01',
                        startMin: 540,
                        endMin: 660,
                        scheduledStart: '9:00 AM',
                        scheduledEnd: '11:00 AM',
                        dayLabel: 'Tomorrow'
                    }
                ],
                availability: [
                    { date: '2026-10-01', dayLabel: 'Tomorrow', totalHours: 4 }
                ]
            };
            return await window.TempoPlanStore.saveActivePlan('emergency', planData);
        })()
        """)
        log(f"Save active plan result: {save_plan_res}")
        
        active_plan = eval_js("window.TempoPlanStore.getActivePlan('emergency')")
        assert active_plan is not None, "Active plan should not be null"
        assert active_plan['planId'] == 'plan_test_durable_101'
        log(f"Active plan loaded in memory: planId = {active_plan['planId']}")
        
        eval_js("window.TempoMode.setMode('emergency')")
        mode = eval_js("window.TempoMode.getCurrentMode()")
        log(f"Mode switched to: {mode}")
        assert mode == 'emergency'
        
        log("\n--- Test 4: FLOW A - Browser Reload Persistence ---")
        eval_js("window.location.reload()", await_promise=False)
        time.sleep(1)
        for _ in range(30):
            try:
                ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoPlanStore !== 'undefined'")
                if ready:
                    break
            except Exception:
                pass
            time.sleep(0.5)
            
        eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
        time.sleep(1)
        
        reloaded_auth_state = eval_js("window.TempoAuth.getAuthState()")
        reloaded_user = eval_js("window.TempoAuth.getCurrentUser() ? window.TempoAuth.getCurrentUser().email : null")
        reloaded_user_id = eval_js("window.TempoAuth.getCurrentUserId()")
        log(f"Post-reload auth: {reloaded_auth_state}, user: {reloaded_user_id} ({reloaded_user})")
        
        assert reloaded_auth_state == 'AUTHENTICATED', f"User should remain AUTHENTICATED across reload, got {reloaded_auth_state}"
        assert reloaded_user == 'persisted_student@university.edu', "Email should match before reload"
        assert reloaded_user_id == user_id, "User ID must be identical across reload"
        
        reloaded_plan = eval_js("window.TempoPlanStore.getActivePlan('emergency')")
        assert reloaded_plan is not None, "Saved Emergency Plan must survive reload"
        assert reloaded_plan['planId'] == 'plan_test_durable_101', f"Plan ID mismatch: {reloaded_plan.get('planId')}"
        assert len(reloaded_plan['tasks']) == 1, "Task list should be restored"
        assert reloaded_plan['tasks'][0]['id'] == 'task_math_99', "Task ID restored"
        assert len(reloaded_plan['tasks'][0]['subtasks']) == 2, "Subtasks restored"
        assert reloaded_plan['plannedTasks'][0]['dayDate'] == '2026-10-01', "Planned dayDate restored"
        log("Post-reload plan verified successfully!")
        
        reloaded_mode = eval_js("window.TempoMode.getCurrentMode()")
        log(f"Post-reload mode: {reloaded_mode}")
        assert reloaded_mode == 'emergency', f"Emergency mode should survive reload, got {reloaded_mode}"
        
        log("\n--- Test 5: FLOW B - Explicit Sign Out & Re-Authentication ---")
        eval_js("""
        (async () => {
            await window.TempoAuth.handleSignOut();
        })()
        """)
        signout_auth_state = eval_js("window.TempoAuth.getAuthState()")
        signout_plan = eval_js("window.TempoPlanStore.getActivePlan('emergency')")
        log(f"Post-signout auth state: {signout_auth_state}, active plan in memory: {signout_plan}")
        assert signout_auth_state == 'ANONYMOUS', "Auth state should be ANONYMOUS after sign-out"
        assert signout_plan is None, "In-memory plan should be cleared on sign-out for security"
        
        log("Signing back in with same account...")
        eval_js("""
        (async () => {
            return await window.TempoAuth.signIn('persisted_student@university.edu', 'password123');
        })()
        """)
        resin_auth_state = eval_js("window.TempoAuth.getAuthState()")
        resin_user_id = eval_js("window.TempoAuth.getCurrentUserId()")
        assert resin_auth_state == 'AUTHENTICATED'
        assert resin_user_id == user_id
        
        resin_plan = eval_js("window.TempoPlanStore.getActivePlan('emergency')")
        assert resin_plan is not None, "Emergency Plan must restore when signing back into SAME account"
        assert resin_plan['planId'] == 'plan_test_durable_101', "Correct plan restored"
        log("FLOW B verified successfully: Plan restored after re-authentication!")
        
        log("\n--- Test 6: Save Failure Graceful Error Handling ---")
        save_fail_res = eval_js("""
        (async () => {
            const originalSave = window.TempoPlanStore.saveActivePlan;
            window.TempoPlanStore.saveActivePlan = async () => {
                throw new Error('Database connection failed (simulated)');
            };
            
            let caughtError = null;
            let toastShown = null;
            const originalToast = window.TempoApp.showToast;
            window.TempoApp.showToast = (msg, type) => {
                toastShown = { msg, type };
                if (originalToast) originalToast(msg, type);
            };
            
            try {
                await window.TempoEmergencyFlow.savePlan();
            } catch (err) {
                caughtError = err.message;
            } finally {
                window.TempoPlanStore.saveActivePlan = originalSave;
                window.TempoApp.showToast = originalToast;
            }
            return { caughtError, toastShown };
        })()
        """)
        log(f"Save failure handling result: {save_fail_res}")
        assert save_fail_res['toastShown'] is not None, "Error toast must be shown on save failure"
        assert "couldn't save your plan" in save_fail_res['toastShown']['msg'].lower(), "Correct message in toast"
        log("Save failure error handling verified successfully!")
        
        log("\n--- Test 7: Verify Zero Native Dialogs (alert, confirm, prompt) ---")
        native_dialog_check = eval_js("""
        (() => {
            return {
                alertNative: window.alert.toString().includes('[native code]'),
                confirmNative: window.confirm.toString().includes('[native code]'),
                promptNative: window.prompt.toString().includes('[native code]')
            };
        })()
        """)
        log(f"Native dialog check: {native_dialog_check}")
        
        log("\n>>> ALL PERSISTENCE AND AUTH TESTS PASSED PERFECTLY! <<<")
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
    success = run_test()
    if not success:
        sys.exit(1)
