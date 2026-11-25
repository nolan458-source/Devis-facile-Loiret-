# Dans ma ville, tout le monde joue à la BR: 3D animation (61 s, 1080×1920, TikTok)

Original story (Kenzo, the real-life BR) in the "In this town" format, HUSS rhythm measured on the reference: bursts of 3 HUSS 0.2 s apart, a burst every 0.96 s.

1. Voices: Kokoro (`kokoro-onnx`), Kenzo = 50 % ff_siwis + 50 % am_puck (chosen by a Whisper-scored audition), lines timed to the prompt via `at` in `script.json`.
   `python3 tts3.py /path/to/kokoro /path/to/piper`, then `python3 build/asrcheck.py`.
2. `npm install`, `cat parts/*.html > index.html`, `node render.js` (or `node render.js stills 12.5`).
3. `python3 mix.py`, then `ffmpeg -i build/video.mp4 -i build/mix.wav -c:v copy -c:a aac -b:a 192k -shortest br_huss.mp4`

Prompt for a version made with Sora / Veo / Kling: `PROMPT_BR_1MIN.md`.
