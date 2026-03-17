"""
CivicPulse — Neighborhood Risk Intelligence
Runs on NVIDIA DGX Spark (GB10)
Four agents (Sentinel → Analyst → Advisor → Messenger) via Nemotron 70B + Ollama
"""
import json
import gradio as gr
import pandas as pd
import numpy as np
import plotly.express as px
from openai import OpenAI
from pathlib import Path

HACK = Path.home() / "hackathon"
OLLAMA_URL = "http://localhost:11434/v1"
MODEL = "nemotron:70b"

client = OpenAI(base_url=OLLAMA_URL, api_key="ollama")

# Load risk profiles
with open(HACK / "zip_risk.json") as f:
    zip_risk_raw = json.load(f)

zip_df = pd.DataFrame(zip_risk_raw)
zip_df = zip_df.dropna(subset=["avg_lat", "avg_lon"])
zip_df["risk_score"] = zip_df["risk_score"].fillna(0)
zip_df["risk_rank"] = zip_df["risk_score"].rank(ascending=False).astype(int)

top_zips = zip_df.nlargest(20, "risk_score")["zip"].tolist()

def get_stats(zip_code):
    rows = [r for r in zip_risk_raw if str(r.get("zip")) == str(zip_code)]
    if not rows:
        return None
    r = rows[0]
    tv = r.get("top_violators") or []
    top_v_text = "\n".join(
        f"  • {v['name']} — {v['critical_violations']} critical, {v['red_inspections']} Red"
        for v in tv[:3]
    )
    total_insp = max(1, r.get("red_count", 0) + r.get("yellow_count", 0) + r.get("green_count", 0))
    return {
        **r,
        "top_v_text": top_v_text or "  None",
        "crit_per_biz": r.get("critical_violations", 0) / max(1, r.get("businesses", 1)),
        "red_pct": r.get("red_count", 0) / total_insp * 100,
        "risk_rank": int(zip_df[zip_df["zip"] == str(zip_code)]["risk_rank"].values[0])
            if str(zip_code) in zip_df["zip"].values else "?",
    }

