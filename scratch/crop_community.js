const http = require('http');
const { spawn } = require('child_process');
const fs = require('fs');

const chrome = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const proc = spawn(chrome, [
    '--headless=new',
    '--remote-debugging-port=9290',
    '--user-data-dir=C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\\scratch\\chrome_user_data_crop',
    'about:blank'
]);

setTimeout(() => {
    http.get('http://127.0.0.1:9290/json', (res) => {
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
                await send('Page.navigate', { url: 'file:///C:/Users/YEN%20NHI/.gemini/antigravity/brain/6baf9c9e-16aa-475f-b2c0-d941b08ac2c6/.user_uploaded/media_1791549782292_9e5f8ddc.png' });
                await new Promise(r => setTimeout(r, 1000));
                
                const dims = await send('Runtime.evaluate', {
                    returnByValue: true,
                    expression: `(() => {
                        const img = document.querySelector('img');
                        const r = img.getBoundingClientRect();
                        return { w: r.width, h: r.height, naturalW: img.naturalWidth, naturalH: img.naturalHeight };
                    })()`
                });
                console.log('Image dimensions:', dims.result.value);

                const iw = dims.result.value.w;
                const ih = dims.result.value.h;
                const clip = {
                    x: Math.round(iw * 0.61),
                    y: Math.round(ih * 0.155),
                    width: Math.round(iw * 0.31),
                    height: Math.round(ih * 0.60),
                    scale: 1
                };
                const shot = await send('Page.captureScreenshot', { format: 'png', clip });
                fs.writeFileSync('C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\\scratch\\community_ref_crop.png', Buffer.from(shot.data, 'base64'));
                console.log('Saved community_ref_crop.png');
                ws.close();
                proc.kill();
                process.exit(0);
            };
        });
    });
}, 2000);
