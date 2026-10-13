const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function inspect(viewportWidth = 1440, viewportHeight = 900) {
    const port = 9320;
    const userDataDir = path.join(ARTIFACT_DIR, 'scratch', `chrome_data_inspect_${viewportWidth}`);
    const chrome = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

    const proc = spawn(chrome, [
        '--headless=new',
        `--remote-debugging-port=${port}`,
        `--user-data-dir=${userDataDir}`,
        `--window-size=${viewportWidth},${viewportHeight}`,
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
                                    if (section && section.children.length === 3) break;
                                    await new Promise(r => setTimeout(r, 200));
                                }
                                await new Promise(r => setTimeout(r, 500));
                            })()`
                        });

                        const inspectionData = await send('Runtime.evaluate', {
                            returnByValue: true,
                            expression: `(() => {
                                const section = document.querySelector('[data-tempo-ui="entry-lower-section"]');
                                if (!section) return { error: 'Section not found' };

                                const parentR = section.getBoundingClientRect();
                                const parentStyle = window.getComputedStyle(section);

                                const cards = Array.from(section.children);

                                function getElementDetails(el, name) {
                                    if (!el) return null;
                                    const r = el.getBoundingClientRect();
                                    const s = window.getComputedStyle(el);
                                    return {
                                        name,
                                        tagName: el.tagName.toLowerCase(),
                                        text: el.innerText ? el.innerText.trim() : '',
                                        rect: {
                                            x: Math.round(r.x * 100) / 100,
                                            y: Math.round(r.y * 100) / 100,
                                            width: Math.round(r.width * 100) / 100,
                                            height: Math.round(r.height * 100) / 100,
                                            top: Math.round(r.top * 100) / 100,
                                            left: Math.round(r.left * 100) / 100,
                                            bottom: Math.round(r.bottom * 100) / 100,
                                            right: Math.round(r.right * 100) / 100
                                        },
                                        computed: {
                                            fontSize: s.fontSize,
                                            fontWeight: s.fontWeight,
                                            lineHeight: s.lineHeight,
                                            color: s.color,
                                            textAlign: s.textAlign,
                                            padding: s.padding,
                                            margin: s.margin,
                                            width: s.width,
                                            height: s.height
                                        }
                                    };
                                }

                                const cardsData = cards.map((card, idx) => {
                                    const r = card.getBoundingClientRect();
                                    const s = window.getComputedStyle(card);

                                    const badge = card.querySelector('span');
                                    const h2 = card.querySelector('h2');
                                    const p = card.querySelector('p');
                                    const btn = card.querySelector('button');
                                    const placeholder = card.querySelector('[title*="Placeholder"], .border-dashed, div[class*="border-dashed"]');

                                    return {
                                        index: idx + 1,
                                        title: h2 ? h2.innerText.trim() : '',
                                        className: card.className,
                                        rect: {
                                            width: Math.round(r.width * 100) / 100,
                                            height: Math.round(r.height * 100) / 100,
                                            top: Math.round(r.top * 100) / 100,
                                            bottom: Math.round(r.bottom * 100) / 100,
                                            left: Math.round(r.left * 100) / 100,
                                            right: Math.round(r.right * 100) / 100
                                        },
                                        computedStyles: {
                                            width: s.width,
                                            height: s.height,
                                            minHeight: s.minHeight,
                                            maxHeight: s.maxHeight,
                                            maxWidth: s.maxWidth,
                                            minWidth: s.minWidth,
                                            padding: {
                                                top: s.paddingTop,
                                                right: s.paddingRight,
                                                bottom: s.paddingBottom,
                                                left: s.paddingLeft,
                                                shorthand: s.padding
                                            },
                                            border: {
                                                width: s.borderWidth,
                                                style: s.borderStyle,
                                                color: s.borderColor,
                                                radius: s.borderRadius
                                            },
                                            backgroundColor: s.backgroundColor,
                                            boxShadow: s.boxShadow,
                                            display: s.display,
                                            flexDirection: s.flexDirection,
                                            justifyContent: s.justifyContent,
                                            alignItems: s.alignItems,
                                            position: s.position
                                        },
                                        innerElements: {
                                            categoryBadge: getElementDetails(badge, 'categoryBadge'),
                                            heading: getElementDetails(h2, 'heading'),
                                            description: getElementDetails(p, 'description'),
                                            actionButton: getElementDetails(btn, 'actionButton'),
                                            mascotPlaceholder: getElementDetails(placeholder, 'mascotPlaceholder')
                                        }
                                    };
                                });

                                // Calculate gaps
                                const gaps = [];
                                for (let i = 0; i < cards.length - 1; i++) {
                                    const r1 = cards[i].getBoundingClientRect();
                                    const r2 = cards[i + 1].getBoundingClientRect();
                                    gaps.push({
                                        between: (i + 1) + ' and ' + (i + 2),
                                        horizontalGapPx: Math.round((r2.left - r1.right) * 100) / 100,
                                        verticalGapPx: Math.round((r2.top - r1.bottom) * 100) / 100
                                    });
                                }

                                return {
                                    viewport: { width: window.innerWidth, height: window.innerHeight },
                                    parentContainer: {
                                        className: section.className,
                                        rect: {
                                            width: Math.round(parentR.width * 100) / 100,
                                            height: Math.round(parentR.height * 100) / 100,
                                            top: Math.round(parentR.top * 100) / 100,
                                            left: Math.round(parentR.left * 100) / 100
                                        },
                                        computedStyles: {
                                            display: parentStyle.display,
                                            gridTemplateColumns: parentStyle.gridTemplateColumns,
                                            columnGap: parentStyle.columnGap,
                                            rowGap: parentStyle.rowGap,
                                            gap: parentStyle.gap,
                                            paddingTop: parentStyle.paddingTop,
                                            paddingRight: parentStyle.paddingRight,
                                            paddingBottom: parentStyle.paddingBottom,
                                            paddingLeft: parentStyle.paddingLeft,
                                            width: parentStyle.width,
                                            maxWidth: parentStyle.maxWidth
                                        }
                                    },
                                    gaps,
                                    cards: cardsData
                                };
                            })()`
                        });

                        ws.close();
                        proc.kill();
                        resolve(inspectionData.result.value);
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
    console.log('Inspecting at Desktop (1440x900)...');
    const desktop = await inspect(1440, 900);
    fs.writeFileSync(path.join(ARTIFACT_DIR, 'scratch', 'inspect_desktop.json'), JSON.stringify(desktop, null, 2));

    console.log('Inspecting at Tablet (768x1024)...');
    const tablet = await inspect(768, 1024);
    fs.writeFileSync(path.join(ARTIFACT_DIR, 'scratch', 'inspect_tablet.json'), JSON.stringify(tablet, null, 2));

    console.log('Inspecting at Mobile (390x844)...');
    const mobile = await inspect(390, 844);
    fs.writeFileSync(path.join(ARTIFACT_DIR, 'scratch', 'inspect_mobile.json'), JSON.stringify(mobile, null, 2));

    console.log('Inspection complete!');
}

main().catch(console.error);
