#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import {execFileSync} from "node:child_process";

const [renderInput, specInput] = process.argv.slice(2);
if (!renderInput || !specInput) {
  console.error("Usage: node verify-render.mjs /absolute/path/to/output.mp4 /absolute/path/to/brand-spec.json");
  process.exit(2);
}

const renderFile = path.resolve(renderInput);
const specFile = path.resolve(specInput);
const spec = JSON.parse(fs.readFileSync(specFile, "utf8"));

let probe;
try {
  probe = JSON.parse(execFileSync("ffprobe", [
    "-v", "error",
    "-show_entries", "format=duration:stream=codec_name,codec_type,width,height,r_frame_rate,channels",
    "-of", "json",
    renderFile
  ], {encoding: "utf8"}));
} catch (error) {
  console.error(`ffprobe failed for ${renderFile}`);
  console.error(error.message);
  process.exit(2);
}

const video = probe.streams.find((stream) => stream.codec_type === "video");
const audio = probe.streams.find((stream) => stream.codec_type === "audio");
const expected = {
  "16:9": [1920, 1080],
  "9:16": [1080, 1920],
  "1:1": [1080, 1080]
}[spec.aspect];
const duration = Number(probe.format.duration);
const fpsParts = (video?.r_frame_rate || "0/1").split("/").map(Number);
const fps = fpsParts[1] ? fpsParts[0] / fpsParts[1] : 0;
const errors = [];

if (!video) errors.push("video stream is missing");
if (video && video.codec_name !== "h264") errors.push(`expected h264 video, found ${video.codec_name}`);
if (spec.music?.mode === "uploaded") {
  if (!audio) errors.push("uploaded-music mode requires an audio stream");
  if (audio && audio.codec_name !== "aac") errors.push(`expected aac audio, found ${audio.codec_name}`);
}
if (spec.music?.mode === "none" && audio) {
  errors.push("designed-beat-grid mode must be silent unless the brand spec records a separately authorized audio mode");
}
if (video && expected && (video.width !== expected[0] || video.height !== expected[1])) {
  errors.push(`expected ${expected[0]}x${expected[1]}, found ${video.width}x${video.height}`);
}
if (fps < 24 || fps > 60) errors.push(`unexpected frame rate: ${fps}`);
if (!Number.isFinite(duration) || Math.abs(duration - spec.duration) > 0.15) {
  errors.push(`duration ${duration} differs from requested ${spec.duration} by more than 0.15s`);
}

const report = {
  ok: errors.length === 0,
  render: renderFile,
  spec: specFile,
  metadata: {
    duration,
    video: video ? {
      codec: video.codec_name,
      width: video.width,
      height: video.height,
      fps
    } : null,
    audio: audio ? {
      codec: audio.codec_name,
      channels: audio.channels
    } : null,
    expectedAudio: spec.music?.mode === "uploaded"
  },
  errors
};

console.log(JSON.stringify(report, null, 2));
process.exit(errors.length ? 1 : 0);
