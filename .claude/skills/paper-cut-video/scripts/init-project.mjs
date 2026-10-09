#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const skillDir = path.resolve(here, '..');
const args = process.argv.slice(2);
const outputIndex = args.indexOf('--output');
const outputArg = outputIndex >= 0 ? args[outputIndex + 1] : args[0];

if (!outputArg) {
  console.error('Usage: node scripts/init-project.mjs --output ./paper-cut-remotion');
  process.exit(2);
}

const output = path.resolve(outputArg);
if (fs.existsSync(output) && fs.readdirSync(output).length > 0) {
  console.error(`Refusing to overwrite non-empty directory: ${output}`);
  process.exit(2);
}

fs.mkdirSync(output, {recursive: true});
fs.cpSync(path.join(skillDir, 'templates', 'remotion'), output, {recursive: true});

const assetDir = path.join(output, 'public', 'assets');
fs.mkdirSync(assetDir, {recursive: true});
fs.copyFileSync(
  path.join(skillDir, 'assets', 'paper-bg-vertical.png'),
  path.join(assetDir, 'paper-bg-vertical.png'),
);

console.log(`Created paper-cut Remotion starter: ${output}`);
console.log('Next: cd into the project, run npm install, then npm run start');
