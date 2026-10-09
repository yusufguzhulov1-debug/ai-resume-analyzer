/*
 * Printed curtain — adapted from "Dynamic ropes 2" by Jason Labbe
 * https://openprocessing.org/sketch/533576  ·  CC BY-SA 4.0 International
 *
 * point.js
 *
 * A verlet particle. Same integration as the original sketch, but written on
 * plain numbers instead of p5.Vector: the curtain runs tens of thousands of
 * these per frame and per-point vector allocation was the whole frame budget.
 */

function Point(x, y) {
	this.x = x;
	this.y = y;
	this.oldX = x;
	this.oldY = y;
	this.fx = 0;
	this.fy = 0;
	this.snap = false;
}


Point.prototype.applyForce = function(fx, fy) {
	this.fx += fx * params.mass;
	this.fy += fy * params.mass;
};


Point.prototype.sim = function() {
	// Snapped points are the curtain rail; they never move.
	if (this.snap) return;

	this.applyForce(0, params.gravity);
	this.repel();

	var vx = this.x - this.oldX + this.fx;
	var vy = this.y - this.oldY + this.fy;

	// Air drag lets it settle instead of ringing forever.
	vx *= params.drag;
	vy *= params.drag;

	// Limiting the velocity helps keep it stable. The cap is a fraction of a
	// link, so a point can never overtake its neighbour in one step — that is
	// what stops a hard shove from folding a strand into a spiral.
	var speed = Math.sqrt(vx * vx + vy * vy);
	if (speed > params.maxSpeed) {
		vx = vx / speed * params.maxSpeed;
		vy = vy / speed * params.maxSpeed;
	}

	this.oldX = this.x;
	this.oldY = this.y;
	this.x += vx;
	this.y += vy;
	this.fx = 0;
	this.fy = 0;
};


// Use the pointer as a repulsion body to push the point away, as the original
// does, but with the force ramped by how deep the point has got instead of held
// constant across the whole radius.
//
// That ramp is what makes the cloth read as threads rather than as a blob. A
// hard "project everything onto the surface" collision is tempting and it does
// look solid, but it lands every strand it touches on the *same* surface, so
// they stack into one smooth silhouette. Letting each strand settle at the
// depth its own momentum earned is what fans them out into a fringe.
Point.prototype.repel = function() {
	var d = distToPointerPath(this.x, this.y);
	if (d.dist >= params.repulsion) return;

	var nx, ny;
	if (d.dist > 0.0001) {
		nx = d.dx / d.dist;
		ny = d.dy / d.dist;
	} else {
		// Dead centre: fall out sideways rather than picking a random direction.
		nx = 1;
		ny = 0;
	}

	var depth = 1 - d.dist / params.repulsion;
	var push = params.push * depth;
	this.applyForce(nx * push, ny * push);
};


// Non-penetration, run after the strand's constraints have been relaxed — so
// this gets the last word and nothing is left inside the body at the end of a
// frame. The force above alone is not enough: a strand with momentum, or a
// pointer moving faster than the cloth can answer, punches straight through and
// the curtain leaks threads across the middle of what should be a clean void.
//
// The step is capped at a link so a deeply buried point walks out over a few
// frames instead of being flung to the rim ahead of its neighbours, which is
// what ties the strand in knots.
Point.prototype.resolveContact = function() {
	if (this.snap) return;

	// Most of the cloth is nowhere near the pointer, and this runs once per
	// point per relaxation pass; reject on the bounding box first.
	if (this.x < pointer.minX || this.x > pointer.maxX ||
	    this.y < pointer.minY || this.y > pointer.maxY) return;

	var d = distToPointerPath(this.x, this.y);
	if (d.dist >= params.repulsion) return;

	var nx, ny;
	if (d.dist > 0.0001) {
		nx = d.dx / d.dist;
		ny = d.dy / d.dist;
	} else {
		nx = 1;
		ny = 0;
	}

	var mx = (d.cx + nx * params.repulsion - this.x) * params.solid;
	var my = (d.cy + ny * params.repulsion - this.y) * params.solid;

	var move = Math.sqrt(mx * mx + my * my);
	if (move > params.contactLimit) {
		mx = mx / move * params.contactLimit;
		my = my / move * params.contactLimit;
	}

	this.x += mx;
	this.y += my;
};
