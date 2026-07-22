# The Flow Report — Daily Production Template

**Format:** AI news anchor video · 15 seconds · 1080p · 16:9  
**Purpose:** City-by-city Google Ads cost transparency · Drives to Flow Program  
**Cadence:** Daily · Alternate Marcus (Mon/Wed/Fri) and Claire (Tue/Thu)

---

## Locked Assets — Never Regenerate

| Asset | Higgsfield Job ID | Notes |
|---|---|---|
| Marcus Hale (anchor image) | `cbee5198-a577-4d38-b4dc-6bf9f297d5fc` | Male, navy suit, news desk |
| Claire Bennett (anchor image) | `f9453360-5a14-4b40-a371-a63b81fa60d6` | Female, charcoal blazer, same set |
| Brooks voice (male) | `c2acff45-84b2-4974-892d-89fa2d4e5598` | Use for Marcus episodes |
| Sloane voice (female) | `b57b22a0-f287-405b-bc82-6f08f5e6bb1f` | Use for Claire episodes |

---

## Step 1 — Get City CPC Data (2 min)

Google Keyword Planner → search "sell my house fast [CITY]" → note the top-of-page CPC bid.

**Reference benchmarks (use if Keyword Planner unavailable):**
- Nationwide average: $3–5/click
- Competitive markets (Dallas, Houston, Phoenix, Atlanta): $4–6/click
- Top-tier markets (LA, NYC, Miami): $6–10/click

Fill in:
- `[CITY]` = target market name
- `[CPC]` = dollar amount per click (e.g., "four dollars", "thirty dollars")
- `[CPC x 8]` = CPC multiplied by 8 (low end of lead cost)
- `[CPC x 15]` = CPC multiplied by 15 (high end of lead cost)

---

## Step 2 — Fill the Script

### Full Episode Script (~40 seconds):
```
Good morning [CITY] wholesalers.

If you're running Google ads right now to find motivated sellers 
in [CITY], your cost per click is sitting around [CPC].

[CPC]. Gone. Every single click.

How many of those clicks before your phone rings? 
Industry average — eight to fifteen clicks per lead.
That's [CPC x 8] to [CPC x 15] before a single motivated 
seller picks up the phone.

And that's before the agency charging you fifteen hundred 
a month to manage it.

Here's the thing — we're already running in [CITY].
The ads are live. The flow is on.

You don't build the machine. You lease the output.

DM me, call, or text — and I'll tell you exactly what 
a spot costs in [CITY].
```

### Hook-Only Script (~15-19 seconds, for Seedance audio sync):
```
Good morning [CITY] wholesalers. If you're running Google ads 
right now to find motivated sellers in [CITY], your cost per 
click is sitting around [CPC]. [CPC]. Gone. Every single click. 
That's the cost before a single motivated seller even picks up 
the phone.
```

> Use the **Hook-Only Script** for Seedance audio input (matches 15-second video).  
> Use the **Full Episode Script** for the Blotato post caption and any extended audio overlay.

---

## Step 3 — Generate Audio (seed_audio · ~2 min)

**Tool:** `generate_audio` via Higgsfield  
**Model:** `seed_audio`  
**Voice ID:** `c2acff45-84b2-4974-892d-89fa2d4e5598` (Brooks · preset · male) or `b57b22a0-f287-405b-bc82-6f08f5e6bb1f` (Sloane · preset · female) for Claire episodes  
**Prompt:** Paste the Hook-Only Script with [CITY] and [CPC] filled in  
**Critical:** Keep the audio clip under 15 seconds — Seedance 2.0 has a 15 sec max. The Hook-Only script should yield 12–14 sec at Brooks/Sloane's pace.

Save the returned job ID — you'll need it in Step 4.

---

## Step 4 — Generate Video (seedance_2_0 · ~20-30 min)

**Tool:** `generate_video` via Higgsfield  
**Model:** `seedance_2_0`  
**Parameters:**
```
aspect_ratio: 16:9
duration: 15
resolution: 1080p
mode: std
generate_audio: false
medias:
  - value: [Marcus OR Claire image job ID]
    role: start_image
  - value: [audio job ID from Step 3]
    role: audio_references
```

**Anchor rotation:**
- Monday / Wednesday / Friday → Marcus (`cbee5198`)
- Tuesday / Thursday → Claire (`f9453360`)

> Seedance 2.0 renders in 20–30 minutes at 1080p. Start the render, then write your caption while it processes.

---

## Step 5 — Write Caption

