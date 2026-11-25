# BOING ! Le gardien de Boulanville: 3D animation (56 s, 1080×1920, TikTok)

An original story: Timéo, who jumps everywhere ("BOING!"), becomes Boulanville's goalkeeper for the match against Grandeville. The losing town repaints its town hall pink.

1. Voices: `pip install kokoro-onnx pyworld`, Kokoro (kokoro-v1.0.onnx + voices-v1.0.bin, github.com/thewh1teagle/kokoro-onnx) for the narrator, Piper `fr_FR-tom-medium` / `fr_FR-upmc-medium` (huggingface.co/rhasspy/piper-voices) for the coach and the neighbour.
   `python3 tts3.py /path/to/kokoro /path/to/piper`: target pitch per voice in `voice_map.json`, pronunciation fixes in `tts3.py` (FIXES).
2. `npm install`, `cat parts/*.html > index.html`, `node render.js` (or `node render.js stills 12.5`).
3. `python3 mix.py`, then `ffmpeg -i build/video.mp4 -i build/mix.wav -c:v copy -c:a aac -b:a 192k -shortest boing.mp4`
