# CivicPulse

**Community Health Intelligence Agent System**

NVIDIA GB10 Hackathon | Human Impact Track

---

### > Start here: [**Download the Pitch Deck**](pitch_deck.html) *(right-click → Save As → open in browser → arrow keys to navigate)*

The pitch deck contains the full story: problem, data findings, agent architecture, district scorecards, recommended actions with projected impact ($4.4M savings, 436 failed inspections prevented), and detailed technical appendix. **20+ slides.**

---

| Asset | Description |
|-------|-------------|
| **[Pitch Deck](pitch_deck.html)** | Full presentation — problem, findings, architecture, impact projections, appendix |
| **[Demo Video](https://github.com/jiahknee5/civicpulse/raw/main/civicpulse.mov)** | Screen recording of the live 4-agent pipeline |
| **Command Center** | `demo/command_center.py` — live 4-agent pipeline on port 7860 |
| **Behind the Scenes** | `demo/behind_the_scenes.py` — data pipeline, risk map, agent internals on port 7861 |

---

## Live Demo

The demo runs on NVIDIA DGX Spark (GB10) with Nemotron 70B via Ollama. All inference on-device — no cloud, no API calls.

```bash
./demo/launch.sh            # Starts both apps (builds data on first run)
```

- **Command Center** → `http://localhost:7860` — select a ZIP, run the 4-agent pipeline live
- **Behind the Scenes** → `http://localhost:7861` — data foundation, risk map, agent deep dive, district scorecard

## What It Does

CivicPulse is a 4-agent system that detects compounding community risk across food safety, crime, health, and economic data — and delivers actionable intelligence to the people who can intervene.

- **SENTINEL** — Scans 8,588 food businesses, flags ZIP codes where food safety, crime, poverty, and health indicators compound
- **ANALYST** — Cross-silo reasoning across 8 datasets using Nemotron 70B. Reads violation comments, connects patterns no single department can see
- **ADVISOR** — Generates tailored Health Officer briefs with specific cross-department intervention plans
- **MESSENGER** — Writes pre-inspection coaching letters for restaurant owners with specific fixes for their violation patterns

## Key Findings (Real Data)

- **9,255** critical food safety violations in 2 years — 37% are temperature control
- **161** repeat-offender restaurants generate **54% of all failed inspections**
- **District 3** (East San Jose) has 19% of businesses but **34% of repeat failures**
- Food-insecure census tracts have **28% more diabetes** and **23% more obesity**
- **ZIP 95122**: 100 Red inspections, 683 critical violations, Banh Mi Oven (9 Red, 23 critical)
- Projected impact: 436 Red inspections prevented, $4.4M restaurant savings, 500-1,500 illness cases avoided

## Stack

- **Hardware**: NVIDIA DGX Spark (GB10) — Grace Blackwell, 128GB unified LPDDR5x
- **Model**: Nemotron 70B (42GB) via Ollama — all inference on-device, no cloud
- **Backend**: FastAPI + Server-Sent Events (SSE) for real-time streaming
- **Frontend**: Vanilla HTML/CSS/JS — McKinsey-style clean UI
- **Data**: Santa Clara County open data (6 datasets) + US Census ACS + CDC PLACES (40 health measures)

## Architecture

```
SENTINEL (rule-based)     → Scans all zips, flags risk > 70
    ↓
ANALYST (Nemotron 70B)    → Deep cross-silo reasoning on flagged zips
    ↓
ADVISOR (Nemotron 70B)    → Generates Health Officer brief
    ↓
MESSENGER (Nemotron 70B)  → Generates restaurant coaching letter
```

## Data Sources

| Dataset | Records | Source |
|---------|---------|-------|
| Crime Reports | 259,660 | SCC Sheriff's Office |
| Food Businesses | 8,588 | SCC Dept of Environmental Health |
| Food Inspections | 21,895 | SCC DEH |
| Food Violations | 64,364 | SCC DEH |
| County Employees (EEO) | 26,042 | SCC HR |
| Photographers' Collection | 4,541 | SCC Archives |
| Census Income/Poverty | 62 zip codes | US Census ACS 2022 |
| CDC Health Outcomes | 16,320 (408 tracts × 40 measures) | CDC PLACES 2023 |

## Files

```
app/
  server.py            # FastAPI backend with SSE agent pipeline
  ui.html              # Frontend UI (McKinsey-style, white, clean)
  data_pipeline.py     # Joins 8 datasets by geography
  agents.py            # Agent definitions (original Gradio version)
  requirements.txt     # Python dependencies

pitch_deck.html        # Presentation slides (20+ slides, arrow keys)
dashboard.py           # Data exploration dashboard (Gradio, 10+ tabs)
pressure_test.py       # Real-data validation of findings
district_scorecard.py  # Per-district analysis (5 supervisorial districts)
action_impact.py       # Projected intervention impact ($4.4M, 436 Reds)
SESSION_LOG.md         # Full session log of the hackathon build process
```
