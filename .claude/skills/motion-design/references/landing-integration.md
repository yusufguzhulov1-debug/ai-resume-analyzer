# Put the film on a website

The render is a master (20 to 70 MB). A page needs a light file that starts fast, plays muted on its own, and a
frame that makes the film stand out. This is how the film "Le devis" sits under the hero of entrepreneurs2-0.com.

## 1. Encode for the web

```bash
ffmpeg -i <project>/renders/video.mp4 -c:v libx264 -profile:v high -preset slow -crf 24 -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart public/motion/film.mp4
```

- `-crf 24`: about 6 MB for a flat 43 s film in 1920 x 1080 (5.6 MB for "Le devis"). A textured direction (wood,
  grain) weighs more: check the texture on a still, lower the crf by 1 or 2 if it turned to mush.
- `-movflags +faststart` moves the index to the head of the file: the browser starts playing before the download ends.
- `yuv420p` and the `high` profile play everywhere, including Safari on iPhone.

Poster (the image shown before playback, and the social preview): pick a frame that tells the story on its own, not
the first frame (a word alone on black says nothing), e.g. the stressed persona surrounded by his pain labels.

```bash
ffmpeg -ss 12.9 -i <project>/renders/video.mp4 -frames:v 1 -q:v 3 public/motion/film.jpg
```

Optional silent loop for the very top of a page (8 to 18 s, no audio track):

```bash
ffmpeg -ss 0 -t 12 -i <project>/renders/video.mp4 -an -c:v libx264 -preset slow -crf 26 -pix_fmt yuv420p -movflags +faststart public/motion/loop.mp4
```

## 2. Play it the right way

- **Muted autoplay when it is on screen.** No browser plays sound on its own, and the film reads without sound (every
  sentence writes itself on screen). Start it muted when 45 % of it is visible (`IntersectionObserver`), pause it when
  it leaves the screen (it saves the battery and the viewer does not miss the start).
- **A sound button that restarts from the beginning.** Turning the sound on mid-film drops the viewer in the middle
  of a sentence: restart at 0 so they hear the hook.
- **`prefers-reduced-motion`**: nothing starts by itself; show a play button instead.
- Attributes: `muted`, `playsInline` (iPhone would open it full screen otherwise), `loop`, `preload="metadata"`, a
  `poster`, and an `aria-label` that says what the film says.

## 3. Frame it

- **Section background = the film's own dark ground** (`#0d0b0a` for the example films): the dark scenes melt into
  the page, no black rectangle around the video.
- **But give the film a visible frame**: on its own dark ground, a frameless film reads "black on black" and looks
  odd. A 2 px border in the accent color with a soft glow of the same color and 10 px corners makes it stand out as an
  object, while the section stays seamless. A faint ember of the accent behind the frame helps too.
- Keep it wide (up to about 1120 px) and close to the hero: it is the proof of the page, not a footnote.

## 4. The component

`templates/LaunchFilm.tsx` is a ready React + Tailwind component (Next.js "use client") doing all of the above:
props `src`, `poster`, `label`, `accent` (default `#c25b28`), `stage` (default `#0d0b0a`). Put the encoded files in
`public/motion/`, then:

```tsx
<section id="film" className="px-4 pb-6 pt-2 sm:px-6" style={{ background: "#0d0b0a" }}>
  <LaunchFilm src="/motion/film.mp4" poster="/motion/film.jpg" label="Film de présentation : ..." />
</section>
```

Without React, the same behavior in plain HTML:

```html
<section style="background:#0d0b0a;padding:8px 16px">
  <div style="max-width:1120px;margin:auto;aspect-ratio:16/9;border:2px solid #c25b28;border-radius:10px;overflow:hidden;box-shadow:0 0 48px -8px rgba(194,91,40,.55)">
    <video id="film" src="/motion/film.mp4" poster="/motion/film.jpg" muted loop playsinline preload="metadata"
      aria-label="Film de présentation : ..." style="width:100%;height:100%;object-fit:cover;display:block"></video>
  </div>
  <button id="film-sound" type="button">Écouter avec le son</button>
</section>
<script>
  const v = document.getElementById("film"), b = document.getElementById("film-sound");
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) { v.controls = true; }
  else new IntersectionObserver(([e]) => (e.isIntersecting ? v.play().catch(() => {}) : v.pause()), { threshold: 0.45 }).observe(v);
  b.onclick = () => { v.muted = !v.muted; if (!v.muted) { v.currentTime = 0; v.play(); } b.textContent = v.muted ? "Écouter avec le son" : "Couper le son"; };
</script>
```

## 5. Change the music or the version later

Keep the same file name, replace the file with another option (`music.md`: mux another mix into the same render),
re-encode with the command above, deploy. The page does not change.

## Checks

- The file starts playing within a second on a phone connection (open the page with the network throttled).
- Muted autoplay works on Safari iPhone (needs `muted` + `playsInline`).
- The sound button restarts at 0 with the voice; turning it off keeps the film running muted.
- The frame is visible on the dark section; the poster is not the empty first frame.
