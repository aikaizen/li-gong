#!/usr/bin/env python3
"""Li Gong · Opening the Top — REAL-TIME follow-along session of the five gates.
Every breath at true pace: 4 s inhale / 6 s exhale. No acceleration.
Pure Python: matplotlib (Agg) draws each frame, ffmpeg encodes H.264.
A soft drone + breath swell + count chimes is synthesised with numpy.
Usage: python3 five_gates_realtime.py [out.mp4] [--still t1,t2,...]
"""
import os, sys, wave, subprocess, multiprocessing as mp
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Circle, Ellipse, Polygon, FancyBboxPatch
from matplotlib.path import Path
from matplotlib.patches import PathPatch

W, H, FPS = 1280, 720, 30
for f in ["/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
          "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"]:
    if os.path.exists(f):
        fm.fontManager.addfont(f)
plt.rcParams["font.family"] = ["Noto Serif CJK TC", "DejaVu Sans", "Noto Sans Symbols"]
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

# ---------------------------------------------------------------- palette
BG_TOP, BG_BOT = np.array([14, 18, 48]) / 255, np.array([4, 5, 14]) / 255
BODY = "#141a3d"
GOLD, GOLD_L = "#d4af37", "#f3d98b"
CINN, CINN_L = "#c8372d", "#ff7a4d"
WATER, WATER_L = "#3f8fd6", "#8fd0ff"
IVORY, MUTED = "#efe6d2", "#8d8aa6"

# ---------------------------------------------------------------- timeline
INH, EXH = 4.0, 6.0          # calm breath: 4 s in, 6 s out
PERIOD = INH + EXH
SEGMENTS = [("intro", 11), ("posture", 9),
            ("g1card", 6), ("g1", 367),
            ("g2card", 6), ("g2", 100),
            ("g3card", 6), ("g3", 96),
            ("g4card", 6), ("g4", 192),
            ("g5card", 6), ("g5", 42),
            ("closecard", 6), ("close", 100),
            ("warn", 14), ("end", 6)]
STARTS, acc = {}, 0.0
for n, d in SEGMENTS:
    STARTS[n] = (acc, d); acc += d
TOTAL = acc
NFRAMES = int(round(TOTAL * FPS))

# breath schedules: start (s into segment), number of breaths / rounds
SCHED = {"g1": (3.0, 36), "g2": (6.0, 9), "g3": (2.0, 9), "g5": (6.0, 3), "close": (2.0, 9)}
GATE_OF = {"g1card": 1, "g1": 1, "g2card": 2, "g2": 2, "g3card": 3, "g3": 3, "g4card": 4, "g4": 4,
           "g5card": 5, "g5": 5, "closecard": 6, "close": 6}

def seg_at(t):
    for n, d in SEGMENTS:
        s, _ = STARTS[n]
        if t < s + d:
            return n, t - s, d
    n, d = SEGMENTS[-1]
    return n, d - 1e-3, d

def breath(name, u):
    """Real-pace breath. ph in [0,0.5) = inhale (4 s), [0.5,1) = exhale (6 s).
    -> dict(n, done, ph, b, active, total, rem = seconds left in the current phase)"""
    st, n = SCHED[name]
    e = u - st
    out = dict(n=0, done=0, ph=0.0, b=0.0, fast=False, active=False, total=n, rem=0.0)
    if e < 0:
        out["rem"] = -e
        return out
    k, w = int(e // PERIOD), e % PERIOD
    if k >= n:
        out.update(n=n, done=n, ph=1.0)
        return out
    if w < INH:
        ph, rem = 0.5 * w / INH, INH - w
    else:
        ph, rem = 0.5 + 0.5 * (w - INH) / EXH, PERIOD - w
    b = 0.5 - 0.5 * np.cos(2 * np.pi * ph)
    out.update(n=k + 1, done=k, ph=ph, b=b, active=True, rem=rem)
    return out

# ---------------------------------------------------------------- helpers
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def lerp(a, b, t): return a + (b - a) * t
def fade(u, d, fi=0.6, fo=0.5): return ease(u / fi) * ease((d - u) / fo)

def glow(ax, x, y, r, color, a=1.0, z=5, n=10):
    for i in range(n):
        k = 1 - i / n
        ax.add_patch(Circle((x, y), r * k, color=color, alpha=clamp(a * 0.11), lw=0, zorder=z))

def txt(ax, x, y, s, size=14, color=IVORY, a=1.0, ha="left", va="center", weight="normal", z=20, **kw):
    if a <= 0.01: return
    ax.text(x, y, s, fontsize=size, color=color, alpha=clamp(a), ha=ha, va=va,
            fontweight=weight, zorder=z, **kw)

def trigram(ax, x, y, lines, w=0.9, lh=0.11, gap=0.2, color=GOLD, a=1.0, z=12, skip_mid=False, mid_offset=(0, 0)):
    """lines top->bottom, 1 = solid (yang), 0 = broken (yin)."""
    for i, L in enumerate(lines):
        yy = y + gap * (1 - i)
        dx, dy = (mid_offset if i == 1 else (0, 0))
        if i == 1 and skip_mid: continue
        if L:
            segs = [(x - w / 2 + dx, w)]
        else:
            g = w * 0.22
            segs = [(x - w / 2 + dx, (w - g) / 2), (x + g / 2 + dx, (w - g) / 2)]
        for sx, sw in segs:
            ax.add_patch(FancyBboxPatch((sx, yy + dy - lh / 2), sw, lh, boxstyle="round,pad=0,rounding_size=0.03",
                                        color=color, alpha=clamp(a), lw=0, zorder=z))

def catmull(pts, n=12):
    P = np.array(pts); m = len(P); out = []
    for i in range(m):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % m], P[(i + 2) % m]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.array(out)

# ---------------------------------------------------------------- body
CX = 4.3
Y = dict(crown=7.5, brow=6.85, heart=4.75, p5=4.05, navel=3.45, lower=2.95, perineum=2.0, sole=1.75)
_hw = [(2.0, 1.25), (2.7, 1.12), (3.3, 1.02), (4.0, 1.12), (4.6, 1.28), (5.15, 1.42)]
TORSO = catmull([(CX + w, y) for y, w in _hw] + [(CX + 1.1, 5.55), (CX + 0.32, 5.8), (CX + 0.3, 6.15),
                 (CX - 0.3, 6.15), (CX - 0.32, 5.8), (CX - 1.1, 5.55)] + [(CX - w, y) for y, w in reversed(_hw)])