```
Good morning [CITY] wholesalers. 🎙

Your cost per click to advertise on Google right now: $[CPC].

Every. Single. Click.

Industry average: 8–15 clicks before your phone rings.
That's $[CPC x 8] to $[CPC x 15] per lead.
Then add $1,500/month in agency fees on top.

We're already running in [CITY].
The ads are live. The flow is on.

You don't build the machine. You lease the output.

👉 DM CALLS
```

---

## Step 6 — Post via Blotato (after GO from Victor)

**Platforms:** Facebook · Instagram · LinkedIn · TikTok  
**Account IDs:**

| Platform | accountId | pageId |
|---|---|---|
| Facebook (RMP Marketing) | `40929` | `102243868616735` |
| Instagram (@rmpmarketing77) | `58461` | — |
| LinkedIn company (RMP Marketing) | `28392` | `37559202` |
| TikTok (@rmpmarket1) | `51447` | — |

**Scheduling:** Post at 8:00 AM local time in the target city  
(Dallas = 2 PM UTC, Phoenix = 3 PM UTC, Miami = 12 PM UTC)

---

## Daily Checklist

- [ ] Pull CPC from Keyword Planner for today's city
- [ ] Fill in Hook-Only script
- [ ] Generate audio (seed_audio · Brooks)
- [ ] Generate video (seedance_2_0 · matched anchor)
- [ ] Write caption
- [ ] Send to #rmp-social for GO
- [ ] Schedule via Blotato at city local 8 AM

---

## ANGLE 11 — The Flow Report: Duo Format + Trading Floor Intro

**Concept:** 5-part episode: cinematic keyword trading floor intro → AI anchor duo open → human host live data → AI anchor close.

The hook: keywords are commodities, just like stocks. The trading floor makes that analogy visceral before a single anchor speaks.

### Structure
| Part | Who | What | Length |
|---|---|---|---|
| 0A — Trading Floor Wide | B-roll (AI) | Busy trading floor, keyword tickers scrolling on screen | ~5 sec |
| 0B — Trader Close-Up | B-roll (AI) | Trader on phone making "keyword deal" energy | ~5 sec |
| 1A — Marcus Open | Marcus (AI) | Introduces himself, hands to Claire | ~5 sec |
| 1B — Claire Open | Claire (AI) | Hands off to "our host" | ~4 sec |
| 2 — Live Data | Victor (human) | Screen: live Google Keyword Planner CPC | ~13 sec |
| 3 — Close | Marcus (AI) | Delivers the math and CTA, lip-synced via Seedance | ~10 sec |

### Why This Works
- The trading floor intro establishes the analogy: keywords = commodities, CPC = stock price
- Keyword tickers make that concrete before a single anchor speaks
- Marcus VO narrates over the floor footage — heard before seen (cinematic)
- Victor's human segment adds credibility — real screen, real number, real person
- Competitors can't replicate this without both AI toolchain + human authenticity
- Perfect for TikTok, Reels, YouTube Shorts — stops the scroll in the first second

### Trading Floor Script — Marcus VO (Part 0)
```
Sell my house fast. Stop foreclosure. Cash for houses.
These aren't stock symbols. They're keywords —
and just like stocks, the price is live every single day.
```
Duration: ~14 sec · Voice: Brooks · Plays over Part 0A + 0B + bleeds 4 sec into Part 1A

### Keyword Ticker Overlays (add in CapCut over Part 0A and 0B)

**Top title card** (0-4 sec, fade in/out):
```
KEYWORD TRADING FLOOR
DAILY MARKET UPDATE — REAL ESTATE DIVISION
```
Style: white bold · red left accent bar · dark semi-transparent background

**Bottom scrolling ticker** (full 0A + 0B duration, left → right scroll):
```
SELL MY HOUSE FAST $30 ↑  •  STOP FORECLOSURE $38 ↑↑  •  CASH FOR HOUSES $26 ↑  •  WE BUY HOUSES $22 →  •  BEHIND ON MORTGAGE $34 ↑  •  PRE-FORECLOSURE HELP $28 ↑  •  MOTIVATED SELLER LEADS $18 →  •  OFF MARKET PROPERTIES $11 ↑  •  WHOLESALE REAL ESTATE $9 ↑  •  PROBATE REAL ESTATE $8.50 ↑  •  TAX LIEN PROPERTIES $10 →  •  TIRED LANDLORD $12 ↑  •  INHERITED PROPERTY BUYERS $16 ↑  •  DISTRESSED PROPERTY $9.50 ↑  •  CASH HOME BUYERS $24 ↑
```
Style: white · dark red `#8B0000` background strip · full width · bottom of frame

