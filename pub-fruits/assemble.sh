#!/usr/bin/env bash
# Assemble 6 plans (>=10.5 s chacun) + piste audio de 60 s en une vidéo 16:9 1080p de 60 s.
set -euo pipefail
cd "$(dirname "$0")"
X=0.5  # durée des fondus
D=10.5 # durée utile de chaque plan avant fondu
norm="scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=24,format=yuv420p,setsar=1"
ffmpeg -y \
  -i s1.mp4 -i s2.mp4 -i s3.mp4 -i s4.mp4 -i s5.mp4 -i s6.mp4 -i audio.wav \
  -filter_complex "
  [0:v]trim=0:$D,setpts=PTS-STARTPTS,$norm[v0];
  [1:v]trim=0:$D,setpts=PTS-STARTPTS,$norm[v1];
  [2:v]trim=0:$D,setpts=PTS-STARTPTS,$norm[v2];
  [3:v]trim=0:$D,setpts=PTS-STARTPTS,$norm[v3];
  [4:v]trim=0:$D,setpts=PTS-STARTPTS,$norm[v4];
  [5:v]trim=0:$D,setpts=PTS-STARTPTS,$norm,tpad=stop_mode=clone:stop_duration=2[v5];
  [v0][v1]xfade=transition=fade:duration=$X:offset=10[a1];
  [a1][v2]xfade=transition=fade:duration=$X:offset=20[a2];
  [a2][v3]xfade=transition=fade:duration=$X:offset=30[a3];
  [a3][v4]xfade=transition=fade:duration=$X:offset=40[a4];
  [a4][v5]xfade=transition=fade:duration=$X:offset=50,trim=0:60,fade=t=out:st=59:d=1[v];
  [6:a]atrim=0:60,afade=t=out:st=57:d=3[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -crf 16 -preset slow -c:a aac -b:a 320k -movflags +faststart \
  pub_fruits_60s.mp4
echo "OK -> pub_fruits_60s.mp4"