def body(ax, a=1.0, chest=0.0):
    """Seated meditator silhouette. chest: 0..1 breath expansion of the ribcage."""
    if a <= 0.01: return
    a = 1.0
    s = 1 + 0.035 * chest
    torso = TORSO.copy()
    m = (torso[:, 1] > 3.6) & (torso[:, 1] < 5.6)
    torso[m, 0] = CX + (torso[m, 0] - CX) * s
    arms = [[(CX - 1.25 * s, 5.15), (CX - 1.42, 3.5), (CX - 1.9, 2.25)],
            [(CX + 1.25 * s, 5.15), (CX + 1.42, 3.5), (CX + 1.9, 2.25)]]
    shapes = [("ell", (CX, 1.6), 5.2, 1.25), ("ell", (CX, 6.78), 1.1, 1.36)]
    # outline + glow pass
    for lw, al in [(9, 0.05), (5, 0.10), (2.2, 0.85)]:
        aa = a * al
        ax.add_patch(Polygon(torso, closed=True, fill=False, ec=GOLD, lw=lw, alpha=aa, zorder=3))
        for _, c, w, h in shapes:
            ax.add_patch(Ellipse(c, w, h, fill=False, ec=GOLD, lw=lw, alpha=aa, zorder=3))
        for arm in arms:
            xs, ys = zip(*arm)
            ax.plot(xs, ys, color=GOLD, lw=34 + lw, alpha=aa, solid_capstyle="round", solid_joinstyle="round", zorder=3)
    # fill pass (hides inner outlines)
    for arm in arms:
        xs, ys = zip(*arm)
        ax.plot(xs, ys, color=BODY, lw=34, alpha=a, solid_capstyle="round", solid_joinstyle="round", zorder=4)
    for _, c, w, h in shapes:
        ax.add_patch(Ellipse(c, w, h, color=BODY, alpha=a, lw=0, zorder=4))
    ax.add_patch(Polygon(torso, closed=True, color=BODY, alpha=a, lw=0, zorder=4))
    # central channel
    ax.plot([CX, CX], [Y["perineum"], Y["crown"] - 0.1], color=GOLD, lw=0.8, alpha=0.18 * a, zorder=5, ls=(0, (2, 4)))
    # lowered eyes
    for dx in (-0.22, 0.22):
        ax.plot([CX + dx - 0.12, CX + dx + 0.12], [6.78, 6.76], color=GOLD, lw=1.1, alpha=0.5 * a, zorder=6)

def dantian_points(ax, a=1.0, which=("brow", "heart", "lower")):
    for k in which:
        glow(ax, CX, Y[k], 0.28, GOLD_L, a * 0.7, z=6, n=6)
        ax.add_patch(Circle((CX, Y[k]), 0.055, color=GOLD_L, alpha=a, zorder=7))

# ---------------------------------------------------------------- hand
FING = {"index": (-0.72, 1.45), "middle": (-0.24, 1.7), "ring": (0.24, 1.52), "little": (0.72, 1.15)}

def _rot(p, hx, hy):
    p = np.asarray(p, float)
    return np.array([hx + (p[1] - hy), hy - (p[0] - hx)])

def hand(ax, hx, hy, s, curl, a=1.0, mid_glow=0.0):
    """Palm-up hand schematic. curl: dict finger->0 (spread/extended) .. 1 (together, tip to thumb)."""
    if a <= 0.01: return
    fold = max(curl.get("index", 0), curl.get("middle", 0), curl.get("ring", 0))
    th_base = np.array([hx - 0.95 * s, hy - 0.55 * s])
    th_tip = np.array([lerp(hx - 1.55 * s, hx - 0.45 * s, fold), lerp(hy + 0.25 * s, hy + 0.15 * s, fold)])
    meet = th_tip + np.array([0.18 * s, 0.12 * s])
    lw = 30 * s
    strokes = []
    for name, (dx, L) in FING.items():
        c = curl.get(name, 0.0)
        base = np.array([hx + dx * s, hy + 0.45 * s])
        ext = base + np.array([dx * 0.12 * s, L * s])
        tip = (1 - c) * ext + c * (meet + np.array([0.04 * s * (dx / 0.24), 0]))
        ctrl = (1 - c) * (base + (ext - base) * 0.5) + c * (base + np.array([dx * 0.1 * s, 0.95 * s]))
        strokes.append((name, base, ctrl, tip, c))
    th_ctrl = (th_base + th_tip) / 2 + np.array([-0.15 * s, 0.05 * s])
    allp = [("thumb", th_base, th_ctrl, th_tip, fold)] + strokes
    allp = [(n_, _rot(b_, hx, hy), _rot(c_, hx, hy), _rot(t_, hx, hy), k_) for n_, b_, c_, t_, k_ in allp]
    strokes = allp[1:]
    # draw extended fingers first, folded later (they lie across the palm)
    order = sorted(allp, key=lambda q: q[4])
    ax.add_patch(FancyBboxPatch((hx - 1.05 * s, hy - 1.0 * s), 1.55 * s, 2.0 * s,
                                boxstyle=f"round,pad=0,rounding_size={0.5 * s}", fc=BODY, ec=GOLD, lw=2.2,
                                alpha=a, zorder=8))
    for name, b0, c0, t0, c in order:
        path = Path([b0, c0, t0], [Path.MOVETO, Path.CURVE3, Path.CURVE3])
        z = 9 + c
        ax.add_patch(PathPatch(path, fill=False, ec=GOLD, lw=lw + 4, alpha=a, capstyle="round", zorder=z))
        ax.add_patch(PathPatch(path, fill=False, ec=BODY, lw=lw, alpha=a, capstyle="round", zorder=z + 0.01))
        if name == "middle" and mid_glow > 0:
            ax.add_patch(PathPatch(path, fill=False, ec=GOLD_L, lw=lw * 0.25, alpha=a * mid_glow * 0.6,
                                   capstyle="round", zorder=z + 0.02))
    # contact sparks where fingertips meet the thumb
    for name, b0, c0, t0, c in strokes:
        if name != "little" and c > 0.85:
            glow(ax, t0[0], t0[1], 0.22 * s, GOLD_L, a * (c - 0.85) / 0.15, z=11, n=5)
    return None

def seal_legend(ax, x, y, lines, a=1.0, color=GOLD, labels=None):
    """trigram + finger labels; lines top->bottom = index, middle, ring."""
    trigram(ax, x, y, lines, w=0.8, lh=0.12, gap=0.55, color=color, a=a, z=12)
    names = labels or ["index finger", "middle finger", "ring finger"]
    for i, L in enumerate(lines):
        yy = y + 0.55 * (1 - i)
        state = "together · solid" if L else "spread · empty"
        txt(ax, x + 0.6, yy + 0.1, names[i], 12, IVORY, a)
        txt(ax, x + 0.6, yy - 0.15, state, 10.5, GOLD_L if L else WATER_L, a * 0.9)

# ---------------------------------------------------------------- panels
PX = 8.7
def title(ax, zh, en, a, sub=None):
    txt(ax, PX, 8.05, zh, 30, GOLD, a, weight="bold")
    txt(ax, PX, 7.4, en, 16.5, IVORY, a)
    if sub: txt(ax, PX, 6.95, sub, 11.5, MUTED, a)

def lines_block(ax, y0, lines, a, size=12.5, color=IVORY, dy=0.4, x=PX):
    for i, s in enumerate(lines):
        txt(ax, x, y0 - i * dy, s, size, color, a)

