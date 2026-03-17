"""CivicPulse — Community Health Intelligence
NVIDIA GB10 Hackathon | Human Impact Track
4 Agents: SENTINEL → ANALYST → ADVISOR → MESSENGER
Nemotron 70B · NVIDIA DGX Spark (GB10) · All inference local
"""
import gradio as gr
import json
from openai import OpenAI
from pathlib import Path
from datetime import datetime

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
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
    f"ZIP {z['zip']} — Risk {z['risk_score']:.0f}  |  {z['total_red']} Red  |  {z['total_critical']} Critical  |  Poverty {z['poverty_rate']}%"
    for z in top_zips
]

# ── Prompts ───────────────────────────────────────────────────────────────────
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

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_zip(sel):
    if not sel:
        return None
    return next((z for z in top_zips if z["zip"] == sel.split()[1]), None)


def zip_stats_html(sel):
    z = get_zip(sel)
    if not z:
        return ""
    wb = z["worst_businesses"]

    biz_rows = ""
    for b in wb[:4]:
        dot = '<span style="color:#b91c1c;">●</span>' if b["red_inspections"] >= 2 else '<span style="color:#d97706;">●</span>'
        biz_rows += f"""<tr>
            <td style="padding:6px 10px;border-bottom:1px solid #e5e7eb;font-size:13px;">{dot} {b['name'][:28]}</td>
            <td style="padding:6px 10px;border-bottom:1px solid #e5e7eb;font-size:13px;color:#6b7280;">{b['city']}</td>
            <td style="padding:6px 10px;border-bottom:1px solid #e5e7eb;font-size:13px;font-weight:600;">{b['critical_violations']}</td>
            <td style="padding:6px 10px;border-bottom:1px solid #e5e7eb;font-size:13px;font-weight:600;color:#b91c1c;">{b['red_inspections']}</td>
        </tr>"""

    def metric_row(label, val, county):
        return f"""<tr>
            <td style="padding:5px 0;font-size:12px;color:#6b7280;border-bottom:1px solid #f3f4f6;">{label}</td>
            <td style="padding:5px 0;font-size:13px;font-weight:600;border-bottom:1px solid #f3f4f6;">{val}</td>
            <td style="padding:5px 0;font-size:12px;color:#9ca3af;border-bottom:1px solid #f3f4f6;">{county}</td>
        </tr>"""

    return f"""
    <div style="padding:20px 0;">
        <div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:2px;">Selected Neighborhood</div>
        <div style="font-size:24px;font-weight:300;color:#111827;margin:8px 0 4px;">ZIP {z['zip']}</div>
        <div style="font-size:13px;color:#6b7280;">Risk Score: <strong style="color:#111827;">{z['risk_score']:.0f}</strong> / 100</div>

        <table style="width:100%;border-collapse:collapse;margin-top:16px;">
            <tr><td style="font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;padding-bottom:6px;border-bottom:1px solid #d1d5db;">Metric</td>
                <td style="font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;padding-bottom:6px;border-bottom:1px solid #d1d5db;">This ZIP</td>
                <td style="font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;padding-bottom:6px;border-bottom:1px solid #d1d5db;">County</td></tr>
            {metric_row("Food Businesses", z['businesses'], "8,588")}
            {metric_row("Red Inspections", f"<span style='color:#b91c1c;'>{z['total_red']}</span>", "800")}
            {metric_row("Critical Violations", f"<span style='color:#b91c1c;'>{z['total_critical']}</span>", "9,255")}
            {metric_row("Repeat Offenders", f"<span style='color:#b91c1c;'>{z['repeat_offenders']}</span>", "161")}
            {metric_row("Crime on Food Streets", f"{z['crime_on_food_streets']:,}", "—")}
            {metric_row("Poverty Rate", f"{z['poverty_rate']}%", "6.5%")}
            {metric_row("Median Income", f"${z['median_income']:,}", "$153K")}
        </table>

        <div style="font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;margin-top:20px;padding-bottom:6px;border-bottom:1px solid #d1d5db;">Highest-Risk Businesses</div>
        <table style="width:100%;border-collapse:collapse;margin-top:4px;">
            <tr>
                <td style="font-size:10px;color:#9ca3af;padding:4px 10px;">Name</td>
                <td style="font-size:10px;color:#9ca3af;padding:4px 10px;">City</td>
                <td style="font-size:10px;color:#9ca3af;padding:4px 10px;">Crit.</td>
                <td style="font-size:10px;color:#9ca3af;padding:4px 10px;">Red</td>
            </tr>
            {biz_rows}
        </table>
    </div>"""


