# Logique de papa — animation 2D (60 s, 16:9)

Rebuild:
1. `pip install piper-tts` and download the French voice `voice-fr-siwis-medium.tar.gz` (github.com/rhasspy/piper, release v0.0.2), then extract it.
2. `python3 tts.py /path/to/fr-siwis-medium.onnx`: generates the voice lines and `build/timeline.json`.
3. `python3 mix.py`: voice, music and sound effects into `build/mix.wav`.
4. `node render.js`: renders the frames into `build/video.mp4` (needs Playwright). `node render.js stills 12.5` renders a single image.
5. `ffmpeg -i build/video.mp4 -i build/mix.wav -c:v copy -c:a aac -b:a 192k -shortest logique_de_papa.mp4`

Edit the text in `script.json`; the animation follows the timings automatically.
