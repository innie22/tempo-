const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function testOptions() {
    const port = 9305;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', 'chrome_data_test_h1');
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
                                    const breathing = document.querySelector('[title="Practice Breathing"]');
                                    if (breathing) break;
                                    await new Promise(r => setTimeout(r, 200));
                                }
                            })()`
                        });

                        // Test variations
                        const testVariants = await send('Runtime.evaluate', {
                            returnByValue: true,
                            expression: `(() => {
                                const card = document.querySelector('[title="Practice Breathing"]');
                                const textDiv = card.querySelector('div');
                                const h3 = card.querySelector('h3');
                                const p = card.querySelector('p');
                                const img = card.querySelector('img');

                                const results = [];

                                // Measure text width at different font sizes
                                const sizes = ['24px', '23px', '22px', '21px', '20px'];
                                for (const sz of sizes) {
                                    h3.style.fontSize = sz;
                                    h3.style.whiteSpace = 'nowrap';
                                    h3.style.display = 'inline-block';
                                    const textWidth = h3.getBoundingClientRect().width;
                                    results.push({
                                        fontSize: sz,
                                        headingWidth: textWidth,
                                        cardWidth: card.getBoundingClientRect().width,
                                        cardInteriorWidth: card.clientWidth,
                                        mascotWidth: img.getBoundingClientRect().width,
                                        availableSpaceForText: card.clientWidth - img.getBoundingClientRect().width
                                    });
                                }
                                return results;
                            })()`
                        });

                        console.log('Size Measurements:', JSON.stringify(testVariants.result.value, null, 2));

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

testOptions().catch(console.error);