# ── Agent log renderer ────────────────────────────────────────────────────────
AGENT_COLORS = {
    "SENTINEL":  "#059669",
    "ANALYST":   "#7c3aed",
    "ADVISOR":   "#2563eb",
    "MESSENGER": "#d97706",
}

def render_log(entries):
    lines = []
    for e in entries:
        color = AGENT_COLORS.get(e["agent"], "#6b7280")
        msg = e["msg"].replace(
            "⚠ FLAGGED", '<span style="color:#b91c1c;font-weight:600;">FLAGGED</span>'
        )
        lines.append(
            f'<div style="padding:4px 0;border-bottom:1px solid #f3f4f6;font-size:12px;line-height:1.6;">'
            f'<span style="color:#9ca3af;font-family:monospace;font-size:11px;">{e["ts"]}</span>'
            f'<span style="color:{color};font-weight:600;margin:0 8px;font-size:10px;text-transform:uppercase;letter-spacing:1px;">{e["agent"]}</span>'
            f'<span style="color:#374151;">{msg}</span></div>'
        )
    inner = (
        "".join(lines)
        or '<span style="color:#9ca3af;font-size:12px;">Pipeline idle. Select a ZIP code and run.</span>'
    )
    return (
        '<div style="background:#f9fafb;padding:14px 18px;border-radius:2px;'
        'max-height:440px;overflow-y:auto;border:1px solid #e5e7eb;">'
        + inner
        + "</div>"
    )


