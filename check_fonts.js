const http = require('http');
const { spawn } = require('child_process');

async function check() {
    const proc = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
        '--headless=new',
        '--remote-debugging-port=9490',
        '--user-data-dir=C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\\scratch\\chrome_inspect',
        '--window-size=1440,900',
        'http://localhost:8000/'
    ]);
    await new Promise(r => setTimeout(r, 2000));
    http.get('http://127.0.0.1:9490/json', (res) => {
        let raw = '';
        res.on('data', c => raw += c);
        res.on('end', async () => {
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
                const res = await send('Runtime.evaluate', {
                    returnByValue: true,
                    awaitPromise: true,
                    expression: `(async () => {
                        for (let i = 0; i < 50; i++) {
                            const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                            const h2 = card?.querySelector('h2');
                            if (h2) break;
                            await new Promise(r => setTimeout(r, 100));
                        }
                        const card = document.querySelector('[data-tempo-ui="entry-lower-section"]')?.children[0];
                        const h2 = card.querySelector('h2');
                        const p = card.querySelector('p');
                        const h2Style = window.getComputedStyle(h2);
                        const pStyle = window.getComputedStyle(p);
                        return {
                            h2: { fontSize: h2Style.fontSize, lineHeight: h2Style.lineHeight },
                            p: { fontSize: pStyle.fontSize, lineHeight: pStyle.lineHeight },
                            cardWidth: card.getBoundingClientRect().width,
                            cardHeight: card.getBoundingClientRect().height
                        };
                    })()`
                });
                console.log(JSON.stringify(res.result.value, null, 2));
                ws.close();
                proc.kill();
            };
        });
    });
}
check().catch(console.error);
