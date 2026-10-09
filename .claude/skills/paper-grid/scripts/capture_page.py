"""Real proof capture of a public web page (e.g. a GitHub repo) at 2x, light theme, site header removed.

    python3 capture_page.py <url> <out.png> [--full] [--crop x,y,w,h]   (crop in 1x CSS pixels)

Screenshots show a static fact; for an action, record motion instead (see the screen-recording skill).
"""
import sys
from playwright.sync_api import sync_playwright
url, out = sys.argv[1], sys.argv[2]
full = '--full' in sys.argv
crop = next((sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == '--crop'), None)
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')
    pg = b.new_context(viewport={'width': 900, 'height': 1100}, device_scale_factor=2, color_scheme='light').new_page()
    pg.goto(url, wait_until='networkidle'); pg.wait_for_timeout(1200)
    pg.evaluate("document.querySelectorAll('header.AppHeader,.js-header-wrapper,[data-testid=cookie-banner]').forEach(e=>e.remove())")
    kw = {'path': out, 'full_page': full}
    if crop:
        x, y, w, h = map(float, crop.split(',')); kw['clip'] = {'x': x, 'y': y, 'width': w, 'height': h}
    pg.screenshot(**kw); b.close()
print(out)
