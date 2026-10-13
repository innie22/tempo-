const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function test200pxMascot() {
    const port = 9385;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', 'chrome_data_200px_test');
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
                                    const section = document.querySelector('[data-tempo-ui="entry-lower-section"]');
                                    if (section) break;
                                    await new Promise(r => setTimeout(r, 200));
                                }
                            })()`
                        });

                        await send('Runtime.evaluate', {
                            awaitPromise: true,
                            expression: `(() => {
                                const section = document.querySelector('[data-tempo-ui="entry-lower-section"]');
                                section.scrollIntoView({ block: 'center' });
                            })()`
                        });
                        await new Promise(r => setTimeout(r, 300));

                        // Test variants of 200px mascot
                        const variants = [
                            {
                                id: 'mascot_200_absolute_corner',
                                desc: 'Absolute bottom-0 right-0 with slight overflow bleed',
                                html: `
                                    <div class="relative z-10 pointer-events-none">
                                        <span class="text-xs font-bold uppercase tracking-wider text-[#527668]/80 block mb-0.5">
                                            Self-check
                                        </span>
                                        <h2 class="text-2xl sm:text-[24px] font-extrabold text-[#527668] leading-tight mb-1">
                                            How are you feeling today?
                                        </h2>
                                        <p class="text-xs sm:text-sm text-[#628A7A] leading-relaxed max-w-[195px]">
                                            Take a moment to check in with yourself.
                                        </p>
                                    </div>
                                    <img src="assets/self-check-mascot.png"
                                         alt="Self-check Mascot"
                                         class="h-[200px] w-auto object-contain select-none pointer-events-none absolute -bottom-3 -right-3" />
                                `
                            },
                            {
                                id: 'mascot_200_absolute_flush',
                                desc: 'Absolute bottom-1 right-1 inside padding',
                                html: `
                                    <div class="relative z-10 pointer-events-none">
                                        <span class="text-xs font-bold uppercase tracking-wider text-[#527668]/80 block mb-0.5">
                                            Self-check
                                        </span>
                                        <h2 class="text-2xl sm:text-[24px] font-extrabold text-[#527668] leading-tight mb-1">
                                            How are you feeling today?
                                        </h2>
                                        <p class="text-xs sm:text-sm text-[#628A7A] leading-relaxed max-w-[195px]">
                                            Take a moment to check in with yourself.
                                        </p>
                                    </div>
                                    <img src="assets/self-check-mascot.png"
                                         alt="Self-check Mascot"
                                         class="h-[200px] w-auto object-contain select-none pointer-events-none absolute bottom-0 right-1" />
                                `
                            },
                            {
                                id: 'mascot_200_absolute_right_offset',
                                desc: 'Absolute bottom-1 -right-2',
                                html: `
                                    <div class="relative z-10 pointer-events-none">
                                        <span class="text-xs font-bold uppercase tracking-wider text-[#527668]/80 block mb-0.5">
                                            Self-check
                                        </span>
                                        <h2 class="text-2xl sm:text-[24px] font-extrabold text-[#527668] leading-tight mb-1">
                                            How are you feeling today?
                                        </h2>
                                        <p class="text-xs sm:text-sm text-[#628A7A] leading-relaxed max-w-[195px]">
                                            Take a moment to check in with yourself.
                                        </p>
                                    </div>
                                    <img src="assets/self-check-mascot.png"
                                         alt="Self-check Mascot"
                                         class="h-[200px] w-auto object-contain select-none pointer-events-none absolute -bottom-1 -right-2" />
                                `
                            }
                        ];

                        for (const v of variants) {
                            await send('Runtime.evaluate', {
                                awaitPromise: true,
                                expression: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]').children[0];
                                    card.innerHTML = \`${v.html}\`;
                                })()`
                            });
                            await new Promise(r => setTimeout(r, 400));

                            // Get measurements
                            const meas = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]').children[0];
                                    const img = card.querySelector('img');
                                    const cR = card.getBoundingClientRect();
                                    const iR = img.getBoundingClientRect();
                                    return {
                                        cardWidth: cR.width,
                                        cardHeight: cR.height,
                                        mascotWidth: iR.width,
                                        mascotHeight: iR.height,
                                        aspectRatio: iR.width / iR.height
                                    };
                                })()`
                            });
                            console.log(`${v.id} measurements:`, JSON.stringify(meas.result.value, null, 2));

                            // Screenshot card
                            const cClip = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]').children[0];
                                    const r = card.getBoundingClientRect();
                                    const pageY = r.top + window.scrollY;
                                    const pageX = r.left + window.scrollX;
                                    return { x: Math.max(0, pageX - 10), y: Math.max(0, pageY - 10), width: r.width + 20, height: r.height + 20, scale: 1 };
                                })()`
                            });
                            const cShot = await send('Page.captureScreenshot', { format: 'png', clip: cClip.result.value });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, `${v.id}.png`), Buffer.from(cShot.data, 'base64'));

                            // Screenshot entire row
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
                            fs.writeFileSync(path.join(ARTIFACT_DIR, `${v.id}_row.png`), Buffer.from(rShot.data, 'base64'));
                        }

                        ws.close();
                        proc.kill();
                        resolve();
                    };
                } catch (err) {
                    proc.kill();
                    reject(err);
                }
            });
        }).on('error', (err) => {
            proc.kill();
            reject(err);
        });
    });
}

test200pxMascot().catch(console.error);
