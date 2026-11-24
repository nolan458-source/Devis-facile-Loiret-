# La ville des compliments : 3D animation (80 s, 1080×1920, TikTok)

Pipeline:
1. `pip install piper-tts pyworld onnxruntime`, plus the French voice `voice-fr-siwis-medium.tar.gz` (github.com/rhasspy/piper, release v0.0.2).
2. `python3 tts.py /path/to/fr-siwis-medium.onnx`: generates the voices (expressive intonation via prosody.py) and `build/timeline.json`.
3. `npm install` (three.js), then `node render.js`: 3D render (WebGL, Playwright) into `build/video.mp4`. `node render.js stills 12.5` renders a single image.
4. `python3 mix.py`: voice, music and sound effects into `build/mix.wav`.
5. `ffmpeg -i build/video.mp4 -i build/mix.wav -c:v copy -c:a aac -b:a 192k -shortest ville_des_compliments.mp4`

Story and lines: `script.json`. Staging (shots, characters, gags): `index.html`.
