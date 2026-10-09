/*
 * Printed curtain — adapted from "Dynamic ropes 2" by Jason Labbe
 * https://openprocessing.org/sketch/533576  ·  CC BY-SA 4.0 International
 *
 * rigidBody.js
 *
 * One hanging strand: a chain of points joined by distance constraints.
 * Strands are independent of each other — nothing ties a strand to its
 * neighbours — which is exactly why the curtain fans out into separate threads
 * when you sweep it aside instead of behaving like a sheet.
 *
 * The chain is deliberately coarse. Relaxation has to travel link by link, so a
 * two-hundred-link strand needs a punishing number of iterations before the
 * rail can hold up the hem; fifty links hold their length at twenty. The fine
 * knit you actually see is resampled off the chain at draw time by resample().
 */

function RigidBody() {
	this.points = [];
	this.segments = [];
}


RigidBody.prototype.addPoint = function(x, y) {
	var newPoint = new Point(x, y);
	this.points.push(newPoint);
	return newPoint;
};


RigidBody.prototype.addSegment = function(point1, point2) {
	var newSegment = new Segment(point1, point2);
	this.segments.push(newSegment);
	return newSegment;
};


RigidBody.prototype.sim = function() {
	var i;

	for (i = 0; i < this.points.length; i++) {
		this.points[i].sim();
	}

	// The higher the timesteps, the more stable it will be.
	// Higher timesteps help maintain its shape, but at the cost of speed and
	// making it feel stiff.
	//
	// Contacts are relaxed inside this loop rather than after it. Run once at
	// the end they lose: twenty passes of distance constraints will happily drag
	// a point back through the pointer to satisfy its neighbours, and the cloth
	// leaks threads across the middle of what should be a clean void. Interleaved,
	// each contact is answered by the constraints that follow it, so the strand
	// flows around the body instead of being torn off it.
	var touching = pointer.active && params.solid > 0;

	for (var ts = 0; ts < params.timesteps; ts++) {
		for (i = 0; i < this.segments.length; i++) {
			this.segments[i].sim();
		}
		if (touching) {
			for (i = 0; i < this.points.length; i++) {
				this.points[i].resolveContact();
			}
		}
	}

	this.relaxBend();

	// Bending can nudge a point back inside, so contacts get the last word.
	if (touching) {
		for (i = 0; i < this.points.length; i++) {
			this.points[i].resolveContact();
		}
	}
};


// Bending resistance. Distance constraints say nothing about the angle between
// two links, so a strand shoved sideways is free to buckle into a zigzag.
// Nudging each point towards the midpoint of its neighbours penalises curvature,
// which keeps the cloth reading as long smooth folds. One pass, no square roots.
RigidBody.prototype.relaxBend = function() {
	var k = params.bend;
	if (k <= 0) return;

	var pts = this.points;
	for (var i = 1; i < pts.length - 1; i++) {
		var b = pts[i];
		if (b.snap) continue;
		var a = pts[i - 1];
		var c = pts[i + 1];
		b.x += ((a.x + c.x) * 0.5 - b.x) * k;
		b.y += ((a.y + c.y) * 0.5 - b.y) * k;
	}
};


// Resamples the coarse chain into `rows` evenly spaced points, written as
// interleaved x,y into `out`. Catmull-Rom passes through the simulated points,
// so the drawn thread never wanders off the physics; the extra rows exist to
// carry the knit and the print at a much finer pitch than the solver runs at.
RigidBody.prototype.resample = function(out, rows) {
	var pts = this.points;
	var last = pts.length - 1;
	var span = last / (rows - 1);

	for (var j = 0; j < rows; j++) {
		var u = j * span;
		var i = u | 0;
		if (i > last - 1) i = last - 1;
		var t = u - i;

		var p0 = pts[i > 0 ? i - 1 : 0];
		var p1 = pts[i];
		var p2 = pts[i + 1];
		var p3 = pts[i < last - 1 ? i + 2 : last];

		var t2 = t * t;
		var t3 = t2 * t;
		var c0 = -t3 + 2 * t2 - t;
		var c1 = 3 * t3 - 5 * t2 + 2;
		var c2 = -3 * t3 + 4 * t2 + t;
		var c3 = t3 - t2;

		out[j * 2] = 0.5 * (c0 * p0.x + c1 * p1.x + c2 * p2.x + c3 * p3.x);
		out[j * 2 + 1] = 0.5 * (c0 * p0.y + c1 * p1.y + c2 * p2.y + c3 * p3.y);
	}
};
