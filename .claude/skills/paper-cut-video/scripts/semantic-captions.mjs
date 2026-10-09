#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
const value = (flag) => {
  const index = args.indexOf(flag);
  return index >= 0 ? args[index + 1] : undefined;
};

const input = value('--input');
const output = value('--output');
if (!input || !output) {
  console.error('Usage: node semantic-captions.mjs --input transcript.json --output captions.srt');
  process.exit(2);
}

const transcript = JSON.parse(fs.readFileSync(path.resolve(input), 'utf8'));
const sourceSegments = Array.isArray(transcript.segments)
  ? transcript.segments
  : [{words: transcript.words ?? []}];

const words = sourceSegments.flatMap((segment, segmentIndex) =>
  (segment.words ?? []).map((item) => ({
    text: String(item.word ?? item.text ?? '').trim(),
    start: Number(item.start),
    end: Number(item.end),
    segmentIndex,
  })),
).filter((item) => item.text && Number.isFinite(item.start) && Number.isFinite(item.end));

if (!words.length) {
  console.error('No word timestamps found. Expected segments[].words[] or words[].');
  process.exit(2);
}

const normalize = (text) => text
  .replaceAll(',', '，')
  .replaceAll('?', '？')
  .replaceAll('!', '！')
  .replace(/\s+/g, ' ')
  .trim();

const visibleLength = (text) => normalize(text).replace(/[\s，。！？、；：,.!?;:]/g, '').length;
const phraseText = (items) => normalize(items.map((item) => item.text).join(''));
const sentenceEnd = /[。！？!?]$/;
const commaEnd = /[，,；;：:]$/;
const closer = /^(?:吗|呢|吧|啊|呀|嘛|对吧|是吧)[，。！？!?]?$/;
const weakEnd = /(?:在|把|被|给|向|和|与|或|并且|而|但|通过|为了|如果|因为|所以|可以|会|要|就|都|还|去|是|像|当|让|将|从|对|跟|为|才|就是|欢迎关注我)$/;

const phrases = [];
let current = [];
const flush = () => {
  if (current.length) phrases.push(current);
  current = [];
};

words.forEach((word, index) => {
  const previous = current.at(-1);
  if (previous && previous.segmentIndex !== word.segmentIndex) flush();
  current.push(word);
  const next = words[index + 1];
  const pause = next ? next.start - word.end : 0;
  if (!next || sentenceEnd.test(word.text) || commaEnd.test(word.text) || pause > 0.58) flush();
});

const cues = [];
for (const phrase of phrases) {
  const text = phraseText(phrase).replace(/[，。！？!?]$/g, '');
  const previous = cues.at(-1);
  if (!previous) {
    cues.push([...phrase]);
    continue;
  }
  const previousText = phraseText(previous).replace(/[，。！？!?]$/g, '');
  const combined = visibleLength(previousText + text);
  const attach = closer.test(text) || visibleLength(text) <= 3 || weakEnd.test(previousText);
  if (attach && combined <= 30) previous.push(...phrase);
  else cues.push([...phrase]);
}

const splitLong = (items) => {
  if (visibleLength(phraseText(items)) <= 30) return [items];
  const result = [];
  let part = [];
  for (const item of items) {
    if (part.length && visibleLength(phraseText([...part, item])) > 26) {
      result.push(part);
      part = [];
    }
    part.push(item);
  }
  if (part.length) result.push(part);
  return result;
};

const repairedCues = [];
for (const items of cues.flatMap(splitLong)) {
  const text = phraseText(items).replace(/[，。！？!?]/g, '');
  if (closer.test(text) && repairedCues.length) repairedCues.at(-1).push(...items);
  else repairedCues.push(items);
}

const finalCues = repairedCues.map((items, index, all) => {
  let text = phraseText(items);
  if (!/[，。！？]$/.test(text) && /(?:吗|呢|对吧|是吧)$/.test(text)) text += '？';
  const start = Math.max(0, items[0].start - 0.03);
  const nextStart = all[index + 1]?.[0].start;
  const naturalEnd = Math.max(start + 0.55, items.at(-1).end + 0.12);
  const end = nextStart === undefined ? naturalEnd : Math.min(naturalEnd, nextStart - 0.04);
  return {start, end: Math.max(start + 0.5, end), text};
});

const timestamp = (seconds) => {
  const ms = Math.max(0, Math.round(seconds * 1000));
  const hours = Math.floor(ms / 3600000);
  const minutes = Math.floor((ms % 3600000) / 60000);
  const secs = Math.floor((ms % 60000) / 1000);
  const millis = ms % 1000;
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')},${String(millis).padStart(3, '0')}`;
};

const outputPath = path.resolve(output);
fs.mkdirSync(path.dirname(outputPath), {recursive: true});
if (outputPath.endsWith('.json')) {
  fs.writeFileSync(outputPath, `${JSON.stringify(finalCues, null, 2)}\n`);
} else {
  const srt = finalCues.map((cue, index) =>
    `${index + 1}\n${timestamp(cue.start)} --> ${timestamp(cue.end)}\n${cue.text}\n`,
  ).join('\n');
  fs.writeFileSync(outputPath, srt);
}

const isolated = finalCues.filter((cue) => closer.test(cue.text.replace(/[，。！？!?]/g, '')));
console.log(JSON.stringify({output: outputPath, cues: finalCues.length, isolatedParticles: isolated.length}));
if (isolated.length) process.exitCode = 1;
