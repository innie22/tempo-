const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function runLiveVerification(vw = 1440, vh = 900, isMobile = false) {
    const port = isMobile ? 9351 : 9350;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', isMobile ? 'chrome_data_sc_m' : 'chrome_data_sc_d');
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
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    const img = card?.querySelector('img');
                                    if (card && img && img.complete && img.naturalWidth > 0) break;
                                    await new Promise(r => setTimeout(r, 200));
                                }
                                await new Promise(r => setTimeout(r, 500));
                            })()`
                        });

                        const metrics = await send('Runtime.evaluate', {
                            returnByValue: true,
                            expression: `(() => {
                                const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                if (!card) return { error: 'Card not found' };

                                const r = card.getBoundingClientRect();
                                const s = window.getComputedStyle(card);

                                const badge = card.querySelector('span');
                                const h2 = card.querySelector('h2');
                                const p = card.querySelector('p');
                                const btn = card.querySelector('button');
                                const img = card.querySelector('img');

                                function rgbToHex(rgb) {
                                    const m = rgb.match(/^rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
                                    if (!m) return rgb;
                                    return "#" + [m[1], m[2], m[3]].map(x => parseInt(x).toString(16).padStart(2, '0')).join('');
                                }

                                return {
                                    viewport: { width: window.innerWidth, height: window.innerHeight },
                                    card: {
                                        rect: { width: Math.round(r.width * 100) / 100, height: Math.round(r.height * 100) / 100 },
                                        backgroundColorRaw: s.backgroundColor,
                                        backgroundColorHex: rgbToHex(s.backgroundColor),
                                        borderColorRaw: s.borderColor,
                                        borderColorHex: rgbToHex(s.borderColor),
                                        borderRadius: s.borderRadius,
                                        hasButton: btn !== null,
                                        buttonElement: btn ? btn.outerHTML : null
                                    },
                                    badgeText: badge ? badge.innerText.trim() : null,
                                    headingText: h2 ? h2.innerText.trim() : null,
                                    descriptionText: p ? p.innerText.trim() : null,
                                    mascot: img ? {
                                        src: img.getAttribute('src'),
                                        naturalWidth: img.naturalWidth,
                                        naturalHeight: img.naturalHeight,
                                        renderedWidth: Math.round(img.getBoundingClientRect().width * 100) / 100,
                                        renderedHeight: Math.round(img.getBoundingClientRect().height * 100) / 100,
                                        aspectRatio: Math.round((img.getBoundingClientRect().width / img.getBoundingClientRect().height) * 1000) / 1000,
                                        objectFit: window.getComputedStyle(img).objectFit
                                    } : null
                                };
                            })()`
                        });

                        console.log(`=== METRICS (${isMobile ? 'MOBILE' : 'DESKTOP'}) ===`);
                        console.log(JSON.stringify(metrics.result.value, null, 2));

                        // Scroll lower section into view
                        await send('Runtime.evaluate', {
                            awaitPromise: true,
                            expression: `(() => {
                                const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                card.scrollIntoView({ block: 'center' });
                            })()`
                        });
                        await new Promise(r => setTimeout(r, 400));

                        if (!isMobile) {
                            // Close-up of Self-check card
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
                            fs.writeFileSync(path.join(ARTIFACT_DIR, 'self_check_card_closeup.png'), Buffer.from(scShot.data, 'base64'));

                            // Row screenshot of all 3 cards
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
                            fs.writeFileSync(path.join(ARTIFACT_DIR, 'three_lower_cards_with_selfcheck.png'), Buffer.from(rowShot.data, 'base64'));

                            // Full desktop screenshot
                            const fullShot = await send('Page.captureScreenshot', { format: 'png' });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, 'entry_home_selfcheck_desktop.png'), Buffer.from(fullShot.data, 'base64'));
                        } else {
                            // Mobile screenshot
                            const mClip = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                    const r = card.getBoundingClientRect();
                                    const pageY = r.top + window.scrollY;
                                    const pageX = r.left + window.scrollX;
                                    return { x: Math.max(0, pageX - 10), y: Math.max(0, pageY - 10), width: r.width + 20, height: r.height + 20, scale: 1 };
                                })()`
                            });
                            const mShot = await send('Page.captureScreenshot', { format: 'png', clip: mClip.result.value });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, 'self_check_card_mobile.png'), Buffer.from(mShot.data, 'base64'));
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

async function main() {
    await runLiveVerification(1440, 900, false);
    await runLiveVerification(390, 844, true);
    console.log('Self-check live verification completed successfully!');
}

main().catch(console.error);
