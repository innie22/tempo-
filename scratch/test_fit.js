const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function testFit() {
    const port = 9890;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', 'chrome_test_fit');
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

                        // Let's test combinations
                        const trials = [
                            {
                                id: 'fit_test_1',
                                desc: 'h2 34px tight, p 24px tight in 150px text width',
                                html: `
                                    <div class="relative z-10 w-[150px] shrink-0">
                                        <span class="text-xs font-bold uppercase tracking-wider text-[#527668]/80 block mb-0.5">
                                            Self-check
                                        </span>
                                        <h2 style="font-size: 34px; line-height: 1.0; margin-bottom: 4px; font-weight: 800; color: #527668; letter-spacing: -0.02em;">
                                            How are you feeling today?
                                        </h2>
                                        <p style="font-size: 24px; line-height: 1.1; color: #628A7A; letter-spacing: -0.02em;">
                                            Take a moment to check in with yourself.
                                        </p>
                                    </div>
                                    <img src="assets/self-check-mascot.png"
                                         alt="Self-check Mascot"
                                         class="h-[190px] w-auto object-contain select-none pointer-events-none shrink-0" />
                                `,
                                cardClass: 'bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-3.5 flex flex-row items-center justify-between shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group'
                            },
                            {
                                id: 'fit_test_2',
                                desc: 'Card p-3, text width 155px, mascot h-[190px] flush right',
                                html: `
                                    <div class="relative z-10 w-[155px] shrink-0">
                                        <span class="text-xs font-bold uppercase tracking-wider text-[#527668]/80 block mb-0.5">
                                            Self-check
                                        </span>
                                        <h2 style="font-size: 34px; line-height: 1.05; margin-bottom: 4px; font-weight: 800; color: #527668; letter-spacing: -0.03em;">
                                            How are you feeling today?
                                        </h2>
                                        <p style="font-size: 24px; line-height: 1.15; color: #628A7A; letter-spacing: -0.02em;">
                                            Take a moment to check in with yourself.
                                        </p>
                                    </div>
                                    <img src="assets/self-check-mascot.png"
                                         alt="Self-check Mascot"
                                         class="h-[190px] w-auto object-contain select-none pointer-events-none shrink-0" />
                                `,
                                cardClass: 'bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-3 flex flex-row items-center justify-between shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group'
                            },
                            {
                                id: 'fit_test_3',
                                desc: 'What if p was 12px -> 22px? Or p 24px? Let us test p 22px vs 24px',
                                html: `
                                    <div class="relative z-10 w-[150px] shrink-0">
                                        <span class="text-xs font-bold uppercase tracking-wider text-[#527668]/80 block mb-0.5">
                                            Self-check
                                        </span>
                                        <h2 style="font-size: 34px; line-height: 1.05; margin-bottom: 4px; font-weight: 800; color: #527668; letter-spacing: -0.02em;">
                                            How are you feeling today?
                                        </h2>
                                        <p style="font-size: 22px; line-height: 1.15; color: #628A7A; letter-spacing: -0.01em;">
                                            Take a moment to check in with yourself.
                                        </p>
                                    </div>
                                    <img src="assets/self-check-mascot.png"
                                         alt="Self-check Mascot"
                                         class="h-[190px] w-auto object-contain select-none pointer-events-none shrink-0" />
                                `,
                                cardClass: 'bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-3.5 flex flex-row items-center justify-between shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group'
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
                                        cardHeight: cR.height,
                                        cardWidth: cR.width,
                                        textWidth: tR.width,
                                        textHeight: tR.height,
                                        mascotHeight: iR.height,
                                        mascotWidth: iR.width,
                                        mascotRight: cR.right - iR.right,
                                        mascotLeft: iR.left - cR.left,
                                        overlapX,
                                        overlapY,
                                        hasOverlap: (overlapX > 0 && overlapY > 0),
                                        verticalOverflow: (tR.bottom > cR.bottom || tR.top < cR.top),
                                        overflowBottomPx: tR.bottom - cR.bottom,
                                        h2Height: hR.height,
                                        pHeight: pR.height
                                    };
                                })()`
                            });

                            console.log('=== ' + t.id + ' ===');
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

testFit().catch(console.error);
