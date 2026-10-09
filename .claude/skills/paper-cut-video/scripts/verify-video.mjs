#!/usr/bin/env node
import {execFileSync, spawnSync} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
const input = args[0];
const value = (flag) => {
  const index = args.indexOf(flag);
  return index >= 0 ? Number(args[index + 1]) : undefined;
};

if (!input) {
  console.error('Usage: node verify-video.mjs final.mp4 [--width 1080 --height 1920 --fps 30]');
  process.exit(2);
}

const file = path.resolve(input);
if (!fs.existsSync(file)) {
  console.error(`File not found: ${file}`);
  process.exit(2);
}

const probe = JSON.parse(execFileSync('ffprobe', [
  '-v', 'error',
  '-show_entries', 'format=duration,size,bit_rate',
  '-show_entries', 'stream=index,codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels,duration',
  '-of', 'json',
  file,
], {encoding: 'utf8'}));

const video = probe.streams.find((stream) => stream.codec_type === 'video');
const audio = probe.streams.find((stream) => stream.codec_type === 'audio');
const failures = [];

if (!video) failures.push('missing video stream');
if (!audio) failures.push('missing audio stream');
if (video && video.codec_name !== 'h264') failures.push(`video codec is ${video.codec_name}, expected h264`);
if (audio && audio.codec_name !== 'aac') failures.push(`audio codec is ${audio.codec_name}, expected aac`);

const expectedWidth = value('--width');
const expectedHeight = value('--height');
const expectedFps = value('--fps');
if (video && expectedWidth && video.width !== expectedWidth) failures.push(`width is ${video.width}, expected ${expectedWidth}`);
if (video && expectedHeight && video.height !== expectedHeight) failures.push(`height is ${video.height}, expected ${expectedHeight}`);

const parseRate = (rate) => {
  const [numerator, denominator] = String(rate).split('/').map(Number);
  return denominator ? numerator / denominator : numerator;
};
const actualFps = video ? parseRate(video.r_frame_rate) : 0;
if (expectedFps && Math.abs(actualFps - expectedFps) > 0.02) failures.push(`fps is ${actualFps}, expected ${expectedFps}`);

const videoDuration = Number(video?.duration ?? probe.format.duration);
const audioDuration = Number(audio?.duration ?? probe.format.duration);
const durationDelta = Math.abs(videoDuration - audioDuration);
if (video && audio && durationDelta > 0.1) failures.push(`audio/video duration delta is ${durationDelta.toFixed(3)}s`);

const decode = spawnSync('ffmpeg', [
  '-hide_banner', '-loglevel', 'error', '-i', file,
  '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-',
], {encoding: 'utf8'});
if (decode.status !== 0) failures.push(`full decode failed: ${(decode.stderr || decode.stdout).trim()}`);

const report = {
  ok: failures.length === 0,
  file,
  video: video ? {codec: video.codec_name, width: video.width, height: video.height, fps: actualFps, duration: videoDuration} : null,
  audio: audio ? {codec: audio.codec_name, sampleRate: Number(audio.sample_rate), channels: audio.channels, duration: audioDuration} : null,
  durationDelta,
  size: Number(probe.format.size),
  failures,
};

console.log(JSON.stringify(report, null, 2));
if (failures.length) process.exit(1);
