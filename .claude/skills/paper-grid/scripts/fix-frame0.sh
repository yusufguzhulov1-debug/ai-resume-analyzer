#!/bin/sh
# HyperFrames 0.8.32 can render frame 0 black on some machines even with a correct initial gsap.set.
# Replace frame 0 with a clone of frame 1; every other frame keeps its position, so lip sync is unchanged.
#   fix-frame0.sh <raw-render.mp4> <out.mp4>
set -e
ffmpeg -v error -y -i "$1" -vf "trim=start_frame=1,setpts=PTS-STARTPTS,tpad=start=1:start_mode=clone" \
  -c:v libx264 -preset slow -crf 14 -pix_fmt yuv420p -r 30 -an "$2"
ffmpeg -v error -i "$2" -frames:v 1 -vf "signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-" -f null - | grep YAVG
