#!/usr/bin/env python3
"""Li Gong · Rib Purification (갈비뼈 순화) → the unmoving mind (不動心). REAL-TIME follow-along.
After 마리지천摩利支天 (@z9_s8_y_9): posts of 2026-11-18 KST (rib purification) and 2026-11-21 KST (iron wall).
Breath at true pace: 5 s inhale / 7 s exhale with 'Om', 18 cycles.
Pure Python: matplotlib (Agg) draws every frame, numpy synthesises the audio, ffmpeg encodes H.264/AAC.
No image or video generators.
Usage: python3 rib_purification.py [out.mp4] [--still t1,t2,...]
"""
import os, sys, wave, subprocess, multiprocessing as mp
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Circle, Ellipse, Polygon, FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1280, 720, 30
for f in ["/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
          "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"]:
    if os.path.exists(f):
        fm.fontManager.addfont(f)
plt.rcParams["font.family"] = ["Noto Serif CJK TC", "DejaVu Sans", "Noto Sans Symbols"]
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

# ---------------------------------------------------------------- palette (as five_gates_realtime.py)
BG_TOP, BG_BOT = np.array([14, 18, 48]) / 255, np.array([4, 5, 14]) / 255
BODY = "#141a3d"
GOLD, GOLD_L = "#d4af37", "#f3d98b"
CINN, CINN_L = "#c8372d", "#ff7a4d"
WATER, WATER_L = "#3f8fd6", "#8fd0ff"
IVORY, MUTED = "#efe6d2", "#8d8aa6"
VIOLET = "#b9a6ff"
MURK = "#4e3e48"

# ---------------------------------------------------------------- timeline
INH, EXH = 5.0, 7.0
PERIOD = INH + EXH
NCYC = 18
LEAD = 4.0                      # seconds into "breathe" before cycle 1
SEGMENTS = [("intro", 12), ("setup", 24), ("breathe", LEAD + NCYC * PERIOD + 6), ("wall", 64), ("close", 18)]
STARTS, acc = {}, 0.0
for n, d in SEGMENTS:
    STARTS[n] = (acc, d); acc += d
TOTAL = acc
NFRAMES = int(round(TOTAL * FPS))
LABELS = {"intro": "intro", "setup": "locate", "breathe": "rib purification · 18 breaths",
          "wall": "iron wall → collapse → heart-fire", "close": "close"}

def seg_at(t):
    for n, d in SEGMENTS:
        s, _ = STARTS[n]
        if t < s + d:
            return n, t - s, d
    n, d = SEGMENTS[-1]
    return n, d - 1e-3, d

