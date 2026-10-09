/*
 * Printed curtain — an adaptation of:
 *   Title: Dynamic ropes 2
 *   Author: Jason Labbe  (jasonlabbe3d.com)
 *   Source: https://openprocessing.org/sketch/533576
 *   License: CC BY-SA 4.0 International
 * This derivative keeps the same licence.
 *
 * print.js
 *
 * The artwork is baked once into an ink layer that lives in the cloth's
 * *material* space (its undeformed rest pose). The renderer looks the layer up
 * per cell, so the print is woven into the cloth: it stretches, folds and tears
 * apart exactly as the threads do, instead of floating on top of them.
 *
 * The layer is RGBA, and premultiplied: alpha is how much ink a cell carries,
 * RGB is the colour of that ink. Premultiplied because cells are area-sampled,
 * and averaging plain colour across the edge of a glyph pulls ink colour out
 * into the bare cloth; laying a sample onto the cloth is then the plain
 * cloth * (1 - a) + rgb. Carrying colour rather than coverage is what lets the
 * icon be a photograph and the type stay a single flat ink.
 *
 * Type is fitted to measured boxes rather than to a font size, so the layout
 * survives whichever of the fallback fonts a machine actually has.
 */

// All identity-specific content lives in a small artwork plug-in loaded before
// this file. Copying it here keeps the engine free to edit runtime overrides
// (such as ?image=...) without mutating the plug-in object itself.
var ACTIVE_ARTWORK = copyArtwork(
	typeof CURTAIN_ARTWORK !== "undefined" ? CURTAIN_ARTWORK : {}
);

var ARTBOARD = ACTIVE_ARTWORK.artboard;


function copyArtwork(source) {
	var fallbackBoard = { w: 1200, h: 1600, lockup: 725, anchor: 610 };
	var board = source.artboard || fallbackBoard;
	var copy = {
		id: source.id || "untitled",
		name: source.name || "Untitled artwork",
		artboard: {
			w: board.w || fallbackBoard.w,
			h: board.h || fallbackBoard.h,
			lockup: board.lockup || fallbackBoard.lockup,
			anchor: board.anchor || fallbackBoard.anchor
		},
		images: [],
		lines: []
	};

	var i;
	for (i = 0; i < (source.images || []).length; i++) {
		copy.images.push(copyObject(source.images[i]));
	}
	for (i = 0; i < (source.lines || []).length; i++) {
		copy.lines.push(copyObject(source.lines[i]));
	}

	// A URL override makes trying another same-origin image a one-link change.
	var override = new URLSearchParams(window.location.search).get("image");
	if (override) {
		if (!copy.images.length) copy.images.push(defaultImageLayer());
		copy.images[0].src = override;
		copy.name = new URLSearchParams(window.location.search).get("name") || "Custom image";
	}

	return copy;
}


function copyObject(source) {
	var copy = {};
	for (var key in source) {
		if (Object.prototype.hasOwnProperty.call(source, key)) copy[key] = source[key];
	}
	return copy;
}


function defaultImageLayer() {
	return { src: "", x: 240, y: 245, w: 720, h: 720, fit: "contain" };
}


function Print(artwork) {
	this.artwork = artwork || ACTIVE_ARTWORK;
	this.board = this.artwork.artboard || ARTBOARD;
	this.lines = this.artwork.lines || [];
	this.images = [];   // p5.Image or HTMLImageElement, one per image layer
	this.ink = null;    // Uint8ClampedArray, premultiplied RGBA per pixel
	this.w = 0;
	this.h = 0;
	this.pxPerArt = 1;  // canvas pixels per artboard unit
	this.originX = 0;   // canvas position of the artboard origin
	this.originY = 0;
}


Print.prototype.setImages = function(images) {
	this.images = images || [];
};


// Places the artwork on a canvas of any shape.
//
// The design is full-bleed on a 3:4 canvas, so the obvious mapping — stretch
// the artboard to the canvas — reproduces the reference exactly and mangles
// everything else, squashing the type to two fifths of its height on a laptop
// screen. Instead the artboard is scaled uniformly: as wide as the canvas
// allows, but never so wide that the lockup outgrows its share of the height.
// The anchor row is then pinned to a fixed fraction of the canvas, so the type
// keeps its proportions and stays where the composition wants it. On the
// reference 1200x1600 this reduces to the identity.
Print.prototype.layout = function(w, h) {
	var board = this.board;
	this.pxPerArt = Math.min(w / board.w, (h * params.printMaxHeight) / board.lockup);
	this.originX = w * 0.5 - board.w * 0.5 * this.pxPerArt;
	this.originY = h * (board.anchor / board.h) - board.anchor * this.pxPerArt;
};


Print.prototype.toArtX = function(canvasX) {
	return (canvasX - this.originX) / this.pxPerArt;
};


