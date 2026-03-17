"""CivicPulse — User Portals
5 interfaces, one per user persona.
Runs on port 7861 alongside the agent app (7860).
NVIDIA DGX Spark (GB10) · Nemotron 70B · All inference local
"""
import gradio as gr
import json
import pandas as pd
from openai import OpenAI
from pathlib import Path
from datetime import datetime, date

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
MODEL = "nemotron:70b"
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

# ── Load data ─────────────────────────────────────────────────────────────────
with open(DATA_DIR / "top_risk_zips.json") as f:
    top_zips = json.load(f)
with open(DATA_DIR / "county_summary.json") as f:
    summary = json.load(f)

biz_df = pd.read_csv(DATA_DIR / "business_profiles.csv")
biz_df["zip"] = biz_df["postal_code"].astype(str).str[:5]
biz_df["critical_violations"] = biz_df["critical_violations"].fillna(0).astype(int)
biz_df["red_inspections"] = biz_df["red_inspections"].fillna(0).astype(int)
biz_df["top_violations"] = biz_df["top_violations"].fillna("")

# Repeat offenders (for inspector + outreach views)
repeat_offenders = biz_df[biz_df["red_inspections"] >= 2].nlargest(50, "critical_violations").copy()

# District zip mapping
ZIP_TO_DISTRICT = {
    "95020": 1, "95037": 1, "95046": 1, "95138": 1, "95139": 1,
    "95119": 1, "95123": 1, "95136": 1, "95111": 1,
    "95014": 2, "95070": 2, "95030": 2, "95032": 2, "95008": 2,
    "95129": 2, "95117": 2, "95128": 2, "95124": 2, "95125": 2,
    "95118": 2, "95120": 2,
    "95116": 3, "95122": 3, "95127": 3, "95148": 3, "95121": 3,
    "95035": 3, "95132": 3, "95133": 3, "95134": 3,
    "95112": 4, "95113": 4, "95110": 4, "95126": 4, "95131": 4,
    "95135": 4, "95140": 4,
    "94022": 5, "94024": 5, "94040": 5, "94041": 5, "94043": 5,
    "94085": 5, "94086": 5, "94087": 5, "94089": 5,
    "94301": 5, "94303": 5, "94304": 5, "94306": 5,
    "95050": 5, "95051": 5, "95054": 5,
}
DISTRICT_NAMES = {
    1: "District 1 — South County",
    2: "District 2 — West Valley",
    3: "District 3 — East San Jose / Milpitas",
    4: "District 4 — Central San Jose",
    5: "District 5 — North County",
}
biz_df["district"] = biz_df["zip"].map(ZIP_TO_DISTRICT)

# ── Shared LLM call (streaming) ───────────────────────────────────────────────
def stream_llm(system, prompt, max_tokens=500, temperature=0.2):
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        stream=True, max_tokens=max_tokens, temperature=temperature,
    )
    text = ""
    for chunk in stream:
        text += chunk.choices[0].delta.content or ""
        yield text

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — COUNTY HEALTH OFFICER  (weekly brief)
# ══════════════════════════════════════════════════════════════════════════════
def health_officer_table():
    rows = []
    for z in top_zips[:8]:
        score = z["risk_score"]
        color = "#ef4444" if score >= 80 else "#eab308" if score >= 70 else "#22c55e"
        rows.append({
            "ZIP": z["zip"],
            "Risk Score": f"{score:.0f}",
            "Red Inspections": z["total_red"],
            "Critical Violations": z["total_critical"],
            "Repeat Offenders": z["repeat_offenders"],
            "Poverty %": f"{z['poverty_rate']:.1f}%",
            "Status": "🔴 FLAGGED" if score >= 70 else "🟡 MONITOR",
        })
    return pd.DataFrame(rows)

