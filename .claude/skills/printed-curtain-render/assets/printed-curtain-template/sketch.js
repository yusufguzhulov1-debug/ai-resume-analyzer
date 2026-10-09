/*
 * Printed Curtain — artwork woven into a simulated cloth
 *
 * Adapted from:
 *   Title: Dynamic ropes 2
 *   Author: Jason Labbe  (jasonlabbe3d.com)
 *   Source: https://openprocessing.org/sketch/533576
 *   License: CC BY-SA 4.0 International
 * This derivative is released under the same licence.
 *
 * The original hangs forty verlet strands from a rail and fills the gaps
 * between them with interpolated "fake" strands, so a few hundred points read
 * as a solid mass of rope. Here that mass is dressed as a curtain: strands run
 * the full height of the window, the pointer is a wide repulsion body you can
 * sweep the cloth aside with, and an artwork is printed into the weave.
 *
 * The print is the part worth explaining. It is not drawn over the curtain —
 * it is sampled once, at build time, at each link's position in the cloth's
 * rest pose, and stored as that link's colour. The image and optional letters
 * therefore belong to the cloth: they stretch when it stretches, shear when it
 * folds, and break into loose threads when you pull the curtain open.
 *
 * The piece runs on a fixed 3:4 stage, the proportions the artwork is composed
 * for, fitted into whatever window it is given. Letting it reflow to the window
 * instead would stretch a full-bleed poster across a laptop screen and leave
 * the title marooned in a wide band of cloth.
 *
 * Controls:
 *   - Move the pointer over the curtain to push it aside.
 *   - H toggles the control panel, R resets.
 */

// Values as designed against a 1200 x 1600 canvas. Anything measured in pixels
// per frame is rescaled to the actual canvas in applyScale().
var DESIGN = {
	gravity: 0.2,
	maxSpeed: 0.75,    // x simulated link length
	repulsion: 0.07,   // x width
	push: 2.0
};

var params = {
	// stage
	stageAspect: 3 / 4,  // width : height, as measured off the recording

	// cloth construction
	ropes: 40,          // simulated strands
	fills: 4,           // drawn strands per gap
	knitLength: 0.0071, // x width — one drawn row, the visible knit
	linkLength: 0.026,  // x width — one simulated link
	ropeLength: 1.05,   // x height — strands hang past the bottom edge
	thickness: 1.0,     // x the spacing between drawn strands

	// solver
	gravity: 0.2,
	mass: 2,
	drag: 0.985,
	maxSpeed: 23,
	stiffness: 1.0,
	timesteps: 20,
	bend: 0.10,
	settleSteps: 140,   // frames run at build time to hang the cloth

	// interaction. repulsion, push, maxSpeed and contactLimit are derived
	// from DESIGN and the cloth's own scale — the values here are placeholders.
	repulsion: 260,
	push: 1.0,
	solid: 1.0,         // how hard the pointer refuses to be occupied
	contactStep: 1.0,   // x simulated link — most a contact may move a point
	contactLimit: 30,

	// idle life — an occasional sideways kick to the tail of a few middle strands
	nudge: 0.002,       // x width, initial tip velocity of a kick

	// print
	printFit: 1.0,      // fine nudge of the print up or down the cloth
	printSoft: 0.5,
	printSpread: 0.15,  // x knit row — ink gain, so fine strokes survive weaving
	printMaxHeight: 0.56,// x canvas height — the most the lockup may occupy

	// Klein blue cloth on a white ground; text stays white. Images keep
	// its own colours — the cloth carries whatever the print puts on it.
	cloth: [0, 47, 167],
	ink: [248, 248, 246],
	backdrop: [255, 255, 255]
};

// The generator writes CURTAIN_STYLE beside the artwork plug-in. Keeping these
// overrides outside the engine lets a generated piece change its palette
// without maintaining a fork of the simulation.
if (typeof CURTAIN_STYLE !== "undefined") {
	params.cloth = validColour(CURTAIN_STYLE.cloth, params.cloth);
	params.ink = validColour(CURTAIN_STYLE.ink, params.ink);
	params.backdrop = validColour(CURTAIN_STYLE.backdrop, params.backdrop);
}

