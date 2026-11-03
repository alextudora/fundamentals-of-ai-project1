import json
import os
import sys
from dataclasses import dataclass

import networkx as nx
import numpy as np
import pandas as pd


@dataclass
class GraphData:
    edges: dict          # {(from, to): minute}  exact ca în CSV
    undirected: set      # {(a, b)} drumuri bidirecționale (aceleași minute în ambele sensuri)
    directed: list       # [(from, to, minute)] drumuri cu sens unic
    graph: nx.DiGraph    # graf pentru desen/layout (bidirecționalele apar o singură dată)
    route_graph: nx.DiGraph  # graf pentru rutare (bidirecționalele merg în ambele sensuri)
    pos: dict            # {nod: np.array([x, y])}


def load_edges(csv_file, from_col='from', to_col='to', weight_col='minutes'):
    """Citește muchiile. Numele coloanelor sunt configurabile, ca să meargă și cu alte fișiere."""
    df = pd.read_csv(csv_file)
    df.columns = [str(c).strip() for c in df.columns]
    for c in (from_col, to_col, weight_col):
        if c not in df.columns:
            raise ValueError(f"Coloana '{c}' nu există în {csv_file}. Coloane găsite: {list(df.columns)}")
    df = df.dropna(subset=[from_col, to_col, weight_col])
    edges = {}
    for _, r in df.iterrows():
        u, v, w = str(r[from_col]).strip(), str(r[to_col]).strip(), float(r[weight_col])
        if w < 0:
            raise ValueError(f"Durată negativă pe muchia {u} -> {v}: {w}")
        if u == v:
            continue  # ignorăm buclele (nod -> același nod)
        edges[(u, v)] = w  # dacă o muchie apare de mai multe ori, rămâne ultima
    if not edges:
        raise ValueError(f"Nu s-au găsit muchii valide în {csv_file}")
    return edges


def split_edges(edges):
    """Separă muchiile în bidirecționale (aceleași minute în ambele sensuri) și cu sens unic."""
    undirected, directed = set(), []
    for (u, v), w in edges.items():
        if (v, u) in edges and edges[(v, u)] == w:
            undirected.add((min(u, v), max(u, v)))
        else:
            directed.append((u, v, w))
    return undirected, directed


def build_graphs(edges, undirected, directed):
    g, gr = nx.DiGraph(), nx.DiGraph()
    for u, v in undirected:
        w = edges[(u, v)]
        g.add_edge(u, v, weight=w, bidirectional=True)
        gr.add_edge(u, v, weight=w); gr.add_edge(v, u, weight=w)
    for u, v, w in directed:
        g.add_edge(u, v, weight=w, bidirectional=False)
        gr.add_edge(u, v, weight=w)
    return g, gr


# ---------------------------------------------------------------------------
#  LAYOUT FĂRĂ SUPRAPUNERI
#  Se generează multe aranjamente (planar, Kamada-Kawai, spring cu multe seed-uri),
#  se notează cu o "penalizare" pentru:
#    - noduri prea apropiate          - linii care trec prin / foarte aproape de alte noduri
#    - linii care se intersectează    - linii paralele/lipite una de alta
#    - linii care pleacă din același nod sub un unghi prea mic
#  iar cel mai bun este îmbunătățit prin mutări mici ale nodurilor (hill climbing).
#  Funcționează pentru orice graf, nu depinde de numele nodurilor.
# ---------------------------------------------------------------------------
def _pt_seg(X, A, B):
    """Distanța de la fiecare punct din X (M,2) la fiecare segment A[j]-B[j] -> (M,E)."""
    AB = B - A
    L2 = np.maximum((AB ** 2).sum(1), 1e-12)
    XA = X[:, None, :] - A[None, :, :]
    t = np.clip((XA * AB[None]).sum(2) / L2[None], 0, 1)
    C = A[None] + t[..., None] * AB[None]
    return np.linalg.norm(X[:, None, :] - C, axis=2)


