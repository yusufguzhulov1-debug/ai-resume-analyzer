#!/usr/bin/env python3
"""Inline the free GSAP 3.13 runtime into a self-contained explainer HTML file.

Usage: python3 inline-gsap.py <target.html> [--refresh]
  default   : replace the single <!--GSAP_INLINE--> marker with all inlined <script> blocks
  --refresh : strip previously-inlined GSAP (/* inlined: ... */ blocks) and re-inline the
              current suite in their place (upgrades an already-inlined file)

Why inline at all: a self-contained / published HTML file usually can't load CDN scripts
(strict Content-Security-Policy), so GSAP has to live inside the file.

Why this repo ships NO GSAP code: GSAP is free to fetch yourself. On first run each plugin
is downloaded from the public jsDelivr CDN into ./vendor/ (which is .gitignored), then
inlined. GSAP is 100% free — including every formerly-premium plugin (DrawSVG, MorphSVG,
SplitText, Physics2D, MotionPath, Flip, the Custom* eases, ...) — since Webflow's 2025
acquisition. See https://gsap.com/ .
"""
import sys, os, re, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(HERE, 'vendor')
CDN = 'https://cdn.jsdelivr.net/npm/gsap@3.13.0/dist/'
MARKER = '<!--GSAP_INLINE-->'
INLINED_RE = r'<script>/\* inlined: [^*]+\*/.*?</script>\n?'

# production set — ORDER MATTERS (core first; CustomEase before CustomWiggle/CustomBounce)
FILES = ['gsap.min.js', 'DrawSVGPlugin.min.js', 'MotionPathPlugin.min.js',
         'MorphSVGPlugin.min.js', 'SplitText.min.js',
         'Physics2DPlugin.min.js', 'PhysicsPropsPlugin.min.js',
         'CustomEase.min.js', 'CustomWiggle.min.js', 'CustomBounce.min.js',
         'Flip.min.js', 'ScrambleTextPlugin.min.js']

REGISTER = ('<script>/* inlined: register-plugins */\n'
            'gsap.registerPlugin(DrawSVGPlugin,MotionPathPlugin,MorphSVGPlugin,SplitText,'
            'Physics2DPlugin,PhysicsPropsPlugin,CustomEase,CustomWiggle,CustomBounce,'
            'Flip,ScrambleTextPlugin);\n</script>')


def ensure(fname):
    """Return the JS source for a plugin, downloading it into vendor/ if missing."""
    path = os.path.join(VENDOR, fname)
    if not os.path.exists(path):
        os.makedirs(VENDOR, exist_ok=True)
        url = CDN + fname
        print('  fetching', url)
        with urllib.request.urlopen(url, timeout=60) as r:
            data = r.read()
        if len(data) < 500:
            raise RuntimeError('suspiciously small download for %s (%d bytes)' % (fname, len(data)))
        open(path, 'wb').write(data)
    return open(path, encoding='utf-8').read()


def blob():
    parts = []
    for f in FILES:
        parts.append('<script>/* inlined: ' + f + ' */\n' + ensure(f) + '\n</script>')
    parts.append(REGISTER)
    return '\n'.join(parts)


def main():
    if len(sys.argv) < 2:
        sys.exit('usage: inline-gsap.py <target.html> [--refresh]')
    target = sys.argv[1]
    s = open(target, encoding='utf-8').read()

    if '--refresh' in sys.argv:
        i = s.find('<script>/* inlined:')
        if i == -1:
            sys.exit('no inlined GSAP blocks found to refresh in ' + target)
        # replace the whole run of inlined blocks with a fresh marker, then fall through
        s = s[:i] + MARKER + re.sub(INLINED_RE, '', s[i:], flags=re.S)

    if MARKER not in s:
        sys.exit('no %s marker in %s (already inlined? use --refresh)' % (MARKER, target))

    s = s.replace(MARKER, blob(), 1)
    open(target, 'w', encoding='utf-8').write(s)
    print('inlined GSAP (%d plugins) into %s -> %d KB'
          % (len(FILES) - 1, target, os.path.getsize(target) // 1024))


if __name__ == '__main__':
    main()
