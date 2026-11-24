# Logique de papa — animation 2D (60 s, 16:9)

Rebuild:
1. `pip install piper-tts onnxruntime` (for the espeak-ng phonemes), then download the voice (see below).
2. `python3 tts.py /path/to/tom_low`: generates the voice lines and `build/timeline.json`.
3. `python3 mix.py`: voice, music and sound effects into `build/mix.wav`.
4. `node render.js`: renders the frames into `build/video.mp4` (needs Playwright). `node render.js stills 12.5` renders a single image.
5. `ffmpeg -i build/video.mp4 -i build/mix.wav -c:v copy -c:a aac -b:a 192k -shortest logique_de_papa.mp4`

Edit the text in `script.json`; the animation follows the timings automatically.

Voice: male French voice "tom_low" (Mimic 3, ODbL licence, Tjiho's Baudelaire dataset), downloaded from
`https://media.githubusercontent.com/media/MycroftAI/mimic3-voices/master/voices/fr_FR/tom_low/generator.onnx`
along with `phonemes.txt` from raw.githubusercontent.com. Run `python3 tts.py /path/to/tom_low` (the folder that holds both files).
