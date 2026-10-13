const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function testViewport(vw, vh, port, isCapture = false) {
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', `chrome_data_vp_${vw}`);
    const chrome = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

    const proc = spawn(chrome, [
        '--headless=new',
        `--remote-debugging-port=${port}`,
        `--user-data-dir=${userDataDir}`,
        `--window-size=${vw},${vh}`,
        'http://localhost:8000/'
    ]);

    await new Promise(r => setTimeout(r, 2000));

    return new Promise((resolve, reject) => {
        http.get(`http://127.0.0.1:${port}/json`, (res) => {
            let raw = '';
            res.on('data', c => raw += c);
            res.on('end', async () => {
                try {
                    const tabs = JSON.parse(raw);
                    const tab = tabs.find(t => t.type === 'page');
                    const ws = new WebSocket(tab.webSocketDebuggerUrl);

                    let msgId = 1;
                    function send(method, params = {}) {
                        return new Promise(resSend => {
                            const id = msgId++;
                            const handler = evt => {
                                const d = JSON.parse(evt.data);
                                if (d.id === id) {
                                    ws.removeEventListener('message', handler);
                                    resSend(d.result);
                                }
                            };
                            ws.addEventListener('message', handler);
                            ws.send(JSON.stringify({ id, method, params }));
                        });
                    }

                    ws.onopen = async () => {
                        await send('Runtime.evaluate', {
                            awaitPromise: true,
                            expression: `(async () => {
                                for (let i = 0; i < 50; i++) {
                                    const breathing = document.querySelector('[title="Practice Breathing"]');
                                    if (breathing) break;
                                    await new Promise(r => setTimeout(r, 200));
                                }
                            })()`
                        });

                        const res = await send('Runtime.evaluate', {
                            returnByValue: true,
                            expression: `(() => {
                                const card = document.querySelector('[title="Practice Breathing"]');
                                const h3 = card.querySelector('h3');
                                const p = card.querySelector('p');
                                const img = card.querySelector('img');

                                const cR = card.getBoundingClientRect();
                                const hR = h3.getBoundingClientRect();
                                const pR = p.getBoundingClientRect();
                                const iR = img.getBoundingClientRect();

                                return {
                                    vw: window.innerWidth,
                                    vh: window.innerHeight,
                                    cardWidth: cR.width,
                                    cardHeight: cR.height,
                                    headingText: h3.innerText,
                                    headingLines: h3.getClientRects().length,
                                    headingWidth: hR.width,
                                    headingRight: hR.right,
                                    mascotLeft: iR.left,
                                    gapBetweenHeadingAndMascot: iR.left - hR.right,
                                    fontSize: window.getComputedStyle(h3).fontSize,
                                    whiteSpace: window.getComputedStyle(h3).whiteSpace
                                };
                            })()`
                        });

                        console.log(`Viewport ${vw}x${vh}:`, JSON.stringify(res.result.value, null, 2));

                        if (isCapture) {
                            const card = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const el = document.querySelector('[title="Practice Breathing"]');
                                    el.scrollIntoView({ block: 'center' });
                                    const r = el.getBoundingClientRect();
                                    const pageY = r.top + window.scrollY;
                                    const pageX = r.left + window.scrollX;
                                    return { x: Math.max(0, pageX - 10), y: Math.max(0, pageY - 10), width: r.width + 20, height: r.height + 20, scale: 1 };
                                })()`
                            });
                            await new Promise(r => setTimeout(r, 300));
                            const shot = await send('Page.captureScreenshot', { format: 'png', clip: card.result.value });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, `breathing_card_${vw}.png`), Buffer.from(shot.data, 'base64'));
                        }

                        ws.close();
                        proc.kill();
                        resolve(res.result.value);
                    };
                } catch (err) {
                    proc.kill();
                    reject(err);
                }
            });
        }).on('error', (err) => {
            proc.kill();
            reject(err);
        });
    });
}

async function runAll() {
    await testViewport(1440, 900, 9310, true);
    await testViewport(1280, 800, 9311, true);
    await testViewport(1024, 768, 9312, true);
    await testViewport(768, 1024, 9313, false);
    await testViewport(390, 844, 9314, true);
    console.log('Done testing all viewports.');
}

runAll().catch(console.error);