def cue_box(ax, a, big, bigcol, sub="", count=None, beads=None, ring_b=None, ring_col=WATER_L, secs=None):
    """Follow-along cue block along the bottom of the right panel."""
    txt(ax, PX, 1.95, big, 40, bigcol, a, weight="bold", family="DejaVu Serif")
    if secs is not None and secs > 0.05:
        txt(ax, PX + 4.25, 1.93, f"{int(np.ceil(secs - 1e-6))}", 22, MUTED, a, family="DejaVu Serif")
    if count: txt(ax, PX, 1.2, count, 15, IVORY, a)
    if beads:
        done, tot, curb = beads
        per = 18
        for i in range(tot):
            bx = PX + 2.95 + (i % per) * 0.15
            by = 1.3 - (i // per) * 0.19
            on, cur = i < done, i == done
            ax.add_patch(Circle((bx, by), 0.045, color=GOLD_L if (on or cur) else MUTED,
                                alpha=a * (1.0 if on else (0.35 + 0.65 * curb) if cur else 0.3), lw=0, zorder=20))
    if sub: txt(ax, PX, 0.72, sub, 10.5, MUTED, a)
    if ring_b is not None:
        x, y = 14.95, 1.5
        r = 0.1 + 0.52 * ring_b
        ax.add_patch(Circle((x, y), 0.62, fill=False, ec=MUTED, lw=0.9, alpha=0.45 * a, zorder=15))
        ax.add_patch(Circle((x, y), r, fc=ring_col, alpha=0.22 * a, lw=0, zorder=15))
        ax.add_patch(Circle((x, y), r, fill=False, ec=ring_col, lw=1.8, alpha=0.9 * a, zorder=15))

def counter(ax, br, label, a, unit="breath", ring_col=WATER_L):
    U = unit.capitalize()
    if br["active"]:
        inh = br["ph"] < 0.5
        big, col = ("INHALE", WATER_L) if inh else ("EXHALE", GOLD_L)
        cnt, secs = f"{U} {br['n']} / {br['total']}", br["rem"]
    elif br["done"] == br["total"]:
        big, col, cnt, secs = "REST", IVORY, f"{U}s complete · {br['total']} / {br['total']}", None
    else:
        big, col, cnt, secs = "READY", MUTED, f"{U} 1 of {br['total']} in", br["rem"]
    cue_box(ax, a, big, col, label, cnt, (br["done"], br["total"], br["b"]), br["b"], ring_col, secs)

# ---------------------------------------------------------------- scenes
def sc_intro(ax, u, d):
    A = fade(u, d, 0.8, 0.8)
    # slow rotating faint bagua ring
    ang = u * 0.06
    for k in range(8):
        th = ang + k * np.pi / 4
        x, y = 8 + 3.6 * np.cos(th), 4.5 + 3.6 * np.sin(th)
        ax.add_patch(Circle((x, y), 0.04, color=GOLD, alpha=0.25 * A, zorder=2))
    ax.add_patch(Circle((8, 4.5), 3.6, fill=False, ec=GOLD, lw=0.6, alpha=0.15 * A, zorder=2))
    ax.add_patch(Circle((8, 4.5), 3.3, fill=False, ec=GOLD, lw=0.4, alpha=0.08 * A, zorder=2))
    a1, a2 = ease((u - 0.5) / 1.5) * A, ease((u - 1.2) / 1.5) * A
    lx, kx = lerp(3.0, 3.6, ease(u / 2)), lerp(13.0, 12.4, ease(u / 2))
    # Li (fire) left, Kan (water) right
    glow(ax, lx, 4.7, 1.2, CINN, a1 * 0.5, z=3)
    glow(ax, kx, 4.7, 1.2, WATER, a2 * 0.5, z=3)
    trigram(ax, lx, 4.7, [1, 0, 1], w=1.4, lh=0.17, gap=0.38, color=CINN_L, a=a1)
    # Kan's middle (yang) line travels into Li's empty middle at the end
    mv = ease((u - 6.5) / 2.6)
    trigram(ax, kx, 4.7, [0, 1, 0], w=1.4, lh=0.17, gap=0.38, color=WATER_L, a=a2, skip_mid=True)
    mx, my = lerp(kx, lx, mv), 4.7 + 1.6 * np.sin(np.pi * mv)
    col = WATER_L if mv < 0.5 else GOLD_L
    glow(ax, mx, my, 0.5 + 0.4 * np.sin(np.pi * mv), col, a2 * (0.3 + 0.7 * np.sin(np.pi * mv)), z=11)
    trigram(ax, mx, my - 0.0, [1], w=1.4, lh=0.17, gap=0.0, color=col, a=a2, z=13)
    if mv > 0.98:
        glow(ax, lx, 4.7, 1.3 * ease((u - 9.1) / 0.6), GOLD_L, A * 0.6, z=10)
    txt(ax, lx, 3.55, "離  Li · fire · heart · 9", 13, CINN_L, a1, ha="center")
    txt(ax, kx, 3.55, "坎  Kan · water · kidneys · 1", 13, WATER_L, a2, ha="center")
    at = ease((u - 2.0) / 1.5) * A
    txt(ax, 8, 5.25, "取坎填離", 54, GOLD, at, ha="center", weight="bold")
    txt(ax, 8, 4.05, "Taking from Kan to Fill Li", 20, IVORY, at, ha="center")
    txt(ax, 8, 3.45, "LI GONG  ·  OPENING THE TOP  ·  THE FIVE GATES", 12, MUTED, ease((u - 3.2) / 1.5) * A, ha="center")
    txt(ax, 8, 1.3, "Empty the fire first — then the water is drawn up, never pushed.", 13, GOLD_L,
        ease((u - 5.0) / 1.2) * A, ha="center", style="italic")

def sc_posture(ax, u, d):
    A = fade(u, d, 0.8, 0.5)
    body(ax, ease(u / 1.5) * A)
    title(ax, "端坐", "Seat and points", ease((u - 0.5)) * A)
    pts = [("crown", "頂  crown", 7.5), ("brow", "上丹田  upper field · between the brows", 6.85),
           ("heart", "中丹田  middle field · heart · Li ☲ 9", 4.75),
           ("p5", "黃庭  yellow court · palace 5 · the center", 4.05),
           ("lower", "下丹田  lower field · Kan ☵ 1", 2.95)]
    for i, (k, lab, yy) in enumerate(pts):
        a = ease((u - 1.2 - i * 0.45) / 0.7) * A
        if a <= 0: continue
        glow(ax, CX, Y[k], 0.3, GOLD_L if k != "lower" else WATER_L, a * 0.8, z=6, n=6)
        ax.add_patch(Circle((CX, Y[k]), 0.055, color=GOLD_L, alpha=a, zorder=7))
        ly = [6.3, 5.75, 4.75, 4.05, 2.95][i] if i < 2 else Y[k]
        ly = {0: 6.45, 1: 5.95}.get(i, ly)
        ax.plot([CX + 0.1, 6.7, 7.1], [Y[k], Y[k], ly], color=GOLD, lw=0.7, alpha=0.6 * a, zorder=7)
        txt(ax, 7.2, ly, lab, 12.5, IVORY, a)
    b = ease((u - 4.2) / 0.8) * A
    lines_block(ax, 1.75, ["Upright on a cushion or the front edge of a chair, feet flat.",
                           "Spine tall · tongue lightly on the palate · eyes lowered like a curtain (垂簾)."],
                b, size=11.5, color=MUTED, x=7.2)

CARDS = {"g1card": ("一", "GATE 1", "放胸", "Soften the chest", "36 breaths · 4 s in / 6 s out",
                     "Sit tall, tongue on the palate, eyes lowered. Breathe in for 4, out for 6."),
         "g2card": ("二", "GATE 2", "離印", "The Li seal · returning the light", "9 rounds",
                     "Palms up. Index and ring fingers to the thumb; middle finger long."),
         "g3card": ("三", "GATE 3", "心火下降", "Heart fire descends to the center", "9 breaths · never below the navel",
                     "Keep the Li seal. Picture a small ember at the heart."),
         "g4card": ("四", "GATE 4", "頂空", "Clear crown", "3-minute hold · pause the video to extend to 5",
                     "Tongue on the palate. Let attention rise lightly to the crown."),
         "g5card": ("五", "GATE 5", "取坎填離", "Join Kan to Li", "3 rounds · soft perineum lift",
                     "Close the middle finger, open index and ring. Keep the chest empty."),
         "closecard": ("收", "CLOSING", "收功", "Seal and ground", "9 breaths · then attention to the soles",
                     "Rub the palms warm, then rest them on the lower belly.")}

def sc_card(ax, name, u, d):
    A = fade(u, d, 0.5, 0.5)
    num, g, zh, en, tgt, prep = CARDS[name]
    txt(ax, 8, 4.9, num, 240, GOLD, 0.06 * A, ha="center", weight="bold")
    txt(ax, 8, 7.0, "NEXT  ·  " + g, 13, GOLD, A, ha="center", weight="bold")
    ax.plot([7.0, 9.0], [6.65, 6.65], color=GOLD, lw=0.8, alpha=0.6 * A)
    txt(ax, 8, 5.7, zh, 54, GOLD_L, A, ha="center", weight="bold")
    txt(ax, 8, 4.55, en, 22, IVORY, A, ha="center")
    txt(ax, 8, 3.95, tgt, 13.5, MUTED, A, ha="center")
    txt(ax, 8, 2.9, "Prepare:  " + prep, 14.5, WATER_L, ease((u - 0.4) / 0.6) * A, ha="center")
    cd = int(np.ceil(d - u - 1e-6))
    txt(ax, 8, 1.85, f"begins in {cd}", 16, GOLD_L, ease((u - 0.6) / 0.5) * A, ha="center", family="DejaVu Serif")

def sc_g1(ax, u, d):
    A = fade(u, d)
    br = breath("g1", u)
    soft = br["done"] / 36 if br["active"] else (1.0 if br["done"] == 36 else 0.0)
    body(ax, A, chest=br["b"])
    # chest: tension lines fade as the chest softens, cool hollow light grows
    glow(ax, CX, Y["heart"], 0.9 + 0.35 * br["b"], WATER_L, A * (0.25 + 0.5 * soft) * (0.6 + 0.4 * br["b"]), z=6)
    rng = np.random.default_rng(3)
    for i in range(7):
        yy = 4.35 + i * 0.13
        xs = np.linspace(CX - 0.8, CX + 0.8, 14)
        ys = yy + 0.05 * np.sign(np.sin(np.arange(14) * 2.2 + i)) * (1 - soft)
        ax.plot(xs, ys, color=CINN_L, lw=1.0, alpha=A * 0.55 * (1 - soft) ** 1.5, zorder=7)
    # sternum drops, shoulder blades widen (arrows on exhale)
    ex = clamp((br["ph"] - 0.5) * 2) if br["active"] else 0
    sd = 0.12 * np.sin(np.pi * ex)
    ax.annotate("", xy=(CX, 4.95 - sd - 0.25), xytext=(CX, 5.3 - sd), zorder=8,
                arrowprops=dict(arrowstyle="-|>", color=GOLD_L, lw=1.4, alpha=A * 0.8))
    for sgn in (-1, 1):
        x0 = CX + sgn * 0.55
        ax.annotate("", xy=(x0 + sgn * (0.35 + 0.25 * br["b"]), 5.05), xytext=(x0, 5.05), zorder=8,
                    arrowprops=dict(arrowstyle="-|>", color=GOLD, lw=1.1, alpha=A * 0.6))
    title(ax, "第一關 · 放胸", "Gate 1 — Soften the chest", A, "36 breaths")
    lines_block(ax, 6.25, ["Let the sternum drop. Let the space between", "the shoulder blades widen.",
                           "Listen to the breath until the ears cannot hear it.",
                           "A breath that makes sound is coarse (Golden Flower, ch. 4)."], A, size=12.5)
    sign_a = ease((u - 27.5) / 1.0) * A
    txt(ax, PX, 4.1, "Sign:", 12.5, GOLD, A * 0.9)
    txt(ax, PX + 0.8, 4.1, "the chest hollow and cool,", 12.5, IVORY, A * (0.35 + 0.65 * soft))
    txt(ax, PX + 0.8, 3.7, "like an empty room.", 12.5, IVORY, A * (0.35 + 0.65 * soft))
    txt(ax, PX, 3.1, "Do not continue while the chest is still tight.", 11, CINN_L, A * 0.85, style="italic")
    counter(ax, br, f"chest softened {int(round(soft * 100))}%", A)

def li_curl(): return {"index": 1, "middle": 0, "ring": 1, "little": 0.15}

def sc_g2(ax, u, d):
    A = fade(u, d)
    br = breath("g2", u)
    body(ax, A, chest=br["b"] * 0.5)
    form = ease((u - 1.0) / 3.5)
    curl = {k: v * form for k, v in li_curl().items()}
    # emptiness / suction at Li (heart)
    open_ = form * (0.55 + 0.45 * br["b"])
    r = 0.15 + 0.38 * open_
    glow(ax, CX, Y["heart"], r * 2.6, CINN, A * 0.45 * form, z=6)
    ax.add_patch(Circle((CX, Y["heart"]), r, color="#020208", alpha=A * form, zorder=8))
    ax.add_patch(Circle((CX, Y["heart"]), r, fill=False, ec=GOLD_L, lw=1.6, alpha=A * form, zorder=8))
    N = 28
    for i in range(N):
        fr = (i / N + u * 0.22) % 1.0
        rr = r + 1.3 * (1 - fr)
        th = i * 2.399 + 2.2 * (1 - fr)
        ax.add_patch(Circle((CX + rr * np.cos(th), Y["heart"] + rr * np.sin(th) * 0.85), 0.03,
                            color=GOLD_L, alpha=A * form * 0.8 * np.sin(np.pi * fr), lw=0, zorder=9))
    ax.plot([CX + 0.5, CX + 2.15], [Y["heart"], Y["heart"]], color=GOLD, lw=0.7, alpha=0.5 * A * form, zorder=8)
    txt(ax, CX + 2.25, Y["heart"], "emptiness · suction", 10.5, GOLD_L, A * form, z=12)
    # attention at the level between the eyes
    glow(ax, CX, Y["brow"], 0.25, GOLD_L, A * 0.5 * form, z=6, n=5)
    title(ax, "第二關 · 離印", "Gate 2 — The Li seal, returning the light", A, "9 rounds")
    lines_block(ax, 6.3, ["Palms up on the thighs. Index and ring together,",
                          "middle finger fully spread — the seal is empty in the middle."], A, size=12)
    hand(ax, 9.75, 4.1, 0.8, curl, A, mid_glow=form)
    seal_legend(ax, 12.55, 3.95, [1, 0, 1], A * ease((u - 3.5) / 1.0), color=CINN_L)
    txt(ax, 12.1, 2.95, "Li ☲  —  fire with an empty heart", 11, CINN_L, A * ease((u - 4) / 1.0))
    if br["active"]:
        cue = "inhale: open the emptiness in the chest" if br["ph"] < 0.5 else "exhale: do not fill it"
    else:
        cue = "" if br["done"] < 9 else "rest attention level between the eyes"
    txt(ax, PX, 2.55, cue, 12, WATER_L, A * 0.9)
    counter(ax, br, "Golden Flower ch. 3: the light enters by itself", A, unit="round")

def sc_g3(ax, u, d):
    A = fade(u, d)
    br = breath("g3", u)
    body(ax, A, chest=br["b"] * 0.4)
    # yellow court target and navel barrier
    glow(ax, CX, Y["p5"], 0.45, GOLD, A * 0.35, z=6, n=6)
    ax.add_patch(Circle((CX, Y["p5"]), 0.07, fill=False, ec=GOLD_L, lw=1.2, alpha=A, zorder=8))
    ax.plot([CX - 1.35, CX + 1.35], [Y["navel"], Y["navel"]], color=CINN, lw=2.0, ls=(0, (6, 4)), alpha=A, zorder=8)
    for i in range(9):
        xx = CX - 1.2 + i * 0.3
        ax.plot([xx, xx + 0.12], [Y["navel"] - 0.04, Y["navel"] - 0.16], color=CINN, lw=1.0, alpha=0.6 * A, zorder=8)
    ax.plot([CX + 1.35, CX + 2.15], [Y["navel"], Y["navel"]], color=CINN, lw=0.8, alpha=0.6 * A, zorder=8)
    txt(ax, CX + 2.25, Y["navel"], "navel — never below", 10.5, CINN_L, A, z=12)
    ax.plot([CX + 0.15, CX + 2.15], [Y["p5"], Y["p5"]], color=GOLD, lw=0.7, alpha=0.5 * A, zorder=8)
    txt(ax, CX + 2.25, Y["p5"], "黃庭 · palace 5", 10.5, GOLD_L, A, z=12)
    # ember: one step down per exhale
    if br["active"]:
        ex = clamp((br["ph"] - 0.5) * 2)
        prog = (br["done"] + ease(ex)) / 9
    else:
        prog = 1.0 if br["done"] == 9 else 0.0
    ey = lerp(Y["heart"], Y["p5"], prog)
    fl = 0.85 + 0.15 * np.sin(u * 13) * np.sin(u * 7.3)
    glow(ax, CX, ey, 0.75 * fl, CINN, A * 0.75, z=9)
    glow(ax, CX, ey, 0.32 * fl, CINN_L, A * 0.9, z=9, n=6)
    ax.add_patch(Circle((CX, ey), 0.07, color="#ffd2a0", alpha=A, zorder=10))
    if prog > 0.97:
        glow(ax, CX, Y["p5"], 0.9, GOLD_L, A * 0.4 * ease((u - 92.3) / 1), z=8)
    # finger-width ticks
    for i in range(10):
        yy = lerp(Y["heart"], Y["p5"], i / 9)
        ax.plot([CX - 0.95, CX - 0.8], [yy, yy], color=GOLD, lw=1.0, alpha=A * (0.9 if i / 9 <= prog + 1e-6 else 0.3), zorder=8)
    title(ax, "第三關 · 心火下降", "Gate 3 — Heart fire descends to the center", A, "9 breaths")
    lines_block(ax, 6.3, ["Picture an ember at the heart. With each exhale it",
                          "sinks one finger-width toward palace 5 — above the",
                          "kidneys, below the heart.",
                          "",
                          "“Water and fire rise and fall within the central palace.”",
                          "                                         — Guizhong zhinan"], A, size=12)
    txt(ax, PX, 3.5, "It comes to rest at the center — never in the belly below.", 12, GOLD_L, A, style="italic")
    counter(ax, br, "one finger-width per exhale", A, ring_col=CINN_L)

HOLD0, HOLD = 4.0, 180.0
def sc_g4(ax, u, d):
    A = fade(u, d)
    body(ax, A)
    cx, cy = CX, Y["crown"]
    op = ease((u - 0.8) / 4)
    ret = ease((u - (HOLD0 + HOLD + 0.5)) / 5.0)
    shim = 0.5 - 0.5 * np.cos(2 * np.pi * (u % PERIOD) / PERIOD)   # slow shimmer only
    # open sky above the crown — kept inside the frame (top below ~8.9)
    glow(ax, cx, cy + 0.25, 1.15 * op, "#a9b8ff", A * 0.25 * op * (1 - ret), z=2)
    for k in range(18):
        th = np.pi * (0.08 + 0.84 * k / 17)
        L = (0.35 + 0.5 * op) * (0.88 + 0.12 * np.sin(u * 0.6 + k))
        ax.plot([cx + 0.38 * np.cos(th), cx + (0.38 + L) * np.cos(th)],
                [cy - 0.05 + 0.38 * np.sin(th), cy - 0.05 + (0.38 + L) * np.sin(th)],
                color=GOLD_L, lw=1.0, alpha=A * (0.25 + 0.15 * shim) * op * (1 - ret), zorder=3, solid_capstyle="round")
    for j in range(3):
        fr = ((u * 0.12) + j / 3) % 1.0
        R_ = 0.3 + 1.9 * fr
        n = 28
        for i in range(n):
            th = 2 * np.pi * i / n + j
            px, py = cx + R_ * np.cos(th), cy + R_ * np.sin(th) * 0.5
            if py < cy - 0.1: continue
            ax.add_patch(Circle((px, py), 0.025, color=GOLD_L, alpha=A * op * (1 - fr) * 0.8 * (1 - ret), lw=0, zorder=3))
    glow(ax, cx, cy - 0.05, 0.4, GOLD_L, A * op * (1 - ret), z=7, n=6)
    if ret > 0:
        ly = lerp(cy - 0.05, Y["p5"], ret)
        glow(ax, cx, ly, 0.45, GOLD_L, A * 0.9, z=9, n=7)
        glow(ax, cx, Y["p5"], 0.6 * ret, GOLD, A * 0.6 * ret, z=8, n=6)
    ax.plot([CX - 0.16, CX + 0.16], [6.38, 6.38], color=CINN_L, lw=1.2, alpha=A * 0.8, zorder=8)
    ax.annotate("", xy=(CX, 6.47), xytext=(CX, 6.32), arrowprops=dict(arrowstyle="-|>", color=CINN_L, lw=1.0, alpha=A), zorder=8)
    txt(ax, CX + 0.75, 6.25, "舌抵上顎  tongue to palate", 9.5, CINN_L, A, z=12)
    title(ax, "第四關 · 頂空", "Gate 4 — Clear crown", A, "tongue on the palate · 3–5 minutes")
    lines_block(ax, 6.3, ["Let attention open at the crown like open sky.",
                          "It does not grip. It does not push qi up.",
                          "Breathe naturally — no counting here."], A, size=12.5)
    tt = clamp((u - HOLD0) / HOLD) * HOLD
    mm, ss = int(tt // 60), int(tt % 60)
    txt(ax, PX, 4.4, f"{mm}:{ss:02d}", 34, GOLD_L, A, weight="bold", family="DejaVu Serif")
    txt(ax, PX + 2.2, 4.4, "/ 3:00 hold", 14, MUTED, A)
    bx0, bw = PX, 6.6
    ax.add_patch(FancyBboxPatch((bx0, 3.65), bw, 0.1, boxstyle="round,pad=0,rounding_size=0.05", color=MUTED, alpha=0.3 * A, lw=0, zorder=15))
    if tt > 0:
        ax.add_patch(FancyBboxPatch((bx0, 3.65), bw * tt / HOLD, 0.1, boxstyle="round,pad=0,rounding_size=0.05", color=GOLD, alpha=A, lw=0, zorder=16))
    for m_ in (1, 2, 3):
        ax.plot([bx0 + bw * m_ / 3] * 2, [3.6, 3.8], color=MUTED, lw=0.8, alpha=0.6 * A, zorder=17)
        txt(ax, bx0 + bw * m_ / 3, 3.38, f"{m_} min", 9.5, MUTED, A, ha="center")
    a2 = ease((u - (HOLD0 + HOLD)) / 1.0) * A
    txt(ax, PX, 2.85, "To extend to 5 minutes, pause the video and keep resting.", 11.5, WATER_L, A * (1 - a2))
    if u < HOLD0:
        cue_box(ax, A, "READY", MUTED, "attention rises lightly to the crown", "Clear crown · 3 minutes", None, None, secs=HOLD0 - u)
    elif tt < HOLD:
        r = HOLD - tt
        cue_box(ax, A, "HOLD", IVORY, "rest at the crown · breathe naturally",
                f"{int(r // 60)}:{int(r % 60):02d} remaining", None, 0.3 + 0.4 * shim, "#a9b8ff")
    else:
        txt(ax, PX, 3.02, "Bring the light back down to the yellow court.", 12, GOLD_L, a2)
        txt(ax, PX, 2.68, "Never end with attention in the head. — Golden Flower, ch. 8", 10.5, MUTED, a2)
        cue_box(ax, A, "RETURN", GOLD_L, "the light descends to palace 5", "Hold complete · 3:00", None, None)

def kan_curl(): return {"index": 0, "middle": 1, "ring": 0, "little": 0.15}

def sc_g5(ax, u, d):
    A = fade(u, d)
    br = breath("g5", u)
    sw = ease((u - 1.0) / 3.5)          # seal change Li -> Kan
    curl = {k: lerp(li_curl()[k], kan_curl()[k], sw) for k in li_curl()}
    body(ax, A, chest=br["b"] * 0.3)
    inh = br["active"] and br["ph"] < 0.5
    ip = clamp(br["ph"] * 2) if br["active"] else 0
    exh = clamp((br["ph"] - 0.5) * 2) if br["active"] else 0
    rounds = br["done"] + (ip if br["active"] else 0)
    merged = clamp(rounds / 3)
    # Li at heart (red, empty middle) and Kan at lower field (blue, solid middle)
    glow(ax, CX, Y["heart"], 0.9, lerp_color(CINN, GOLD, merged), A * 0.55, z=6)
    glow(ax, CX, Y["lower"], 0.85, WATER, A * 0.55 * (1 - 0.6 * merged), z=6)
    final = ease((u - 36.3) / 1.4) if br["done"] == 3 else 0.0
    # trigrams: on the third round the yang line of Kan rises into Li
    lift = ease(ip) if br["n"] == 3 and br["active"] else (1.0 if br["done"] == 3 else 0.0)
    li_col = lerp_color(CINN_L, GOLD_L, final)
    kan_col = lerp_color(WATER_L, "#cfd6ff", final)
    trigram(ax, CX, Y["heart"], [1, 0 if lift < 1 else 1, 1], w=0.7, lh=0.08, gap=0.17, color=li_col, a=A, z=12)
    trigram(ax, CX, Y["lower"], [0, 1, 0] if lift <= 0 else [0, 0, 0], w=0.7, lh=0.08, gap=0.17, color=kan_col, a=A, z=12)
    if 0 < lift < 1:
        my = lerp(Y["lower"], Y["heart"], lift)
        glow(ax, CX, my, 0.35, GOLD_L, A, z=11, n=6)
        trigram(ax, CX, my - 0.17 * 0, [1], w=0.7, lh=0.08, gap=0, color=lerp_color(WATER_L, GOLD_L, lift), a=A, z=13)
    # water stream rising on the inhale
    if inh:
        for i in range(22):
            fr = (i / 22 + u * 0.9) % 1.0
            if fr > ip * 1.15: continue
            yy = lerp(Y["perineum"] + 0.2, Y["heart"], fr)
            xx = CX + 0.12 * np.sin(fr * 9 + u * 3)
            c = lerp_color(WATER_L, GOLD_L, fr ** 1.5)
            ax.add_patch(Circle((xx, yy), 0.045, color=c, alpha=A * 0.9, lw=0, zorder=10))
        # soft perineum lift
        for k in range(2):
            yy = Y["perineum"] - 0.15 + 0.12 * k + 0.1 * ip
            ax.plot([CX - 0.18, CX, CX + 0.18], [yy, yy + 0.1, yy], color=WATER_L, lw=1.3, alpha=A * 0.8 * np.sin(np.pi * ip), zorder=10)
        txt(ax, CX + 0.55, Y["perineum"] - 0.05, "soft lift", 9.5, WATER_L, A * np.sin(np.pi * ip), z=12)
    if br["active"] and not inh:
        glow(ax, CX, Y["heart"], 0.55 + 0.25 * np.sin(np.pi * exh), GOLD_L, A * 0.6, z=9, n=6)
    if final > 0:
        glow(ax, CX, Y["heart"], 1.6 * final, GOLD_L, A * 0.35, z=7)
        txt(ax, CX - 1.5, Y["heart"] + 0.75, "Li → Qian ☰", 10.5, GOLD_L, A * final, ha="right", z=12)
        txt(ax, CX - 1.5, Y["lower"] - 0.2, "Kan → Kun ☷", 10.5, "#cfd6ff", A * final, ha="right", z=12)
    title(ax, "第五關 · 取坎填離", "Gate 5 — Join Kan to Li", A, "3 rounds · keep the chest empty")
    lines_block(ax, 6.3, ["Change the seal: close the middle finger — Kan.",
                          "Shine the turned-in light gently down into Kan."], A, size=12)
    hand(ax, 9.75, 4.1, 0.8, curl, A, mid_glow=sw)
    lg = [lerp(1, 0, sw) > 0.5, sw > 0.5, lerp(1, 0, sw) > 0.5]
    seal_legend(ax, 12.55, 3.95, [int(x) for x in lg], A, color=lerp_color(CINN_L, WATER_L, sw))
    txt(ax, 12.1, 2.95, "Kan ☵  —  water holding one yang line" if sw > 0.5 else "Li ☲  —  fire with an empty heart",
        11, WATER_L if sw > 0.5 else CINN_L, A)
    if br["active"]:
        cue = "inhale: a whisper-light lift — the yang line is drawn up" if inh else "exhale: let it rest in the empty chest"
    elif br["done"] == 3:
        cue = "從此變成乾健體 — it becomes the strong body of Qian"
    else:
        cue = ""
    txt(ax, PX, 2.55, cue, 12, GOLD_L if br["done"] == 3 else WATER_L, A * 0.95)
    counter(ax, br, "attraction, never squeezing", A, unit="round")

def sc_close(ax, u, d):
    A = fade(u, d)
    br = breath("close", u)
    body(ax, A)
    p1 = 1 - ease((u - 92.4) / 1.0)
    glow(ax, CX, Y["lower"], 0.8, "#ffb070", A * 0.55 * p1 * (0.6 + 0.4 * br["b"]), z=6)
    for sx in (-1, 1):
        ax.add_patch(Ellipse((CX + 0.32 * sx, Y["lower"] - 0.05), 0.55, 0.32, fc=BODY, ec=GOLD, lw=1.4, alpha=A * p1, zorder=8))
    s2 = ease((u - 92.2) / 1.2)
    for sx in (-1.5, 1.5):
        glow(ax, CX + sx, Y["sole"], 0.55, GOLD_L, A * s2 * 0.8, z=7)
    title(ax, "收功", "Closing — seal and ground", A)
    lines_block(ax, 6.3, ["Rub the palms warm. Rest them on the lower belly",
                          "for 9 breaths.",
                          "Then palms to soles if you can — the 坎離印:",
                          "Laogong meets Yongquan; fire descends, water rises.",
                          "End with attention at the soles."], A, size=12.5)
    if br["done"] == 9:
        cue_box(ax, A, "SOLES", GOLD_L, "rest attention at the soles (湧泉), then slowly open the eyes",
                "Breaths complete · 9 / 9", None, None)
    else:
        counter(ax, br, "palms on the lower belly", A)

def sc_warn(ax, u, d):
    A = fade(u, d, 0.6, 0.8)
    body(ax, A)
    # cycle: heat in head (red) -> stop -> attention drops to soles, head cools
    cyc = (u % 5.0) / 5.0
    heat = ease(cyc / 0.35) * (1 - ease((cyc - 0.45) / 0.25))
    drop = ease((cyc - 0.4) / 0.35)
    glow(ax, CX, 6.85, 1.1, CINN, A * 0.85 * heat, z=7)
    if 0.4 < cyc < 0.9:
        yy = lerp(6.6, Y["sole"], drop)
        glow(ax, CX, yy, 0.35, GOLD_L, A * 0.8 * (1 - ease((cyc - 0.8) / 0.1)), z=8, n=6)
    for sx in (-1.5, 1.5):
        glow(ax, CX + sx, Y["sole"], 0.55, GOLD_L, A * 0.8 * drop * (1 - ease((cyc - 0.92) / 0.08)), z=7)
    txt(ax, CX, 8.4, "heat in the head → stop → soles", 11, CINN_L, A, ha="center")
    # warning card
    ax.add_patch(FancyBboxPatch((8.4, 4.15), 7.1, 3.95, boxstyle="round,pad=0.05,rounding_size=0.15",
                                fc="#1a0c10", ec=CINN, lw=1.6, alpha=0.9 * A, zorder=14))
    txt(ax, 8.75, 7.65, "火昇水降", 24, CINN_L, A, weight="bold")
    txt(ax, 10.85, 7.62, "Fire rising without water", 15, IVORY, A)
    lines_block(ax, 6.95, ["Heat, pressure or tightness in the head, eyes or",
                           "forehead means fire is climbing with no water to meet it.",
                           "Stop the sitting at once. Bring attention to the soles",
                           "(湧泉 Yongquan) and take the 坎離印 until the head is cool.",
                           "Return to gates 1–3 until the chest has softened again."],
                ease((u - 0.6) / 0.8) * A, size=11.5, dy=0.5, x=8.75)
    b = ease((u - 2.5) / 0.8) * A
    txt(ax, PX, 3.55, "The order of practice", 15, GOLD, b, weight="bold")
    rows = [("Days 1–21", "Gates 1–3 + closing, daily"),
            ("From day 22", "Add gate 4 — clear crown"),
            ("Then", "Add gate 5 only once the crown stays cool and clear"),
            ("Within 100 days", "All five gates — the foundation (百日築基)")]
    for i, (k, v) in enumerate(rows):
        a = ease((u - 3.0 - i * 0.5) / 0.7) * A
        txt(ax, PX, 3.0 - i * 0.48, k, 12, GOLD_L, a, weight="bold")
        txt(ax, PX + 2.0, 3.0 - i * 0.48, v, 12, IVORY, a)
    txt(ax, PX, 0.75, "Soften the chest before you open the top. Never push — the force is attraction.", 11, MUTED,
        ease((u - 5.5) / 0.8) * A, style="italic")

def sc_end(ax, u, d):
    A = fade(u, d, 0.8, 1.6)
    trigram(ax, 6.3, 4.7, [1, 1, 1], w=1.1, lh=0.14, gap=0.3, color=GOLD_L, a=A * 0.9)
    trigram(ax, 9.7, 4.7, [0, 0, 0], w=1.1, lh=0.14, gap=0.3, color="#cfd6ff", a=A * 0.9)
    txt(ax, 6.3, 3.85, "乾", 14, GOLD_L, A, ha="center")
    txt(ax, 9.7, 3.85, "坤", 14, "#cfd6ff", A, ha="center")
    txt(ax, 8, 4.75, "取坎填離", 40, GOLD, A, ha="center", weight="bold")
    txt(ax, 8, 2.9, "Later Heaven returns to Former Heaven.", 15, IVORY, A, ha="center")
    txt(ax, 8, 2.3, "Li Gong · Opening the Top", 12, MUTED, A, ha="center")

def lerp_color(c1, c2, t):
    a = np.array(matplotlib.colors.to_rgb(c1)); b = np.array(matplotlib.colors.to_rgb(c2))
    return tuple(a + (b - a) * clamp(t))

SCENES = {"intro": sc_intro, "posture": sc_posture, "g1": sc_g1, "g2": sc_g2, "g3": sc_g3,
          "g4": sc_g4, "g5": sc_g5, "close": sc_close, "warn": sc_warn, "end": sc_end}

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
    if name.endswith("card"):
        sc_card(ax, name, u, d)
    else:
        SCENES[name](ax, u, d)
    if not name.endswith("card") and name not in ("intro", "end"):
        ov = 1 - fade(u, d, 0.45, 0.35)
        if ov > 0.01:
            ax.add_patch(matplotlib.patches.Rectangle((0, 0), 16, 9, color=BG_BOT, alpha=ov, zorder=29))
    # session clock + gate-segmented progress bar
    rem = max(0.0, TOTAL - t)
    txt(ax, 15.6, 8.72, f"session {int(t // 60):02d}:{int(t % 60):02d}  ·  {int(rem // 60):02d}:{int(rem % 60):02d} left",
        10, MUTED, 0.85, ha="right", z=32, family="DejaVu Sans")
    x0, x1 = 0.35, 15.65
    sx = lambda tt: x0 + (x1 - x0) * tt / TOTAL
    ax.plot([x0, x1], [0.22, 0.22], color=MUTED, lw=0.6, alpha=0.25, zorder=30)
    cur = GATE_OF.get(name, 0)
    for gi, (cn, gn) in enumerate([("g1card", "g1"), ("g2card", "g2"), ("g3card", "g3"), ("g4card", "g4"),
                                   ("g5card", "g5"), ("closecard", "close")], start=1):
        a0 = STARTS[cn][0]; a1 = STARTS[gn][0] + STARTS[gn][1]
        on = gi == cur
        ax.plot([sx(a0) + 0.03, sx(a1) - 0.03], [0.22, 0.22], color=GOLD_L if on else GOLD, lw=3.2 if on else 1.6,
                alpha=0.9 if on else 0.3, zorder=31, solid_capstyle="butt")
        lab = f"G{gi}" if gi < 6 else "收功"
        txt(ax, (sx(a0) + sx(a1)) / 2, 0.42, lab, 9.5 if on else 8.5, GOLD_L if on else MUTED,
            1.0 if on else 0.55, ha="center", z=32)
    ax.add_patch(Circle((sx(t), 0.22), 0.05, color=IVORY, alpha=0.9, lw=0, zorder=33))

def render(i):
    draw(i / FPS)
    _FIG.canvas.draw()
    return bytes(np.asarray(_FIG.canvas.buffer_rgba())[..., :3].tobytes())

# ---------------------------------------------------------------- audio
def make_audio(path, sr=32000):
    """Gentle eyes-closed audio: breath tone rising on inhale / falling on exhale,
    soft breath swell, faint drone, a bell on each count, a gong at each gate change."""
    n = int(TOTAL * sr); t = np.arange(n) / sr
    grid = np.arange(0, TOTAL, 1 / 200)
    bb = np.zeros_like(grid); act = np.zeros_like(grid); counts = []
    for k, g in enumerate(grid):
        name, u, d = seg_at(g)
        if name in SCHED:
            br = breath(name, u)
            if br["active"]:
                bb[k] = br["b"]; act[k] = 1.0
    # smooth the activity gate (1 s)
    ker = np.ones(200) / 200
    act = np.convolve(act, ker, mode="same")
    for name in SCHED:
        st, d = STARTS[name]
        prev = 0
        for g in np.arange(0, d, 1 / 200):
            dn = breath(name, g)["done"]
            if dn > prev:
                counts.append((st + g, dn == SCHED[name][1])); prev = dn
    b = np.interp(t, grid, bb); a = np.interp(t, grid, act)
    # breath tone: pitch glides up a major third on inhale, back down on exhale
    f = 174.6 * 2 ** (b * 4 / 12)
    ph = 2 * np.pi * np.cumsum(f) / sr
    tone = (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph + 0.4)) * a * (0.2 + 0.8 * b)
    # band-passed noise swell (tiled 20 s buffer)
    rng = np.random.default_rng(1)
    L = 20 * sr
    nz = rng.standard_normal(L); F = np.fft.rfft(nz); fr = np.fft.rfftfreq(L, 1 / sr)
    F *= np.exp(-((fr - 450) / 300) ** 2); nz = np.fft.irfft(F, L); nz /= np.abs(nz).max()
    nz = np.tile(nz, n // L + 1)[:n]
    swell = nz * b * a
    drone = (0.5 * np.sin(2 * np.pi * 87.3 * t) + 0.3 * np.sin(2 * np.pi * 130.8 * t + 0.3)) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.05 * t))
    out = 0.035 * drone + 0.10 * tone + 0.10 * swell
    def add_bell(tc, f0, amp, dur, dec):
        i0 = int(tc * sr); L_ = min(int(sr * dur), n - i0)
        if L_ <= 0 or i0 < 0: return
        tt = np.arange(L_) / sr
        att = np.clip(tt / 0.004, 0, 1)
        sig = (np.sin(2 * np.pi * f0 * tt) + 0.35 * np.sin(2 * np.pi * f0 * 2.76 * tt) * np.exp(-tt * 3)
               + 0.15 * np.sin(2 * np.pi * f0 * 5.4 * tt) * np.exp(-tt * 6)) * np.exp(-tt * dec) * att
        out[i0:i0 + L_] += amp * sig
    for tc, last in counts:
        if last:
            add_bell(tc, 784.0, 0.06, 4.0, 1.2); add_bell(tc + 0.25, 1046.5, 0.05, 4.0, 1.2)
        else:
            add_bell(tc, 1046.5, 0.035, 2.0, 2.8)
    # gong at each gate change (start of each prepare card)
    for cn in ["g1card", "g2card", "g3card", "g4card", "g5card", "closecard"]:
        st = STARTS[cn][0]
        i0 = int(st * sr); L_ = min(int(sr * 8), n - i0); tt = np.arange(L_) / sr
        g = (np.sin(2 * np.pi * 110 * tt) + 0.6 * np.sin(2 * np.pi * 110 * 2.02 * tt + 0.5) * np.exp(-tt * 0.8)
             + 0.35 * np.sin(2 * np.pi * 110 * 2.93 * tt) * np.exp(-tt * 1.4)
             + 0.2 * np.sin(2 * np.pi * 110 * 4.1 * tt) * np.exp(-tt * 2.0))
        g *= np.exp(-tt * 0.55) * np.clip(tt / 0.01, 0, 1) * (1 + 0.08 * np.sin(2 * np.pi * 3.5 * tt))
        out[i0:i0 + L_] += 0.13 * g
    # gate 4: soft minute chimes and a bell at the end of the hold
    g4 = STARTS["g4"][0] + HOLD0
    add_bell(g4, 659.3, 0.04, 3.0, 1.5)
    for m_ in (60, 120):
        add_bell(g4 + m_, 1318.5, 0.025, 2.5, 2.0)
    add_bell(g4 + HOLD, 784.0, 0.06, 4.0, 1.2); add_bell(g4 + HOLD + 0.25, 1046.5, 0.05, 4.0, 1.2)
    fadeL = int(2 * sr); out[:fadeL] *= np.linspace(0, 1, fadeL); out[-fadeL:] *= np.linspace(1, 0, fadeL)
    out = out / max(1e-9, np.abs(out).max()) * 0.7
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())

def main():
    args = sys.argv[1:]
    out = "/workspace/kinetic/five_gates_realtime.mp4"
    if "--still" in args:
        ts = [float(x) for x in args[args.index("--still") + 1].split(",")]
        _init()
        os.makedirs("/workspace/kinetic/frames_rt", exist_ok=True)
        for tt in ts:
            draw(tt); p = f"/workspace/kinetic/frames_rt/t{tt:06.1f}.png"; _FIG.savefig(p, dpi=100); print(p)
        return
    if args: out = args[0]
    wav = "/workspace/kinetic/_audio_rt.wav"
    make_audio(wav)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "28",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    workers = int(os.environ.get("WORKERS", "6"))
    with mp.Pool(workers, initializer=_init) as pool:
        for i, buf in enumerate(pool.imap(render, range(NFRAMES), chunksize=6)):
            ff.stdin.write(buf)
            if i % 900 == 0:
                print(f"frame {i}/{NFRAMES}", flush=True)
    ff.stdin.close(); ff.wait()
    print("done", out, TOTAL, "s")

if __name__ == "__main__":
    main()