Print.prototype.toArtY = function(canvasY) {
	return (canvasY - this.originY) / this.pxPerArt;
};


// Renders the artwork into an offscreen layer. `pxWidth` is the raster width;
// bake generously above the cell grid so cells can be area-sampled. `spread` is
// ink gain in artboard units — see drawFittedLine.
Print.prototype.bake = function(pxWidth, spread) {
	this.spread = spread || 0;
	var scale = pxWidth / this.board.w;
	this.w = Math.round(this.board.w * scale);
	this.h = Math.round(this.board.h * scale);

	var rgba = this.paint(scale);

	if (!rgba) {
		// The pixels only come back unreadable if an image has tainted the canvas,
		// which is what happens when the page is opened straight off disk: a file://
		// image counts as cross-origin. Serve the folder and the artwork appears;
		// until then, print text layers alone rather than not printing at all.
		this.images = [];
		rgba = this.paint(scale);
	}

	// Premultiply once, here, so sampling is a plain weighted sum.
	this.ink = new Uint8ClampedArray(rgba.length);
	for (var q = 0; q < rgba.length; q += 4) {
		var a = rgba[q + 3] / 255;
		this.ink[q] = rgba[q] * a;
		this.ink[q + 1] = rgba[q + 1] * a;
		this.ink[q + 2] = rgba[q + 2] * a;
		this.ink[q + 3] = rgba[q + 3];
	}
};


// Paints the lockup and reads it back, or returns null if the pixels cannot be
// read. The canvas is built fresh on every call because tainting is permanent:
// a reused canvas would read back nothing on the retry above.
Print.prototype.paint = function(scale) {
	var cvs = document.createElement("canvas");
	cvs.width = this.w;
	cvs.height = this.h;

	// The layer starts fully transparent, which is the "bare cloth" state.
	var ctx = cvs.getContext("2d", { willReadFrequently: true });
	ctx.scale(scale, scale);
	// Image layers carry their own colour and alpha. They arrive far larger than
	// the weave can show, and the cloth samples them coarsely again afterwards,
	// so ask for the good filter: the threads should pick up an area average, not
	// whichever source pixel happened to land under the sample point.
	ctx.imageSmoothingEnabled = true;
	ctx.imageSmoothingQuality = "high";
	for (var p = 0; p < this.artwork.images.length; p++) {
		if (this.images[p]) drawImageLayer(ctx, this.images[p], this.artwork.images[p]);
	}

	for (var i = 0; i < this.lines.length; i++) {
		if (this.lines[i].text) {
			ctx.fillStyle = colourStyle(this.lines[i].colour || params.ink);
			drawFittedLine(ctx, this.lines[i], this.spread);
		}
	}

	try {
		return ctx.getImageData(0, 0, this.w, this.h).data;
	} catch (e) {
		return null;
	}
};


function colourStyle(colour) {
	if (typeof colour === "string") return colour;
	return "rgb(" + colour[0] + "," + colour[1] + "," + colour[2] + ")";
}


function drawImageLayer(ctx, image, layer) {
	var source = image.canvas || image.elt || image;
	var sourceW = source.naturalWidth || source.videoWidth || source.width || image.width;
	var sourceH = source.naturalHeight || source.videoHeight || source.height || image.height;
	if (!(sourceW > 0 && sourceH > 0)) return;

	var x = numberOr(layer.x, 0);
	var y = numberOr(layer.y, 0);
	var w = numberOr(layer.w, sourceW);
	var h = numberOr(layer.h, sourceH);
	var fit = layer.fit || "contain";
	var drawX = x, drawY = y, drawW = w, drawH = h;

	if (fit !== "stretch") {
		var scale = fit === "cover" ? Math.max(w / sourceW, h / sourceH) : Math.min(w / sourceW, h / sourceH);
		drawW = sourceW * scale;
		drawH = sourceH * scale;
		drawX = x + (w - drawW) * 0.5;
		drawY = y + (h - drawH) * 0.5;
	}

	ctx.save();
	ctx.globalAlpha = layer.opacity === undefined ? 1 : Math.max(0, Math.min(1, layer.opacity));
	if (fit === "cover") {
		ctx.beginPath();
		ctx.rect(x, y, w, h);
		ctx.clip();
	}
	ctx.drawImage(source, drawX, drawY, drawW, drawH);
	ctx.restore();
}


function numberOr(value, fallback) {
	return typeof value === "number" && isFinite(value) ? value : fallback;
}


// Ink at a point in artboard units, averaged over a box of `soft` units: rgb is
// premultiplied colour on 0..255, a is coverage on 0..1. Outside the artboard
// the cloth is bare. The result object is shared between calls.
var _ink = { r: 0, g: 0, b: 0, a: 0 };