def breath(u):
    """inside 'breathe': dict(n, done, inh(bool), p (0..1 phase progress), b (lung volume), active, rem)"""
    e = u - LEAD
    out = dict(n=0, done=0, inh=True, p=0.0, b=0.0, active=False, rem=0.0, k=-1)
    if e < 0:
        out["rem"] = -e; return out
    k, w = int(e // PERIOD), e % PERIOD
    if k >= NCYC:
        out.update(n=NCYC, done=NCYC, k=NCYC); return out
    if w < INH:
        p = w / INH; b = 0.5 - 0.5 * np.cos(np.pi * p); out.update(inh=True, p=p, b=b, rem=INH - w)
    else:
        p = (w - INH) / EXH; b = 0.5 + 0.5 * np.cos(np.pi * p); out.update(inh=False, p=p, b=b, rem=PERIOD - w)
    out.update(n=k + 1, done=k, active=True, k=k)
    return out

# ---------------------------------------------------------------- helpers
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def lerp(a, b, t): return a + (b - a) * t
def fade(u, d, fi=0.6, fo=0.5): return ease(u / fi) * ease((d - u) / fo)
def lerp_color(c1, c2, t):
    a = np.array(matplotlib.colors.to_rgb(c1)); b = np.array(matplotlib.colors.to_rgb(c2))
    return tuple(a + (b - a) * clamp(t))

def glow(ax, x, y, r, color, a=1.0, z=5, n=10):
    if a <= 0.01 or r <= 0: return
    for i in range(n):
        k = 1 - i / n
        ax.add_patch(Circle((x, y), r * k, color=color, alpha=clamp(a * 0.11), lw=0, zorder=z))

def txt(ax, x, y, s, size=14, color=IVORY, a=1.0, ha="left", va="center", weight="normal", z=20, **kw):
    if a <= 0.01: return
    ax.text(x, y, s, fontsize=size, color=color, alpha=clamp(a), ha=ha, va=va, fontweight=weight, zorder=z,
            linespacing=1.35, **kw)

def catmull(pts, n=14, closed=True):
    P = np.array(pts, float); m = len(P); out = []
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0 = P[i - 1] if (closed or i > 0) else P[0]
        p1, p2 = P[i], P[(i + 1) % m]
        p3 = P[(i + 2) % m] if (closed or i + 2 < m) else P[-1]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    if not closed: out.append(P[-1])
    return np.array(out)

def poly_at(P, f):
    """point at fraction f (0..1) of arc length along polyline P"""
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    s = clamp(f) * d[-1]
    i = min(np.searchsorted(d, s, side="right") - 1, len(P) - 2)
    t = (s - d[i]) / max(1e-9, d[i + 1] - d[i])
    return P[i] + (P[i + 1] - P[i]) * t

def poly_sub(P, f0, f1, n=40):
    return np.array([poly_at(P, f) for f in np.linspace(clamp(f0), clamp(f1), n)])

def flow(ax, P, f, color, a=1.0, trail=0.4, lw=3.0, head=0.32, z=12):
    """light travelling along path P, head at fraction f, fading trail behind"""
    if a <= 0.01: return
    f0 = max(0.0, f - trail)
    if f - f0 > 0.005:
        seg = poly_sub(P, f0, f, 24)
        for i in range(len(seg) - 1):
            k = (i + 1) / (len(seg) - 1)
            ax.plot(seg[i:i + 2, 0], seg[i:i + 2, 1], color=color, lw=lw * 2.6, alpha=clamp(a * 0.12 * k), zorder=z,
                    solid_capstyle="round")
            ax.plot(seg[i:i + 2, 0], seg[i:i + 2, 1], color=color, lw=lw, alpha=clamp(a * k), zorder=z + 0.1,
                    solid_capstyle="round")
    hx, hy = poly_at(P, f)
    glow(ax, hx, hy, head, color, a, z=z + 0.2, n=7)
    ax.add_patch(Circle((hx, hy), 0.045, color=IVORY, alpha=clamp(a), zorder=z + 0.3))

def faint_path(ax, P, color, a, lw=1.0, ls=(0, (3, 4)), z=7):
    if a > 0.01: ax.plot(P[:, 0], P[:, 1], color=color, lw=lw, alpha=clamp(a), ls=ls, zorder=z)

# ---------------------------------------------------------------- side-view body (facing left)
def profile(ax, ox, oy, s=1.0, a=1.0, zb=3):
    def P(x, y): return np.array((ox + x * s, oy + y * s))
    torso = [(2.75, 6.25), (2.68, 5.9), (2.25, 5.45), (1.98, 4.75), (2.05, 4.0), (2.0, 3.2),
             (2.1, 2.4), (2.35, 1.9), (3.4, 1.72), (4.2, 1.95), (4.0, 2.8), (4.12, 3.8),
             (4.35, 4.8), (4.22, 5.6), (3.55, 6.25)]
    tor = catmull([P(*q) for q in torso])
    head_c, legs_c = P(3.1, 6.95), P(2.55, 1.55)
    if a > 0.01:
        for lw, al in [(7, 0.05), (3.5, 0.10), (1.5, 0.8)]:
            ax.add_patch(Polygon(tor, closed=True, fill=False, ec=GOLD, lw=lw, alpha=al * a, zorder=zb))
            ax.add_patch(Ellipse(head_c, 1.25 * s, 1.5 * s, fill=False, ec=GOLD, lw=lw, alpha=al * a, zorder=zb))
            ax.add_patch(Ellipse(legs_c, 4.3 * s, 0.95 * s, fill=False, ec=GOLD, lw=lw, alpha=al * a, zorder=zb))
        ax.add_patch(Ellipse(legs_c, 4.3 * s, 0.95 * s, color=BODY, alpha=a, lw=0, zorder=zb + 1))
        ax.add_patch(Polygon(tor, closed=True, color=BODY, alpha=a, lw=0, zorder=zb + 1))
        ax.add_patch(Ellipse(head_c, 1.25 * s, 1.5 * s, color=BODY, alpha=a, lw=0, zorder=zb + 1))
        ax.plot(*zip(P(2.49, 7.05), P(2.36, 6.82), P(2.5, 6.78)), color=GOLD, lw=1.2, alpha=0.8 * a, zorder=zb + 2)
        ax.plot(*zip(P(2.68, 7.05), P(2.86, 7.03)), color=GOLD, lw=1.0, alpha=0.6 * a, zorder=zb + 2)
        sp = catmull([P(3.35, 6.15), P(3.78, 5.5), P(3.98, 4.8), P(3.88, 3.8), P(3.66, 2.9), P(3.78, 2.1)],
                     n=20, closed=False)
        ax.plot(sp[:, 0], sp[:, 1], color=GOLD, lw=0.8, alpha=0.35 * a, zorder=zb + 2)
        for i in np.linspace(4, len(sp) - 3, 22).astype(int):
            d = sp[i + 1] - sp[i - 1]; d = d / np.linalg.norm(d); nrm = np.array([-d[1], d[0]])
            p, q = sp[i] - nrm * 0.1 * s, sp[i] + nrm * 0.1 * s
            ax.plot([p[0], q[0]], [p[1], q[1]], color=GOLD, lw=2.4 * s, alpha=0.3 * a, solid_capstyle="round", zorder=zb + 2)
    return dict(center=P(2.62, 4.35), front=P(1.99, 4.42), lingtai=P(3.97, 4.95), mingmen=P(3.68, 2.95),
                lower=P(2.75, 2.45), prefrontal=P(2.62, 7.35), parietal=P(3.4, 7.62), s=s)

def side_ring(d, n=90):
    """perspective ring of the ribcage at chest level, front surface → Lingtai. returns (near, far) arcs F→L"""
    F, L = d["front"], d["lingtai"]
    M = (F + L) / 2; u = (L - F) / np.linalg.norm(L - F); v = np.array([-u[1], u[0]])
    a_ = np.linalg.norm(L - F) / 2; b_ = 0.42 * d["s"]
    th_near = np.linspace(np.pi, 2 * np.pi, n); th_far = np.linspace(np.pi, 0, n)
    near = np.array([M + a_ * np.cos(t) * u + b_ * np.sin(t) * v for t in th_near])
    far = np.array([M + a_ * np.cos(t) * u + b_ * np.sin(t) * v for t in th_far])
    return near, far

# ---------------------------------------------------------------- top-down ribcage
TCX, TCY, TRX, TRY = 7.75, 4.35, 1.95, 1.5
TC = np.array((TCX, TCY - 0.62)); TL = np.array((TCX, TCY + TRY - 0.22))
def top_paths():
    k = 0.84
    out = []
    for sgn in (1, -1):
        a = np.linspace(-np.pi / 2, np.pi / 2, 80) if sgn > 0 else np.linspace(-np.pi / 2, -3 * np.pi / 2, 80)
        arc = np.c_[TCX + TRX * k * np.cos(a), TCY + TRY * k * np.sin(a)]
        out.append(np.vstack([TC, arc[1:]]))
    return out
TOP_INH = top_paths()
TOP_EXH = np.array([TL, TC])

def ribcage_top(ax, a=1.0, label=True):
    if a <= 0.01: return
    th = np.linspace(0, 2 * np.pi, 160)
    ax.add_patch(Ellipse((TCX, TCY), 2 * TRX, 2 * TRY, color=BODY, alpha=0.92 * a, zorder=4))
    for lw, al in [(7, 0.06), (1.6, 0.8)]:
        ax.plot(TCX + TRX * np.cos(th), TCY + TRY * np.sin(th), color=GOLD, lw=lw, alpha=al * a, zorder=5)
    for kk in (0.55, 0.7, 0.84):
        ax.plot(TCX + TRX * kk * np.cos(th), TCY + TRY * kk * np.sin(th), color=GOLD, lw=0.5, alpha=0.15 * a, zorder=5)
    ax.add_patch(FancyBboxPatch((TCX - 0.24, TCY + TRY - 0.12), 0.48, 0.36, boxstyle="round,pad=0,rounding_size=0.08",
                                fc=BODY, ec=GOLD_L, lw=1.1, alpha=a, zorder=7))
    txt(ax, TCX, TCY + TRY + 0.06, "T5", 8, GOLD_L, a, ha="center", z=8)
    if label:
        txt(ax, TCX, TCY + TRY + 0.7, "ribcage from above", 12, GOLD_L, a, ha="center")
        txt(ax, TCX, TCY - TRY - 0.25, "FRONT · sternum", 9.5, MUTED, a, ha="center")
        txt(ax, TCX - 0.35, TCY + TRY + 0.06, "BACK · spine", 9.5, MUTED, a, ha="right")

# turbid-qi particles: each released on one inhale and washed out to Lingtai
NP = 72
_rs = np.random.RandomState(11)
P_ANG = _rs.uniform(0, 2 * np.pi, NP); P_RAD = np.sqrt(_rs.uniform(0, 1, NP)) * 0.55
P_REL = np.sort((NCYC * (1 - np.sqrt(1 - _rs.uniform(0, 0.97, NP)))).astype(int))   # more washed out early
P_SIDE = _rs.randint(0, 2, NP); P_PH = _rs.uniform(0, 2 * np.pi, NP); P_DEL = _rs.uniform(0, 0.25, NP)

def turbid(ax, u, br, A):
    k = br["k"]
    for i in range(NP):
        rel = P_REL[i]
        if br["active"] and k > rel: continue
        if not br["active"] and br["done"] >= NCYC: continue
        jx = 0.05 * np.sin(1.3 * u + P_PH[i]); jy = 0.05 * np.cos(1.1 * u + P_PH[i] * 1.7)
        base = TC + np.array((P_RAD[i] * np.cos(P_ANG[i]) * 1.3, P_RAD[i] * np.sin(P_ANG[i]) * 0.9 + 0.15))
        pos, al = base + (jx, jy), 0.75
        if br["active"] and k == rel and br["inh"]:
            f = ease((br["p"] - P_DEL[i]) / 0.75)
            path = TOP_INH[P_SIDE[i]]
            target = poly_at(path, f)
            pos = base * (1 - min(1, f * 4)) + target * min(1, f * 4) if f < 0.25 else target
            al = 0.75 * (1 - ease((f - 0.75) / 0.25))
        elif br["active"] and k == rel and not br["inh"]:
            continue
        ax.add_patch(Circle(pos, 0.055, color=MURK, alpha=clamp(al * A), lw=0, zorder=9))
        ax.add_patch(Circle(pos, 0.11, color="#2a2230", alpha=clamp(0.35 * al * A), lw=0, zorder=8.9))

def remaining(br):
    if not br["active"]:
        return 1.0 if br["done"] < NCYC else 0.0
    k = br["k"]; frac = np.mean(P_REL >= k)
    if br["inh"]:
        frac -= np.mean(P_REL == k) * ease(br["p"])
    else:
        frac -= np.mean(P_REL == k)
    return max(0.0, frac)

# ---------------------------------------------------------------- right panel
PX = 10.75
def title(ax, zh, en, a, sub=None):
    txt(ax, PX, 7.95, zh, 26, GOLD, a, weight="bold")
    txt(ax, PX, 7.35, en, 15, IVORY, a)
    if sub: txt(ax, PX, 6.92, sub, 10.5, MUTED, a)

def lines_block(ax, y0, lines, a, size=11.5, color=IVORY, dy=0.36, x=PX):
    for i, s in enumerate(lines):
        if isinstance(s, tuple): s, c = s
        else: c = color
        txt(ax, x, y0 - i * dy, s, size, c, a)

def cue(ax, br, a):
    if br["active"]:
        big, col = ("INHALE", WATER_L) if br["inh"] else ("EXHALE", CINN_L)
        sub = "들숨 · out along the ribs to Lingtai" if br["inh"] else "날숨 · 'Om' · straight back to the center"
        cnt, secs = f"Breath {br['n']} / {NCYC}", br["rem"]
    elif br["done"] >= NCYC:
        big, col, sub, cnt, secs = "REST", IVORY, "breathe naturally", f"Breaths complete · {NCYC} / {NCYC}", None
    else:
        big, col, sub, cnt, secs = "READY", MUTED, "breath 1 begins with the bell", f"Breath 1 of {NCYC} in", br["rem"]
    txt(ax, PX, 2.05, big, 34, col, a, weight="bold", family="DejaVu Serif")
    if secs is not None and secs > 0.05:
        txt(ax, PX + 3.55, 2.03, f"{int(np.ceil(secs - 1e-6))}", 20, MUTED, a, family="DejaVu Serif")
    txt(ax, PX, 1.45, cnt, 13, IVORY, a)
    txt(ax, PX, 1.05, sub, 10.5, MUTED, a)
    # beads
    for i in range(NCYC):
        bx, by = PX + 2.55 + (i % 9) * 0.2, 1.52 - (i // 9) * 0.22
        on, cur = i < br["done"], (i == br["done"] and br["active"])
        ax.add_patch(Circle((bx, by), 0.055, color=GOLD_L if (on or cur) else MUTED,
                            alpha=a * (1.0 if on else (0.35 + 0.65 * br["b"]) if cur else 0.3), lw=0, zorder=20))
    # breath ring
    x, y = 15.15, 2.0; r = 0.1 + 0.42 * br["b"]
    ax.add_patch(Circle((x, y), 0.52, fill=False, ec=MUTED, lw=0.8, alpha=0.45 * a, zorder=15))
    rc = WATER_L if br["inh"] else CINN_L
    ax.add_patch(Circle((x, y), r, fc=rc, alpha=0.22 * a, lw=0, zorder=15))
    ax.add_patch(Circle((x, y), r, fill=False, ec=rc, lw=1.6, alpha=0.9 * a, zorder=15))
    # phase progress bar under the big word
    if br["active"]:
        ax.plot([PX, PX + 4.6], [2.5, 2.5], color=MUTED, lw=1, alpha=0.3 * a, zorder=15)
        ax.plot([PX, PX + 4.6 * br["p"]], [2.5, 2.5], color=col, lw=2.4, alpha=0.9 * a, zorder=16)

# ---------------------------------------------------------------- scenes
SIDE = dict(ox=0.25, oy=0.55, s=0.95)

def sc_intro(ax, u, d):
    A = fade(u, d, 0.8, 0.9)
    for i in range(7):
        r = ((u * 0.35 + i / 7) % 1.0) * 3.8
        ax.add_patch(Circle((8, 4.6), r, fill=False, ec=GOLD_L, lw=0.9, alpha=0.22 * A * (1 - r / 3.8), zorder=2))
    glow(ax, 8, 4.6, 1.1, GOLD_L, 0.5 * A, z=3)
    at = ease((u - 1.0) / 1.5) * A
    txt(ax, 8, 5.35, "갈비뼈 순화", 50, GOLD, at, ha="center", weight="bold")
    txt(ax, 8, 4.3, "Rib Purification", 22, IVORY, at, ha="center")
    txt(ax, 8, 3.65, "the iron wall and its collapse  ·  toward the unmoving mind  不動心", 13, GOLD_L,
        ease((u - 2.5) / 1.5) * A, ha="center")
    txt(ax, 8, 2.9, "REAL-TIME FOLLOW-ALONG  ·  18 BREATHS  ·  5 s IN / 7 s OUT WITH 'OM'", 11, MUTED,
        ease((u - 3.5) / 1.5) * A, ha="center")
    txt(ax, 8, 1.35, "after 마리지천摩利支天 @z9_s8_y_9 · posts of 2026-11-18 and 2026-11-21 KST", 10.5, MUTED,
        ease((u - 4.5) / 1.5) * A, ha="center")
    txt(ax, 8, 1.95, "Don't press emotion down. Spread it out along the ribs, and draw it back to the center.", 12.5,
        GOLD_L, ease((u - 6.0) / 1.2) * A, ha="center", style="italic")

def points(ax, d, a, pulse=0.0):
    c, lt = d["center"], d["lingtai"]
    glow(ax, c[0], c[1], 0.32 + 0.06 * pulse, GOLD_L, a, z=10, n=7)
    ax.add_patch(Circle(c, 0.06, color=GOLD_L, alpha=a, zorder=11))
    glow(ax, lt[0], lt[1], 0.22, CINN_L, a * 0.8, z=10, n=6)
    ax.add_patch(Circle(lt, 0.06, color=CINN_L, alpha=a, zorder=11))

def sc_setup(ax, u, d):
    A = fade(u, d, 0.8, 0.5)
    dd = profile(ax, **SIDE, a=ease(u / 1.5) * A)
    ribcage_top(ax, ease((u - 0.5) / 1.5) * A)
    title(ax, "定位", "Find the two points", ease((u - 0.5)) * A, "sit upright · eyes softly closed")
    a1 = ease((u - 2.5) / 1.2) * A; a2 = ease((u - 8.0) / 1.2) * A; a3 = ease((u - 13.5) / 1.2) * A; a4 = ease((u - 19.0) / 1.2) * A
    c, lt = dd["center"], dd["lingtai"]
    # center
    for i in range(6):
        ax.add_patch(Circle(c, 0.25 + i * 0.22, fill=False, ec=GOLD_L, lw=0.8, alpha=a1 * (0.45 - i * 0.06), zorder=9))
    glow(ax, c[0], c[1], 0.32, GOLD_L, a1, z=10, n=7); ax.add_patch(Circle(c, 0.06, color=GOLD_L, alpha=a1, zorder=11))
    glow(ax, *TC, 0.3, GOLD_L, a1, z=10, n=7); ax.add_patch(Circle(TC, 0.06, color=GOLD_L, alpha=a1, zorder=11))
    txt(ax, TC[0], TC[1] - 0.33, "center", 10, GOLD_L, a1, ha="center")
    lines_block(ax, 6.3, [("1 · The center  중심", GOLD_L), "1 cm above the solar plexus (명치),",
                          "5 cm in, inside the chest."], a1)
    # lingtai
    glow(ax, lt[0], lt[1], 0.22, CINN_L, a2 * 0.8, z=10, n=6); ax.add_patch(Circle(lt, 0.06, color=CINN_L, alpha=a2, zorder=11))
    ax.add_patch(Circle(TL, 0.06, color=CINN_L, alpha=a2, zorder=11))
    txt(ax, TCX + 0.35, TCY + TRY + 0.06, "Lingtai 영대", 10, CINN_L, a2)
    ax.plot([c[0], lt[0]], [c[1], lt[1]], color=GOLD_L, lw=1.0, alpha=0.6 * a2, zorder=10)
    txt(ax, lt[0] + 0.32, lt[1] + 0.55, "Lingtai\n靈臺 · ~T5", 10.5, CINN_L, a2)
    lines_block(ax, 5.05, [("2 · Lingtai  영대 靈臺", CINN_L), "on the spine behind the heart,",
                           "around T5 (his placement)."], a2)
    # routes
    for P in TOP_INH: faint_path(ax, P, WATER_L, 0.75 * a3, lw=1.4)
    faint_path(ax, TOP_EXH, CINN_L, 0.75 * a3, lw=1.4)
    near, far = side_ring(dd)
    faint_path(ax, np.vstack([c, near]), WATER_L, 0.7 * a3, lw=1.2); faint_path(ax, far, WATER_L, 0.35 * a3, lw=1.0)
    lines_block(ax, 3.8, [("3 · The circuit  水平 회전 회로", GOLD_L), ("in: out along both rib edges to Lingtai", WATER_L),
                          ("out + 'Om': straight back to the center", CINN_L)], a3)
    txt(ax, PX, 2.25, "Don't push the breath down to the belly.\nLet the chest open sideways and around.", 12, GOLD_L, a4,
        style="italic")
    txt(ax, PX, 1.25, "breathing begins in a moment", 10.5, MUTED, a4)

def sc_breathe(ax, u, d):
    A = fade(u, d, 0.8, 0.8)
    br = breath(u)
    s_exp = br["b"] if br["active"] else 0.0
    dd = profile(ax, **SIDE, a=A)
    ribcage_top(ax, A)
    rem = remaining(br)
    prog = 1 - rem
    # chest center: from coarse reddish heat to clear gold as turbid qi washes out
    ccol = lerp_color("#b0563f", GOLD_L, prog)
    c, lt = dd["center"], dd["lingtai"]
    glow(ax, c[0], c[1], 0.36 + 0.08 * s_exp, ccol, A, z=10, n=7)
    ax.add_patch(Circle(c, 0.06, color=ccol, alpha=A, zorder=11))
    glow(ax, lt[0], lt[1], 0.22, CINN_L, A * 0.7, z=10, n=6); ax.add_patch(Circle(lt, 0.06, color=CINN_L, alpha=A, zorder=11))
    glow(ax, *TC, 0.34 + 0.06 * s_exp, ccol, A, z=10, n=7); ax.add_patch(Circle(TC, 0.06, color=ccol, alpha=A, zorder=11))
    ax.add_patch(Circle(TL, 0.06, color=CINN_L, alpha=A, zorder=11))
    # murk around the side-view center fades with progress
    glow(ax, c[0], c[1], 0.75, "#3a2a34", A * 0.9 * rem, z=9, n=6)
    near, far = side_ring(dd)
    side_in = np.vstack([c, near]); side_far = np.vstack([c, far])
    for P in TOP_INH: faint_path(ax, P, WATER_L, 0.22 * A)
    faint_path(ax, TOP_EXH, CINN_L, 0.22 * A)
    faint_path(ax, side_in, WATER_L, 0.2 * A); faint_path(ax, far, WATER_L, 0.12 * A)
    # ribcage widening rings (side view) on inhale
    for i in range(5):
        r = 0.35 + i * 0.25 + 0.18 * s_exp
        ax.add_patch(Circle(c, r, fill=False, ec=GOLD_L, lw=0.7, alpha=A * (0.25 - i * 0.04) * (0.4 + 0.6 * s_exp), zorder=8))
    turbid(ax, u, br, A)
    if br["active"]:
        p = br["p"]
        if br["inh"]:
            f = ease(p)
            for P in TOP_INH: flow(ax, P, f, WATER_L, A, trail=0.45)
            flow(ax, side_in, f, WATER_L, A, trail=0.45, lw=2.6, head=0.26)
            flow(ax, side_far, f, WATER_L, A * 0.45, trail=0.4, lw=1.8, head=0.2, z=7.5)
            if p > 0.85:
                glow(ax, *TL, 0.35 * ease((p - 0.85) / 0.15), WATER_L, A, z=11)
        else:
            f = ease(p / 0.8)
            flow(ax, TOP_EXH, f, CINN_L, A, trail=0.5, lw=3.2)
            flow(ax, np.array([lt, c]), f, CINN_L, A, trail=0.5, lw=2.6, head=0.26)
            om = 0.5 + 0.5 * np.sin(2 * np.pi * 1.2 * p * EXH / 3)
            ao = A * ease(p / 0.1) * ease((1 - p) / 0.15)
            txt(ax, TCX + 0.22, TCY + 0.25, "Om", 15, CINN_L, ao * (0.6 + 0.4 * om), style="italic")
            for i in range(3):   # om vibration rings at the side-view center
                r = ((p * 3 + i / 3) % 1.0) * 1.1
                ax.add_patch(Circle(c, 0.1 + r, fill=False, ec=CINN_L, lw=0.9, alpha=ao * 0.4 * (1 - r / 1.1), zorder=9))
            if f >= 1.0:
                glow(ax, *TC, 0.5 * ease((p - 0.8) / 0.2), ccol, A, z=11)
    txt(ax, TCX + 0.35, TCY + TRY + 0.06, "Lingtai 영대", 9.5, CINN_L, A * 0.9)
    txt(ax, TC[0], TC[1] - 0.33, "center", 9.5, GOLD_L, A * 0.8, ha="center")
    txt(ax, TCX, TCY + TRY + 0.7, "ribcage from above", 12, GOLD_L, A, ha="center")
    txt(ax, TCX, TCY - TRY - 0.25, "FRONT · sternum", 9.5, MUTED, A, ha="center")
    txt(ax, TCX - 0.35, TCY + TRY + 0.06, "BACK · spine", 9.5, MUTED, A, ha="right")
    txt(ax, 2.7, 0.75, "side view", 9.5, MUTED, A, ha="center")
    # right panel
    title(ax, "갈비뼈 순화", "Rib purification · real time", A, "the horizontal circuit through the chest")
    lines_block(ax, 6.3, [("In  들숨: the ribcage widens; carry the", WATER_L), ("chest's congestion out along both rib", WATER_L),
                          ("edges and scatter it to Lingtai.", WATER_L)], A, size=11)
    lines_block(ax, 5.1, [("Out  날숨 + 'Om': draw what gathered at", CINN_L), ("Lingtai straight back along the", CINN_L),
                          ("midline to the center.", CINN_L)], A, size=11)
    # turbid qi meter
    txt(ax, PX, 3.75, "turbid qi 濁氣 in the ribs", 10.5, MUTED, A)
    ax.add_patch(FancyBboxPatch((PX, 3.33), 4.6, 0.16, boxstyle="round,pad=0,rounding_size=0.06", fc="none", ec=MUTED,
                                lw=0.8, alpha=0.6 * A, zorder=15))
    if rem > 0.005:
        ax.add_patch(FancyBboxPatch((PX + 0.02, 3.35), 4.56 * rem, 0.12, boxstyle="round,pad=0,rounding_size=0.05",
                                    color=MURK, alpha=0.95 * A, lw=0, zorder=16))
    txt(ax, PX + 4.6, 3.05, "washing out" if rem > 0.02 else "clear · the chest empties like the void", 9.5, GOLD_L if rem <= 0.02 else MUTED,
        A, ha="right")
    cue(ax, br, A)

WALL_T = dict(form=(4, 18), tense=(18, 34), collapse=(34, 37.5), bright=(36.5, 42), fire=(50, 58))
def sc_wall(ax, u, d):
    A = fade(u, d, 1.0, 0.8)
    dd = profile(ax, ox=2.3, oy=0.45, s=1.0, a=A)
    c, mm, low = dd["center"], dd["mingmen"], dd["lower"]
    w = ease((u - 4) / 14); ten = ease((u - 18) / 16); col = ease((u - 34) / 3.5)
    bri = ease((u - 36.5) / 5.5); fire = ease((u - 50) / 8)
    pre = 1 - col
    # Mingmen
    glow(ax, mm[0], mm[1], 0.3, CINN_L, A * pre, z=10, n=6)
    ax.add_patch(Circle(mm, 0.06, color=CINN_L, alpha=A * (0.25 + 0.75 * pre), zorder=11))
    txt(ax, mm[0] + 0.35, mm[1] - 0.15, "Mingmen 명문 命門\narousal · sympathetic", 10.5, CINN_L, A * ease((u - 3) / 1.5) * pre)
    # red stream Mingmen → chest center
    path = catmull([mm, mm + (-0.15, 0.7), c + (0.6, -0.3), c + (0.12, 0)], n=16, closed=False)
    sa = A * ease((u - 3) / 2) * pre
    faint_path(ax, path, CINN_L, 0.35 * sa, lw=1.2)
    for i in range(6):
        f = ((u * 0.35 + i / 6) % 1.0)
        pt = poly_at(path, f)
        glow(ax, pt[0], pt[1], 0.16, CINN_L, sa * (0.5 + 0.5 * ten) * np.sin(np.pi * f), z=12, n=5)
    # blue ripples converging from the front (rib purification + Om relaxation)
    for i in range(4):
        r = 1.15 - ((u * 0.3 + i / 4) % 1.0) * 0.95
        th = np.linspace(np.pi * 0.62, np.pi * 1.38, 40)
        ax.plot(c[0] - 0.1 + r * np.cos(th), c[1] + r * np.sin(th), color=WATER_L, lw=1.8,
                alpha=clamp(sa * 0.8 * (1 - abs(r - 0.6) / 0.6)), zorder=12)
    txt(ax, 0.3, c[1] + 1.25, "rib purification + 'Om'\nrelaxation · parasympathetic", 10.5, WATER_L, sa)
    # the iron wall
    if w > 0.01 and col < 0.999:
        jit = 0.025 * ten * np.sin(u * 47) * pre
        h = 0.7 * w
        for lw, al in [(18, 0.08), (8, 0.22), (3.2, 1.0)]:
            ax.plot([c[0] + jit, c[0] + jit], [c[1] - h, c[1] + h], color=GOLD_L, lw=lw, alpha=A * al * w * (1 - col) * (0.7 + 0.3 * ten),
                    zorder=13, solid_capstyle="butt")
        glow(ax, c[0], c[1], 0.5 + 0.5 * ten, GOLD_L, A * 0.35 * ten * pre, z=12)
    # boundary still held: prefrontal + parietal
    for p in (dd["prefrontal"], dd["parietal"]):
        glow(ax, p[0], p[1], 0.26, GOLD_L, A * 0.8 * w * pre, z=12, n=6)
        ax.add_patch(Circle(p, 0.05, color=GOLD_L, alpha=A * w * pre, zorder=13))
        if col > 0.3:
            ax.add_patch(Circle(p, 0.06, fill=False, ec=MUTED, lw=1, ls=":", alpha=A * col * (1 - fire), zorder=13))
    txt(ax, dd["parietal"][0] + 0.4, dd["parietal"][1] - 0.35, "prefrontal + parietal still\nhold a subtle boundary",
        10, GOLD_L, A * w * pre)
    # collapse: fragments fly apart
    if 0.0 < col < 1.0:
        rs = np.random.RandomState(5)
        for i in range(16):
            y0 = c[1] + rs.uniform(-0.7, 0.7); ang = rs.uniform(0, 2 * np.pi); dist = rs.uniform(0.8, 2.0)
            x = c[0] + np.cos(ang) * dist * col; y = y0 + np.sin(ang) * dist * col
            sp = rs.uniform(0, np.pi)
            ax.plot([x - 0.1 * np.cos(sp), x + 0.1 * np.cos(sp)], [y - 0.1 * np.sin(sp), y + 0.1 * np.sin(sp)],
                    color=GOLD_L, lw=2.6, alpha=A * (1 - col), zorder=13)
        glow(ax, c[0], c[1], 2.2 * col, IVORY, A * np.sin(np.pi * col) * 0.8, z=12)
    # bright empty space
    if bri > 0.01:
        pul = 0.06 * np.sin(u * 1.4)
        glow(ax, c[0], c[1], (0.6 + 1.6 * bri) * (1 + pul), VIOLET, A * bri * (1 - 0.3 * fire), z=9)
        glow(ax, c[0], c[1], 0.55 + 0.3 * bri, IVORY, A * 0.8 * bri, z=10)
        rs = np.random.RandomState(9)
        th = rs.uniform(0, 2 * np.pi, 40); rr = rs.uniform(0.6, 2.0, 40)
        for i in range(40):
            tw = 0.5 + 0.5 * np.sin(u * 2 + i)
            ax.add_patch(Circle((c[0] + rr[i] * np.cos(th[i]) * bri, c[1] + rr[i] * np.sin(th[i]) * bri), 0.025,
                                color=GOLD_L, alpha=A * bri * tw * 0.8, zorder=11))
    # heart-fire sinks by itself to the lower dantian / Yellow Court
    if fire > 0.0:
        fpath = catmull([c + (0, -0.2), c + (0.1, -0.9), low + (0.05, 0.3), low], n=16, closed=False)
        faint_path(ax, fpath, GOLD_L, 0.45 * A * min(1, fire * 3), lw=1.2)
        pt = poly_at(fpath, fire)
        glow(ax, pt[0], pt[1], 0.32, lerp_color(GOLD_L, CINN_L, fire), A * (1 - ease((fire - 0.9) / 0.1) * 0.6), z=13, n=7)
        glow(ax, low[0], low[1], 0.5 * ease((u - 56) / 3), CINN_L, A, z=12)
        ax.add_patch(Circle(low, 0.06, color=CINN_L, alpha=A * ease((u - 56) / 2), zorder=13))
        txt(ax, low[0] - 0.45, low[1] - 0.05, "lower dantian 下丹田\nYellow Court 黃庭", 10.5, CINN_L, A * ease((u - 56) / 2), ha="right")
    # right panel, three stages
    a3 = A * ease((u - 0.5) / 1.5) * (1 - ease((u - 35) / 1.5))
    title(ax, "三禪定 · 철벽", "3rd dhyāna: the iron wall", a3, "from the 2026-11-21 post")
    lines_block(ax, 6.3, [("Mingmen's strong arousal and the", IVORY), ("relaxation of the ribs and 'Om' face off", IVORY),
                          ("tautly in the center of the chest:", IVORY), ("both systems on at once, held dense.", IVORY)],
                A * ease((u - 6) / 1.5) * (1 - ease((u - 35) / 1.5)), size=11)
    lines_block(ax, 4.6, [("It feels like a solid wall.", GOLD_L), ("No emotion moves you;", GOLD_L),
                          ("emotion feels as if cut off.", GOLD_L)], A * ease((u - 20) / 1.5) * (1 - ease((u - 35) / 1.5)), size=11.5)
    a4 = A * ease((u - 37) / 1.5) * (1 - ease((u - 49.5) / 1.5))
    title(ax, "四禪定 · 텅 빔", "4th dhyāna: the wall collapses", a4, "past the critical point, the frame lets go (무위 無爲)")
    lines_block(ax, 6.3, ["Empty spaciousness (no-mind 무심)", "and clear wakefulness coexist", "without conflict:",
                          ("the bright nature  밝은 성품", VIOLET)], a4, size=11.5)
    lines_block(ax, 4.65, [("Heart and lungs in deep harmony: the heart", WATER_L), ("releases ANP; cortisol and amygdala", WATER_L),
                           ("anxiety drop; the oxytocin pathway opens.", WATER_L), "A quiet, clear joy  선열 禪悅."],
                A * ease((u - 41) / 1.5) * (1 - ease((u - 49.5) / 1.5)), size=10.5, dy=0.33)
    a5 = A * ease((u - 50.5) / 1.5)
    title(ax, "心火 → 黃庭", "Heart-fire sinks by itself", a5, "from the 2026-11-18 post")
    lines_block(ax, 6.3, ["The ground of the chest is empty like", "the void, and a warm heart-fire arises.",
                          "Without being pushed, it flows down,", "like gravity, to the lower dantian,",
                          ("the Yellow Court 黃庭.", CINN_L)], a5, size=11.5)
    txt(ax, PX, 1.6, "keep breathing naturally" if u < 50 else "rest here", 11, MUTED, A * ease((u - 2) / 1.5), style="italic")

def sc_close(ax, u, d):
    A = fade(u, d, 1.0, 1.5)
    dd = profile(ax, ox=0.9, oy=0.5, s=0.9, a=A * 0.55)
    glow(ax, *dd["lower"], 0.45, CINN_L, A * 0.8, z=10)
    glow(ax, *dd["center"], 0.4, GOLD_L, A * 0.5, z=10)
    txt(ax, 9.6, 6.5, "不動心", 44, GOLD, A * ease(u / 1.5), ha="center", weight="bold")
    txt(ax, 9.6, 5.65, "the unmoving mind", 17, IVORY, A * ease((u - 0.8) / 1.5), ha="center")
    lines = ["Don't press emotion down.", "Spread it across the ribs, scatter it to Lingtai,",
             "draw it back to the center with 'Om'.", "When the chest is empty, the warmth sinks on its own."]
    for i, s in enumerate(lines):
        txt(ax, 9.6, 4.65 - i * 0.45, s, 13, GOLD_L if i == 3 else IVORY, A * ease((u - 2 - i * 1.2) / 1.3), ha="center")
    txt(ax, 9.6, 2.0, "after 마리지천摩利支天 @z9_s8_y_9 · posts of 2026-11-18 and 2026-11-21 KST", 10, MUTED,
        A * ease((u - 7) / 1.5), ha="center")
    txt(ax, 9.6, 1.6, "li-gong · drawn and voiced in Python", 9.5, MUTED, A * ease((u - 7.5) / 1.5), ha="center")

SCENES = {"intro": sc_intro, "setup": sc_setup, "breathe": sc_breathe, "wall": sc_wall, "close": sc_close}

# ---------------------------------------------------------------- render
_FIG = _AX = _BGIMG = None
def _init():
    global _FIG, _AX, _BGIMG
    _FIG = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    _AX = _FIG.add_axes([0, 0, 1, 1])
    yy = np.linspace(0, 1, 72)[:, None]; xx = np.linspace(0, 1, 128)[None, :]
    g = BG_BOT + (BG_TOP - BG_BOT) * yy[..., None]
    vig = 1 - 0.55 * (((xx - 0.5) * 1.2) ** 2 + ((yy - 0.55) * 1.4) ** 2)
    _BGIMG = np.clip(g * vig[..., None], 0, 1)

def draw(t):
    ax = _AX
    ax.cla(); ax.set_xlim(0, 16); ax.set_ylim(0, 9); ax.axis("off")
    ax.imshow(_BGIMG, extent=(0, 16, 0, 9), origin="lower", interpolation="bicubic", zorder=0, aspect="auto")
    name, u, d = seg_at(t)
    SCENES[name](ax, u, d)
    rem = max(0.0, TOTAL - t)
    txt(ax, 15.6, 8.72, f"session {int(t // 60):02d}:{int(t % 60):02d}  ·  {int(rem // 60):02d}:{int(rem % 60):02d} left",
        10, MUTED, 0.85, ha="right", z=32, family="DejaVu Sans")
    x0, x1 = 0.35, 15.65
    sx = lambda tt: x0 + (x1 - x0) * tt / TOTAL
    for n_, d_ in SEGMENTS:
        a0 = STARTS[n_][0]; on = n_ == name
        ax.plot([sx(a0) + 0.03, sx(a0 + d_) - 0.03], [0.22, 0.22], color=GOLD_L if on else GOLD, lw=3.0 if on else 1.5,
                alpha=0.9 if on else 0.3, zorder=31, solid_capstyle="butt")
        if d_ > 20:
            txt(ax, (sx(a0) + sx(a0 + d_)) / 2, 0.42, LABELS[n_], 9 if on else 8, GOLD_L if on else MUTED,
                1.0 if on else 0.55, ha="center", z=32)
    ax.add_patch(Circle((sx(t), 0.22), 0.05, color=IVORY, alpha=0.9, lw=0, zorder=33))

def render(i):
    draw(i / FPS)
    _FIG.canvas.draw()
    return bytes(np.asarray(_FIG.canvas.buffer_rgba())[..., :3].tobytes())

# ---------------------------------------------------------------- audio
def make_audio(path, sr=32000):
    """Inhale: soft rising tone + breath swell. Exhale: low 'Om'-like hum (vowel o → closed m).
    A gentle bell at each breath's start, a gong at each section, beating tension under the wall,
    a struck bell at the collapse, a soft pad for the bright space, a descending warm tone for heart-fire."""
    n = int(TOTAL * sr); t = np.arange(n) / sr
    out = np.zeros(n)
    drone = (0.5 * np.sin(2 * np.pi * 87.3 * t) + 0.3 * np.sin(2 * np.pi * 130.8 * t + 0.3)) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.05 * t))
    out += 0.03 * drone
    rng = np.random.default_rng(1)
    L = 20 * sr
    nz = rng.standard_normal(L); F = np.fft.rfft(nz); fr = np.fft.rfftfreq(L, 1 / sr)
    F *= np.exp(-((fr - 500) / 320) ** 2); nz = np.fft.irfft(F, L); nz /= np.abs(nz).max()

    def add_bell(tc, f0, amp, dur, dec):
        i0 = int(tc * sr); L_ = min(int(sr * dur), n - i0)
        if L_ <= 0 or i0 < 0: return
        tt = np.arange(L_) / sr
        sig = (np.sin(2 * np.pi * f0 * tt) + 0.35 * np.sin(2 * np.pi * f0 * 2.76 * tt) * np.exp(-tt * 3)
               + 0.15 * np.sin(2 * np.pi * f0 * 5.4 * tt) * np.exp(-tt * 6)) * np.exp(-tt * dec) * np.clip(tt / 0.004, 0, 1)
        out[i0:i0 + L_] += amp * sig

    def add_gong(tc, f0=110, amp=0.12, dur=8):
        i0 = int(tc * sr); L_ = min(int(sr * dur), n - i0); tt = np.arange(L_) / sr
        g = (np.sin(2 * np.pi * f0 * tt) + 0.6 * np.sin(2 * np.pi * f0 * 2.02 * tt + 0.5) * np.exp(-tt * 0.8)
             + 0.35 * np.sin(2 * np.pi * f0 * 2.93 * tt) * np.exp(-tt * 1.4) + 0.2 * np.sin(2 * np.pi * f0 * 4.1 * tt) * np.exp(-tt * 2.0))
        g *= np.exp(-tt * 0.55) * np.clip(tt / 0.01, 0, 1) * (1 + 0.08 * np.sin(2 * np.pi * 3.5 * tt))
        out[i0:i0 + L_] += amp * g

    # breathing section
    b0 = STARTS["breathe"][0] + LEAD
    f0 = 98.0                                        # Om fundamental
    harm = np.arange(1, 25)
    for k in range(NCYC):
        ts = b0 + k * PERIOD
        add_bell(ts, 1046.5 if k < NCYC - 1 else 784.0, 0.05, 3.0, 1.8)
        # inhale tone: soft, rising a fourth
        i0 = int(ts * sr); Li = int(INH * sr); tt = np.arange(Li) / sr; p = tt / INH
        env = np.sin(np.pi * np.clip(p, 0, 1)) ** 1.2
        fr_ = 220 * 2 ** (5 / 12 * (0.5 - 0.5 * np.cos(np.pi * p)))
        ph = 2 * np.pi * np.cumsum(fr_) / sr
        tone = (np.sin(ph) + 0.25 * np.sin(2 * ph)) * env
        sw = nz[(np.arange(Li) + k * 3131) % L] * env
        out[i0:i0 + Li] += 0.07 * tone + 0.08 * sw
        # exhale Om: harmonic stack through a formant filter morphing 'o' → 'm'
        e0 = int((ts + INH) * sr); Le = int(EXH * sr); tt = np.arange(Le) / sr; p = tt / EXH
        env = np.clip(tt / 0.6, 0, 1) * np.clip((EXH - tt) / 1.0, 0, 1)
        m = np.clip((p - 0.35) / 0.25, 0, 1)            # 0 = 'o', 1 = 'm'
        vib = 1 + 0.004 * np.sin(2 * np.pi * 5 * tt)
        ph = 2 * np.pi * f0 * np.cumsum(vib) / sr
        sig = np.zeros(Le)
        for h in harm:
            fh = f0 * h
            w_o = np.exp(-((fh - 450) / 140) ** 2) + 0.6 * np.exp(-((fh - 800) / 180) ** 2) + 0.5 * np.exp(-((fh - 120) / 80) ** 2)
            w_m = np.exp(-((fh - 250) / 130) ** 2) + 0.9 * np.exp(-((fh - 100) / 60) ** 2)
            wgt = (1 - m) * w_o + m * w_m
            sig += wgt * np.sin(h * ph) / h ** 0.3
        sig /= 3.0
        out[e0:e0 + Le] += 0.16 * sig * env
    # section gongs
    for nm in ("setup", "breathe", "wall", "close"):
        add_gong(STARTS[nm][0], amp=0.10)
    # wall: beating tension, collapse bell, bright pad, descending heart-fire
    w0 = STARTS["wall"][0]
    def env_in(a, b, c_, d_):
        return np.clip((t - (w0 + a)) / (b - a), 0, 1) * np.clip(((w0 + d_) - t) / (d_ - c_), 0, 1)
    ten = env_in(4, 32, 34, 35)
    out += 0.05 * ten * (np.sin(2 * np.pi * 146.8 * t) + np.sin(2 * np.pi * (146.8 + 1.5 + 3 * ten) * t)) * (0.4 + 0.6 * ten)
    add_gong(w0 + 34.5, f0=82.4, amp=0.16, dur=10); add_bell(w0 + 34.6, 659.3, 0.07, 5.0, 0.9); add_bell(w0 + 34.85, 987.8, 0.05, 5.0, 1.0)
    pad = env_in(36.5, 41, 48, 54)
    out += 0.035 * pad * sum(np.sin(2 * np.pi * f * t + i) for i, f in enumerate([220, 277.2, 329.6, 440]))
    fe = env_in(50, 51, 59, 63)
    fr_ = 330 * 2 ** (-12 / 12 * np.clip((t - (w0 + 50)) / 8, 0, 1))
    ph = 2 * np.pi * np.cumsum(fr_) / sr
    out += 0.06 * fe * (np.sin(ph) + 0.3 * np.sin(2 * ph))
    add_bell(w0 + 58, 523.3, 0.06, 5.0, 1.0)
    add_bell(STARTS["close"][0] + 14, 784.0, 0.05, 4.0, 1.2)
    fadeL = int(2 * sr); out[:fadeL] *= np.linspace(0, 1, fadeL); out[-fadeL:] *= np.linspace(1, 0, fadeL)
    out = out / max(1e-9, np.abs(out).max()) * 0.7
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())

def main():
    args = sys.argv[1:]
    out = os.path.join(HERE, "rib_purification.mp4")
    if "--still" in args:
        ts = [float(x) for x in args[args.index("--still") + 1].split(",")]
        _init()
        sd = os.environ.get("STILLDIR", os.path.join(HERE, "stills"))
        os.makedirs(sd, exist_ok=True)
        for tt in ts:
            draw(tt); p = os.path.join(sd, f"t{tt:06.1f}.png"); _FIG.savefig(p, dpi=100); print(p)
        return
    if args: out = args[0]
    wav = "/tmp/_rib_audio.wav"
    make_audio(wav)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "28",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    workers = int(os.environ.get("WORKERS", "7"))
    with mp.Pool(workers, initializer=_init) as pool:
        for i, buf in enumerate(pool.imap(render, range(NFRAMES), chunksize=6)):
            ff.stdin.write(buf)
            if i % 900 == 0:
                print(f"frame {i}/{NFRAMES}", flush=True)
    ff.stdin.close(); ff.wait()
    print("done", out, TOTAL, "s")

if __name__ == "__main__":
    main()
