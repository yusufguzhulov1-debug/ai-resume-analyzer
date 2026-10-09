/*
 * Printed curtain — adapted from "Dynamic ropes 2" by Jason Labbe
 * https://openprocessing.org/sketch/533576  ·  CC BY-SA 4.0 International
 *
 * segment.js
 *
 * A distance constraint between two points, relaxed the same way the original
 * does it. The one change is that the original's hard-coded divisor of 10
 * became a `stiffness` dial: a curtain hangs a lot more weight off its top link
 * than a short rope does, and at one tenth of a correction per iteration it
 * would have stretched to half again its length.
 *
 * The correction stays evenly split between the two ends. Biasing it downwards
 * converges far faster on a long chain, but it also means a strand that has
 * folded back on itself is perfectly happy to stay folded — the child sits at
 * the right distance from its parent, just in the wrong direction, and nothing
 * pulls it straight again. Even splitting lets gravity win instead.
 */

function Segment(point1, point2) {
	this.point1 = point1;
	this.point2 = point2;

	var dx = point2.x - point1.x;
	var dy = point2.y - point1.y;
	this.restLength = Math.sqrt(dx * dx + dy * dy);
}


Segment.prototype.sim = function() {
	var p1 = this.point1;
	var p2 = this.point2;

	var dx = p2.x - p1.x;
	var dy = p2.y - p1.y;
	var currentLength = Math.sqrt(dx * dx + dy * dy);
	if (currentLength < 0.0001) return;

	// Fraction of the current span each end has to travel to restore rest length.
	var offsetPercent = ((this.restLength - currentLength) / currentLength) * params.stiffness;

	var free1 = !p1.snap;
	var free2 = !p2.snap;
	if (!free1 && !free2) return;

	// Half each, unless one end is pinned and the other has to take it all.
	var share = (free1 && free2) ? 0.5 : 1.0;
	var ox = dx * offsetPercent * share;
	var oy = dy * offsetPercent * share;

	if (free1) {
		p1.x -= ox;
		p1.y -= oy;
	}
	if (free2) {
		p2.x += ox;
		p2.y += oy;
	}
};
