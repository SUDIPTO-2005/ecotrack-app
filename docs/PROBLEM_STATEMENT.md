# EcoTrack — Problem Statement & Feature Justification

> **Document version:** 1.0.0  
> **Last reviewed:** 2026-06-17  
> **Maintained by:** EcoTrack Product Team  
> **Audience:** Product reviewers, ethics boards, investors, open-source contributors

---

## Table of Contents

1. [The Core Problem](#the-core-problem)
2. [Why Individual Action Still Matters](#why-individual-action-still-matters)
3. [Feature-by-Feature Civic Justification](#feature-by-feature-civic-justification)
   - [Feature 1 — Carbon Footprint Calculator](#feature-1--carbon-footprint-calculator)
   - [Feature 2 — Lifestyle Log & History](#feature-2--lifestyle-log--history)
   - [Feature 3 — Goal Setting & Streaks](#feature-3--goal-setting--streaks)
   - [Feature 4 — Social Leaderboard & Friends](#feature-4--social-leaderboard--friends)
   - [Feature 5 — Emissions Breakdown Dashboard](#feature-5--emissions-breakdown-dashboard)
   - [Feature 6 — Weekly Eco-Report (Digest Email)](#feature-6--weekly-eco-report-digest-email)
   - [Feature 7 — Offset Marketplace Directory](#feature-7--offset-marketplace-directory)
   - [Feature 8 — AI Eco-Coach (EcoCoach)](#feature-8--ai-eco-coach-ecocoach)
   - [Feature 9 — Community Challenges](#feature-9--community-challenges)
   - [Feature 10 — Admin & Transparency Dashboard](#feature-10--admin--transparency-dashboard)
4. [Anti-Dark-Pattern Commitments](#anti-dark-pattern-commitments)
5. [Theory of Change](#theory-of-change)
6. [Scope Boundaries (What EcoTrack Is Not)](#scope-boundaries-what-ecotrack-is-not)

---

## The Core Problem

### 1. The Quantification Gap

Most people vastly underestimate their personal carbon footprint and have no reliable way to measure it. Studies consistently show:

- People underestimate the carbon cost of flying by **~8×** (Wynes & Nicholas, 2017).
- Most individuals overestimate the impact of easy actions (recycling) and underestimate the impact of high-impact actions (diet, flight reduction).
- Structural invisibility: CO₂ is colourless, odourless, and its consequences are geographically and temporally displaced from the act that caused it.

Without accurate, personalised quantification, behaviour change is shooting in the dark.

### 2. The Sustaining Gap

Even when people understand their footprint, sustained behaviour change is extremely difficult:

- One-off calculators produce momentary awareness but no ongoing accountability.
- Without feedback loops, initial motivation decays within weeks (Fogg, 2009).
- Isolated action feels futile against systemic emissions — a "drop in the ocean" psychological barrier.

### 3. The Social Gap

Carbon reduction is predominantly framed as a solitary, ascetic sacrifice rather than a collective, rewarding social act:

- Social norms powerfully drive behaviour. Visible peer action is one of the strongest predictors of individual behaviour change (Cialdini, 2003).
- Existing tools don't leverage social accountability, shared challenges, or peer recognition.
- Climate anxiety is rising, especially among younger users (Hickman et al., 2021) — connection and collective action are protective factors.

### 4. The Greenwash Trust Gap

The offset market is rife with low-quality credits, misleading marketing, and unverified claims. Users who want to compensate their residual emissions have no trusted directory of methodologically sound projects. This erodes trust in climate action broadly.

---

## Why Individual Action Still Matters

EcoTrack is fully aware of the **systemic change vs. individual action debate**. Our position:

1. **Individual action is not sufficient** — but it is necessary. Household consumption accounts for approximately **72% of global GHG emissions** when supply-chain upstream is allocated to end consumers (Ivanova et al., 2016).

2. **Demand signals drive supply.** Aggregated shifts in consumer behaviour (diet, flight frequency, EV adoption) create market pressure that accelerates corporate and policy change. The automobile electrification transition is an example.

3. **Individual actors are also voters, shareholders, and employees.** Engaged citizens with accurate carbon literacy are more likely to support climate-aligned policies and corporate accountability.

4. **Psychological spillover.** Research shows that making one pro-environmental commitment increases the likelihood of additional pro-environmental behaviours (Nilsson et al., 2016).

EcoTrack explicitly avoids the "individualisation of blame" trap by:
- Showing structural context (national average, sector benchmarks) alongside personal footprint.
- Pointing to systemic barriers in the AI coach's suggestions ("switching to an EV may not be feasible for you, here's what you *can* control").
- Never implying that individual offsets "solve" the climate crisis.

---

## Feature-by-Feature Civic Justification

### Feature 1 — Carbon Footprint Calculator

**Civic need:** Citizens cannot make informed decisions about their environmental impact without an accurate, category-level view of their emissions.

**Problem solved:** Closes the quantification gap. The calculator decomposes footprint into seven domains (electricity, diet, transport, flights, home energy, devices, waste) using peer-reviewed emission factors (see `DATA_SOURCES.md`). This specificity is essential: telling someone their total is "8 tonnes/year" is useless without knowing *which categories* to act on.

**Design principle:** The calculator asks only the minimum necessary questions for each category (progressive disclosure). No dark-pattern over-precision that implies false accuracy — uncertainty ranges are shown.

**Outcome link:** Users who see a concrete, itemised footprint report higher motivation to act (Lorenzoni et al., 2007).

---

### Feature 2 — Lifestyle Log & History

**Civic need:** Sustained behaviour change requires a feedback loop. A single measurement is a snapshot; a time series is accountability.

**Problem solved:** Closes the sustaining gap. Users can log activities (meals, journeys, purchases) and see their footprint trend over time. Historical data enables comparison ("I reduced my transport emissions 18% this month") that a one-time calculator cannot provide.

**Design principle:** Logging is opt-in and asynchronous — no push notifications demanding daily entries. The platform is designed to reward *consistency* over *frequency*, reducing anxiety for users who miss days.

**Data ownership:** Users can export their full history as CSV at any time and delete their account with all associated data (GDPR Article 17 compliance).

---

### Feature 3 — Goal Setting & Streaks

**Civic need:** Behaviour change science shows that specific, measurable, time-bound goals dramatically outperform vague intentions ("I'll try to reduce my footprint" vs. "I'll reduce my diet footprint by 10% this month").

**Problem solved:** Translates awareness into committed, trackable action. Users set category-specific reduction goals with timeframes. Streaks reward consistent logging behaviour — the habit that makes goal tracking possible.

**Design principle:** Streaks track *logging consistency*, not *perfection*. A user who logs a high-emission day is not penalised — honesty is rewarded over data gaming. Streaks are broken by multi-day gaps in logging, not by individual high-emission days.

**Psychological basis:** Implementation intentions (Gollwitzer, 1999) — committing to a specific "when, where, how" plan significantly increases follow-through. Goal-setting theory (Locke & Latham, 2002) — specific, difficult goals lead to higher performance than "do your best."

---

### Feature 4 — Social Leaderboard & Friends

**Civic need:** Social norms are among the most powerful drivers of behaviour change. Visible peer action normalises low-carbon choices and creates positive accountability.

**Problem solved:** Closes the social gap. Friends can connect, compare footprints, and cheer each other's reductions. The leaderboard ranks by *reduction percentage* rather than absolute footprint, so a high-income frequent flyer who makes significant changes ranks well — not just those who start with low footprints.

**Design principle — anti-shame:** Absolute footprint values are never shown on the leaderboard. Only reduction percentages and trend arrows are visible to friends. Users with higher absolute footprints are not publicly marked or ranked low — this would discourage high-emitters from joining, the users who have the most impact potential.

**Opt-out:** Social features are entirely opt-in. Users can use EcoTrack in full anonymity without connecting any friends or joining any leaderboard.

---

### Feature 5 — Emissions Breakdown Dashboard

**Civic need:** Aggregate awareness ("I emit 8 tonnes") does not drive action. Category-level insight ("70% of my footprint is diet and flights") identifies the leverage points.

**Problem solved:** Bridges quantification and action. Interactive charts break down emissions by domain, trend over time, and compare to national/peer averages. Users can drill into any category to see the specific activities driving their footprint.

**Design principle:** Comparisons are always contextualised. Showing that a user emits "3× the sustainable per-capita budget" without context creates anxiety and paralysis. EcoTrack always pairs a comparison with the primary *actionable category* and an estimated impact if the top action is taken.

---

### Feature 6 — Weekly Eco-Report (Digest Email)

**Civic need:** Environmental feedback loops must be regular and low-friction to maintain engagement without demanding daily app opens.

**Problem solved:** Delivers a curated weekly footprint summary, trend, and one personalised action tip via email. This "ambient accountability" keeps users engaged between active logging sessions and serves as a re-engagement mechanism for lapsed users.

**Design principle:** Emails are fully opt-out at any time (one-click unsubscribe per CAN-SPAM / GDPR). Email frequency is limited to one per week maximum. No "we miss you!" manipulation emails — lapsed users simply stop receiving reports after 30 days of inactivity.

---

### Feature 7 — Offset Marketplace Directory

**Civic need:** There is genuine demand from individuals and organisations wishing to compensate their *residual* emissions after reduction efforts. However, the voluntary carbon market is opaque, with widespread low-quality and fraudulent credits.

**Problem solved:** Provides a curated, methodology-disclosed directory of offset and climate-finance projects for informational purposes.

**Why informational, not transactional:**

EcoTrack is explicitly **NOT** a carbon offset broker or marketplace operator. Feature 7 is a **directory with editorial curation**, not a purchasing engine. Reasons:

1. **Transactional offset sales create perverse incentives.** A platform that earns revenue from offset sales has a financial interest in users *not* reducing emissions. EcoTrack's commercial model must not conflict with its mission.

2. **Legal and regulatory risk.** Acting as an offset broker in multiple jurisdictions carries significant regulatory complexity (financial services, consumer protection, greenwash legislation under EU CSRD and UK FCA).

3. **Trust and editorial independence.** A directory model allows EcoTrack to curate only projects meeting minimum quality thresholds (Gold Standard, VCS/Verra, CDM) without being perceived as promoting specific vendors for commercial gain.

4. **Hierarchy of climate action.** Offsets should be the *last resort* after reduction. An offset sales feature risks communicating that buying credits is equivalent to reducing emissions — a scientifically and ethically false equivalence.

**What Feature 7 provides:**
- A directory of verified offset project types and standards (Gold Standard, Verra VCS, American Carbon Registry).
- Links to independent project registries where users can verify credits.
- Editorial notes on project quality, additionality, and permanence.
- A prominent disclaimer (exact text in `AI_SAFETY_NOTES.md §7`) stating that offsets are supplementary and imperfect.

**What Feature 7 does NOT provide:**
- Direct purchase flow or payment processing.
- Affiliate links or revenue-sharing arrangements with any offset provider.
- A claim that any offset "cancels" or "neutralises" user emissions.

---

### Feature 8 — AI Eco-Coach (EcoCoach)

**Civic need:** Generic sustainability advice ("eat less meat, fly less") has low uptake because it is not personalised to the user's actual footprint profile, constraints, or life context. Personalised coaching dramatically increases action likelihood (Miller & Rollnick, 2012).

**Problem solved:** EcoCoach uses a user's actual footprint breakdown to generate personalised, specific, actionable suggestions. It explains *why* a given category is their largest, suggests *realistic* alternatives given their profile, and answers follow-up questions.

**Why supportive, not manipulative:**

EcoCoach is designed as a **supportive informational tool**, not a persuasion engine. The key distinctions:

1. **Rate limited:** One AI-generated tip per user per week. This prevents dependency, compulsive use, and excessive API cost amplification. (See `AI_SAFETY_NOTES.md §4`.)

2. **No gamification hooks on AI interaction.** EcoCoach does not award points, badges, or streak credits for engaging with AI suggestions. Engagement with AI advice is not a metric.

3. **Transparent about limitations.** The AI system prompt explicitly instructs the model to acknowledge uncertainty, decline to give medical or financial advice, and note when a suggestion may not be feasible for all users.

4. **No dark nudges.** EcoCoach does not use loss-aversion framing ("you're falling behind your peers!"), artificial urgency, or social pressure to drive engagement. Suggestions are framed positively: "here's what would make the biggest difference for your profile."

5. **Graceful rule-based fallback.** When the AI API is unavailable or the weekly cap is reached, a deterministic rule-based tip generator provides useful advice without requiring an API call. Users cannot be left without support due to budget constraints.

6. **Output sanitisation.** All AI-generated text is treated as untrusted input and sanitised before rendering to prevent XSS, even though the text originates from a controlled prompt. (See `AI_SAFETY_NOTES.md §3`.)

**Psychological basis:** Motivational interviewing principles — focus on the user's stated goals, avoid direct confrontation, elicit their own reasons for change (Miller & Rollnick, 2012). The AI prompt is designed around these principles, not around maximising engagement metrics.

---

### Feature 9 — Community Challenges

**Civic need:** Collective action problems — including climate change — are better addressed through coordinated group effort than isolated individual action. Group challenges leverage social commitment and normative influence.

**Problem solved:** Users can join time-limited community challenges (e.g., "No-Beef November," "Flight-Free Summer," "Reduce Home Energy 15% This Month"). Progress is aggregated and visible to the group, creating collective momentum and social accountability.

**Design principle:** Challenges are opt-in and non-competitive in absolute terms. The community sees *aggregate progress* (total collective reduction), not individual rankings within the challenge. This creates "we're doing this together" framing rather than winner/loser dynamics that demotivate lower-performing participants.

**Civic spillover:** Community challenges create a natural mechanism for EcoTrack to partner with municipalities, schools, universities, and NGOs who want to run coordinated climate action campaigns.

---

### Feature 10 — Admin & Transparency Dashboard

**Civic need:** Platforms that handle personal environmental data and use AI must be accountable. Users and regulators need confidence that the platform is not misusing data, AI, or emissions metrics.

**Problem solved:** The admin dashboard provides platform operators with visibility into:
- Aggregate anonymised usage statistics (not individual-level surveillance).
- AI API usage and cost (daily/weekly, to prevent runaway spend).
- Data quality flags (anomalous footprint entries, potential gaming).
- System health and error rates.

**Why this is a civic feature:** Transparency tools are a commitment device for the platform itself. By building the monitoring infrastructure, EcoTrack holds itself accountable to its own stated policies on AI usage limits, data retention, and cost controls. This is documented in `AI_SAFETY_NOTES.md §5`.

---

## Anti-Dark-Pattern Commitments

EcoTrack publicly commits to the following design constraints. Violation of any item is considered a product integrity issue requiring escalation to leadership:

### ❌ We will NOT:

| Dark pattern | Why it is prohibited |
|-------------|---------------------|
| Variable-ratio reward schedules (slot machine mechanics) | Designed to create compulsive engagement, not genuine behaviour change |
| "You're falling behind!" guilt notifications | Loss-aversion manipulation; increases anxiety without improving outcomes |
| FOMO countdown timers on challenges | Creates artificial urgency not grounded in genuine environmental deadlines |
| Affiliate commissions on offset purchases | Creates financial conflict with the mission |
| Claiming offsets "cancel" or "neutralise" emissions | Scientifically inaccurate; normalises offsetting over reduction |
| Hiding the unsubscribe option | Violates GDPR, CAN-SPAM, and user trust |
| Selling individual user data to advertisers | Core data ethics violation |
| Requiring social features to access core tracking | Social features are opt-in; basic tracking is always available |
| Showing AI-generated text without sanitisation | Security failure (XSS vector) |
| Unlimited AI API calls per user | Creates dependency and unpredictable cost |
| "Delete account" flows that obscure data deletion | Violates GDPR Article 17 right to erasure |
| Inflating footprint estimates to drive action | Dishonest; erodes trust when corrected |

### ✅ We WILL:

- Show uncertainty ranges on all emission factor calculations.
- Allow full data export (CSV) at any time.
- Provide a one-click account and data deletion flow.
- Disclose all emission factor sources and versions (see `DATA_SOURCES.md`).
- Cap AI features at one call per user per week with a hard monthly cost ceiling.
- Make opt-out of every notification type possible from a single settings screen.
- Publish an annual transparency report on aggregate platform emissions impact and AI costs.

---

## Theory of Change

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWARENESS PHASE                          │
│                                                                 │
│  User completes calculator → sees personalised footprint        │
│  breakdown → understands which categories matter most           │
│                          │                                      │
│              "I didn't know flights were that big."             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        INTENTION PHASE                          │
│                                                                 │
│  User reads EcoCoach tip → sets a specific, category goal       │
│  → commits to a community challenge                             │
│                          │                                      │
│        "I'll reduce my diet footprint by 15% this month."       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        ACTION PHASE                             │
│                                                                 │
│  User logs meals, journeys, activities → weekly digest          │
│  confirms progress → streak maintains logging habit             │
│                          │                                      │
│    "My diet emissions dropped 12% — I can see it happening."    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SOCIALISATION PHASE                         │
│                                                                 │
│  User shares progress with friends → joins leaderboard          │
│  → friends join platform → social norm of tracking spreads      │
│                          │                                      │
│    "My friend group is all doing this — it's become normal."    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SYSTEMIC SPILLOVER                          │
│                                                                 │
│  Aggregated demand signals (diet shift, flight reduction)        │
│  → corporate supply-chain response → policy advocacy            │
│  by climate-literate, engaged citizens                          │
│                                                                 │
│    "I know my numbers. I vote for policies that match."         │
└─────────────────────────────────────────────────────────────────┘
```

**Key assumptions in this theory of change:**
1. Quantification → motivation: Accurate, personalised footprint data increases motivation to act (supported by Lorenzoni et al., 2007; Attari et al., 2010).
2. Goals + feedback → sustained behaviour change (Locke & Latham, 2002).
3. Social norms → behaviour: Visible peer action is a strong predictor of individual behaviour (Cialdini, 2003; Schultz et al., 2007).
4. Collective action amplifies individual impact: The social and challenge features aggregate individual actions into community-level and ultimately market-level signals.

**What could go wrong (risks):**
- **Preaching to the choir:** Early adopters may be already high-motivation individuals whose behaviour is easiest to change. Reaching less-engaged users is harder and requires partnerships (employers, schools).
- **Rebound effect:** Efficiency gains may be offset by increased consumption ("I switched to EV so I can drive more"). EcoTrack mitigates this by showing absolute footprint, not just percentage change.
- **Offset substitution:** Users may use offset information as permission to not reduce. Mitigated by offset disclaimer and reduction-first UI hierarchy.

---

## Scope Boundaries (What EcoTrack Is Not)

| Not EcoTrack | Reason |
|-------------|--------|
| A carbon accounting platform for businesses | Scope 1/2/3 corporate accounting is a different product with different regulatory requirements (GHG Protocol) |
| A carbon offset broker | Financial and legal complexity; mission conflict (see Feature 7) |
| A replacement for structural/policy change | Individual action is necessary but not sufficient; EcoTrack explicitly tells users this |
| A health or nutrition tracking app | Dietary data is used only for emission calculations, never for nutritional advice |
| A surveillance tool for employers | No employer dashboard; individual footprint data is never shared with third parties without explicit consent |
| A social media platform | Social features are minimal, functional, and not designed for time-maximisation |

---

## References

- Attari, S. Z., et al. (2010). Public perceptions of energy consumption and savings. *PNAS*, 107(37), 16054–16059.
- Cialdini, R. B. (2003). Crafting normative messages to protect the environment. *Current Directions in Psychological Science*, 12(4), 105–109.
- Fogg, B. J. (2009). A behavior model for persuasive design. *Proceedings of Persuasive Technology*, ACM.
- Gollwitzer, P. M. (1999). Implementation intentions: Strong effects of simple plans. *American Psychologist*, 54(7), 493–503.
- Hickman, C., et al. (2021). Climate anxiety in children and young people and their beliefs about government responses. *The Lancet Planetary Health*, 5(12), e863–e873.
- Ivanova, D., et al. (2016). Environmental impact assessment of household consumption. *Journal of Industrial Ecology*, 20(3), 526–536.
- Locke, E. A., & Latham, G. P. (2002). Building a practically useful theory of goal setting. *American Psychologist*, 57(9), 705–717.
- Lorenzoni, I., Nicholson-Cole, S., & Whitmarsh, L. (2007). Barriers perceived to engaging with climate change among the UK public. *Global Environmental Change*, 17(3–4), 445–459.
- Miller, W. R., & Rollnick, S. (2012). *Motivational Interviewing: Helping People Change* (3rd ed.). Guilford Press.
- Nilsson, A., et al. (2016). Does a short-term environmental campaign change attitudes, behaviours and moral norms? *Environment and Behavior*, 48(2), 207–234.
- Schultz, P. W., et al. (2007). The constructive, destructive, and reconstructive power of social norms. *Psychological Science*, 18(5), 429–434.
- Wynes, S., & Nicholas, K. A. (2017). The climate mitigation gap. *Environmental Research Letters*, 12(7), 074024.

---

*End of PROBLEM_STATEMENT.md — EcoTrack v1.0.0*
