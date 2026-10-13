const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function testLineHeights() {
    const port = 9335;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', 'chrome_lh_test');
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
                                    if (card && img && img.complete) break;
                                    await new Promise(r => setTimeout(r, 100));
                                }
                            })()`
                        });

                        await send('Runtime.evaluate', {
                            expression: `document.querySelector('[data-tempo-ui="entry-lower-section"]')?.scrollIntoView({ block: 'center' });`
                        });
                        await new Promise(r => setTimeout(r, 400));

                        const trials = [
                            {
                                id: 'lh_120',
                                lhClass: 'leading-[1.2]',
                                desc: 'line-height: 1.2 (approx 34.8px)'
                            },
                            {
                                id: 'lh_122',
                                lhClass: 'leading-[1.22]',
                                desc: 'line-height: 1.22 (approx 35.4px)'
                            },
                            {
                                id: 'lh_125',
                                lhClass: 'leading-[1.25]',
                                desc: 'line-height: 1.25 (approx 36.25px)'
                            }
                        ];

                        for (const t of trials) {
                            await send('Runtime.evaluate', {
                                expression: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    const h2 = card.querySelector('h2');
                                    h2.className = "text-[29px] font-extrabold text-[#527668] ${t.lhClass} mb-1.5 tracking-tight";
                                })()`
                            });
                            await new Promise(r => setTimeout(r, 200));

                            const metrics = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    const text = card.children[0];
                                    const h2 = text.querySelector('h2');
                                    const p = text.querySelector('p');
                                    const img = card.querySelector('img');

                                    const cR = card.getBoundingClientRect();
                                    const tR = text.getBoundingClientRect();
                                    const hR = h2.getBoundingClientRect();
                                    const pR = p.getBoundingClientRect();
                                    const iR = img.getBoundingClientRect();

                                    const h2Style = window.getComputedStyle(h2);
                                    const pStyle = window.getComputedStyle(p);

                                    const fontSizePx = parseFloat(h2Style.fontSize);
                                    const lineHeightPx = parseFloat(h2Style.lineHeight);
                                    const ratio = Math.round((lineHeightPx / fontSizePx) * 1000) / 1000;

                                    return {
                                        fontSize: h2Style.fontSize,
                                        computedLineHeight: h2Style.lineHeight,
                                        lineHeightRatio: ratio,
                                        h2Height: Math.round(hR.height * 100) / 100,
                                        h2Lines: Math.round(hR.height / lineHeightPx),
                                        gapH2ToDescription: Math.round((pR.top - hR.bottom) * 100) / 100,
                                        textTotalHeight: Math.round(tR.height * 100) / 100,
                                        cardHeight: cR.height,
                                        bottomRemainingSpace: Math.round((cR.bottom - tR.bottom) * 100) / 100,
                                        hasCollision: pR.top < hR.bottom
                                    };
                                })()`
                            });

                            console.log('=== ' + t.id + ' (' + t.desc + ') ===');
                            console.log(JSON.stringify(metrics.result.value, null, 2));

                            const clip = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    const r = card.getBoundingClientRect();
                                    const pageY = r.top + window.scrollY;
                                    const pageX = r.left + window.scrollX;
                                    return { x: Math.max(0, pageX - 10), y: Math.max(0, pageY - 10), width: r.width + 20, height: r.height + 20, scale: 1 };
                                })()`
                            });
                            const shot = await send('Page.captureScreenshot', { format: 'png', clip: clip.result.value });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, `${t.id}.png`), Buffer.from(shot.data, 'base64'));
                        }

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

testLineHeights().catch(console.error);
