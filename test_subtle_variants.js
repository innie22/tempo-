const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function testSubtleVariants() {
    const port = 9345;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', 'chrome_data_subtle');
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

                        const options = [
                            {
                                id: 'opt_135_natural',
                                imgClass: 'h-[135px] w-auto object-contain shrink-0 select-none pointer-events-none',
                                divClass: 'flex items-end justify-end mt-auto'
                            },
                            {
                                id: 'opt_138_nudge_bottom',
                                imgClass: 'h-[138px] w-auto object-contain shrink-0 select-none pointer-events-none -mr-1 -mb-1',
                                divClass: 'flex items-end justify-end mt-auto'
                            },
                            {
                                id: 'opt_142_bleed',
                                imgClass: 'h-[142px] w-auto object-contain shrink-0 select-none pointer-events-none -mr-1.5 -mb-1.5',
                                divClass: 'flex items-end justify-end mt-auto'
                            }
                        ];

                        for (const opt of options) {
                            await send('Runtime.evaluate', {
                                awaitPromise: true,
                                expression: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]').children[0];
                                    card.className = "bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-6 flex flex-col justify-between shadow-xs relative min-h-[240px] md:h-[300px] overflow-hidden cursor-pointer group";
                                    card.setAttribute('onclick', "window.TempoMode.openStrack('setup', { sourceContext: 'entry' });");
                                    
                                    card.innerHTML = \`
                                        <div class="relative z-10">
                                            <span class="text-xs font-bold uppercase tracking-wider text-[#527668]/80 block mb-1">
                                                Self-check
                                            </span>
                                            <h2 class="text-2xl sm:text-[26px] font-extrabold text-[#527668] leading-tight mb-1.5">
                                                How are you feeling today?
                                            </h2>
                                            <p class="text-xs sm:text-sm text-[#628A7A] leading-relaxed max-w-[210px] mb-2">
                                                Take a moment to check in with yourself.
                                            </p>
                                        </div>
                                        <div class="${opt.divClass}">
                                            <img src="assets/self-check-mascot.png"
                                                 alt="Self-check Mascot"
                                                 class="${opt.imgClass}" />
                                        </div>
                                    \`;
                                })()`
                            });
                            await new Promise(r => setTimeout(r, 400));

                            // Screenshot card
                            const cardClip = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]').children[0];
                                    const r = card.getBoundingClientRect();
                                    const pageY = r.top + window.scrollY;
                                    const pageX = r.left + window.scrollX;
                                    return { x: Math.max(0, pageX - 10), y: Math.max(0, pageY - 10), width: r.width + 20, height: r.height + 20, scale: 1 };
                                })()`
                            });
                            const cardShot = await send('Page.captureScreenshot', { format: 'png', clip: cardClip.result.value });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, `${opt.id}.png`), Buffer.from(cardShot.data, 'base64'));

                            // Screenshot entire 3-card row
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
                            fs.writeFileSync(path.join(ARTIFACT_DIR, `${opt.id}_row.png`), Buffer.from(rowShot.data, 'base64'));
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

testSubtleVariants().catch(console.error);
