# CivicPulse — Video Narration Script

**Target: ~3 minutes | Screen recording with voiceover**
**Tone: Founder pitch — confident, specific, human. No filler.**

---

## PART 0: Introduction [~15s]
**On screen: Pitch deck — Title slide**

> I'm Johnny Chung. I'm a data scientist, I build AI agent systems, and I'm a father of three kids growing up in Santa Clara County.
>
> This is CivicPulse — and it started with a question I couldn't let go of: what happens when the neighborhoods where my kids eat are also the ones where every system is failing at once, and nobody's connecting the dots?

---

## PART 1: The Problem [~40s]
**On screen: Flip to Situation slide**

> Here's what I found when I started digging into the county's open data.
>
> **[flip to Situation slide]**
>
> There are 9,255 critical food safety violations on record in this county. And the neighborhoods with the most violations are also the poorest, the most crime-affected, and the ones where diabetes and food insecurity are highest.
>
> But here's the thing — no one sees that.
>
> **[flip to Problem slide — "4 data sources. Zero connections."]**
>
> Environmental Health has the inspection data. The police department has the crime data. The Census has the poverty data. The CDC has the health data. Four systems. Four agencies. Zero connections between them.
>
> **[flip to Ground Zero slide]**
>
> ZIP 95122, East San Jose. 100 failed inspections. 683 critical violations. Poverty rate nearly double the county median. Banh Mi Oven has failed 9 out of its last 13 inspections. And the system's response? Schedule another routine visit.
>
> That's the problem. Not bad people — blind systems.

---

## PART 2: The Solution [~30s]
**On screen: Solution slide (4 agents), then What Changes**

> **[flip to Solution slide]**
>
> CivicPulse joins these datasets by geography and runs four AI agents — all on a single NVIDIA DGX Spark.
>
> Sentinel scans every ZIP code and flags compounding risk. Analyst does the deep reasoning — why is this neighborhood different? Advisor writes a tailored brief for each person who needs to act. And Messenger routes it to the right channel at the right time.
>
> **[flip to What Changes slide]**
>
> The key shift: every output reaches a *specific person* with a *specific ask*. The Health Officer gets a brief she can forward Monday morning. The restaurant owner gets a coaching text with their three most likely violations. The resident can just ask, "Is it safe to eat there?"
>
> Nobody gets a dashboard. Everyone gets a decision.

---

## PART 3: Live Demo [~90s]
**On screen: Switch to Command Center (port 7860)**

> Let me show you this running live on the GB10.
>
> **[Command Center is open. Select a ZIP from the dropdown.]**
>
> I'm selecting ZIP 95122 — our Ground Zero. Watch the agents work.
>
> **[Click Run. Agents start streaming.]**
>
> Sentinel just flagged it — risk score 82, severity 4. That took under a second. It's rule-based, no LLM call needed.
>
> Now Analyst is reasoning. This is Nemotron 70B running locally on the GB10 — 42 gigs of model, 128K context window, all on-device. No cloud. No API calls. The inspection data never leaves this machine.
>
> **[As Analyst streams, read a key line from the output]**
>
> Look at that — it's connecting the food safety failures to the poverty rate and identifying that 22 repeat offenders in one ZIP is a systemic pattern, not a coincidence. That's the cross-silo insight that no single department's report would ever surface.
>
> **[Advisor starts streaming]**
>
> Now Advisor is writing the Health Officer brief. Situation, recommended actions, cross-agency coordination — ready to forward to Environmental Health, the Sheriff, and Public Health with one click.
>
> **[Messenger starts]**
>
> And Messenger is writing the coaching letter to the restaurant owner. Specific violations. Specific fixes. "Your cooler was 46 degrees — it needs to be 41 or below."
>
> That whole pipeline — from raw data to four tailored outputs — took about 80 seconds. On one machine.

---

## PART 4: Behind the Scenes [~25s]
**On screen: Switch to Behind the Scenes app (port 7861)**

> For the judges who want to see under the hood —
>
> **[Click Data Foundation tab]**
>
> This is the data pipeline. Six files from four sources — DEH food safety, SJPD crime, Census income, CDC health outcomes. Joined by geography. 350,000 records into 92 ZIP-level risk profiles.
>
> **[Click Risk Map tab, show the bubble map briefly]**
>
> Every bubble is a ZIP code. Size is number of restaurants. Color is compounding risk. The red cluster in East San Jose — that's the signal the agents are acting on.

---

## PART 5: Close [~20s]
**On screen: Switch back to pitch deck — Conclusion slide, then Close slide**

> **[Conclusion slide]**
>
> 210,000 residents in five ZIP codes carrying 30 percent of this county's food safety failures. That pattern was invisible until the data talked to each other.
>
> Less than 90 seconds from raw data to a Health Officer brief — all on one GB10.
>
> **[Close slide — "The data has always known..."]**
>
> The data has always known which neighborhoods need help. Now it has a voice.
>
> I'm Johnny Chung. This is CivicPulse. Thanks for watching.

---

## Pre-Recording Checklist

- [ ] Ollama running on DGX Spark with nemotron:70b loaded
- [ ] `./demo/launch.sh` — both apps up (7860 + 7861)
- [ ] Do one warm-up run so the model is loaded in memory
- [ ] QuickTime → New Screen Recording (or OBS)
- [ ] Resolution: 1920x1080
- [ ] Close all notifications, hide dock
- [ ] Pitch deck open in browser tab 1
- [ ] Command Center open in browser tab 2
- [ ] Behind the Scenes open in browser tab 3
- [ ] Practice once without recording — aim for under 3:30
