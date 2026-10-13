const fs = require('fs');

// Read PNG and parse chunk or use canvas/jimp/pngjs if available, or just decode PNG
// Let's see if we have any png parser or we can inspect via Chrome Runtime.evaluate!
const http = require('http');
const { spawn } = require('child_process');

async function inspectMascotPixels() {
    const proc = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
        '--headless=new',
        '--remote-debugging-port=9690',
        '--user-data-dir=C:\\Users\\YEN NHI\\.gemini\\antigravity\\brain\\6baf9c9e-16aa-475f-b2c0-d941b08ac2c6\\scratch\\chrome_inspect_mascot',
        'http://localhost:8000/'
    ]);
    await new Promise(r => setTimeout(r, 2000));
    http.get('http://127.0.0.1:9690/json', (res) => {
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
                const result = await send('Runtime.evaluate', {
                    returnByValue: true,
                    awaitPromise: true,
                    expression: `(async () => {
                        const img = new Image();
                        img.src = 'assets/self-check-mascot.png';
                        await new Promise(r => img.onload = r);
                        const canvas = document.createElement('canvas');
                        canvas.width = img.naturalWidth;
                        canvas.height = img.naturalHeight;
                        const ctx = canvas.getContext('2d');
                        ctx.drawImage(img, 0, 0);
                        const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;

                        let minX = canvas.width, maxX = 0, minY = canvas.height, maxY = 0;
                        for (let y = 0; y < canvas.height; y++) {
                            for (let x = 0; x < canvas.width; x++) {
                                const alpha = data[(y * canvas.width + x) * 4 + 3];
                                if (alpha > 10) {
                                    if (x < minX) minX = x;
                                    if (x > maxX) maxX = x;
                                    if (y < minY) minY = y;
                                    if (y > maxY) maxY = y;
                                }
                            }
                        }

                        // Also find where the main body is vs the floating bubbles on the left
                        // Find alpha > 50 columns
                        const colOpaqueCounts = [];
                        for (let x = 0; x < canvas.width; x++) {
                            let count = 0;
                            for (let y = 0; y < canvas.height; y++) {
                                if (data[(y * canvas.width + x) * 4 + 3] > 50) count++;
                            }
                            colOpaqueCounts.push(count);
                        }

                        return {
                            naturalWidth: img.naturalWidth,
                            naturalHeight: img.naturalHeight,
                            boundingBox: { minX, maxX, minY, maxY, width: maxX - minX + 1, height: maxY - minY + 1 },
                            colOpaqueCounts: colOpaqueCounts.slice(0, 50) // first 50 columns on the left
                        };
                    })()`
                });
                console.log(JSON.stringify(result.result.value, null, 2));
                ws.close();
                proc.kill();
            };
        });
    });
}
inspectMascotPixels().catch(console.error);