**Second ticker row** (offset, starts 2 sec in):
```
DALLAS TX $30/CLICK  •  HOUSTON TX $28  •  PHOENIX AZ $24  •  MIAMI FL $35  •  LA CA $42  •  NYC NY $48  •  ATLANTA GA $22  •  CHICAGO IL $26  •  DENVER CO $21  •  CHARLOTTE NC $19  •  NASHVILLE TN $20
```

**Full keyword reference list for the board (use on any graphic assets):**

MOTIVATED SELLER — HIGH DEMAND (red)
- SELL MY HOUSE FAST · $28–45/click · EXTREME competition
- STOP FORECLOSURE · $32–55/click · EXTREME
- FACING FORECLOSURE · $29–50/click · EXTREME
- AVOID FORECLOSURE · $30–52/click · EXTREME
- BEHIND ON MORTGAGE · $22–40/click · HIGH
- PRE-FORECLOSURE HELP · $18–38/click · HIGH
- CASH FOR HOUSES · $24–42/click · HIGH
- WE BUY HOUSES · $20–38/click · HIGH
- SELL HOUSE AS IS · $18–32/click · HIGH
- CASH HOME BUYERS · $20–35/click · HIGH
- HOME BUYERS NEAR ME · $22–38/click · HIGH

WHOLESALE / INVESTOR (green)
- WHOLESALE REAL ESTATE · $8–14/click · MED
- OFF MARKET PROPERTIES · $10–18/click · MED
- DISTRESSED PROPERTY · $8–16/click · MED
- ABSENTEE OWNER HOMES · $10–20/click · MED
- PROBATE REAL ESTATE · $8–18/click · LOW
- TAX LIEN PROPERTIES · $10–22/click · LOW
- TIRED LANDLORD · $8–15/click · MED
- VACANT PROPERTY BUYER · $10–18/click · MED
- INHERITED PROPERTY BUYERS · $14–25/click · MED
- DIVORCE HOME SALE · $12–24/click · MED
- SELL RENTAL PROPERTY FAST · $15–30/click · MED
- FIRE DAMAGED HOMES · $8–18/click · LOW
- ASSIGNMENT OF CONTRACT · $6–12/click · LOW
- SUBJECT TO REAL ESTATE · $6–15/click · LOW
- SELLER FINANCING HOMES · $8–18/click · LOW
- FIX AND FLIP HOMES · $10–20/click · MED
- VIRTUAL WHOLESALING · $5–12/click · LOW
- SKIP TRACING SERVICES · $4–10/click · LOW
- DRIVING FOR DOLLARS APP · $3–8/click · LOW
- DIRECT MAIL REAL ESTATE · $3–8/click · LOW
- CREATIVE FINANCING HOMES · $7–15/click · LOW
- BRRRR STRATEGY HOMES · $5–12/click · LOW
- LEASE OPTION HOMES · $8–18/click · LOW
- OWNER FINANCE HOMES · $9–22/click · MED
- LAND CONTRACT HOMES · $6–14/click · LOW

MARKET SUPPORT (blue)
- REO PROPERTIES · $12–22/click · MED
- SHORT SALE HOMES · $14–26/click · MED
- BANK OWNED HOMES · $12–24/click · MED
- FORECLOSURE LISTINGS · $15–28/click · MED
- MOTIVATED SELLER LEADS · $16–28/click · HIGH
- REAL ESTATE INVESTOR LEADS · $12–22/click · MED

### Opening Script (AI Anchors — Part 1)
```
MARCUS: Good morning, Claire.
CLAIRE: Good morning, Marcus. Big question today — what's it actually 
        costing wholesalers to advertise in [CITY] right now?
MARCUS: Let's check in with our host.
```

### Human Host Script (Victor — Part 2)
Victor faces camera, screen visible behind him or in screen-share overlay:
```
"Hey — I just pulled this up live in Google Keyword Planner.
Right now, if you're bidding on 'sell my house fast [CITY]'...
you're paying [CPC] per click. Every. Single. Click.
Back to you."
```

### Close Script (AI Anchor — Part 3)
Must be ≤15 seconds for Seedance 2.0. Use this tight version (fills ~10-12 sec):
```
[CPC]. Per click. Gone. Every single click.
We're already in [CITY]. The ads are live.
The flow is on. You lease the output. DM CALLS.
```

### Production Flow (Full Episode)