# ── Pipeline ──────────────────────────────────────────────────────────────────
def run_pipeline(zip_sel):
    z = get_zip(zip_sel)
    if not z:
        yield render_log([]), "ZIP not found", "", "", ""
        return

    log = []

    def L(agent, msg):
        log.append({"ts": datetime.now().strftime("%H:%M:%S"), "agent": agent, "msg": msg})
        return render_log(log)

    lh = L("SENTINEL", f"Scanning {summary['total_businesses']:,} businesses across county...")
    yield lh, "Scanning...", "", "", ""

    lh = L("SENTINEL", f"⚠ FLAGGED {z['zip']} — score {z['risk_score']:.0f}/100 | {z['total_red']} Red | {z['total_critical']} critical | poverty {z['poverty_rate']}%")
    top_biz = z["worst_businesses"][0] if z["worst_businesses"] else None
    if top_biz:
        lh = L("SENTINEL", f"  Top violator: {top_biz['name']} — {top_biz['critical_violations']} critical, {top_biz['red_inspections']} Red")
    lh = L("SENTINEL", "Handing off to ANALYST")

    sentinel_summary = (
        f"Scan complete.\n\n"
        f"ZIP flagged: {z['zip']}\n"
        f"Risk score: {z['risk_score']:.0f}/100 (threshold: 70)\n\n"
        f"Signals:\n"
        f"  {z['total_red']} failed inspections\n"
        f"  {z['total_critical']} critical violations\n"
        f"  {z['repeat_offenders']} repeat offenders\n"
        f"  {z['crime_on_food_streets']:,} crimes on food streets\n"
        f"  {z['poverty_rate']}% poverty rate\n\n"
        f"Passed to ANALYST"
    )
    yield lh, sentinel_summary, "ANALYST reasoning...", "Waiting...", ""

    # ── ANALYST ──────────────────────────────────────────────────────────────
    lh = L("ANALYST", f"Cross-correlating food safety + crime + poverty for ZIP {z['zip']}...")
    worst_txt = "\n".join(
        f"  - {b['name']} ({b['city']}): {b['critical_violations']} critical, {b['red_inspections']} Red — {b['top_violations'][:70]}"
        for b in z["worst_businesses"][:3]
    )
    analyst_prompt = f"""FLAGGED ZIP: {z['zip']} — Risk Score {z['risk_score']:.0f}/100

SIGNALS:
- Businesses: {z['businesses']} | Red inspections: {z['total_red']} | Critical violations: {z['total_critical']} | Repeat offenders: {z['repeat_offenders']}
- Crime on food streets: {z['crime_on_food_streets']:,} | Poverty: {z['poverty_rate']}% (county median 6.5%) | Income: ${z['median_income']:,} (county median $153K)
- County CDC avg — food insecurity: {cdc_avg['food_insecurity_pct']:.1f}% | diabetes: {cdc_avg['diabetes_pct']:.1f}% | obesity: {cdc_avg['obesity_pct']:.1f}%

TOP VIOLATING BUSINESSES:
{worst_txt}

Note: temperature control = 37% of all critical violations countywide (3,442 of 9,255 total).

Provide your structured assessment."""

    analyst_text = ""
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": ANALYST_SYS},
            {"role": "user", "content": analyst_prompt},
        ],
        stream=True, max_tokens=600, temperature=0.2,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        analyst_text += delta
        yield lh, sentinel_summary, analyst_text, "Waiting for Analyst...", ""

    lh = L("ANALYST", f"Assessment complete — handing off to ADVISOR")
    yield lh, sentinel_summary, analyst_text, "ADVISOR drafting brief...", ""

    # ── ADVISOR ──────────────────────────────────────────────────────────────
    lh = L("ADVISOR", f"Drafting Health Officer brief for ZIP {z['zip']}...")
    advisor_prompt = f"""ZIP {z['zip']} — {z['businesses']} businesses, {z['total_red']} Red inspections, {z['total_critical']} critical violations, {z['repeat_offenders']} repeat offenders. Poverty {z['poverty_rate']}%.

ANALYST ASSESSMENT:
{analyst_text}

Write the Health Officer brief."""

    advisor_text = ""
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": ADVISOR_SYS},
            {"role": "user", "content": advisor_prompt},
        ],
        stream=True, max_tokens=500, temperature=0.2,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        advisor_text += delta
        yield lh, sentinel_summary, analyst_text, advisor_text, "Waiting for Advisor..."

    lh = L("ADVISOR", "Health Officer brief complete — handing off to MESSENGER")
    yield lh, sentinel_summary, analyst_text, advisor_text, "MESSENGER drafting coaching..."

    # ── MESSENGER ────────────────────────────────────────────────────────────
    if top_biz:
        lh = L("MESSENGER", f"Coaching for: {top_biz['name']} ({top_biz['city']})")
        messenger_prompt = f"""Restaurant: {top_biz['name']} ({top_biz['city']}, ZIP {z['zip']})
Failed inspections: {top_biz['red_inspections']} Red, {top_biz['critical_violations']} critical violations
Specific violations: {top_biz['top_violations']}

Write the pre-inspection coaching letter."""

        messenger_text = ""
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": MESSENGER_SYS},
                {"role": "user", "content": messenger_prompt},
            ],
            stream=True, max_tokens=350, temperature=0.3,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            messenger_text += delta
            yield lh, sentinel_summary, analyst_text, advisor_text, messenger_text

        lh = L("MESSENGER", f"Coaching generated for {top_biz['name']}")
        lh = L("MESSENGER", "Routing: Health Officer brief → IMMEDIATE | Coaching → SCHEDULED | Pipeline complete")
    else:
        messenger_text = "No businesses to coach."

    yield lh, sentinel_summary, analyst_text, advisor_text, messenger_text


