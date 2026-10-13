const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function explore() {
    const port = 9790;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', 'chrome_explore');
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
                        const configs = [
                            {
                                id: 'optA_p4_w180_absRight',
                                desc: 'Card p-4, text w-[180px], mascot absolute -right-3 -bottom-1',
                                setup: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    card.className = "bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-4 flex flex-col justify-between shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group";
                                    const text = card.children[0];
                                    text.className = "relative z-10 w-[180px]";
                                    const h2 = text.querySelector('h2');
                                    h2.className = "text-[34px] font-extrabold text-[#527668] leading-[1.08] mb-1 tracking-tight";
                                    const p = text.querySelector('p');
                                    p.className = "text-[24px] text-[#628A7A] leading-[1.18] tracking-tight";
                                    const img = card.querySelector('img');
                                    img.className = "h-[190px] w-auto object-contain select-none pointer-events-none absolute -bottom-1 -right-3";
                                })()`
                            },
                            {
                                id: 'optB_p4_w185_absRight_offset',
                                desc: 'Card p-4, text w-[185px], mascot absolute -right-6 -bottom-0',
                                setup: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    card.className = "bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-4 flex flex-col justify-center shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group";
                                    const text = card.children[0];
                                    text.className = "relative z-10 w-[185px]";
                                    const h2 = text.querySelector('h2');
                                    h2.className = "text-[34px] font-extrabold text-[#527668] leading-[1.08] mb-1.5 tracking-tight";
                                    const p = text.querySelector('p');
                                    p.className = "text-[24px] text-[#628A7A] leading-[1.18] tracking-tight";
                                    const img = card.querySelector('img');
                                    img.className = "h-[190px] w-auto object-contain select-none pointer-events-none absolute bottom-0 -right-6";
                                })()`
                            },
                            {
                                id: 'optC_p45_w175_absRight_offset',
                                desc: 'Card p-4.5, text w-[170px], mascot absolute -right-8 bottom-0',
                                setup: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    card.className = "bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-4.5 flex flex-col justify-center shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group";
                                    const text = card.children[0];
                                    text.className = "relative z-10 w-[170px]";
                                    const h2 = text.querySelector('h2');
                                    h2.className = "text-[34px] font-extrabold text-[#527668] leading-[1.08] mb-1 tracking-tight";
                                    const p = text.querySelector('p');
                                    p.className = "text-[24px] text-[#628A7A] leading-[1.18] tracking-tight";
                                    const img = card.querySelector('img');
                                    img.className = "h-[190px] w-auto object-contain select-none pointer-events-none absolute bottom-0 -right-8";
                                })()`
                            },
                            {
                                id: 'optD_flex_row_justify_between',
                                desc: 'Card p-4 flex flex-row items-center, text w-[175px], mascot shrink-0 h-[190px] -mr-8',
                                setup: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    card.className = "bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-4 flex flex-row items-center justify-between shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group";
                                    const text = card.children[0];
                                    text.className = "relative z-10 w-[175px] shrink-0";
                                    const h2 = text.querySelector('h2');
                                    h2.className = "text-[34px] font-extrabold text-[#527668] leading-[1.08] mb-1.5 tracking-tight";
                                    const p = text.querySelector('p');
                                    p.className = "text-[24px] text-[#628A7A] leading-[1.18] tracking-tight";
                                    const img = card.querySelector('img');
                                    img.className = "h-[190px] w-auto object-contain select-none pointer-events-none shrink-0 -mr-8";
                                })()`
                            }
                        ];

                        for (const c of configs) {
                            await send('Runtime.evaluate', { expression: c.setup });
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

                                    // Let's also check distance from right edge of text to left edge of mascot
                                    const horizontalGap = iR.left - tR.right;

                                    return {
                                        cardHeight: cR.height,
                                        cardWidth: cR.width,
                                        textWidth: tR.width,
                                        textHeight: tR.height,
                                        mascotHeight: iR.height,
                                        mascotWidth: iR.width,
                                        horizontalGap,
                                        overlapX,
                                        overlapY,
                                        hasOverlap: (overlapX > 0 && overlapY > 0),
                                        verticalOverflow: (tR.bottom > cR.bottom || tR.top < cR.top),
                                        h2Lines: Math.round(hR.height / 36),
                                        pLines: Math.round(pR.height / 28)
                                    };
                                })()`
                            });

                            console.log('=== ' + c.id + ' ===');
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
                            fs.writeFileSync(path.join(ARTIFACT_DIR, `${c.id}.png`), Buffer.from(shot.data, 'base64'));
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

explore().catch(console.error);
