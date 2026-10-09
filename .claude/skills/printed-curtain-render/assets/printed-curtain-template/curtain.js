/*
 * Printed curtain — adapted from "Dynamic ropes 2" by Jason Labbe
 * https://openprocessing.org/sketch/533576  ·  CC BY-SA 4.0 International
 *
 * curtain.js
 *
 * Builds the cloth and draws it.
 *
 * The original's central trick is that the cloth costs far less than it looks
 * like it should: only forty strands are simulated, and the gaps between them
 * are filled by drawing extra strands interpolated from their neighbours. Here
 * that trick runs on both axes — across the cloth as before, and now along it
 * too, because a strand long enough to reach the floor needs a coarse chain to
 * stay stiff but a fine one to carry a legible print. So each strand simulates
 * ~50 links and is resampled to ~200 rows for drawing.
 *
 * The print rides on those rows. Every row knows where it sits in the cloth's
 * rest pose, and that rest position is what the artwork is sampled at — once,
 * at build time — and laid onto the cloth colour. The print is therefore a
 * property of the cloth rather than of the screen: it stretches when the cloth
 * stretches, shears when it folds, and comes apart into loose threads when you
 * pull the curtain open.
 */

// Baked colours are quantised to this step per channel before the runs are cut,
// so that a strand crossing flat ink or bare cloth stays one long stroke rather
// than a few hundred one-segment ones. A step of 8 is finer than the weave can
// show anyway: a thread is a hairline seen against its neighbours.
var COLOUR_STEP = 8;

// Distinct colours are few — the cloth, the ink, the icon's flat pixel-art
// palette and the ramps between them — so the style strings are worth keeping.
var STYLES = {};


function Curtain() {
	this.ropes = [];
	this.threads = [];      // drawn strands, real and interpolated
	this.paths = [];        // per rope: resampled screen path, interleaved x,y
	this.rows = 0;          // drawn rows per strand
	this.simRows = 0;       // simulated links per strand
	this.thickness = 1;
	this.spanX = 0;
	this.knitLength = 0;
	this.ropeLength = 0;
}


Curtain.prototype.build = function(w, h, print) {
	this.ropes = [];
	this.threads = [];
	this.paths = [];

	var ropeCount = params.ropes;
	var fills = params.fills;

	this.spanX = w;
	var gap = w / (ropeCount - 1);
	this.thickness = (gap / fills) * params.thickness;

	// Strands hang a little past the bottom edge so no hem is visible at rest.
	this.ropeLength = h * params.ropeLength;

	// Drawn rows carry the knit and the print; simulated links carry the physics.
	this.knitLength = w * params.knitLength;
	this.rows = clampInt(Math.round(this.ropeLength / this.knitLength) + 1, 24, 400);
	this.simRows = clampInt(Math.round(this.ropeLength / (w * params.linkLength)) + 1, 8, 160);

	var simLink = this.ropeLength / (this.simRows - 1);
	params.contactLimit = params.contactStep * simLink;

	var i, j;

	for (i = 0; i < ropeCount; i++) {
		var rb = new RigidBody();
		var x = gap * i;

		for (j = 0; j < this.simRows; j++) {
			var newPoint = rb.addPoint(x, simLink * j);

			// Snap the first point to the rail, otherwise link it to the one above.
			if (rb.points.length === 1) {
				newPoint.snap = true;
			} else {
				rb.addSegment(rb.points[rb.points.length - 2], newPoint);
			}
		}

		this.ropes.push(rb);
		this.paths.push(new Float32Array(this.rows * 2));
	}

	// Let the cloth hang before the artwork is baked into it. Gravity stretches
	// the strands by a per-cent or two, and more near the rail than near the hem,
	// so the pose the print has to line up with is the settled one, not the
	// geometric one the strands were built at. Settling first also means the
	// first drawn frame is already at rest instead of dropping into place.
	this.settle(params.settleSteps);

	this.buildThreads(print, h);
};


Curtain.prototype.settle = function(steps) {
	var wasActive = pointer.active;
	var i;
	pointer.active = false;

	// Resampling is only needed once, at the end.
	for (var s = 0; s < steps; s++) {
		for (i = 0; i < this.ropes.length; i++) {
			this.ropes[i].sim();
		}
	}
	for (i = 0; i < this.ropes.length; i++) {
		this.ropes[i].resample(this.paths[i], this.rows);
	}

	pointer.active = wasActive;
};


// Lays out the drawn strands and bakes the artwork into them.
Curtain.prototype.buildThreads = function(print, h) {
	var ropeCount = params.ropes;
	var fills = params.fills;

	// A cell is one knit row tall; sampling the artwork over roughly that
	// footprint is what gives the type its woven edge.
	var soft = params.printSoft * this.knitLength / print.pxPerArt;

	for (var g = 0; g < ropeCount - 1; g++) {
		for (var s = 0; s < fills; s++) {
			this.threads.push(this.makeThread(g, g + 1, s / fills, print, h, soft));
		}
	}
	// The last real strand closes the right edge.
	this.threads.push(this.makeThread(ropeCount - 1, ropeCount - 1, 0, print, h, soft));
};


