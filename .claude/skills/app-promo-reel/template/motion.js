// Motion language: one entry per object type. Edit values here, not in the timeline.
// Every ease is a pure function of progress p (0..1): the same time gives the same frame.
// A spring is trimmed so f(0)=0 and f(1)=1 and the tween always lands exactly.
// os is the first overshoot (0.06 = 6% past the target). Allowed range: 0 to 0.35. Default 0.12.
const spring = (os = 0.12) => {
  if (!(typeof os === "number" && os >= 0 && os <= 0.35)) throw new Error(`spring(${os}): overshoot must be 0-0.35`);
  let raw;
  if (os === 0) {
    const w = 9;
    raw = (t) => 1 - (1 + w * t) * Math.exp(-w * t);
  } else {
    const L = Math.log(os);
    const z = -L / Math.sqrt(Math.PI ** 2 + L * L);
    const w = Math.log(500) / z;
    const wd = w * Math.sqrt(1 - z * z);
    raw = (t) => 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + ((z * w) / wd) * Math.sin(wd * t));
  }
  const e1 = raw(1);
  return (p) => raw(p) - (e1 - 1) * p;
};

const MOTION = {
  micro: { ease: spring(0.06), dur: 0.18 },
  panel: { ease: spring(0.07), dur: 0.55 },
  headline: { ease: spring(0.13), dur: 0.35, hold: 1.0 },
  icon: { ease: spring(0.1), dur: 0.32 },
  camera: { drift: "sine.inOut", move: "power2.inOut" },
};