var curtain;
var print;
var artworkImages = [];
var ctx;
var nextNudge = 0;

var pointer = {
	x: -9999, y: -9999, px: -9999, py: -9999,
	active: false,
	minX: 0, maxX: 0, minY: 0, maxY: 0   // bounds of the swept capsule
};


// Artwork images have to be in hand before the cloth is baked. If a layer does
// not arrive, the other layers still render.
function preload() {
	var layers = ACTIVE_ARTWORK.images || [];
	for (var i = 0; i < layers.length; i++) {
		artworkImages[i] = loadImage(layers[i].src, null, imageLoadFailed(i));
	}
}


function imageLoadFailed(index) {
	return function() {
		artworkImages[index] = null;
		console.warn("Printed Curtain could not load artwork layer " + index + ".");
	};
}


function setup() {
	var stage = stageSize();
	createCanvas(stage.w, stage.h);

	// The stage is bounded, so the cost of drawing at device resolution is too;
	// the threads are hairlines and want the extra pixels.
	pixelDensity(Math.min(2, displayDensity()));
	ctx = drawingContext || document.querySelector("canvas").getContext("2d");

	print = new Print(ACTIVE_ARTWORK);
	print.setImages(artworkImages);
	resetScene();

	if (typeof buildControls === "function") buildControls();
	bindArtworkDrop();
	document.title = ACTIVE_ARTWORK.name + " — Printed Curtain";
	window.__PRINTED_CURTAIN_READY__ = true;
}


function validColour(value, fallback) {
	if (!Array.isArray(value) || value.length !== 3) return fallback;
	for (var i = 0; i < 3; i++) {
		if (typeof value[i] !== "number" || value[i] < 0 || value[i] > 255) return fallback;
	}
	return value.slice();
}


function rgbaStyle(colour, alpha) {
	return "rgba(" + colour[0] + "," + colour[1] + "," + colour[2] + "," + alpha + ")";
}


// The largest 3:4 rectangle the window will hold.
function stageSize() {
	var w = windowWidth;
	var h = windowHeight;

	if (w / h > params.stageAspect) {
		w = h * params.stageAspect;
	} else {
		h = w / params.stageAspect;
	}
	return { w: Math.max(160, Math.round(w)), h: Math.max(213, Math.round(h)) };
}


function resetScene() {
	applyScale();

	bakePrint();

	curtain = new Curtain();
	curtain.build(width, height, print);
}


// Bakes the artwork a little above the cell grid, so the type has edges to
// sample rather than steps. Ink gain is measured against a knit row, since that
// is the scale a stroke has to beat to survive being woven into the cloth.
function bakePrint() {
	print.layout(width, height);
	var knitRow = (width * params.knitLength) / print.pxPerArt;
	print.bake(Math.max(1200, width * 1.2), params.printSpread * knitRow);
}


// Public runtime seam used by the panel and by drag-and-drop. The file never
// leaves the browser: FileReader turns it into a local data URL, p5 decodes it,
// and the existing cloth is re-inked without resetting its motion.
function loadArtworkImageFile(file, done) {
	if (!file || !/^image\//.test(file.type)) {
		if (done) done("Choose a PNG, JPEG, or WebP image.");
		return;
	}

	var reader = new FileReader();
	reader.onerror = function() {
		if (done) done("The image could not be read.");
	};
	reader.onload = function() {
		loadImage(reader.result, function(image) {
			if (!ACTIVE_ARTWORK.images.length) ACTIVE_ARTWORK.images.push(defaultImageLayer());
			artworkImages[0] = image;
			print.setImages(artworkImages);
			ACTIVE_ARTWORK.name = file.name.replace(/\.[^.]+$/, "") || "Custom image";
			reprint();
			if (done) done(null, ACTIVE_ARTWORK.name);
		}, function() {
			if (done) done("The browser could not decode that image.");
		});
	};
	reader.readAsDataURL(file);
}


function bindArtworkDrop() {
	var canvas = document.querySelector("canvas");
	if (!canvas) return;

	canvas.addEventListener("dragover", function(event) {
		event.preventDefault();
	});
	canvas.addEventListener("drop", function(event) {
		event.preventDefault();
		var file = event.dataTransfer && event.dataTransfer.files[0];
		loadArtworkImageFile(file, function(error, name) {
			if (typeof showArtworkStatus === "function") showArtworkStatus(error || name);
		});
	});
}


