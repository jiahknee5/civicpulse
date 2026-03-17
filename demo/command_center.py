"""
CivicPulse — Command Center
NVIDIA GB10 Hackathon | Human Impact Track
4-Agent Pipeline: SENTINEL → ANALYST → ADVISOR → MESSENGER
Nemotron 70B · NVIDIA DGX Spark (GB10) · All inference local
Port 7860
"""
import json, re
import gradio as gr
from openai import OpenAI
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent / "data"
MODEL = "nemotron:70b"
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

# ── Data ──────────────────────────────────────────────────────────────────────
with open(DATA_DIR / "top_risk_zips.json") as f:
    top_zips = json.load(f)
with open(DATA_DIR / "county_summary.json") as f:
    summary = json.load(f)
with open(DATA_DIR / "cdc_averages.json") as f:
    cdc_avg = json.load(f)

zip_choices = [
    f"ZIP {z['zip']} — Risk {z['risk_score']:.0f}  |  {z['total_red']} Red  |  "
    f"{z['total_critical']} Critical  |  Poverty {z['poverty_rate']}%"
    for z in top_zips
]

# ── Agent prompts ──────────────────────────────────────────────────────────────
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

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_zip(sel):
    if not sel:
        return None
    return next((z for z in top_zips if z["zip"] == sel.split()[1]), None)

def zip_stats_md(sel):
    z = get_zip(sel)
    if not z:
        return ""
    wb = z["worst_businesses"]
    biz_rows = "".join(
        f"| {'🔴' if b['red_inspections'] >= 2 else '🟡'} **{b['name'][:28]}** "
        f"| {b['city']} | {b['critical_violations']} | {b['red_inspections']} |\n"
        for b in wb[:4]
    )
    return f"""### ZIP {z['zip']} — Risk Score **{z['risk_score']:.0f}** / 100

| Metric | This ZIP | County Avg |
|--------|----------|------------|
| Food Businesses | {z['businesses']} | — |
| Red (Failed) Inspections | **{z['total_red']}** | — |
| Critical Violations | **{z['total_critical']}** | — |
| Repeat Offenders (2+ Red) | **{z['repeat_offenders']}** | — |
| Crime on Food Streets | {z['crime_on_food_streets']:,} | — |
| Poverty Rate | **{z['poverty_rate']}%** | 6.5% |
| Median Household Income | ${z['median_income']:,} | $153,000 |

**Top violating businesses:**

| | Name | City | Critical | Red |
|-|------|------|----------|-----|
{biz_rows}"""

# ── Agent log renderer ─────────────────────────────────────────────────────────
AGENT_COLORS = {
    "SENTINEL": "#16a34a",
    "ANALYST":  "#7c3aed",
    "ADVISOR":  "#2563eb",
    "MESSENGER":"#d97706",
}

def render_log(entries):
    lines = []
    for e in entries:
        color = AGENT_COLORS.get(e["agent"], "#64748b")
        msg = e["msg"].replace("FLAGGED", '<span style="color:#dc2626;font-weight:600;">FLAGGED</span>')
        lines.append(
            f'<div style="padding:6px 0;border-bottom:1px solid #f1f5f9;font-size:12px;line-height:1.6;">'
            f'<span style="color:#94a3b8;font-family:monospace;font-size:11px;">{e["ts"]}</span>'
            f'<span style="color:{color};font-weight:600;margin:0 10px;font-size:10px;'
            f'text-transform:uppercase;letter-spacing:1px;">{e["agent"]}</span>'
            f'<span style="color:#475569;">{msg}</span></div>'
        )
    inner = (
        "".join(lines) or
        '<span style="color:#94a3b8;font-size:12px;">Pipeline idle. Select a ZIP and click Run Analysis.</span>'
    )
    return (
        '<div style="background:#f8fafc;padding:16px 20px;border-radius:8px;'
        'max-height:400px;overflow-y:auto;border:1px solid #e2e8f0;">'
        + inner + "</div>"
    )

