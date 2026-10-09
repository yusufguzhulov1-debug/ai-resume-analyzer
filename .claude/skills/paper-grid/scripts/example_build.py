"""Demo / smoke test for the paper-grid library: every component in ~26s on any 1080x1920 camera plate.

    python3 example_build.py <camera-clean.mp4> <out-dir> [proof.png]

Frame numbers here are arbitrary demo beats. In a real run, take them from the paper edit's word timeline,
put the build script in the run's work/ folder and pass real proof captures.
This demo shows mechanics only; design each real reel's beats for its own story.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paper_grid import Reel, claude_mark

cam, out = sys.argv[1], sys.argv[2]
proof = sys.argv[3] if len(sys.argv) > 3 else None
reel = Reel(out, camera=cam, total=780)
reel.layouts([('split', 0, 300), ('face', 300, 335), ('split', 335, 560), ('face', 560, 600), ('split', 600, 780)])

with reel.scene('sPost', 0, 120):               # frame 1 already shows the product moving
    reel.live_chip('now', 'Just dropped', until=50)
    reel.chip('pack', 'Claude skill pack', logo=claude_mark(), at=54)
    reel.post_card('post', at=0, drop=True, stack_at=30, autopilot_at=66, counts=((248, 37, 19), 70, 115),
                   bubbles=[('Great point 👏', 80, 640, 812), ('Saving this.', 92, 210, 822)])
with reel.scene('sFree', 120, 160):
    reel.big_number('zero', '$<span>0</span>', 120, chips=[('star', 'Free'), ('github', 'Open source'), ('check', 'MIT')])
with reel.scene('sProof', 160, 220):
    if proof:
        reel.image_card('shot', proof, 160, kenburns=(160, 220))
    else:
        reel.hero_chip('stand', 'Real proof goes here', 'code', 162)
with reel.scene('sSkills', 220, 300):
    reel.skill_beat('k1', 'Post Writer', 'pen', 220, 258, 'typed', text="Most people write from a blank page. Here's what I do ↓",
                    type_span=(226, 252), tag=('Hook formula: curiosity gap', 240, 'hook'))
    reel.skill_beat('k2', 'Content Planner', 'calendar', 258, None, 'week', fill_at=264)
with reel.scene('sHero', 335, 360):
    reel.hero_chip('hum', 'Humanizer', 'sparkle', 335)
PARTS = [("In today's fast-paced world", 1), (", it's ", 0), ("crucial", 1), (" to ", 0), ("leverage", 1), (" AI ", 0), ("—", 2),
         (" and ", 0), ("delve", 1), (" into what matters ", 0), ("—", 2), (" to grow.", 0)]
with reel.scene('sDraft', 360, 500):
    reel.flag_draft('draft', 360, PARTS, flag_frames=[372, 384, 392, 404], scan=(368, 412), dash_fix=(420, [(0, 432), (1, 438)]), shrink_at=450)
    reel.meter_rows('det', [('Detector A', .22), ('Detector B', .48), ('Detector C', .14)], at=458, fill_at=466, focus_at=486,
                    note=('eye', 'Only you see this', 490))
with reel.scene('sYes', 500, 560):
    reel.approval('ok', 500, click_at=538)
with reel.scene('sBlank', 600, 630):
    reel.composer('blank', 600, 630)
with reel.scene('sNote', 630, 720):
    reel.note_to_post('note', 630, [('SHIPPED', 'A new feature', 640, 656), ('WHAT CHANGED', 'Less busywork', 662, 678)],
                      fly_at=684, post_html="Here's what changed this week ↓", post_at=696, counts=((120, 18), 704, 718))
with reel.scene('sCta', 720, 780):
    reel.cta('cta', 'KEYWORD', 720, (724, 738), 742, chips=[('github', 'The repo', 752), ('note', 'The template', 764)])
reel.camera_moves(face_pushes=[(300, 335, 1.04, 1.16), (560, 600, 1.0, 1.06)], split_settles=[335, 600], split_push=(0, 38, 1.07))
print(reel.compile('paper-grid demo'))
