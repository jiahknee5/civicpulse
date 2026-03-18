# CivicPulse — Build Process

## How This Was Built: A 5-Hour Journey from Raw Data to Working Agent System

### The Setup
- **Date**: March 17, 2026
- **Hardware**: NVIDIA DGX Spark (GB10) — Dell Pro Max, codename DELL-31
- **Dev machine**: M5 Max MacBook Pro running Claude Code (Opus 4.6)
- **Model**: Nemotron 70B via Ollama (42GB, all inference on GB10)
- **Solo builder**: Johnny Chung

### Timeline

---

#### 11:40am — First Contact

Connected to DELL-31 via SSH. Machine was bare — no models, no Ollama, no server running. 119GB RAM free, 2.3TB disk, GPU idle.

**First moves (parallel):**
- Installed Ollama on DELL-31
- Started pulling Nemotron 70B (40GB download)
- Created Python venv, installed dependencies (openclaw, gradio, pandas, plotly, openai)
- While model downloaded: explored the 6 datasets

**Key decision:** Don't wait for the model. Start understanding the data immediately.

---

#### 11:40–12:15 — Data Deep Dive

Built a quick Gradio dashboard to explore all 6 datasets visually. This wasn't the submission — it was a thinking tool.

**What I learned:**
- Crime: 260K incidents, 6 years, 325 types. "Other" is 35% — classification is broken
- Food: 3-table relational set. 90% pass, 4% fail. 161 repeat offenders
- EEO: Healthcare is 47% of the entire county workforce
- Photos: 1950-1993 metadata only, no images

**Key insight:** The datasets are all siloed. Each serves one department. Nobody cross-references them.

**Dashboard evolved iteratively:** Added maps (food businesses have lat/lon), overlaid crime by street matching, added filters, sample data, data dictionaries. The dashboard became the analysis tool for the rest of the hackathon.

---

#### 12:15–12:30 — Supplemental Data

Pulled three external sources in parallel (using Claude Code agents):
1. **US Census ACS** — income and poverty by zip code (62 zips)
2. **CDC PLACES** — 40 health measures by census tract (408 tracts)
3. **SCC Open Data Portal scan** — identified 15+ additional datasets available

**This changed everything.** The CDC data showed that food-insecure census tracts have 28% more diabetes and 23% more obesity. The Census data let us compute poverty rates per zip. Suddenly the food safety data wasn't just about restaurants — it was about health equity.

---

#### 12:30–1:30 — Track Selection & Brainstorming

Structured the decision across 4 tabs in the dashboard:
1. **Data Analysis** — what we have
2. **Three Tracks** — Human Impact vs Eco vs Culture, with objectives for each
3. **Supplemental Data** — what we acquired and what's available
4. **Brainstorm** — current use of data, alternative uses, decision framework

**Explored multiple directions:**
- SafePlate (food safety predictor) — too much like a dashboard
- CrimeWatch (multi-stakeholder debate) — innovative but risky to build
- Heritage Guide (cultural tour) — thin data
- Environmental Cost Calculator — derivative

**Pressure tested with real data:** Ran actual queries to validate every claim. Found ZIP 95122 (East San Jose) as ground zero: 100 Red inspections, 683 critical violations, 10.5% poverty. Found Banh Mi Oven: 9 Red inspections, 23 critical violations. Found the District 3 disparity: 19% of businesses, 34% of repeat failures.

**Key pushback moment:** I realized all my ideas were "data analysis" — overlaying datasets on each other. The user (me) pushed: "What's actually actionable? Who does something different tomorrow because this exists?" This led to the agent concept.

---

#### 1:30–2:00 — Design & Architecture

Designed the 4-agent system (Sentinel → Analyst → Advisor → Messenger) with specific focus on:
- **Each agent makes a real decision** (not just processing)
- **Each output has a named recipient** (Health Officer, Supervisor, Owner, Resident)
- **The counterfactual is clear** (what happens without vs with CivicPulse)

**Another pushback moment:** "Why agents and not a script?" Honest answer: most of what we designed doesn't need agents. The genuine agent value is reading 64,364 free-text violation comments and reasoning about context — something SQL can't do.

This led to a simpler, more honest architecture:
- SENTINEL = scoring engine (rule-based, no LLM)
- ANALYST + ADVISOR = the actual LLM brain (reads text, reasons, generates)
- MESSENGER = delivery infrastructure (not an agent)

---

#### 2:00–2:30 — Pitch Deck

Built a full HTML presentation (pitch_deck.html) before writing agent code. This was deliberate — the pitch tells the story, the code proves it works.

**20+ slides including:**
- Executive summary (McKinsey-style)
- Ground Zero: ZIP 95122 with real restaurant names and violation counts
- Health equity gap: real CDC numbers
- District Scorecard: all 5 supervisorial districts compared
- Recommended actions with projected impact ($4.4M, 436 Reds prevented)
- "A Week with CivicPulse" — Mon-Fri timeline of user interactions
- Why agents, not scripts
- Full technical appendix (architecture, agent specs, data pipeline, risk scoring)

