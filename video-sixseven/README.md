# La règle du six-seven: 3D animation (66 s, 1080×1920, TikTok)

1. Voices: Kokoro (`pip install kokoro-onnx`, kokoro-v1.0.onnx + voices-v1.0.bin) for the narrator, M. Durand, the principal, and the class chant (6 young voices layered, "six seven" pronounced in English).
   `python3 tts3.py /path/to/kokoro /path/to/piper`, then `python3 build/asrcheck.py` (Whisper pronunciation check).
2. `npm install`, `cat parts/*.html > index.html`, `node render.js` (or `node render.js stills 12.5`).
3. `python3 mix.py`, then `ffmpeg -i build/video.mp4 -i build/mix.wav -c:v copy -c:a aac -b:a 192k -shortest six_seven.mp4`

Prompts for a realistic version (Sora / Veo / Kling): `PROMPT_1MIN.md`, `PROMPT_SIX_SEVEN.md`.