function applyScale() {
	var scale = width / print.board.w;
	params.gravity = DESIGN.gravity * scale;
	params.push = DESIGN.push * scale;
	params.repulsion = DESIGN.repulsion * width;
	// Capped against the simulated link, so a point can never overtake its
	// neighbour in one step.
	params.maxSpeed = DESIGN.maxSpeed * params.linkLength * width;
}


function draw() {
	background(params.backdrop[0], params.backdrop[1], params.backdrop[2]);

	updatePointer();
	updatePointerBounds();

	// Not weather — just the odd passer-by. Every few seconds a small cluster
	// of middle strands gets a random sideways kick and settles back.
	if (params.nudge > 0 && millis() > nextNudge) {
		curtain.nudge(width * params.nudge);
		nextNudge = millis() + 2500 + Math.random() * 3500;
	}

	curtain.sim();
	curtain.draw(ctx);

	// The pointer body, drawn at the size the cloth actually feels, so you can
	// see what you are pushing with.
	if (pointer.active) {
		ctx.beginPath();
		ctx.arc(pointer.x, pointer.y, params.repulsion, 0, Math.PI * 2);
		ctx.fillStyle = rgbaStyle(params.cloth, 0.22);
		ctx.fill();
	}
}


function updatePointer() {
	pointer.px = pointer.x;
	pointer.py = pointer.y;
	pointer.x = mouseX;
	pointer.y = mouseY;

	if (!pointer.active || pointer.px < -9000) {
		// While the ball is away there is no sweep, so it re-entering the cloth
		// never drags a capsule across it.
		pointer.px = pointer.x;
		pointer.py = pointer.y;
	}
}


function updatePointerBounds() {
	var r = params.repulsion;
	pointer.minX = Math.min(pointer.x, pointer.px) - r;
	pointer.maxX = Math.max(pointer.x, pointer.px) + r;
	pointer.minY = Math.min(pointer.y, pointer.py) - r;
	pointer.maxY = Math.max(pointer.y, pointer.py) + r;
}


// Distance from a cloth point to the path the pointer swept this frame, plus
// the closest point on that path. Testing against the swept segment rather than
// where the pointer landed keeps a fast drag from passing straight through the
// curtain — the pointer is a capsule, not a dot.
var _probe = { dist: 0, dx: 0, dy: 0, cx: 0, cy: 0 };

function distToPointerPath(x, y) {
	if (!pointer.active) {
		_probe.dist = 1e9;
		return _probe;
	}

	var ax = pointer.px, ay = pointer.py;
	var vx = pointer.x - ax, vy = pointer.y - ay;
	var len2 = vx * vx + vy * vy;
	var t = 0;

	if (len2 > 1e-6) {
		t = ((x - ax) * vx + (y - ay) * vy) / len2;
		if (t < 0) t = 0;
		else if (t > 1) t = 1;
	}

	_probe.cx = ax + vx * t;
	_probe.cy = ay + vy * t;
	_probe.dx = x - _probe.cx;
	_probe.dy = y - _probe.cy;
	_probe.dist = Math.sqrt(_probe.dx * _probe.dx + _probe.dy * _probe.dy);
	return _probe;
}


// The ball lives wherever the pointer is, on or off the stage: p5 tracks the
// mouse at window level, so positions past the canvas edge still arrive. A
// lifted finger, though, is gone — the ball leaves with it.
function mouseMoved() { pointer.active = true; }
function touchStarted() { pointer.active = true; }
function touchEnded() { pointer.active = false; }

// Returning false keeps a swipe over the cloth from scrolling the page.
function touchMoved() { return false; }


function windowResized() {
	var stage = stageSize();
	resizeCanvas(stage.w, stage.h);
	resetScene();
}


function keyPressed() {
	if (key === "r" || key === "R") resetScene();
	if (key === "h" || key === "H") {
		var panel = document.getElementById("panel");
		if (panel) panel.classList.toggle("hidden");
	}
}
