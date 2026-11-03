const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function verify() {
    const port = 9345;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', 'chrome_170_verify');
    const chrome = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

    const proc = spawn(chrome, [
        '--headless=new',
        `--remote-debugging-port=${port}`,
        `--user-data-dir=${userDataDir}`,
        '--window-size=1440,900',
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
                                    await new Promise(r => setTimeout(r, 100));
                                }
                                await new Promise(r => setTimeout(r, 300));
                            })()`
                        });

                        const metrics = await send('Runtime.evaluate', {
                            returnByValue: true,
                            expression: `(() => {
                                const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                const text = card.children[0];
                                const img = card.querySelector('img');
                                const h2 = text.querySelector('h2');
                                const p = text.querySelector('p');

                                const cR = card.getBoundingClientRect();
                                const tR = text.getBoundingClientRect();
                                const iR = img.getBoundingClientRect();
                                const hR = h2.getBoundingClientRect();
                                const pR = p.getBoundingClientRect();

                                const h2Style = window.getComputedStyle(h2);
                                const pStyle = window.getComputedStyle(p);
                                const imgStyle = window.getComputedStyle(img);
                                const cardStyle = window.getComputedStyle(card);

                                return {
                                    card: {
                                        width: Math.round(cR.width * 100) / 100,
                                        height: Math.round(cR.height * 100) / 100,
                                        backgroundColor: cardStyle.backgroundColor,
                                        border: cardStyle.border
                                    },
                                    mascot: {
                                        renderedWidth: Math.round(iR.width * 100) / 100,
                                        renderedHeight: Math.round(iR.height * 100) / 100,
                                        isHeightExactly170: Math.abs(iR.height - 170) < 0.5,
                                        aspectRatio: Math.round((iR.width / iR.height) * 1000) / 1000,
                                        naturalWidth: img.naturalWidth,
                                        naturalHeight: img.naturalHeight,
                                        naturalAspectRatio: Math.round((img.naturalWidth / img.naturalHeight) * 1000) / 1000,
                                        isProportional: Math.abs((iR.width / iR.height) - (img.naturalWidth / img.naturalHeight)) < 0.01,
                                        objectFit: imgStyle.objectFit,
                                        position: imgStyle.position,
                                        bottom: imgStyle.bottom,
                                        right: imgStyle.right,
                                        topDistFromCardTop: Math.round((iR.top - cR.top) * 100) / 100,
                                        bottomDistFromCardBottom: Math.round((cR.bottom - iR.bottom) * 100) / 100,
                                        rightDistFromCardRight: Math.round((cR.right - iR.right) * 100) / 100,
                                        isClipped: (iR.right > cR.right || iR.left < cR.left || iR.bottom > cR.bottom || iR.top < cR.top)
                                    },
                                    text: {
                                        h2FontSize: h2Style.fontSize,
                                        pFontSize: pStyle.fontSize,
                                        h2FontWeight: h2Style.fontWeight,
                                        h2Color: h2Style.color,
                                        pColor: pStyle.color,
                                        textWidth: Math.round(tR.width * 100) / 100,
                                        textHeight: Math.round(tR.height * 100) / 100,
                                        hasVerticalOverflow: (tR.bottom > cR.bottom || tR.top < cR.top),
                                        horizontalGapToMascot: Math.round((iR.left - tR.right) * 100) / 100
                                    }
                                };
                            })()`
                        });

                        console.log('=== METRICS (170px MASCOT) ===');
                        console.log(JSON.stringify(metrics.result.value, null, 2));

                        // Scroll into view
                        await send('Runtime.evaluate', {
                            expression: `document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0].scrollIntoView({ block: 'center' });`
                        });
                        await new Promise(r => setTimeout(r, 400));

                        // Desktop closeup
                        const cClip = await send('Runtime.evaluate', {
                            returnByValue: true,
                            expression: `(() => {
                                const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                const r = card.getBoundingClientRect();
                                const pageY = r.top + window.scrollY;
                                const pageX = r.left + window.scrollX;
                                return { x: Math.max(0, pageX - 10), y: Math.max(0, pageY - 10), width: r.width + 20, height: r.height + 20, scale: 1 };
                            })()`
                        });
                        const cShot = await send('Page.captureScreenshot', { format: 'png', clip: cClip.result.value });
                        fs.writeFileSync(path.join(ARTIFACT_DIR, 'self_check_170px_closeup.png'), Buffer.from(cShot.data, 'base64'));

                        // Desktop row
                        const rClip = await send('Runtime.evaluate', {
                            returnByValue: true,
                            expression: `(() => {
                                const sec = document.querySelector('[data-tempo-ui="entry-lower-section"]');
                                const r = sec.getBoundingClientRect();
                                const pageY = r.top + window.scrollY;
                                const pageX = r.left + window.scrollX;
                                return { x: Math.max(0, pageX - 10), y: Math.max(0, pageY - 10), width: r.width + 20, height: r.height + 20, scale: 1 };
                            })()`
                        });
                        const rShot = await send('Page.captureScreenshot', { format: 'png', clip: rClip.result.value });
                        fs.writeFileSync(path.join(ARTIFACT_DIR, 'three_lower_cards_170px.png'), Buffer.from(rShot.data, 'base64'));

                        // Full desktop page
                        const fullShot = await send('Page.captureScreenshot', { format: 'png' });
                        fs.writeFileSync(path.join(ARTIFACT_DIR, 'entry_home_170px_desktop.png'), Buffer.from(fullShot.data, 'base64'));

                        ws.close();
                        proc.kill();
                        resolve();
                    };
                } catch (e) {
                    proc.kill();
                    reject(e);
                }
            });
        }).on('error', err => {
            proc.kill();
            reject(err);
        });
    });
}

verify().catch(console.error);
