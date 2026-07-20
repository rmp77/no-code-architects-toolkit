# Cold Email Audit Checklist
## Based on the 8 Trust Killers (GDocs On Steroids Framework)

Run every ReachInbox template through this before publishing.
Score: 8/8 = ship it. Below 6/8 = rewrite.

---

## Pre-Send Gate: Hard Rules

Before the 8 questions, confirm all three pass or don't send:

- [ ] Email is **under 90 words** (body only, excluding signature)
- [ ] There is **exactly one CTA** — one action, one link, one ask
- [ ] Subject line contains a **specific number, city, or observation** — no generic subject lines

---

## The 8 Trust Killers → Cold Email Translation

### 1. "They don't believe you can get the result."
**Cold email version:** Does the email state a specific outcome — not a category of benefit?

- FAIL: "I help local businesses get more clients."
- PASS: "I send plumbers in Tampa an average of 14 inbound calls in their first 30 days."

**Audit question:** If you removed the business owner's name and your name, could this email be about anyone? If yes — rewrite.

---

### 2. "They don't think they'll get enough attention."
**Cold email version:** Does the CTA make the next step brain-dead simple with zero friction?

- FAIL: "Let me know if you'd like to explore this further sometime."
- PASS: "Reply 'calls' and I'll send over how it works in 2 sentences."

**Audit question:** Could a 60-year-old contractor figure out exactly what to do next without thinking? If not — simplify.

---

### 3. "They don't think you care."
**Cold email version:** Does the email reference something specific about *their* business — not a vertical in general?

Use at least one of: `{{city}}`, `{{googleRank}}`, `{{yelpRating}}`, `{{yelpGap}}`, `{{companyName}}`

- FAIL: "I noticed your business could use more calls."
- PASS: "You're ranked #{{googleRank}} on Google Maps in {{city}} — but your Yelp rating is {{yelpGap}} stars lower than your Google score."

**Audit question:** Would this exact email work if you sent it to a plumber AND a divorce lawyer? If yes — it's not specific enough.

---

### 4. "They think you'll disappear."
**Cold email version:** Does the email explain what happens *immediately* after they respond?

- FAIL: "Happy to chat if you're interested."
- PASS: "Reply and I'll send a 2-minute breakdown of exactly how it works — no call needed."

**Audit question:** Does the prospect know what the next 24 hours look like if they say yes? If not — add it.

---

### 5. "They think you'll give a half-assed effort."
**Cold email version:** Does the email prove you researched this specific business — not just scraped their category?

The `{{recentNewsTitle}}` and `{{coldEmailAngle}}` variables exist for this. Use them when populated.

- FAIL: Any generic opener about the industry
- PASS: A hook that references their actual rank, Yelp gap, or a recent news item

**Audit question:** Did you have to look this business up to write this email? If yes — make that visible. If no — you're not specific enough.

---

### 6. "They don't believe the testimonials."
**Cold email version:** Skip testimonials in email #1. Too early. Zero trust baseline = testimonials read as claims.

Reserve proof for Stage 2 (Offer Doc) after the first reply.

**Exception:** A mirror case study in 1 sentence works if it's hyper-specific:
"A Tampa roofer in the same spot ranked #6 — we moved him to #2 and he got 11 calls his first week."

**Audit question:** If you included a testimonial — is it a real name, a real number, and a real situation the prospect can see themselves in? Otherwise cut it.

---

### 7. "They don't feel safe being vulnerable."
**Cold email version:** Is the email completely free of pressure language?

Words to remove: "limited spots", "act now", "don't miss out", "you'd be crazy not to", "serious inquiries only"

- FAIL: "I only have 2 spots left this month — let me know if you're serious."
- PASS: "No pitch, no obligation — just reply if you want to see how the call volume works."

**Audit question:** Does the email create urgency through scarcity OR through genuine insight? Scarcity in cold email = spam. Insight = reply.

---

### 8. "Missing earned confidence cues."
**Cold email version:** Does the email use language that only someone who actually runs pay-per-call for this vertical would use?

Insider language by category:
- Plumbers/HVAC: "dispatch calls", "service radius", "after-hours inbound"
- Lawyers: "signed retainer", "case type", "intake team"
- Roofers: "storm season", "insurance claim calls", "supplement work"
- Insurance: "X-date", "monoline", "auto/home bundle"
- Real estate: "buyer leads vs. listing leads", "days on market", "zip code farm"

**Audit question:** Could someone who has never worked in this vertical have written this email? If yes — add one insider phrase from the vertical's section in `docs/avatar-playbook.md`.

---

## Scoring

| Score | Action |
|-------|--------|
| 8/8   | Ship it |
| 6-7/8 | Fix the failures, re-check, then ship |
| 4-5/8 | Full rewrite before publishing |
| Below 4 | Don't send — will hurt deliverability and brand |

---

## Quick Reference: PRISM Variables That Satisfy Trust Killers

| Variable | Satisfies Trust Killer |
|----------|----------------------|
| `{{googleRank}}` | #3 (they care), #5 (research proof), #8 (specificity) |
| `{{yelpRating}}` / `{{yelpGap}}` | #3, #5, #8 |
| `{{city}}` | #3, #8 |
| `{{companyName}}` | #3 |
| `{{coldEmailAngle}}` | #1 (result clarity), #8 (earned confidence) |
| `{{recentNewsTitle}}` | #5 (research proof) |
| `{{businessCategory}}` | #8 (insider language) |
| `{{totalRatings}}` | #8 (specificity) |

---

## Subject Line Audit (Separate Pass)

The subject line must pass at least 2 of these 3:

1. **Specific:** Contains a number, city, or name — not a category
2. **Curious:** Creates a gap the reader needs to close
3. **Safe:** Doesn't sound like a sales pitch or trigger spam filters

| FAIL | PASS |
|------|------|
| "More leads for your business" | "{{city}} Google rank — quick note" |
| "Partnership opportunity" | "Your Yelp vs. Google gap ({{companyName}})" |
| "I help contractors get calls" | "#{{googleRank}} on Maps — something worth a look" |
| "Question for you" (too vague) | "{{googleRank}} position — one thing I noticed" |

---

*Updated: July 2026 | Framework source: GDocs On Steroids 2.0 + PRISM Stage 1*
