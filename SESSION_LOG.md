# NVIDIA GB10 Hackathon — Session Log
## Date: 2026-03-17
## Machine: DELL-31.local (nvidia@)
## Started: 11:40am | Submission: 4:30pm

---

## 11:40 — Initial Recon

### DELL-31 System Specs
- **GPU**: NVIDIA GB10 (DGX Spark / Blackwell)
- **RAM**: 119GB unified LPDDR5x (116GB available)
- **Disk**: 3.6TB NVMe, 2.3TB free
- **OS**: Ubuntu Linux (aarch64), kernel 6.17.0-1008-nvidia
- **CUDA**: 13.0
- **Python**: 3.12.3
- **Docker**: installed (no containers running)

### Data on DELL-31 (~/data/)
| File | Rows | Description |
|------|------|-------------|
| Crime_Reports_20260306.csv | 259,660 | Incidents: type, datetime, address, city |
| Employee_Breakdown_by_EEO_20260306.csv | 26,042 | County workforce: gender, ethnicity, dept, status |
| SCC_DEH_Food_Data_BUSINESS_20260306.csv | 8,588 | Restaurants: name, address, city, lat/lon |
| SCC_DEH_Food_Data_INSPECTIONS_20260306.csv | 21,895 | Inspections: score, result (G/Y/R), type |
| SCC_DEH_Food_Data_VIOLATIONS_20260306.csv | 64,364 | Violations: description, code, critical flag |
| County_Photographers'_Collection_20260306.csv | 4,541 | Historical photo archive: date, subject, dept |

### Key Data Insights
- All data is Santa Clara County, CA public records (March 2026 exports)
- Crime: 56 parent categories, 325 incident types. Top: Disturbance, Suspicious Vehicle, Alarm
- Food: 3-table relational set (biz → inspections → violations). 90% pass, 14% critical violations
- EEO: 65% female, 34% Asian, 24% Hispanic. Healthcare = 47% of workforce
- Food biz: San Jose 46%, 23 cities total. All CA.
- Photographers: metadata only (no image files on disk)

---

## 11:40 — Infrastructure Setup

### Installed
- [x] SSH key auth (id_ed25519) → DELL-31
- [x] sshpass (brew, for initial key copy)
- [x] Ollama on DELL-31 (systemd service)
- [x] Python venv: ~/hackathon/.venv
- [x] Packages: openclaw, gradio, pandas, plotly, openai, pydantic, requests

### In Progress
- [ ] Nemotron 70B pulling via Ollama (40GB+ download)

### Ports
- :22 SSH
- :11434 Ollama
- :11000 unknown (localhost only)

---

## 11:40 — Hackathon Context

### Tracks
1. **Human Impact** — e.g., agent that works for a hospital, autonomously meets patients
2. **Cultural Impact** — e.g., cultural tour guide agent
3. **Eco Impact** — e.g., reducing traffic, congestion, pollution, water use

### Prizes
- 1 GB10 per track (3 total)
- **Extra prize: Best Use of OpenClaw** (agent orchestration)

### Key Resources
- [NVIDIA/dgx-spark-playbooks](https://github.com/NVIDIA/dgx-spark-playbooks)
- OpenClaw playbook: gateway + Ollama backend, skills system
- Multi-agent chatbot playbook: supervisor + specialist agents
- vLLM: supports Nemotron-3-Super-120B NVFP4 on single Spark
- SGLang: FP8 models with flashinfer

### Project Ideas Discussed
1. **SafePlate (Human Impact)** — AI food safety risk predictor, inspector triage agent
2. **CrimeWatch SCC (Human Impact)** — Multi-stakeholder debate agents analyzing crime data
3. **EquityLens (Human Impact)** — Workforce representation analyzer
4. **County Heritage Guide (Cultural)** — Photo collection tour guide agent
5. **Traffic Reducer (Eco)** — Crime traffic data → congestion/emissions reduction

### Innovative Agent Concepts for CrimeWatch
- **Multi-Stakeholder Debate**: Sheriff vs Community Advocate vs Budget Director → Mediator
- **Anomaly Hunter → Specialist Router**: Scout finds anomalies, routes to specialists
- **Persona Simulation**: Data-grounded fictional characters telling "day in the life"

---

## ~12:15pm — Supplemental Data Acquired

### Census ACS (census_income.csv)
- 62 Santa Clara County zip codes
- Median household income, poverty pop, total pop
- Income caps at $250K+ (Los Altos Hills, Los Altos)

### CDC PLACES (cdc_places.csv)
- 16,320 rows: 408 census tracts x 40 health measures
- Key: 12.7% food insecurity, 10.3% diabetes, 22.7% obesity, 38.5% loneliness
- Joinable by census tract FIPS

### SCC Open Data Portal (data.sccgov.org)
- Medical Examiner-Coroner (geocoded deaths)
- Parcels + Zoning + General Plan
- COVID by Census Tract
- Homelessness data
- Flood Hazard Zones

## ~12:30pm — Dashboard Restructured

4-step workflow tabs:
1. Data Analysis — dataset summaries, insights, connections
2. Three Tracks — objectives, comparison matrix
3. Supplemental Data — Census, CDC, SCC portal
4. Brainstorm — current use, alternative use, decision framework

### Decision Matrix Result
- Community Health Intelligence (Human Impact): 29/30
- Neighborhood Narrator (Culture): 20/30
- Environmental Cost Calculator (Eco): 16/30

## ~2:45pm — CivicPulse Built

### App Running
- **URL**: http://DELL-31.local:7860
- **Stack**: Gradio + Nemotron 70B (Ollama) + streaming
- **4 agents**: SENTINEL (instant triage) → ANALYST (cross-silo reasoning) → ADVISOR (Health Officer brief) → MESSENGER (restaurant coaching)
- **Streaming**: Agent outputs appear in real-time as Nemotron generates
- **Full pipeline**: ~5-6 min per zip (3 Nemotron 70B calls)
- **Pre-computed**: Top 3 risk zips cached for instant demo

### Pitch Deck
- **URL**: http://DELL-31.local:7861/pitch_deck.html
- **20+ slides**: main deck + appendix with architecture, specs, data dictionary, risk scoring
- Includes: executive summary, district scorecards, action items with projected impact, agent flow

### Key Numbers
- 9,255 critical violations, 37% temperature control
- 161 repeat offenders generate 54% of all Red inspections
- District 3: 19% of businesses, 34% of repeat failures
- Combined impact: 436 Reds prevented, $4.4M saved, 500-1,500 illness cases avoided
- ZIP 95122: 100 Red, 683 critical, Banh Mi Oven (9 Red, 23 critical)

## Status: BUILT. Polish and test remaining.

---

## Commands Reference
```bash
# SSH to GB10
ssh nvidia@DELL-31.local

# Activate venv
source ~/hackathon/.venv/bin/activate

# Check Ollama models
ollama list

# Check GPU
nvidia-smi

# Sync local → GB10
rsync -az ~/hackathon/ nvidia@DELL-31.local:~/hackathon/
```
