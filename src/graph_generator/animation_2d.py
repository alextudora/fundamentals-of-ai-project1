"""
Animație 2D (vedere de sus, cameră fixă) a unui traseu pe graf.
Nu mai randează video: generează un singur fișier HTML care rulează animația direct în browser
(canvas), deci generarea durează fracțiuni de secundă.

Folosire:  python animation_2d.py [edges.csv] ['["A","B","C"]']
Rezultat:  graph_animation_2d.html (lângă CSV) - se deschide dublu-click în browser.
"""
import base64
import json
import sys
from pathlib import Path

import numpy as np

from generator import load_graph, shortest_route

# ================= SETĂRI =================
BASE = Path(__file__).resolve().parent
CSV_FILE = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else BASE / 'edges.csv'
SPRITES_DIR = BASE / 'sprites'
POSITIONS_FILE = None
SECONDS_PER_MINUTE = 0.8
MIN_EDGE_SECONDS = 0.6
PAUSE_AT_NODE = 0.5
END_HOLD = 2.5             # cât rămâne cadrul final după ce ajunge la destinație
SPRITE_STEP = 0.06         # distanța (unități din graf) după care se schimbă cadrul de mers
SPRITE_HEIGHT = 0.12       # înălțimea personajului ca fracțiune din înălțimea cadrului
POP_SECONDS = 1.0
POP_SCALE = 0.35
OUTPUT = CSV_FILE.with_name('graph_animation_2d.html')

# ================= DATE =================
data = load_graph(CSV_FILE, positions_file=POSITIONS_FILE)
und, dire, ed, GR, pos = data.undirected, data.directed, data.edges, data.route_graph, data.pos

path = json.loads(sys.argv[2]) if len(sys.argv) > 2 else shortest_route(data)
if not isinstance(path, list) or not path or not all(isinstance(n, str) for n in path):
    raise ValueError("The route must be a non-empty list of node IDs.")
if any(n not in GR for n in path):
    raise ValueError("The route contains a node that is not present in the selected graph.")
if any(not GR.has_edge(u, v) for u, v in zip(path, path[1:])):
    raise ValueError("The route contains a connection that is not present in the selected graph.")


def dur(w):
    return w * SECONDS_PER_MINUTE if w > 0 else MIN_EDGE_SECONDS


def xy(n):
    return [float(pos[n][0]), float(pos[n][1])]


# ================= TIMELINE =================
segs, arrival, t = [], {path[0]: 0.4}, 0.8
for u, v in zip(path[:-1], path[1:]):
    w = GR[u][v]['weight']
    segs.append(dict(a=xy(u), b=xy(v), t0=t, d=dur(w), w=float(w)))
    t += dur(w)
    arrival[v] = t
    t += PAUSE_AT_NODE
total_walk = segs[-1]['t0'] + segs[-1]['d'] if segs else 0.0
total_min = float(sum(s['w'] for s in segs))

# ================= SPRITE-URI (încorporate în HTML) =================
def sprite_uri(name):
    f = SPRITES_DIR / name
    if not f.exists():
        raise FileNotFoundError(f"Lipsește sprite-ul: {f}")
    return 'data:image/png;base64,' + base64.b64encode(f.read_bytes()).decode('ascii')


payload = dict(
    path=path,
    nodes={n: xy(n) for n in pos},
    und=[[u, v, float(ed[(u, v)])] for u, v in und],
    dire=[[u, v, float(w)] for u, v, w in dire],
    segs=segs,
    arrival={k: float(v) for k, v in arrival.items()},
    start=xy(path[0]),
    totalWalk=float(total_walk),
    totalMin=total_min,
    endHold=END_HOLD,
    spriteStep=SPRITE_STEP,
    spriteHeight=SPRITE_HEIGHT,
    popSeconds=POP_SECONDS,
    popScale=POP_SCALE,
    sprites=dict(
        walk=[sprite_uri(f'back_walk_{i}.png') for i in range(4)],
        idle=sprite_uri('back_idle.png'),
        trans=sprite_uri('side_walk_01.png'),
        front=sprite_uri('side_walk_00.png'),
    ),
)

