#!/usr/bin/env node
import path from "node:path";
import process from "node:process";
import { parseArgs } from "../lib/args.mjs";
import { pathExists } from "../lib/files.mjs";
import { studioPath } from "../lib/paths.mjs";
import { commandStatus } from "../lib/process.mjs";

const args = parseArgs(process.argv.slice(2));
const workspace = path.resolve(typeof args.workspace === "string" ? args.workspace : process.cwd());
const runtime = path.join(studioPath(workspace), "runtime");
const hyperframesBinary = path.join(runtime, "node_modules", ".bin", "hyperframes");
const hyperframesInstalled = await pathExists(hyperframesBinary);
const hyperframesStatus = hyperframesInstalled ? commandStatus(hyperframesBinary, ["--version"], { timeout: 20_000 }) : null;
const gsapFile = path.join(runtime, "node_modules", "gsap", "dist", "gsap.min.js");
const favstash = commandStatus("favstash", ["--version"]);
const favstashVersion = favstash.version?.match(/\d+\.\d+\.\d+/)?.[0] ?? null;
const [favstashMajor = 0, favstashMinor = 0] = (favstashVersion ?? "").split(".").map(Number);

const nodeMajor = Number(process.versions.node.split(".")[0]);
// Optional: the paper-grid and breakout-card builders and the duplicate check run on Python.
const python = commandStatus("python3", ["--version"]);
const pythonModule = (module) => python.available && commandStatus("python3", ["-c", `import ${module}`]).available;
const checks = {
  node: {
    available: nodeMajor >= 22,
    version: process.versions.node,
    required: ">=22",
  },
  npm: commandStatus("npm", ["--version"]),
  ffmpeg: commandStatus("ffmpeg", ["-version"]),
  ffprobe: commandStatus("ffprobe", ["-version"]),
  ytDlp: commandStatus("yt-dlp", ["--version"]),
  hyperframes: {
    available: Boolean(hyperframesStatus?.available),
    version: hyperframesStatus?.version ?? null,
    expected: "0.8.32",
    location: hyperframesBinary,
    error: hyperframesStatus?.error ?? null,
  },
  gsap: {
    available: await pathExists(gsapFile),
    expected: "3.14.2",
    location: gsapFile,
  },
  python: { available: python.available, version: python.version, note: "Optional: paper-grid, breakout-card and the duplicate check" },
  pythonNumpy: { available: pythonModule("numpy") },
  pythonOpenCv: { available: pythonModule("cv2"), note: "breakout-card plates (pip install opencv-python)" },
  pythonPdq: { available: pythonModule("pdqhash") && pythonModule("scipy"), note: "duplicate check (pip install pdqhash scipy)" },
  pythonPlaywright: { available: pythonModule("playwright"), note: "paper-grid page captures and snapshots (pip install playwright)" },
  swiftc: { available: process.platform === "darwin" && commandStatus("swiftc", ["--version"]).available, note: "breakout-card built-in matte on macOS; elsewhere pass --matte" },
  // Optional: the preferred FavStash route for local coding agents.
  favstashCli: {
    available: favstash.available && (favstashMajor > 0 || favstashMinor >= 4),
    version: favstashVersion,
    required: ">=0.4.0",
    note: "Installation only. Run favstash doctor for the authenticated connection check.",
  },
};

const report = {
  schemaVersion: 1,
  workspace,
  studioInitialized: await pathExists(studioPath(workspace)),
  coreReady: checks.node.available && checks.npm.available && checks.ffmpeg.available && checks.ffprobe.available,
  referenceAnalysisReady: checks.ytDlp.available,
  renderReady: checks.node.available && checks.ffmpeg.available && checks.ffprobe.available && checks.hyperframes.available,
  glassReady: checks.node.available && checks.ffprobe.available && checks.hyperframes.available && checks.gsap.available,
  paperGridReady: checks.hyperframes.available && checks.gsap.available && checks.python.available,
  breakoutCardReady: checks.hyperframes.available && checks.gsap.available && checks.pythonNumpy.available && checks.pythonOpenCv.available,
  duplicateCheckReady: checks.ffmpeg.available && checks.pythonNumpy.available && checks.pythonPdq.available,
  checks,
  guidance: [
    !checks.node.available && "Install Node.js 22 or newer.",
    (!checks.ffmpeg.available || !checks.ffprobe.available) && "Install an FFmpeg build that includes ffprobe.",
    !checks.ytDlp.available && "Install yt-dlp before URL-based reference analysis (for example: brew install yt-dlp or follow the official installer).",
    (!checks.hyperframes.available || !checks.gsap.available) && "If this edit needs HyperFrames or the glass scaffold, run: node <skill>/scripts/init-workspace.mjs --workspace <path> --install",
    !checks.python.available && "Optional: install Python 3 for the paper-grid and breakout-card styles and the duplicate check.",
    checks.python.available && !(checks.pythonNumpy.available && checks.pythonOpenCv.available) && "Optional: pip install numpy opencv-python for breakout-card plates.",
    checks.python.available && !checks.pythonPdq.available && "Optional: pip install pdqhash scipy numpy for the duplicate check.",
    !checks.favstashCli.available && "Optional: for FavStash in Codex or Claude Code, install the CLI with npm install -g @sketric/favstash-mcp@latest (see publish-and-analyze).",
  ].filter(Boolean),
};

if (args.json) {
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`);
} else {
  const icon = (ready) => ready ? "✓" : "✗";
  console.log("FavStash creator-loop tools");
  console.log(`Workspace: ${workspace}`);
  console.log(`${icon(checks.node.available)} Node ${checks.node.version} (requires ${checks.node.required})`);
  console.log(`${icon(checks.npm.available)} npm${checks.npm.version ? ` ${checks.npm.version}` : ""}`);
  console.log(`${icon(checks.ffmpeg.available)} FFmpeg`);
  console.log(`${icon(checks.ffprobe.available)} FFprobe`);
  console.log(`${icon(checks.ytDlp.available)} yt-dlp — required for URL reference analysis`);
  console.log(`${icon(checks.hyperframes.available)} HyperFrames ${checks.hyperframes.version ?? checks.hyperframes.expected} workspace runtime`);
  console.log(`${icon(checks.gsap.available)} GSAP ${checks.gsap.expected} for the glass scaffold`);
  console.log(`${icon(checks.python.available)} Python 3 — optional, for paper-grid, breakout-card and the duplicate check`);
  console.log(`${icon(report.breakoutCardReady)} breakout-card plates (numpy, opencv-python)${checks.swiftc.available ? " with the built-in macOS matte" : ""}`);
  console.log(`${icon(report.duplicateCheckReady)} duplicate check (pdqhash, scipy)`);
  console.log(`${icon(checks.favstashCli.available)} FavStash CLI${checks.favstashCli.version ? ` ${checks.favstashCli.version}` : ""} — optional, for planning and publishing`);
  if (report.guidance.length) {
    console.log("\nNext steps:");
    for (const item of report.guidance) console.log(`- ${item}`);
  }
}

if (args.strict && !report.renderReady) process.exitCode = 1;
