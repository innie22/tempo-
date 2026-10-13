const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function verify(vw = 1440, vh = 900, isCapture = false) {
    const port = isCapture ? 9370 : 9371;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', `chrome_data_250px_final_${vw}`);
    const chrome = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

    const proc = spawn(chrome, [
        '--headless=new',
        `--remote-debugging-port=${port}`,
        `--user-data-dir=${userDataDir}`,
        `--window-size=${vw},${vh}`,
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
                                    const img = section ? section.querySelector('img') : null;
                                    if (section && section.children.length === 3 && img && img.complete) break;
                                    await new Promise(r => setTimeout(r, 200));
                                }
                                await new Promise(r => setTimeout(r, 600));
                            })()`
                        });

                        const data = await send('Runtime.evaluate', {
                            returnByValue: true,
                            expression: `(() => {
                                const section = document.querySelector('[data-tempo-ui="entry-lower-section"]');
                                const cards = Array.from(section.children);

                                function rgbToHex(rgb) {
                                    const m = rgb.match(/^rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
                                    if (!m) return rgb;
                                    return "#" + [m[1], m[2], m[3]].map(x => parseInt(x).toString(16).padStart(2, '0')).join('');
                                }

                                const results = cards.map((card, idx) => {
                                    const r = card.getBoundingClientRect();
                                    const s = window.getComputedStyle(card);
                                    const title = card.querySelector('h2').innerText.trim();

                                    const allDescendants = Array.from(card.querySelectorAll('*'));
                                    let hasOverflow = false;
                                    let maxBottom = r.bottom;
                                    for (const el of allDescendants) {
                                        const cRect = el.getBoundingClientRect();
                                        if (cRect.bottom > r.bottom + 1) {
                                            hasOverflow = true;
                                            maxBottom = Math.max(maxBottom, cRect.bottom);
                                        }
                                    }

                                    return {
                                        index: idx + 1,
                                        title,
                                        width: Math.round(r.width * 100) / 100,
                                        height: Math.round(r.height * 100) / 100,
                                        top: Math.round(r.top * 100) / 100,
                                        bottom: Math.round(r.bottom * 100) / 100,
                                        left: Math.round(r.left * 100) / 100,
                                        right: Math.round(r.right * 100) / 100,
                                        computedHeight: s.height,
                                        backgroundColorHex: rgbToHex(s.backgroundColor),
                                        hasButton: card.querySelector('button') !== null,
                                        hasOverflow,
                                        overflowDeltaPx: Math.round((maxBottom - r.bottom) * 100) / 100
                                    };
                                });

                                const gaps = [];
                                for (let i = 0; i < cards.length - 1; i++) {
                                    const r1 = cards[i].getBoundingClientRect();
                                    const r2 = cards[i + 1].getBoundingClientRect();
                                    gaps.push({
                                        between: (i + 1) + ' and ' + (i + 2),
                                        horizontalGap: Math.round((r2.left - r1.right) * 100) / 100,
                                        verticalGap: Math.round((r2.top - r1.bottom) * 100) / 100
                                    });
                                }

                                return {
                                    viewport: { width: window.innerWidth, height: window.innerHeight },
                                    cards: results,
                                    allCardsHeight250: results.every(c => Math.abs(c.height - 250) < 0.5),
                                    allCardsAlignedHorizontally: (results[0].top === results[1].top && results[1].top === results[2].top),
                                    gaps
                                };
                            })()`
                        });

                        console.log(`=== RESULTS (${vw}x${vh}) ===`);
                        console.log(JSON.stringify(data.result.value, null, 2));

                        // Scroll lower section into view
                        await send('Runtime.evaluate', {
                            awaitPromise: true,
                            expression: `(() => {
                                const section = document.querySelector('[data-tempo-ui="entry-lower-section"]');
                                section.scrollIntoView({ block: 'center' });
                            })()`
                        });
                        await new Promise(r => setTimeout(r, 400));

                        if (isCapture) {
                            // Screenshot lower section
                            const secClip = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const section = document.querySelector('[data-tempo-ui="entry-lower-section"]');
                                    const r = section.getBoundingClientRect();
                                    const pageY = r.top + window.scrollY;
                                    const pageX = r.left + window.scrollX;
                                    return { x: Math.max(0, pageX - 12), y: Math.max(0, pageY - 12), width: r.width + 24, height: r.height + 24, scale: 1 };
                                })()`
                            });
                            const secShot = await send('Page.captureScreenshot', { format: 'png', clip: secClip.result.value });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, 'three_lower_cards_250px.png'), Buffer.from(secShot.data, 'base64'));

                            // Screenshot Self-check card closeup
                            const scClip = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    const r = card.getBoundingClientRect();
                                    const pageY = r.top + window.scrollY;
                                    const pageX = r.left + window.scrollX;
                                    return { x: Math.max(0, pageX - 10), y: Math.max(0, pageY - 10), width: r.width + 20, height: r.height + 20, scale: 1 };
                                })()`
                            });
                            const scShot = await send('Page.captureScreenshot', { format: 'png', clip: scClip.result.value });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, 'self_check_card_250px.png'), Buffer.from(scShot.data, 'base64'));

                            // Full desktop screenshot
                            const fullShot = await send('Page.captureScreenshot', { format: 'png' });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, 'entry_home_250px_desktop.png'), Buffer.from(fullShot.data, 'base64'));
                        } else {
                            // Mobile screenshot
                            const mClip = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const sec = document.querySelector('[data-tempo-ui="entry-lower-section"]');
                                    const r = sec.getBoundingClientRect();
                                    const pageY = r.top + window.scrollY;
                                    const pageX = r.left + window.scrollX;
                                    return { x: Math.max(0, pageX - 10), y: Math.max(0, pageY - 10), width: r.width + 20, height: r.height + 20, scale: 1 };
                                })()`
                            });
                            const mShot = await send('Page.captureScreenshot', { format: 'png', clip: mClip.result.value });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, 'three_lower_cards_mobile_250.png'), Buffer.from(mShot.data, 'base64'));
                        }

                        ws.close();
                        proc.kill();
                        resolve(data.result.value);
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

async function main() {
    await verify(1440, 900, true);
    await verify(390, 844, false);
    console.log('250px verification finished successfully!');
}

main().catch(console.error);
