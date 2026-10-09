import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { ffprobe, pathExists, readJson, sha256File, STUDIO_DIRECTORY, writeJson } from "./support.mjs";

export const GLASS_ASSETS = fileURLToPath(new URL("../assets/", import.meta.url));
export const LAYOUTS = new Set(["face", "split-half", "split-third", "full-proof"]);
export const SCENE_TYPES = new Set(["none", "media-bleed", "media-card", "media-wide", "proof", "diagram"]);
const MATERIALS = new Set(["soft", "optical"]);
const TONES = new Set(["dark", "light"]);
const IMAGE_EXTENSIONS = new Set([".png", ".jpg", ".jpeg", ".webp"]);
const GSAP_IN_RUNTIME = path.join("runtime", "node_modules", "gsap", "dist", "gsap.min.js");
const PALETTE_VARIABLES = {
  bg: "background", glow: "backgroundGlow", deep: "backgroundDeep", ink: "headingInk",
  text: "text", muted: "mutedText", glass: "glassBase", rim: "glassRim", accent: "accentFill",
  "label-base": "labelBase", "grid-opacity": "gridOpacity",
};

const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[character]);
const lines = (value) => String(value ?? "").split("\n").map((line) => `<span class="line">${escapeHtml(line)}</span>`).join("");
const js = (value) => JSON.stringify(value);
const round = (value) => Math.round(value * 10000) / 10000;

// Walk up from the config to the workspace whose runtime has GSAP installed.
export async function findRuntimeGsap(start) {
  let directory = path.resolve(start);
  for (;;) {
    const candidate = path.basename(directory) === STUDIO_DIRECTORY
      ? path.join(directory, GSAP_IN_RUNTIME)
      : path.join(directory, STUDIO_DIRECTORY, GSAP_IN_RUNTIME);
    if (await pathExists(candidate)) return candidate;
    const parent = path.dirname(directory);
    if (parent === directory) return null;
    directory = parent;
  }
}

async function mediaDuration(file, probe) {
  const result = await probe(file);
  return Number(result?.format?.duration ?? 0);
}

export async function loadPalette(config, resolve) {
  const catalogue = await readJson(path.join(GLASS_ASSETS, "palettes.json"));
  const name = config.palette ?? catalogue.default;
  const base = catalogue.palettes[name];
  if (!base) throw new Error(`Unknown palette "${name}". Choose one of: ${Object.keys(catalogue.palettes).join(", ")}`);
  const overrides = config.paletteFile ? await readJson(resolve(config.paletteFile)) : {};
  const palette = { name, ...base, ...overrides };
  for (const field of [...Object.values(PALETTE_VARIABLES), "captionBacking", "captionBackingOpacity"]) {
    if (palette[field] === undefined) throw new Error(`Palette is missing ${field}`);
  }
  return palette;
}

