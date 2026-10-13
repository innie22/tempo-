const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function testMobile() {
    const port = 9397;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', 'chrome_mobile_test');
    const chrome = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

    const proc = spawn(chrome, [
        '--headless=new',
        `--remote-debugging-port=${port}`,
        `--user-data-dir=${userDataDir}`,
        '--window-size=390,844',
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

                        const markup = `
                            <div class="relative z-10 w-[158px] sm:w-[170px] shrink-0 flex flex-col justify-center">
                                <span class="text-xs font-bold uppercase tracking-wider text-[#527668]/80 block mb-0.5 leading-tight">
                                    Self-check
                                </span>
                                <h2 class="text-[34px] font-extrabold text-[#527668] leading-[32px] mb-1 tracking-tight">
                                    How are you feeling today?
                                </h2>
                                <p class="text-[24px] text-[#628A7A] leading-[24px] tracking-tight">
                                    Take a moment to check in with yourself.
                                </p>
                            </div>
                            <img src="assets/self-check-mascot.png"
                                 alt="Self-check Mascot"
                                 class="h-[190px] w-auto object-contain select-none pointer-events-none shrink-0" />
                        `;

                        await send('Runtime.evaluate', {
                            expression: `(() => {
                                const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                card.className = "bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] px-3.5 py-2 flex flex-row items-center justify-between shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group";
                                card.innerHTML = \`${markup}\`;
                            })()`
                        });

                        await new Promise(r => setTimeout(r, 300));

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

                                const overlapX = Math.max(0, Math.min(tR.right, iR.right) - Math.max(tR.left, iR.left));
                                const overlapY = Math.max(0, Math.min(tR.bottom, iR.bottom) - Math.max(tR.top, iR.top));

                                return {
                                    card: { width: cR.width, height: cR.height },
                                    gapBetweenTextAndMascot: iR.left - tR.right,
                                    hasOverlap: (overlapX > 0 && overlapY > 0),
                                    mascotHeight: iR.height,
                                    mascotWidth: iR.width,
                                    h2FontSize: window.getComputedStyle(h2).fontSize,
                                    pFontSize: window.getComputedStyle(p).fontSize
                                };
                            })()`
                        });

                        console.log('=== MOBILE METRICS ===');
                        console.log(JSON.stringify(metrics.result.value, null, 2));

                        // Scroll and screenshot
                        await send('Runtime.evaluate', {
                            expression: `document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0].scrollIntoView({ block: 'center' });`
                        });
                        await new Promise(r => setTimeout(r, 400));

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
                        fs.writeFileSync(path.join(ARTIFACT_DIR, 'self_check_mobile_refine.png'), Buffer.from(shot.data, 'base64'));

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

testMobile().catch(console.error);
