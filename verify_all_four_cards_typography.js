const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function main() {
    const chrome = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
    const proc = spawn(chrome, [
        '--headless=new',
        '--remote-debugging-port=9288',
        '--user-data-dir=C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\\scratch\\chrome_user_data_all4_typo',
        '--window-size=1440,900',
        'http://localhost:8000/'
    ]);

    await new Promise(r => setTimeout(r, 2000));

    http.get('http://127.0.0.1:9288/json', (res) => {
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
                // Wait for all 4 cards and their images
                await send('Runtime.evaluate', {
                    awaitPromise: true,
                    expression: `(async () => {
                        for (let i = 0; i < 50; i++) {
                            const grid = document.querySelector('[data-tempo-ui="entry-tool-grid"]');
                            if (grid && grid.children.length >= 4) {
                                const imgs = Array.from(grid.querySelectorAll('img'));
                                if (imgs.length >= 4 && imgs.every(img => img.complete && img.naturalWidth > 0)) break;
                            }
                            await new Promise(r => setTimeout(r, 200));
                        }
                        await new Promise(r => setTimeout(r, 500));
                    })()`
                });

                // Detailed inspection of all 4 cards
                const report = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        function rgbToHex(rgb) {
                            if (!rgb) return '';
                            const match = rgb.match(/\\d+/g);
                            if (!match) return rgb;
                            return '#' + match.slice(0, 3).map(x => parseInt(x).toString(16).padStart(2, '0')).join('').toUpperCase();
                        }

                        const grid = document.querySelector('[data-tempo-ui="entry-tool-grid"]');
                        const names = ['Quick Relief', 'Focus Now', 'Learn & Solve', 'Tempo break'];

                        return Array.from(grid.children).map((card, idx) => {
                            const h3 = card.querySelector('h3');
                            const p = card.querySelector('p');
                            const img = card.querySelector('img');
                            const textDiv = card.querySelector('div');

                            const cR = card.getBoundingClientRect();
                            const hR = h3.getBoundingClientRect();
                            const pR = p.getBoundingClientRect();
                            const iR = img ? img.getBoundingClientRect() : null;
                            const dR = textDiv.getBoundingClientRect();

                            const cStyle = window.getComputedStyle(card);
                            const hStyle = window.getComputedStyle(h3);
                            const pStyle = window.getComputedStyle(p);

                            return {
                                index: idx,
                                name: names[idx] || h3.textContent.trim(),
                                title: {
                                    text: h3.textContent.trim().replace(/\\s+/g, ' '),
                                    fontSize: hStyle.fontSize,
                                    fontWeight: hStyle.fontWeight,
                                    fontFamily: hStyle.fontFamily.split(',')[0].replace(/['"]/g, ''),
                                    lineHeight: hStyle.lineHeight,
                                    colorHex: rgbToHex(hStyle.color),
                                    lineCount: h3.getClientRects().length,
                                    width: Math.round(hR.width),
                                    height: Math.round(hR.height)
                                },
                                description: {
                                    text: p.textContent.trim().replace(/\\s+/g, ' '),
                                    fontSize: pStyle.fontSize,
                                    fontWeight: pStyle.fontWeight,
                                    fontFamily: pStyle.fontFamily.split(',')[0].replace(/['"]/g, ''),
                                    lineHeight: pStyle.lineHeight,
                                    colorHex: rgbToHex(pStyle.color),
                                    lineCount: p.getClientRects().length,
                                    width: Math.round(pR.width),
                                    height: Math.round(pR.height)
                                },
                                card: {
                                    bgHex: rgbToHex(cStyle.backgroundColor),
                                    borderHex: rgbToHex(cStyle.borderColor),
                                    width: Math.round(cR.width),
                                    height: Math.round(cR.height),
                                    borderRadius: cStyle.borderRadius
                                },
                                mascot: img ? {
                                    src: img.getAttribute('src'),
                                    renderedW: Math.round(iR.width),
                                    renderedH: Math.round(iR.height),
                                    aspectRatio: (iR.width / iR.height).toFixed(3)
                                } : null,
                                spacing: {
                                    textDivW: Math.round(dR.width),
                                    mascotW: iR ? Math.round(iR.width) : 0,
                                    gapBetweenTextAndMascot: iR ? Math.round(iR.left - dR.right) : 0
                                }
                            };
                        });
                    })()`
                });

                console.log('=== ALL FOUR CARDS TYPOGRAPHY COMPARISON ===');
                console.log(JSON.stringify(report.result.value, null, 2));

                // Capture high-res screenshots
                // 1. Grid of all 4 cards
                const gridClip = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        const el = document.querySelector('[data-tempo-ui="entry-tool-grid"]');
                        const r = el.getBoundingClientRect();
                        return { x: r.x - 12, y: r.y - 12, width: r.width + 24, height: r.height + 24, scale: 1 };
                    })()`
                });
                const gridShot = await send('Page.captureScreenshot', { format: 'png', clip: gridClip.result.value });
                fs.writeFileSync(path.join(ARTIFACT_DIR, 'all_four_cards_typography_grid.png'), Buffer.from(gridShot.data, 'base64'));

                // 2. Tempo break card closeup
                const tbClip = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        const el = document.querySelector('[data-tempo-ui="entry-tool-grid"]').children[3];
                        const r = el.getBoundingClientRect();
                        return { x: r.x - 8, y: r.y - 8, width: r.width + 16, height: r.height + 16, scale: 1 };
                    })()`
                });
                const tbShot = await send('Page.captureScreenshot', { format: 'png', clip: tbClip.result.value });
                fs.writeFileSync(path.join(ARTIFACT_DIR, 'tempo_break_typography_closeup.png'), Buffer.from(tbShot.data, 'base64'));

                // 3. Bottom row comparison (Learn & Solve vs Tempo break)
                const bottomRowClip = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        const grid = document.querySelector('[data-tempo-ui="entry-tool-grid"]');
                        const c2 = grid.children[2].getBoundingClientRect();
                        const c3 = grid.children[3].getBoundingClientRect();
                        const minX = Math.min(c2.left, c3.left);
                        const maxX = Math.max(c2.right, c3.right);
                        const minY = Math.min(c2.top, c3.top);
                        const maxY = Math.max(c2.bottom, c3.bottom);
                        return { x: minX - 10, y: minY - 10, width: (maxX - minX) + 20, height: (maxY - minY) + 20, scale: 1 };
                    })()`
                });
                const bottomRowShot = await send('Page.captureScreenshot', { format: 'png', clip: bottomRowClip.result.value });
                fs.writeFileSync(path.join(ARTIFACT_DIR, 'bottom_row_comparison.png'), Buffer.from(bottomRowShot.data, 'base64'));

                ws.close();
                proc.kill();
                process.exit(0);
            };
        });
    });
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
