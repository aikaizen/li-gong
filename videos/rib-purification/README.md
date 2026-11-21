# Rib Purification (갈비뼈 순화) → the unmoving mind (不動心): a real-time follow-along video

**[rib_purification.mp4](rib_purification.mp4)**: 5:44, 1280×720, H.264 + AAC.

This is a follow-along session of two posts by 마리지천摩利支天 ([@z9_s8_y_9](https://x.com/z9_s8_y_9)):
- **[2026-11-18 KST](https://x.com/z9_s8_y_9/status/2123057544998568036): rib purification.** The horizontal chest circuit. On the in-breath, carry the chest's congestion out along both rib edges to Lingtai (靈臺, around T5). On the out-breath, sound "Om" and draw it straight back to the center (1 cm above the solar plexus, 5 cm in). Turbid qi (濁氣) washes out, and heart-fire (心火) then sinks by itself to the lower dantian / Yellow Court (黃庭).
- **[2026-11-21 KST](https://x.com/z9_s8_y_9/status/2124124210348097894): how to cultivate the unmoving mind.** The 3rd-dhyāna "iron wall" forms where Mingmen's arousal meets the relaxation of the ribs and Om. In the 4th dhyāna the wall collapses into empty, lucid space: the bright nature (밝은 성품).

Translations are in [graph/translated/2026/11](../../graph/translated/2026/11/), and still diagrams in [notes/diagrams/2026-11-21-unmoving-mind](../../notes/diagrams/2026-11-21-unmoving-mind/README.md).

Everything is made in Python. matplotlib draws every frame, numpy synthesises the audio, and ffmpeg encodes it. No image or video generators were used. The style and render pipeline follow `videos/five-gates`.

## Timestamps

| Time | Section |
|---|---|
| 0:00 | Intro: 갈비뼈 순화 · Rib Purification · 不動心 |
| 0:12 | Find the two points (side view and a top-down view of the ribcage): the center (1 cm above the solar plexus, 5 cm in), Lingtai 靈臺 (~T5, his placement), and the circuit |
| 0:36 | Breathing starts. The first bell rings at **0:40** |
| 0:40 – 4:16 | **18 breaths in real time:** 5 s inhale, light flowing from the center out along both rib edges to Lingtai, then 7 s exhale with "Om", flowing straight back along the midline to the center. Dark turbid-qi particles wash out over the cycles, and the chest center turns from dull red heat to clear gold. |
| 4:16 | Rest (breathe naturally) |
| 4:22 | **3rd dhyāna: the iron wall** (Mingmen's arousal vs. the relaxation of the ribs and Om; prefrontal and parietal still hold a subtle boundary) |
| 4:56 | **The wall collapses** (struck bell) |
| 4:59 | **4th dhyāna: the bright nature** 밝은 성품 (emptiness + clear wakefulness; ANP, cortisol and amygdala anxiety down, oxytocin up; 선열 禪悅) |
| 5:12 | **Heart-fire 心火 sinks by itself** to the lower dantian / Yellow Court 黃庭 |
| 5:26 | Close: 不動心 |

## Audio

Every sound is synthesised in numpy:
- **Inhale:** a soft tone rising a fourth, with a breath swell.
- **Exhale:** a low "Om"-like hum at 98 Hz, its harmonic stack filtered so the vowel moves from "o" to a closed "m".
- **Bells and gongs:** a gentle bell at the start of each breath, and a gong at each section change.
- **Iron wall:** two close tones beat against each other while the wall forms.
- **Collapse and after:** a struck bell at the collapse, a soft pad for the bright space, and a descending warm tone as the heart-fire sinks.

## Files

- `rib_purification.py` makes the video. Run `python3 rib_purification.py` for the full video (set the number of worker processes with `WORKERS=7`), or `python3 rib_purification.py --still 44,47,297` to save single frames to `stills/`.
- `stills/` holds sample frames.