class _LayoutScorer:
    def __init__(self, n, pairs, min_dist, clearance, sep, min_angle):
        self.n, self.E = n, len(pairs)
        self.min_dist, self.clearance, self.sep, self.min_angle = min_dist, clearance, sep, min_angle
        self.iu = np.array([p[0] for p in pairs], dtype=int)
        self.iv = np.array([p[1] for p in pairs], dtype=int)
        self.tri = np.triu(np.ones((n, n), bool), 1)
        self.nbrs = [[] for _ in range(n)]
        for u, v in pairs:
            self.nbrs[u].append(v); self.nbrs[v].append(u)
        if self.E:
            self.incid = np.zeros((n, self.E), bool)
            self.incid[self.iu, np.arange(self.E)] = True
            self.incid[self.iv, np.arange(self.E)] = True
            share = (self.incid.T.astype(int) @ self.incid.astype(int)) > 0
            self.pairmask = np.triu(~share)          # perechi de muchii care NU au un nod comun

    def parts(self, P):
        """Returnează (noduri_apropiate, muchii_prin_noduri, intersecții, muchii_lipite, unghiuri_mici, lungime)."""
        D = np.linalg.norm(P[:, None] - P[None], axis=2)
        nn = (np.maximum(0, 1 - D[self.tri] / self.min_dist) ** 2).sum()
        if not self.E:
            return nn, 0, 0, 0, 0, 0
        A, B = P[self.iu], P[self.iv]
        dn = _pt_seg(P, A, B)
        ne = (np.maximum(0, 1 - dn / self.clearance) ** 2)[~self.incid].sum()
        dA, dB = _pt_seg(A, A, B), _pt_seg(B, A, B)
        d = np.minimum(np.minimum(dA, dB), np.minimum(dA.T, dB.T))
        cr = lambda p, q, r: (q[..., 0] - p[..., 0]) * (r[..., 1] - p[..., 1]) - (q[..., 1] - p[..., 1]) * (r[..., 0] - p[..., 0])
        o1, o2 = cr(A[:, None], B[:, None], A[None]), cr(A[:, None], B[:, None], B[None])
        o3, o4 = cr(A[None], B[None], A[:, None]), cr(A[None], B[None], B[:, None])
        crossings = ((o1 * o2 < 0) & (o3 * o4 < 0) & self.pairmask).sum()
        close = ((np.maximum(0, 1 - d / self.sep) ** 2) * self.pairmask).sum()
        ang = 0.0
        for i, nb in enumerate(self.nbrs):
            if len(nb) > 1:
                a = np.sort(np.arctan2(P[nb, 1] - P[i, 1], P[nb, 0] - P[i, 0]))
                gap = np.diff(np.concatenate([a, [a[0] + 2 * np.pi]])).min()
                ang += max(0, 1 - gap / self.min_angle) ** 2
        return nn, ne, crossings, close, ang, np.linalg.norm(B - A, axis=1).sum()

    def __call__(self, P):
        nn, ne, cr_, close, ang, length = self.parts(P)
        return 60 * nn + 80 * ne + 150 * cr_ + 40 * close + 40 * ang + 0.3 * length


def _refine(P, scorer, rng, steps, L):
    best = scorer(P)
    for t in range(steps):
        sigma = 0.25 * (1 - t / steps) + 0.02
        i = rng.integers(len(P))
        Q = P.copy()
        Q[i] = np.clip(Q[i] + rng.normal(0, sigma, 2), -L, L)
        sc = scorer(Q)
        if sc < best:
            P, best = Q, sc
    return P, best


def compute_layout(graph, seed=42, k=1.5, iterations=50, tries=150, refine_steps=1500,
                   min_dist=0.40, clearance=0.16, sep=0.10, min_angle_deg=25):
    """Poziții pentru noduri, fără suprapuneri.
    min_dist   = distanța minimă între două noduri
    clearance  = distanța minimă dintre un nod și o linie care nu pleacă din el
    sep        = distanța minimă între două linii diferite
    Mărește aceste valori pentru un desen mai aerisit; crește `tries`/`refine_steps` pentru căutare mai amănunțită.
    (Unitățile: nodurile încap într-un pătrat de ~[-1,1]; pentru grafuri mari pătratul crește automat.)"""
    nodes = list(graph.nodes)
    n = len(nodes)
    if n <= 2:
        pos = nx.spring_layout(graph, seed=seed)
        return {nd: np.array(p, dtype=float) for nd, p in pos.items()}

    idx = {nd: i for i, nd in enumerate(nodes)}
    pairs = sorted({(min(idx[u], idx[v]), max(idx[u], idx[v])) for u, v in graph.edges() if u != v})
    ug = nx.Graph()
    ug.add_nodes_from(nodes)
    ug.add_edges_from((nodes[i], nodes[j]) for i, j in pairs)

    L = max(1.0, float(np.sqrt(n / 12.0)))
    def to_array(pos):
        arr = np.array([pos[nd] for nd in nodes], dtype=float)
        arr -= (arr.max(0) + arr.min(0)) / 2
        m = np.abs(arr).max()
        return arr * (L / m) if m > 0 else arr

    candidates = []
    try:
        if nx.check_planarity(ug)[0]:
            candidates.append(to_array(nx.planar_layout(ug)))
    except Exception:
        pass
    try:
        candidates.append(to_array(nx.kamada_kawai_layout(ug)))
    except Exception:
        pass
    for s in range(seed, seed + tries):
        candidates.append(to_array(nx.spring_layout(ug, seed=s, k=k, iterations=iterations)))

    scorer = _LayoutScorer(n, pairs, min_dist, clearance, sep, np.radians(min_angle_deg))
    candidates.sort(key=scorer)
    rng = np.random.default_rng(seed)
    results = [_refine(P, scorer, rng, refine_steps, L) for P in candidates[:3]]
    best, _ = min(results, key=lambda r: r[1])
    return {nodes[i]: best[i].copy() for i in range(n)}


