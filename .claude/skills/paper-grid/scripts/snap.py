"""Quick layout stills from a built composition (diagnostic only; judge the encoded render, snapshots can race on seek).

    python3 snap.py <composition-dir> <out-dir> 0,30,120,...
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
comp, od, frames = Path(sys.argv[1]), Path(sys.argv[2]), [int(x) for x in sys.argv[3].split(',')]
od.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome')   # system Chrome; no Playwright browser download needed
    pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    pg.goto((comp / 'index.html').resolve().as_uri()); pg.wait_for_timeout(800)
    for f in frames:
        pg.evaluate(f"""async()=>{{const t={f}/30;window.__timelines.main.seek(t,false);
          for(const v of document.querySelectorAll('video')){{v.currentTime=t;await new Promise(r=>{{v.onseeked=r;setTimeout(r,800)}})}}}}""")
        pg.wait_for_timeout(120); pg.screenshot(path=str(od / f'f{f:04}.png'))
    b.close()
