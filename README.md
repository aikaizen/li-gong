# Li Gong 理功

A living study of Daoist internal alchemy (內丹), centered on **取坎填離 (taking from Kan to fill Li)** and the "opening the top" practice. It has two parts:

1. **A knowledge graph** of the teachings posted by 마리지천 摩利支天 ([@z9_s8_y_9](https://x.com/z9_s8_y_9)), a Korean practitioner who writes on 내단, 신기문 (body-Qimen), trigram hand positions, and 수승화강.
2. **Practice videos** rendered entirely in Python (matplotlib, numpy audio, ffmpeg), with no AI image or video generators.

## Layout
| Path | What's there |
|---|---|
| `videos/five-gates/` | The Five Gates of Opening the Top: a 3:22 demo and a 16:13 real-time follow-along video, plus their source code and stills |
| `graph/scripts/` | Harvest, ingest and analysis scripts for the post archive |
| `graph/processed/` | Post index (metadata only), the IDs of truncated posts, and the posts that best match the Ligong passage (links with short excerpts) |
| `graph/PHASE1_REPORT.md` | Archive analysis, proposed graph schema, and the plan |
| `notes/concepts/`, `notes/practices/` | One markdown note per concept or practice (in progress) |

## Source of the core teaching
The Ligong / 취감전리 passage comes from [this post (2026-10-20)](https://x.com/z9_s8_y_9/status/2112365901437919440): pumping energy into the lower dantian alone is not effective. First open Li ☲ (palace 9), then connect Kan ☵ (palace 1).

## On source material
All teachings are credited to and linked back to the original author. The full post text and images are not republished here. The repo holds links, short excerpts, metadata, and our own synthesis and code.

## Status
- [x] Five Gates videos
- [x] Phase 1 harvest (3,710 posts) and analysis
- [ ] Full archive harvest (runs daily)
- [ ] Text extraction from the images on truncated posts
- [ ] Concept and claim extraction, and graph export (JSON/GraphML)
- [ ] Concept and practice notes
