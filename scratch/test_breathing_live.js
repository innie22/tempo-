const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function runTest(width = 1440, height = 900, isMobile = false) {
    const port = isMobile ? 9303 : 9302;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', isMobile ? 'chrome_data_breathing_m' : 'chrome_data_breathing_d');
    const chrome = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

    const proc = spawn(chrome, [
        '--headless=new',
        `--remote-debugging-port=${port}`,
        `--user-data-dir=${userDataDir}`,
        `--window-size=${width},${height}`,
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
                        // Wait for breathing card
                        await send('Runtime.evaluate', {
                            awaitPromise: true,
                            expression: `(async () => {
                                for (let i = 0; i < 50; i++) {
                                    const breathing = document.querySelector('[title="Practice Breathing"]');
                                    const mascot = breathing ? breathing.querySelector('img') : null;
                                    if (breathing && mascot && mascot.complete && mascot.naturalWidth > 0) break;
                                    await new Promise(r => setTimeout(r, 200));
                                }
                                await new Promise(r => setTimeout(r, 800));
                            })()`
                        });

                        // Extract detailed metrics
                        const metrics = await send('Runtime.evaluate', {
                            returnByValue: true,
                            expression: `(() => {
                                const panel = document.querySelector('[data-tempo-ui="entry-community-panel"]');
                                const breathing = document.querySelector('[title="Practice Breathing"]');
                                const h3 = breathing.querySelector('h3');
                                const p = breathing.querySelector('p');
                                const img = breathing.querySelector('img');

                                const bR = breathing.getBoundingClientRect();
                                const pR = panel ? panel.getBoundingClientRect() : null;
                                const hR = h3.getBoundingClientRect();
                                const pDescR = p.getBoundingClientRect();
                                const iR = img.getBoundingClientRect();

                                const bStyle = window.getComputedStyle(breathing);
                                const hStyle = window.getComputedStyle(h3);
                                const pStyle = window.getComputedStyle(p);
                                const iStyle = window.getComputedStyle(img);

                                function rgbToHex(rgb) {
                                    const m = rgb.match(/^rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
                                    if (!m) return rgb;
                                    return "#" + [m[1], m[2], m[3]].map(x => parseInt(x).toString(16).padStart(2, '0')).join('');
                                }

                                return {
                                    viewport: { width: window.innerWidth, height: window.innerHeight },
                                    gapBetweenPanelAndBreathing: pR ? (bR.top - pR.bottom) : null,
                                    card: {
                                        rect: { width: bR.width, height: bR.height },
                                        backgroundColorRaw: bStyle.backgroundColor,
                                        backgroundColorHex: rgbToHex(bStyle.backgroundColor),
                                        borderColorRaw: bStyle.borderColor,
                                        borderColorHex: rgbToHex(bStyle.borderColor),
                                        borderWidth: bStyle.borderWidth,
                                        borderRadius: bStyle.borderRadius,
                                        boxShadow: bStyle.boxShadow
                                    },
                                    heading: {
                                        text: h3.innerText,
                                        colorRaw: hStyle.color,
                                        colorHex: rgbToHex(hStyle.color),
                                        fontSize: hStyle.fontSize,
                                        fontWeight: hStyle.fontWeight,
                                        lineHeight: hStyle.lineHeight
                                    },
                                    description: {
                                        text: p.innerText,
                                        colorRaw: pStyle.color,
                                        colorHex: rgbToHex(pStyle.color),
                                        fontSize: pStyle.fontSize,
                                        lineHeight: pStyle.lineHeight
                                    },
                                    mascot: {
                                        src: img.getAttribute('src'),
                                        renderedWidth: iR.width,
                                        renderedHeight: iR.height,
                                        aspectRatio: iR.width / iR.height,
                                        naturalWidth: img.naturalWidth,
                                        naturalHeight: img.naturalHeight,
                                        objectFit: iStyle.objectFit
                                    }
                                };
                            })()`
                        });

                        console.log(`=== METRICS (${isMobile ? 'MOBILE' : 'DESKTOP'}) ===`);
                        console.log(JSON.stringify(metrics.result.value, null, 2));

                        if (!isMobile) {
                            // Close-up of breathing card
                            const bClip = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const el = document.querySelector('[title="Practice Breathing"]');
                                    const r = el.getBoundingClientRect();
                                    return { x: r.x - 12, y: r.y - 12, width: r.width + 24, height: r.height + 24, scale: 1 };
                                })()`
                            });
                            const bShot = await send('Page.captureScreenshot', { format: 'png', clip: bClip.result.value });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, 'breathing_card_closeup.png'), Buffer.from(bShot.data, 'base64'));

                            // Combined community + breathing column screenshot
                            const colClip = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const panel = document.querySelector('[data-tempo-ui="entry-community-panel"]');
                                    const breathing = document.querySelector('[title="Practice Breathing"]');
                                    const r1 = panel.getBoundingClientRect();
                                    const r2 = breathing.getBoundingClientRect();
                                    const top = Math.min(r1.top, r2.top) - 10;
                                    const bottom = Math.max(r1.bottom, r2.bottom) + 10;
                                    const left = Math.min(r1.left, r2.left) - 10;
                                    const right = Math.max(r1.right, r2.right) + 10;
                                    return { x: left, y: top, width: right - left, height: bottom - top, scale: 1 };
                                })()`
                            });
                            const colShot = await send('Page.captureScreenshot', { format: 'png', clip: colClip.result.value });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, 'breathing_and_community_desktop.png'), Buffer.from(colShot.data, 'base64'));

                            // Full desktop screenshot
                            const fullShot = await send('Page.captureScreenshot', { format: 'png' });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, 'breathing_full_desktop.png'), Buffer.from(fullShot.data, 'base64'));
                        } else {
                            // Mobile screenshot of breathing card
                            const bClipScrolled = await send('Runtime.evaluate', {
                                returnByValue: true,
                                expression: `(() => {
                                    const el = document.querySelector('[title="Practice Breathing"]');
                                    el.scrollIntoView({ block: 'center' });
                                    const r = el.getBoundingClientRect();
                                    const pageY = r.top + window.scrollY;
                                    const pageX = r.left + window.scrollX;
                                    return { x: Math.max(0, pageX - 8), y: Math.max(0, pageY - 8), width: r.width + 16, height: r.height + 16, scale: 1 };
                                })()`
                            });
                            await new Promise(r => setTimeout(r, 400));
                            const bShot = await send('Page.captureScreenshot', { format: 'png', clip: bClipScrolled.result.value });
                            fs.writeFileSync(path.join(ARTIFACT_DIR, 'breathing_mobile_card.png'), Buffer.from(bShot.data, 'base64'));
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
    await runTest(1440, 900, false);
    await runTest(390, 844, true);
    console.log('All tests completed successfully!');
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
