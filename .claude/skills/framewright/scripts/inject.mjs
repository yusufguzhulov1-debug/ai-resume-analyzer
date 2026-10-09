#!/usr/bin/env node
// Replace the block between /*PORTRAIT_START*/ and /*PORTRAIT_END*/ in an HTML file with generated data.
//   node inject.mjs [portrait.js] [index.html]
import fs from 'node:fs';
const src = process.argv[2] || 'portrait.js', html = process.argv[3] || process.env.HTML || 'index.html';
let s = fs.readFileSync(html, 'utf8'); const js = fs.readFileSync(src, 'utf8').trim();
const re = /\/\*PORTRAIT_START\*\/[\s\S]*?\/\*PORTRAIT_END\*\//;
if (!re.test(s)) throw new Error(`markers PORTRAIT_START/END not found in ${html}`);
s = s.replace(re, () => '/*PORTRAIT_START*/\n' + js + '\n/*PORTRAIT_END*/');
fs.writeFileSync(html, s);
console.log(`${html} updated: ${(js.length / 1024).toFixed(0)} KB of polygon data from ${src}`);
