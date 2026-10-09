#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const args = process.argv.slice(2);
const readArg = (name, fallback = null) => {
  const index = args.indexOf(`--${name}`);
  return index >= 0 ? args[index + 1] : fallback;
};

const duration = Number(readArg("duration"));
const bpm = Number(readArg("bpm"));
const output = readArg("output", "audiomap.json");
const beatsPerBar = Number(readArg("beats-per-bar", "4"));
const offset = Number(readArg("offset", "0"));
const pattern = readArg("pattern", "strong,weak,medium,weak")
  .split(",")
  .map((value) => value.trim().toLowerCase())
  .filter(Boolean);

const errors = [];
if (!Number.isFinite(duration) || duration < 1 || duration > 600) {
  errors.push("--duration must be between 1 and 600 seconds");
}
if (!Number.isFinite(bpm) || bpm < 60 || bpm > 180) {
  errors.push("--bpm must be between 60 and 180");
}
if (!Number.isInteger(beatsPerBar) || beatsPerBar < 2 || beatsPerBar > 8) {
  errors.push("--beats-per-bar must be an integer from 2 to 8");
}
if (!Number.isFinite(offset) || offset < 0 || offset >= duration) {
  errors.push("--offset must be non-negative and shorter than duration");
}
if (!pattern.length || pattern.some((value) => !["strong", "medium", "weak"].includes(value))) {
  errors.push("--pattern must be a comma-separated list of strong, medium, or weak");
}

if (errors.length) {
  console.error(JSON.stringify({ok: false, errors}, null, 2));
  process.exit(1);
}

const secondsPerBeat = 60 / bpm;
const events = [];
const beats = [];
const downbeats = [];

for (let index = 0, time = offset; time < duration - 0.000001; index += 1, time = offset + index * secondsPerBeat) {
  const rounded = Number(time.toFixed(3));
  const beatInBar = index % beatsPerBar;
  const bar = Math.floor(index / beatsPerBar) + 1;
  const strength = pattern[index % pattern.length];
  beats.push(rounded);
  if (beatInBar === 0) downbeats.push(rounded);
  events.push({
    t: rounded,
    kind: "BEAT",
    strength,
    bar,
    beat: beatInBar + 1
  });
}

const barDuration = secondsPerBeat * beatsPerBar;
const phrases = [];
for (let start = 0, index = 1; start < duration; start += barDuration * 2, index += 1) {
  phrases.push({
    id: `P${String(index).padStart(2, "0")}`,
    start: Number(start.toFixed(3)),
    end: Number(Math.min(duration, start + barDuration * 2).toFixed(3)),
    role: index === 1 ? "hook-and-build" : "develop-or-resolve"
  });
}

const map = {
  version: 1,
  summary: `${bpm} BPM designed beat grid · ${events.length} beats · ${duration}s · silent`,
  source: {
    type: "designed-beat-grid",
    audio: null,
    silent: true
  },
  duration_sec: duration,
  tempo: {
    bpm,
    beats_per_bar: beatsPerBar,
    seconds_per_beat: Number(secondsPerBeat.toFixed(6)),
    offset_sec: offset,
    accent_pattern: pattern
  },
  grid: {
    beats_sec: beats,
    downbeats_sec: downbeats
  },
  phrases,
  events,
  key_moments: [
    ...events.filter((event) => event.strength === "strong").map((event) => ({
      t: event.t,
      kind: "ACCENT",
      strength: "strong"
    })),
    {
      t: duration,
      kind: "HARD_STOP",
      strength: "strong"
    }
  ]
};

const outputFile = path.resolve(output);
fs.mkdirSync(path.dirname(outputFile), {recursive: true});
fs.writeFileSync(outputFile, `${JSON.stringify(map, null, 2)}\n`);
console.log(JSON.stringify({
  ok: true,
  output: outputFile,
  duration,
  bpm,
  beats: events.length,
  bars: Math.ceil(events.length / beatsPerBar),
  silent: true
}, null, 2));
