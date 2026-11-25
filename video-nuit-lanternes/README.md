# La Nuit des Lanternes: 3D animation (67 s, 1080×1920, TikTok)

An original story: in Clairbois, the festival lanterns vanish into the forest every year. Lina, who is afraid of the dark, follows hers and finds a giant owl whose babies are afraid of the dark too.

1. `pip install piper-tts pyworld onnxruntime` + the male French voice "tom_low" (MycroftAI/mimic3-voices, voices/fr_FR/tom_low: generator.onnx via media.githubusercontent.com, phonemes.txt via raw.githubusercontent.com).
2. Narration: `pip install kokoro-onnx`, files `kokoro-v1.0.onnx` + `voices-v1.0.bin` (github.com/thewh1teagle/kokoro-onnx, release model-files-v1.0), then
   `python3 tts3.py /path/to/kokoro /path/to/piper` (French voice ff_siwis; the mayor uses Piper fr_FR-tom-medium).
   Former option, Piper voices (huggingface.co/rhasspy/piper-voices): `fr_FR-tom-medium` (narrator) and `fr_FR-upmc-medium` (Jessica = Lina, Pierre = the mayor), .onnx + .onnx.json in one folder.
   `python3 tts2.py /path/to/folder`: narration, intonation per clause (formant-preserving rubberband) and `build/timeline.json`.
3. `npm install`, then rebuild the page: `cat parts/*.html > index.html`, then `node render.js` (or `node render.js stills 12.5`).
4. `python3 mix.py`, then `ffmpeg -i build/video.mp4 -i build/mix.wav -c:v copy -c:a aac -b:a 192k -shortest nuit_des_lanternes.mp4`
