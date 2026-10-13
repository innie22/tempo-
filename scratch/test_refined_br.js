const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function testRefinedBR() {
    const port = 9360;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', 'chrome_refined_br');
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

                        const configs = [
                            {
                                id: 'br_optA_w158_bottom0_right0',
                                textWidth: 'w-[158px]',
                                imgClass: 'h-[180px] w-auto object-contain select-none pointer-events-none absolute bottom-0 right-0'
                            },
                            {
                                id: 'br_optB_w160_bottom0_right0',
                                textWidth: 'w-[160px]',
                                imgClass: 'h-[180px] w-auto object-contain select-none pointer-events-none absolute bottom-0 right-0'
                            },
                            {
                                id: 'br_optC_w158_bottom_minus1_right_minus1',
                                textWidth: 'w-[158px]',
                                imgClass: 'h-[180px] w-auto object-contain select-none pointer-events-none absolute -bottom-1 -right-1'
                            }
                        ];

                        for (const c of configs) {
                            await send('Runtime.evaluate', {
                                expression: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    card.className = "bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-5 flex flex-col justify-between shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group";
                                    const text = card.children[0];
                                    text.className = "relative z-10 ${c.textWidth} shrink-0";
                                    const img = card.querySelector('img');
                                    img.className = "${c.imgClass}";
                                })()`
                            });
                            await new Promise(r => setTimeout(r, 200));

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

                                    const overlapX = Math.max(0, Math.min(tR.right, iR.right) - Math.max(tR.left, iR.left));
                                    const overlapY = Math.max(0, Math.min(tR.bottom, iR.bottom) - Math.max(tR.top, iR.top));

                                    return {
                                        card: { width: cR.width, height: cR.height },
                                        mascot: {
                                            topMargin: iR.top - cR.top,
                                            bottomMargin: cR.bottom - iR.bottom,
                                            rightMargin: cR.right - iR.right,
                                            leftMargin: iR.left - cR.left,
                                            height: iR.height,
                                            width: iR.width
                                        },
                                        text: {
                                            topMargin: tR.top - cR.top,
                                            bottomMargin: cR.bottom - tR.bottom,
                                            width: tR.width,
                                            height: tR.height
                                        },
                                        gapBetweenTextAndMascot: iR.left - tR.right,
                                        hasOverlap: (overlapX > 0 && overlapY > 0),
                                        overlapX,
                                        overlapY
                                    };
                                })()`
                            });

                            console.log('=== ' + c.id + ' ===');
                            console.log(JSON.stringify(metrics.result.value, null, 2));

                            const clip = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    const rect = card.getBoundingClientRect();
                                    const pageY = rect.top + window.scrollY;
                                    const pageX = rect.left + window.scrollX;
                                    return { x: Math.max(0, pageX - 10), y: Math.max(0, pageY - 10), width: rect.width + 20, height: rect.height + 20, scale: 1 };
                                })()`
                            });
                            const shot = await send('Page.captureScreenshot', { format: 'png', clip: clip.result.value });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, `${c.id}.png`), Buffer.from(shot.data, 'base64'));

                            // Row screenshot
                            const rowClip = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const sec = document.querySelector('[data-tempo-ui="entry-lower-section"]');
                                    const rect = sec.getBoundingClientRect();
                                    const pageY = rect.top + window.scrollY;
                                    const pageX = rect.left + window.scrollX;
                                    return { x: Math.max(0, pageX - 10), y: Math.max(0, pageY - 10), width: rect.width + 20, height: rect.height + 20, scale: 1 };
                                })()`
                            });
                            const rowShot = await send('Page.captureScreenshot', { format: 'png', clip: rowClip.result.value });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, `${c.id}_row.png`), Buffer.from(rowShot.data, 'base64'));
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

testRefinedBR().catch(console.error);
