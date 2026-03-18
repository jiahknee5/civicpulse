"""CivicPulse API — serves agent pipeline via SSE for the frontend.

Agent orchestration follows the OpenClaw multi-agent pattern:
  - Agents are specialized (Sentinel, Analyst, Advisor, Messenger)
  - Context passes between agents (Sentinel flags → Analyst reasons → Advisor briefs → Messenger coaches)
  - Each agent has a distinct system prompt, model config, and decision boundary
  - Inference via OpenAI-compatible API (Ollama serving Nemotron 70B)

Note: OpenClaw package (pip install openclaw) was installed but has a dependency
conflict (cmdop.exceptions.TimeoutError missing in openclaw 2026.3.12 + cmdop 2026.3.17).
Agent orchestration is implemented directly using the same architectural pattern.
"""
import json
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
import uvicorn

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
MODEL = "nemotron:70b"
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

with open(DATA_DIR / "top_risk_zips.json") as f:
    top_zips = json.load(f)
with open(DATA_DIR / "county_summary.json") as f:
    summary = json.load(f)
with open(DATA_DIR / "cdc_averages.json") as f:
    cdc_avg = json.load(f)

ANALYST_SYS = """You are ANALYST in CivicPulse — a 4-agent community health intelligence system for Santa Clara County.
SENTINEL has flagged a ZIP code with compounding risk across food safety, crime, and poverty.
Your job: deep cross-silo analysis. Be specific — use real numbers and business names.
Structure: SEVERITY | ROOT CAUSES | AFFECTED POPULATION | CROSS-SILO INSIGHT | 30-DAY PRIORITIES (3 items)
Max 280 words. No filler."""

ADVISOR_SYS = """You are ADVISOR in CivicPulse. You write for the County Health Officer — a senior official who acts Monday morning.
Format exactly: ## SITUATION / ## RECOMMENDED ACTIONS (numbered 1-3) / ## CROSS-AGENCY COORDINATION / ## EXPECTED IMPACT
Max 220 words. Every sentence drives toward a decision."""

MESSENGER_SYS = """You are MESSENGER in CivicPulse. You write a pre-inspection coaching letter to a restaurant manager.
Be direct and helpful — they want to pass, they just need specific guidance.
Format: Start "Dear Manager,". Give exactly 3 numbered fixes with precise requirements (temperatures, procedures, frequencies).
End with one next-step sentence. Max 180 words."""

app = FastAPI()

@app.get("/")
async def index():
    return FileResponse(APP_DIR / "ui.html")

@app.get("/api/data")
async def get_data():
    return {"top_zips": top_zips, "summary": summary, "cdc_avg": cdc_avg}

