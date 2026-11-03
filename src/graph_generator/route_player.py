"""
Player 2D pentru traseu, direct în Tkinter (vedere de sus, cameră fixă).
Nu generează video sau fișiere: desenează animația live pe un Canvas, deci pornește instant.

Folosire în app:
    player = RoutePlayer(parent_frame, sprites_dir)
    player.play(edges_csv_path, route_list)
"""
import math
import os
import re
import time
from pathlib import Path
from tkinter import Button, Canvas, Frame
from typing import Dict, List, Optional

from PIL import Image, ImageTk

from generator import load_graph

# ================= SETĂRI =================
SECONDS_PER_MINUTE = 0.8
MIN_EDGE_SECONDS = 0.6
PAUSE_AT_NODE = 0.5
END_HOLD = 2.5             # cât rămâne cadrul final după ce ajunge la destinație
SPRITE_STEP = 0.06         # distanța (unități din graf) după care se schimbă cadrul de mers
SPRITE_FACES_RIGHT = True  # False dacă side_walk_XX.png privesc spre stânga
SPRITE_HEIGHT = 0.12       # înălțimea personajului ca fracțiune din înălțimea canvasului
POP_SECONDS = 1.0
POP_SCALE = 0.35
FRAME_MS = 16              # ~60 fps

DARK = "#1A2536"
MUTED = "#667085"


def build_animation(graph, path: List[str]) -> Dict:
    """Validează ruta și construiește timeline-ul (poziții, segmente, momente de sosire)."""
    gr, pos = graph.route_graph, graph.pos
    if not isinstance(path, list) or not path or not all(isinstance(n, str) for n in path):
        raise ValueError("The route must be a non-empty list of node IDs.")
    if any(n not in gr for n in path):
        raise ValueError("The route contains a node that is not present in the selected graph.")
    if any(not gr.has_edge(u, v) for u, v in zip(path, path[1:])):
        raise ValueError("The route contains a connection that is not present in the selected graph.")

    def dur(w):
        return w * SECONDS_PER_MINUTE if w > 0 else MIN_EDGE_SECONDS

    def xy(n):
        return (float(pos[n][0]), float(pos[n][1]))

    segs, arrival, t = [], {path[0]: 0.4}, 0.8
    for u, v in zip(path[:-1], path[1:]):
        w = float(gr[u][v]["weight"])
        a, b = xy(u), xy(v)
        segs.append(dict(a=a, b=b, t0=t, d=dur(w), w=w, L=math.hypot(b[0] - a[0], b[1] - a[1]) or 1e-9))
        t += dur(w)
        arrival[v] = t
        t += PAUSE_AT_NODE

    total_walk = segs[-1]["t0"] + segs[-1]["d"] if segs else 0.0
    cum_w, cum_d = [0.0], [0.0]
    for s in segs:
        cum_w.append(cum_w[-1] + s["w"])
        cum_d.append(cum_d[-1] + s["L"])

    return dict(
        path=path,
        pos={n: xy(n) for n in pos},
        und=[(u, v, float(graph.edges[(u, v)])) for u, v in graph.undirected],
        dire=[(u, v, float(w)) for u, v, w in graph.directed],
        segs=segs,
        arrival=arrival,
        start=xy(path[0]),
        total_walk=total_walk,
        total_min=cum_w[-1],
        total_time=total_walk + END_HOLD,
        cum_w=cum_w,
        cum_d=cum_d,
    )


def state_at(d: Dict, t: float):
    """poziție, minute parcurse, distanță parcursă, merge?, direcția pe x"""
    segs = d["segs"]
    if not segs:
        return d["start"], 0.0, 0.0, False, 0.0
    idx = next((i for i, s in enumerate(segs) if t < s["t0"] + s["d"]), len(segs) - 1)
    s = segs[idx]
    cw, cd = d["cum_w"][idx], d["cum_d"][idx]
    dx = s["b"][0] - s["a"][0]
    if t < s["t0"]:
        return s["a"], cw, cd, False, dx
    if t >= s["t0"] + s["d"]:
        return s["b"], cw + s["w"], cd + s["L"], False, dx
    f = (t - s["t0"]) / s["d"]
    p = (s["a"][0] + (s["b"][0] - s["a"][0]) * f, s["a"][1] + (s["b"][1] - s["a"][1]) * f)
    return p, cw + s["w"] * f, cd + s["L"] * f, True, dx


