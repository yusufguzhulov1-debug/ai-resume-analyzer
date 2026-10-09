"use client";

// Launch film block for a Next.js / React + Tailwind site (template of the motion-design skill).
// Derived from the component that shows the film "Le devis" on entrepreneurs2-0.com.
// - Plays muted as soon as 45 % of it is on screen (the film reads without sound), pauses when it leaves.
// - The sound button restarts the film from the beginning with the voice (the viewer hears the hook).
// - With prefers-reduced-motion, nothing starts by itself: a play button is shown instead.
// - A 2 px accent border with a soft glow of the same color, 10 px corners: on a section painted with the film's own
//   dark ground, a frameless film reads as black on black.
import { useEffect, useRef, useState, type CSSProperties } from "react";

type Props = {
  src: string; // web encode, e.g. "/motion/film.mp4" (see references/landing-integration.md)
  poster: string; // a frame that tells the story, e.g. "/motion/film.jpg"
  label: string; // what the film says, for screen readers
  accent?: string; // the film's accent color
  stage?: string; // the film's dark ground, also used for the section background
};

export default function LaunchFilm({ src, poster, label, accent = "#c25b28", stage = "#0d0b0a" }: Props) {
  const ref = useRef<HTMLVideoElement>(null);
  const [muted, setMuted] = useState(true);
  const [paused, setPaused] = useState(true);
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const v = ref.current;
    if (!v) return;
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    setReduced(prefersReduced);
    if (prefersReduced) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) v.play().catch(() => {});
        else v.pause();
      },
      { threshold: 0.45 }
    );
    io.observe(v);
    return () => io.disconnect();
  }, []);

  const toggleSound = () => {
    const v = ref.current;
    if (!v) return;
    if (v.muted) {
      v.muted = false;
      v.currentTime = 0;
      v.play().catch(() => {});
      setMuted(false);
    } else {
      v.muted = true;
      setMuted(true);
    }
  };

  const playWithSound = () => {
    const v = ref.current;
    if (!v) return;
    v.muted = false;
    setMuted(false);
    v.play().catch(() => {});
  };

  const vars = { "--film-accent": accent, "--film-stage": stage } as CSSProperties;

  return (
    <div className="relative mx-auto w-full max-w-[1120px]" style={vars}>
      {/* soft ember behind the film */}
      <div className="pointer-events-none absolute -inset-x-10 -inset-y-16 rounded-[40px] bg-[radial-gradient(50%_50%_at_50%_50%,color-mix(in_srgb,var(--film-accent)_18%,transparent),transparent_70%)] blur-2xl" />
      {/* the frame: 2 px accent border + a glow of the same color, so the film stands out from the dark section */}
      <div className="relative aspect-video overflow-hidden rounded-[10px] border-2 border-[var(--film-accent)] bg-[var(--film-stage)] shadow-[0_0_0_1px_color-mix(in_srgb,var(--film-accent)_25%,transparent),0_0_48px_-8px_color-mix(in_srgb,var(--film-accent)_55%,transparent),0_40px_120px_-20px_rgba(0,0,0,0.75)]">
        <video
          ref={ref}
          src={src}
          poster={poster}
          muted
          loop
          playsInline
          preload="metadata"
          onPlay={() => setPaused(false)}
          onPause={() => setPaused(true)}
          className="h-full w-full object-cover"
          aria-label={label}
        />

        {reduced && paused && (
          <button
            type="button"
            onClick={playWithSound}
            className="absolute inset-0 grid place-items-center bg-black/25 transition-colors duration-300 hover:bg-black/10"
            aria-label="Lire le film avec le son"
          >
            <span className="grid h-16 w-16 place-items-center rounded-full bg-[var(--film-accent)] text-white shadow-lg">
              <svg viewBox="0 0 24 24" className="ml-1 h-6 w-6 fill-current"><path d="M8 5v14l11-7z" /></svg>
            </span>
          </button>
        )}

        {!(reduced && paused) && (
          <button
            type="button"
            onClick={toggleSound}
            className="absolute bottom-2 left-2 flex items-center gap-1.5 rounded-full border border-white/15 bg-black/55 py-1 pl-1 pr-2.5 text-left backdrop-blur-md transition-[border-color,background-color] duration-300 hover:border-[var(--film-accent)] hover:bg-black/70 sm:bottom-4 sm:left-4 sm:gap-2 sm:py-1.5 sm:pl-1.5 sm:pr-3.5"
            aria-label={muted ? "Activer le son et relancer le film" : "Couper le son"}
          >
            <span className="grid h-5 w-5 place-items-center rounded-full bg-[var(--film-accent)] text-white sm:h-7 sm:w-7">
              {muted ? (
                <svg viewBox="0 0 24 24" className="h-2.5 w-2.5 fill-none stroke-current sm:h-3.5 sm:w-3.5" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
                  <path d="M11 5 6 9H3v6h3l5 4z" /><path d="m22 9-6 6" /><path d="m16 9 6 6" />
                </svg>
              ) : (
                <svg viewBox="0 0 24 24" className="h-2.5 w-2.5 fill-none stroke-current sm:h-3.5 sm:w-3.5" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
                  <path d="M11 5 6 9H3v6h3l5 4z" /><path d="M15.5 8.5a5 5 0 0 1 0 7" /><path d="M18.5 5.5a9 9 0 0 1 0 13" />
                </svg>
              )}
            </span>
            <span className="text-[11px] font-semibold text-white/90 sm:text-[12.5px]">
              <span className="sm:hidden">{muted ? "Son" : "Couper"}</span>
              <span className="hidden sm:inline">{muted ? "Écouter avec le son" : "Couper le son"}</span>
            </span>
          </button>
        )}
      </div>
    </div>
  );
}

// Usage, right under the hero, on a section painted with the film's own dark ground:
//
// <section id="film" className="px-4 pb-6 pt-2 sm:px-6" style={{ background: "#0d0b0a" }}>
//   <LaunchFilm src="/motion/film.mp4" poster="/motion/film.jpg" label="Film de présentation : ..." />
// </section>