def gen_health_brief(zip_sel):
    z = next((x for x in top_zips if x["zip"] == zip_sel), None)
    if not z:
        yield "ZIP not found."
        return
    sys = """You are an AI system writing the County Health Officer's weekly brief.
Write for a senior official. Lead with the most urgent fact. Be direct, specific, under 200 words.
Format: SITUATION (2 sentences) / RECOMMENDED ACTION (1 sentence, bold) / CROSS-AGENCY NOTE (1 sentence)."""
    prompt = f"""ZIP {z['zip']} — Risk Score {z['risk_score']:.0f}/100
{z['businesses']} food businesses · {z['total_red']} Red inspections · {z['total_critical']} critical violations
{z['repeat_offenders']} repeat offenders · {z['crime_on_food_streets']:,} crimes on food streets · {z['poverty_rate']}% poverty

Top violating businesses:
{chr(10).join(f"  - {b['name']}: {b['critical_violations']} critical, {b['red_inspections']} Red" for b in z['worst_businesses'][:3])}

Write the weekly brief for the County Health Officer."""
    yield from stream_llm(sys, prompt, max_tokens=300)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — INSPECTION SUPERVISOR  (daily priority queue)
# ══════════════════════════════════════════════════════════════════════════════
def inspector_queue_table():
    top = repeat_offenders[["name", "CITY", "zip", "critical_violations", "red_inspections", "top_violations"]].head(20).copy()
    top.columns = ["Business", "City", "ZIP", "Critical", "Red", "Top Violations"]
    top["Top Violations"] = top["Top Violations"].str[:60]
    top.insert(0, "Priority", [f"#{i+1}" for i in range(len(top))])
    return top

def gen_previsit_brief(biz_name):
    row = biz_df[biz_df["name"].str.contains(biz_name, case=False, na=False)].head(1)
    if row.empty:
        yield "Business not found. Try a partial name."
        return
    r = row.iloc[0]
    sys = """You are generating a pre-visit inspection brief for a DEH food safety inspector.
Be concise and tactical — the inspector reads this on the way to the visit.
Format: WHAT TO FOCUS ON (top 3 specific checkpoints based on history) / PRIOR FAILURES (key pattern) / WHAT TO DOCUMENT (if Red is likely)
Max 150 words."""
    prompt = f"""Business: {r['name']} ({r['CITY']}, ZIP {r['zip']})
Red inspections: {r['red_inspections']} | Critical violations: {r['critical_violations']}
Known violation patterns: {r['top_violations']}

Write the pre-visit brief for the inspector."""
    yield from stream_llm(sys, prompt, max_tokens=250)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — RESTAURANT OWNER  (pre-inspection coaching)
# ══════════════════════════════════════════════════════════════════════════════
def restaurant_search(query):
    if not query or len(query) < 2:
        return pd.DataFrame()
    matches = biz_df[
        (biz_df["name"].str.contains(query, case=False, na=False)) &
        (biz_df["red_inspections"] >= 1)
    ][["name", "CITY", "zip", "critical_violations", "red_inspections", "top_violations"]].head(10)
    matches.columns = ["Name", "City", "ZIP", "Critical Violations", "Red Inspections", "Violation Patterns"]
    return matches

def gen_coaching_letter(biz_name):
    row = biz_df[biz_df["name"].str.contains(biz_name, case=False, na=False)].head(1)
    if row.empty:
        yield "Business not found."
        return
    r = row.iloc[0]
    sys = """You are MESSENGER in CivicPulse writing a pre-inspection coaching letter to a restaurant manager.
Be helpful and direct — they want to pass, they just need specific guidance.
Start "Dear Manager,". Give exactly 3 numbered fixes with precise requirements (temperatures in °F, procedures, frequencies).
End with one encouraging sentence. Max 200 words."""
    prompt = f"""Restaurant: {r['name']} ({r['CITY']}, ZIP {r['zip']})
Failed inspections: {r['red_inspections']} Red, {r['critical_violations']} critical violations
Their specific violation patterns: {r['top_violations']}

Write the coaching letter."""
    yield from stream_llm(sys, prompt, max_tokens=350, temperature=0.3)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — COMMUNITY RESIDENT  (neighborhood safety chat)
