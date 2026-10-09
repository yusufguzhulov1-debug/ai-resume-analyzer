#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";

const input = process.argv[2];
if (!input) {
  console.error("Usage: node validate-brand-spec.mjs /absolute/path/to/brand-spec.json");
  process.exit(2);
}

const file = path.resolve(input);
let spec;
try {
  spec = JSON.parse(fs.readFileSync(file, "utf8"));
} catch (error) {
  console.error(`Cannot read valid JSON: ${file}`);
  console.error(error.message);
  process.exit(2);
}

const errors = [];
const requiredStrings = ["brand", "creator", "category", "tagline", "style", "rhythm", "aspect"];
for (const key of requiredStrings) {
  if (typeof spec[key] !== "string" || spec[key].trim() === "") {
    errors.push(`${key} must be a non-empty string`);
  }
}

if (!Array.isArray(spec.services) || spec.services.length < 2 || spec.services.length > 4) {
  errors.push("services must contain 2 to 4 items");
} else if (spec.services.some((item) => typeof item !== "string" || item.trim() === "")) {
  errors.push("every services item must be a non-empty string");
} else if (new Set(spec.services).size !== spec.services.length) {
  errors.push("services must not contain duplicates");
}

if (!Array.isArray(spec.palette) || spec.palette.length < 3 || spec.palette.length > 6) {
  errors.push("palette must contain 3 to 6 colors");
} else if (spec.palette.some((color) => !/^#[0-9a-f]{6}$/i.test(color))) {
  errors.push("every palette item must be a six-digit hex color");
}

if (!["16:9", "9:16", "1:1"].includes(spec.aspect)) {
  errors.push("aspect must be 16:9, 9:16, or 1:1");
}

if (typeof spec.duration !== "number" || spec.duration < 5 || spec.duration > 12) {
  errors.push("duration must be a number from 5 to 12 seconds");
}

if (!Array.isArray(spec.engine) || spec.engine.length < 1) {
  errors.push("engine must contain hyperframes, remotion, or both");
} else {
  const allowed = new Set(["hyperframes", "remotion"]);
  if (spec.engine.some((engine) => !allowed.has(engine))) {
    errors.push("engine contains an unsupported value");
  }
  if (new Set(spec.engine).size !== spec.engine.length) {
    errors.push("engine must not contain duplicates");
  }
}

const visualModes = new Set(["text-illustration", "image-assisted", "mixed"]);
if (!visualModes.has(spec.visualMode)) {
  errors.push("visualMode must be text-illustration, image-assisted, or mixed");
}

if (!spec.media || typeof spec.media !== "object" || !Array.isArray(spec.media.images)) {
  errors.push("media.images must be an array");
} else {
  if (spec.visualMode === "text-illustration" && spec.media.images.length) {
    errors.push("text-illustration mode must not include external images");
  }
  if (["image-assisted", "mixed"].includes(spec.visualMode) && spec.media.images.length === 0) {
    errors.push(`${spec.visualMode} mode requires at least one image`);
  }
  for (const [index, image] of spec.media.images.entries()) {
    if (!image || typeof image !== "object") {
      errors.push(`media.images[${index}] must be an object`);
      continue;
    }
    for (const key of ["role", "source", "working"]) {
      if (typeof image[key] !== "string" || image[key].trim() === "") {
        errors.push(`media.images[${index}].${key} must be a non-empty string`);
      }
    }
    if (!["user-provided", "generated"].includes(image.origin)) {
      errors.push(`media.images[${index}].origin must be user-provided or generated`);
    }
    if (image.origin === "generated" && image.generationApproved !== true) {
      errors.push(`media.images[${index}].generationApproved must be true for generated media`);
    }
  }
}

if (!spec.music || typeof spec.music !== "object" || Array.isArray(spec.music)) {
  errors.push("music must be an object");
} else if (spec.music.mode === "uploaded") {
  if (typeof spec.music.source !== "string" || spec.music.source.trim() === "") {
    errors.push("uploaded music requires music.source");
  }
  if (typeof spec.music.working !== "string" || spec.music.working.trim() === "") {
    errors.push("uploaded music requires music.working");
  }
  if (spec.music.userUploaded !== true) {
    errors.push("uploaded music requires music.userUploaded to be true");
  }
  if (!spec.music.segment || typeof spec.music.segment !== "object") {
    errors.push("uploaded music requires music.segment");
  } else {
    if (typeof spec.music.segment.start !== "number" || spec.music.segment.start < 0) {
      errors.push("music.segment.start must be a non-negative number");
    }
    if (typeof spec.music.segment.duration !== "number" || spec.music.segment.duration <= 0) {
      errors.push("music.segment.duration must be a positive number");
    } else if (typeof spec.duration === "number" && Math.abs(spec.music.segment.duration - spec.duration) > 0.15) {
      errors.push("music.segment.duration must match duration within 0.15 seconds");
    }
  }
} else if (spec.music.mode === "none") {
  if (spec.music.source !== null || spec.music.working !== null) {
    errors.push("music.mode none requires null source and working values");
  }
  if (spec.music.userUploaded !== false) {
    errors.push("music.mode none requires music.userUploaded to be false");
  }
} else {
  errors.push("music.mode must be uploaded or none");
}

if (!spec.timing || typeof spec.timing !== "object") {
  errors.push("timing must be an object");
} else {
  if (typeof spec.timing.map !== "string" || spec.timing.map.trim() === "") {
    errors.push("timing.map must identify the canonical timing map");
  }
  if (spec.music?.mode === "uploaded" && spec.timing.mode !== "uploaded-music") {
    errors.push("uploaded music requires timing.mode uploaded-music");
  }
  if (spec.music?.mode === "none") {
    if (spec.timing.mode !== "designed-beat-grid") {
      errors.push("music.mode none requires timing.mode designed-beat-grid");
    }
    if (typeof spec.timing.bpm !== "number" || spec.timing.bpm < 60 || spec.timing.bpm > 180) {
      errors.push("designed beat grid requires timing.bpm from 60 to 180");
    }
    if (!Number.isInteger(spec.timing.beatsPerBar) || spec.timing.beatsPerBar < 2 || spec.timing.beatsPerBar > 8) {
      errors.push("designed beat grid requires timing.beatsPerBar from 2 to 8");
    }
    if (typeof spec.timing.offset !== "number" || spec.timing.offset < 0) {
      errors.push("designed beat grid requires a non-negative timing.offset");
    }
    if (!Array.isArray(spec.timing.accentPattern) || spec.timing.accentPattern.length < 1) {
      errors.push("designed beat grid requires a non-empty timing.accentPattern");
    } else if (spec.timing.accentPattern.some((value) => !["strong", "medium", "weak"].includes(value))) {
      errors.push("timing.accentPattern may contain only strong, medium, or weak");
    }
  }
}

const expectedDimensions = {
  "16:9": [1920, 1080],
  "9:16": [1080, 1920],
  "1:1": [1080, 1080]
}[spec.aspect];
if (!spec.delivery || typeof spec.delivery !== "object") {
  errors.push("delivery must be an object");
} else {
  if (expectedDimensions && (spec.delivery.width !== expectedDimensions[0] || spec.delivery.height !== expectedDimensions[1])) {
    errors.push(`delivery dimensions must be ${expectedDimensions[0]}x${expectedDimensions[1]} for ${spec.aspect}`);
  }
  if (![24, 30, 60].includes(spec.delivery.fps)) {
    errors.push("delivery.fps must be 24, 30, or 60");
  }
  if (spec.delivery.format !== "mp4") {
    errors.push("delivery.format must be mp4");
  }
}

if (errors.length) {
  console.error(JSON.stringify({ok: false, file, errors}, null, 2));
  process.exit(1);
}

console.log(JSON.stringify({
  ok: true,
  file,
  summary: {
    brand: spec.brand,
    visualMode: spec.visualMode,
    imageCount: spec.media.images.length,
    aspect: spec.aspect,
    duration: spec.duration,
    engine: spec.engine,
    musicMode: spec.music.mode,
    timingMode: spec.timing.mode,
    bpm: spec.timing.bpm ?? null,
    accentPattern: spec.timing.accentPattern ?? null
  }
}, null, 2));
