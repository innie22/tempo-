const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function main() {
    const chrome = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
    const proc = spawn(chrome, [
        '--headless=new',
        '--remote-debugging-port=9278',
        '--user-data-dir=C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\\scratch\\chrome_user_data_tb_typo',
        '--window-size=1440,900',
        'http://localhost:8000/'
    ]);

    await new Promise(r => setTimeout(r, 2000));

    http.get('http://127.0.0.1:9278/json', (res) => {
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
                    })()`
                });

                // Measure 25px vs 29px
                const variants = [
                    { name: '25px', titleClass: 'text-[22px] sm:text-[25px]' },
                    { name: '29px', titleClass: 'text-[25px] sm:text-[29px]' }
                ];

                for (const v of variants) {
                    await send('Runtime.evaluate', {
                        expression: `(() => {
                            const tb = document.querySelector('[data-tempo-ui="entry-tool-grid"]').children[3];
                            const h3 = tb.querySelector('h3');
                            h3.className = '${v.titleClass} font-bold text-[#736D69] mb-1 group-hover:text-[#5B5551] transition leading-tight whitespace-nowrap';
                        })()`
                    });
                    await new Promise(r => setTimeout(r, 200));

                    const metrics = await send('Runtime.evaluate', {
                        returnByValue: true,
                        expression: `(() => {
                            const tb = document.querySelector('[data-tempo-ui="entry-tool-grid"]').children[3];
                            const h3 = tb.querySelector('h3');
                            const p = tb.querySelector('p');
                            const img = tb.querySelector('img');
                            const textDiv = tb.querySelector('div');

                            const cR = tb.getBoundingClientRect();
                            const hR = h3.getBoundingClientRect();
                            const pR = p.getBoundingClientRect();
                            const iR = img.getBoundingClientRect();
                            const dR = textDiv.getBoundingClientRect();

                            return {
                                variant: '${v.name}',
                                h3FontSize: window.getComputedStyle(h3).fontSize,
                                h3Width: hR.width,
                                h3Lines: h3.getClientRects().length,
                                pWidth: pR.width,
                                pLines: p.getClientRects().length,
                                gapH3ToImg: Math.round(iR.left - hR.right),
                                gapDivToImg: Math.round(iR.left - dR.right),
                                isOverlapping: iR.left < hR.right,
                                cardW: cR.width,
                                cardH: cR.height
                            };
                        })()`
                    });

                    console.log('=== Variant ' + v.name + ' ===');
                    console.log(JSON.stringify(metrics.result.value, null, 2));

                    // Take close-up screenshot
                    const tbClip = await send('Runtime.evaluate', {
                        returnByValue: true,
                        expression: `(() => {
                            const el = document.querySelector('[data-tempo-ui="entry-tool-grid"]').children[3];
                            const r = el.getBoundingClientRect();
                            return { x: r.x - 10, y: r.y - 10, width: r.width + 20, height: r.height + 20, scale: 1 };
                        })()`
                    });
                    const tbShot = await send('Page.captureScreenshot', { format: 'png', clip: tbClip.result.value });
                    fs.writeFileSync(path.join(ARTIFACT_DIR, 'tb_typo_' + v.name + '_closeup.png'), Buffer.from(tbShot.data, 'base64'));

                    // Take grid screenshot
                    const gridClip = await send('Runtime.evaluate', {
                        returnByValue: true,
                        expression: `(() => {
                            const el = document.querySelector('[data-tempo-ui="entry-tool-grid"]');
                            const r = el.getBoundingClientRect();
                            return { x: r.x - 15, y: r.y - 15, width: r.width + 30, height: r.height + 30, scale: 1 };
                        })()`
                    });
                    const gridShot = await send('Page.captureScreenshot', { format: 'png', clip: gridClip.result.value });
                    fs.writeFileSync(path.join(ARTIFACT_DIR, 'tb_typo_' + v.name + '_grid.png'), Buffer.from(gridShot.data, 'base64'));
                }

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
