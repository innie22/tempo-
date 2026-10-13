const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function testLayouts() {
    const port = 9590;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', 'chrome_test_layouts');
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

                        // Scroll lower section into view
                        await send('Runtime.evaluate', {
                            expression: `document.querySelector('[data-tempo-ui="entry-lower-section"]')?.scrollIntoView({ block: 'center' });`
                        });
                        await new Promise(r => setTimeout(r, 400));

                        // Define trial configurations
                        const trials = [
                            {
                                name: 'trial1_flex_row',
                                fn: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    card.className = "bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-5 flex flex-row items-center justify-between shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group";
                                    const textContainer = card.children[0];
                                    textContainer.className = "relative z-10 flex-1 max-w-[190px] pr-2";
                                    const h2 = textContainer.querySelector('h2');
                                    h2.className = "text-[34px] font-extrabold text-[#527668] leading-[1.1] mb-1.5";
                                    const p = textContainer.querySelector('p');
                                    p.className = "text-[24px] text-[#628A7A] leading-snug";
                                    const img = card.querySelector('img');
                                    img.className = "h-[190px] w-auto object-contain select-none pointer-events-none shrink-0 -mr-3";
                                })()`
                            },
                            {
                                name: 'trial2_absolute_mascot',
                                fn: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    card.className = "bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-5 flex flex-col justify-center shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group";
                                    const textContainer = card.children[0];
                                    textContainer.className = "relative z-10 max-w-[175px]";
                                    const h2 = textContainer.querySelector('h2');
                                    h2.className = "text-[34px] font-extrabold text-[#527668] leading-[1.1] mb-1.5";
                                    const p = textContainer.querySelector('p');
                                    p.className = "text-[24px] text-[#628A7A] leading-[1.2]";
                                    const img = card.querySelector('img');
                                    img.className = "h-[190px] w-auto object-contain select-none pointer-events-none absolute -bottom-1 -right-6";
                                })()`
                            },
                            {
                                name: 'trial3_balanced_flex',
                                fn: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    card.className = "bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-5 flex items-center justify-between gap-2 shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group";
                                    const textContainer = card.children[0];
                                    textContainer.className = "relative z-10 flex-1 min-w-0";
                                    const h2 = textContainer.querySelector('h2');
                                    h2.className = "text-[34px] font-extrabold text-[#527668] leading-[1.1] mb-1";
                                    const p = textContainer.querySelector('p');
                                    p.className = "text-[24px] text-[#628A7A] leading-[1.2]";
                                    const img = card.querySelector('img');
                                    img.className = "h-[190px] w-auto object-contain select-none pointer-events-none shrink-0 -mr-4";
                                })()`
                            }
                        ];

                        for (const t of trials) {
                            await send('Runtime.evaluate', { expression: t.fn });
                            await new Promise(r => setTimeout(r, 200));

                            const metrics = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    const textContainer = card.children[0];
                                    const img = card.querySelector('img');
                                    const h2 = card.querySelector('h2');
                                    const p = card.querySelector('p');

                                    const cR = card.getBoundingClientRect();
                                    const tR = textContainer.getBoundingClientRect();
                                    const iR = img.getBoundingClientRect();
                                    const hR = h2.getBoundingClientRect();
                                    const pR = p.getBoundingClientRect();

                                    const overlapX = Math.max(0, Math.min(tR.right, iR.right) - Math.max(tR.left, iR.left));
                                    const overlapY = Math.max(0, Math.min(tR.bottom, iR.bottom) - Math.max(tR.top, iR.top));
                                    const isOverlapping = (overlapX > 0 && overlapY > 0);

                                    return {
                                        card: { width: cR.width, height: cR.height },
                                        textContainer: { top: tR.top, bottom: tR.bottom, left: tR.left, right: tR.right, width: tR.width, height: tR.height },
                                        mascot: { top: iR.top, bottom: iR.bottom, left: iR.left, right: iR.right, width: iR.width, height: iR.height },
                                        h2: { fontSize: window.getComputedStyle(h2).fontSize, height: hR.height },
                                        p: { fontSize: window.getComputedStyle(p).fontSize, height: pR.height },
                                        overlapX,
                                        overlapY,
                                        isOverlapping,
                                        gapBetweenTextAndMascot: iR.left - tR.right,
                                        verticalOverflow: tR.bottom > cR.bottom
                                    };
                                })()`
                            });
                            console.log('=== ' + t.name + ' ===');
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
                            fs.writeFileSync(path.join(ARTIFACT_DIR, `${t.name}.png`), Buffer.from(shot.data, 'base64'));
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

testLayouts().catch(console.error);
