const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function inspectMascot(vw = 1440, vh = 900) {
    const port = 9380;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', `chrome_data_mascot_inspect_${vw}`);
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
                                    if (card && img && img.complete) break;
                                    await new Promise(r => setTimeout(r, 200));
                                }
                                await new Promise(r => setTimeout(r, 500));
                            })()`
                        });

                        const details = await send('Runtime.evaluate', {
                            returnByValue: true,
                            expression: `(() => {
                                const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                                const parentDiv = card.querySelector('div.flex');
                                const img = card.querySelector('img');

                                const cardR = card.getBoundingClientRect();
                                const parentR = parentDiv.getBoundingClientRect();
                                const imgR = img.getBoundingClientRect();

                                const s = window.getComputedStyle(img);
                                const pStyle = window.getComputedStyle(parentDiv);
                                const cStyle = window.getComputedStyle(card);

                                return {
                                    viewport: { width: window.innerWidth, height: window.innerHeight },
                                    htmlMarkup: img.outerHTML,
                                    parentMarkup: parentDiv.outerHTML,
                                    renderedDimensionsPx: {
                                        width: Math.round(imgR.width * 100) / 100,
                                        height: Math.round(imgR.height * 100) / 100,
                                        aspectRatio: Math.round((imgR.width / imgR.height) * 1000) / 1000
                                    },
                                    naturalDimensionsPx: {
                                        naturalWidth: img.naturalWidth,
                                        naturalHeight: img.naturalHeight,
                                        naturalAspectRatio: Math.round((img.naturalWidth / img.naturalHeight) * 1000) / 1000
                                    },
                                    cssWidthHeight: {
                                        computedWidth: s.width,
                                        computedHeight: s.height,
                                        declaredClasses: img.className
                                    },
                                    constraints: {
                                        maxWidth: s.maxWidth,
                                        maxHeight: s.maxHeight,
                                        minWidth: s.minWidth,
                                        minHeight: s.minHeight
                                    },
                                    objectFitAndRatio: {
                                        objectFit: s.objectFit,
                                        objectPosition: s.objectPosition,
                                        aspectRatio: s.aspectRatio
                                    },
                                    positioning: {
                                        position: s.position,
                                        top: s.top,
                                        right: s.right,
                                        bottom: s.bottom,
                                        left: s.left,
                                        transform: s.transform,
                                        transformOrigin: s.transformOrigin,
                                        margin: {
                                            top: s.marginTop,
                                            right: s.marginRight,
                                            bottom: s.marginBottom,
                                            left: s.marginLeft,
                                            shorthand: s.margin
                                        },
                                        distanceFromCardBottomPx: Math.round((cardR.bottom - imgR.bottom) * 100) / 100,
                                        distanceFromCardRightPx: Math.round((cardR.right - imgR.right) * 100) / 100,
                                        distanceFromCardLeftPx: Math.round((imgR.left - cardR.left) * 100) / 100,
                                        distanceFromCardTopPx: Math.round((imgR.top - cardR.top) * 100) / 100
                                    },
                                    parentContainer: {
                                        className: parentDiv.className,
                                        display: pStyle.display,
                                        flexDirection: pStyle.flexDirection,
                                        alignItems: pStyle.alignItems,
                                        justifyContent: pStyle.justifyContent,
                                        marginTop: pStyle.marginTop,
                                        rect: {
                                            width: Math.round(parentR.width * 100) / 100,
                                            height: Math.round(parentR.height * 100) / 100
                                        }
                                    },
                                    cardContainer: {
                                        padding: cStyle.padding,
                                        rect: {
                                            width: Math.round(cardR.width * 100) / 100,
                                            height: Math.round(cardR.height * 100) / 100
                                        }
                                    }
                                };
                            })()`
                        });

                        ws.close();
                        proc.kill();
                        resolve(details.result.value);
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
    const desktop = await inspectMascot(1440, 900);
    console.log('=== DESKTOP (1440x900) ===');
    console.log(JSON.stringify(desktop, null, 2));

    const mobile = await inspectMascot(390, 844);
    console.log('=== MOBILE (390x844) ===');
    console.log(JSON.stringify(mobile, null, 2));
}

main().catch(console.error);
