# CivicPulse

**Community Health Intelligence Agent System**

NVIDIA GB10 Hackathon | Human Impact Track

## What It Does

CivicPulse is a 4-agent system that detects compounding community risk across food safety, crime, health, and economic data — and delivers actionable intelligence to the people who can intervene.

- **SENTINEL** — Scans 8,588 food businesses, flags ZIP codes with compounding risk
- **ANALYST** — Cross-silo reasoning across 6 datasets using Nemotron 70B
- **ADVISOR** — Generates tailored briefs for Health Officers
- **MESSENGER** — Writes pre-inspection coaching letters for restaurant owners

## Key Findings

- 9,255 critical food safety violations in 2 years
- 161 repeat-offender restaurants generate 54% of all failed inspections
- District 3 (East San Jose) has 19% of businesses but 34% of repeat failures
- Food-insecure census tracts have 28% more diabetes and 23% more obesity

## Stack

- **Hardware**: NVIDIA DGX Spark (GB10) — 128GB unified memory
- **Model**: Nemotron 70B via Ollama (all inference on-device)
- **Backend**: FastAPI + SSE streaming
- **Frontend**: Vanilla HTML/CSS/JS
- **Data**: Santa Clara County open data + US Census ACS + CDC PLACES

## Run

```bash
# On GB10
cd app
pip install -r requirements.txt
python3 data_pipeline.py   # Build data joins
python3 server.py          # Start app on :7860
```

## Files

```
app/
  server.py          # FastAPI backend with SSE agent pipeline
  ui.html            # Frontend UI
  data_pipeline.py   # Joins 8 datasets by geography
  agents.py          # Agent definitions (original version)
  data/              # Pre-computed risk profiles and summaries

pitch_deck.html      # Presentation slides
dashboard.py         # Data exploration dashboard (Gradio)
pressure_test.py     # Real-data validation of findings
district_scorecard.py # Per-district analysis
action_impact.py     # Projected intervention impact
```
