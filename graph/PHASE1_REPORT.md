# Gurumaxx: @z9_s8_y_9 (마리지천摩利支天) knowledge graph: Phase 1 report
_As of 2026-10-30, 11:50 PM CDT_

## 1. Harvest status
- **Posts harvested: 3,710 non-retweet posts** (raw/posts.jsonl). Alongside them: 1,733 referenced/quoted posts (raw/referenced.jsonl) and 1,099 media records (1,097 photos, 2 videos; URLs only, nothing downloaded).
- **Date range covered:** 2021-03-05 to 2026-10-31 UTC. The archive is only partly covered; it's dense from 2025-06 onward.
- **Calls:** about 223 used this run. 777 of 1000 reads left today; the quota resets 2026-10-31 7:00 PM CDT.
- **Method:** `search_posts_all` with `from:z9_s8_y_9 -is:retweet`, sort_order recency, 25 posts per page. About 20 date-window chains run in parallel, and each chain pages backward (newest first) from its own window. Cursors live in `state.json` and ingest is dedupe-safe (`scripts/run.sh`). A mirror is kept at /home/box/gurumaxx_backup/.
- **Gotcha:** if you call without start_time, only the last ~30 days come back. Every chain needs an explicit window.
- **Priority (user steer: newest first):** the 2026 chains run first (s01b/c/d, s02/b/c, s03/b/c), then the late-2025 chains (s04/b/c, s05b/c), then 2025 H1 and 2024. The 2021–2023 chain (s09) goes last; it's mostly sparse Bitcoin and trading content.
- **Estimate to finish:** the profile shows 45k tweets, but most of those are retweets. About 15–20k originals and replies remain, mostly from 2025-06 onward, at 25–50 posts a day. At about 800 calls (≈20k posts) a day, **that's roughly 1–2 more daily quotas.**
- **Known gap:** about 77+ long posts come back truncated with a self-link. `note_tweet` is missing even from `get_posts_by_id` (checked with 2114204012811792440). The rest of the text is often in the attached images (most teaching posts carry 1–3 info-graphic photos). Phase 2 needs OCR of the image URLs, or a logged-in browser read.

## 2. Sample analysis (n=3,710, all harvested)
| class | share | median chars | has media | long-form (note_tweet) |
|---|---|---|---|---|
| social_reply (greetings, short replies to followers) | 49% | 36 | 2% | 0% |
| **teaching** (neidan / 기문 / breath / trigram vocabulary, ≥60 chars) | **19%** | 184 | 58% | 33% |
| essay_other (psychology, philosophy, spirituality essays) | 15% | 185 | 62% | 24% |
| chatter | 12% | 85 | 36% | 0% |
| market (BTC, MSTR, bills, often with 일진 timing) | 5% | 114 | 73% | 12% |

- **Teaching density is rising.** Teaching posts were 130 in 2025-12 and 62 in 2026-10 (so far), up from about 15 a month in early 2026. Oct 2026 is the 신기문 / 내단주역괘 (hexagram-for-practice) period.
- **Threads:** the account barely builds explicit self-threads (219 self-replies; the longest thread is 9 posts). Its main linking device is **quote-chaining** (392 quotes): each new teaching post quotes the previous one, as in 2113802659836891366 → 2114204012811792440. The graph should follow `referenced_tweets.quoted` as a "builds_on" edge.
- **Topic eras:**
  - 2024: Bitcoin, 종교성, 정신공학, 보이차.
  - 2025 H1: 단전호흡, 축기, 얼/내관, PC muscle, 미주신경 breathing.
  - 2025 H2: crura/횡격막 breathing, 쿤달리니, T6, 용문남파 소주천, 연정화기.
  - 2025-12: talismans (부적), 주술, 점술, 洗心, 四寅斬邪, 乙丑靈氣.
  - 2026: 신기문 (body 奇門遁甲), hand mudras per trigram, daily 일진 (e.g. 정축일), hexagrams as practice (뇌택귀매, 풍택중부, 택뢰수), Tibetan (자 라훌라, 생법궁), 보이차 노차.
- **Top teaching terms:** 기운, 호흡, 크루라, 횡격막, 에너지, 척추, 쿤달리니, 프라나, 정화(丁火), 점술/부적/주술, 洗心, 四寅斬邪, 視之不見/聽之不聞, 乙丑靈氣, 심장, 단계, 억지로 (a recurring "don't force" motif).

## 3. Ligong / 감수인 passage matches
**The source passage was found.** It's the account's own post:
- ⭐ **2026-10-20 · https://x.com/z9_s8_y_9/status/2112365901437919440** (189 likes, 2 images).
  - "하단전에 에너지를 때려 넣는 방법은 효과적이지 않습니다… 처음에 하단전인 감궁만 누르면, 위쪽 통로가 열려 있지 않아 압력이 아래쪽(회음·생식기)으로 터져 나갑니다… 먼저 9번 이궁(☲: 검지·약지를 붙이고 가운데 중지를 활짝 펴서 비움)을 활성화… 1번 감궁(☵: 중지를 붙임)을 연결하는 순간… 진양(⚊)이… 이궁(☲)의 빈자리를 향해… 빨려 올라가 합일(취감전리 取坎填離)".
  - It quotes 2111253190553559456 (생법궁 / Tibetan 하단전 triangle, 2026-10-17).

