/* Pairwise overlap auditor for gsap-explainer videos.
 * Inject into the page (javascript_tool), then call:
 *   __ovlAudit(sceneIdx, [t0,t1,...])   -> violations at those timeline times
 *   __ovlAuditAll(stepSeconds)          -> sweep every scene at `step` intervals (default 1s)
 *
 * Catches what frozen-preview sweeps miss: CSS-entrance elements are included
 * once their animation-delay <= t (geometry measured via a temporary force-visible style).
 * Includes the host actor and ambient mini-bees. Ancestor/descendant pairs skipped.
 * Deliberate teaching overlaps: give BOTH elements data-ovl-ok="sameToken".
 * RULE: nothing else may overlap — words on words, bee on anything, arrows on text = violation.
 *
 * Adapting to a specific file (extend an INJECTED copy, keep this canonical):
 * - extra entrance classes (e.g. spin-in): widen the isCssEntrance regex
 * - exiting elements (.shatter etc.): exclude after delay+exit-duration or they count forever
 * - text children under a not-yet-entered entrance ancestor: skip (phantom candidates)
 * - CSS-flight hosts (flagship FLIGHTS) don't tick in the frozen preview — compute their
 *   positions from keyframe %s × scene clock and intersect mathematically instead
 * - trust nothing: plant a fake overlap first and confirm the tool catches it
 */
/* CSS-entrance elements are measured per-element: temporarily forced to end-state
   ONLY when their animation-delay <= t, then restored. No blanket style. */

window.__ovlAudit = function(sceneIdx, times, opts){
  opts = opts || {};
  const MIN_PEN = opts.minPen || 8;              // px penetration to count
  const stage = document.querySelector('#xplStage');
  const root  = document.getElementById('xplRoot') || document.body;
  const scene = document.querySelector('.xpl-scene[data-scene="'+sceneIdx+'"]');
  if (!scene) return {error:'no scene '+sceneIdx};
  const out = [];
  window.__xpl.goto(sceneIdx);
  const tl = window.__xpl.tl();

  // parse a CSS element's entrance delay (inline animation-delay), seconds
  const delayOf = e => {
    const d = (e.style && e.style.animationDelay) || '';
    const m = d.match(/([\d.]+)s/); return m ? +m[1] : 0;
  };
  const isCssEntrance = e => /(^|\s)(fu|fi|pp|l3)(\s|$)/.test(e.className||'');

  try {
    for (const t of times) {
      if (tl && tl.duration() < 9e9) tl.pause(Math.min(t, tl.duration()-0.01)); else if (tl) tl.pause(t);
      const sb = stage.getBoundingClientRect(), sc = sb.width/800;
      // candidates: text-bearing leaves + marked props + actor + ambient bees
      const cands = []; const forced = [];
      scene.querySelectorAll('*').forEach(e => {
        const cs = getComputedStyle(e);
        if (cs.visibility==='hidden') return;
        const gsapHidden = !isCssEntrance(e) && +cs.opacity < 0.15;
        if (gsapHidden) return;
        if (isCssEntrance(e)) {
          if (delayOf(e) > t) return;                              // not yet on screen at time t
          forced.push([e, e.style.cssText]);
          e.style.animation='none'; e.style.opacity='1'; e.style.translate='0 0'; e.style.scale='1';
        }
        const hasText = [...e.childNodes].some(n=>n.nodeType===3 && n.textContent.trim().length>1);
        const marked  = e.hasAttribute('data-prop');
        if (!hasText && !marked) return;
        const b = e.getBoundingClientRect(); if (b.width<8||b.height<8) return;
        cands.push({e, b, kind: hasText?'text':'prop'});
      });
      const actor = document.querySelector('.xpl-actor');
      if (actor) { const b = actor.getBoundingClientRect();
        if (b.left < sb.right && b.right > sb.left) cands.push({e:actor,b,kind:'actor'}); }
      scene.querySelectorAll('.mb,.gbees span,.obee').forEach(e=>{
        const b=e.getBoundingClientRect(); if(b.width>6) cands.push({e,b,kind:'bee'});
      });
      // measure boxes AFTER all forcing (layout settled)
      cands.forEach(c=>{ c.b=c.e.getBoundingClientRect(); });
      forced.forEach(([e,css])=>{ e.style.cssText=css; });
      // pairwise
      for (let i=0;i<cands.length;i++) for (let j=i+1;j<cands.length;j++){
        const A=cands[i], B=cands[j];
        if (A.e.contains(B.e) || B.e.contains(A.e)) continue;
        if (A.kind==='text' && B.kind==='text' && (A.e.parentElement===B.e.parentElement) && A.e.closest('svg')) continue; // svg label siblings
        const ok1=A.e.getAttribute('data-ovl-ok'), ok2=B.e.getAttribute('data-ovl-ok');
        if (ok1 && ok1===ok2) continue;
        const L=Math.max(A.b.left,B.b.left), R=Math.min(A.b.right,B.b.right);
        const T=Math.max(A.b.top,B.b.top),  Bo=Math.min(A.b.bottom,B.b.bottom);
        const w=(R-L)/sc, h=(Bo-T)/sc;
        if (w>MIN_PEN && h>MIN_PEN) {
          const id = x => (x.e.className&&x.e.className.baseVal!==undefined?x.e.className.baseVal:String(x.e.className||x.e.tagName)).toString().trim().slice(0,26)+'['+x.kind+']';
          out.push({t, a:id(A), b:id(B), pen:Math.round(Math.min(w,h)),
            aTxt:(A.e.textContent||'').trim().slice(0,18), bTxt:(B.e.textContent||'').trim().slice(0,18)});
        }
      }
    }
  } finally {}
  // dedupe by pair, keep max penetration + first time
  const seen={};
  out.forEach(v=>{ const k=v.a+'|'+v.b; if(!seen[k]||v.pen>seen[k].pen) seen[k]={...v, firstT:(seen[k]?Math.min(seen[k].firstT,v.t):v.t)}; });
  return Object.values(seen).sort((x,y)=>y.pen-x.pen);
};

window.__ovlAuditAll = function(step){
  step = step || 0.5;   // 0.5s is the publish gate — 1s sampling missed a 96px transit strike
  const n = window.__xpl.scenes();
  const SC = (typeof SCENES!=='undefined') ? SCENES : null;
  const report = {};
  for (let i=0;i<n;i++){
    window.__xpl.goto(i);
    const tl = window.__xpl.tl();
    let dur = 20; try { const d = tl.duration(); if (d>0 && d<9e9) dur = Math.min(d+2, 30); } catch(e){}
    const times=[]; for(let t=0.8;t<=dur;t+=step) times.push(+t.toFixed(1));
    const v = window.__ovlAudit(i, times);
    if (v.length) report['S'+i] = v.slice(0,12);
  }
  return report;
};
'tool defined';
