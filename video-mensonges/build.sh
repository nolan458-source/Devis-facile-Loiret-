#!/usr/bin/env bash
# Builds the whole video: voices -> pronunciation check -> 3D render -> sound mix -> final MP4.
set -e
cd "$(dirname "$0")"
python3 tts.py models/kokoro                       # 1. voices + timeline (script.json + voice_profile.json)
python3 check_pronunciation.py || true             # 2. Whisper check (optional, does not block)
cat parts/a_head.html parts/b_world.html parts/c_chars.html parts/d_cast.html parts/e_overlay.html parts/f_direction.html > index.html
node render.js                                     # 3. 3D render, 25 fps, 1080x1920 -> build/video.mp4
python3 mix.py                                     # 4. voices + music + sound effects -> build/mix.wav
ffmpeg -loglevel error -y -i build/video.mp4 -i build/mix.wav -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart mensonges.mp4
echo "Done: mensonges.mp4"
