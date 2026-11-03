const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function runVerification() {
    const chrome = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
    const proc = spawn(chrome, [
        '--headless=new',
        '--remote-debugging-port=9277',
        '--user-data-dir=C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\\scratch\\chrome_user_data_tb_verify',
        '--window-size=1440,900',
        'http://localhost:8000/'
    ]);

    await new Promise(r => setTimeout(r, 2000));

    http.get('http://127.0.0.1:9277/json', (res) => {
        let raw = '';
        res.on('data', c => raw += c);
        res.on('end', async () => {
            const tabs = JSON.parse(raw);
            const tab = tabs.find(t => t.type === 'page');
            const ws = new WebSocket(tab.webSocketDebuggerUrl);

            let msgId = 1;
            function send(method, params = {}) {
                return new Promise((resolve) => {
                    const id = msgId++;
                    const handler = (evt) => {
                        const data = JSON.parse(evt.data);
                        if (data.id === id) {
                            ws.removeEventListener('message', handler);
                            resolve(data.result);
                        }
                    };
                    ws.addEventListener('message', handler);
                    ws.send(JSON.stringify({ id, method, params }));
                });
            }

            ws.onopen = async () => {
                // Wait for tool grid and mascot images
                await send('Runtime.evaluate', {
                    awaitPromise: true,
                    expression: `(async () => {
                        for (let i = 0; i < 50; i++) {
                            const grid = document.querySelector('[data-tempo-ui="entry-tool-grid"]');
                            if (grid && grid.children.length >= 4) {
                                const tbImg = grid.children[3].querySelector('img');
                                if (tbImg && tbImg.complete && tbImg.naturalWidth > 0) break;
                            }
                            await new Promise(r => setTimeout(r, 200));
                        }
                        await new Promise(r => setTimeout(r, 600));
                    })()`
                });

                // Measure live metrics
                const data = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        function rgbToHex(rgb) {
                            if (!rgb) return '';
                            const match = rgb.match(/\\d+/g);
                            if (!match) return rgb;
                            return '#' + match.slice(0, 3).map(x => parseInt(x).toString(16).padStart(2, '0')).join('').toUpperCase();
                        }

                        const grid = document.querySelector('[data-tempo-ui="entry-tool-grid"]');
                        const cards = Array.from(grid.children);

                        const cardSummaries = cards.map((c, idx) => {
                            const h3 = c.querySelector('h3');
                            const p = c.querySelector('p');
                            const img = c.querySelector('img');
                            const cStyle = window.getComputedStyle(c);
                            const hStyle = h3 ? window.getComputedStyle(h3) : null;
                            const pStyle = p ? window.getComputedStyle(p) : null;
                            const iStyle = img ? window.getComputedStyle(img) : null;

                            const cR = c.getBoundingClientRect();
                            const iR = img ? img.getBoundingClientRect() : null;

                            return {
                                index: idx,
                                title: h3 ? h3.textContent.trim().replace(/\\s+/g, ' ') : null,
                                titleFontSize: hStyle ? hStyle.fontSize : null,
                                titleFontWeight: hStyle ? hStyle.fontWeight : null,
                                titleColorHex: hStyle ? rgbToHex(hStyle.color) : null,
                                titleLines: h3 ? h3.getClientRects().length : null,
                                descText: p ? p.textContent.trim().replace(/\\s+/g, ' ') : null,
                                descFontSize: pStyle ? pStyle.fontSize : null,
                                descColorHex: pStyle ? rgbToHex(pStyle.color) : null,
                                descLines: p ? p.getClientRects().length : null,
                                cardW: Math.round(cR.width),
                                cardH: Math.round(cR.height),
                                bgHex: rgbToHex(cStyle.backgroundColor),
                                borderHex: rgbToHex(cStyle.borderColor),
                                img: img ? {
                                    src: img.src,
                                    naturalW: img.naturalWidth,
                                    naturalH: img.naturalHeight,
                                    naturalAspect: (img.naturalWidth / img.naturalHeight).toFixed(4),
                                    renderedW: Math.round(iR.width),
                                    renderedH: Math.round(iR.height),
                                    renderedAspect: (iR.width / iR.height).toFixed(4),
                                    filter: iStyle.filter,
                                    opacity: iStyle.opacity,
                                    mixBlendMode: iStyle.mixBlendMode
                                } : null
                            };
                        });

                        // Detailed check for Tempo break
                        const tbCard = cards[3];
                        const tbH3 = tbCard.querySelector('h3');
                        const tbP = tbCard.querySelector('p');
                        const tbImg = tbCard.querySelector('img');
                        const tbDiv = tbCard.querySelector('div');

                        const tbCR = tbCard.getBoundingClientRect();
                        const tbHR = tbH3.getBoundingClientRect();
                        const tbPR = tbP.getBoundingClientRect();
                        const tbIR = tbImg.getBoundingClientRect();
                        const tbDR = tbDiv.getBoundingClientRect();

                        const tbDetail = {
                            cardRect: { x: tbCR.x, y: tbCR.y, width: tbCR.width, height: tbCR.height },
                            textGroupRect: { x: tbDR.x, y: tbDR.y, width: tbDR.width, height: tbDR.height },
                            imgRect: { x: tbIR.x, y: tbIR.y, width: tbIR.width, height: tbIR.height },
                            h3Rect: { x: tbHR.x, y: tbHR.y, width: tbHR.width, height: tbHR.height },
                            pRect: { x: tbPR.x, y: tbPR.y, width: tbPR.height, height: tbPR.height },
                            gapBetweenTextAndImg: Math.round(tbIR.left - tbDR.right),
                            isOverlappingText: tbIR.left < tbDR.right,
                            isImgClippedLeft: tbIR.left < tbCR.left,
                            isImgClippedRight: tbIR.right > tbCR.right + 2, // 2px margin of error
                            isImgClippedTop: tbIR.top < tbCR.top,
                            isImgClippedBottom: tbIR.bottom > tbCR.bottom + 2
                        };

                        return {
                            allCards: cardSummaries,
                            tempoBreakDetail: tbDetail
                        };
                    })()`
                });

                console.log('=== VERIFICATION RESULTS ===');
                console.log(JSON.stringify(data.result.value, null, 2));

                // 1. Close-up screenshot of Tempo break
                const tbClip = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        const el = document.querySelector('[data-tempo-ui="entry-tool-grid"]').children[3];
                        const r = el.getBoundingClientRect();
                        return { x: r.x - 10, y: r.y - 10, width: r.width + 20, height: r.height + 20, scale: 1 };
                    })()`
                });
                const tbShot = await send('Page.captureScreenshot', { format: 'png', clip: tbClip.result.value });
                fs.writeFileSync(path.join(ARTIFACT_DIR, 'tempo_break_final_closeup.png'), Buffer.from(tbShot.data, 'base64'));

                // 2. 2x2 Tool Grid screenshot
                const gridClip = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        const el = document.querySelector('[data-tempo-ui="entry-tool-grid"]');
                        const r = el.getBoundingClientRect();
                        return { x: r.x - 15, y: r.y - 15, width: r.width + 30, height: r.height + 30, scale: 1 };
                    })()`
                });
                const gridShot = await send('Page.captureScreenshot', { format: 'png', clip: gridClip.result.value });
                fs.writeFileSync(path.join(ARTIFACT_DIR, 'tempo_break_final_grid.png'), Buffer.from(gridShot.data, 'base64'));

                // 3. Desktop Entry Home view
                const heroClip = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        const grid = document.querySelector('[data-tempo-ui="entry-tool-grid"]');
                        const section = grid.closest('main') || grid.closest('section') || document.body;
                        return { x: 0, y: 0, width: 1440, height: 850, scale: 1 };
                    })()`
                });
                const heroShot = await send('Page.captureScreenshot', { format: 'png', clip: heroClip.result.value });
                fs.writeFileSync(path.join(ARTIFACT_DIR, 'tempo_break_final_desktop.png'), Buffer.from(heroShot.data, 'base64'));

                // 4. Mobile Viewport (390 x 844)
                await send('Emulation.setDeviceMetricsOverride', {
                    width: 390,
                    height: 844,
                    deviceScaleFactor: 2,
                    mobile: true
                });
                await new Promise(r => setTimeout(r, 500));
                const mobileTbClip = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        const el = document.querySelector('[data-tempo-ui="entry-tool-grid"]').children[3];
                        const r = el.getBoundingClientRect();
                        return { x: Math.max(0, r.x - 8), y: Math.max(0, r.y - 8), width: r.width + 16, height: r.height + 16, scale: 2 };
                    })()`
                });
                const mobileShot = await send('Page.captureScreenshot', { format: 'png', clip: mobileTbClip.result.value });
                fs.writeFileSync(path.join(ARTIFACT_DIR, 'tempo_break_final_mobile.png'), Buffer.from(mobileShot.data, 'base64'));

                ws.close();
                proc.kill();
                process.exit(0);
            };
        });
    });
}

runVerification().catch(err => {
    console.error(err);
    process.exit(1);
});