# ── Pipeline ───────────────────────────────────────────────────────────────────
def run_pipeline(zip_sel):
    z = get_zip(zip_sel)
    if not z:
        yield render_log([]), "ZIP not found.", "", "", ""
        return

    log = []
    def L(agent, msg):
        log.append({"ts": datetime.now().strftime("%H:%M:%S"), "agent": agent, "msg": msg})
        return render_log(log)

    # ── SENTINEL (rule-based, instant) ────────────────────────────────────────
    lh = L("SENTINEL", f"Scanning {summary['total_businesses']:,} businesses across {summary.get('total_zips', 92)} ZIP codes...")
    yield lh, "⚙ SENTINEL scanning...", "⏳ Waiting...", "⏳ Waiting...", ""

    lh = L("SENTINEL", f"FLAGGED {z['zip']} — score {z['risk_score']:.0f}/100 | {z['total_red']} Red | {z['total_critical']} critical | poverty {z['poverty_rate']}%")
    top_biz = z["worst_businesses"][0] if z["worst_businesses"] else None
    if top_biz:
        lh = L("SENTINEL", f"  Top violator: {top_biz['name']} — {top_biz['critical_violations']} critical, {top_biz['red_inspections']} Red")
    lh = L("SENTINEL", "→ Passing context to ANALYST")

    sentinel_out = (
        f"✓ Scan complete\n\n"
        f"ZIP flagged: {z['zip']}\n"
        f"Risk score: {z['risk_score']:.0f} / 100  (threshold: 70)\n\n"
        f"Signals:\n"
        f"  • {z['total_red']} failed inspections\n"
        f"  • {z['total_critical']} critical violations\n"
        f"  • {z['repeat_offenders']} repeat offenders (2+ Red)\n"
        f"  • {z['crime_on_food_streets']:,} crimes on food-business streets\n"
        f"  • {z['poverty_rate']}% poverty rate  (county: 6.5%)\n\n"
        f"→ Passed to ANALYST"
    )
    yield lh, sentinel_out, "⏳ ANALYST reasoning...", "⏳ Waiting...", ""

    # ── ANALYST (streaming) ────────────────────────────────────────────────────
    lh = L("ANALYST", f"Cross-correlating food safety + crime + poverty for ZIP {z['zip']}...")
    worst_txt = "\n".join(
        f"  - {b['name']} ({b['city']}): {b['critical_violations']} critical, "
        f"{b['red_inspections']} Red — {b.get('top_violations', '')[:70]}"
        for b in z["worst_businesses"][:3]
    )
    analyst_prompt = (
        f"FLAGGED ZIP: {z['zip']} — Risk Score {z['risk_score']:.0f}/100\n\n"
        f"SIGNALS:\n"
        f"- Businesses: {z['businesses']} | Red: {z['total_red']} | Critical: {z['total_critical']} | Repeat offenders: {z['repeat_offenders']}\n"
        f"- Crime on food streets: {z['crime_on_food_streets']:,} | Poverty: {z['poverty_rate']}% (county median 6.5%) | Income: ${z['median_income']:,} (county median $153K)\n"
        f"- County CDC avg — food insecurity: {cdc_avg['food_insecurity_pct']:.1f}% | diabetes: {cdc_avg['diabetes_pct']:.1f}%\n\n"
        f"TOP VIOLATING BUSINESSES:\n{worst_txt}\n\n"
        f"Note: temperature control = 37% of all critical violations countywide.\n\nProvide your structured assessment."
    )
    analyst_text = ""
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": ANALYST_SYS}, {"role": "user", "content": analyst_prompt}],
        stream=True, max_tokens=600, temperature=0.2,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        analyst_text += delta
        yield lh, sentinel_out, analyst_text, "⏳ Waiting for Analyst...", ""

    lh = L("ANALYST", f"Assessment complete → Passing to ADVISOR")
    yield lh, sentinel_out, analyst_text, "⏳ ADVISOR drafting brief...", ""

    # ── ADVISOR (streaming) ────────────────────────────────────────────────────
    lh = L("ADVISOR", f"Drafting County Health Officer brief for ZIP {z['zip']}...")
    advisor_prompt = (
        f"ZIP {z['zip']} — {z['businesses']} businesses, {z['total_red']} Red, "
        f"{z['total_critical']} critical violations, {z['repeat_offenders']} repeat offenders. "
        f"Poverty {z['poverty_rate']}%.\n\nANALYST ASSESSMENT:\n{analyst_text}\n\nWrite the Health Officer brief."
    )
    advisor_text = ""
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": ADVISOR_SYS}, {"role": "user", "content": advisor_prompt}],
        stream=True, max_tokens=500, temperature=0.2,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        advisor_text += delta
        yield lh, sentinel_out, analyst_text, advisor_text, "⏳ Waiting for Advisor..."

    lh = L("ADVISOR", "Health Officer brief complete → Passing to MESSENGER")
    yield lh, sentinel_out, analyst_text, advisor_text, "⏳ MESSENGER drafting coaching letter..."

    # ── MESSENGER (streaming) ─────────────────────────────────────────────────
    if top_biz:
        lh = L("MESSENGER", f"Generating pre-inspection coaching: {top_biz['name']} ({top_biz['city']})")
        lh = L("MESSENGER", f"  {top_biz['critical_violations']} critical violations · {top_biz['red_inspections']} Red · {top_biz.get('top_violations', '')[:60]}")
        messenger_prompt = (
            f"Restaurant: {top_biz['name']} ({top_biz['city']}, ZIP {z['zip']})\n"
            f"Failed inspections: {top_biz['red_inspections']} Red, {top_biz['critical_violations']} critical violations\n"
            f"Specific violations: {top_biz.get('top_violations', 'temperature control, labeling, handwash')}\n\n"
            f"Write the pre-inspection coaching letter."
        )
        messenger_text = ""
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": MESSENGER_SYS}, {"role": "user", "content": messenger_prompt}],
            stream=True, max_tokens=350, temperature=0.3,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            messenger_text += delta
            yield lh, sentinel_out, analyst_text, advisor_text, messenger_text

        lh = L("MESSENGER", f"Coaching letter sent to {top_biz['name']}")
        lh = L("MESSENGER", "Routing: Health Officer brief → IMMEDIATE · Restaurant coaching → SCHEDULED · ✓ Pipeline complete")
    else:
        messenger_text = "No priority businesses to coach in this ZIP."

    yield lh, sentinel_out, analyst_text, advisor_text, messenger_text


