"""Diagrams for 마리지천's post "How to cultivate the unmoving mind" (부동심 不動心), 2026-11-21 KST.
https://x.com/z9_s8_y_9/status/2124124210348097894  (quotes the Nov 18 rib-purification post
https://x.com/z9_s8_y_9/status/2123057544998568036)

Pure matplotlib, no generators. Palette and fonts follow kinetic/five_gates.py.
Run:  python3 make_diagrams.py   -> writes 01..06 PNGs (1920x1080) next to this file.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Circle, Ellipse, Polygon, FancyBboxPatch, FancyArrowPatch, Rectangle
import logging; logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

for f in ["/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
          "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"]:
    if os.path.exists(f):
        fm.fontManager.addfont(f)
plt.rcParams["font.family"] = ["Noto Serif CJK TC", "DejaVu Sans", "Noto Sans Symbols"]

OUT = os.path.dirname(os.path.abspath(__file__))
BG_TOP, BG_BOT = np.array([14, 18, 48]) / 255, np.array([4, 5, 14]) / 255
BODY = "#141a3d"
GOLD, GOLD_L = "#d4af37", "#f3d98b"
CINN, CINN_L = "#c8372d", "#ff7a4d"
WATER, WATER_L = "#3f8fd6", "#8fd0ff"
IVORY, MUTED = "#efe6d2", "#8d8aa6"
VIOLET = "#b9a6ff"
SRC = "Source: 마리지천摩利支天 @z9_s8_y_9 · post of 2026-11-21 KST"

def clamp(v): return max(0.0, min(1.0, v))

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

def new_fig(seed=1):
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 16); ax.set_ylim(0, 9); ax.axis("off")
    g = np.linspace(0, 1, 256)[:, None, None]
    img = BG_TOP * (1 - g) + BG_BOT * g
    ax.imshow(img, extent=[0, 16, 0, 9], aspect="auto", zorder=0)
    rs = np.random.RandomState(seed)
    ax.scatter(rs.uniform(0, 16, 160), rs.uniform(0, 9, 160), s=rs.uniform(0.5, 3, 160),
               color=IVORY, alpha=0.18, lw=0, zorder=1)
    return fig, ax

def glow(ax, x, y, r, color, a=1.0, z=5, n=10):
    for i in range(n):
        k = 1 - i / n
        ax.add_patch(Circle((x, y), r * k, color=color, alpha=clamp(a * 0.11), lw=0, zorder=z))

def T(ax, x, y, s, size=15, color=IVORY, ha="left", va="center", weight="normal", z=20, **kw):
    return ax.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, fontweight=weight, zorder=z,
                   linespacing=1.35, **kw)

def title(ax, main, sub):
    T(ax, 8, 8.5, main, 30, GOLD_L, ha="center", weight="bold")
    T(ax, 8, 8.0, sub, 16, MUTED, ha="center")
    ax.plot([5.2, 10.8], [7.72, 7.72], color=GOLD, lw=0.8, alpha=0.5, zorder=3)

def footer(ax, extra=""):
    T(ax, 0.3, 0.22, SRC + (("  ·  " + extra) if extra else ""), 11, MUTED, ha="left")
    T(ax, 15.7, 0.22, "li-gong · diagrams drawn in Python", 11, MUTED, ha="right")

def arrow(ax, p, q, color=GOLD_L, lw=2.2, rad=0.0, a=0.95, z=12, head=18, ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, connectionstyle=f"arc3,rad={rad}", arrowstyle="-|>",
                                 mutation_scale=head, color=color, lw=lw, alpha=a, zorder=z, linestyle=ls))

def card(ax, x, y, w, h, ec=GOLD, a=0.9, fc="#0c1030", z=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.18",
                                fc=fc, ec=ec, lw=1.4, alpha=a, zorder=z))

def save(fig, name):
    p = os.path.join(OUT, name); fig.savefig(p, dpi=100); plt.close(fig); print("wrote", p)

# ------------------------------------------------------------- profile body (facing left)
def profile(ax, ox, oy, s=1.0, spine=True, zb=3):
    """Seated meditator in profile, facing left. Returns dict of anatomical anchor points."""
    def P(x, y): return (ox + x * s, oy + y * s)
    torso = [(2.75, 6.25), (2.68, 5.9), (2.25, 5.45), (1.98, 4.75), (2.05, 4.0), (2.0, 3.2),
             (2.1, 2.4), (2.35, 1.9), (3.4, 1.72), (4.2, 1.95), (4.0, 2.8), (4.12, 3.8),
             (4.35, 4.8), (4.22, 5.6), (3.55, 6.25)]
    tor = catmull([P(*q) for q in torso])
    head_c, legs_c = P(3.1, 6.95), P(2.55, 1.55)
    for lw, al in [(9, 0.05), (5, 0.10), (2.0, 0.8)]:
        ax.add_patch(Polygon(tor, closed=True, fill=False, ec=GOLD, lw=lw, alpha=al, zorder=zb))
        ax.add_patch(Ellipse(head_c, 1.25 * s, 1.5 * s, fill=False, ec=GOLD, lw=lw, alpha=al, zorder=zb))
        ax.add_patch(Ellipse(legs_c, 4.3 * s, 0.95 * s, fill=False, ec=GOLD, lw=lw, alpha=al, zorder=zb))
    ax.add_patch(Ellipse(legs_c, 4.3 * s, 0.95 * s, color=BODY, lw=0, zorder=zb + 1))
    ax.add_patch(Polygon(tor, closed=True, color=BODY, lw=0, zorder=zb + 1))
    ax.add_patch(Ellipse(head_c, 1.25 * s, 1.5 * s, color=BODY, lw=0, zorder=zb + 1))
    # nose + closed eye
    ax.plot(*zip(P(2.49, 7.05), P(2.36, 6.82), P(2.5, 6.78)), color=GOLD, lw=1.6, alpha=0.8, zorder=zb + 2)
    ax.plot(*zip(P(2.68, 7.05), P(2.86, 7.03)), color=GOLD, lw=1.2, alpha=0.6, zorder=zb + 2)
    sp = catmull([P(3.35, 6.15), P(3.78, 5.5), P(3.98, 4.8), P(3.88, 3.8), P(3.66, 2.9), P(3.78, 2.1)],
                 n=20, closed=False)
    if spine:
        ax.plot(sp[:, 0], sp[:, 1], color=GOLD, lw=1.0, alpha=0.35, zorder=zb + 2)
        idx = np.linspace(4, len(sp) - 3, 22).astype(int)
        for i in idx:
            d = sp[i + 1] - sp[i - 1]; d = d / np.linalg.norm(d); nrm = np.array([-d[1], d[0]])
            a, b = sp[i] - nrm * 0.11 * s, sp[i] + nrm * 0.11 * s
            ax.plot([a[0], b[0]], [a[1], b[1]], color=GOLD, lw=3.2 * s, alpha=0.33, solid_capstyle="round", zorder=zb + 2)
    return dict(center=P(2.62, 4.35), xiphoid=P(2.02, 4.2), lingtai=P(3.97, 4.95), mingmen=P(3.68, 2.95),
                lower=P(2.75, 2.45), head=head_c, prefrontal=P(2.7, 7.35), parietal=P(3.45, 7.6), s=s)

# =============================================================== 01 seesaw vs spillover
def fig01():
    fig, ax = new_fig(1)
    title(ax, "The Seesaw and the Spillover", "자율신경 범람 (Autonomic Spillover) · the precondition for the unmoving mind 부동심 不動心")
    # ---- left panel: seesaw
    T(ax, 3.9, 7.1, "1 · Ordinarily: a seesaw", 20, GOLD_L, ha="center", weight="bold")
    T(ax, 3.9, 6.62, "reciprocal inhibition 상호 억제", 15, MUTED, ha="center")
    fx, fy = 3.9, 2.55
    ax.add_patch(Polygon([(fx - 0.55, fy - 0.85), (fx + 0.55, fy - 0.85), (fx, fy)], color=GOLD, alpha=0.85, zorder=6))
    ang = np.deg2rad(14); L = 2.9
    l = (fx - L * np.cos(ang), fy + L * np.sin(ang)); r = (fx + L * np.cos(ang), fy - L * np.sin(ang))
    ax.plot([l[0], r[0]], [l[1], r[1]], color=GOLD_L, lw=7, solid_capstyle="round", zorder=7)
    for (x, y), c, cl in [(l, CINN, CINN_L), (r, WATER, WATER_L)]:
        glow(ax, x + 0.4, y + 0.42, 0.9, cl, 0.7, z=6)
        ax.add_patch(Circle((x + 0.4, y + 0.42), 0.38, color=c, zorder=8))
        ax.add_patch(Circle((x + 0.3, y + 0.54), 0.11, color="white", alpha=0.35, zorder=9))
    T(ax, l[0] + 0.25, l[1] + 1.55, "Arousal system ↑\n각성계 · sympathetic 交感", 15, CINN_L, ha="center")
    T(ax, r[0] + 0.25, r[1] - 0.75, "Quiescence system ↓\n고요계 · parasympathetic 副交感", 15, WATER_L, ha="center")
    T(ax, 3.2, 0.95, "When one side rises, the other goes down.\nThey hold each other in check.", 15, IVORY, ha="center")
    # ---- middle trigger arrow
    arrow(ax, (7.35, 4.4), (8.75, 4.4), GOLD_L, lw=3, head=26)
    T(ax, 8.05, 5.25, "push one system\nto its critical point", 13.5, GOLD_L, ha="center")
    T(ax, 8.05, 3.45, "deep meditation\nintense breath\nor ritual", 13, MUTED, ha="center")
    # ---- right panel: two full gauges overflowing
    T(ax, 12.35, 7.1, "2 · Spillover 범람", 20, GOLD_L, ha="center", weight="bold")
    T(ax, 12.35, 6.62, "inhibition released: both systems at peak together", 15, MUTED, ha="center")
    gx = {"S": 11.0, "P": 13.7}; base, top = 1.9, 5.3
    for k, c, cl, lab in [("S", CINN, CINN_L, "Arousal\n각성계"), ("P", WATER, WATER_L, "Quiescence\n고요계")]:
        x = gx[k]
        ax.add_patch(FancyBboxPatch((x - 0.45, base), 0.9, top - base, boxstyle="round,pad=0,rounding_size=0.2",
                                    fc="none", ec=GOLD, lw=1.6, alpha=0.8, zorder=9))
        ax.add_patch(FancyBboxPatch((x - 0.38, base + 0.07), 0.76, top - base - 0.1, boxstyle="round,pad=0,rounding_size=0.16",
                                    color=c, alpha=0.85, lw=0, zorder=8))
        glow(ax, x, top, 0.8, cl, 0.8, z=7)
        T(ax, x, base - 0.55, lab, 15, cl, ha="center")
    ax.plot([10.2, 14.5], [4.7, 4.7], color=GOLD_L, lw=1.2, ls=(0, (5, 4)), alpha=0.8, zorder=10)
    T(ax, 14.62, 4.7, "critical\npoint\n임계점", 12.5, GOLD_L, va="center")
    arrow(ax, (11.15, top + 0.15), (13.55, top + 0.15), CINN_L, lw=2.4, rad=-0.45, head=20)
    arrow(ax, (13.55, top - 0.05), (11.15, top - 0.05), WATER_L, lw=2.4, rad=-0.45, head=20)
    T(ax, 12.35, 4.15, "energy floods\ninto the\nopposite system", 13, IVORY, ha="center")
    T(ax, 12.35, 0.95, "Both nervous systems switch on at full intensity at once.", 15, IVORY, ha="center")
    footer(ax)
    save(fig, "01_seesaw_and_spillover.png")

# =============================================================== 02 two roads
def fig02():
    fig, ax = new_fig(2)
    title(ax, "Two Roads to Spillover", "the two routes neurotheology describes (as given in the post) · curves are schematic, not measured data")
    def sig(t, c, k): return 1 / (1 + np.exp(-(t - c) * k))
    panels = [
        (0.7, "Still-meditation path  (정적 명상 경로)", "Quiescence → Arousal   고요계 → 각성계",
         "WATER", "Stillness and no-mind (무심 無心) pushed to the extreme;\nsamādhi (선정 禪定) until the parasympathetic saturates",
         "Then the clear arousal circuit suddenly switches on too:\nextremely, lucidly awake without falling asleep,\nyet without a speck of agitation."),
        (8.35, "Dynamic-practice path  (역동적 수행 경로)", "Arousal → Quiescence   각성계 → 고요계",
         "CINN", "Tibetan tummo breath and breath retention (지식 止息),\nSufi whirling, fierce mantras: sympathetic driven to its limit",
         "Past the critical point the parasympathetic rebounds and fires\nexplosively: amid overwhelming energy and heat, emotions cut off;\nuncanny stillness and ecstatic bliss (Active Bliss) burst out."),
    ]
    for x0, ttl, sub, lead, how, res in panels:
        w = 6.95
        card(ax, x0, 0.75, w, 6.7, ec=GOLD, a=0.55, fc="#0a0d26", z=2)
        T(ax, x0 + w / 2, 7.05, ttl, 18, GOLD_L, ha="center", weight="bold")
        T(ax, x0 + w / 2, 6.6, sub, 15, WATER_L if lead == "WATER" else CINN_L, ha="center")
        T(ax, x0 + w / 2, 5.95, how, 13, MUTED, ha="center")
        # axes
        ax0, ay0, aw, ah = x0 + 0.7, 2.35, w - 1.4, 2.75
        ax.plot([ax0, ax0], [ay0, ay0 + ah], color=MUTED, lw=1, zorder=5)
        ax.plot([ax0, ax0 + aw], [ay0, ay0], color=MUTED, lw=1, zorder=5)
        T(ax, ax0 + aw, ay0 - 0.22, "time →", 12, MUTED, ha="right")
        T(ax, ax0 - 0.12, ay0 + ah, "activation", 12, MUTED, ha="right", va="top", rotation=90)
        t = np.linspace(0, 1, 400); tc = 0.55
        thr = ay0 + ah * 0.78
        ax.plot([ax0, ax0 + aw], [thr, thr], color=GOLD_L, lw=1, ls=(0, (5, 4)), alpha=0.75, zorder=6)
        T(ax, ax0 + aw - 0.05, thr - 0.2, "critical point 임계점", 11.5, GOLD_L, ha="right")
        ax.add_patch(Rectangle((ax0 + aw * tc, ay0), aw * (1 - tc), ah, color=GOLD, alpha=0.07, lw=0, zorder=4))
        T(ax, ax0 + aw * (tc + 1) / 2, ay0 + ah * 0.42, "both ON", 14, GOLD_L, ha="center", weight="bold")
        if lead == "WATER":
            lead_y = 0.12 + 0.8 * (1 - np.exp(-t * 4.2))
            other = 0.15 + 0.73 * sig(t, tc + 0.03, 60)
            lc, oc = WATER_L, CINN_L; ln, on = "quiescence (parasymp.)", "arousal (symp.)"
        else:
            lead_y = 0.1 + 0.82 * (1 - np.exp(-t * 4.0)) + 0.05 * np.sin(t * 46) * (1 - sig(t, tc, 25))
            other = 0.12 + 0.86 * sig(t, tc + 0.03, 70) - 0.1 * sig(t, tc + 0.14, 30)
            lc, oc = CINN_L, WATER_L; ln, on = "arousal (symp.)", "quiescence (parasymp.)"
        X = ax0 + t * aw
        for lw, al in [(7, 0.12), (2.6, 1)]:
            ax.plot(X, ay0 + lead_y * ah, color=lc, lw=lw, alpha=al, zorder=7)
            ax.plot(X, ay0 + other * ah, color=oc, lw=lw, alpha=al, zorder=7)
        if lead == "WATER":
            T(ax, ax0 + aw * 0.06, ay0 + lead_y[60] * ah + 0.3, "leads: " + ln, 12, lc)
        else:
            T(ax, ax0 + aw * 0.2, ay0 + 0.9, "leads: " + ln, 12, lc)
        T(ax, ax0 + aw * 0.06, ay0 + other[20] * ah + 0.22, on, 12, oc)
        T(ax, x0 + w / 2, 1.45, res, 13, IVORY, ha="center")
    footer(ax)
    save(fig, "02_two_roads_to_spillover.png")

# =============================================================== 03 deafferentation
def fig03():
    fig, ax = new_fig(3)
    title(ax, "Deafferentation: the Boundary Stops Being Drawn",
          "d'Aquili & Newberg's account, as the post summarizes it · 구심성 차단 (Deafferentation)")
    sx, sy, s = 0.2, -0.75, 1.0
    def P(x, y): return (sx + x * s, sy + y * s)
    brain = catmull([P(*q) for q in [(1.9, 5.0), (2.2, 6.0), (3.0, 6.9), (4.3, 7.3), (5.6, 7.25), (6.8, 6.8), (7.7, 6.0),
                                     (8.1, 5.0), (7.9, 4.2), (7.0, 3.75), (6.0, 3.75), (5.2, 3.4), (4.0, 3.3),
                                     (3.2, 3.6), (3.0, 4.2), (2.4, 4.3)]])
    ax.add_patch(Polygon(brain, closed=True, fc=BODY, ec=GOLD, lw=2, zorder=4))
    ax.add_patch(Ellipse(P(7.1, 3.35), 1.7, 0.95, fc=BODY, ec=GOLD, lw=1.4, alpha=0.9, zorder=3))
    ax.add_patch(Polygon([P(5.6, 3.7), P(6.45, 3.75), P(6.3, 2.35), P(5.95, 2.35)], fc=BODY, ec=GOLD, lw=1.4, zorder=3))
    for pts in [[(3.2, 4.45), (4.3, 4.9), (5.7, 5.25)], [(5.05, 7.25), (4.8, 6.2), (4.45, 5.05)],
                [(6.85, 6.82), (7.0, 6.2), (7.3, 5.65)]]:
        c = catmull([P(*q) for q in pts], n=12, closed=False)
        ax.plot(c[:, 0], c[:, 1], color=GOLD, lw=1.3, alpha=0.55, zorder=5)
    # OAA highlight
    oaa = catmull([P(*q) for q in [(5.25, 7.2), (6.75, 6.8), (7.2, 6.0), (6.4, 5.7), (5.4, 6.1), (5.15, 6.7)]])
    gc = P(6.15, 6.45)
    glow(ax, gc[0], gc[1], 1.35, VIOLET, 0.9, z=5)
    ax.add_patch(Polygon(oaa, closed=True, fc=VIOLET, ec=IVORY, lw=1.2, alpha=0.55, zorder=6))
    pf = catmull([P(*q) for q in [(2.0, 5.0), (2.25, 6.0), (2.95, 6.8), (3.6, 7.05), (3.6, 5.6), (2.6, 4.6)]])
    ax.add_patch(Polygon(pf, closed=True, fc=GOLD, alpha=0.12, lw=0, zorder=5))
    T(ax, P(2.95, 5.95)[0], P(2.95, 5.95)[1], "prefrontal\n전전두엽", 12.5, GOLD_L, ha="center")
    # label OAA
    T(ax, 8.2, 7.2, "posterior superior parietal lobe = Orientation\nAssociation Area (OAA) · 후상부 두정엽 · 방향연합영역",
      13, VIOLET, ha="center")
    ax.plot([7.6, gc[0] + 0.3], [6.88, gc[1] + 0.25], color=VIOLET, lw=1, alpha=0.8, zorder=7)
    T(ax, P(4.9, 4.2)[0], P(4.9, 4.2)[1], "its job: draw the line between\n'where my body ends' and\n'where the outside world begins'", 12.5, IVORY, ha="center")
    # incoming signals, blocked
    for (a0, a1), lab in [(((8.8, 2.6), (6.95, 5.75)), ""), (((9.2, 4.3), (7.3, 6.15)), ""), (((9.3, 6.2), (7.45, 6.5)), "")]:
        p, q = P(*a0), P(*a1)
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=16, color=WATER_L, lw=2, alpha=0.85,
                                     zorder=8, linestyle=(0, (4, 3))))
        m = (0.45 * np.array(p) + 0.55 * np.array(q))
        ax.plot([m[0] - 0.15, m[0] + 0.15], [m[1] - 0.15, m[1] + 0.15], color=CINN_L, lw=3, zorder=9)
        ax.plot([m[0] - 0.15, m[0] + 0.15], [m[1] + 0.15, m[1] - 0.15], color=CINN_L, lw=3, zorder=9)
    T(ax, P(9.45, 2.25)[0], P(9.45, 2.25)[1], "space-time and body-boundary\nsignals: cut off", 12.5, WATER_L, ha="center")
    T(ax, 4.45, 1.05, "Trigger: sympathetic + parasympathetic activation peaking together (the spillover)", 13, GOLD_L, ha="center")
    # right side: before / after
    bx = 12.95
    card(ax, 10.75, 4.35, 4.45, 3.05, ec=GOLD, a=0.6, fc="#0a0d26", z=2)
    T(ax, bx, 7.05, "Boundary drawn", 16, GOLD_L, ha="center", weight="bold")
    ax.add_patch(Circle((bx, 5.6), 0.7, fc=BODY, ec=GOLD_L, lw=2.6, zorder=6))
    T(ax, bx, 5.6, "I\n나", 15, GOLD_L, ha="center")
    T(ax, bx - 1.45, 6.4, "world", 12.5, MUTED, ha="center"); T(ax, bx + 1.5, 4.8, "world", 12.5, MUTED, ha="center")
    T(ax, bx, 4.6, "a solid frame: self | world", 12.5, IVORY, ha="center")
    arrow(ax, (bx, 4.25), (bx, 3.75), GOLD_L, lw=2.4, head=20)
    card(ax, 10.75, 0.6, 4.45, 3.05, ec=VIOLET, a=0.6, fc="#0a0d26", z=2)
    T(ax, bx, 3.3, "Boundary no longer drawn", 16, VIOLET, ha="center", weight="bold")
    rs = np.random.RandomState(7)
    glow(ax, bx, 2.05, 1.4, VIOLET, 0.8, z=4); glow(ax, bx, 2.05, 0.6, IVORY, 0.7, z=5)
    th = np.linspace(0, 2 * np.pi, 40, endpoint=False)
    ax.scatter(bx + 0.7 * np.cos(th) * rs.uniform(0.9, 1.9, 40), 2.05 + 0.7 * np.sin(th) * rs.uniform(0.9, 1.5, 40),
               s=rs.uniform(3, 14, 40), color=GOLD_L, alpha=0.7, lw=0, zorder=6)
    T(ax, bx, 0.98, "'I' dissolves into oneness with the\nuniverse / the void: Absolute Unitary\nBeing (AUB 절대적 단일 존재)", 12, IVORY, ha="center")
    footer(ax, "brain drawing is schematic")
    save(fig, "03_deafferentation_parietal.png")

# =============================================================== 04 rib purification circuit
def fig04():
    fig, ax = new_fig(4)
    title(ax, "Rib Purification: the Horizontal Chest Circuit",
          "갈비뼈 순화 · from the quoted post of 2026-11-18 KST, the practice the 'iron wall' grows out of")
    d = profile(ax, 0.25, 0.25, 1.0)
    c, lt = d["center"], d["lingtai"]
    for i, r in enumerate(np.linspace(0.25, 1.55, 9)):
        ax.add_patch(Circle(c, r, fill=False, ec=GOLD_L, lw=1.0, alpha=0.5 - i * 0.045, zorder=9))
    glow(ax, c[0], c[1], 0.45, GOLD_L, 1, z=10)
    ax.add_patch(Circle(c, 0.08, color=GOLD_L, zorder=11))
    ax.add_patch(Circle(lt, 0.09, color=CINN_L, zorder=11))
    ax.plot([c[0], lt[0]], [c[1], lt[1]], color=GOLD_L, lw=1.4, alpha=0.8, zorder=10)
    T(ax, 0.35, 5.95, "center (중심)\n1 cm above the solar\nplexus (명치), 5 cm in", 12.5, GOLD_L)
    ax.plot([1.6, c[0] - 0.08], [5.45, c[1] + 0.06], color=GOLD_L, lw=0.9, alpha=0.7, zorder=12)
    T(ax, lt[0] + 0.5, lt[1] + 0.85, "Lingtai\n영대 靈臺\n~T5", 13, CINN_L)
    ax.plot([lt[0] + 0.48, lt[0] + 0.08], [lt[1] + 0.55, lt[1] + 0.05], color=CINN_L, lw=0.9, alpha=0.7, zorder=12)
    T(ax, 2.6, 1.0, "side view (after the drawing in the Nov 18 post)", 12, MUTED, ha="center")
    # ---- top-down cross-section of the ribcage
    cx, cy, rx, ry = 9.1, 4.3, 2.35, 1.75
    T(ax, cx, 7.15, "ribcage seen from above: a cylinder", 17, GOLD_L, ha="center", weight="bold")
    T(ax, cx, 6.72, "front (chest) at the bottom, back (spine) at the top", 13, MUTED, ha="center")
    th = np.linspace(0, 2 * np.pi, 200)
    for lw, al in [(9, 0.06), (2, 0.8)]:
        ax.plot(cx + rx * np.cos(th), cy + ry * np.sin(th), color=GOLD, lw=lw, alpha=al, zorder=5)
    ax.add_patch(Ellipse((cx, cy), 2 * rx, 2 * ry, color=BODY, alpha=0.9, zorder=4))
    for k in np.linspace(0.55, 0.85, 3):
        ax.plot(cx + rx * k * np.cos(th), cy + ry * k * np.sin(th), color=GOLD, lw=0.6, alpha=0.18, zorder=5)
    C = (cx, cy - 0.85); L = (cx, cy + ry - 0.25)
    ax.add_patch(FancyBboxPatch((cx - 0.3, cy + ry - 0.15), 0.6, 0.45, boxstyle="round,pad=0,rounding_size=0.1",
                                fc=BODY, ec=GOLD_L, lw=1.4, zorder=7))
    T(ax, cx, cy + ry + 0.08, "T5", 10, GOLD_L, ha="center", z=8)
    glow(ax, *C, 0.45, GOLD_L, 1, z=8); ax.add_patch(Circle(C, 0.08, color=GOLD_L, zorder=9))
    ax.add_patch(Circle(L, 0.08, color=CINN_L, zorder=9))
    T(ax, C[0], C[1] - 0.4, "center", 12.5, GOLD_L, ha="center")
    T(ax, L[0] + 0.45, L[1] - 0.05, "Lingtai 영대", 12.5, CINN_L)
    T(ax, cx, cy - ry - 0.3, "FRONT (sternum)", 11.5, MUTED, ha="center")
    # inhale paths along both rib edges
    for sgn in (-1, 1):
        a = np.linspace(-np.pi / 2 - sgn * 0.0, np.pi / 2, 60) if sgn > 0 else np.linspace(-np.pi / 2, -3 * np.pi / 2, 60)
        k = 0.82
        xs = cx + rx * k * np.cos(a); ys = cy + ry * k * np.sin(a)
        xs = np.concatenate([[C[0]], xs]); ys = np.concatenate([[C[1]], ys])
        for lw, al in [(8, 0.12), (2.6, 1)]:
            ax.plot(xs[:-4], ys[:-4], color=WATER_L, lw=lw, alpha=al, zorder=10, solid_capstyle="round")
        arrow(ax, (xs[-6], ys[-6]), (L[0] + sgn * 0.12, L[1] + 0.02), WATER_L, lw=2.6, head=18, z=11)
        mid = len(xs) // 2
        arrow(ax, (xs[mid - 1], ys[mid - 1]), (xs[mid + 1], ys[mid + 1]), WATER_L, lw=0, head=20, z=11)
    # exhale: straight midline back to center
    for lw, al in [(8, 0.12), (2.6, 1)]:
        ax.plot([L[0], C[0]], [L[1] - 0.12, C[1] + 0.25], color=CINN_L, lw=lw, alpha=al, zorder=10)
    arrow(ax, (cx, cy + 0.2), (cx, C[1] + 0.12), CINN_L, lw=2.6, head=20, z=11)
    T(ax, cx + 0.15, cy + 0.55, "Om", 13, CINN_L, style="italic")
    # ---- explanation column
    x3 = 12.05
    card(ax, x3 - 0.2, 4.55, 4.0, 2.75, ec=WATER, a=0.7, fc="#0a0d26")
    T(ax, x3, 7.0, "Inhale 들숨", 16, WATER_L, weight="bold")
    T(ax, x3, 6.6, "As the ribcage widens, carry the\ncongestion and density of passion\nfrom the front center out along the\nouter edges of both rib walls, and\nscatter it to Lingtai at the back.\nOne clump spreads over a broad\nsurface and drains to the spine.", 12, IVORY, va="top")
    card(ax, x3 - 0.2, 1.65, 4.0, 2.25, ec=CINN, a=0.7, fc="#0a0d26")
    T(ax, x3, 3.6, "Exhale 날숨 (+ 'Om')", 16, CINN_L, weight="bold")
    T(ax, x3, 3.2, "Draw the qi gathered at Lingtai\n(dense sympathetic ganglia, where\npassion is stored) straight back\nto the center along the midline.\nRepeat the round trip.", 12, IVORY, va="top")
    T(ax, 9.1, 1.55, "Why not just push the breath down? If the chest is not\npurified first, pressing down causes bloating, or rising\nqi (상기 上氣) shooting to the head; the emotion gets\nlocked in the intercostal nerves and rib fascia.", 12, MUTED, ha="center")
    footer(ax, "Lingtai location and the 1 cm / 5 cm center as stated in the Nov 18 post")
    save(fig, "04_rib_purification_circuit.png")

# =============================================================== 05 iron wall vs collapse
def fig05():
    fig, ax = new_fig(5)
    title(ax, "The Iron Wall and Its Collapse", "철벽 → 철벽 붕괴 · how the spillover is felt in the chest during rib purification")
    for x0, stage in [(0.35, 3), (8.2, 4)]:
        w = 7.45
        card(ax, x0, 0.7, w, 6.75, ec=GOLD if stage == 3 else VIOLET, a=0.5, fc="#0a0d26", z=2)
        d = profile(ax, x0 + 0.1, 0.95, 0.75)
        c, mm, lt, low = d["center"], d["mingmen"], d["lingtai"], d["lower"]
        ax.add_patch(Circle(mm, 0.08, color=CINN_L, zorder=11))
        if stage == 3:
            T(ax, x0 + w / 2, 7.1, "3rd dhyāna (3선정 三禪定): the 'iron wall' 철벽", 17, GOLD_L, ha="center", weight="bold")
            # red from Mingmen up to chest
            path = catmull([mm, (mm[0] - 0.15, mm[1] + 0.7), (c[0] + 0.55, c[1] - 0.25), (c[0] + 0.12, c[1])], n=14, closed=False)
            for lw, al in [(9, 0.12), (3, 1)]:
                ax.plot(path[:-3, 0], path[:-3, 1], color=CINN_L, lw=lw, alpha=al, zorder=10)
            arrow(ax, tuple(path[-5]), (c[0] + 0.14, c[1]), CINN_L, lw=3, head=18, z=11)
            # blue ripples (Om / rib relaxation) from the front
            for r in (0.35, 0.6, 0.85):
                th = np.linspace(np.pi * 0.62, np.pi * 1.38, 40)
                ax.plot(c[0] - 0.08 + r * np.cos(th), c[1] + r * np.sin(th), color=WATER_L, lw=2, alpha=0.8 - r * 0.4, zorder=10)
            # the wall
            for lw, al in [(22, 0.10), (10, 0.25), (4, 1)]:
                ax.plot([c[0], c[0]], [c[1] - 0.6, c[1] + 0.6], color=GOLD_L, lw=lw, alpha=al, zorder=12, solid_capstyle="butt")
            for p in (d["prefrontal"], d["parietal"]):
                glow(ax, p[0], p[1], 0.32, GOLD_L, 0.9, z=12); ax.add_patch(Circle(p, 0.06, color=GOLD_L, zorder=13))
            T(ax, mm[0] + 0.3, mm[1] - 0.35, "Mingmen 명문 命門\nstrong arousal\n(sympathetic)", 12, CINN_L)
            T(ax, x0 + 0.2, c[1] + 1.35, "rib purification and\n'Om' vibration: relaxation\n(parasympathetic)", 12, WATER_L)
            T(ax, d["parietal"][0] + 0.45, d["parietal"][1] - 0.45, "prefrontal and parietal\nstill hold a subtle boundary\n(subtle intentional awareness\n미세적 유위각 微細的 有爲覺)", 11.5, GOLD_L)
            T(ax, x0 + 5.0, 3.65, "the two face off tautly\nin the center of the chest:\nspillover held at high\ndensity, felt as a solid wall", 12.5, IVORY)
            T(ax, x0 + w / 2, 1.15, "Unshaken by any emotion; it feels as if emotions have been cut off.", 13, GOLD_L, ha="center")
        else:
            T(ax, x0 + w / 2, 7.1, "4th dhyāna: the wall collapses (텅 빔)", 17, VIOLET, ha="center", weight="bold")
            glow(ax, c[0], c[1], 1.6, VIOLET, 0.9, z=9); glow(ax, c[0], c[1], 0.7, IVORY, 0.8, z=10)
            rs = np.random.RandomState(3)
            for _ in range(9):
                yy = c[1] + rs.uniform(-0.8, 0.8); xx = c[0] + rs.uniform(-0.9, 0.9); ang = rs.uniform(0, np.pi)
                ax.plot([xx - 0.12 * np.cos(ang), xx + 0.12 * np.cos(ang)], [yy - 0.12 * np.sin(ang), yy + 0.12 * np.sin(ang)],
                        color=GOLD_L, lw=3, alpha=0.5, zorder=11)
            for p in (d["prefrontal"], d["parietal"]):
                ax.add_patch(Circle(p, 0.06, fill=False, ec=MUTED, lw=1.2, ls=":", zorder=13))
            # heart-fire flows down by itself
            path = catmull([(c[0], c[1] - 0.25), (c[0] + 0.1, c[1] - 0.9), (low[0] + 0.05, low[1] + 0.35)], n=16, closed=False)
            ax.plot(path[:-2, 0], path[:-2, 1], color=GOLD_L, lw=2.4, ls=(0, (3, 3)), zorder=11)
            arrow(ax, tuple(path[-4]), (low[0], low[1] + 0.12), GOLD_L, lw=2.4, head=16, z=11)
            glow(ax, low[0], low[1], 0.4, CINN_L, 0.9, z=10); ax.add_patch(Circle(low, 0.07, color=CINN_L, zorder=12))
            T(ax, d["parietal"][0] + 0.45, d["parietal"][1] - 0.45, "the frame held by parietal and\nprefrontal lets go: sensory\ndeafferentation, a shift to\nnon-doing (무위 無爲)", 11.5, MUTED)
            T(ax, x0 + 4.95, 4.75, "empty spaciousness (no-mind 무심)\n+ clear wakefulness (sympathetic)\ncoexist without conflict\n→ the bright nature 밝은 성품", 12.5, IVORY)
            T(ax, x0 + 4.95, 3.25, "heart (cardiopulmonary rhythm in\nharmony) releases ANP:\n↓ cortisol  ↓ amygdala anxiety\n↑ oxytocin pathway", 12.5, WATER_L)
            T(ax, x0 + 4.95, 2.05, "heart-fire 心火 then flows down by\nitself to the lower dantian 下丹田 /\nYellow Court 黃庭 (Nov 18 post)", 12, CINN_L)
            T(ax, x0 + w / 2, 1.15, "Not dopamine pleasure from outside stimuli: a quiet, clear joy\n(선열 禪悅) welling up unconditionally inside the chest.", 12.5, VIOLET, ha="center")
    arrow(ax, (7.55, 4.3), (8.45, 4.3), GOLD_L, lw=3, head=24, z=15)
    T(ax, 8.0, 4.75, "past the\ncritical point", 11, GOLD_L, ha="center", z=15)
    footer(ax)
    save(fig, "05_iron_wall_and_collapse.png")

# =============================================================== 06 whole sequence
def fig06():
    fig, ax = new_fig(6)
    title(ax, "From Turbulent Emotion to the Unmoving Mind", "the whole arc of the two posts, step by step · 부동심 不動心")
    cards = [
        ("1", "Passion lodges in the chest", "격정 · 중단전 中丹田", CINN_L,
         "Emotion surges as heat and\nsympathetic arousal. Forcing it\ndown to the belly backfires:\nbloating or rising qi 上氣."),
        ("2", "Rib purification", "갈비뼈 순화", WATER_L,
         "Inhale: out along both rib edges\nto Lingtai 靈臺 (~T5). Exhale +\n'Om': straight back to center.\nTurbid qi 濁氣 washes out."),
        ("3", "Autonomic spillover", "자율신경 범람", GOLD_L,
         "The seesaw breaks: Mingmen's\narousal and the ribs' / Om's\nrelaxation both run at peak.\n(Still or dynamic route.)"),
        ("4", "3rd dhyāna · Iron wall", "3선정 · 철벽", GOLD_L,
         "A taut wall in mid-chest; a subtle\nboundary is still held. No emotion\nmoves you; emotions feel\ncut off."),
        ("5", "4th dhyāna · Collapse", "4선정 · 철벽 붕괴 · 텅 빔", VIOLET,
         "Past the critical point the\nparietal / prefrontal frame lets go\n(deafferentation, 무위 無爲).\nSelf-world boundary dissolves."),
        ("6", "Bright nature · heart-fire", "밝은 성품 · 선열 禪悅 · 心火", CINN_L,
         "Emptiness + clarity coexist. ANP,\n↓ cortisol, ↑ oxytocin: quiet joy.\nWarm heart-fire sinks by itself\nto the lower dantian 黃庭."),
    ]
    W, H = 4.55, 2.55
    pos = [(0.55, 4.45), (5.72, 4.45), (10.9, 4.45), (10.9, 1.05), (5.72, 1.05), (0.55, 1.05)]
    for (n, t1, t2, col, body), (x, y) in zip(cards, pos):
        card(ax, x, y, W, H, ec=col, a=0.85, fc="#0b0f2c")
        ax.add_patch(Circle((x + 0.45, y + H - 0.45), 0.28, fc="none", ec=col, lw=1.6, zorder=10))
        T(ax, x + 0.45, y + H - 0.45, n, 15, col, ha="center", weight="bold")
        T(ax, x + 0.9, y + H - 0.38, t1, 15.5, col, weight="bold")
        T(ax, x + 0.9, y + H - 0.8, t2, 12.5, MUTED)
        T(ax, x + 0.3, y + H - 1.2, body, 13, IVORY, va="top")
    for a, b in [(0, 1), (1, 2)]:
        arrow(ax, (pos[a][0] + W + 0.05, pos[a][1] + H / 2), (pos[b][0] - 0.05, pos[b][1] + H / 2), GOLD_L, lw=2.6, head=22)
    arrow(ax, (pos[2][0] + W / 2, pos[2][1] - 0.05), (pos[3][0] + W / 2, pos[3][1] + H + 0.05), GOLD_L, lw=2.6, head=22)
    for a, b in [(3, 4), (4, 5)]:
        arrow(ax, (pos[a][0] - 0.05, pos[a][1] + H / 2), (pos[b][0] + W + 0.05, pos[b][1] + H / 2), GOLD_L, lw=2.6, head=22)
    footer(ax, "steps 1-2 and the heart-fire in 6 come from the quoted Nov 18 post")
    save(fig, "06_whole_sequence.png")

if __name__ == "__main__":
    for f in (fig01, fig02, fig03, fig04, fig05, fig06):
        f()