---

#### 2:37–3:30 — Build the Agent System

**Data pipeline** (30 min):
- Joined all 8 datasets by geography (zip, street, tract)
- Computed composite risk scores per zip
- Pre-computed top 10 risk zips with worst businesses
- Saved as JSON for the agent to consume

**Agent code** (45 min):
- First version: Gradio app with 4 sequential Nemotron calls
- Tested full pipeline: 351 seconds (~6 min) for all 4 agents
- Started pre-computing outputs for top 3 zips (ran in background)

**Pivoted to FastAPI + SSE** for better streaming UX:
- Custom HTML frontend with full CSS control
- Server-Sent Events for real-time streaming of agent outputs
- Each agent's text appears word-by-word as Nemotron generates

**Tested live:** ANALYST produced a real assessment of ZIP 95122 — severity rating, root cause analysis, affected population, recommended intervention. It read the violation comments and synthesized patterns. This was the proof that the agent adds value beyond a script.

---

#### 3:30–4:00 — Polish & Iterate

**UI iterations:**
- Started dark mode → switched to light (McKinsey style)
- Fought with Gradio CSS limitations → rebuilt as vanilla HTML for full control
- Multiple rounds of styling: header, stats bar, agent headers, log, output boxes

**OpenClaw status:**
- Installed (pip install openclaw) but has a runtime dependency conflict
- Documented honestly in code comments
- Architecture follows the OpenClaw pattern — agent orchestration principles are the same

**GitHub:**
- Created public repo: github.com/jiahknee5/civicpulse
- Made all other repos private
- README structured as an executive summary with pitch deck prominently linked

---

#### 4:00–4:30 — Submission

- Recorded demo video
- Filled out submission form
- Final push to GitHub

---

### What I'd Do Differently

1. **Spend less time on the exploration dashboard.** It was valuable for understanding the data but consumed 2+ hours. Pre-built EDA templates would have halved this.

2. **Build the pitch deck FIRST, code SECOND.** This is what actually happened and it was the right call. The pitch is what judges evaluate. The code just needs to prove it's not vaporware.

3. **Pre-identify supplemental data sources.** Census + CDC were game-changers but took 30 min to find and pull. Having these ready would have accelerated the insight discovery.

4. **Don't fight the framework.** Gradio CSS is limited. I should have gone to vanilla HTML/FastAPI from the start instead of iterating through 4 Gradio redesigns.

5. **Pre-build a FastAPI + SSE + vanilla HTML template.** This is the stack that actually shipped. Having it ready would have saved 45 min.

6. **Test OpenClaw before the event.** The package had a dependency conflict that wasn't discoverable until runtime. Should have tested on ARM64/Ubuntu before relying on it.

### What Worked

1. **Claude Code as the co-pilot.** Running analysis, writing code, building the deck, and pushing to GitHub — all from one terminal session. The parallel agent capability (running data pulls in background while building UI) was critical.

2. **Data-first, code-second.** Spending 3 hours understanding the data before writing agent code meant every agent output was grounded in real, validated findings.

3. **Pressure testing with real examples.** Every claim in the pitch is backed by an actual query against actual data. ZIP 95122, Banh Mi Oven, District 3 — all real.

4. **The pushback loop.** Forcing myself to answer "why agents?" and "so what?" at every step killed weak ideas early and led to a more honest, defensible project.

5. **Nemotron 70B on GB10.** The model ran smoothly once loaded. 128GB unified memory meant the model + data pipeline ran simultaneously without memory pressure. Inference was slow (~2 min per call) but streaming made it usable.

### Tools Used

| Tool | Role |
|------|------|
| Claude Code (Opus 4.6) | Primary development environment — code, analysis, writing, Git |
| Nemotron 70B | Agent inference (Analyst, Advisor, Messenger) |
| Ollama | Model serving on GB10 |
| FastAPI + Uvicorn | Backend API with SSE streaming |
| Vanilla HTML/CSS/JS | Frontend UI |
| Pandas | Data pipeline and joins |
| Plotly | Visualization (dashboard) |
| Gradio | Early exploration dashboard |
| US Census API | Supplemental income/poverty data |
| CDC PLACES API | Supplemental health outcome data |
| GitHub (gh CLI) | Repo management |

### Key Metrics

| Metric | Value |
|--------|-------|
| Total time | ~5 hours (11:40am – 4:30pm) |
| Time on data analysis | ~2.5 hours (50%) |
| Time on design/pitch | ~1 hour (20%) |
| Time on agent code | ~1 hour (20%) |
| Time on polish/submission | ~30 min (10%) |
| Datasets joined | 8 |
| Total records processed | ~401,000 |
| Nemotron 70B calls in final demo | 3 (streaming) |
| Pitch deck slides | 20+ |
| Lines of code (app) | ~400 |
| Git commits | 5 |