Other strong matches, newest first:
- 2026-10-29 https://x.com/z9_s8_y_9/status/2115673907097375154: 택뢰수 ䷐, 심수기 / 물망물조 ("don't force").
- 2026-10-25 https://x.com/z9_s8_y_9/status/2114204012811792440: 선천 건곤 → 후천 離☲/坎☵, 수락화염 (water falls, fire flares). This is the theory behind 取坎填離 (truncated).
- 2026-10-24 https://x.com/z9_s8_y_9/status/2113802659836891366: 진기 is not made by forcing awareness into one point of the lower belly (quoted by the post above).
- 2026-10-20 https://x.com/z9_s8_y_9/status/2112439969352749071: "[안전하게 하단전에 기운을 기르는 방법]", 진유합금, 수승화강 = 감리 교류. It's the follow-up that quotes the ⭐ post. Near-duplicate: 2112437772237877746.
- 2026-10-20 https://x.com/z9_s8_y_9/status/2112349557434786024: 누정, 건궁☰ "battery", don't plug the bottom hole.
- 2026-10-19 https://x.com/z9_s8_y_9/status/2112036566436806775: 신기상응, 상단전 神 ↔ 하단전 氣, 풍택중부 문화(文火).
- 2025-10-22 https://x.com/z9_s8_y_9/status/1980857088613212580: 용문남파 소주천, "억지로 밀어 넣은 숨" (forced breath) fails.
- 2025-10-23 https://x.com/z9_s8_y_9/status/1981377238487748645: 소주천 step 1, 회음–척추–백회.
- 2025-08-24 https://x.com/z9_s8_y_9/status/1959533234062332266: 수승화강 heat that rises by itself, not forced.
- 2025-02-25 https://x.com/z9_s8_y_9/status/1894360419638415678: 단전호흡 without forcing, PC muscle.

The full scored list is in `processed/ligong_matches.json` (40 hits).
- **Lineage note:** the vocabulary (감궁/이궁 numbered as 洛書 palaces 1/9, 신기문, 취감전리) is this author's own 신기문 synthesis. It's built on 기문둔갑 plus 내단 (용문파 / 전진교 references), so the attribution should go to this account rather than a separate Korean 선도 text.

## 4. Knowledge-graph schema (v0)
**Nodes:**
- **Post**: id, url, date, text, class, media_urls, likes, lang.
- **Concept**: e.g. 취감전리, 수승화강, 누정, 진공흡입력; ko/hanja/en labels, aliases.
- **Practice/Exercise**: steps, body_parts, mudra, breath_pattern, cautions, video_id.
- **Trigram**: ☰…☷ with palace number (洛書 1–9), finger mapping (e.g. ☲ = 검지+약지 붙임, 중지 펴기).
- **Hexagram**: 64, e.g. 택뢰수 ䷐.
- **Stem/Branch**: 천간 / 지지 / 60갑자 day, e.g. 정축.
- **BodyLocus**: 하단전, 회음, 백회, T6, crura.
- **Text/Source**: 주역 계사전, 용문파, Freud, Mindell, 김주환.
- **Claim**: an atomic assertion with stance, e.g. "하단전-first practice causes 누정 and arrogance".

**Edges:**
- explains (Post→Concept/Practice)
- asserts (Post→Claim)
- about (Claim→Concept)
- prerequisite_of (Practice→Practice, e.g. 이궁 activation → 감궁 connection)
- contrasts_with (Concept↔Concept, e.g. 하단전-pumping vs 취감전리)
- uses_trigram / uses_hexagram / located_at / timed_by (Practice→Trigram / Hexagram / BodyLocus / Stem-Branch)
- cites (Post→Text/Source)
- builds_on (Post→quoted Post)
- part_of_thread (Post→root via conversation_id)
- demonstrated_in (Practice→Video)

Every Concept, Practice and Claim keeps `evidence: [post_id…]` for provenance.

## 5. Korean-aware relevance classifier
1. **Rule pre-filter** (done; `scripts/analyze.py`). Strip leading @mentions; flag social replies under 80 chars. Match a domain lexicon in hangul, hanja and symbols: ☰–☷, ䷀–䷿, `[갑…계][자…해]일`, 단전, 감궁, 이궁, 기문, 크루라 and so on. Match a market lexicon: BTC, MSTR, 법안.
2. **LLM pass** on the posts that survive: about 50% of the corpus, run on teaching + essay + market. It labels {teaching, practice-instruction, theory, market-timing, essay, social}. It also extracts concepts, trigrams, practices and claims as JSON against the schema, normalizing hanja ↔ hangul aliases (取坎填離 = 취감전리).
3. **Images:** OCR the photo URLs (Korean + hanja). This is needed for truncated posts and info-graphics.
4. **Quality check:** a hand-labelled set of 200, then precision and recall per class.

## 6. Repo layout
```
gurumaxx/
  raw/            posts.jsonl referenced.jsonl media.jsonl pages/   (append-only)
  state.json      harvest cursors
  processed/      post_index.json  graph.json  graph.graphml  ligong_matches.json
  notes/concepts/<slug>.md   (one per Concept: def, hanja, claims, evidence links)
  notes/practices/<slug>.md  (steps, mudra, cautions, linked video)
  videos/         kinetic/ li_gong_five_gates/ … (Python-rendered practice videos)
  scripts/        ingest.py ingest_auto.py run.sh analyze.py ligong_match.py (+ build_graph.py, ocr.py next)
  PHASE1_REPORT.md
```