# ══════════════════════════════════════════════════════════════════════════════
def resident_chat(message, history):
    # Look up any restaurant or ZIP mentioned
    context = ""
    for row in biz_df[biz_df["name"].str.contains(message[:30], case=False, na=False)].head(3).itertuples():
        status = "🔴 High Risk" if row.red_inspections >= 3 else "🟡 Caution" if row.red_inspections >= 1 else "🟢 Clean"
        context += f"\n- {row.name} ({row.CITY}): {status} — {row.critical_violations} critical violations, {row.red_inspections} Red inspections. Issues: {row.top_violations[:80]}"

    for z in top_zips:
        if z["zip"] in message:
            context += f"\nZIP {z['zip']}: Risk score {z['risk_score']:.0f}/100, {z['total_red']} failed inspections, {z['total_critical']} critical violations, {z['poverty_rate']}% poverty."

    sys = """You are a helpful community assistant for CivicPulse — a public food safety tool for Santa Clara County.
Answer questions about restaurant safety, neighborhoods, and food inspection records.
Be honest but not alarmist. Use plain language. If a restaurant is risky, say so clearly but suggest safe alternatives nearby.
Keep answers under 100 words."""
    prompt = f"""Resident question: {message}

Relevant data from SCC food inspection records:{context if context else ' No specific restaurant matched — answer based on general county food safety info.'}

County context: {summary['total_businesses']:,} restaurants monitored, {summary['total_red']} failed inspections in 2 years, {summary['total_repeat_offenders']} repeat offenders."""

    response = ""
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": sys},
            *[{"role": "user" if i % 2 == 0 else "assistant", "content": m}
              for i, m in enumerate([m for pair in history for m in pair if m])],
            {"role": "user", "content": prompt},
        ],
        stream=True, max_tokens=200, temperature=0.4,
    )
    for chunk in stream:
        response += chunk.choices[0].delta.content or ""
        yield response

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — COUNTY SUPERVISOR  (district scorecard)
# ══════════════════════════════════════════════════════════════════════════════
def district_scorecard(district_num):
    d = int(district_num)
    d_biz = biz_df[biz_df["district"] == d]
    if d_biz.empty:
        return "No data for this district.", pd.DataFrame()

    total_biz = len(biz_df[biz_df["district"].notna()])
    total_red = biz_df["red_inspections"].sum()
    total_crit = biz_df["critical_violations"].sum()

    d_red = d_biz["red_inspections"].sum()
    d_crit = d_biz["critical_violations"].sum()
    d_repeat = (d_biz["red_inspections"] >= 2).sum()

    pct_biz = len(d_biz) / max(1, total_biz) * 100
    pct_red = d_red / max(1, total_red) * 100
    flag = "⚠️ Disproportionate" if pct_red > pct_biz * 1.3 else "✓ Proportionate"

    top_offenders = d_biz.nlargest(5, "critical_violations")[
        ["name", "CITY", "zip", "critical_violations", "red_inspections"]
    ].copy()
    top_offenders.columns = ["Business", "City", "ZIP", "Critical Violations", "Red Inspections"]

    scorecard = f"""## {DISTRICT_NAMES[d]} — Scorecard
*Generated {date.today().strftime('%B %d, %Y')} · CivicPulse*

| Metric | District {d} | County Total | District Share | Status |
|--------|-------------|--------------|----------------|--------|
| Food Businesses | {len(d_biz):,} | {total_biz:,} | {pct_biz:.1f}% | — |
| Red Inspections | **{d_red:,}** | {int(total_red):,} | **{pct_red:.1f}%** | {flag} |
| Critical Violations | {d_crit:,} | {int(total_crit):,} | {d_crit/max(1,total_crit)*100:.1f}% | — |
| Repeat Offenders | **{d_repeat}** | {(biz_df['red_inspections']>=2).sum()} | {d_repeat/max(1,(biz_df['red_inspections']>=2).sum())*100:.1f}% | — |

**Board talking point:** *"District {d} has {pct_red:.0f}% of county's failed inspections with {pct_biz:.0f}% of county's restaurants."*"""

    return scorecard, top_offenders

def gen_supervisor_brief(district_num):
    d = int(district_num)
    d_biz = biz_df[biz_df["district"] == d]
    d_red = int(d_biz["red_inspections"].sum())
    d_crit = int(d_biz["critical_violations"].sum())
    d_repeat = int((d_biz["red_inspections"] >= 2).sum())
    top_3 = d_biz.nlargest(3, "critical_violations")[["name", "CITY", "critical_violations", "red_inspections"]]

    sys = """You are ADVISOR in CivicPulse writing a monthly district scorecard brief for a County Supervisor.
They present this at the Board of Supervisors meeting.
Format: HEADLINE FINDING (1 bold sentence) / 3 RECOMMENDED ACTIONS (numbered, each with responsible department) / BOARD TALKING POINT (1 quotable sentence in quotes)
Max 180 words. No jargon."""
    prompt = f"""{DISTRICT_NAMES[d]}
Food businesses: {len(d_biz):,} | Red inspections: {d_red} | Critical violations: {d_crit:,} | Repeat offenders: {d_repeat}

Top violating businesses:
{chr(10).join(f'  - {r.name} ({r.CITY}): {r.critical_violations} critical, {r.red_inspections} Red' for _, r in top_3.iterrows())}

County comparison: district has {d_red/max(1,int(biz_df['red_inspections'].sum()))*100:.0f}% of county's Red inspections with {len(d_biz)/max(1,len(biz_df[biz_df['district'].notna()]))*100:.0f}% of county's businesses.

Write the district brief for the Board of Supervisors."""
    yield from stream_llm(sys, prompt, max_tokens=280)

