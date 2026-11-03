const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6';

async function main() {
    const chrome = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
    const proc = spawn(chrome, [
        '--headless=new',
        '--remote-debugging-port=9298',
        '--user-data-dir=C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\\scratch\\chrome_user_data_p1_verify',
        '--window-size=1440,900',
        'http://localhost:8000/'
    ]);

    await new Promise(r => setTimeout(r, 2000));

    http.get('http://127.0.0.1:9298/json', (res) => {
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
                // Clear any old localStorage and reload to ensure clean render
                await send('Runtime.evaluate', {
                    expression: `(() => {
                        localStorage.removeItem('tempo_community_posts');
                        if (window.TempoCommunity && typeof window.TempoCommunity.init === 'function') {
                            window.TempoCommunity.init();
                        }
                    })()`
                });
                await new Promise(r => setTimeout(r, 500));

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

                // Measure live metrics and verify Post 1
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
                        const posts = Array.from(panel.querySelectorAll('[data-post-id]'));
                        const post1 = posts[0];
                        const post2 = posts[1];

                        const p1Style = window.getComputedStyle(post1);
                        const p2Style = window.getComputedStyle(post2);

                        // Check for comments beneath post 1
                        const p1Text = post1.textContent;
                        const hasFessComment = p1Text.includes('fess') || p1Text.includes('Omg same here');
                        const hasSubReply = p1Text.includes('Where can I find a solution');

                        const p1Thumbnails = post1.querySelectorAll('[class*="aspect-"]');
                        const p2Thumbnails = post2.querySelectorAll('[class*="aspect-"]');

                        return {
                            post1: {
                                id: post1.getAttribute('data-post-id'),
                                author: post1.querySelector('span.font-bold')?.textContent?.trim(),
                                content: post1.querySelector('p')?.textContent?.trim(),
                                timestampPresent: p1Text.includes('2 hours ago'),
                                tags: Array.from(post1.querySelectorAll('span.rounded-full')).map(s => s.textContent.trim()),
                                bgHex: rgbToHex(p1Style.backgroundColor),
                                borderHex: rgbToHex(p1Style.borderColor),
                                hasCommentsBeneath: hasFessComment || hasSubReply,
                                fessCommentFound: hasFessComment,
                                subReplyFound: hasSubReply,
                                likesText: post1.querySelector('button[title*="like" i]')?.textContent?.trim(),
                                commentsText: post1.querySelector('button[title*="comment" i]')?.textContent?.trim(),
                                bookmarkPresent: !!post1.querySelector('button[title*="bookmark" i]'),
                                sharePresent: !!post1.querySelector('button[title*="share" i]'),
                                height: Math.round(post1.getBoundingClientRect().height)
                            },
                            post2: {
                                id: post2.getAttribute('data-post-id'),
                                author: post2.querySelector('span.font-bold')?.textContent?.trim(),
                                content: post2.querySelector('p')?.textContent?.trim(),
                                thumbnailsCount: p2Thumbnails.length,
                                height: Math.round(post2.getBoundingClientRect().height)
                            }
                        };
                    })()`
                });

                console.log('=== POST 1 VERIFICATION RESULTS ===');
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
                fs.writeFileSync(path.join(ARTIFACT_DIR, 'post1_no_comments_closeup.png'), Buffer.from(panelShot.data, 'base64'));

                // Capture desktop overview
                const heroClip = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        return { x: 0, y: 0, width: 1440, height: 860, scale: 1 };
                    })()`
                });
                const heroShot = await send('Page.captureScreenshot', { format: 'png', clip: heroClip.result.value });
                fs.writeFileSync(path.join(ARTIFACT_DIR, 'post1_no_comments_desktop.png'), Buffer.from(heroShot.data, 'base64'));

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
