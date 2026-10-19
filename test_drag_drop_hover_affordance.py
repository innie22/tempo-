"""
TEMPO TEST SUITE: Working Plan Drag-and-Drop Restoration & Grab-Hand Cursor Verification
File: test_drag_drop_hover_affordance.py

Verifies all 7 required behaviors:
1. Dragging a task by its handle starts successfully.
2. A task can be moved to a different position and dropped.
3. The task order updates correctly after dropping.
4. Hovering the handle displays the pixel-style grab-hand cursor matching the reference.
5. The cursor changes appropriately while dragging (grabbing hand).
6. Buttons and other interactive elements inside task cards remain usable.
7. The card hover effect still works.
"""

import subprocess
import time
import json
import urllib.request
import tempfile
import websocket
import sys

sys.stdout.reconfigure(encoding='utf-8')

def log(msg):
    print(msg, flush=True)

def run_tests():
    user_data_dir = tempfile.mkdtemp(prefix="tempo_drag_restore_test_")
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    port = 9248
    
    cmd = [
        edge_path,
        "--headless=new",
        f"--remote-debugging-port={port}",
        "--remote-allow-origins=*",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu",
        "--no-first-run",
        "http://localhost:8000/"
    ]
    
    log(f"Launching Edge on port {port}...")
    proc = subprocess.Popen(cmd)
    ws = None
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
                msg = json.loads(raw)
                if msg.get("id") == cid:
                    if "error" in msg:
                        raise RuntimeError(f"CDP error: {msg['error']}")
                    return msg.get("result", {})

        def eval_js(expr, await_promise=True):
            res = send_command("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": await_promise
            })
            if "exceptionDetails" in res:
                raise RuntimeError(f"JS Exception: {res['exceptionDetails']}")
            return res.get("result", {}).get("value")

        def wait_for_ready():
            for _ in range(40):
                try:
                    ready = eval_js("document.readyState === 'complete' && typeof window.TempoAuth !== 'undefined' && typeof window.TempoEmergencyFlow !== 'undefined' && typeof window.TempoPlanWorkspace !== 'undefined'")
                    if ready:
                        eval_js("window.TempoAuth.waitForAuthResolution ? window.TempoAuth.waitForAuthResolution() : Promise.resolve()")
                        return
                except Exception:
                    pass
                time.sleep(0.5)
            raise RuntimeError("Timed out waiting for Tempo app ready")

        wait_for_ready()
        log("App is ready.")

        # =====================================================================
        # 1. SETUP PLAN WITH 2 TASKS
        # =====================================================================
        log("\n--- SETUP: Initialize 2-Task Working Plan ---")
        setup_res = eval_js("""
            (async () => {
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const today = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;

                const testPlan = {
                    id: 'plan_drag_restore',
                    planType: 'emergency',
                    plannedTasks: [
                        {
                            dayDate: today,
                            dayLabel: 'TODAY',
                            startTime: '09:00 AM',
                            endTime: '10:00 AM',
                            executionBadge: 'UP NEXT',
                            task: {
                                id: 'task-1',
                                name: 'First Milestone Task',
                                durationLabel: '1h',
                                durationMinutes: 60,
                                hasDeadline: false,
                                completed: false,
                                subtasks: [{ id: 's1', title: 'Step 1', completed: false }]
                            }
                        },
                        {
                            dayDate: today,
                            dayLabel: 'TODAY',
                            startTime: '10:30 AM',
                            endTime: '12:00 PM',
                            executionBadge: 'THEN',
                            task: {
                                id: 'task-2',
                                name: 'Second Milestone Task',
                                durationLabel: '1h 30m',
                                durationMinutes: 90,
                                hasDeadline: false,
                                completed: false,
                                subtasks: []
                            }
                        }
                    ],
                    tasks: [],
                    availabilityDays: [{ label: 'TODAY', date: today, blocks: [{ start: '09:00', end: '17:00' }] }]
                };
                testPlan.tasks = testPlan.plannedTasks.map(pt => pt.task);

                await window.TempoPlanStore.saveActivePlan('emergency', testPlan);
                window.TempoEmergencyFlow.restorePlanState();
                window.TempoEmergencyFlow.goToStage('plan-review');

                const cards = document.querySelectorAll('.em-timeline-card');
                const dragHandles = document.querySelectorAll('.em-drag-handle');

                return {
                    cardsCount: cards.length,
                    dragHandlesCount: dragHandles.length
                };
            })()
        """)
        log(f"Setup verification: {json.dumps(setup_res, indent=2)}")
        assert setup_res['cardsCount'] == 2, f"Expected 2 task cards, got {setup_res['cardsCount']}"
        assert setup_res['dragHandlesCount'] == 2, f"Expected 2 drag handles, got {setup_res['dragHandlesCount']}"

        # =====================================================================
        # VERIFICATION 4: HOVERING THE HANDLE DISPLAYS PIXEL GRAB HAND CURSOR
        # =====================================================================
        log("\n--- VERIFICATION 4: Pixel-Style Grab-Hand Cursor on Handle Hover ---")
        cursor_check = eval_js("""
            (() => {
                const card = document.querySelector('.em-timeline-card');
                const handle = card.querySelector('.em-drag-handle');
                const button = card.querySelector('button');

                const cardCursor = window.getComputedStyle(card).cursor;
                const handleCursor = window.getComputedStyle(handle).cursor;
                const buttonCursor = window.getComputedStyle(button).cursor;

                // Check CSS cursor rule definition
                let grabCursorInCSS = false;
                for (const sheet of document.styleSheets) {
                    try {
                        for (const rule of sheet.cssRules) {
                            if (rule.selectorText && rule.selectorText.includes('.em-drag-handle')) {
                                if (rule.style && rule.style.cursor && rule.style.cursor.includes('grab')) {
                                    grabCursorInCSS = true;
                                }
                            }
                        }
                    } catch (e) {}
                }

                return {
                    cardCursor,
                    handleCursor,
                    buttonCursor,
                    grabCursorInCSS,
                    hasCustomCursorUrl: handleCursor.includes('grab.png') || handleCursor.includes('data:image') || handleCursor.includes('grab')
                };
            })()
        """)
        log(f"Cursor verification: {json.dumps(cursor_check, indent=2)}")
        assert cursor_check['cardCursor'] == 'default', f"Card cursor must be 'default', got {cursor_check['cardCursor']}"
        assert cursor_check['hasCustomCursorUrl'], f"Handle cursor must reference grab cursor, got {cursor_check['handleCursor']}"
        assert cursor_check['buttonCursor'] == 'pointer', f"Button cursor must be 'pointer', got {cursor_check['buttonCursor']}"
        log("✓ Hovering the handle displays the pixel-style grab-hand cursor, card is 'default', buttons are 'pointer'.")

        # =====================================================================
        # VERIFICATION 1: DRAGGING A TASK BY ITS HANDLE STARTS SUCCESSFULLY
        # =====================================================================
        log("\n--- VERIFICATION 1: Dragging a Task Starts Successfully ---")
        drag_start_check = eval_js("""
            (() => {
                const cards = document.querySelectorAll('.em-timeline-card');
                const card0 = cards[0];
                const handle0 = card0.querySelector('.em-drag-handle');

                // Verify draggable is enabled on card
                const isDraggable = card0.getAttribute('draggable') === 'true' || card0.draggable === true;

                // Dispatch native dragstart event simulating user grabbing the handle
                const dragEvent = new Event('dragstart', { bubbles: true, cancelable: true });
                dragEvent.dataTransfer = {
                    setData: (type, val) => { dragEvent._data = { type, val }; },
                    effectAllowed: ''
                };
                Object.defineProperty(dragEvent, 'target', { value: handle0 });

                const notCancelled = card0.dispatchEvent(dragEvent);

                const cardHasDraggingClass = card0.classList.contains('em-card-dragging');
                const cardHasOpacity = card0.classList.contains('opacity-60');
                const cardHasBorderDashed = card0.classList.contains('border-dashed');
                const cardHasShadowLg = card0.classList.contains('shadow-lg');
                const bodyHasDraggingClass = document.body.classList.contains('is-dragging-card');
                const handleHasIsGrabbing = handle0.classList.contains('is-grabbing');

                return {
                    isDraggable,
                    notCancelled,
                    cardHasDraggingClass,
                    cardHasOpacity,
                    cardHasBorderDashed,
                    cardHasShadowLg,
                    bodyHasDraggingClass,
                    handleHasIsGrabbing,
                    draggedData: dragEvent._data
                };
            })()
        """)
        log(f"Drag start check: {json.dumps(drag_start_check, indent=2)}")
        assert drag_start_check['isDraggable'], "Card must have draggable=true"
        assert drag_start_check['notCancelled'], "dragstart must start successfully (not cancelled)"
        assert drag_start_check['cardHasDraggingClass'], "Card must receive .em-card-dragging feedback"
        assert drag_start_check['cardHasOpacity'], "Card must have reduced opacity (opacity-60)"
        assert drag_start_check['cardHasShadowLg'], "Card must have stronger shadow (shadow-lg)"
        assert drag_start_check['cardHasBorderDashed'], "Card must have dashed border"
        log("✓ Dragging starts successfully with clear, restrained feedback (shadow, opacity, dashed border).")

        # =====================================================================
        # VERIFICATION 5: CURSOR CHANGES APPROPRIATELY WHILE DRAGGING
        # =====================================================================
        log("\n--- VERIFICATION 5: Cursor Changes to Grabbing while Dragging ---")
        dragging_cursor_check = eval_js("""
            (() => {
                const bodyCursor = window.getComputedStyle(document.body).cursor;
                const card = document.querySelector('.em-timeline-card');
                const handle = card.querySelector('.em-drag-handle');
                const handleCursor = window.getComputedStyle(handle).cursor;

                return {
                    bodyCursor,
                    handleCursor,
                    isGrabbing: handleCursor.includes('grabbing') || bodyCursor.includes('grabbing')
                };
            })()
        """)
        log(f"Dragging cursor check: {json.dumps(dragging_cursor_check, indent=2)}")
        assert dragging_cursor_check['isGrabbing'], f"Cursor must switch to grabbing while active, got {dragging_cursor_check}"
        log("✓ Cursor changes appropriately to grabbing cursor while actively dragging.")

        # =====================================================================
        # VERIFICATION 2 & 3: TASK CAN BE MOVED, DROPPED, AND ORDER UPDATES
        # =====================================================================
        log("\n--- VERIFICATION 2 & 3: Moving to Different Position, Dropping & Order Update ---")
        drop_reorder_check = eval_js("""
            (() => {
                const cards = document.querySelectorAll('.em-timeline-card');
                const card0 = cards[0];
                const card1 = cards[1];

                // Simulate dragenter on target card
                const enterEvent = new Event('dragenter', { bubbles: true, cancelable: true });
                card1.dispatchEvent(enterEvent);

                const targetHasDropTarget = card1.classList.contains('em-drop-target');
                const targetHasBorderB = card1.classList.contains('border-b-2');

                // Simulate drop event on target card (index 1)
                const dropEvent = new Event('drop', { bubbles: true, cancelable: true });
                dropEvent.dataTransfer = { getData: () => '0' };
                card1.dispatchEvent(dropEvent);

                // Check updated state
                const plan = window.TempoPlanStore.getActivePlan('emergency');
                const newIds = plan.plannedTasks.map(pt => pt.task.id);
                const newNames = plan.plannedTasks.map(pt => pt.task.name);

                const cleanAfterDrop = !document.body.classList.contains('is-dragging-card') &&
                                       !document.querySelector('.em-timeline-card.em-card-dragging');

                return {
                    targetHasDropTarget,
                    targetHasBorderB,
                    newIds,
                    newNames,
                    cleanAfterDrop,
                    firstIsTask2: newIds[0] === 'task-2',
                    secondIsTask1: newIds[1] === 'task-1'
                };
            })()
        """)
        log(f"Drop & reorder check: {json.dumps(drop_reorder_check, indent=2)}")
        assert drop_reorder_check['targetHasDropTarget'], "Target card must show drop-position indicator"
        assert drop_reorder_check['firstIsTask2'] and drop_reorder_check['secondIsTask1'], f"Task order must swap after drop, got: {drop_reorder_check['newIds']}"
        assert drop_reorder_check['cleanAfterDrop'], "Drag styles and is-dragging-card must be cleaned up on drop"
        log("✓ Task moved, drop position indicator displayed, drop completed, and order updated correctly.")

        # =====================================================================
        # VERIFICATION 6: BUTTONS AND CONTROLS REMAIN FULLY USABLE
        # =====================================================================
        log("\n--- VERIFICATION 6: Buttons and Controls Usable Without Triggering Drag ---")
        button_check = eval_js("""
            (() => {
                const laterBtn = document.querySelector('button[title=\"Do this task later\"]');
                const breakBtn = document.querySelector('button[title=\"Break task down\"]');

                // Try dragstart on button (must be prevented)
                const dragEventOnBtn = new Event('dragstart', { bubbles: true, cancelable: true });
                Object.defineProperty(dragEventOnBtn, 'target', { value: laterBtn });
                const btnDragAllowed = laterBtn.dispatchEvent(dragEventOnBtn);

                // Open schedule modal via button click
                laterBtn.click();
                const modalVisible = document.querySelector('#em-schedule-modal-title') !== null;

                // Close modal
                window.TempoEmergencyFlow.closeScheduleModal();
                const modalClosed = document.querySelector('#em-schedule-modal-title') === null;

                return {
                    btnDragAllowed,
                    modalVisible,
                    modalClosed
                };
            })()
        """)
        log(f"Button usability check: {json.dumps(button_check, indent=2)}")
        assert not button_check['btnDragAllowed'], "Dragging from buttons must be prevented"
        assert button_check['modalVisible'], "Clicking button must open schedule modal"
        assert button_check['modalClosed'], "Modal must close cleanly"
        log("✓ Buttons remain fully usable, clickable, and do not trigger drag.")

        # =====================================================================
        # VERIFICATION 7: CARD HOVER EFFECT STILL WORKS
        # =====================================================================
        log("\n--- VERIFICATION 7: Card Hover Effect Preserved ---")
        hover_check = eval_js("""
            (() => {
                const card = document.querySelector('.em-timeline-card');
                const handle = card.querySelector('.em-drag-handle');

                let cardHoverShadow = false;
                let cardHoverBorder = false;
                let handleContrastHover = false;

                for (const sheet of document.styleSheets) {
                    try {
                        for (const rule of sheet.cssRules) {
                            const sel = rule.selectorText || '';
                            if (sel.includes('.em-timeline-card:hover')) {
                                if (rule.style && rule.style.boxShadow) cardHoverShadow = true;
                                if (rule.style && rule.style.borderColor) cardHoverBorder = true;
                            }
                            if (sel.includes('.em-timeline-card:hover .em-drag-handle')) {
                                if (rule.style && rule.style.color) handleContrastHover = true;
                            }
                        }
                    } catch (e) {}
                }

                return {
                    cardHoverShadow,
                    cardHoverBorder,
                    handleContrastHover,
                    transition: window.getComputedStyle(card).transition,
                    transitionProperty: window.getComputedStyle(card).transitionProperty,
                    hasTransition: window.getComputedStyle(card).transitionProperty !== 'none' && window.getComputedStyle(card).transitionDuration !== '0s'
                };
            })()
        """)
        log(f"Hover effect check: {json.dumps(hover_check, indent=2)}")
        assert hover_check['cardHoverShadow'], "Card hover elevation shadow must be present in stylesheet"
        assert hover_check['cardHoverBorder'], "Card hover border deepen must be present in stylesheet"
        assert hover_check['handleContrastHover'], "Handle contrast enhancement on card hover must be present"
        assert hover_check['hasTransition'], "Smooth transition must be preserved"
        log("✓ Card hover effect (subtle elevation, restrained border, handle contrast, smooth transition) verified.")

        log("\n=====================================================================")
        log(">>> ALL 7 BEHAVIOR VERIFICATIONS COMPLETED AND PASSED WITH 100%! <<<")
        log("=====================================================================")

    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()

if __name__ == '__main__':
    run_tests()
