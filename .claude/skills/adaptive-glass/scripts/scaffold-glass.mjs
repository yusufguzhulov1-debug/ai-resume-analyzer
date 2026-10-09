#!/usr/bin/env node
import process from "node:process";
import { buildGlassComposition } from "../lib/glass.mjs";
import { parseArgs, requireString } from "../lib/support.mjs";

const args = parseArgs(process.argv.slice(2));
if (args.help || !args._[0]) {
  console.log("Usage: node <skill>/scripts/scaffold-glass.mjs <scene-config.json> --output <new-directory> [--workspace <path>] [--gsap <gsap.min.js>]");
  process.exit(args.help ? 0 : 1);
}

try {
  const summary = await buildGlassComposition(args._[0], requireString(args, "output"), {
    workspace: typeof args.workspace === "string" ? args.workspace : undefined,
    gsap: typeof args.gsap === "string" ? args.gsap : undefined,
  });
  console.log(JSON.stringify(summary));
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
