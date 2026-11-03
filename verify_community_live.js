const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function main() {
    const chrome = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
    const proc = spawn(chrome, [
        '--headless=new',
        '--remote-debugging-port=9295',
        '--user-data-dir=C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\\scratch\\chrome_user_data_comm_verify',
        '--window-size=1440,900',
        'http://localhost:8000/'
    ]);

    await new Promise(r => setTimeout(r, 2000));

    http.get('http://127.0.0.1:9295/json', (res) => {
        let raw = '';
        res.on('data', c => raw += c);
        res.on('end', async () => {
            const tabs = JSON.parse(raw);
            const tab = tabs.find(t => t.type === 'page');
            const ws = new WebSocket(tab.webSocketDebuggerUrl);

            let msgId = 1;
            function send(method, params = {}) {
                return new Promise(resolve => {
                    const id = msgId++;
                    const handler = evt => {
                        const d = JSON.parse(evt.data);
                        if (d.id === id) {
                            ws.removeEventListener('message', handler);
                            resolve(d.result);
                        }
                    };
                    ws.addEventListener('message', handler);
                    ws.send(JSON.stringify({ id, method, params }));
                });
            }

            ws.onopen = async () => {
                // Wait for community panel to load
                await send('Runtime.evaluate', {
                    awaitPromise: true,
                    expression: `(async () => {
                        for (let i = 0; i < 50; i++) {
                            const panel = document.querySelector('[data-tempo-ui="entry-community-panel"]');
                            if (panel) {
                                const posts = panel.querySelectorAll('[data-post-id]');
                                if (posts.length >= 2) break;
                            }
                            await new Promise(r => setTimeout(r, 200));
                        }
                        await new Promise(r => setTimeout(r, 600));
                    })()`
                });

                // Measure live metrics and verify colors
                const data = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        function rgbToHex(rgb) {
                            if (!rgb) return '';
                            const match = rgb.match(/\\d+/g);
                            if (!match) return rgb;
                            return '#' + match.slice(0, 3).map(x => parseInt(x).toString(16).padStart(2, '0')).join('').toUpperCase();
                        }

                        const panel = document.querySelector('[data-tempo-ui="entry-community-panel"]');
                        const pStyle = window.getComputedStyle(panel);

                        const iconWrapper = panel.querySelector('.rounded-full');
                        const iconImg = iconWrapper.querySelector('img');
                        const heading = panel.querySelector('h3');
                        const seeAllBtn = panel.querySelector('#btn-see-all-posts');
                        const divider = panel.querySelector('.border-b');
                        const posts = Array.from(panel.querySelectorAll('[data-post-id]'));

                        const iwStyle = iconWrapper ? window.getComputedStyle(iconWrapper) : null;
                        const hStyle = heading ? window.getComputedStyle(heading) : null;
                        const saStyle = seeAllBtn ? window.getComputedStyle(seeAllBtn) : null;

                        const postMetrics = posts.map((post, idx) => {
                            const pStyle = window.getComputedStyle(post);
                            return {
                                index: idx,
                                id: post.getAttribute('data-post-id'),
                                bgHex: rgbToHex(pStyle.backgroundColor),
                                borderHex: rgbToHex(pStyle.borderColor),
                                borderWidth: pStyle.borderWidth,
                                borderRadius: pStyle.borderRadius,
                                contentText: post.querySelector('p')?.textContent?.trim().slice(0, 60),
                                hasAvatar: !!post.querySelector('img'),
                                hasBookmark: !!post.querySelector('button[title*="bookmark" i]'),
                                hasLike: !!post.querySelector('button[title*="like" i]'),
                                hasComment: !!post.querySelector('button[title*="comment" i]'),
                                hasShare: !!post.querySelector('button[title*="share" i]'),
                                tags: Array.from(post.querySelectorAll('span.rounded-full')).map(s => s.textContent.trim())
                            };
                        });

                        return {
                            communitySection: {
                                bgHex: rgbToHex(pStyle.backgroundColor),
                                borderHex: rgbToHex(pStyle.borderColor),
                                borderRadius: pStyle.borderRadius
                            },
                            commentSymbol: {
                                wrapperBgHex: iwStyle ? rgbToHex(iwStyle.backgroundColor) : null,
                                wrapperBorderRadius: iwStyle ? iwStyle.borderRadius : null,
                                imgSrc: iconImg ? iconImg.getAttribute('src') : null,
                                imgComplete: iconImg ? iconImg.complete : false,
                                imgNaturalW: iconImg ? iconImg.naturalWidth : null,
                                imgNaturalH: iconImg ? iconImg.naturalHeight : null,
                                imgRenderedW: iconImg ? iconImg.getBoundingClientRect().width : null,
                                imgRenderedH: iconImg ? iconImg.getBoundingClientRect().height : null
                            },
                            heading: {
                                text: heading ? heading.textContent.trim() : null,
                                colorHex: hStyle ? rgbToHex(hStyle.color) : null,
                                fontWeight: hStyle ? hStyle.fontWeight : null,
                                fontSize: hStyle ? hStyle.fontSize : null
                            },
                            seeAllButton: {
                                text: seeAllBtn ? seeAllBtn.textContent.trim().replace(/\\s+/g, ' ') : null,
                                bgHex: saStyle ? rgbToHex(saStyle.backgroundColor) : null,
                                colorHex: saStyle ? rgbToHex(saStyle.color) : null,
                                borderRadius: saStyle ? saStyle.borderRadius : null
                            },
                            dividerPresent: !!divider,
                            postsCount: posts.length,
                            posts: postMetrics
                        };
                    })()`
                });

                console.log('=== COMMUNITY SECTION VERIFICATION ===');
                console.log(JSON.stringify(data.result.value, null, 2));

                // Capture close-up screenshot of the community section
                const panelClip = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        const panel = document.querySelector('[data-tempo-ui="entry-community-panel"]');
                        const r = panel.getBoundingClientRect();
                        return { x: r.x - 10, y: r.y - 10, width: r.width + 20, height: r.height + 20, scale: 1 };
                    })()`
                });
                const panelShot = await send('Page.captureScreenshot', { format: 'png', clip: panelClip.result.value });
                fs.writeFileSync(path.join(ARTIFACT_DIR, 'community_section_closeup.png'), Buffer.from(panelShot.data, 'base64'));

                // Capture desktop overview (1440x900)
                const heroClip = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        return { x: 0, y: 0, width: 1440, height: 860, scale: 1 };
                    })()`
                });
                const heroShot = await send('Page.captureScreenshot', { format: 'png', clip: heroClip.result.value });
                fs.writeFileSync(path.join(ARTIFACT_DIR, 'community_section_desktop.png'), Buffer.from(heroShot.data, 'base64'));

                // Capture mobile viewport (390px)
                await send('Emulation.setDeviceMetricsOverride', {
                    width: 390,
                    height: 844,
                    deviceScaleFactor: 2,
                    mobile: true
                });
                await new Promise(r => setTimeout(r, 500));
                const mobileClip = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        const panel = document.querySelector('[data-tempo-ui="entry-community-panel"]');
                        const r = panel.getBoundingClientRect();
                        return { x: Math.max(0, r.x - 8), y: Math.max(0, r.y - 8), width: r.width + 16, height: r.height + 16, scale: 2 };
                    })()`
                });
                const mobileShot = await send('Page.captureScreenshot', { format: 'png', clip: mobileClip.result.value });
                fs.writeFileSync(path.join(ARTIFACT_DIR, 'community_section_mobile.png'), Buffer.from(mobileShot.data, 'base64'));

                // Test like interaction
                await send('Runtime.evaluate', {
                    expression: `(() => {
                        const likeBtn = document.querySelector('[data-post-id] button[title*="like" i]');
                        if (likeBtn) likeBtn.click();
                    })()`
                });
                await new Promise(r => setTimeout(r, 300));

                const likeCheck = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        const post = document.querySelector('[data-post-id]');
                        const likeSpan = post.querySelector('button[title*="like" i] span');
                        return { likesText: likeSpan ? likeSpan.textContent : null };
                    })()`
                });
                console.log('Like interaction check:', likeCheck.result.value);

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
