// Serves the folder over HTTP (ES modules), renders index.html frame by frame (25 fps) to build/video.mp4,
// or stills: node render.js stills 3.2 10.5
const { chromium } = require('playwright'); const fs = require('fs'); const http = require('http'); const path = require('path'); const { spawn } = require('child_process');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2', '.json': 'application/json' };
const srv = http.createServer((q, r) => { const f = path.join(__dirname, decodeURIComponent(q.url.split('?')[0])); if (!f.startsWith(__dirname) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'Content-Type': TYPES[path.extname(f)] || 'application/octet-stream' }); fs.createReadStream(f).pipe(r); });
(async () => {
  await new Promise(r => srv.listen(0, '127.0.0.1', r)); const port = srv.address().port;
  const tl = JSON.parse(fs.readFileSync(__dirname + '/build/timeline.json'));
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 720, height: 1280 } });
  p.on('pageerror', e => { console.error('PAGE ERROR', e.message); process.exit(1); });
  p.on('console', m => { if (m.type() === 'error') console.error('console:', m.text()); });
  await p.goto(`http://127.0.0.1:${port}/index.html`); await p.waitForFunction(() => window.ready === true);
  await p.evaluate(tl => window.init(tl), tl);
  const args = process.argv.slice(2);
  if (args[0] === 'stills') {
    for (const t of args.slice(1)) { const d = await p.evaluate(t => window.frame(+t, 'image/jpeg'), t); fs.writeFileSync(`${__dirname}/build/still_${t}.jpg`, Buffer.from(d.split(',')[1], 'base64')); }
    await b.close(); srv.close(); return;
  }
  const N = Math.round(tl.total * 25), t0 = Date.now();
  const ff = spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', '25', '-c:v', 'mjpeg', '-i', '-', '-vf', 'scale=1080:1920:flags=lanczos', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', __dirname + '/build/video.mp4'], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < N; i++) {
    const d = await p.evaluate(t => window.frame(t, 'image/jpeg'), i / 25);
    if (!ff.stdin.write(Buffer.from(d.split(',')[1], 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 250 === 0) console.log(i, '/', N, Math.round((Date.now() - t0) / 1000) + 's');
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close(); srv.close(); console.log('done');
})();
