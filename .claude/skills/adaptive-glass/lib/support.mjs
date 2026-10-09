// The few file, probe and argument helpers the glass scaffold needs, kept here so this style works when installed alone.
import { spawn } from "node:child_process";
import crypto from "node:crypto";
import { createReadStream } from "node:fs";
import fs from "node:fs/promises";
import path from "node:path";

export const STUDIO_DIRECTORY = ".favstash-studio";

export async function pathExists(target) {
  try {
    await fs.access(target);
    return true;
  } catch {
    return false;
  }
}

export async function readJson(target) {
  return JSON.parse(await fs.readFile(target, "utf8"));
}

export async function writeJson(target, value) {
  await fs.mkdir(path.dirname(target), { recursive: true });
  await fs.writeFile(target, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

export async function sha256File(target) {
  const hash = crypto.createHash("sha256");
  for await (const chunk of createReadStream(target)) hash.update(chunk);
  return hash.digest("hex");
}

export function ffprobe(target) {
  return new Promise((resolve, reject) => {
    const child = spawn("ffprobe", ["-v", "error", "-show_entries",
      "format=duration,size,format_name,bit_rate:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
      "-of", "json", target], { stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.once("error", reject);
    child.once("exit", (code) => (code === 0 ? resolve(JSON.parse(stdout)) : reject(new Error(`ffprobe exited ${code}: ${stderr.trim()}`))));
  });
}

export function parseArgs(argv) {
  const parsed = { _: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (!token.startsWith("--")) {
      parsed._.push(token);
      continue;
    }
    const equals = token.indexOf("=");
    if (equals !== -1) {
      parsed[token.slice(2, equals)] = token.slice(equals + 1);
      continue;
    }
    const next = argv[index + 1];
    if (next !== undefined && !next.startsWith("--")) {
      parsed[token.slice(2)] = next;
      index += 1;
    } else {
      parsed[token.slice(2)] = true;
    }
  }
  return parsed;
}

export function requireString(args, key) {
  const value = args[key];
  if (typeof value !== "string" || value.trim() === "") throw new Error(`Missing required option --${key} <value>`);
  return value.trim();
}