HTML = r'''<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="utf-8">
<title>Animație traseu</title>
<style>
  body { margin: 0; background: #fff; font-family: system-ui, Arial, sans-serif; color: #1A2536; }
  #wrap { max-width: 1200px; margin: 0 auto; padding: 8px; }
  canvas { width: 100%; height: auto; display: block; }
  #bar { display: flex; gap: 8px; padding: 6px 0; }
  button { font-size: 14px; padding: 6px 14px; cursor: pointer; border: 1px solid #7A8A99; background: #f4f0e8; border-radius: 6px; }
</style>
</head>
<body>
<div id="wrap">
  <canvas id="c"></canvas>
  <div id="bar">
    <button id="play">Pauză</button>
    <button id="replay">Reia de la început</button>
  </div>
</div>
<script>
const D = __DATA__;
const W = 1200, H = 800;
const cv = document.getElementById('c');
const dpr = window.devicePixelRatio || 1;
cv.width = W * dpr; cv.height = H * dpr;
const ctx = cv.getContext('2d');
ctx.scale(dpr, dpr);

// ---------- transformare graf -> pixeli (cadru fix, vedere de sus) ----------
const names = Object.keys(D.nodes);
const xs = names.map(n => D.nodes[n][0]), ys = names.map(n => D.nodes[n][1]);
const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
const area = { l: 90, r: W - 90, t: 120, b: H - 70 };
const spanX = Math.max(maxX - minX, 0.5), spanY = Math.max(maxY - minY, 0.5);
const scale = Math.min((area.r - area.l) / spanX, (area.b - area.t) / spanY, 400);
const cx = (area.l + area.r) / 2, cy = (area.t + area.b) / 2;
const mx = (minX + maxX) / 2, my = (minY + maxY) / 2;
const toPx = p => [cx + (p[0] - mx) * scale, cy - (p[1] - my) * scale];
const P = {}; names.forEach(n => P[n] = toPx(D.nodes[n]));
const RPX = Math.max(16, Math.min(30, 0.075 * scale));

// ---------- sprite-uri ----------
const load = src => new Promise(res => { const i = new Image(); i.onload = () => res(i); i.src = src; });

// ---------- timeline ----------
const segs = D.segs.map(s => ({ ...s, L: Math.hypot(s.b[0] - s.a[0], s.b[1] - s.a[1]) }));
const cumW = [0], cumD = [0];
segs.forEach(s => { cumW.push(cumW[cumW.length - 1] + s.w); cumD.push(cumD[cumD.length - 1] + s.L); });
const TOTAL = D.totalWalk + D.endHold;

function stateAt(t) {
  if (!segs.length) return { p: D.start, el: 0, dist: 0, moving: false };
  let idx = segs.findIndex(s => t < s.t0 + s.d);
  if (idx < 0) idx = segs.length - 1;
  const s = segs[idx];
  if (t < s.t0) return { p: s.a, el: cumW[idx], dist: cumD[idx], moving: false };
  if (t >= s.t0 + s.d) return { p: s.b, el: cumW[idx] + s.w, dist: cumD[idx] + s.L, moving: false };
  const f = (t - s.t0) / s.d;
  return {
    p: [s.a[0] + (s.b[0] - s.a[0]) * f, s.a[1] + (s.b[1] - s.a[1]) * f],
    el: cumW[idx] + s.w * f, dist: cumD[idx] + s.L * f, moving: true
  };
}
const bump = x => (x >= 0 && x <= 1) ? Math.sin(Math.PI * x) : 0;

// ---------- desen ----------
function ends(u, v) {
  const a = P[u], b = P[v];
  const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1;
  const ux = dx / L, uy = dy / L;
  return { a: [a[0] + ux * RPX, a[1] + uy * RPX], b: [b[0] - ux * RPX, b[1] - uy * RPX], ux, uy };
}

// strat static (muchii + etichete de greutate) desenat o singură dată
const staticLayer = document.createElement('canvas');
staticLayer.width = W * dpr; staticLayer.height = H * dpr;
const sctx = staticLayer.getContext('2d'); sctx.scale(dpr, dpr);
function drawEdges(g) {
  g.lineCap = 'round'; g.lineWidth = 4;
  const labels = [];
  D.und.forEach(([u, v, w]) => {
    const e = ends(u, v);
    g.strokeStyle = '#7A8A99'; g.beginPath(); g.moveTo(...e.a); g.lineTo(...e.b); g.stroke();
    labels.push([(P[u][0] + P[v][0]) / 2, (P[u][1] + P[v][1]) / 2, w]);
  });
  D.dire.forEach(([u, v, w]) => {
    const e = ends(u, v);
    g.strokeStyle = '#C85A17'; g.beginPath(); g.moveTo(...e.a); g.lineTo(...e.b); g.stroke();
    const nx = -e.uy, ny = e.ux;
    [1, -1].forEach(s => {
      g.beginPath(); g.moveTo(...e.b);
      g.lineTo(e.b[0] - e.ux * 14 + nx * s * 7, e.b[1] - e.uy * 14 + ny * s * 7); g.stroke();
    });
    labels.push([(P[u][0] + P[v][0]) / 2, (P[u][1] + P[v][1]) / 2, w]);
  });
  labels.forEach(([x, y, w]) => weightLabelOn(g, x, y, w));
}
function weightLabelOn(g, x, y, w) {
  g.font = 'bold 13px system-ui, Arial, sans-serif';
  const txt = String(+w.toFixed(2)), tw = g.measureText(txt).width;
  g.fillStyle = 'rgba(255,255,255,0.9)';
  g.beginPath();
  if (g.roundRect) g.roundRect(x - tw / 2 - 5, y - 10, tw + 10, 20, 6); else g.rect(x - tw / 2 - 5, y - 10, tw + 10, 20);
  g.fill();
  g.fillStyle = '#1A2536'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText(txt, x, y + 1);
}

drawEdges(sctx);

let SP = null;
function draw(t) {
  const { p, el, dist, moving } = stateAt(t);
  const pp = toPx(p);

  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H);

  // titlu
  ctx.fillStyle = '#1A2536'; ctx.font = 'bold 22px system-ui, Arial, sans-serif';
  ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
  ctx.fillText('Ruta: ' + D.path.join(' \u2192 ') + '  (' + (+D.totalMin.toFixed(2)) + ' min)', 30, 50, W - 60);

  // muchii + greutăți
  ctx.drawImage(staticLayer, 0, 0, W, H);

  // urma de pași
  const pts = [];
  segs.forEach(s => { if (t >= s.t0) pts.push(toPx(s.a)); });
  pts.push(pp);
  if (pts.length > 1) {
    ctx.strokeStyle = 'rgba(30,136,229,0.85)'; ctx.lineWidth = 6; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath(); ctx.moveTo(...pts[0]); pts.slice(1).forEach(q => ctx.lineTo(...q)); ctx.stroke();
  }

  // noduri
  names.forEach(n => {
    const ta = D.arrival[n];
    const k = ta !== undefined ? bump((t - ta) / D.popSeconds) : 0;
    const visited = ta !== undefined && t >= ta;
    const r = RPX * (1 + D.popScale * k);
    ctx.beginPath(); ctx.arc(P[n][0], P[n][1], r, 0, Math.PI * 2);
    ctx.fillStyle = k > 0 ? '#FFB300' : (visited ? '#9BD3A8' : '#F4F0E8');
    ctx.fill(); ctx.lineWidth = 1.5; ctx.strokeStyle = '#1A2536'; ctx.stroke();
    ctx.fillStyle = '#1A2536'; ctx.font = 'bold 15px system-ui, Arial, sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
    ctx.fillText(n, P[n][0], P[n][1] - r - 5);
  });

  // personaj
  let img, bob = 0;
  if (moving) {
    img = SP.walk[Math.floor(dist / D.spriteStep) % SP.walk.length];
    bob = 3 * Math.abs(Math.sin(Math.PI * dist / D.spriteStep / 2));
  } else if (t < D.totalWalk) {
    img = SP.idle;
  } else {
    const extra = t - D.totalWalk;
    img = extra < 0.4 ? SP.idle : (extra < 0.8 ? SP.trans : SP.front);
  }
  ctx.fillStyle = 'rgba(0,0,0,0.28)';
  ctx.beginPath(); ctx.ellipse(pp[0], pp[1], 13, 6, 0, 0, Math.PI * 2); ctx.fill();
  const h = D.spriteHeight * H, w = img.naturalWidth * h / img.naturalHeight;
  ctx.drawImage(img, pp[0] - w / 2, pp[1] - bob - h, w, h);

  // ceas
  ctx.fillStyle = '#1A2536'; ctx.font = 'bold 20px system-ui, Arial, sans-serif';
  ctx.textAlign = 'right'; ctx.textBaseline = 'alphabetic';
  ctx.fillText(el.toFixed(1) + ' / ' + (+D.totalMin.toFixed(2)) + ' min', W - 30, H - 25);
}

// ---------- bucla de animație ----------
let t = 0, playing = true, last = null;
function frame(now) {
  if (last === null) last = now;
  const dt = (now - last) / 1000; last = now;
  if (playing) t = Math.min(TOTAL, t + dt);
  draw(t);
  requestAnimationFrame(frame);
}
const playBtn = document.getElementById('play');
playBtn.onclick = () => { playing = !playing; playBtn.textContent = playing ? 'Pauză' : 'Continuă'; };
document.getElementById('replay').onclick = () => { t = 0; playing = true; playBtn.textContent = 'Pauză'; };

Promise.all([...D.sprites.walk.map(load), load(D.sprites.idle), load(D.sprites.trans), load(D.sprites.front)])
  .then(imgs => {
    SP = { walk: imgs.slice(0, D.sprites.walk.length), idle: imgs[imgs.length - 3], trans: imgs[imgs.length - 2], front: imgs[imgs.length - 1] };
    requestAnimationFrame(frame);
  });
</script>
</body>
</html>
'''

if __name__ == '__main__':
    html = HTML.replace('__DATA__', json.dumps(payload, ensure_ascii=False).replace('</', '<\\/'))
    OUTPUT.write_text(html, encoding='utf-8')
    print('Salvat', OUTPUT)