@app.get("/api/run/{zip_code}")
async def run_pipeline(zip_code: str):
    z = next((x for x in top_zips if x["zip"] == zip_code), None)
    if not z:
        return {"error": "ZIP not found"}

    def generate():
        def sse(obj):
            return f"data: {json.dumps(obj)}\n\n"

        # SENTINEL
        biz_count = f"{summary['total_businesses']:,}"
        yield sse({"agent":"SENTINEL","type":"log","msg":f"Scanning {biz_count} businesses..."})

        score_str = f"{z['risk_score']:.0f}"
        yield sse({"agent":"SENTINEL","type":"log","msg":f"FLAGGED {z['zip']} — score {score_str}/100 | {z['total_red']} Red | {z['total_critical']} critical | poverty {z['poverty_rate']}%"})

        top_biz = z["worst_businesses"][0] if z["worst_businesses"] else None
        if top_biz:
            yield sse({"agent":"SENTINEL","type":"log","msg":f"Top violator: {top_biz['name']} — {top_biz['critical_violations']} critical, {top_biz['red_inspections']} Red"})

        crime_str = f"{z['crime_on_food_streets']:,}"
        sentinel_text = f"Scan complete. ZIP {z['zip']} flagged.\nRisk: {score_str}/100\n\n{z['total_red']} Red | {z['total_critical']} critical | {z['repeat_offenders']} repeat offenders\n{crime_str} crimes on food streets | {z['poverty_rate']}% poverty"
        yield sse({"agent":"SENTINEL","type":"output","text":sentinel_text})
        yield sse({"agent":"SENTINEL","type":"log","msg":"Handing off to ANALYST"})

        # ANALYST
        yield sse({"agent":"ANALYST","type":"log","msg":f"Cross-correlating food safety + crime + poverty for ZIP {z['zip']}..."})

        worst_txt = "\n".join(
            f"  - {b['name']} ({b['city']}): {b['critical_violations']} critical, {b['red_inspections']} Red — {b['top_violations'][:70]}"
            for b in z["worst_businesses"][:3]
        )
        analyst_prompt = f"""FLAGGED ZIP: {z['zip']} — Risk Score {z['risk_score']:.0f}/100
SIGNALS:
- Businesses: {z['businesses']} | Red: {z['total_red']} | Critical: {z['total_critical']} | Repeat offenders: {z['repeat_offenders']}
- Crime on food streets: {z['crime_on_food_streets']:,} | Poverty: {z['poverty_rate']}% | Income: ${z['median_income']:,}
- County CDC avg — food insecurity: {cdc_avg['food_insecurity_pct']:.1f}% | diabetes: {cdc_avg['diabetes_pct']:.1f}%
TOP VIOLATORS:
{worst_txt}
Temperature control = 37% of all critical violations countywide.
Provide your structured assessment."""

        stream = client.chat.completions.create(
            model=MODEL,
            messages=[{"role":"system","content":ANALYST_SYS},{"role":"user","content":analyst_prompt}],
            stream=True, max_tokens=600, temperature=0.2,
        )
        analyst_text = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            analyst_text += delta
            yield sse({"agent":"ANALYST","type":"stream","delta":delta})

        yield sse({"agent":"ANALYST","type":"log","msg":"Assessment complete — handing off to ADVISOR"})

        # ADVISOR
        yield sse({"agent":"ADVISOR","type":"log","msg":f"Drafting Health Officer brief for ZIP {z['zip']}..."})
        advisor_prompt = f"""ZIP {z['zip']} — {z['businesses']} businesses, {z['total_red']} Red, {z['total_critical']} critical, {z['repeat_offenders']} repeat offenders. Poverty {z['poverty_rate']}%.
ANALYST ASSESSMENT:
{analyst_text}
Write the Health Officer brief."""

        stream = client.chat.completions.create(
            model=MODEL,
            messages=[{"role":"system","content":ADVISOR_SYS},{"role":"user","content":advisor_prompt}],
            stream=True, max_tokens=500, temperature=0.2,
        )
        advisor_text = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            advisor_text += delta
            yield sse({"agent":"ADVISOR","type":"stream","delta":delta})

        yield sse({"agent":"ADVISOR","type":"log","msg":"Brief complete — handing off to MESSENGER"})

        # MESSENGER
        if top_biz:
            biz_name = top_biz['name']
            biz_city = top_biz['city']
            yield sse({"agent":"MESSENGER","type":"log","msg":f"Coaching for: {biz_name} ({biz_city})"})
            msg_prompt = f"""Restaurant: {biz_name} ({biz_city}, ZIP {z['zip']})
Failed inspections: {top_biz['red_inspections']} Red, {top_biz['critical_violations']} critical
Violations: {top_biz['top_violations']}
Write the pre-inspection coaching letter."""

            stream = client.chat.completions.create(
                model=MODEL,
                messages=[{"role":"system","content":MESSENGER_SYS},{"role":"user","content":msg_prompt}],
                stream=True, max_tokens=350, temperature=0.3,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                yield sse({"agent":"MESSENGER","type":"stream","delta":delta})

            yield sse({"agent":"MESSENGER","type":"log","msg":"Coaching generated. Pipeline complete."})

        yield sse({"type":"done"})

    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