// Validate everything before writing, then create a new, silent composition.
export async function buildGlassComposition(configPath, outputPath, options = {}) {
  const probe = options.probe ?? ffprobe;
  const configFile = path.resolve(configPath);
  const config = await readJson(configFile);
  const base = path.dirname(configFile);
  const resolve = (value) => path.resolve(base, value);
  const output = path.resolve(outputPath);
  if (await pathExists(output)) throw new Error("Output already exists; choose a new revision directory.");

  const fps = config.fps ?? 30;
  const frames = config.durationFrames;
  if (fps !== 30 || !Number.isInteger(frames) || frames <= 0) {
    throw new Error("This tested starter requires 30 fps and a positive integer durationFrames.");
  }
  const duration = frames / fps;
  const palette = await loadPalette(config, resolve);
  const layouts = config.layoutsFile ? await readJson(resolve(config.layoutsFile)) : await readJson(path.join(GLASS_ASSETS, "layouts.json"));
  if (typeof config.cameraSource !== "string") throw new Error("Supply cameraSource, the prepared camera plate.");
  const camera = resolve(config.cameraSource);
  if (!(await pathExists(camera))) throw new Error(`Missing cameraSource: ${camera}`);
  const gsap = options.gsap ? path.resolve(options.gsap)
    : config.gsapSource ? resolve(config.gsapSource)
    : await findRuntimeGsap(options.workspace ?? base);
  if (!gsap || !(await pathExists(gsap)) || path.extname(gsap) !== ".js") {
    throw new Error("GSAP was not found. Run init-workspace.mjs --install for this workspace, or pass --gsap <local gsap.min.js>.");
  }
  if (await mediaDuration(camera, probe) + 1 / fps < duration) throw new Error("Camera plate does not cover the composition duration.");

  const scenes = config.scenes;
  if (!Array.isArray(scenes) || scenes.length === 0) throw new Error("Add at least one scene.");
  const files = new Set([camera]);
  const ids = new Set();
  let cursor = 0;
  for (const scene of scenes) {
    const { id, startFrame: start, endFrame: end, layout, type } = scene;
    if (!/^[a-z][a-z0-9-]*$/.test(id ?? "") || ids.has(id)) throw new Error("Scene IDs must be unique lowercase identifiers.");
    ids.add(id);
    if (!Number.isInteger(start) || !Number.isInteger(end) || start !== cursor || end <= start) {
      throw new Error("Scenes must cover the composition in order without gaps or overlap.");
    }
    cursor = end;
    if (!LAYOUTS.has(layout) || !SCENE_TYPES.has(type)) throw new Error(`Unknown layout or type in scene ${id}.`);
    const material = scene.glassMaterial ?? config.glassMaterial ?? "optical";
    const tone = scene.glassTone ?? config.glassTone ?? "dark";
    if (!MATERIALS.has(material)) {
      throw new Error("glassMaterial must be soft or optical; true refraction needs a verified native HyperFrames block.");
    }
    if (!TONES.has(tone)) throw new Error("glassTone must be dark or light.");
    if (layout === "full-proof" && !["media-bleed", "media-wide", "proof"].includes(type)) {
      throw new Error("Full proof needs a detailed media crop; simple cards and diagrams fit a split.");
    }
    if (type === "none" && layout !== "face") throw new Error("A supporting-content layout needs actual content.");
    if (type === "media-bleed" && layout === "face") throw new Error("Edge-to-edge proof needs a split or full-proof layout.");
    if (type === "diagram" && !(scene.items?.length >= 1 && scene.items.length <= 3)) {
      throw new Error("The starter diagram supports one to three short items.");
    }
    let mediaCursor = start;
    for (const media of scene.media ?? []) {
      const { startFrame: from, endFrame: to } = media;
      if (!["contain", "cover", undefined].includes(media.fit)) throw new Error("Media fit must be contain or cover; use a deliberate crop.");
      if (!Number.isInteger(from) || !Number.isInteger(to) || from !== mediaCursor || to <= from || to > end) {
        throw new Error("Prepared media must cover its scene consecutively.");
      }
      mediaCursor = to;
      const file = resolve(media.path ?? "");
      if (!media.path || !(await pathExists(file))) throw new Error(`Missing prepared media: ${file}`);
      files.add(file);
      if (!IMAGE_EXTENSIONS.has(path.extname(file).toLowerCase())
        && await mediaDuration(file, probe) + 1 / fps < (to - from) / fps) {
        throw new Error(`Prepared clip is shorter than its selected range: ${file}`);
      }
    }
    if (["media-bleed", "media-card", "media-wide", "proof"].includes(type) && mediaCursor !== end) {
      throw new Error("A media scene needs complete prepared media coverage.");
    }
  }
  if (cursor !== frames) throw new Error("Last scene must end at durationFrames.");

  // Writing starts here. Creating the directory fails if it appeared meanwhile.
  await fs.mkdir(path.dirname(output), { recursive: true });
  await fs.mkdir(output);
  await fs.mkdir(path.join(output, "assets"));
  const mapping = new Map();
  const manifest = [];
  for (const source of [...files].sort()) {
    const digest = await sha256File(source);
    const copiedTo = `assets/${digest.slice(0, 16)}${path.extname(source).toLowerCase()}`;
    if (!(await pathExists(path.join(output, copiedTo)))) await fs.copyFile(source, path.join(output, copiedTo));
    mapping.set(source, copiedTo);
    manifest.push({ source, copiedTo, sha256: digest });
  }
  await fs.copyFile(gsap, path.join(output, "assets", "gsap.min.js"));

  const variables = `:root{${Object.entries(PALETTE_VARIABLES).map(([name, field]) => `--${name}:${palette[field]}`).join(";")}}`;
  const css = `${await fs.readFile(path.join(GLASS_ASSETS, "glass.css"), "utf8")}\n${variables}\n`;
  await fs.writeFile(path.join(output, "style.css"), css);
  await writeJson(path.join(output, "palette.json"), palette);
  await writeJson(path.join(output, "layouts.json"), layouts);

  const cameraUrl = mapping.get(camera);
  const cameraVideo = (id) => `<video id="${id}" class="clip" data-layout-allow-overflow src="${cameraUrl}" data-start="0" data-duration="${duration}" data-track-index="0" muted playsinline></video>`;
  const pane = (layout) => layouts[layout === "split-half" ? "half" : "third"];
  const initial = [];
  const timeline = [];
  const sections = [];
  const anchors = [];
  const cameraState = (layout) => {
    const state = [
      ["#camFull", { opacity: layout === "face" ? 1 : 0 }],
      ["#camSplit", { opacity: layout.startsWith("split") ? 1 : 0 }],
    ];
    if (layout.startsWith("split")) {
      const { paneTop, paneHeight, foreground, background } = pane(layout);
      state.push(["#camSplit", { top: paneTop, height: paneHeight }], ["#splitVideo", foreground], ["#splitBackground", background]);
    }
    return state;
  };

  for (const scene of scenes) {
    const { id, layout, type } = scene;
    const start = scene.startFrame / fps;
    const end = scene.endFrame / fps;
    const material = scene.glassMaterial ?? config.glassMaterial ?? "optical";
    const tone = scene.glassTone ?? config.glassTone ?? "dark";
    const glassAttributes = `data-glass="${material}" data-glass-tone="${tone}"`;
    const label = escapeHtml(scene.label);
    const footer = escapeHtml(scene.footer);
    const media = (scene.media ?? []).map((item, index) => {
      const source = resolve(item.path);
      const image = IMAGE_EXTENSIONS.has(path.extname(source).toLowerCase());
      const fit = item.fit ?? (layout === "full-proof" || type === "media-bleed" ? "cover" : "contain");
      const attributes = `id="media-${id}-${index}" class="clip" data-layout-allow-overflow src="${mapping.get(source)}" `
        + `data-start="${round(item.startFrame / fps)}" data-duration="${round((item.endFrame - item.startFrame) / fps)}" data-track-index="2" `
        + `style="object-fit:${fit};object-position:${escapeHtml(item.objectPosition ?? "50% 50%")}"`;
      return image ? `<img ${attributes} alt="Supporting source">` : `<video ${attributes} muted playsinline></video>`;
    }).join("");
    const sheen = `<div class="sheen" id="sheen-${id}" data-layout-ignore></div>`;
    const viewport = `<div class="brollViewport">${media}</div>`;
    let content = "";
    if (type === "none") {
      content = label ? `<div class="brand">${label}</div>` : "";
    } else if (type === "media-bleed") {
      const height = layout === "full-proof" ? 1920 : pane(layout).paneTop;
      content = `<div class="bleedViewport" style="height:${height}px">${media}</div>`;
    } else if (type === "media-card") {
      content = `<div ${glassAttributes} class="glass compact mediaPanel">${sheen}`
        + (label ? `<div class="promoMeta">${label}</div>` : "")
        + (scene.title ? `<div class="promoTitle">${lines(scene.title)}</div>` : "")
        + viewport + (footer ? `<div class="promoFooter">${footer}</div>` : "") + "</div>";
    } else if (type === "media-wide" || type === "proof") {
      const heading = (label ? `<div class="eyebrow">${label}</div>` : "")
        + (scene.title ? `<div class="title">${lines(scene.title)}</div>` : "")
        + (scene.subtitle ? `<div class="subtitle">${escapeHtml(scene.subtitle)}</div>` : "");
      if (heading) content += `<div class="heading">${heading}</div>`;
      if (type === "proof" && scene.labels?.length) {
        content += `<div class="proofLabels">${scene.labels.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</div>`;
      }
      const unlabelled = !heading && !scene.labels?.length ? " unlabelled" : "";
      content += `<div ${glassAttributes} class="glass ${type === "proof" ? "proofBox" : "wideBox"}${unlabelled}">${sheen}${viewport}</div>`;
    } else {
      content = `<div ${glassAttributes} class="glass compact diagram">${sheen}<div class="eyebrow">${label}</div>`
        + `<div class="title">${lines(scene.title)}</div><div class="triad">`
        + scene.items.map((item, index) => `<div class="tile" id="item-${id}-${index}">${escapeHtml(item)}</div>`).join("")
        + `</div>${footer ? `<div class="shared" id="shared-${id}">${footer}</div>` : ""}</div>`;
    }
    sections.push(`<section id="scene-${id}" class="scene ${layout}" style="opacity:0"><div id="art-${id}" class="art">${content}</div></section>`);

    // Frame 0 comes from gsap.set: a zero-duration tl.set at 0 can revert on seek.
    const place = start === 0
      ? (selector, value) => initial.push(`gsap.set(${js(selector)},${js(value)});`)
      : (selector, value) => timeline.push(`tl.set(${js(selector)},${js(value)},${round(start)});`);
    place(`#scene-${id}`, { opacity: 1 });
    for (const [selector, value] of cameraState(layout)) place(selector, value);
    if (scene.endFrame < frames) timeline.push(`tl.set(${js(`#scene-${id}`)},{opacity:0},${round(end)});`);
    if (content && type !== "media-bleed") {
      // Move the surface at full opacity so backdrop sampling stays stable.
      timeline.push(`tl.fromTo(${js(`#art-${id}`)},{y:18},{y:0,duration:${round(Math.min(0.42, end - start))},ease:"power3.out",immediateRender:false},${round(start)});`);
      if (type !== "none" && material === "optical" && end - start >= 1.4) {
        timeline.push(`tl.fromTo(${js(`#sheen-${id}`)},{x:0},{x:1500,duration:1,ease:"power1.inOut",immediateRender:false},${round(start + 0.4)});`);
      }
    }
    if (type === "diagram") {
      const targets = scene.items.map((_, index) => `#item-${id}-${index}`).concat(footer ? [`#shared-${id}`] : []);
      targets.forEach((target, index) => timeline.push(
        `tl.fromTo(${js(target)},{opacity:0,scale:.85},{opacity:1,scale:1,duration:.25,ease:"back.out(1.1)",immediateRender:false},${round(start + 0.18 + index * 0.23)});`,
      ));
    }
    anchors.push({
      scene: id, frames: [scene.startFrame, scene.endFrame], layout, x: 0.5,
      y: scene.captionY ?? layouts.captionAnchors[layout],
      note: "Starting anchor only. Measure the rendered caption box, backing and shadow against the face, proof and safe area.",
    });
  }

  if (sections.some((section) => section.includes('class="sheen"'))) initial.unshift("gsap.set('.sheen',{rotation:24});");
  const page = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>${escapeHtml(config.name ?? "Adaptive glass")}</title>`
    + `<script src="assets/gsap.min.js"></script><link rel="stylesheet" href="style.css"></head><body>`
    + `<div id="root" data-composition-id="main" data-start="0" data-duration="${duration}" data-width="1080" data-height="1920">`
    + `<div id="canvas"></div><div id="grid"></div><div id="camFull">${cameraVideo("fullVideo")}</div>`
    + `<div id="camSplit">${cameraVideo("splitBackground")}${cameraVideo("splitVideo")}</div>${sections.join("")}</div>`
    + `<script>${initial.join("")}const tl=gsap.timeline({paused:true});${timeline.join("")}`
    + `window.__timelines=window.__timelines||{};window.__timelines.main=tl;</script></body></html>\n`;
  await fs.writeFile(path.join(output, "index.html"), page);
  await writeJson(path.join(output, "hyperframes.json"), { media: { autoProxy: false } });
  await writeJson(path.join(output, "source-config.json"), config);
  await writeJson(path.join(output, "media-manifest.json"), manifest);
  await writeJson(path.join(output, "captions.json"), {
    style: {
      fontFamily: "Helvetica Neue", fontWeight: 700, fontSizePx: 54, align: "center", color: palette.text,
      backing: { color: palette.captionBacking, opacity: palette.captionBackingOpacity, radiusPx: 16, paddingPx: { x: 20, y: 10 } },
      shadow: { color: "#051225", blurPx: 4, offsetYPx: 2 },
      note: "Starting style for the editor's caption tool; inspect the rendered size rather than trusting font units.",
    },
    anchors,
  });
  return { output, frames, fps, scenes: scenes.length, palette: palette.name, silentVisualComposition: true };
}