// One strand, cut into runs of equal colour: {start, end, style}, where the run
// covers the rows start..end and so is stroked through the points start..end.
// Cutting them here rather than per frame is what keeps ~30k links affordable —
// away from the print a whole strand is a single run.
Curtain.prototype.makeThread = function(a, b, weight, print, h, soft) {
	var runs = [];
	var gap = this.spanX / (params.ropes - 1);
	var cloth = params.cloth;
	var previous = -1;

	// Where this strand lies in the cloth's rest pose, in artboard units.
	var restX = print.toArtX(gap * (a + weight));

	// Vertically, use where the row actually came to rest on screen, read off a
	// representative settled strand.
	var profile = this.paths[Math.floor(this.ropes.length / 2)];

	for (var j = 0; j < this.rows - 1; j++) {
		var restY = (profile[j * 2 + 1] + profile[j * 2 + 3]) * 0.5;
		var ink = print.sample(restX, print.toArtY(restY * params.printFit), soft);

		// The ink is premultiplied, so laying it over the cloth is an add.
		var bare = 1 - ink.a;
		var colour = (quantise(cloth[0] * bare + ink.r) << 16) |
		             (quantise(cloth[1] * bare + ink.g) << 8) |
		              quantise(cloth[2] * bare + ink.b);

		if (colour === previous) {
			runs[runs.length - 1].end = j + 1;
		} else {
			runs.push({ start: j, end: j + 1, style: styleFor(colour) });
			previous = colour;
		}
	}

	return { a: a, b: b, w: weight, runs: runs };
};


Curtain.prototype.sim = function() {
	for (var i = 0; i < this.ropes.length; i++) {
		this.ropes[i].sim();
		this.ropes[i].resample(this.paths[i], this.rows);
	}
};


// A small sideways kick to the tail of a handful of strands near the middle,
// as if something brushed the hem. The impulse is written into each point's
// history (verlet velocity) and confined to the last few links, ramping to
// full strength at the very tip, so a little wave travels up the strand.
Curtain.prototype.nudge = function(strength) {
	var count = 2 + Math.floor(Math.random() * 4);
	var centre = this.ropes.length * (0.5 + (Math.random() - 0.5) * 0.3);
	var start = Math.round(centre - count / 2);
	start = Math.max(0, Math.min(this.ropes.length - count, start));
	var dir = Math.random() < 0.5 ? -1 : 1;

	for (var i = start; i < start + count; i++) {
		var points = this.ropes[i].points;
		var tail = Math.max(1, Math.round(points.length * 0.12));
		for (var j = points.length - tail; j < points.length; j++) {
			var falloff = (j - (points.length - tail)) / tail;
			points[j].oldX -= dir * strength * falloff * (0.7 + Math.random() * 0.6);
		}
	}
};


Curtain.prototype.draw = function(ctx) {
	ctx.lineCap = "round";
	ctx.lineJoin = "round";
	ctx.lineWidth = this.thickness;

	for (var t = 0; t < this.threads.length; t++) {
		var thread = this.threads[t];
		var A = this.paths[thread.a];
		var B = this.paths[thread.b];
		var weight = thread.w;
		var runs = thread.runs;

		for (var i = 0; i < runs.length; i++) {
			var run = runs[i];
			var k = run.start * 2;

			ctx.strokeStyle = run.style;
			ctx.beginPath();
			ctx.moveTo(A[k] + (B[k] - A[k]) * weight,
			           A[k + 1] + (B[k + 1] - A[k + 1]) * weight);

			for (var r = run.start + 1; r <= run.end; r++) {
				k = r * 2;
				ctx.lineTo(A[k] + (B[k] - A[k]) * weight,
				           A[k + 1] + (B[k + 1] - A[k + 1]) * weight);
			}
			ctx.stroke();
		}
	}
};


// How far the cloth hangs past its rest length once it has settled. Used to
// calibrate params.printFit.
Curtain.prototype.measureStretch = function() {
	var pts = this.ropes[Math.floor(this.ropes.length / 2)].points;
	return pts[pts.length - 1].y / this.ropeLength;
};


function clampInt(v, lo, hi) {
	return v < lo ? lo : (v > hi ? hi : v);
}


function quantise(v) {
	v = Math.round(v / COLOUR_STEP) * COLOUR_STEP;
	return v < 0 ? 0 : (v > 255 ? 255 : v);
}


function styleFor(colour) {
	var style = STYLES[colour];
	if (!style) {
		style = STYLES[colour] = "rgb(" + (colour >> 16) + "," +
			((colour >> 8) & 255) + "," + (colour & 255) + ")";
	}
	return style;
}
