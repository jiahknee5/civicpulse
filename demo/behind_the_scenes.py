"""
CivicPulse — Behind the Scenes
Technical deep dive: data pipeline, risk methodology, agent internals, district scorecard
Port 7861
"""
import json, time, re
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import gradio as gr
from openai import OpenAI
from pathlib import Path
from datetime import datetime

HACK = Path(__file__).parent.parent
DATA_DIR = Path(__file__).parent / "data"
RAW_DATA = Path.home() / "data"
MODEL = "nemotron:70b"
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

# ── Load pre-built risk profiles ───────────────────────────────────────────────
with open(DATA_DIR / "zip_risk.json") as f:
    zip_risk_raw = json.load(f)

zip_df = pd.DataFrame(zip_risk_raw).dropna(subset=["avg_lat", "avg_lon"])
zip_df["risk_score"] = zip_df["risk_score"].fillna(0)
zip_df["risk_rank"] = zip_df["risk_score"].rank(ascending=False).astype(int)

with open(DATA_DIR / "county_summary.json") as f:
    summary = json.load(f)
with open(DATA_DIR / "top_risk_zips.json") as f:
    top_zips = json.load(f)
with open(DATA_DIR / "cdc_averages.json") as f:
    cdc_avg = json.load(f)

# ── McKinsey CSS ───────────────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
body, .gradio-container {
    background: #f8fafc !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
}
.gradio-container { max-width: 1500px !important; }
footer { display: none !important; }
.tab-nav button {
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    color: #64748b !important;
    border-bottom: 2px solid transparent !important;
}
.tab-nav button.selected {
    color: #0f172a !important;
    border-bottom-color: #dc2626 !important;
}
button.primary {
    background: #0f172a !important;
    border: none !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    letter-spacing: 0.5px !important;
    border-radius: 8px !important;
}
button.primary:hover { background: #1e293b !important; }
.agent-box textarea {
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
    line-height: 1.7 !important;
    background: #ffffff !important;
    color: #1e293b !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 6px !important;
}
.agent-box .label-wrap { display: none !important; }
"""

HEADER = """
<div style="padding:28px 48px 20px;background:#ffffff;border-bottom:2px solid #e2e8f0;margin-bottom:0;">
  <div style="display:flex;justify-content:space-between;align-items:flex-end;">
    <div>
      <div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:3px;margin-bottom:6px;font-family:Inter,sans-serif;">
        CivicPulse · Technical Reference
      </div>
      <div style="font-size:28px;font-weight:300;color:#0f172a;letter-spacing:-0.5px;font-family:Inter,sans-serif;">
        Behind the Scenes
      </div>
      <div style="font-size:12px;color:#64748b;margin-top:4px;font-family:Inter,sans-serif;">
        Data pipeline · Risk methodology · Agent internals · District scorecard
      </div>
    </div>
    <div style="text-align:right;font-size:11px;color:#94a3b8;font-family:Inter,sans-serif;line-height:1.8;">
      NVIDIA DGX Spark (GB10) · Nemotron 70B<br>
      {total_biz:,} businesses · {total_insp:,} inspections · {total_crit:,} critical violations
    </div>
  </div>
</div>
""".format(
    total_biz=summary["total_businesses"],
    total_insp=summary.get("total_inspections", 0),
    total_crit=summary["total_critical"],
)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: DATA FOUNDATION
# ═══════════════════════════════════════════════════════════════════════════════

DATASETS = [
    {
        "name": "Food Businesses",
        "file": "SCC_DEH_Food_Data_BUSINESS_20260306.csv",
        "dept": "Dept. of Environmental Health",
        "rows": 8588,
        "role": "Business registry. Provides lat/lon for geographic join, names for display and coaching messages.",
        "key_fields": "business_id, name, address, postal_code, latitude, longitude",
        "drives": "Geographic join backbone — all other datasets anchor to this",
        "color": "#dc2626",
    },
    {
        "name": "Food Inspections",
        "file": "SCC_DEH_Food_Data_INSPECTIONS_20260306.csv",
        "dept": "Dept. of Environmental Health",
        "rows": 95000,
        "role": "Inspection outcomes (Red/Yellow/Green) per visit. Core signal for repeat offender detection.",
        "key_fields": "inspection_id, business_id, date, result (R/Y/G)",
        "drives": "Red count, repeat offenders → 50% of risk score",
        "color": "#dc2626",
    },
    {
        "name": "Food Violations",
        "file": "SCC_DEH_Food_Data_VIOLATIONS_20260306.csv",
        "dept": "Dept. of Environmental Health",
        "rows": 26000,
        "role": "Individual violation records with critical flag and description. Powers the pre-inspection coaching letter.",
        "key_fields": "violation_id, inspection_id, critical (bool), DESCRIPTION",
        "drives": "Critical violation count/biz → 25% of risk score + Messenger coaching content",
        "color": "#dc2626",
    },
    {
        "name": "Crime Reports",
        "file": "Crime_Reports_20260306.csv",
        "dept": "San Jose Police Dept.",
        "rows": 259660,
        "role": "SJPD incident reports with address. Matched to food-business streets to measure co-location of crime and food risk. Covers San Jose only.",
        "key_fields": "report_id, date, address, category",
        "drives": "Crime per business → 25% of risk score. Also justifies cross-agency coordination ask.",
        "color": "#7c3aed",
    },
    {
        "name": "Census ACS (Income/Poverty)",
        "file": "census_income.csv (manual)",
        "dept": "US Census Bureau — ACS 2022",
        "rows": 62,
        "role": "ZIP-level median household income and poverty rate. The equity dimension — converts food safety failures into a health equity story.",
        "key_fields": "zip, median_income, poverty_pop, total_pop",
        "drives": "Poverty rate percentile → 25% of risk score. Context for every agent output.",
        "color": "#2563eb",
    },
    {
        "name": "CDC PLACES Health Outcomes",
        "file": "cdc_places.csv",
        "dept": "CDC — PLACES 2023",
        "rows": 16320,
        "role": "Census-tract-level health measures: food insecurity, diabetes, obesity, mental health. Joined to ZIPs via nearest-centroid. Adds health context to Analyst prompts.",
        "key_fields": "locationid, measureid, data_value, geolocation",
        "drives": "Health context in Analyst reasoning. Not in risk score formula.",
        "color": "#16a34a",
    },
]

JOIN_HTML = """
<div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:28px;margin-top:16px;">
  <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:2px;margin-bottom:20px;font-family:Inter,sans-serif;">Join Architecture</div>
  <div style="font-family:monospace;font-size:13px;line-height:2;color:#475569;background:#f8fafc;padding:20px;border-radius:8px;">
    <span style="color:#dc2626;font-weight:600;">Food Businesses</span> (8,588 records)<br>
    &nbsp;&nbsp;├── <span style="color:#64748b;">business_id</span> → Inspections → <span style="color:#dc2626;">Red/Yellow/Green + date</span><br>
    &nbsp;&nbsp;├── <span style="color:#64748b;">business_id</span> → Violations → <span style="color:#dc2626;">Critical count + descriptions</span><br>
    &nbsp;&nbsp;├── <span style="color:#64748b;">postal_code[:5]</span> → Census ZIP → <span style="color:#2563eb;">income, poverty rate</span><br>
    &nbsp;&nbsp;├── <span style="color:#64748b;">address → street_norm</span> → Crime addresses → <span style="color:#7c3aed;">incidents on food streets</span><br>
    &nbsp;&nbsp;└── <span style="color:#64748b;">lat/lon → nearest centroid</span> → CDC tracts → <span style="color:#16a34a;">food insecurity, diabetes %</span><br>
    <br>
    <span style="color:#0f172a;font-weight:600;">Output: 92 ZIP-level risk profiles</span><br>
    &nbsp;&nbsp;└── risk_score = pct_rank(crit/biz)×0.25 + pct_rank(red/biz)×0.25 + pct_rank(poverty)×0.25 + pct_rank(crime/biz)×0.25
  </div>
  <div style="margin-top:16px;font-size:12px;color:#94a3b8;font-family:Inter,sans-serif;">
    <strong style="color:#475569;">Street normalization</strong> strips block numbers ("1400 Block of Story Rd" → "Story Rd") before matching crime records to food business addresses.<br>
    <strong style="color:#475569;">CDC spatial join</strong> uses scipy cKDTree nearest-neighbor on tract centroids vs ZIP centroids derived from business coordinates.
  </div>
</div>
"""

def make_dataset_cards():
    cards = []
    for d in DATASETS:
        cards.append(f"""
<div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:10px;padding:20px;border-top:3px solid {d['color']};">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px;">
    <div>
      <div style="font-size:14px;font-weight:600;color:#0f172a;font-family:Inter,sans-serif;">{d['name']}</div>
      <div style="font-size:11px;color:#94a3b8;margin-top:2px;font-family:Inter,sans-serif;">{d['dept']}</div>
    </div>
    <div style="font-size:22px;font-weight:300;color:{d['color']};font-family:Inter,sans-serif;">{d['rows']:,}</div>
  </div>
  <div style="font-size:12px;color:#475569;line-height:1.6;margin-bottom:10px;font-family:Inter,sans-serif;">{d['role']}</div>
  <div style="font-size:11px;font-family:monospace;color:#64748b;background:#f8fafc;padding:6px 10px;border-radius:4px;margin-bottom:8px;">{d['key_fields']}</div>
  <div style="font-size:11px;color:{d['color']};font-weight:600;font-family:Inter,sans-serif;">→ {d['drives']}</div>
</div>""")
    return "\n".join(cards)

DATA_FOUNDATION_HTML = f"""
{HEADER}
<div style="padding:24px 48px;">
  <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:2px;margin-bottom:20px;font-family:Inter,sans-serif;">Source Datasets</div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;">
    {make_dataset_cards()}
  </div>
  {JOIN_HTML}
</div>
"""

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: RISK MAP
# ═══════════════════════════════════════════════════════════════════════════════

def make_risk_map():
    df = zip_df.copy()
    df["bubble_size"] = np.sqrt(df["businesses"].clip(lower=1)) * 2.5
    df["risk_label"] = df["risk_score"].round(0).astype(int).astype(str)
    fig = px.scatter_mapbox(
        df, lat="avg_lat", lon="avg_lon",
        color="risk_score", size="bubble_size", size_max=35,
        color_continuous_scale=["#22c55e", "#eab308", "#ef4444"],
        range_color=[20, 90],
        hover_name="zip",
        hover_data={
            "businesses": True, "red_count": True, "critical_violations": True,
            "poverty_rate": ":.1f", "risk_score": ":.0f",
            "avg_lat": False, "avg_lon": False, "bubble_size": False,
        },
        labels={
            "risk_score": "Risk Score", "businesses": "Food Businesses",
            "red_count": "Red Inspections", "critical_violations": "Critical Violations",
            "poverty_rate": "Poverty Rate %",
        },
        title="Compounding Risk by ZIP Code — Santa Clara County",
        height=560, zoom=9.5, center={"lat": 37.35, "lon": -121.9},
    )
    fig.update_layout(
        mapbox_style="carto-positron", template="plotly_white",
        coloraxis_colorbar=dict(title="Risk Score", tickvals=[20, 40, 60, 80]),
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(family="Inter, sans-serif"),
    )
    return fig

def make_risk_table():
    top = zip_df.nlargest(20, "risk_score")[[
        "zip", "risk_score", "businesses", "red_count",
        "critical_violations", "repeat_offenders", "poverty_rate", "crime_on_food_streets"
    ]].copy()
    top["risk_score"] = top["risk_score"].round(1)
    top["poverty_rate"] = top["poverty_rate"].round(1)
    top.columns = ["ZIP", "Risk Score", "Businesses", "Red Inspections",
                   "Critical Violations", "Repeat Offenders", "Poverty %", "Crime on Food Streets"]
    return top

def make_score_breakdown():
    """Bar chart showing each risk component for top 10 ZIPs."""
    top10 = zip_df.nlargest(10, "risk_score").copy()
    top10["crit_component"] = top10["crit_per_biz"].rank(pct=True) * 25
    top10["red_component"]  = top10["red_per_biz"].rank(pct=True) * 25
    top10["pov_component"]  = top10["poverty_rate"].rank(pct=True) * 25
    top10["crime_component"]= top10["crime_per_biz"].rank(pct=True) * 25

    fig = go.Figure()
    components = [
        ("crit_component",  "Critical Violations/Biz (25%)", "#dc2626"),
        ("red_component",   "Red Inspections/Biz (25%)",     "#f97316"),
        ("pov_component",   "Poverty Rate (25%)",            "#d97706"),
        ("crime_component", "Crime/Biz (25%)",               "#7c3aed"),
    ]
    for col, label, color in components:
        fig.add_trace(go.Bar(
            name=label, x=top10["zip"].astype(str), y=top10[col],
            marker_color=color, opacity=0.85,
        ))
    fig.update_layout(
        barmode="stack", title="Risk Score Decomposition — Top 10 ZIP Codes",
        xaxis_title="ZIP Code", yaxis_title="Score Component (max 100)",
        template="plotly_white", height=380,
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(family="Inter, sans-serif", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: AGENT DEEP DIVE
# ═══════════════════════════════════════════════════════════════════════════════

AGENT_COLORS = {
    "SENTINEL": "#16a34a", "ANALYST": "#7c3aed",
    "ADVISOR": "#2563eb",  "MESSENGER": "#d97706",
}

def render_log_detailed(entries):
    if not entries:
        return '<div style="background:#f8fafc;padding:20px;border-radius:8px;border:1px solid #e2e8f0;font-size:12px;color:#94a3b8;font-family:Inter,sans-serif;">Pipeline idle — select a ZIP and click Run.</div>'
    lines = []
    for e in entries:
        color = AGENT_COLORS.get(e["agent"], "#64748b")
        timing = f' <span style="color:#cbd5e1;font-size:10px;">+{e.get("ms","")}</span>' if e.get("ms") else ""
        flagged = '<span style="color:#dc2626;font-weight:700;background:#fee2e2;padding:1px 5px;border-radius:3px;">FLAGGED</span>'
        msg = e["msg"].replace("FLAGGED", flagged)
        lines.append(
            f'<div style="padding:7px 0;border-bottom:1px solid #f1f5f9;font-size:11.5px;line-height:1.6;">'
            f'<span style="color:#94a3b8;font-family:monospace;">{e["ts"]}</span>'
            f'<span style="color:{color};font-weight:700;margin:0 10px;font-size:10px;text-transform:uppercase;letter-spacing:1.5px;">{e["agent"]}</span>'
            f'<span style="color:#475569;font-family:Inter,sans-serif;">{msg}</span>{timing}</div>'
        )
    return (
        '<div style="background:#f8fafc;padding:16px 20px;border-radius:8px;'
        'max-height:320px;overflow-y:auto;border:1px solid #e2e8f0;">'
        + "".join(lines) + "</div>"
    )

AGENT_PROMPTS = {
    "SENTINEL": "Rule-based — no LLM call. Computes percentile composite score from pre-built ZIP profiles. Threshold = 70.",
    "ANALYST": (
        "System: Cross-silo analysis agent. Input: ZIP stats + top violators + CDC averages. "
        "Output format: SEVERITY | ROOT CAUSES | AFFECTED POPULATION | CROSS-SILO INSIGHT | 30-DAY PRIORITIES. "
        "Max 280 tokens. Temperature 0.2."
    ),
    "ADVISOR": (
        "System: Health Officer brief writer. Recipient: senior county official. "
        "Output format: ## SITUATION | ## RECOMMENDED ACTIONS | ## CROSS-AGENCY COORDINATION | ## EXPECTED IMPACT. "
        "Max 220 tokens. Temperature 0.2."
    ),
    "MESSENGER": (
        "System: Restaurant coaching letter writer. Recipient: restaurant manager. "
        "Output: 'Dear Manager,' + 3 numbered specific fixes + one next-step sentence. "
        "Max 180 tokens. Temperature 0.3."
    ),
}

zip_choices_deep = [
    f"ZIP {z['zip']} — Risk {z['risk_score']:.0f}"
    for z in top_zips
]

def get_zip_deep(sel):
    if not sel:
        return None
    return next((z for z in top_zips if z["zip"] == sel.split()[1]), None)

def run_deep_pipeline(zip_sel):
    z = get_zip_deep(zip_sel)
    if not z:
        yield render_log_detailed([]), "", "", "", "", ""
        return

    log = []
    timings = {}

    def L(agent, msg, ms=None):
        entry = {"ts": datetime.now().strftime("%H:%M:%S.%f")[:-3], "agent": agent, "msg": msg}
        if ms:
            entry["ms"] = f"{ms}ms"
        log.append(entry)
        return render_log_detailed(log)

    # ── SENTINEL ──────────────────────────────────────────────────────────────
    t0 = time.time()
    lh = L("SENTINEL", f"Loading {summary['total_businesses']:,} business profiles from zip_risk.json...")
    yield lh, AGENT_PROMPTS["SENTINEL"], "", "", "", ""

    lh = L("SENTINEL", f"Evaluating ZIP {z['zip']}: score={z['risk_score']:.1f} | threshold=70")
    lh = L("SENTINEL", f"FLAGGED → {z['total_red']} Red | {z['total_critical']} critical | {z['repeat_offenders']} repeat | {z['poverty_rate']}% poverty")
    ms = int((time.time() - t0) * 1000)
    lh = L("SENTINEL", f"→ Passing to ANALYST", ms=ms)

    sentinel_out = (
        f"SEVERITY: {min(5, max(1, int(z['risk_score'] / 18)))}\n"
        f"FLAG: YES\n"
        f"SCORE: {z['risk_score']:.1f}/100\n\n"
        f"Signals:\n"
        f"  Red inspections:    {z['total_red']}\n"
        f"  Critical violations:{z['total_critical']}\n"
        f"  Repeat offenders:   {z['repeat_offenders']}\n"
        f"  Crime on food st.:  {z['crime_on_food_streets']:,}\n"
        f"  Poverty rate:       {z['poverty_rate']}%\n\n"
        f"Latency: {ms}ms (rule-based, no LLM)"
    )
    yield lh, AGENT_PROMPTS["SENTINEL"], sentinel_out, "", "", ""

    # ── ANALYST ──────────────────────────────────────────────────────────────
    worst_txt = "\n".join(
        f"  - {b['name']}: {b['critical_violations']} critical, {b['red_inspections']} Red — {b.get('top_violations','')[:70]}"
        for b in z["worst_businesses"][:3]
    )
    analyst_prompt = (
        f"FLAGGED ZIP: {z['zip']} — Risk Score {z['risk_score']:.0f}/100\n\n"
        f"SIGNALS: {z['total_red']} Red | {z['total_critical']} critical | "
        f"{z['repeat_offenders']} repeat offenders | {z['crime_on_food_streets']:,} crimes | "
        f"{z['poverty_rate']}% poverty | ${z['median_income']:,} income\n\n"
        f"TOP VIOLATORS:\n{worst_txt}\n\n"
        f"CDC context: food insecurity {cdc_avg['food_insecurity_pct']:.1f}% | diabetes {cdc_avg['diabetes_pct']:.1f}%\n\n"
        f"Provide structured assessment."
    )

    lh = L("ANALYST", f"Context loaded: {len(analyst_prompt)} chars | max_tokens=600 | temp=0.2")
    yield lh, f"[Prompt sent to Nemotron 70B]\n\n{analyst_prompt}", sentinel_out, "⏳ Streaming from Nemotron 70B...", "", ""

    t0 = time.time()
    analyst_text = ""
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are ANALYST in CivicPulse. " + AGENT_PROMPTS["ANALYST"]},
            {"role": "user", "content": analyst_prompt},
        ],
        stream=True, max_tokens=600, temperature=0.2,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        analyst_text += delta
        yield lh, f"[Prompt sent to Nemotron 70B]\n\n{analyst_prompt}", sentinel_out, analyst_text, "", ""

    ms = int((time.time() - t0) * 1000)
    lh = L("ANALYST", f"Complete: {len(analyst_text)} chars | {ms}ms | → ADVISOR", ms=ms)
    yield lh, f"[Prompt sent to Nemotron 70B]\n\n{analyst_prompt}", sentinel_out, analyst_text, "", ""

    # ── ADVISOR ───────────────────────────────────────────────────────────────
    advisor_prompt = (
        f"ZIP {z['zip']} — {z['businesses']} businesses, {z['total_red']} Red, "
        f"{z['total_critical']} critical, {z['repeat_offenders']} repeat. Poverty {z['poverty_rate']}%.\n\n"
        f"ANALYST:\n{analyst_text}\n\nWrite the Health Officer brief."
    )
    lh = L("ADVISOR", f"Generating Health Officer brief | max_tokens=500 | temp=0.2")
    yield lh, f"[Prompt]\n\n{advisor_prompt}", sentinel_out, analyst_text, "⏳ Streaming...", ""

    t0 = time.time()
    advisor_text = ""
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are ADVISOR in CivicPulse. " + AGENT_PROMPTS["ADVISOR"]},
            {"role": "user", "content": advisor_prompt},
        ],
        stream=True, max_tokens=500, temperature=0.2,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        advisor_text += delta
        yield lh, f"[Prompt]\n\n{advisor_prompt}", sentinel_out, analyst_text, advisor_text, ""

    ms = int((time.time() - t0) * 1000)
    lh = L("ADVISOR", f"Complete: {len(advisor_text)} chars | {ms}ms | → MESSENGER", ms=ms)
    yield lh, f"[Prompt]\n\n{advisor_prompt}", sentinel_out, analyst_text, advisor_text, ""

    # ── MESSENGER ─────────────────────────────────────────────────────────────
    top_biz = z["worst_businesses"][0] if z["worst_businesses"] else None
    if top_biz:
        messenger_prompt = (
            f"Restaurant: {top_biz['name']} ({top_biz['city']}, ZIP {z['zip']})\n"
            f"Red: {top_biz['red_inspections']} | Critical: {top_biz['critical_violations']}\n"
            f"Top violations: {top_biz.get('top_violations','temperature control, labeling')}\n\n"
            f"Write the pre-inspection coaching letter."
        )
        lh = L("MESSENGER", f"Target: {top_biz['name']} | max_tokens=350 | temp=0.3")
        yield lh, f"[Prompt]\n\n{messenger_prompt}", sentinel_out, analyst_text, advisor_text, "⏳ Streaming..."

        t0 = time.time()
        messenger_text = ""
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are MESSENGER in CivicPulse. " + AGENT_PROMPTS["MESSENGER"]},
                {"role": "user", "content": messenger_prompt},
            ],
            stream=True, max_tokens=350, temperature=0.3,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            messenger_text += delta
            yield lh, f"[Prompt]\n\n{messenger_prompt}", sentinel_out, analyst_text, advisor_text, messenger_text

        ms = int((time.time() - t0) * 1000)
        lh = L("MESSENGER", f"Complete: {len(messenger_text)} chars | {ms}ms | ✓ Pipeline done", ms=ms)
    else:
        messenger_text = "No priority businesses for this ZIP."

    yield lh, "", sentinel_out, analyst_text, advisor_text, messenger_text

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: DISTRICT SCORECARD
# ═══════════════════════════════════════════════════════════════════════════════

ZIP_TO_DISTRICT = {
    "95020": 1, "95037": 1, "95046": 1, "95138": 1, "95139": 1,
    "95119": 1, "95123": 1, "95136": 1, "95111": 1,
    "95014": 2, "95070": 2, "95030": 2, "95032": 2, "95008": 2,
    "95129": 2, "95117": 2, "95128": 2, "95124": 2, "95125": 2, "95118": 2, "95120": 2,
    "95116": 3, "95122": 3, "95127": 3, "95148": 3, "95121": 3,
    "95035": 3, "95132": 3, "95133": 3, "95134": 3,
    "95112": 4, "95113": 4, "95110": 4, "95126": 4, "95131": 4, "95135": 4,
    "94022": 5, "94024": 5, "94040": 5, "94041": 5, "94043": 5,
    "94085": 5, "94086": 5, "94087": 5, "94089": 5,
    "94301": 5, "94303": 5, "94306": 5,
    "95050": 5, "95051": 5, "95054": 5,
}

DISTRICT_NAMES = {
    1: "South County — Morgan Hill, Gilroy",
    2: "West Valley — Cupertino, Saratoga, Los Gatos",
    3: "East San Jose — Milpitas",
    4: "Central San Jose — Downtown",
    5: "North County — Palo Alto, Mountain View, Sunnyvale",
}

def make_district_data():
    df = zip_df.copy()
    df["district"] = df["zip"].astype(str).map(ZIP_TO_DISTRICT)
    df_mapped = df.dropna(subset=["district"])
    df_mapped["district"] = df_mapped["district"].astype(int)

    rows = []
    total_red = df_mapped["red_count"].sum()
    total_crit = df_mapped["critical_violations"].sum()
    total_repeat = df_mapped["repeat_offenders"].sum()
    total_biz = df_mapped["businesses"].sum()

    for d in [1, 2, 3, 4, 5]:
        sub = df_mapped[df_mapped["district"] == d]
        if sub.empty:
            continue
        rows.append({
            "District": f"District {d}",
            "Geography": DISTRICT_NAMES[d],
            "Businesses": int(sub["businesses"].sum()),
            "Red Inspections": int(sub["red_count"].sum()),
            "Critical Violations": int(sub["critical_violations"].sum()),
            "Repeat Offenders": int(sub["repeat_offenders"].sum()),
            "Avg Poverty %": round(sub["poverty_rate"].mean(), 1),
            "% of County Red": round(sub["red_count"].sum() / max(1, total_red) * 100, 1),
            "% of County Biz": round(sub["businesses"].sum() / max(1, total_biz) * 100, 1),
        })
    return pd.DataFrame(rows)

def make_district_chart():
    df = make_district_data()
    if df.empty:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Bar(name="% of County Businesses", x=df["District"],
                         y=df["% of County Biz"], marker_color="#cbd5e1", opacity=0.9))
    fig.add_trace(go.Bar(name="% of County Red Inspections", x=df["District"],
                         y=df["% of County Red"], marker_color="#dc2626", opacity=0.8))
    fig.update_layout(
        barmode="group",
        title="District Share of County Food Safety Problems vs. Business Count",
        xaxis_title="Supervisorial District",
        yaxis_title="% of County Total",
        template="plotly_white", height=360,
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(family="Inter, sans-serif", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=40, r=20, t=60, b=40),
    )
    for _, row in df.iterrows():
        if row["% of County Red"] > row["% of County Biz"] * 1.25:
            fig.add_annotation(
                x=row["District"], y=row["% of County Red"] + 1,
                text="⚠", showarrow=False, font=dict(size=14),
            )
    return fig

# ═══════════════════════════════════════════════════════════════════════════════
# GRADIO APP
# ═══════════════════════════════════════════════════════════════════════════════

with gr.Blocks(title="CivicPulse — Behind the Scenes", css=CSS) as app:

    gr.HTML(HEADER)

    with gr.Tabs():

        # ── Tab 1: Data Foundation ─────────────────────────────────────────────
        with gr.Tab("📊  Data Foundation"):
            gr.HTML(DATA_FOUNDATION_HTML)

        # ── Tab 2: Risk Map & Scoring ──────────────────────────────────────────
        with gr.Tab("🗺  Risk Map & Scoring"):
            gr.HTML("""
            <div style="padding:20px 48px 0;font-family:Inter,sans-serif;">
              <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px;">Risk Score = Percentile rank across 4 signals × 25% each</div>
              <div style="font-size:13px;color:#475569;">Bubble size = number of food businesses. Color = composite risk score (green → red).</div>
            </div>
            """)
            risk_map_plot = gr.Plot(value=make_risk_map)
            gr.HTML('<div style="padding:0 48px;"><div style="height:1px;background:#e2e8f0;margin:8px 0;"></div></div>')
            with gr.Row():
                with gr.Column(scale=1):
                    gr.HTML('<div style="padding:0 0 8px;font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:2px;font-family:Inter,sans-serif;">Score Decomposition — Top 10 ZIPs</div>')
                    score_chart = gr.Plot(value=make_score_breakdown)
                with gr.Column(scale=1):
                    gr.HTML('<div style="padding:0 0 8px;font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:2px;font-family:Inter,sans-serif;">Top 20 ZIP Codes by Risk Score</div>')
                    risk_table = gr.Dataframe(value=make_risk_table, interactive=False)

        # ── Tab 3: Agent Deep Dive ─────────────────────────────────────────────
        with gr.Tab("🤖  Agent Deep Dive"):
            gr.HTML("""
            <div style="padding:20px 48px 16px;font-family:Inter,sans-serif;">
              <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px;">Live pipeline with full prompts, token counts, and latency per agent</div>
              <div style="font-size:13px;color:#475569;">This is what the Command Center runs under the hood.</div>
            </div>
            """)
            with gr.Row():
                zip_dd_deep = gr.Dropdown(choices=zip_choices_deep, value=zip_choices_deep[0],
                                          label="ZIP Code", scale=3)
                run_deep_btn = gr.Button("▶  Run Deep Pipeline", variant="primary", scale=1)

            gr.HTML('<div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:2px;margin:8px 0 4px;font-family:Inter,sans-serif;">Agent Communication Log (with timing)</div>')
            deep_log = gr.HTML(render_log_detailed([]))

            with gr.Row():
                gr.HTML('<div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:2px;font-family:Inter,sans-serif;">Prompt Sent →</div>')
            prompt_box = gr.Textbox(label="Last Prompt", lines=8, interactive=False, elem_classes="agent-box")

            gr.HTML('<div style="height:1px;background:#e2e8f0;margin:12px 0;"></div>')
            gr.HTML('<div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px;font-family:Inter,sans-serif;">Agent Outputs</div>')

            with gr.Row():
                deep_sentinel = gr.Textbox(label="SENTINEL (rule-based)", lines=12, interactive=False, elem_classes="agent-box")
                deep_analyst  = gr.Textbox(label="ANALYST",               lines=12, interactive=False, elem_classes="agent-box")
                deep_advisor  = gr.Textbox(label="ADVISOR",               lines=12, interactive=False, elem_classes="agent-box")
                deep_messenger= gr.Textbox(label="MESSENGER",             lines=12, interactive=False, elem_classes="agent-box")

            run_deep_btn.click(
                fn=run_deep_pipeline,
                inputs=[zip_dd_deep],
                outputs=[deep_log, prompt_box, deep_sentinel, deep_analyst, deep_advisor, deep_messenger],
            )

        # ── Tab 4: District Scorecard ──────────────────────────────────────────
        with gr.Tab("📋  District Scorecard"):
            gr.HTML("""
            <div style="padding:20px 48px 16px;font-family:Inter,sans-serif;">
              <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:2px;margin-bottom:4px;">5 Supervisorial Districts · ZIP-level aggregation</div>
              <div style="font-size:13px;color:#475569;">⚠ = district's share of Red inspections exceeds its share of businesses by &gt;25%</div>
            </div>
            """)
            district_chart = gr.Plot(value=make_district_chart)
            gr.HTML('<div style="padding:0 0 8px;font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:2px;font-family:Inter,sans-serif;">District Summary Table</div>')
            district_table = gr.Dataframe(value=make_district_data, interactive=False)
            gr.HTML("""
            <div style="padding:16px 0;font-size:12px;color:#94a3b8;font-family:Inter,sans-serif;">
              District boundaries approximated by ZIP code mapping. Crime data covers San Jose only (SJPD jurisdiction).
              Census poverty data from ACS 2022. Full data at ZIP level in the Risk Map tab.
            </div>
            """)

    gr.HTML("""
    <div style="text-align:center;padding:16px;border-top:1px solid #e2e8f0;margin-top:8px;">
      <span style="font-size:10px;color:#cbd5e1;font-family:Inter,sans-serif;letter-spacing:1px;text-transform:uppercase;">
        CivicPulse Behind the Scenes · Nemotron 70B · NVIDIA DGX Spark (GB10) · All inference on-device
      </span>
    </div>
    """)


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7861, share=False)
