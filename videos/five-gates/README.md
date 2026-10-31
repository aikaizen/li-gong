# Li Gong · Opening the Top: Five Gates animation

Everything in these videos is drawn in Python with matplotlib. ffmpeg encodes the frames into MP4. The audio is synthesized with numpy. There are no image assets or AI generators, so every shape, color, and motion is defined in the code.

## Files
- `five_gates.py`: the 3:22 demo. Some sections are sped up.
- `five_gates_realtime.py`: the 16:13 real-time follow-along session, with breaths at 4 s in and 6 s out. It's a standalone script: it started as a copy of the demo, then its timing and cues were reworked.
- `stills/`: reference frames taken from both rendered videos.

## Requirements
- Python 3.10+ with `numpy` and `matplotlib` (built with numpy 2.x and matplotlib 3.11).
- `ffmpeg` on the PATH.
- Fonts: Noto Serif CJK TC for the Chinese text. The scripts load it from `/usr/share/fonts/opentype/noto/NotoSerifCJK-*.ttc`, which is the Linux path, so change it at the top of each script if you're on Mac or Windows. The scripts also use DejaVu Sans and Noto Sans Symbols for the trigram glyphs (☰ ☷ ☵ ☲).

## Running
```
python3 five_gates.py                    # full render
python3 five_gates.py --still 30,70      # preview frames at given seconds
python3 five_gates_realtime.py out.mp4   # real-time session
```
The default output and temp paths are hard-coded to `/workspace/kinetic/`, so search for that path and change it.
Rendering runs in parallel across CPU cores. On 6 cores the demo takes about 3.5 minutes and the real-time version about 15.
Video output is 1280x720, 30 fps, H.264, with AAC audio.

## How it's structured
- **`SEGMENTS`**: a list of (name, seconds). This list sets the whole timeline.
- **A per-segment draw function**: given the time t, it draws that segment's frame.
- **Small helpers**: easing, glow, text, the meditator figure, the hand seal, the trigrams, and the breath ring.
- **Audio**: built separately as a WAV whose timing matches the visual breath cycle, then muxed in by ffmpeg.
- **Palette**: dark indigo background, gold (yang/light), cinnabar (Li/fire), blue (Kan/water).

## Content (what's being animated)
Five gates of Opening the Top (取坎填離, taking from Kan to fill Li):
1. 放胸 Soften the chest: 36 breaths
2. 離印 Li seal (index and ring fingers together, middle finger spread): 9 rounds
3. 心火下降 Heart fire descends to the solar plexus, never below the navel: 9 breaths
4. 頂空 Clear crown, tongue to palate: 3–5 min
5. 取坎填離 Join Kan to Li (middle finger closes, soft perineum lift): 3 rounds
Then 收功 closing (palms on the lower belly, 9 breaths, attention to the soles), and a warning card.

## Where a designer could take it further
- **Meditator figure**: it's a flat stylized outline. A proper illustrated or anatomical figure would help most.
- **Hand seal**: the drawing is a simple sketch.
- **Transitions**: segments fade through the background color.
- **Typography and layout**: these are functional, not polished.
- **Audio**: it's procedural and its loudness hasn't been tested.