# --- Map ---
def make_risk_map():
    df = zip_df.copy()
    df["bubble_size"] = np.sqrt(df["businesses"].clip(lower=1)) * 2.5
    df["risk_label"] = df["risk_score"].round(0).astype(int).astype(str)

    fig = px.scatter_mapbox(
        df,
        lat="avg_lat", lon="avg_lon",
        color="risk_score",
        size="bubble_size",
        size_max=35,
        color_continuous_scale=["#22c55e", "#eab308", "#ef4444"],
        range_color=[20, 90],
        hover_name="zip",
        hover_data={
            "businesses": True,
            "red_count": True,
            "critical_violations": True,
            "poverty_rate": ":.1f",
            "risk_score": ":.0f",
            "avg_lat": False, "avg_lon": False, "bubble_size": False,
        },
        labels={
            "risk_score": "Risk Score",
            "businesses": "Food Businesses",
            "red_count": "Red Inspections",
            "critical_violations": "Critical Violations",
            "poverty_rate": "Poverty Rate %",
        },
        title="CivicPulse — Compounding Risk by ZIP Code",
        height=600,
        zoom=9.5,
        center={"lat": 37.35, "lon": -121.9},
    )
    fig.update_layout(
        mapbox_style="carto-positron",
        template="plotly_white",
        coloraxis_colorbar=dict(title="Risk Score", tickvals=[20, 40, 60, 80]),
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    return fig

def make_table():
    top = zip_df.nlargest(15, "risk_score")[[
        "zip", "risk_score", "businesses", "red_count",
        "critical_violations", "repeat_offenders", "poverty_rate", "crime_on_food_streets"
    ]].copy()
    top["risk_score"] = top["risk_score"].round(1)
    top["poverty_rate"] = top["poverty_rate"].round(1)
    top.columns = ["ZIP", "Risk Score", "Businesses", "Red Inspections",
                   "Critical Violations", "Repeat Offenders", "Poverty %", "Crime on Food Streets"]
    return top

# --- Stats panel ---
def stats_panel(zip_code):
    s = get_stats(zip_code)
    if not s:
        return "ZIP not found."
    food_insec = s.get("FOODINSECU")
    diabetes   = s.get("DIABETES")
    food_str = f"\n| Food Insecurity (CDC) | {food_insec:.1f}% |" if food_insec else ""
    diab_str  = f"\n| Diabetes (CDC) | {diabetes:.1f}% |" if diabetes else ""
    return f"""### ZIP {s['zip']} — Risk Score: **{s['risk_score']:.0f}/100** (County Rank #{s['risk_rank']})

| Metric | Value |
|--------|-------|
| Food Businesses | {s.get('businesses', 0)} |
| Red (Failed) Inspections | {s.get('red_count', 0)} ({s['red_pct']:.0f}% of all inspections) |
| Critical Violations | {s.get('critical_violations', 0)} ({s['crit_per_biz']:.1f} per business) |
| Repeat Offenders (2+ Red) | {s.get('repeat_offenders', 0)} |
| Crime on Food Streets | {s.get('crime_on_food_streets', 0):,} |
| Poverty Rate | {s.get('poverty_rate', 0):.1f}% |
| Median Income | ${s.get('median_income', 0):,.0f} |{food_str}{diab_str}

**Top Violators:**
{s['top_v_text']}"""

# --- Agents ---
SENTINEL_PROMPT = """You are SENTINEL, fast-triage agent for CivicPulse.

ZIP: {zip}  |  Risk Score: {risk_score:.0f}/100  |  County Rank: #{risk_rank}

SIGNALS:
- Food businesses: {businesses}
- Red inspections: {red_count} ({red_pct:.0f}% fail rate)
- Critical violations: {critical_violations} ({crit_per_biz:.1f} per business, county avg: 3.2)
- Repeat offenders (2+ Red): {repeat_offenders}
- Crime on food streets: {crime_on_food_streets:,}
- Poverty rate: {poverty_rate:.1f}% (county median: 6.5%)
- Median income: ${median_income:,.0f} (county median: $153,000)

Output EXACTLY:
SEVERITY: [1-5, where 5 = cross-agency action needed immediately]
FLAG: [YES / MONITOR / NO]
REASON: [2 sentences max — what makes this neighborhood different]
TOP_CONCERN: [the single most alarming signal and why]"""

ANALYST_PROMPT = """You are ANALYST, cross-silo intelligence agent for CivicPulse.
Sentinel flagged ZIP {zip} (Risk Score {risk_score:.0f}/100, Rank #{risk_rank}).

SENTINEL OUTPUT:
{sentinel_output}

FULL DATA PROFILE:
- Food: {businesses} businesses, {red_count} Red inspections ({red_pct:.0f}%), {critical_violations} critical violations ({crit_per_biz:.1f}/biz), {repeat_offenders} repeat offenders
- Top violators:
{top_v_text}
- Crime: {crime_on_food_streets:,} incidents on food business streets
- Economic: {poverty_rate:.1f}% poverty, ${median_income:,.0f} median income
- Health context: SCC food-insecure tracts average +28% more diabetes, +23% more obesity vs food-secure tracts

Provide a structured analysis:

1. SEVERITY — How severe is the compounding risk here, specifically?
2. ROOT CAUSES — What systemic factors explain this pattern?
3. AFFECTED POPULATION — Who is at risk and how many people?
4. CROSS-SILO INSIGHT — What does combining food + crime + poverty reveal that no single dataset shows?
5. 30-DAY PRIORITIES — Three specific actions, each with a named responsible party.

Be direct. Use the numbers. No filler."""

ADVISOR_PROMPT = """You are ADVISOR, action-planning agent for CivicPulse.

ANALYST FINDINGS for ZIP {zip}:
{analyst_output}

Generate a COUNTY HEALTH OFFICER BRIEF:

## Executive Summary
[2-3 sentences. Lead with the most urgent fact. What decision does she need to make today?]

## Recommended Actions — Next 30 Days
1. [Action, responsible party, measurable outcome]
2. [Action, responsible party, measurable outcome]
3. [Action, responsible party, measurable outcome]

## Cross-Agency Coordination Required
[Which departments, why, and what specifically they need to do]

## Resource Recommendation
[Specific program or allocation to address the root cause — with a dollar range or staffing estimate]

## Board of Supervisors Framing
[How to present this in 2 sentences at the next board meeting]

Write for a senior official. Every sentence must drive toward a decision."""

def run_pipeline(zip_code):
    s = get_stats(zip_code)
    if not s:
        yield "ZIP not found.", "", ""
        return

    # Sentinel
    sentinel_text = ""
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": SENTINEL_PROMPT.format(**s)}],
        stream=True,
        max_tokens=250,
        temperature=0.1,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        sentinel_text += delta
        yield sentinel_text, "⏳ Waiting for Sentinel to complete...", "⏳ Waiting for Analyst..."

    # Analyst
    analyst_text = ""
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": ANALYST_PROMPT.format(**s, sentinel_output=sentinel_text)}],
        stream=True,
        max_tokens=700,
        temperature=0.2,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        analyst_text += delta
        yield sentinel_text, analyst_text, "⏳ Waiting for Analyst to complete..."

    # Advisor
    advisor_text = ""
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": ADVISOR_PROMPT.format(zip=s["zip"], analyst_output=analyst_text)}],
        stream=True,
        max_tokens=700,
        temperature=0.2,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        advisor_text += delta
        yield sentinel_text, analyst_text, advisor_text

# --- UI ---
DARK_CSS = """
body { background: #0a0a0a !important; }
.gradio-container { background: #0a0a0a !important; max-width: 1400px !important; }
.agent-label { font-family: monospace !important; font-size: 13px !important; }
"""

with gr.Blocks(theme=gr.themes.Base(primary_hue="red", neutral_hue="slate"),
               css=DARK_CSS, title="CivicPulse") as app:

    gr.Markdown("""
# CivicPulse
### Neighborhood Risk Intelligence — Santa Clara County
*Four agents · Nemotron 70B · OpenClaw · NVIDIA DGX Spark (GB10)*
""")

    with gr.Tabs():

        with gr.Tab("Risk Map"):
            gr.Markdown("ZIP codes sized by number of food businesses, colored by compounding risk score.")
            risk_plot = gr.Plot(value=make_risk_map)
            gr.Markdown("### Top 15 Highest-Risk ZIP Codes")
            risk_tbl = gr.Dataframe(value=make_table, interactive=False)

        with gr.Tab("Agent Analysis"):
            with gr.Row():
                zip_drop = gr.Dropdown(
                    choices=top_zips,
                    value=top_zips[0] if top_zips else None,
                    label="ZIP Code (top 20 by risk score)",
                    scale=2,
                )
                run_btn = gr.Button("▶  Run CivicPulse Analysis", variant="primary", scale=1)

            stats_md = gr.Markdown(value=lambda: stats_panel(top_zips[0]) if top_zips else "")
            zip_drop.change(fn=stats_panel, inputs=zip_drop, outputs=stats_md)

            gr.Markdown("---")
            gr.Markdown("*Analysis streams live from Nemotron 70B running locally on the GB10.*")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### SENTINEL — Triage")
                    sentinel_box = gr.Textbox(
                        label="Fast Triage · Nemotron 70B", lines=10,
                        elem_classes="agent-label", show_copy_button=True
                    )
                with gr.Column():
                    gr.Markdown("### ANALYST — Deep Reasoning")
                    analyst_box = gr.Textbox(
                        label="Cross-Silo Analysis · Nemotron 70B", lines=10,
                        elem_classes="agent-label", show_copy_button=True
                    )
                with gr.Column():
                    gr.Markdown("### ADVISOR — Health Officer Brief")
                    advisor_box = gr.Textbox(
                        label="Action Plan · Nemotron 70B", lines=10,
                        elem_classes="agent-label", show_copy_button=True
                    )

            run_btn.click(
                fn=run_pipeline,
                inputs=zip_drop,
                outputs=[sentinel_box, analyst_box, advisor_box],
            )

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
