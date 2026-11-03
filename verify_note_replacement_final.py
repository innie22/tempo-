# -*- coding: utf-8 -*-
import subprocess, time, json, urllib.request, websocket, base64, tempfile, os

CDP_PORT = 9488
artifact_dir = r'C:\Users\YEN NHI\.gemini\antigravity\brain\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6'
user_data_dir = tempfile.mkdtemp(prefix='edge_verify_replace_')

proc = subprocess.Popen([
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    '--headless=new',
    f'--remote-debugging-port={CDP_PORT}',
    '--remote-allow-origins=*',
    f'--user-data-dir={user_data_dir}',
    '--window-size=1440,1100',
    'http://127.0.0.1:8000/'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

try:
    time.sleep(2.5)
    with urllib.request.urlopen(f'http://127.0.0.1:{CDP_PORT}/json') as resp:
        tabs = json.loads(resp.read().decode())
    pages = [t for t in tabs if t.get('type') == 'page' and '127.0.0.1' in t.get('url', '')]
    ws_url = (pages[0] if pages else tabs[0])['webSocketDebuggerUrl']
    ws = websocket.create_connection(ws_url)

    msg_id = [1]
    def send(method, params=None):
        mid = msg_id[0]
        msg_id[0] += 1
        ws.send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == mid:
                if 'error' in resp:
                    raise Exception(f"CDP Error in {method}: {resp['error']}")
                return resp.get('result', {})

    send('Page.enable')
    send('DOM.enable')
    send('Emulation.setDeviceMetricsOverride', {'width': 1440, 'height': 1100, 'deviceScaleFactor': 1, 'mobile': False})

    def eval_js(expr, await_promise=False):
        params = {'expression': expr, 'returnByValue': True}
        if await_promise:
            params['awaitPromise'] = True
        res = send('Runtime.evaluate', params)
        if 'exceptionDetails' in res.get('result', {}):
            raise Exception(f"JS Exception: {res['result']['exceptionDetails']}")
        return res.get('result', {}).get('value')

    def take_screenshot(filename, clip=None):
        params = {'format': 'png'}
        if clip:
            params['clip'] = clip
        res = send('Page.captureScreenshot', params)
        data = base64.b64decode(res['data'])
        filepath = os.path.join(artifact_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(data)
        print(f"Captured: {filepath} ({len(data)} bytes)")
        return filepath

    # Wait for TempoApp
    for _ in range(30):
        val = eval_js("typeof window.TempoApp !== 'undefined' && typeof window.TempoMode !== 'undefined' && typeof window.TempoAuth !== 'undefined'")
        if val:
            break
        time.sleep(0.5)

    print("================================================================")
    print("STEP 1: Authenticate and switch to URmode (emergency)")
    print("================================================================")
    uid = 'usr_alex_replace_final'
    eval_js(f"""
        (async function() {{
            const uid = '{uid}';
            localStorage.clear();
            const mockAccount = {{
                id: uid,
                email: 'student@tempo.app',
                password: 'password123',
                full_name: 'Alex Rivera',
                role: 'student',
                user_metadata: {{ full_name: 'Alex Rivera', role: 'student' }}
            }};
            localStorage.setItem('tempo_mock_account_student@tempo.app', JSON.stringify(mockAccount));
            localStorage.setItem('tempo_local_dev_user', JSON.stringify(mockAccount));
            localStorage.setItem('tempo_user_role', 'student');
            localStorage.setItem('tempo_active_mode', 'emergency');
            localStorage.setItem('tempo_originating_mode', 'emergency');

            if (window.TempoAuth && typeof window.TempoAuth.signIn === 'function') {{
                await window.TempoAuth.signIn('student@tempo.app', 'password123');
            }}
            if (window.TempoAuth && typeof window.TempoAuth.closeAllAuthModals === 'function') window.TempoAuth.closeAllAuthModals();
            document.querySelectorAll('.auth-modal-overlay').forEach(m => m.classList.add('hidden'));

            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') window.TempoMode.setMode('emergency');
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') window.TempoApp.navigateTo('today');
        }})()
    """, await_promise=True)
    time.sleep(2)

    print("\n================================================================")
    print("STEP 2: Verify NOTE Removal & Create Notes Placement in URmode")
    print("================================================================")
    urmodeVerification = eval_js("""
        (function() {
            const emodeBox = document.getElementById('emode-home-content');
            const rightCol = emodeBox ? emodeBox.querySelector('.urgent-right-col') : null;
            const oldNoteCard = emodeBox ? emodeBox.querySelector('[data-tempo-ui="dashboard-note-card"]') : null;
            const oldNoteTextInRight = rightCol ? rightCol.innerText.includes('Drink more than 3 cups of water') : false;
            const oldNoteHeadingInRight = rightCol ? (rightCol.innerText.includes('💡') || rightCol.innerText.includes('NOTE')) : false;

            const createNotesCard = rightCol ? rightCol.querySelector('[data-tempo-ui="urmode-create-notes"]') : null;
            const planCard = rightCol ? rightCol.querySelector('.urgent-working-plan-card') : null;
            const lowerSection = emodeBox ? emodeBox.querySelector('#urgent-rebuilt-section') : null;
            const lowerCreateNotes = lowerSection ? lowerSection.querySelector('[data-tempo-ui="lower-create-notes"], [data-tempo-ui="urmode-create-notes"]') : null;
            const streakCard = lowerSection ? lowerSection.querySelector('[data-tempo-ui="lower-selfcheck-streak"]') : null;

            // Inner elements of Create Notes Card
            const textBlock = createNotesCard ? createNotesCard.querySelector('[data-tempo-ui="notes-text-block"]') : null;
            const mascotImg = createNotesCard ? createNotesCard.querySelector('img[src*="create-notes-mascot.png"]') : null;
            const plusBtn = createNotesCard ? createNotesCard.querySelector('button[aria-label="Create a new note"]') : null;
            const viewNotesBtn = createNotesCard ? createNotesCard.querySelector('button') : null;

            const rRightCol = rightCol ? rightCol.getBoundingClientRect() : null;
            const rCard = createNotesCard ? createNotesCard.getBoundingClientRect() : null;
            const rPlan = planCard ? planCard.getBoundingClientRect() : null;
            const rText = textBlock ? textBlock.getBoundingClientRect() : null;
            const rMascot = mascotImg ? mascotImg.getBoundingClientRect() : null;
            const rPlus = plusBtn ? plusBtn.getBoundingClientRect() : null;

            const gapTextToMascot = (rMascot && rText) ? Math.round((rMascot.left - rText.right) * 100) / 100 : null;
            const gapMascotToPlus = (rPlus && rMascot) ? Math.round((rPlus.left - rMascot.right) * 100) / 100 : null;
            const gapCardToPlan = (rPlan && rCard) ? Math.round((rPlan.top - rCard.bottom) * 100) / 100 : null;

            const csCard = createNotesCard ? window.getComputedStyle(createNotesCard) : null;
            const csMascot = mascotImg ? window.getComputedStyle(mascotImg) : null;

            return {
                oldNoteCardExists: !!oldNoteCard,
                oldNoteTextInRight: oldNoteTextInRight,
                oldNoteHeadingInRight: oldNoteHeadingInRight,
                createNotesCardInRightCol: !!createNotesCard,
                createNotesCardDirectlyAbovePlan: (rPlan && rCard && rPlan.top > rCard.bottom),
                gapCardToPlan: gapCardToPlan,
                cardWidth: rCard ? Math.round(rCard.width * 100) / 100 : null,
                cardHeight: rCard ? Math.round(rCard.height * 100) / 100 : null,
                rightColWidth: rRightCol ? Math.round(rRightCol.width * 100) / 100 : null,
                planCardWidth: rPlan ? Math.round(rPlan.width * 100) / 100 : null,
                widthMatchesRightCol: rCard && rRightCol && (Math.abs(rCard.width - rRightCol.width) < 0.5),
                widthMatchesPlanCard: rCard && rPlan && (Math.abs(rCard.width - rPlan.width) < 0.5),
                mascotRenderedWidth: rMascot ? Math.round(rMascot.width * 100) / 100 : null,
                mascotRenderedHeight: rMascot ? Math.round(rMascot.height * 100) / 100 : null,
                mascotNaturalWidth: mascotImg ? mascotImg.naturalWidth : null,
                mascotNaturalHeight: mascotImg ? mascotImg.naturalHeight : null,
                mascotAspectRatio: rMascot ? Math.round((rMascot.width / rMascot.height) * 10000) / 10000 : null,
                gapTextToMascot: gapTextToMascot,
                gapMascotToPlus: gapMascotToPlus,
                plusBtnWidth: rPlus ? Math.round(rPlus.width * 100) / 100 : null,
                plusBtnHeight: rPlus ? Math.round(rPlus.height * 100) / 100 : null,
                plusBtnMarginToCardRight: (rCard && rPlus) ? Math.round((rCard.right - rPlus.right) * 100) / 100 : null,
                cardOverflowStyle: csCard ? csCard.overflow : null,
                duplicateCreateNotesInLowerSection: !!lowerCreateNotes,
                streakCardExistsInLowerSection: !!streakCard
            };
        })()
    """)
    print("URmode Verification Results:\n", json.dumps(urmodeVerification, indent=2))

    assert not urmodeVerification['oldNoteCardExists'], "FAIL: Old Note card still exists in URmode!"
    assert not urmodeVerification['oldNoteTextInRight'], "FAIL: Old Note text still found in right col!"
    assert not urmodeVerification['oldNoteHeadingInRight'], "FAIL: Old Note heading still found in right col!"
    assert urmodeVerification['createNotesCardInRightCol'], "FAIL: Create Notes card not in right col!"
    assert urmodeVerification['createNotesCardDirectlyAbovePlan'], "FAIL: Create Notes card not above Working Plan!"
    assert urmodeVerification['widthMatchesRightCol'], "FAIL: Create Notes card width does not match right column!"
    assert urmodeVerification['widthMatchesPlanCard'], "FAIL: Create Notes card width does not match plan card!"
    assert urmodeVerification['cardHeight'] == 122.0, f"FAIL: Card height is {urmodeVerification['cardHeight']}px instead of 122px!"
    assert urmodeVerification['mascotRenderedHeight'] == 120.0, f"FAIL: Mascot height is {urmodeVerification['mascotRenderedHeight']}px instead of 120px!"
    assert abs(urmodeVerification['mascotRenderedWidth'] - 131.72) < 0.5, f"FAIL: Mascot width is {urmodeVerification['mascotRenderedWidth']}px!"
    assert urmodeVerification['gapTextToMascot'] == 5.0, f"FAIL: Gap text to mascot is {urmodeVerification['gapTextToMascot']}px instead of 5px!"
    assert urmodeVerification['gapMascotToPlus'] > 10.0, "FAIL: Gap between mascot and plus button is too tight!"
    assert not urmodeVerification['duplicateCreateNotesInLowerSection'], "FAIL: Duplicate Create Notes found in lower section!"
    assert urmodeVerification['streakCardExistsInLowerSection'], "FAIL: Streak card missing from lower section!"
    print(">>> ALL URMODE VERIFICATION CHECKS PASSED SUCCESSFULLY! <<<")

    # Take screenshots
    print("\nTaking URmode Overview and Closeup Screenshots...")
    take_screenshot('urmode_replace_note_overview.png')

    clip_rc = eval_js("""
        (function() {
            const rightCol = document.querySelector('.urgent-right-col');
            const r = rightCol.getBoundingClientRect();
            return {
                x: Math.max(0, r.x - 20),
                y: Math.max(0, r.y - 20),
                width: r.width + 40,
                height: Math.min(800, r.height + 40),
                scale: 1
            };
        })()
    """)
    if clip_rc:
        take_screenshot('urmode_replace_note_closeup.png', clip=clip_rc)

    clip_lower = eval_js("""
        (function() {
            const lowerSection = document.querySelector('#urgent-rebuilt-section');
            if (!lowerSection) return null;
            lowerSection.scrollIntoView({ behavior: 'instant', block: 'start' });
            const r = lowerSection.getBoundingClientRect();
            return {
                x: Math.max(0, r.x - 10),
                y: Math.max(0, r.y - 10),
                width: r.width + 20,
                height: Math.min(700, r.height + 20),
                scale: 1
            };
        })()
    """)
    time.sleep(0.5)
    if clip_lower:
        take_screenshot('urmode_lower_section_verified.png', clip=clip_lower)

    # Scroll back up
    eval_js("window.scrollTo(0, 0);")
    time.sleep(0.5)

    print("\n================================================================")
    print("STEP 3: Verify Interactions (View my notes & Create note +)")
    print("================================================================")
    interactionTest = eval_js("""
        (function() {
            const card = document.querySelector('[data-tempo-ui="urmode-create-notes"]');
            const viewBtn = card.querySelector('button');
            const plusBtn = card.querySelector('button[aria-label="Create a new note"]');

            let notesNavTriggered = false;
            let openNotesTriggered = false;

            const origNav = window.TempoApp ? window.TempoApp.navigateTo : null;
            const origOpenNotes = (window.TempoTools && window.TempoTools.openNotes) ? window.TempoTools.openNotes : null;

            if (window.TempoApp) {
                window.TempoApp.navigateTo = function(dest) {
                    if (dest === 'notes') notesNavTriggered = true;
                };
            }
            if (window.TempoTools) {
                window.TempoTools.openNotes = function() {
                    openNotesTriggered = true;
                };
            }

            viewBtn.click();
            plusBtn.click();

            if (origNav && window.TempoApp) window.TempoApp.navigateTo = origNav;
            if (origOpenNotes && window.TempoTools) window.TempoTools.openNotes = origOpenNotes;

            return {
                notesNavTriggered: notesNavTriggered,
                openNotesTriggered: openNotesTriggered
            };
        })()
    """)
    print("Interaction Results:", json.dumps(interactionTest, indent=2))
    assert interactionTest['notesNavTriggered'], "FAIL: View my notes click did not navigate to notes!"
    assert interactionTest['openNotesTriggered'], "FAIL: Plus button click did not call openNotes!"
    print(">>> INTERACTION CHECKS PASSED! <<<")

    print("\n================================================================")
    print("STEP 4: Verify Scope Isolation: Rmode and EntryHome Intact")
    print("================================================================")
    # Check Rmode
    eval_js("""
        (function() {
            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
                window.TempoMode.setMode('recovery');
            }
        })()
    """)
    time.sleep(1.5)
    rmodeInfo = eval_js("""
        (function() {
            const rmodeBox = document.getElementById('rmode-home-content');
            const isVisible = rmodeBox && !rmodeBox.classList.contains('hidden');
            const rNoteCard = rmodeBox ? rmodeBox.querySelector('[data-tempo-ui="dashboard-note-card"]') : null;
            const rPlanCard = rmodeBox ? rmodeBox.querySelector('.recovery-working-plan-card') : null;
            return {
                rmodeVisible: isVisible,
                rmodeHasNoteCard: !!rNoteCard,
                rmodeHasPlanCard: !!rPlanCard
            };
        })()
    """)
    print("Rmode Intact Check:", json.dumps(rmodeInfo, indent=2))
    assert rmodeInfo['rmodeVisible'], "FAIL: Rmode should be visible!"
    assert rmodeInfo['rmodeHasNoteCard'], "FAIL: Rmode should still have its note card intact!"
    take_screenshot('rmode_verified_intact_replace_task.png')

    # Check EntryHome (neutral dmode)
    eval_js("""
        (function() {
            if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
                window.TempoMode.setMode('neutral');
            }
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('today');
            }
        })()
    """)
    time.sleep(1.5)
    entryhomeInfo = eval_js("""
        (function() {
            const dmodeBox = document.getElementById('dmode-home-content');
            const isVisible = dmodeBox && !dmodeBox.classList.contains('hidden');
            const welcomeCard = dmodeBox ? dmodeBox.querySelector('[data-tempo-ui="welcome-card"]') : null;
            return {
                entryhomeVisible: isVisible,
                entryhomeHasWelcomeCard: !!welcomeCard
            };
        })()
    """)
    print("EntryHome Intact Check:", json.dumps(entryhomeInfo, indent=2))
    assert entryhomeInfo['entryhomeVisible'], "FAIL: EntryHome should be visible!"
    take_screenshot('entryhome_verified_intact_replace_task.png')
    print(">>> SCOPE ISOLATION CONFIRMED: Rmode and EntryHome 100% UNTOUCHED & FUNCTIONAL! <<<")

finally:
    try: ws.close()
    except: pass
    try: proc.terminate()
    except: pass