# ── UI ────────────────────────────────────────────────────────────────────────

HEADER_HTML = f"""
<div style="padding:32px 0 24px;border-bottom:2px solid #111827;">
  <div style="display:flex;justify-content:space-between;align-items:flex-end;">
    <div>
      <div style="font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:3px;">Community Health Intelligence</div>
      <div style="font-size:36px;font-weight:300;color:#111827;margin-top:6px;letter-spacing:-0.5px;">CivicPulse</div>
      <div style="font-size:13px;color:#6b7280;margin-top:4px;">Santa Clara County · Human Impact Track</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:10px;color:#9ca3af;letter-spacing:1px;">NVIDIA DGX Spark (GB10) · Nemotron 70B</div>
      <div style="font-size:10px;color:#9ca3af;margin-top:2px;">OpenClaw · 4 Agents · On-device inference</div>
    </div>
  </div>
</div>
"""

STATS_HTML = f"""
<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:32px;padding:28px 0;border-bottom:1px solid #e5e7eb;">
  <div>
    <div style="font-size:32px;font-weight:300;color:#b91c1c;">{summary['total_critical']:,}</div>
    <div style="font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Critical Violations</div>
  </div>
  <div>
    <div style="font-size:32px;font-weight:300;color:#d97706;">{summary['total_red']:,}</div>
    <div style="font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Failed Inspections</div>
  </div>
  <div>
    <div style="font-size:32px;font-weight:300;color:#b91c1c;">{summary['total_repeat_offenders']:,}</div>
    <div style="font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Repeat Offenders</div>
  </div>
  <div>
    <div style="font-size:32px;font-weight:300;color:#374151;">{summary['total_businesses']:,}</div>
    <div style="font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Businesses Monitored</div>
  </div>
  <div>
    <div style="font-size:32px;font-weight:300;color:#059669;">4</div>
    <div style="font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Active Agents</div>
  </div>
</div>
"""

AGENT_HEADERS_HTML = """
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0;border-bottom:1px solid #e5e7eb;">
  <div style="padding:10px 12px;border-right:1px solid #e5e7eb;">
    <div style="font-size:10px;font-weight:600;color:#059669;text-transform:uppercase;letter-spacing:2px;">Sentinel</div>
    <div style="font-size:10px;color:#9ca3af;margin-top:2px;">Risk triage · Rule-based</div>
  </div>
  <div style="padding:10px 12px;border-right:1px solid #e5e7eb;">
    <div style="font-size:10px;font-weight:600;color:#7c3aed;text-transform:uppercase;letter-spacing:2px;">Analyst</div>
    <div style="font-size:10px;color:#9ca3af;margin-top:2px;">Cross-silo reasoning · Nemotron 70B</div>
  </div>
  <div style="padding:10px 12px;border-right:1px solid #e5e7eb;">
    <div style="font-size:10px;font-weight:600;color:#2563eb;text-transform:uppercase;letter-spacing:2px;">Advisor</div>
    <div style="font-size:10px;color:#9ca3af;margin-top:2px;">Health Officer brief · Nemotron 70B</div>
  </div>
  <div style="padding:10px 12px;">
    <div style="font-size:10px;font-weight:600;color:#d97706;text-transform:uppercase;letter-spacing:2px;">Messenger</div>
    <div style="font-size:10px;color:#9ca3af;margin-top:2px;">Restaurant coaching · Nemotron 70B</div>
  </div>
</div>
"""

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