# ── CSS ────────────────────────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

body, .gradio-container {
    background: #f8fafc !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
}
.gradio-container { max-width: 1500px !important; }
footer { display: none !important; }

/* Agent output boxes */
.agent-box textarea {
    font-family: 'Inter', -apple-system, sans-serif !important;
    font-size: 13px !important;
    line-height: 1.7 !important;
    background: #ffffff !important;
    color: #1e293b !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    padding: 16px !important;
}
.agent-box .label-wrap { display: none !important; }

/* Run button */
button.primary {
    background: #0f172a !important;
    border: none !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    letter-spacing: 0.5px !important;
    border-radius: 8px !important;
}
button.primary:hover { background: #1e293b !important; }

/* Dropdown */
.wrap { border: 1px solid #e2e8f0 !important; background: #ffffff !important; border-radius: 8px !important; }

/* Stats strip */
.stats-strip { border-bottom: 2px solid #e2e8f0; }
"""

# ── HTML components ────────────────────────────────────────────────────────────
HEADER = """
<div style="padding:32px 48px 24px;background:#ffffff;border-bottom:2px solid #e2e8f0;margin-bottom:0;">
  <div style="display:flex;justify-content:space-between;align-items:flex-end;max-width:1400px;margin:0 auto;">
    <div>
      <div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:3px;margin-bottom:8px;font-family:Inter,sans-serif;">
        NVIDIA GB10 Hackathon · Human Impact Track
      </div>
      <div style="font-size:36px;font-weight:300;color:#0f172a;letter-spacing:-1px;font-family:Inter,sans-serif;">
        CivicPulse
      </div>
      <div style="font-size:13px;color:#64748b;margin-top:4px;font-family:Inter,sans-serif;">
        Neighborhood Risk Intelligence · Santa Clara County
      </div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:11px;color:#94a3b8;font-family:Inter,sans-serif;line-height:1.8;">
        NVIDIA DGX Spark (GB10)<br>
        Nemotron 70B · Ollama · OpenClaw<br>
        4 Agents · All inference on-device
      </div>
    </div>
  </div>
</div>
"""

def make_stats_html():
    return f"""
<div style="padding:20px 48px;background:#ffffff;border-bottom:1px solid #e2e8f0;margin-bottom:0;">
  <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:32px;max-width:1400px;margin:0 auto;">
    <div style="border-top:3px solid #dc2626;padding-top:12px;">
      <div style="font-size:32px;font-weight:300;color:#dc2626;font-family:Inter,sans-serif;">{summary['total_critical']:,}</div>
      <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px;font-family:Inter,sans-serif;">Critical Violations</div>
    </div>
    <div style="border-top:3px solid #d97706;padding-top:12px;">
      <div style="font-size:32px;font-weight:300;color:#d97706;font-family:Inter,sans-serif;">{summary['total_red']:,}</div>
      <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px;font-family:Inter,sans-serif;">Failed Inspections</div>
    </div>
    <div style="border-top:3px solid #dc2626;padding-top:12px;">
      <div style="font-size:32px;font-weight:300;color:#dc2626;font-family:Inter,sans-serif;">{summary['total_repeat_offenders']:,}</div>
      <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px;font-family:Inter,sans-serif;">Repeat Offenders</div>
    </div>
    <div style="border-top:3px solid #64748b;padding-top:12px;">
      <div style="font-size:32px;font-weight:300;color:#475569;font-family:Inter,sans-serif;">{summary['total_businesses']:,}</div>
      <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px;font-family:Inter,sans-serif;">Businesses Monitored</div>
    </div>
    <div style="border-top:3px solid #16a34a;padding-top:12px;">
      <div style="font-size:32px;font-weight:300;color:#16a34a;font-family:Inter,sans-serif;">4</div>
      <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px;font-family:Inter,sans-serif;">Active Agents</div>
    </div>
  </div>
</div>
"""

AGENT_HEADERS = """
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:#e2e8f0;margin-top:16px;border-radius:8px 8px 0 0;overflow:hidden;">
  <div style="padding:10px 16px;background:#f8fafc;">
    <div style="font-size:11px;font-weight:700;color:#16a34a;text-transform:uppercase;letter-spacing:2px;font-family:Inter,sans-serif;">Sentinel</div>
    <div style="font-size:10px;color:#94a3b8;margin-top:2px;font-family:Inter,sans-serif;">Fast triage · rule-based</div>
  </div>
  <div style="padding:10px 16px;background:#f8fafc;">
    <div style="font-size:11px;font-weight:700;color:#7c3aed;text-transform:uppercase;letter-spacing:2px;font-family:Inter,sans-serif;">Analyst</div>
    <div style="font-size:10px;color:#94a3b8;margin-top:2px;font-family:Inter,sans-serif;">Cross-silo reasoning · Nemotron 70B</div>
  </div>
  <div style="padding:10px 16px;background:#f8fafc;">
    <div style="font-size:11px;font-weight:700;color:#2563eb;text-transform:uppercase;letter-spacing:2px;font-family:Inter,sans-serif;">Advisor</div>
    <div style="font-size:10px;color:#94a3b8;margin-top:2px;font-family:Inter,sans-serif;">Health Officer brief · Nemotron 70B</div>
  </div>
  <div style="padding:10px 16px;background:#f8fafc;">
    <div style="font-size:11px;font-weight:700;color:#d97706;text-transform:uppercase;letter-spacing:2px;font-family:Inter,sans-serif;">Messenger</div>
    <div style="font-size:10px;color:#94a3b8;margin-top:2px;font-family:Inter,sans-serif;">Restaurant coaching · Nemotron 70B</div>
  </div>
</div>
"""

# ── UI ─────────────────────────────────────────────────────────────────────────
with gr.Blocks(title="CivicPulse — Command Center", css=CSS) as app:

    gr.HTML(HEADER)
    gr.HTML(make_stats_html())

    with gr.Row(elem_classes="controls"):
        zip_dd = gr.Dropdown(
            choices=zip_choices,
            value=zip_choices[0],
            label="Neighborhood — Flagged by Sentinel (Risk Score > 70)",
            scale=4,
        )
        run_btn = gr.Button("▶  Run Analysis", variant="primary", scale=1, size="lg")

    with gr.Row():
        with gr.Column(scale=1):
            zip_stats = gr.Markdown(value=zip_stats_md(zip_choices[0]))
        with gr.Column(scale=2):
            gr.HTML('<div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:2px;margin-bottom:6px;font-family:Inter,sans-serif;">Agent Communication Log</div>')
            agent_log_html = gr.HTML(render_log([]))

    gr.HTML(AGENT_HEADERS)

    with gr.Row():
        sentinel_box = gr.Textbox(label="", lines=18, interactive=False, elem_classes="agent-box",
            value="Waiting — SENTINEL will flag ZIP codes above risk threshold 70.")
        analyst_box = gr.Textbox(label="", lines=18, interactive=False, elem_classes="agent-box",
            value="Waiting for SENTINEL...")
        advisor_box = gr.Textbox(label="", lines=18, interactive=False, elem_classes="agent-box",
            value="Waiting for ANALYST...")
        messenger_box = gr.Textbox(label="", lines=18, interactive=False, elem_classes="agent-box",
            value="Waiting for ADVISOR...")

    gr.HTML("""
    <div style="text-align:center;padding:20px;margin-top:16px;border-top:1px solid #e2e8f0;">
      <span style="font-size:10px;color:#cbd5e1;font-family:Inter,sans-serif;letter-spacing:1px;text-transform:uppercase;">
        CivicPulse · Nemotron 70B · NVIDIA DGX Spark (GB10) · All inference on-device · No data leaves the machine
      </span>
    </div>
    """)

    zip_dd.change(fn=zip_stats_md, inputs=zip_dd, outputs=zip_stats)
    run_btn.click(
        fn=run_pipeline,
        inputs=[zip_dd],
        outputs=[agent_log_html, sentinel_box, analyst_box, advisor_box, messenger_box],
    )

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
