#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import {execFileSync} from "node:child_process";

const input = process.argv[2];
if (!input) {
  console.error("Usage: node inspect-uploaded-music.mjs /absolute/path/to/user-upload");
  process.exit(2);
}

const file = path.resolve(input);
if (!fs.existsSync(file) || !fs.statSync(file).isFile()) {
  console.error(JSON.stringify({ok: false, file, errors: ["uploaded file does not exist"]}, null, 2));
  process.exit(1);
}

let probe;
try {
  probe = JSON.parse(execFileSync("ffprobe", [
    "-v", "error",
    "-show_entries", "format=duration,format_name,size:stream=codec_name,codec_type,sample_rate,channels",
    "-of", "json",
    file
  ], {encoding: "utf8"}));
} catch (error) {
  console.error(JSON.stringify({ok: false, file, errors: ["ffprobe could not read the upload"]}, null, 2));
  process.exit(1);
}

const audio = probe.streams.find((stream) => stream.codec_type === "audio");
const video = probe.streams.find((stream) => stream.codec_type === "video");
const duration = Number(probe.format?.duration);
const errors = [];

if (!audio) errors.push("upload does not contain an audio stream");
if (!Number.isFinite(duration) || duration <= 0.5) errors.push("audio duration must be longer than 0.5 seconds");

const report = {
  ok: errors.length === 0,
  file,
  metadata: {
    format: probe.format?.format_name || null,
    sizeBytes: Number(probe.format?.size || 0),
    duration,
    audio: audio ? {
      codec: audio.codec_name,
      sampleRate: Number(audio.sample_rate || 0),
      channels: audio.channels
    } : null,
    containsVideo: Boolean(video)
  },
  errors
};

console.log(JSON.stringify(report, null, 2));
process.exit(errors.length ? 1 : 0);
