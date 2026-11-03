const http = require('http');
const { spawn } = require('child_process');

async function measureText() {
    const proc = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
        '--headless=new',
        '--remote-debugging-port=9499',
        '--user-data-dir=C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\\scratch\\chrome_measure',
        'http://localhost:8000/'
    ]);
    await new Promise(r => setTimeout(r, 2000));
    http.get('http://127.0.0.1:9499/json', (res) => {
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
                const widths = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        const canvas = document.createElement('canvas');
                        const ctx = canvas.getContext('2d');
                        
                        function m(text, font) {
                            ctx.font = font;
                            return Math.round(ctx.measureText(text).width * 100) / 100;
                        }
                        
                        return {
                            h2_34px: {
                                'How are': m('How are', '800 34px Inter, system-ui, sans-serif'),
                                'you feeling': m('you feeling', '800 34px Inter, system-ui, sans-serif'),
                                'today?': m('today?', '800 34px Inter, system-ui, sans-serif'),
                                'How are you': m('How are you', '800 34px Inter, system-ui, sans-serif'),
                                'feeling today?': m('feeling today?', '800 34px Inter, system-ui, sans-serif')
                            },
                            p_24px: {
                                'Take a moment': m('Take a moment', '400 24px Inter, system-ui, sans-serif'),
                                'to check in with': m('to check in with', '400 24px Inter, system-ui, sans-serif'),
                                'yourself.': m('yourself.', '400 24px Inter, system-ui, sans-serif'),
                                'to check in': m('to check in', '400 24px Inter, system-ui, sans-serif'),
                                'with yourself.': m('with yourself.', '400 24px Inter, system-ui, sans-serif')
                            }
                        };
                    })()`
                });
                console.log(JSON.stringify(widths.result.value, null, 2));
                ws.close();
                proc.kill();
            };
        });
    });
}
measureText().catch(console.error);
