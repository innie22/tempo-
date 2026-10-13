const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function test180() {
    const port = 9380;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', 'chrome_test_180');
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

                        // Candidates to evaluate
                        const trials = [
                            {
                                id: 'opt1_w165_gap',
                                desc: 'Card p-4 flex items-center justify-between, text w-[165px], h2 29px leading-[1.08], p 19px leading-[1.18]',
                                cardClass: 'bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-4 flex flex-row items-center justify-between shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group',
                                html: `
                                    <div class="relative z-10 w-[165px] shrink-0 flex flex-col justify-center">
                                        <span class="text-xs font-bold uppercase tracking-wider text-[#527668]/80 block mb-1 leading-tight">
                                            Self-check
                                        </span>
                                        <h2 class="text-[29px] font-extrabold text-[#527668] leading-[30px] mb-1.5 tracking-tight">
                                            How are you feeling today?
                                        </h2>
                                        <p class="text-[19px] text-[#628A7A] leading-[22px] tracking-tight">
                                            Take a moment to check in with yourself.
                                        </p>
                                    </div>
                                    <img src="assets/self-check-mascot.png"
                                         alt="Self-check Mascot"
                                         class="h-[180px] w-auto object-contain select-none pointer-events-none shrink-0" />
                                `
                            },
                            {
                                id: 'opt2_w170_comfortable',
                                desc: 'Card px-4 py-3.5 flex items-center justify-between, text w-[168px], h2 29px leading-[31px], p 19px leading-[23px]',
                                cardClass: 'bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] px-4 py-3.5 flex flex-row items-center justify-between shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group',
                                html: `
                                    <div class="relative z-10 w-[168px] shrink-0 flex flex-col justify-center">
                                        <span class="text-xs font-bold uppercase tracking-wider text-[#527668]/80 block mb-1 leading-tight">
                                            Self-check
                                        </span>
                                        <h2 class="text-[29px] font-extrabold text-[#527668] leading-[31px] mb-1.5 tracking-tight">
                                            How are you feeling today?
                                        </h2>
                                        <p class="text-[19px] text-[#628A7A] leading-[23px] tracking-tight">
                                            Take a moment to check in with yourself.
                                        </p>
                                    </div>
                                    <img src="assets/self-check-mascot.png"
                                         alt="Self-check Mascot"
                                         class="h-[180px] w-auto object-contain select-none pointer-events-none shrink-0" />
                                `
                            },
                            {
                                id: 'opt3_p45_w160',
                                desc: 'Card p-4.5 flex items-center justify-between, text w-[160px]',
                                cardClass: 'bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-4.5 flex flex-row items-center justify-between shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group',
                                html: `
                                    <div class="relative z-10 w-[160px] shrink-0 flex flex-col justify-center">
                                        <span class="text-xs font-bold uppercase tracking-wider text-[#527668]/80 block mb-1 leading-tight">
                                            Self-check
                                        </span>
                                        <h2 class="text-[29px] font-extrabold text-[#527668] leading-[30px] mb-1 tracking-tight">
                                            How are you feeling today?
                                        </h2>
                                        <p class="text-[19px] text-[#628A7A] leading-[22px] tracking-tight">
                                            Take a moment to check in with yourself.
                                        </p>
                                    </div>
                                    <img src="assets/self-check-mascot.png"
                                         alt="Self-check Mascot"
                                         class="h-[180px] w-auto object-contain select-none pointer-events-none shrink-0" />
                                `
                            }
                        ];

                        for (const t of trials) {
                            await send('Runtime.evaluate', {
                                expression: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    card.className = "${t.cardClass}";
                                    card.innerHTML = \`${t.html}\`;
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
                                            topMargin: tR.top - cR.top,
                                            bottomMargin: cR.bottom - tR.bottom,
                                            width: tR.width,
                                            height: tR.height
                                        },
                                        mascot: {
                                            topMargin: iR.top - cR.top,
                                            bottomMargin: cR.bottom - iR.bottom,
                                            rightMargin: cR.right - iR.right,
                                            leftMargin: iR.left - cR.left,
                                            height: iR.height,
                                            width: iR.width,
                                            isClipped: (iR.right > cR.right || iR.left < cR.left || iR.bottom > cR.bottom || iR.top < cR.top)
                                        },
                                        h2Lines: Math.round(hR.height / 30),
                                        pLines: Math.round(pR.height / 22),
                                        hasOverlap: (overlapX > 0 && overlapY > 0),
                                        hasVerticalOverflow: (tR.bottom > cR.bottom || tR.top < cR.top),
                                        gapBetweenTextAndMascot: iR.left - tR.right,
                                        h2FontSize: window.getComputedStyle(h2).fontSize,
                                        pFontSize: window.getComputedStyle(p).fontSize
                                    };
                                })()`
                            });

                            console.log('=== ' + t.id + ' ===');
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
                            fs.writeFileSync(path.join(ARTIFACT_DIR, `${t.id}.png`), Buffer.from(shot.data, 'base64'));

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
                            fs.writeFileSync(path.join(ARTIFACT_DIR, `${t.id}_row.png`), Buffer.from(rowShot.data, 'base64'));
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

test180().catch(console.error);
