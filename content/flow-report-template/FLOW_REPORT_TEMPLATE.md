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

## ANGLE 11 — The Flow Report: Duo Format (AI Anchors + Human Host)

**Concept:** Upgrade the solo anchor episodes into a 3-part duo/duet format.

### Structure
| Part | Who | What | Length |
|---|---|---|---|
| 1 — Open | Marcus + Claire (AI) | Greet each other, hand off to "our human host" | ~5 sec |
| 2 — Live Data | Victor (human) | Screen recording: pulls up actual Google Ads CPC for today's city, says the number on camera | ~10-15 sec |
| 3 — Close | Marcus or Claire (AI) | Delivers the rest of the Flow Report script with the real CPC number | ~15 sec |

### Why This Works
- The AI anchors add brand consistency and production value
- Victor's human segment adds credibility — it's a real screen, a real number, a real person
- The handoff creates a "breaking news" feel that stops the scroll
- Perfect for TikTok Duet and YouTube split-screen formats
- AI does the daily heavy lifting; Victor records one 15-second selfie video per episode

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

### Production Flow (Duo Format)

**AI asset generation (runs in parallel):**
1. Generate Part 1A audio: Marcus open line · Brooks voice · ~6 sec
2. Generate Part 1B audio: Claire open line · Sloane voice · ~4 sec
3. Generate Part 3 audio: Marcus/Claire close · ≤15 sec (use tight close script above)
4. Generate Part 1A video: Kling 3.0 · Marcus image · 9:16 · 5 sec
5. Generate Part 1B video: Kling 3.0 · Claire image · 9:16 · 5 sec
6. Generate Part 3 video: Seedance 2.0 · anchor image + Part 3 audio · 9:16 · match audio duration

**Victor records Part 2 (~15 sec):**
- Phone vertical (9:16), tripod or propped
- Google Keyword Planner open on screen behind you or screen-share overlay
- Script: "Hey — I just pulled this live. Right now, bidding on 'sell my house fast [CITY]' — you're paying [CPC] per click. Every. Single. Click. Back to you."
- Keep it 12–15 sec. Eyes to camera, not the screen.

**CapCut assembly:**
1. New project · 9:16 · 1080×1920 · 30fps
2. Timeline order: `Part1A.mp4` → `Part1B.mp4` → `victor.mp4` → `Part3.mp4` (hard cuts, no transitions)
3. Mute Part 1A, 1B, and Part 3 video tracks (Volume → 0)
4. Add audio layer: `Part1A.wav` aligned to Part 1A clip · `Part1B.wav` to Part 1B · `Part3.wav` to Part 3
5. Victor's clip stays at full volume
6. Add lower-thirds text: "MARCUS HALE" / "CLAIRE BENNETT" / "LIVE DATA · GOOGLE KEYWORD PLANNER" (for Victor's segment)
7. Auto-captions → English → clean up "$[CPC]" and "DM CALLS"
8. Export: 1080p · 30fps · H.264

5. Post as single video via Blotato

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
| 2026-07-23 | Dallas, TX | $30 | Marcus | ✅ Proof complete |
| | | | | |
| | | | | |