Print.prototype.sample = function(x, y, soft) {
	_ink.r = _ink.g = _ink.b = _ink.a = 0;
	if (!this.ink) return _ink;

	var s = this.w / this.board.w;
	var r = Math.max(0, (soft || 0) * 0.5 * s);
	var cx = x * s;
	var cy = y * s;

	if (r < 0.5) {
		tap(this, cx, cy, 1);
		return _ink;
	}

	// A 3x3 tap box is enough to soften a cell edge without blurring the type.
	for (var j = -1; j <= 1; j++) {
		for (var i = -1; i <= 1; i++) {
			tap(this, cx + i * r, cy + j * r, 1 / 9);
		}
	}
	return _ink;
};


function tap(print, px, py, weight) {
	var x = px | 0;
	var y = py | 0;
	if (x < 0 || y < 0 || x >= print.w || y >= print.h) return;

	var q = (y * print.w + x) * 4;
	var d = print.ink;
	_ink.r += d[q] * weight;
	_ink.g += d[q + 1] * weight;
	_ink.b += d[q + 2] * weight;
	_ink.a += (d[q + 3] / 255) * weight;
}


// --- type fitting -----------------------------------------------------------

// Ink extents of a run of glyphs laid out with a fixed tracking, measured from
// the font's own bounding boxes so no pixels have to be scanned.
function measureRun(ctx, chars, tracking) {
	var pen = 0, left = Infinity, right = -Infinity, asc = 0, desc = 0;

	for (var i = 0; i < chars.length; i++) {
		var m = ctx.measureText(chars[i]);
		// Spaces carry no ink and must not drag the box outwards.
		if (m.actualBoundingBoxLeft + m.actualBoundingBoxRight > 0.01) {
			left = Math.min(left, pen - m.actualBoundingBoxLeft);
			right = Math.max(right, pen + m.actualBoundingBoxRight);
			asc = Math.max(asc, m.actualBoundingBoxAscent);
			desc = Math.max(desc, m.actualBoundingBoxDescent);
		}
		pen += m.width + tracking;
	}

	if (left === Infinity) return { left: 0, right: 0, asc: 0, desc: 0, w: 0, h: 0 };
	return { left: left, right: right, asc: asc, desc: desc, w: right - left, h: asc + desc };
}


// `spread` is ink gain: the glyphs are outlined as well as filled, the way ink
// bleeds into a woven ground. It is not decoration — a stroke thinner than the
// knit's eight-pixel row lands between samples and vanishes, so without a
// little gain the script line dissolves into a rash of dots. The target box is
// shrunk by the same amount first, so the finished ink still measures what the
// layout asked for.
function drawFittedLine(ctx, line, spread) {
	var chars = Array.from(line.text);
	var probe = 200;
	var targetW = Math.max(1, line.w - spread);

	ctx.textAlign = "left";
	ctx.textBaseline = "alphabetic";

	// Size the face vertically; neither tracking nor condensing touches this.
	ctx.font = line.weight + probe + "px " + line.family;
	var m = measureRun(ctx, chars, 0);
	if (m.h <= 0) return;

	var size;
	if (line.xh) {
		var xh = ctx.measureText("x").actualBoundingBoxAscent;
		if (!(xh > 0)) xh = m.h * 0.45;
		size = probe * Math.max(1, line.xh - spread) / xh;
	} else {
		size = probe * Math.max(1, line.h - spread) / m.h;
	}
	ctx.font = line.weight + size + "px " + line.family;

	// Then reach the target width. The reference lockup is set tight and
	// condensed, so a font that runs wide gets squeezed horizontally rather than
	// having its word spaces pulled to nothing; a font that runs narrow is
	// tracked out instead of being fattened.
	var w0 = measureRun(ctx, chars, 0).w;
	var tracking = 0;
	var squeeze = 1;

	if (w0 > targetW) {
		squeeze = Math.max(0.2, targetW / w0);
	} else {
		var w1 = measureRun(ctx, chars, 1).w;
		if (w1 - w0 > 1e-6) tracking = (targetW - w0) / (w1 - w0);
	}

	var box = measureRun(ctx, chars, tracking);
	var baseline = line.xh ? line.base : line.y + spread * 0.5 + box.asc;

	ctx.save();
	ctx.translate(line.cx - targetW * 0.5, baseline);
	ctx.scale(squeeze, 1);

	ctx.lineWidth = spread / squeeze;
	ctx.lineJoin = "round";
	ctx.strokeStyle = ctx.fillStyle;

	var pen = -box.left;
	for (var i = 0; i < chars.length; i++) {
		ctx.fillText(chars[i], pen, 0);
		if (spread > 0) ctx.strokeText(chars[i], pen, 0);
		pen += ctx.measureText(chars[i]).width + tracking;
	}
	ctx.restore();
}
