const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function findOptimal() {
    const port = 9395;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', 'chrome_find_optimal');
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

                        const candidates = [
                            {
                                id: 'cand_1_flex_p35_h2_34_p_24',
                                name: 'Flex layout, p-3.5, h2 34px leading-[1.0], p 24px leading-[1.05], text w-[152px]',
                                cardClass: 'bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-3.5 flex flex-row items-center justify-between shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group',
                                html: `
                                    <div class="relative z-10 w-[150px] shrink-0 flex flex-col justify-center">
                                        <span class="text-xs font-bold uppercase tracking-wider text-[#527668]/80 block mb-0.5">
                                            Self-check
                                        </span>
                                        <h2 class="text-[34px] font-extrabold text-[#527668] leading-[0.98] mb-1 tracking-tight">
                                            How are you feeling today?
                                        </h2>
                                        <p class="text-[24px] text-[#628A7A] leading-[1.02] tracking-tight">
                                            Take a moment to check in with yourself.
                                        </p>
                                    </div>
                                    <img src="assets/self-check-mascot.png"
                                         alt="Self-check Mascot"
                                         class="h-[190px] w-auto object-contain select-none pointer-events-none shrink-0" />
                                `
                            },
                            {
                                id: 'cand_2_flex_px3_py25_h2_34_p_24',
                                name: 'Flex layout, px-3.5 py-2.5, h2 34px leading-[0.96], p 24px leading-[1.0], text w-[154px]',
                                cardClass: 'bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] px-3.5 py-2 flex flex-row items-center justify-between shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group',
                                html: `
                                    <div class="relative z-10 w-[154px] shrink-0 flex flex-col justify-center">
                                        <span class="text-xs font-bold uppercase tracking-wider text-[#527668]/80 block mb-0.5">
                                            Self-check
                                        </span>
                                        <h2 class="text-[34px] font-extrabold text-[#527668] leading-[0.96] mb-1 tracking-tight">
                                            How are you feeling today?
                                        </h2>
                                        <p class="text-[24px] text-[#628A7A] leading-[1.0] tracking-tight">
                                            Take a moment to check in with yourself.
                                        </p>
                                    </div>
                                    <img src="assets/self-check-mascot.png"
                                         alt="Self-check Mascot"
                                         class="h-[190px] w-auto object-contain select-none pointer-events-none shrink-0" />
                                `
                            },
                            {
                                id: 'cand_3_flex_px4_py3_h2_34_p_22',
                                name: 'Flex layout, p-3.5, h2 34px leading-[1.02], p 22px leading-[1.1], text w-[150px]',
                                cardClass: 'bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-3.5 flex flex-row items-center justify-between shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group',
                                html: `
                                    <div class="relative z-10 w-[150px] shrink-0 flex flex-col justify-center">
                                        <span class="text-xs font-bold uppercase tracking-wider text-[#527668]/80 block mb-0.5">
                                            Self-check
                                        </span>
                                        <h2 class="text-[34px] font-extrabold text-[#527668] leading-[1.02] mb-1 tracking-tight">
                                            How are you feeling today?
                                        </h2>
                                        <p class="text-[22px] text-[#628A7A] leading-[1.1] tracking-tight">
                                            Take a moment to check in with yourself.
                                        </p>
                                    </div>
                                    <img src="assets/self-check-mascot.png"
                                         alt="Self-check Mascot"
                                         class="h-[190px] w-auto object-contain select-none pointer-events-none shrink-0" />
                                `
                            },
                            {
                                id: 'cand_4_flex_pt2_pb2_h2_34_p_24',
                                name: 'Flex layout, px-3 pt-2 pb-2, h2 34px leading-[1.0], p 24px leading-[1.05], text w-[155px]',
                                cardClass: 'bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] px-3 pt-2 pb-2 flex flex-row items-center justify-between shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group',
                                html: `
                                    <div class="relative z-10 w-[155px] shrink-0 flex flex-col justify-center">
                                        <span class="text-xs font-bold uppercase tracking-wider text-[#527668]/80 block mb-0.5">
                                            Self-check
                                        </span>
                                        <h2 class="text-[34px] font-extrabold text-[#527668] leading-[1.0] mb-0.5 tracking-tight">
                                            How are you feeling today?
                                        </h2>
                                        <p class="text-[24px] text-[#628A7A] leading-[1.04] tracking-tight">
                                            Take a moment to check in with yourself.
                                        </p>
                                    </div>
                                    <img src="assets/self-check-mascot.png"
                                         alt="Self-check Mascot"
                                         class="h-[190px] w-auto object-contain select-none pointer-events-none shrink-0" />
                                `
                            }
                        ];

                        for (const c of candidates) {
                            await send('Runtime.evaluate', {
                                expression: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    card.className = "${c.cardClass}";
                                    card.innerHTML = \`${c.html}\`;
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
                                        text: {
                                            topDist: tR.top - cR.top,
                                            bottomDist: cR.bottom - tR.bottom,
                                            width: tR.width,
                                            height: tR.height
                                        },
                                        mascot: {
                                            topDist: iR.top - cR.top,
                                            bottomDist: cR.bottom - iR.bottom,
                                            rightDist: cR.right - iR.right,
                                            leftDist: iR.left - cR.left,
                                            height: iR.height,
                                            width: iR.width
                                        },
                                        gapBetweenTextAndMascot: iR.left - tR.right,
                                        hasOverlap: (overlapX > 0 && overlapY > 0),
                                        hasVerticalOverflow: (tR.bottom > cR.bottom || tR.top < cR.top),
                                        isMascotClipped: (iR.right > cR.right || iR.left < cR.left || iR.bottom > cR.bottom || iR.top < cR.top),
                                        h2FontSize: window.getComputedStyle(h2).fontSize,
                                        pFontSize: window.getComputedStyle(p).fontSize
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

findOptimal().catch(console.error);