def layout_report(data_or_pos, graph, **kw):
    """Utilitar de verificare: câte suprapuneri are un layout."""
    pos = data_or_pos
    nodes = list(graph.nodes); idx = {nd: i for i, nd in enumerate(nodes)}
    pairs = sorted({(min(idx[u], idx[v]), max(idx[u], idx[v])) for u, v in graph.edges() if u != v})
    P = np.array([pos[nd] for nd in nodes])
    sc = _LayoutScorer(len(nodes), pairs, kw.get('min_dist', .4), kw.get('clearance', .16), kw.get('sep', .1),
                       np.radians(kw.get('min_angle_deg', 25)))
    D = np.linalg.norm(P[:, None] - P[None], axis=2)[sc.tri]
    nn, ne, cr_, close, ang, _ = sc.parts(P)
    return dict(distanta_minima_noduri=round(float(D.min()), 3), intersectii_linii=int(cr_),
                linii_prea_aproape_de_noduri=round(float(ne), 3), linii_lipite=round(float(close), 3))


def save_positions(pos, path='nodes.json'):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({n: [float(p[0]), float(p[1])] for n, p in pos.items()}, f, indent=2, ensure_ascii=False)


def load_positions(path):
    with open(path, encoding='utf-8') as f:
        return {n: np.array(p, dtype=float) for n, p in json.load(f).items()}


def load_graph(csv_file, positions_file=None, seed=42, k=1.5, iterations=50,
               from_col='from', to_col='to', weight_col='minutes'):
    """Punctul de intrare. Dacă positions_file există, pozițiile se citesc de acolo
    (poți edita manual nodes.json); altfel se generează automat."""
    edges = load_edges(csv_file, from_col, to_col, weight_col)
    undirected, directed = split_edges(edges)
    g, gr = build_graphs(edges, undirected, directed)
    if positions_file and os.path.exists(positions_file):
        pos = load_positions(positions_file)
        missing = set(g.nodes) - set(pos)
        if missing:
            raise ValueError(f"Lipsesc poziții pentru nodurile: {sorted(missing)}")
    else:
        pos = compute_layout(g, seed, k, iterations)
    return GraphData(edges, undirected, directed, g, gr, pos)


def auto_route_endpoints(data):
    """Alege automat un traseu când nu specifici unul: pornește din primul nod din CSV
    și merge la cel mai îndepărtat nod la care se poate ajunge (în minute)."""
    start = next(iter(data.edges))[0]
    dist = nx.single_source_dijkstra_path_length(data.route_graph, start, weight='weight')
    end = max((n for n in dist if n != start), key=lambda n: dist[n], default=None)
    if end is None:
        raise ValueError(f"Din '{start}' nu se poate ajunge la niciun alt nod.")
    return start, end


def shortest_route(data, start=None, end=None):
    """Cel mai scurt drum (în minute), respectând sensurile unice. Returnează lista de noduri.
    Dacă start/end sunt None, traseul se alege automat."""
    if start is None or end is None:
        start, end = auto_route_endpoints(data)
    for n in (start, end):
        if n not in data.route_graph:
            raise ValueError(f"Nodul '{n}' nu există. Noduri disponibile: {sorted(data.route_graph.nodes)}")
    try:
        return nx.shortest_path(data.route_graph, start, end, weight='weight')
    except nx.NetworkXNoPath:
        raise ValueError(f"Nu există drum de la '{start}' la '{end}' (ținând cont de sensurile unice).")


if __name__ == '__main__':
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'edges.csv'
    data = load_graph(csv_file)
    print(f"{len(data.pos)} noduri, {len(data.undirected)} drumuri bidirecționale, {len(data.directed)} cu sens unic")
    for n, p in data.pos.items():
        print(f"  {n}: ({p[0]:.3f}, {p[1]:.3f})")
    save_positions(data.pos)
    print("Poziții salvate în nodes.json")