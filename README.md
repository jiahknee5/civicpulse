# CivicPulse

**Community Health Intelligence Agent System**

NVIDIA GB10 Hackathon | Human Impact Track | Johnny Chung

---

### Start here: [**Pitch Deck**](pitch_deck.html) *(right-click → Save As → open in browser → arrow keys)*

20+ slides covering the problem, real data findings, 4-agent architecture, district scorecards, recommended actions, projected impact, and full technical appendix.

---

## The Problem

Santa Clara County maintains 8 datasets across 4 departments — food safety, crime, workforce, and public health. These datasets share geography and time but have **never been analyzed together**. When a neighborhood is failing across food safety, crime, AND health outcomes simultaneously, nobody knows — because the data lives in separate systems, analyzed by separate teams, reported to separate boards.

## What CivicPulse Does

CivicPulse is a **4-agent system** that autonomously detects compounding community risk and delivers actionable intelligence to the people who can intervene — not as a dashboard, but as targeted briefs, coaching letters, and alerts tailored to each recipient.

| Agent | Role | How |
|-------|------|-----|
| **Sentinel** | Scans 8,588 businesses, flags ZIP codes with compounding risk | Rule-based scoring across food safety + crime + poverty + health |
| **Analyst** | Deep cross-silo reasoning on flagged neighborhoods | Nemotron 70B reads violation comments, connects patterns across 8 datasets |
| **Advisor** | Generates a Health Officer brief with intervention plan | Nemotron 70B — specific actions, cross-department coordination, expected impact |
| **Messenger** | Writes pre-inspection coaching for restaurant owners | Nemotron 70B — "Your 3 most likely violations and exactly how to fix them" |

## What We Found (Real Data)

| Finding | Number | Why It Matters |
|---------|--------|---------------|
| Critical food safety violations | **9,255** in 2 years | 37% are temperature control — the #1 cause of foodborne illness |
| Repeat-offender restaurants | **161** (2+ failed inspections) | These 161 generate **54% of all failed inspections** countywide |
| District 3 disparity | 19% of businesses, **34% of repeat failures** | East San Jose bears disproportionate food safety burden |
| Health equity gap | **+28% diabetes** in food-insecure tracts | People who can't afford to choose where they eat face worse health outcomes |
| ZIP 95122 (East San Jose) | 100 Red inspections, 683 critical violations | 4 of the top 15 worst restaurants in the county are in this single zip code |

## Projected Impact (Year 1)

| Action | Impact |
|--------|--------|
| Coach 161 repeat offenders before inspections | **129 Red inspections prevented**, $1.3M restaurant savings |
| Reallocate inspectors by risk (not schedule) | **6,326 inspector hours** redeployed from low-risk to high-risk |
| Temperature control blitz (top 100 violators) | **200–500 foodborne illness cases** prevented |
| District 3 cross-department intervention | Bring Red rate from 14.7% → county avg 9.3%, **253K residents** benefited |
| **Combined** | **436 Reds prevented, $4.4M saved, 500–1,500 illness cases avoided** |

None of these actions require new budget. They require connecting data that already exists.

## Demo

Runs entirely on **NVIDIA DGX Spark (GB10)** — Nemotron 70B (42GB) via Ollama. No cloud. No data leaves the machine.

```bash
./demo/launch.sh            # Starts both apps (builds data on first run)
```

- **Command Center** → `http://localhost:7860` — select a ZIP, watch 4 agents reason in real-time with streaming output
- **Behind the Scenes** → `http://localhost:7861` — data pipeline, risk maps, agent internals, district scorecards

## Stack

| Component | Technology |
|-----------|-----------|
| Hardware | NVIDIA DGX Spark (GB10) — Grace Blackwell, 128GB unified LPDDR5x |
| Model | Nemotron 70B (42GB) via Ollama — all inference on-device |
| Backend | FastAPI + Server-Sent Events (SSE) for real-time streaming |
| Frontend | Vanilla HTML/CSS/JS |
| Data | 6 SCC datasets + US Census ACS (62 zips) + CDC PLACES (408 tracts, 40 health measures) |

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│  NVIDIA DGX Spark (GB10) — 128GB Unified Memory                   │
│                                                                    │
│  SENTINEL (rule-based)                                             │
│    Scans all ZIP codes → flags compounding risk above threshold    │
│        ↓                                                           │
│  ANALYST (Nemotron 70B)                                            │
│    Reads violation comments, cross-references crime + poverty +    │
│    health data → severity assessment + root cause analysis         │
│        ↓                                                           │
│  ADVISOR (Nemotron 70B)                                            │
│    Generates Health Officer brief → specific intervention plan     │
│    with cross-department actions and expected impact                │
│        ↓                                                           │
│  MESSENGER (Nemotron 70B)                                          │
│    Generates restaurant coaching letter → "Fix these 3 things      │
│    before your next inspection"                                    │
│                                                                    │
│  Ollama :11434 ──── OpenAI-compat API ──── FastAPI+SSE :7860      │
└────────────────────────────────────────────────────────────────────┘
```

## Data Sources

| Dataset | Records | Time Range | Source |
|---------|---------|------------|-------|
| Crime Reports | 259,660 | 2019–2026 | SCC Sheriff's Office |
| Food Businesses | 8,588 | Current | SCC Dept of Environmental Health |
| Food Inspections | 21,895 | 2024–2026 | SCC DEH |
| Food Violations | 64,364 | 2024–2026 | SCC DEH |
| County Employees (EEO) | 26,042 | Current | SCC HR |
| Photographers' Collection | 4,541 | 1950–1993 | SCC Archives |
| Census Income/Poverty | 62 zip codes | 2022 | US Census ACS |
| CDC Health Outcomes | 16,320 | 2023 | CDC PLACES (40 measures × 408 tracts) |

## Repository

```
pitch_deck.html          # THE PITCH DECK — start here (20+ slides)

app/
  server.py              # FastAPI backend with SSE agent pipeline
  ui.html                # Frontend UI
  data_pipeline.py       # Joins 8 datasets by geography
  data/                  # Pre-computed risk profiles (JSON)

demo/
  command_center.py      # Live 4-agent pipeline UI
  behind_the_scenes.py   # Data exploration + agent internals
  launch.sh              # One-command launcher

planning/
  pressure_test.py       # Real-data validation of all findings
  district_scorecard.py  # 5-district analysis
  action_impact.py       # Projected impact calculations

SESSION_LOG.md           # Full build log from the hackathon
```
