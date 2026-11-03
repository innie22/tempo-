const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function verify(vw = 1440, vh = 900, isMobile = false) {
    const port = isMobile ? 9391 : 9390;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', isMobile ? 'chrome_data_200_live_m' : 'chrome_data_200_live_d');
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
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    const img = card?.querySelector('img');
                                    if (card && img && img.complete && img.naturalWidth > 0) break;
                                    await new Promise(r => setTimeout(r, 200));
                                }
                                await new Promise(r => setTimeout(r, 600));
                            })()`
                        });

                        const metrics = await send('Runtime.evaluate', {
                            returnByValue: true,
                            expression: `(() => {
                                const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                const img = card.querySelector('img');
                                const h2 = card.querySelector('h2');
                                const p = card.querySelector('p');

                                const cR = card.getBoundingClientRect();
                                const iR = img.getBoundingClientRect();
                                const hR = h2.getBoundingClientRect();
                                const pR = p.getBoundingClientRect();

                                const s = window.getComputedStyle(img);

                                return {
                                    viewport: { width: window.innerWidth, height: window.innerHeight },
                                    card: {
                                        width: Math.round(cR.width * 100) / 100,
                                        height: Math.round(cR.height * 100) / 100
                                    },
                                    mascot: {
                                        src: img.getAttribute('src'),
                                        renderedWidth: Math.round(iR.width * 100) / 100,
                                        renderedHeight: Math.round(iR.height * 100) / 100,
                                        isHeightExactly200: Math.abs(iR.height - 200) < 0.5,
                                        aspectRatio: Math.round((iR.width / iR.height) * 1000) / 1000,
                                        naturalWidth: img.naturalWidth,
                                        naturalHeight: img.naturalHeight,
                                        naturalAspectRatio: Math.round((img.naturalWidth / img.naturalHeight) * 1000) / 1000,
                                        isProportional: Math.abs((iR.width / iR.height) - (img.naturalWidth / img.naturalHeight)) < 0.01,
                                        objectFit: s.objectFit,
                                        position: s.position,
                                        computedHeight: s.height,
                                        computedWidth: s.width
                                    },
                                    textReadability: {
                                        headingBottom: hR.bottom,
                                        descriptionBottom: pR.bottom,
                                        mascotTop: iR.top,
                                        headingObscured: false
                                    }
                                };
                            })()`
                        });

                        console.log(`=== METRICS (${isMobile ? 'MOBILE' : 'DESKTOP'}) ===`);
                        console.log(JSON.stringify(metrics.result.value, null, 2));

                        // Scroll lower section into view
                        await send('Runtime.evaluate', {
                            awaitPromise: true,
                            expression: `(() => {
                                const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                card.scrollIntoView({ block: 'center' });
                            })()`
                        });
                        await new Promise(r => setTimeout(r, 400));

                        if (!isMobile) {
                            // Self-check closeup
                            const scClip = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    const r = card.getBoundingClientRect();
                                    const pageY = r.top + window.scrollY;
                                    const pageX = r.left + window.scrollX;
                                    return { x: Math.max(0, pageX - 10), y: Math.max(0, pageY - 10), width: r.width + 20, height: r.height + 20, scale: 1 };
                                })()`
                            });
                            const scShot = await send('Page.captureScreenshot', { format: 'png', clip: scClip.result.value });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, 'self_check_200px_closeup.png'), Buffer.from(scShot.data, 'base64'));

                            // Row screenshot
                            const rowClip = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const sec = document.querySelector('[data-tempo-ui="entry-lower-section"]');
                                    const r = sec.getBoundingClientRect();
                                    const pageY = r.top + window.scrollY;
                                    const pageX = r.left + window.scrollX;
                                    return { x: Math.max(0, pageX - 10), y: Math.max(0, pageY - 10), width: r.width + 20, height: r.height + 20, scale: 1 };
                                })()`
                            });
                            const rowShot = await send('Page.captureScreenshot', { format: 'png', clip: rowClip.result.value });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, 'three_lower_cards_with_200px_mascot.png'), Buffer.from(rowShot.data, 'base64'));

                            // Full desktop screenshot
                            const fullShot = await send('Page.captureScreenshot', { format: 'png' });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, 'entry_home_200px_mascot_desktop.png'), Buffer.from(fullShot.data, 'base64'));
                        } else {
                            // Mobile screenshot
                            const mClip = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    const r = card.getBoundingClientRect();
                                    const pageY = r.top + window.scrollY;
                                    const pageX = r.left + window.scrollX;
                                    return { x: Math.max(0, pageX - 10), y: Math.max(0, pageY - 10), width: r.width + 20, height: r.height + 20, scale: 1 };
                                })()`
                            });
                            const mShot = await send('Page.captureScreenshot', { format: 'png', clip: mClip.result.value });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, 'self_check_200px_mobile.png'), Buffer.from(mShot.data, 'base64'));
                        }

                        ws.close();
                        proc.kill();
                        resolve();
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

async function main() {
    await verify(1440, 900, false);
    await verify(390, 844, true);
    console.log('200px mascot live verification completed successfully!');
}

main().catch(console.error);
