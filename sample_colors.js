const http = require('http');
const { spawn } = require('child_process');

const chrome = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const proc = spawn(chrome, [
    '--headless=new',
    '--remote-debugging-port=9292',
    '--user-data-dir=C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\\scratch\\chrome_user_data_sample',
    'about:blank'
]);

setTimeout(() => {
    http.get('http://127.0.0.1:9292/json', (res) => {
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
                await send('Page.navigate', { url: 'file:///C:/Users/YEN%20NHI/.gemini/antigravity/brain/6baf9c9e-16aa-475f-b2c0-d941b08ac2c6/scratch/community_ref_crop.png' });
                await new Promise(r => setTimeout(r, 1000));
                const colors = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        const img = document.querySelector('img');
                        const canvas = document.createElement('canvas');
                        canvas.width = img.naturalWidth;
                        canvas.height = img.naturalHeight;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(img, 0, 0);

                        function getHex(x, y) {
                            const p = ctx.getImageData(x, y, 1, 1).data;
                            return '#' + [p[0], p[1], p[2]].map(v => v.toString(16).padStart(2, '0')).join('').toUpperCase();
                        }

                        return {
                            panelBg: getHex(100, 20),
                            commentIconBg: getHex(32, 51),
                            seeAllBg: getHex(205, 51),
                            post1Bg: getHex(100, 100),
                            post1Border: getHex(25, 100),
                            divider: getHex(100, 66)
                        };
                    })()`
                });
                console.log('Sampled colors:', colors.result.value);
                ws.close();
                proc.kill();
                process.exit(0);
            };
        });
    });
}, 2000);
