const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function verify() {
    const port = 9325;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', 'chrome_heading_refine');
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

                                const fSize = parseFloat(h2Style.fontSize);
                                const lHeight = parseFloat(h2Style.lineHeight);
                                const relativeRatio = Math.round((lHeight / fSize) * 1000) / 1000;

                                return {
                                    heading: {
                                        fontSize: h2Style.fontSize,
                                        computedLineHeight: h2Style.lineHeight,
                                        relativeLineHeightRatio: relativeRatio,
                                        fontWeight: h2Style.fontWeight,
                                        color: h2Style.color,
                                        renderedHeight: Math.round(hR.height * 100) / 100,
                                        lineCount: Math.round(hR.height / lHeight),
                                        isInTargetRange: (relativeRatio >= 1.2 && relativeRatio <= 1.25)
                                    },
                                    spacingAndCollision: {
                                        gapBetweenHeadingAndDescription: Math.round((pR.top - hR.bottom) * 100) / 100,
                                        hasCollision: pR.top < hR.bottom,
                                        cardHeight: cR.height,
                                        textTotalHeight: Math.round(tR.height * 100) / 100,
                                        bottomRemainingSpace: Math.round((cR.bottom - tR.bottom) * 100) / 100
                                    },
                                    mascot: {
                                        height: Math.round(iR.height * 100) / 100,
                                        width: Math.round(iR.width * 100) / 100,
                                        position: imgStyle.position,
                                        bottom: imgStyle.bottom,
                                        right: imgStyle.right
                                    }
                                };
                            })()`
                        });

                        console.log('=== HEADING REFINEMENT VERIFICATION ===');
                        console.log(JSON.stringify(metrics.result.value, null, 2));

                        // Scroll into view
                        await send('Runtime.evaluate', {
                            expression: `document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0].scrollIntoView({ block: 'center' });`
                        });
                        await new Promise(r => setTimeout(r, 400));

                        // Closeup
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
                        fs.writeFileSync(path.join(ARTIFACT_DIR, 'self_check_heading_refined_closeup.png'), Buffer.from(cShot.data, 'base64'));

                        // Row
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
                        fs.writeFileSync(path.join(ARTIFACT_DIR, 'three_lower_cards_heading_refined.png'), Buffer.from(rShot.data, 'base64'));

                        // Desktop page
                        const fullShot = await send('Page.captureScreenshot', { format: 'png' });
                        fs.writeFileSync(path.join(ARTIFACT_DIR, 'entry_home_desktop_heading_refined.png'), Buffer.from(fullShot.data, 'base64'));

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