def bump(x: float) -> float:
    return math.sin(math.pi * x) if 0 <= x <= 1 else 0.0


class RoutePlayer(Frame):
    def __init__(self, master, sprites_dir, bg: str = "#ffffff", **kwargs) -> None:
        super().__init__(master, bg=bg, **kwargs)
        self.bg = bg
        self.sprites_dir = Path(sprites_dir)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas = Canvas(self, bg=bg, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        bar = Frame(self, bg=bg)
        bar.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        btn_style = dict(bg="#f4f0e8", relief="flat", padx=14, pady=4, cursor="hand2", state="disabled")
        self.pause_btn = Button(bar, text="Pause", command=self.toggle_pause, **btn_style)
        self.pause_btn.pack(side="left", padx=(0, 6))
        self.restart_btn = Button(bar, text="Restart", command=self.restart, **btn_style)
        self.restart_btn.pack(side="left")

        self.data: Optional[Dict] = None
        self._graph_key = None
        self._graph = None
        self._pil: Optional[Dict[str, Image.Image]] = None
        self._photos: Dict[str, ImageTk.PhotoImage] = {}
        self._t = 0.0
        self._playing = False
        self._finished = False
        self._last = 0.0
        self._after: Optional[str] = None
        self._resize_job: Optional[str] = None

        self.canvas.bind("<Configure>", self._on_resize)
        self._layout()

    # ---------------- API public ----------------
    def play(self, csv_file, path: List[str]) -> None:
        graph = self._get_graph(csv_file)
        data = build_animation(graph, path)
        self._load_sprites()
        self.data = data
        self._t = 0.0
        self._playing = True
        self._finished = False
        self._layout()
        self._draw(0.0)
        self.pause_btn.config(state="normal", text="Pause")
        self.restart_btn.config(state="normal")
        self._start_loop()

    def clear(self) -> None:
        self._cancel_loop()
        self.data = None
        self._playing = False
        self.pause_btn.config(state="disabled", text="Pause")
        self.restart_btn.config(state="disabled")
        self._layout()

    def toggle_pause(self) -> None:
        if self.data is None:
            return
        if self._finished:
            self.restart()
            return
        self._playing = not self._playing
        self.pause_btn.config(text="Pause" if self._playing else "Resume")
        if self._playing:
            self._start_loop()

    def restart(self) -> None:
        if self.data is None:
            return
        self._t = 0.0
        self._playing = True
        self._finished = False
        self.pause_btn.config(text="Pause")
        self._start_loop()

    def destroy(self) -> None:
        self._cancel_loop()
        super().destroy()

    # ---------------- date ----------------
    def _get_graph(self, csv_file):
        key = (str(csv_file), os.path.getmtime(csv_file))
        if key != self._graph_key:
            # layout-ul se calculează o singură dată per fișier (poate dura câteva secunde)
            self._graph = load_graph(Path(csv_file))
            self._graph_key = key
        return self._graph

    def _load_sprites(self) -> None:
        if self._pil is not None:
            return
        def load(f):
            return Image.open(f).convert("RGBA")

        idle = self.sprites_dir / "side_walk_00.png"      # front idle: în picioare
        if not idle.exists():
            raise FileNotFoundError(f"Missing sprite: {idle}")
        frames = []
        for f in self.sprites_dir.glob("side_walk_*.png"):
            m = re.fullmatch(r"side_walk_(\d+)\.png", f.name)
            if m and int(m.group(1)) >= 1:
                frames.append((int(m.group(1)), f))
        frames.sort()
        if not frames:
            raise FileNotFoundError(f"No side_walk_01.png, side_walk_02.png ... found in {self.sprites_dir}")

        pil = {"idle": load(idle)}
        for i, (_, f) in enumerate(frames):
            im = load(f)
            pil[f"walk{i}"] = im
            pil[f"walkF{i}"] = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)   # variantă oglindită
        self._n_walk = len(frames)
        self._pil = pil

    # ---------------- bucla ----------------
    def _start_loop(self) -> None:
        if self._after is None:
            self._last = time.perf_counter()
            self._after = self.after(1, self._tick)

    def _cancel_loop(self) -> None:
        if self._after is not None:
            try:
                self.after_cancel(self._after)
            except Exception:
                pass
            self._after = None

    def _tick(self) -> None:
        self._after = None
        if self.data is None:
            return
        now = time.perf_counter()
        dt, self._last = now - self._last, now
        if self._playing:
            self._t = min(self.data["total_time"], self._t + dt)
        self._draw(self._t)
        if self._t >= self.data["total_time"]:
            self._finished = True
            self.pause_btn.config(text="Replay")
            return
        if self._playing:
            self._after = self.after(FRAME_MS, self._tick)

    def _on_resize(self, _event=None) -> None:
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(60, self._relayout)

    def _relayout(self) -> None:
        self._resize_job = None
        self._layout()
        if self.data is not None:
            self._draw(self._t)

    # ---------------- desen ----------------
    def _px(self, p):
        return (self._cx + (p[0] - self._mx) * self._scale, self._cy - (p[1] - self._my) * self._scale)

    def _layout(self) -> None:
        """Redesenează partea statică (muchii, noduri, etichete) și creează elementele animate."""
        c = self.canvas
        c.delete("all")
        w, h = max(c.winfo_width(), 300), max(c.winfo_height(), 200)
        d = self.data
        if d is None:
            c.create_text(w / 2, h / 2, text="Select a task to see the route animation.",
                          fill=MUTED, font=("Segoe UI", 12))
            return

        names = list(d["pos"])
        xs = [d["pos"][n][0] for n in names]
        ys = [d["pos"][n][1] for n in names]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        spanx, spany = max(maxx - minx, 0.5), max(maxy - miny, 0.5)
        left, right, top, bottom = 50, w - 50, 70, h - 50
        self._scale = min((right - left) / spanx, (bottom - top) / spany, 400)
        self._cx, self._cy = (left + right) / 2, (top + bottom) / 2
        self._mx, self._my = (minx + maxx) / 2, (miny + maxy) / 2
        R = max(12.0, min(24.0, 0.075 * self._scale))
        self._R = R
        P = {n: self._px(d["pos"][n]) for n in names}
        self._P = P

        def ends(u, v):
            a, b = P[u], P[v]
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy) or 1.0
            ux, uy = dx / L, dy / L
            return (a[0] + ux * R, a[1] + uy * R), (b[0] - ux * R, b[1] - uy * R), ux, uy

        labels = []
        for u, v, wt in d["und"]:
            a, b, _, _ = ends(u, v)
            c.create_line(*a, *b, fill="#7A8A99", width=4, capstyle="round")
            labels.append(((P[u][0] + P[v][0]) / 2, (P[u][1] + P[v][1]) / 2, wt))
        for u, v, wt in d["dire"]:
            a, b, ux, uy = ends(u, v)
            c.create_line(*a, *b, fill="#C85A17", width=4, capstyle="round")
            nx_, ny_ = -uy, ux
            for s in (1, -1):
                c.create_line(*b, b[0] - ux * 14 + nx_ * s * 7, b[1] - uy * 14 + ny_ * s * 7,
                              fill="#C85A17", width=4, capstyle="round")
            labels.append(((P[u][0] + P[v][0]) / 2, (P[u][1] + P[v][1]) / 2, wt))

        # urma de pași (sub etichete și noduri)
        self._trail = c.create_line(0, 0, 0, 0, fill="#1E88E5", width=6, capstyle="round", joinstyle="round")

        for x, y, wt in labels:
            tid = c.create_text(x, y, text=f"{wt:g}", fill=DARK, font=("Segoe UI", 9, "bold"))
            x0, y0, x1, y1 = c.bbox(tid)
            rid = c.create_rectangle(x0 - 4, y0 - 2, x1 + 4, y1 + 2, fill="#ffffff", outline="")
            c.tag_lower(rid, tid)

        self._node_items = {}
        self._nstate = {}
        for n in names:
            x, y = P[n]
            oval = c.create_oval(x - R, y - R, x + R, y + R, fill="#F4F0E8", outline=DARK, width=1.5)
            txt = c.create_text(x, y - R - 4, text=n, anchor="s", fill=DARK, font=("Segoe UI", 10, "bold"))
            self._node_items[n] = (oval, txt)

        # sprite-uri redimensionate pentru dimensiunea curentă a canvasului
        sh = max(40, int(SPRITE_HEIGHT * h))
        self._photos = {}
        for key, im in self._pil.items():
            sw = max(1, int(im.width * sh / im.height))
            self._photos[key] = ImageTk.PhotoImage(im.resize((sw, sh), Image.Resampling.LANCZOS))

        self._shadow = c.create_oval(0, 0, 0, 0, fill="#c9cdd2", outline="")
        self._sprite = c.create_image(0, 0, anchor="s", image=self._photos["idle"])
        self._cur_img = "idle"

        title = "Ruta: " + " \u2192 ".join(d["path"]) + f"  ({d['total_min']:g} min)"
        c.create_text(16, 14, text=title, anchor="nw", width=w - 32, fill=DARK, font=("Segoe UI", 12, "bold"))
        self._clock = c.create_text(w - 16, h - 14, anchor="se", text="", fill=DARK, font=("Segoe UI", 12, "bold"))

    def _draw(self, t: float) -> None:
        d, c, P, R = self.data, self.canvas, self._P, self._R
        p, el, dist, moving, dx = state_at(d, t)
        px, py = self._px(p)

        # urma de pași
        pts = []
        for s in d["segs"]:
            if t >= s["t0"]:
                pts.extend(self._px(s["a"]))
        pts.extend((px, py))
        if len(pts) < 4:
            pts = pts * 2
        c.coords(self._trail, *pts)

        # noduri (se actualizează doar cele care și-au schimbat starea)
        for n, (oval, txt) in self._node_items.items():
            ta = d["arrival"].get(n)
            k = bump((t - ta) / POP_SECONDS) if ta is not None else 0.0
            visited = ta is not None and t >= ta
            st = (round(k, 2), visited)
            if self._nstate.get(n) != st:
                r = R * (1 + POP_SCALE * k)
                x, y = P[n]
                c.coords(oval, x - r, y - r, x + r, y + r)
                c.itemconfigure(oval, fill="#FFB300" if k > 0 else ("#9BD3A8" if visited else "#F4F0E8"))
                c.coords(txt, x, y - r - 4)
                self._nstate[n] = st

        # personaj
        bob = 0.0
        if moving:
            go_right = dx >= 0
            flip = (not go_right) if SPRITE_FACES_RIGHT else go_right
            frame = int(dist / SPRITE_STEP) % self._n_walk
            key = f"walk{'F' if flip else ''}{frame}"
            bob = 3 * abs(math.sin(math.pi * dist / SPRITE_STEP / 2))
        else:
            key = "idle"   # front idle: la start, în noduri și la final
        if key != self._cur_img:
            c.itemconfigure(self._sprite, image=self._photos[key])
            self._cur_img = key
        c.coords(self._sprite, px, py - bob)
        c.coords(self._shadow, px - 13, py - 5, px + 13, py + 5)

        c.itemconfigure(self._clock, text=f"{el:.1f} / {d['total_min']:g} min")