const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function testCard2Options() {
    const port = 9365;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', 'chrome_data_c2_test');
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

                        // Option C: Card 2 centered with button + mascot side-by-side in center
                        await send('Runtime.evaluate', {
                            awaitPromise: true,
                            expression: `(() => {
                                const sec = document.querySelector('[data-tempo-ui="entry-lower-section"]');
                                const [c1, c2, c3] = sec.children;

                                // Card 1: Self-check
                                c1.className = "bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-5 md:p-5 lg:p-5.5 flex flex-col justify-between shadow-xs relative min-h-[240px] md:h-[250px] overflow-hidden cursor-pointer group";
                                c1.innerHTML = \`
                                    <div class="relative z-10">
                                        <span class="text-xs font-bold uppercase tracking-wider text-[#527668]/80 block mb-0.5">
                                            Self-check
                                        </span>
                                        <h2 class="text-xl sm:text-[23px] font-extrabold text-[#527668] leading-tight mb-1">
                                            How are you feeling today?
                                        </h2>
                                        <p class="text-xs sm:text-sm text-[#628A7A] leading-relaxed max-w-[200px]">
                                            Take a moment to check in with yourself.
                                        </p>
                                    </div>
                                    <div class="flex items-end justify-end mt-auto">
                                        <img src="assets/self-check-mascot.png"
                                             alt="Self-check Mascot"
                                             class="h-[115px] sm:h-[120px] w-auto object-contain shrink-0 select-none pointer-events-none -mr-1" />
                                    </div>
                                \`;

                                // Card 2: Work Plan (centered bottom row)
                                c2.className = "bg-[#FBEAE5] border border-[#F0D5CC] rounded-3xl sm:rounded-[28px] p-5 md:p-5 lg:p-5.5 flex flex-col justify-between items-center text-center shadow-xs relative min-h-[240px] md:h-[250px]";
                                c2.innerHTML = \`
                                    <div>
                                        <span class="text-xs font-bold uppercase tracking-wider text-[#CC6E55]/80 block mb-0.5">
                                            Work Plan
                                        </span>
                                        <h2 class="text-xl sm:text-[23px] font-extrabold text-[#CC6E55] leading-tight mb-1">
                                            What needs to get done?
                                        </h2>
                                        <p class="text-xs sm:text-sm text-[#BD7966] leading-relaxed max-w-[270px]">
                                            Organize your tasks and take things one step at a time.
                                        </p>
                                    </div>
                                    <div class="flex items-center justify-center gap-3.5 pt-1 w-full">
                                        <button type="button"
                                                onclick="window.TempoApp.navigateTo('plan-workspace');"
                                                class="px-5 py-2 rounded-full bg-[#F5D5C8] hover:bg-[#EDC5B5] text-[#A64B30] font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer shrink-0">
                                            Work Plan
                                        </button>
                                        <div class="w-28 h-18 rounded-2xl border-2 border-dashed border-[#202124]/20 bg-white/50 text-[#202124] flex flex-col items-center justify-center p-1.5 text-center shrink-0 select-none shadow-2xs" 
                                             title="Illustration Placeholder: Mascot">
                                            <div class="w-5 h-5 rounded-full bg-white/80 text-[#202124]/70 flex items-center justify-center text-[10px] mb-0.5 shadow-2xs">
                                                🌱
                                            </div>
                                            <span class="text-[9px] font-bold text-[#202124]/80 leading-tight">Mascot</span>
                                            <span class="text-[7.5px] text-[#202124]/55 leading-tight">Work Plan Desk</span>
                                        </div>
                                    </div>
                                \`;

                                // Card 3: Notes
                                c3.className = "bg-[#FDF2DE] border border-[#F1DFC0] rounded-3xl sm:rounded-[28px] p-5 md:p-5 lg:p-5.5 flex flex-col justify-between shadow-xs relative min-h-[240px] md:h-[250px]";
                                c3.innerHTML = \`
                                    <div>
                                        <span class="text-xs font-bold uppercase tracking-wider text-[#AF7F47]/80 block mb-0.5 text-right">
                                            Notes
                                        </span>
                                        <h2 class="text-xl sm:text-[23px] font-extrabold text-[#AF7F47] leading-tight mb-1 text-right">
                                            What is your notes for today?
                                        </h2>
                                        <p class="text-xs sm:text-sm text-[#A67E4F] leading-relaxed text-right ml-auto max-w-[220px]">
                                            Write down anything you want to remember.
                                        </p>
                                    </div>
                                    <div class="flex items-end justify-between gap-3 pt-1">
                                        <div class="w-28 h-18 rounded-2xl border-2 border-dashed border-[#202124]/20 bg-white/50 text-[#202124] flex flex-col items-center justify-center p-1.5 text-center shrink-0 select-none shadow-2xs" 
                                             title="Illustration Placeholder: Mascot">
                                            <div class="w-5 h-5 rounded-full bg-white/80 text-[#202124]/70 flex items-center justify-center text-[10px] mb-0.5 shadow-2xs">
                                                🌱
                                            </div>
                                            <span class="text-[9px] font-bold text-[#202124]/80 leading-tight">Mascot</span>
                                            <span class="text-[7.5px] text-[#202124]/55 leading-tight">Notes Journal</span>
                                        </div>
                                        <button type="button"
                                                class="px-5 py-2 rounded-full bg-[#F6DFC0] hover:bg-[#EED0A9] text-[#916531] font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer shrink-0">
                                            Notes
                                        </button>
                                    </div>
                                \`;
                            })()`
                        });
                        await new Promise(r => setTimeout(r, 400));

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
                        const shot = await send('Page.captureScreenshot', { format: 'png', clip: rowClip.result.value });
                        fs.writeFileSync(path.join(ARTIFACT_DIR, 'test_250px_optC_row.png'), Buffer.from(shot.data, 'base64'));

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

testCard2Options().catch(console.error);