**Step 1 — Generate trading floor b-roll (Kling 3.0, run in parallel):**
- Part 0A: wide trading floor · "Cinematic wide-angle busy Wall Street trading floor, professionals on phones, monitors on walls, camera pushing in, financial district atmosphere"
- Part 0B: trader close-up · "Confident financial professional on phone at desk, monitors in background, busy trading floor visible, cinematic bokeh"
- Both: `kling3_0` · `9:16` · `5 sec`

**Step 2 — Generate all audio (seed_audio, run in parallel):**
- Part 0 VO: Marcus · Brooks voice · Trading floor script (~14 sec)
- Part 1A: Marcus · Brooks voice · "Good morning. I'm Marcus Hale. [Claire] — what are wholesalers paying to advertise in [CITY] today?" (~6 sec)
- Part 1B: Claire · Sloane voice · "Let's find out. Here's our host with today's number." (~4 sec)
- Part 3: Marcus · Brooks voice · Tight close script · ≤15 sec

**Step 3 — Generate anchor videos (run in parallel):**
- Part 1A video: `kling3_0` · Marcus image · `9:16` · 5 sec
- Part 1B video: `kling3_0` · Claire image · `9:16` · 5 sec
- Part 3 video: `seedance_2_0` · Marcus image + Part 3 audio · `9:16` · match audio duration

**Step 4 — Victor records Part 2 (~13 sec):**
- Phone vertical (9:16), tripod or propped
- Google Keyword Planner open on screen behind you (or screen-share overlay on desktop)
- Script: "Hey — I just pulled this live. Right now, bidding on 'sell my house fast [CITY]' — you're paying [CPC] per click. Every. Single. Click. Back to you."
- Keep it 12–13 sec. Eyes to camera, not the screen.

**Step 5 — CapCut assembly:**
1. New project · 9:16 · 1080×1920 · 30fps
2. Timeline order (hard cuts, no transitions):
   `Part0A.mp4` → `Part0B.mp4` → `Part1A.mp4` → `Part1B.mp4` → `victor.mp4` → `Part3.mp4`
3. Mute ALL Kling video tracks (0A, 0B, 1A, 1B) — Volume → 0. Part 3 Seedance keeps its audio.
4. Add audio layer: `Part0_VO.wav` at 0:00 (runs ~14 sec, covers 0A + 0B + first 4 sec of 1A establishing shot)
5. Add `Part1A_audio.wav` starting at ~14 sec
6. Add `Part1B_audio.wav` starting at ~20 sec
7. Victor's clip stays at full volume
8. Text overlays for trading floor (see Keyword Ticker Overlays section above):
   - Top title card (0–4 sec)
   - Bottom scrolling ticker (0–10 sec)
   - Second city ticker (2–10 sec)
9. Lower-thirds: "MARCUS HALE" (Part 1A) · "CLAIRE BENNETT" (Part 1B) · "LIVE DATA · GOOGLE KEYWORD PLANNER" (Victor)
10. Auto-captions → English → clean up "$[CPC]" and "DM CALLS"
11. Export: 1080p · 30fps · H.264

**Step 6 — Post:** Send to #rmp-social for GO, then schedule via Blotato at city local 8 AM

### On Automating the CPC Data
**Short answer: semi-automatable, not fully.**

Options ranked by effort vs. accuracy:
- **Victor's screen recording (recommended):** Most authentic. Real proof. Takes 60 seconds. The human element is the point — it's not a bug, it's a feature.
- **Google Ads API:** Fully automatable if Victor has a Google Ads account. `KeywordPlanIdeaService` returns suggested CPC bids by keyword + location. Setup takes ~2 hours once. Returns daily data on demand.
- **SEMrush/Ahrefs API:** Third-party CPC estimates. Accurate but not real-time. Good fallback if no Google Ads account.
- **Google Keyword Planner (manual):** Free, accurate, 2 minutes per city. Best option until volume justifies API setup.

**Verdict:** For now, Victor records the screen segment live. It's faster to set up, more credible on camera, and creates a format competitors can't replicate with pure AI. If daily volume hits 5+ cities/day, wire up the Google Ads API to pull CPC automatically and inject it into the script template.

---

## City Queue (fill in as you go)

| Date | City | CPC | Anchor | Status |
|---|---|---|---|---|
| 2026-07-22 | Dallas, TX | $30 | Marcus | ✅ All AI assets done · Victor records Part 2 · Assemble in CapCut |
| | | | | |
| | | | | |
