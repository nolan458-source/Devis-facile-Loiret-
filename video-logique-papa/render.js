// Renders index.html frame by frame (25 fps) into build/video.mp4, or PNG stills: node render.js stills 3.2 10.5
const { chromium } = require('playwright'); const fs = require('fs'); const { spawn } = require('child_process');
(async () => {
  const tl = JSON.parse(fs.readFileSync(__dirname + '/build/timeline.json'));
  const V = process.env.FORMAT === 'tiktok'; const OUTV = V ? '/build/video_tiktok.mp4' : '/build/video.mp4';
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
  p.on('pageerror', e => { console.error('PAGE ERROR', e.message); process.exit(1); });
  await p.goto('file://' + __dirname + '/index.html');
  await p.evaluate(([tl, m]) => window.init(tl, m), [tl, V ? 'v' : 'h']);
  const args = process.argv.slice(2);
  if (args[0] === 'stills') {
    for (const t of args.slice(1)) { const d = await p.evaluate(t => window.frame(+t, 'image/jpeg'), t); fs.writeFileSync(`${__dirname}/build/still${V ? 'V' : ''}_${t}.jpg`, Buffer.from(d.split(',')[1], 'base64')); }
    await b.close(); return;
  }
  const N = Math.round(tl.total * 25);
  const ff = spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', '25', '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', __dirname + OUTV], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let i = 0; i < N; i++) {
    const d = await p.evaluate(t => window.frame(t, 'image/jpeg'), i / 25);
    if (!ff.stdin.write(Buffer.from(d.split(',')[1], 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 250 === 0) console.log(i, '/', N);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close(); console.log('done');
})();