# ══════════════════════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════════════════════
HEADER = """
<div style="background:linear-gradient(135deg,#050810,#0f172a);padding:20px 32px;border-radius:10px;
            margin-bottom:12px;border:1px solid #1e293b;display:flex;justify-content:space-between;align-items:center;">
  <div>
    <span style="font-size:24px;font-weight:700;color:#f1f5f9;">CivicPulse</span>
    <span style="font-size:14px;color:#64748b;margin-left:12px;">User Portals</span>
  </div>
  <div style="font-size:11px;color:#334155;text-align:right;">
    NVIDIA DGX Spark (GB10) · Nemotron 70B<br>
    5 user interfaces · Santa Clara County
  </div>
</div>
"""

CSS = """
body { background: #030712 !important; }
.gradio-container { background: #030712 !important; max-width: 1400px !important; }
footer { display: none !important; }
.tab-label { font-size: 13px !important; font-weight: 600 !important; }
"""

with gr.Blocks(title="CivicPulse Portals") as portal:

    gr.HTML(HEADER)

    with gr.Tabs():

        # ── Tab 1: Health Officer ─────────────────────────────────────────────
        with gr.Tab("🔴  Health Officer", elem_classes="tab-label"):
            gr.Markdown("""### County Health Officer — Weekly Risk Brief
*Automated Monday 8:00 AM · Flagged ZIPs above compound risk threshold 70*""")

            with gr.Row():
                with gr.Column(scale=2):
                    gr.Markdown("**This week's flagged ZIP codes**")
                    flagged_tbl = gr.Dataframe(value=health_officer_table, interactive=False)
                with gr.Column(scale=1):
                    zip_sel = gr.Dropdown(
                        choices=[z["zip"] for z in top_zips],
                        value=top_zips[0]["zip"],
                        label="Generate brief for ZIP",
                    )
                    gen_brief_btn = gr.Button("Generate Health Officer Brief", variant="primary")
                    brief_out = gr.Markdown("*Select a ZIP and click Generate.*")

            gen_brief_btn.click(fn=gen_health_brief, inputs=zip_sel, outputs=brief_out)

        # ── Tab 2: Inspection Supervisor ──────────────────────────────────────
        with gr.Tab("🟡  Inspection Supervisor", elem_classes="tab-label"):
            gr.Markdown(f"""### Inspection Supervisor — Priority Queue
*Today: {date.today().strftime('%A, %B %d')} · {len(repeat_offenders)} repeat offenders in county · Sorted by compound risk*""")

            with gr.Row():
                with gr.Column(scale=2):
                    gr.Markdown("**Today's priority queue** — businesses with 2+ Red inspections, ranked by critical violations")
                    queue_tbl = gr.Dataframe(value=inspector_queue_table, interactive=False)
                with gr.Column(scale=1):
                    biz_search = gr.Textbox(label="Business name (partial match)", placeholder="e.g. Banh Mi")
                    gen_brief_btn2 = gr.Button("Generate Pre-Visit Brief", variant="primary")
                    previsit_out = gr.Markdown("*Enter a business name and click Generate.*")

            gen_brief_btn2.click(fn=gen_previsit_brief, inputs=biz_search, outputs=previsit_out)

        # ── Tab 3: Restaurant Owner ───────────────────────────────────────────
        with gr.Tab("🟢  Restaurant Owner", elem_classes="tab-label"):
            gr.Markdown("""### Restaurant Owner — Pre-Inspection Coaching
*Sent 7 days before scheduled inspection · Personalized to your violation history*""")

            with gr.Row():
                with gr.Column(scale=1):
                    owner_search = gr.Textbox(
                        label="Search your restaurant",
                        placeholder="e.g. Banh Mi Oven, Tomi Sushi...",
                    )
                    search_btn = gr.Button("Search", variant="secondary")
                    search_results = gr.Dataframe(label="Matching restaurants", interactive=False)
                    search_btn.click(fn=restaurant_search, inputs=owner_search, outputs=search_results)

                with gr.Column(scale=1):
                    coaching_name = gr.Textbox(
                        label="Restaurant name (for coaching letter)",
                        placeholder="Paste exact name from search results",
                    )
                    coaching_btn = gr.Button("Generate Coaching Letter", variant="primary")
                    coaching_out = gr.Markdown("*Enter the restaurant name above and click Generate.*")
                    coaching_btn.click(fn=gen_coaching_letter, inputs=coaching_name, outputs=coaching_out)

        # ── Tab 4: Community Resident ─────────────────────────────────────────
        with gr.Tab("🔵  Community Resident", elem_classes="tab-label"):
            gr.Markdown("""### Community Resident — Is It Safe to Eat Here?
*Ask about any restaurant or neighborhood in Santa Clara County · Powered by CivicPulse*""")

            chatbot = gr.Chatbot(
                value=[
                    {"role": "assistant", "content": f"Hi! I can tell you about food safety at any restaurant in Santa Clara County. We monitor **{summary['total_businesses']:,} businesses** and track inspection records going back 2 years. What would you like to know?"}
                ],
                height=420,
                label="",
                show_label=False,
            )
            with gr.Row():
                chat_input = gr.Textbox(
                    placeholder="Ask: 'Is Banh Mi Oven safe?' or 'What's the food safety like in 95116?'",
                    label="",
                    scale=4,
                    show_label=False,
                )
                chat_btn = gr.Button("Send", variant="primary", scale=1)

            def chat_respond(message, history):
                history = history or []
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": ""})
                response = ""
                # Convert messages format back to pairs for resident_chat context
                pairs = []
                msgs = [m for m in history[:-2] if m["role"] in ("user", "assistant")]
                for i in range(0, len(msgs) - 1, 2):
                    if msgs[i]["role"] == "user" and msgs[i+1]["role"] == "assistant":
                        pairs.append([msgs[i]["content"], msgs[i+1]["content"]])
                for chunk in resident_chat(message, pairs):
                    response = chunk
                    history[-1]["content"] = response
                    yield "", history

            chat_btn.click(fn=chat_respond, inputs=[chat_input, chatbot], outputs=[chat_input, chatbot])
            chat_input.submit(fn=chat_respond, inputs=[chat_input, chatbot], outputs=[chat_input, chatbot])

        # ── Tab 5: County Supervisor ──────────────────────────────────────────
        with gr.Tab("🟣  County Supervisor", elem_classes="tab-label"):
            gr.Markdown(f"""### County Supervisor — District Scorecard
*Monthly report · Board of Supervisors · {date.today().strftime('%B %Y')}*""")

            with gr.Row():
                district_dd = gr.Dropdown(
                    choices=[(v, str(k)) for k, v in DISTRICT_NAMES.items()],
                    value="3",
                    label="Select your district",
                    scale=2,
                )
                load_btn = gr.Button("Load Scorecard", variant="secondary", scale=1)
                brief_btn = gr.Button("Generate Board Brief", variant="primary", scale=1)

            with gr.Row():
                with gr.Column(scale=1):
                    scorecard_md = gr.Markdown("")
                    offenders_tbl = gr.Dataframe(label="Top violating businesses in district", interactive=False)
                with gr.Column(scale=1):
                    board_brief = gr.Markdown("*Click 'Generate Board Brief' for AI-drafted talking points.*")

            def load_scorecard(d):
                md, tbl = district_scorecard(d)
                return md, tbl

            load_btn.click(fn=load_scorecard, inputs=district_dd, outputs=[scorecard_md, offenders_tbl])
            brief_btn.click(fn=gen_supervisor_brief, inputs=district_dd, outputs=board_brief)

            # Load District 3 by default
            scorecard_md.value, offenders_tbl.value = district_scorecard("3")


if __name__ == "__main__":
    portal.launch(server_name="0.0.0.0", server_port=7861, share=False, css=CSS)
