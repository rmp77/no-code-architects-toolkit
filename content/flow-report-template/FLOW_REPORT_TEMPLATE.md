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
**Voice ID:** `c2acff45-84b2-4974-892d-89fa2d4e5598` (Brooks · preset · male)  
**Prompt:** Paste the Hook-Only Script with [CITY] and [CPC] filled in

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

## City Queue (fill in as you go)

| Date | City | CPC | Anchor | Status |
|---|---|---|---|---|
| 2026-07-23 | Dallas, TX | $30 | Marcus | ✅ Proof complete |
| | | | | |
| | | | | |