body { background: #ffffff !important; }
.gradio-container { background: #ffffff !important; max-width: 1440px !important; padding: 0 40px !important; }
footer { display: none !important; }
*, h1, h2, h3, h4, h5, p, span, div, td, th, label, input, textarea, select, button {
    font-family: 'Inter', -apple-system, sans-serif !important;
}

/* Strip Gradio chrome */
.block, .form, .wrap, .panel, .gradio-group, .gradio-column { background: transparent !important; border: none !important; box-shadow: none !important; }

/* Agent output boxes */
.agent-box textarea {
    font-family: 'Inter', -apple-system, sans-serif !important;
    font-size: 12.5px !important;
    line-height: 1.8 !important;
    background: #f9fafb !important;
    color: #1f2937 !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 2px !important;
    padding: 16px 18px !important;
}
.agent-box { background: transparent !important; border: none !important; }

/* Labels */
label { font-size: 10px !important; color: #9ca3af !important; text-transform: uppercase !important; letter-spacing: 1.5px !important; font-weight: 500 !important; }

/* Dropdown */
select, input, .choices__inner { background: #ffffff !important; border: 1px solid #d1d5db !important; border-radius: 2px !important; color: #111827 !important; font-size: 13px !important; }

/* Run button */
button.primary, button[variant="primary"] {
    background: #111827 !important;
    border: none !important;
    color: #ffffff !important;
    font-weight: 500 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    font-size: 11px !important;
    border-radius: 2px !important;
    padding: 14px 32px !important;
}
button.primary:hover { background: #1f2937 !important; }
"""

with gr.Blocks(title="CivicPulse") as app:

    gr.HTML(HEADER_HTML)
    gr.HTML(STATS_HTML)

    # Controls
    with gr.Row():
        zip_dd = gr.Dropdown(
            choices=zip_choices,
            value=zip_choices[0],
            label="Neighborhood",
            scale=4,
        )
        run_btn = gr.Button("Run Pipeline", variant="primary", scale=1, size="lg")

    # ZIP stats + agent log
    with gr.Row():
        with gr.Column(scale=1):
            zip_stats = gr.HTML(value=zip_stats_html(zip_choices[0]))
        with gr.Column(scale=2):
            gr.HTML('<div style="font-size:10px;color:#9ca3af;text-transform:uppercase;letter-spacing:2px;margin-bottom:8px;margin-top:12px;">Agent Communication Log</div>')
            agent_log_html = gr.HTML(render_log([]))

    gr.HTML('<div style="height:1px;background:#e5e7eb;margin:20px 0 12px;"></div>')
    gr.HTML(AGENT_HEADERS_HTML)

    # 4 agent output boxes
    with gr.Row():
        sentinel_box = gr.Textbox(
            label="", lines=16, interactive=False, elem_classes="agent-box",
            value="SENTINEL will flag ZIP codes above risk threshold 70.",
            show_label=False,
        )
        analyst_box = gr.Textbox(
            label="", lines=16, interactive=False, elem_classes="agent-box",
            value="Waiting for SENTINEL...",
            show_label=False,
        )
        advisor_box = gr.Textbox(
            label="", lines=16, interactive=False, elem_classes="agent-box",
            value="Waiting for ANALYST...",
            show_label=False,
        )
        messenger_box = gr.Textbox(
            label="", lines=16, interactive=False, elem_classes="agent-box",
            value="Waiting for ADVISOR...",
            show_label=False,
        )

    gr.HTML("""
    <div style="text-align:center;padding:28px 0;margin-top:24px;border-top:1px solid #e5e7eb;">
      <div style="font-size:9px;color:#9ca3af;text-transform:uppercase;letter-spacing:2px;">
        CivicPulse · Nemotron 70B · OpenClaw · NVIDIA DGX Spark (GB10) · All inference on-device
      </div>
    </div>
    """)

    # Wire
    zip_dd.change(fn=zip_stats_html, inputs=zip_dd, outputs=zip_stats)

    run_btn.click(
        fn=run_pipeline,
        inputs=[zip_dd],
        outputs=[agent_log_html, sentinel_box, analyst_box, advisor_box, messenger_box],
    )


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860, share=False, css=CSS)
