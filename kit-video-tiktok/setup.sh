#!/usr/bin/env bash
# One-time installation (Linux / macOS / WSL). Needs: python3 (3.10+), node (18+), ffmpeg with rubberband.
set -e
cd "$(dirname "$0")"
pip install "setuptools<81" numpy onnxruntime kokoro-onnx pyworld faster-whisper
npm install
npx playwright install chromium
mkdir -p models/kokoro
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  [ -f models/kokoro/$f ] || curl -L -o models/kokoro/$f https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f
done
echo "Install complete. Run: bash build.sh"
