/*
 * Printed curtain — adapted from "Dynamic ropes 2" by Jason Labbe
 * https://openprocessing.org/sketch/533576  ·  CC BY-SA 4.0 International
 *
 * controls.js
 *
 * Replaces the original's on-canvas sliders with an HTML panel, so nothing is
 * painted over the artwork. Press H to hide it.
 *
 * Three grades of change:
 *   live    — the running cloth just reads the new value
 *   restyle — only the stroke width changes
 *   reprint — the artwork is re-baked into the existing cloth, mid-motion
 *   rebuild — the cloth is respun from scratch
 */

var artworkStatusNode = null;

function buildControls() {
	var panel = document.getElementById("panel");
	if (!panel) return;

	panel.innerHTML = "";
	panel.appendChild(el("h1", "Printed Curtain"));
	artworkStatusNode = el("p", ACTIVE_ARTWORK.name);
	artworkStatusNode.className = "artwork-status";
	panel.appendChild(artworkStatusNode);

	group(panel, "Cloth", [
		slider("Strands", params, "ropes", 12, 80, 1, rebuild),
		slider("Fills per gap", params, "fills", 1, 8, 1, rebuild),
		slider("Knit row", params, "knitLength", 0.004, 0.03, 0.0005, rebuild),
		slider("Sim link", params, "linkLength", 0.01, 0.08, 0.002, rebuild),
		slider("Strand length", params, "ropeLength", 0.6, 1.6, 0.01, rebuild),
		slider("Thickness", params, "thickness", 0.3, 2.0, 0.05, restyle)
	]);

	group(panel, "Physics", [
		slider("Gravity", DESIGN, "gravity", 0.01, 0.6, 0.01, applyScale),
		slider("Mass", params, "mass", 0.5, 3, 0.1, null),
		slider("Air drag", params, "drag", 0.95, 1, 0.001, null),
		slider("Stiffness", params, "stiffness", 0.05, 1, 0.05, null),
		slider("Bend", params, "bend", 0, 0.4, 0.01, null),
		slider("Timesteps", params, "timesteps", 1, 40, 1, null),
		slider("Nudge", params, "nudge", 0, 0.008, 0.0001, null)
	]);

	group(panel, "Pointer", [
		slider("Repulsion size", DESIGN, "repulsion", 0.02, 0.5, 0.01, applyScale),
		slider("Push", DESIGN, "push", 0.1, 8, 0.1, applyScale),
		slider("Solidity", params, "solid", 0, 1, 0.05, null),
		slider("Contact step", params, "contactStep", 0.2, 3, 0.1, rebuild)
	]);

	var printRows = [imagePicker()];
	printRows.push(slider("Print size", params, "printMaxHeight", 0.15, 0.9, 0.01, reprint));
	printRows.push(slider("Print fit", params, "printFit", 0.85, 1.2, 0.005, reprint));
	printRows.push(slider("Ink gain", params, "printSpread", 0, 1.2, 0.05, reprint));
	printRows.push(slider("Print softness", params, "printSoft", 0, 1.5, 0.05, reprint));
	group(panel, "Print", printRows);

	var hint = el("p", "H panel · R reset");
	hint.className = "hint";
	panel.appendChild(hint);
}


function rebuild() { resetScene(); }

function restyle() {
	curtain.thickness = (width / (params.ropes - 1) / params.fills) * params.thickness;
}


function imagePicker() {
	var row = el("label");
	row.className = "image-picker";
	var input = document.createElement("input");
	input.type = "file";
	input.accept = "image/png,image/jpeg,image/webp";

	row.appendChild(el("span", "Choose image"));
	row.appendChild(input);

	input.addEventListener("change", function() {
		var file = input.files && input.files[0];
		showArtworkStatus("Loading…");
		loadArtworkImageFile(file, function(error, name) {
			showArtworkStatus(error || name);
			input.value = "";
		});
	});
	return row;
}


function showArtworkStatus(message) {
	if (artworkStatusNode) artworkStatusNode.textContent = message;
}

// Re-bakes the artwork into the cloth without disturbing the simulation, so you
// can watch the image reflow onto a curtain that is already in motion.
function reprint() {
	bakePrint();
	curtain.threads = [];
	curtain.buildThreads(print, height);
}


// --- tiny DOM helpers -------------------------------------------------------

function el(tag, text) {
	var node = document.createElement(tag);
	if (text !== undefined) node.textContent = text;
	return node;
}

function group(panel, title, rows) {
	var section = el("section");
	section.appendChild(el("h2", title));
	for (var i = 0; i < rows.length; i++) section.appendChild(rows[i]);
	panel.appendChild(section);
}

function slider(label, target, key, min, max, step, onChange) {
	var row = el("label");
	row.className = "row";
	var name = el("span", label);
	var readout = el("output", format(target[key]));
	var input = document.createElement("input");
	input.type = "range";
	input.min = min;
	input.max = max;
	input.step = step;
	input.value = target[key];

	input.addEventListener("input", function() {
		target[key] = parseFloat(input.value);
		readout.textContent = format(target[key]);
		if (onChange) onChange();
	});

	row.appendChild(name);
	row.appendChild(readout);
	row.appendChild(input);
	return row;
}

function toggle(label, target, key) {
	var row = el("label");
	row.className = "row check";
	var input = document.createElement("input");
	input.type = "checkbox";
	input.checked = !!target[key];
	input.addEventListener("change", function() { target[key] = input.checked; });
	row.appendChild(input);
	row.appendChild(el("span", label));
	return row;
}

function textField(target, key, onChange) {
	var row = el("label");
	row.className = "row text";
	var input = document.createElement("input");
	input.type = "text";
	input.value = target[key];
	input.addEventListener("input", function() {
		target[key] = input.value;
		if (onChange) onChange();
	});
	// Keep sketch shortcuts from firing while typing.
	input.addEventListener("keydown", function(e) { e.stopPropagation(); });
	row.appendChild(input);
	return row;
}

function format(v) {
	if (Math.abs(v) >= 10 || v === Math.round(v)) return String(Math.round(v * 100) / 100);
	return v.toFixed(v < 0.02 ? 4 : 3);
}
