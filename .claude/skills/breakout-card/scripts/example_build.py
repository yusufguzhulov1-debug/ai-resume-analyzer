"""Demo / smoke test for the breakout-card library: every component in ~25s on plates from build_plates.py.

    python3 example_build.py <plate-dir> <out-dir> [proof.png]

Frame numbers and captions here are arbitrary demo beats. In a real run, take them from the paper edit's word
timeline, put the build script in the run's work/ folder and pass real proof captures. Mechanics only: design each
real reel's beats for its own story.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from breakout import Reel, claude_mark

plates, out = Path(sys.argv[1]), sys.argv[2]
proof = sys.argv[3] if len(sys.argv) > 3 else None
reel = Reel(out, page_plate=plates / 'page-plate.mp4', cam_plate=plates / 'cam-plate.mp4', total=750)
reel.layouts([('page', 0, 200), ('cam', 200, 260), ('page', 260, 470), ('camz', 470, 540, 1.2, 1.27), ('page', 540, 750)])
reel.captions([('frame one', 0), ('shows the', .8), ('product', 1.4), ('moving', 2.2), ('then a', 3.3), ('BIG word.', 4.0, 6.6),
               ('name drop', 6.7), (None, 7.4, 8.6), ('rules tick', 8.7), ('on their', 9.6), ('words.', 10.4, 15.6),
               ('re-hook', 15.7), ('push in.', 16.6, 18.0), ('cta', 18.1), ('types', 19.0), ('the keyword.', 20.0, 25.0)])

with reel.scene('s1', 0, 200):                       # frame 1: proof already flying in
    if proof:
        reel.shot('proof', proof, top=214, at=0, drop=True, highlight=(14, 92, 420, 44, 11))
    else:
        reel.chip('proof', 'real proof goes here', top=300, at=0, ic='code')
    reel.counter_pill('stars', 215697, top=838, at=46, count=(50, 87))
    for sel in ('#proof', '#stars'):
        reel.blur_out(sel, 95)
    reel.headline('h', 300, f'makes {claude_mark(52)} claude', 'NOTICEABLY', 'SMARTER.', at=(97, 120, 140))
    reel.headline_out('h', 150)
    reel.tile_drop('fold', 470, 'folder', 'your project', 'CLAUDE.md', at=153, drop_at=168)
with reel.scene('s2', 200, 260):
    reel.title('ttl', 'CLAUDE.md', 400, 222)
with reel.scene('s3', 260, 470):
    reel.checklist('rules', 'Four rules.', [('Think before you code', 280, 292), ('Keep it simple', 300, 312), ('Only touch what you asked', 320, 332),
                                            ('Define done', 340, 352)], top=262, at=262)
    reel.pill('loop', "loop until it's true", top=800, at=370, ic='loop', ok_at=400)
    reel.spin('#loopI', 376)
with reel.scene('s5', 540, 750):
    reel.pill('pA', 'how it codes', top=390, at=542, ok_at=556)
    reel.pill('pB', 'where it looks', top=530, at=562, strike_at=584)
    reel.cursor_click('cur', 640, 600, 566, 584)
    for sel in ('#pA', '#pB', '#cur'):
        reel.blur_out(sel, 600, .24)
    reel.tree('t', ['archive/', 'assets/', 'brain/', 'node_modules/', 'skills/', 'video-editing/', 'work/'], top=222, at=604, sub={5}, meter=True)
    reel.tree_wander('t', [3, 0, 6, 2, 1], [470, 700, 500, 680, 560], 612, 640, meter_at=640)
    reel.blur_out('#t', 660, .24)
    reel.comment('cmt', 'CLAUDE', 340, 664, (670, 684), heart_at=690, chips=[('github', 'the repo', 700), ('doc', 'map template', 712)])
print(reel.compile('breakout-card demo'))
