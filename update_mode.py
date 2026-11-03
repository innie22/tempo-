import sys

with open('mode.js', 'rb') as f:
    raw = f.read()

crlf = raw.count(b'\r\n')
lf = raw.count(b'\n') - crlf
print(f"Original mode.js line endings: CRLF={crlf}, lone-LF={lf}")

content = raw.decode('utf-8')

# Target 1: in initMode
target_init = """        if (activeContext === MODES.RECOVERY) {
            if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.shouldShowFirstTimeWelcome === 'function') {
                if (window.TempoRecoverySetup.shouldShowFirstTimeWelcome()) {
                    window.TempoRecoverySetup.open(1);
                }
            }
        }"""

replacement_init = """        if (activeContext === MODES.RECOVERY) {
            if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.handleRmodeEntry === 'function') {
                window.TempoRecoverySetup.handleRmodeEntry();
            } else if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.shouldShowFirstTimeWelcome === 'function') {
                if (window.TempoRecoverySetup.shouldShowFirstTimeWelcome()) {
                    window.TempoRecoverySetup.open(1);
                }
            }
        }"""

# Target 2: in transitionContext
target_trans = """        closeAllModeDropdowns();

        if (!options.silent && window.TempoApp) {"""

replacement_trans = """        closeAllModeDropdowns();

        if (targetContext !== MODES.RECOVERY) {
            try {
                const uid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') ? (window.TempoAuth.getCurrentUserId() || 'local_user') : 'local_user';
                sessionStorage.removeItem(`tempo_rmode_session_welcomed_${uid}`);
            } catch (e) {}
        }

        if (!options.silent && window.TempoApp) {"""

# Target 3: in transitionContext post-render
target_trans_post = """        if (targetContext === MODES.RECOVERY) {
            if (!options.skipSetupCheck && window.TempoRecoverySetup && typeof window.TempoRecoverySetup.shouldShowFirstTimeWelcome === 'function') {
                if (window.TempoRecoverySetup.shouldShowFirstTimeWelcome()) {
                    window.TempoRecoverySetup.open(1);
                }
            }
        }"""

replacement_trans_post = """        if (targetContext === MODES.RECOVERY) {
            if (!options.skipSetupCheck && window.TempoRecoverySetup && typeof window.TempoRecoverySetup.handleRmodeEntry === 'function') {
                window.TempoRecoverySetup.handleRmodeEntry(options);
            } else if (!options.skipSetupCheck && window.TempoRecoverySetup && typeof window.TempoRecoverySetup.shouldShowFirstTimeWelcome === 'function') {
                if (window.TempoRecoverySetup.shouldShowFirstTimeWelcome()) {
                    window.TempoRecoverySetup.open(1);
                }
            }
        }"""

# Target 4: handleRecoveryIntroSetupClick
target_click = """    function handleRecoveryIntroSetupClick() {
        if (window.TempoRecoverySetup) {
            if (typeof window.TempoRecoverySetup.open === 'function') {
                window.TempoRecoverySetup.open(1);
            }
            if (typeof window.TempoRecoverySetup.goToStage === 'function') {
                window.TempoRecoverySetup.goToStage(1);
            }
        } else if (typeof openStrack === 'function') {
            openStrack('setup', { stage: 1 });
        }
    }"""

replacement_click = """    function handleRecoveryIntroSetupClick() {
        if (window.TempoRecoverySetup) {
            if (typeof window.TempoRecoverySetup.handleRmodeEntry === 'function') {
                window.TempoRecoverySetup.handleRmodeEntry({ force: true });
            } else if (typeof window.TempoRecoverySetup.open === 'function') {
                window.TempoRecoverySetup.open(1, { force: true });
            }
        } else if (typeof openStrack === 'function') {
            openStrack('setup', { stage: 1 });
        }
    }"""

for name, target in [('target_init', target_init), ('target_trans', target_trans), ('target_trans_post', target_trans_post), ('target_click', target_click)]:
    if target not in content:
        print(f"ERROR: {name} not found in mode.js!")
        sys.exit(1)

content = content.replace(target_init, replacement_init, 1)
content = content.replace(target_trans, replacement_trans, 1)
content = content.replace(target_trans_post, replacement_trans_post, 1)
content = content.replace(target_click, replacement_click, 1)

# Ensure strictly LF
content = content.replace('\r\n', '\n')

with open('mode.js', 'wb') as f:
    f.write(content.encode('utf-8'))

with open('mode.js', 'rb') as f:
    new_raw = f.read()

new_crlf = new_raw.count(b'\r\n')
new_lf = new_raw.count(b'\n') - new_crlf
print(f"Updated mode.js line endings: CRLF={new_crlf}, lone-LF={new_lf}")
print("Successfully updated mode.js")
