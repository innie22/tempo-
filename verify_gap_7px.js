const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function main() {
    const chrome = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
    const proc = spawn(chrome, [
        '--headless=new',
        '--remote-debugging-port=9301',
        '--user-data-dir=C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\\scratch\\chrome_user_data_gap_verify',
        '--window-size=1440,900',
        'http://localhost:8000/'
    ]);

    await new Promise(r => setTimeout(r, 2000));

    http.get('http://127.0.0.1:9301/json', (res) => {
        let raw = '';
        res.on('data', c => raw += c);
        res.on('end', async () => {
            const tabs = JSON.parse(raw);
            const tab = tabs.find(t => t.type === 'page');
            const ws = new WebSocket(tab.webSocketDebuggerUrl);

            let msgId = 1;
            function send(method, params = {}) {
                return new Promise(resolve => {
                    const id = msgId++;
                    const handler = evt => {
                        const d = JSON.parse(evt.data);
                        if (d.id === id) {
                            ws.removeEventListener('message', handler);
                            resolve(d.result);
                        }
                    };
                    ws.addEventListener('message', handler);
                    ws.send(JSON.stringify({ id, method, params }));
                });
            }

            ws.onopen = async () => {
                // Wait for community panel and breathing card
                await send('Runtime.evaluate', {
                    awaitPromise: true,
                    expression: `(async () => {
                        for (let i = 0; i < 50; i++) {
                            const panel = document.querySelector('[data-tempo-ui="entry-community-panel"]');
                            const breathing = document.querySelector('[title="Practice Breathing"]');
                            if (panel && breathing) break;
                            await new Promise(r => setTimeout(r, 200));
                        }
                        await new Promise(r => setTimeout(r, 600));
                    })()`
                });

                // Measure live metrics and exact gap
                const data = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        const panel = document.querySelector('[data-tempo-ui="entry-community-panel"]');
                        const breathing = document.querySelector('[title="Practice Breathing"]');
                        const parent = panel.parentElement;

                        const panelR = panel.getBoundingClientRect();
                        const breathingR = breathing.getBoundingClientRect();
                        const parentR = parent.getBoundingClientRect();

                        const pStyle = window.getComputedStyle(parent);
                        const bStyle = window.getComputedStyle(breathing);

                        const gap = breathingR.top - panelR.bottom;

                        return {
                            parentClassName: parent.className,
                            parentSpacingStyle: pStyle.rowGap || pStyle.gap,
                            breathingMarginTop: bStyle.marginTop,
                            panelRect: {
                                top: panelR.top,
                                bottom: panelR.bottom,
                                height: panelR.height
                            },
                            breathingRect: {
                                top: breathingR.top,
                                bottom: breathingR.bottom,
                                height: breathingR.height
                            },
                            measuredVerticalGapPx: gap
                        };
                    })()`
                });

                console.log('=== GAP MEASUREMENT RESULTS ===');
                console.log(JSON.stringify(data.result.value, null, 2));

                // Capture close-up screenshot of both sections showing the gap
                const rightColClip = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        const panel = document.querySelector('[data-tempo-ui="entry-community-panel"]');
                        const breathing = document.querySelector('[title="Practice Breathing"]');
                        const r1 = panel.getBoundingClientRect();
                        const r2 = breathing.getBoundingClientRect();
                        const top = Math.min(r1.top, r2.top) - 10;
                        const bottom = Math.max(r1.bottom, r2.bottom) + 10;
                        const left = Math.min(r1.left, r2.left) - 10;
                        const right = Math.max(r1.right, r2.right) + 10;
                        return { x: left, y: top, width: right - left, height: bottom - top, scale: 1 };
                    })()`
                });
                const colShot = await send('Page.captureScreenshot', { format: 'png', clip: rightColClip.result.value });
                fs.writeFileSync(path.join(ARTIFACT_DIR, 'community_breathing_gap_7px.png'), Buffer.from(colShot.data, 'base64'));

                // Capture desktop overview
                const heroClip = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        return { x: 0, y: 0, width: 1440, height: 860, scale: 1 };
                    })()`
                });
                const heroShot = await send('Page.captureScreenshot', { format: 'png', clip: heroClip.result.value });
                fs.writeFileSync(path.join(ARTIFACT_DIR, 'community_breathing_desktop_7px.png'), Buffer.from(heroShot.data, 'base64'));

                ws.close();
                proc.kill();
                process.exit(0);
            };
        });
    });
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
