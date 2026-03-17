#!/usr/bin/env python3
"""Transform pitch_deck.html: McKinsey light mode CSS + slide 8 + full arch slide + user guide appendix."""

import re

with open('/Users/johnny/hackathon/pitch_deck.html', 'r') as f:
    content = f.read()

# ── 1. Replace CSS block ──────────────────────────────────────────────────────
NEW_CSS = """<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Inter', -apple-system, sans-serif;
    background: #ffffff;
    color: #1e293b;
    overflow: hidden;
  }

  .slide {
    display: none;
    width: 100vw;
    height: 100vh;
    padding: 60px 80px;
    flex-direction: column;
    justify-content: center;
  }

  .slide.active { display: flex; }

  .hero-number { font-size: 140px; font-weight: 700; line-height: 1; color: #dc2626; }
  .hero-number.green { color: #16a34a; }
  .hero-number.blue { color: #2563eb; }
  .hero-number.amber { color: #d97706; }

  h1 { font-size: 56px; font-weight: 600; line-height: 1.15; margin-bottom: 20px; color: #0f172a; }
  h2 { font-size: 36px; font-weight: 500; line-height: 1.3; margin-bottom: 16px; color: #64748b; }
  h3 { font-size: 13px; font-weight: 600; color: #94a3b8; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 2px; }
  p { font-size: 22px; line-height: 1.6; color: #475569; max-width: 900px; }
  .small { font-size: 16px; color: #94a3b8; }
  .accent { color: #dc2626; font-weight: 600; }
  .accent-green { color: #16a34a; font-weight: 600; }
  .accent-blue { color: #2563eb; font-weight: 600; }

  .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 60px; align-items: start; }
  .three-col { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 40px; }
  .four-col { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 30px; }

  .card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 32px;
  }
  .card h4 { font-size: 18px; font-weight: 600; margin-bottom: 8px; color: #0f172a; }
  .card p { font-size: 16px; color: #475569; }
  .card .stat { font-size: 48px; font-weight: 700; margin-bottom: 4px; }
  .card .stat.red { color: #dc2626; }
  .card .stat.green { color: #16a34a; }
  .card .stat.blue { color: #2563eb; }
  .card .stat.amber { color: #d97706; }

  .data-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
  .data-table th { text-align: left; font-size: 14px; color: #94a3b8; padding: 12px 16px; border-bottom: 2px solid #e2e8f0; text-transform: uppercase; letter-spacing: 1px; }
  .data-table td { font-size: 18px; padding: 14px 16px; border-bottom: 1px solid #f1f5f9; color: #1e293b; }
  .data-table tr:hover { background: #f8fafc; }

  .badge { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: 600; }
  .badge.red { background: #fee2e2; color: #dc2626; }
  .badge.green { background: #dcfce7; color: #16a34a; }
  .badge.amber { background: #fef9c3; color: #d97706; }

  .pipeline { display: flex; align-items: center; gap: 12px; margin: 30px 0; }
  .pipeline-node {
    background: #f8fafc;
    border: 2px solid #3b82f6;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    flex: 1;
  }
  .pipeline-node.nano { border-color: #16a34a; }
  .pipeline-node.big { border-color: #7c3aed; }
  .pipeline-node h4 { font-size: 16px; margin-bottom: 4px; color: #0f172a; }
  .pipeline-node .model { font-size: 12px; color: #94a3b8; }
  .pipeline-arrow { font-size: 24px; color: #cbd5e1; }

  .spacer { height: 30px; }
  .spacer-lg { height: 50px; }
  .divider { height: 1px; background: #e2e8f0; margin: 30px 0; }

  .slide-footer {
    position: absolute;
    bottom: 30px;
    left: 80px;
    right: 80px;
    display: flex;
    justify-content: space-between;
    font-size: 14px;
    color: #cbd5e1;
  }

  .nav {
    position: fixed;
    bottom: 20px;
    right: 30px;
    display: flex;
    gap: 10px;
    z-index: 100;
  }
  .nav button {
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    color: #475569;
    padding: 10px 20px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
  }
  .nav button:hover { background: #e2e8f0; }

  .slide-counter {
    position: fixed;
    bottom: 25px;
    left: 30px;
    font-size: 14px;
    color: #cbd5e1;
    z-index: 100;
  }

  .highlight {
    background: #f8fafc;
    border-left: 4px solid #dc2626;
    padding: 24px 32px;
    border-radius: 0 12px 12px 0;
    margin: 20px 0;
  }
  .highlight.green { border-left-color: #16a34a; }
  .highlight.blue { border-left-color: #2563eb; }
  .highlight p { font-size: 20px; color: #1e293b; }

  .code-block {
    font-family: monospace;
    font-size: 14px;
    line-height: 1.7;
    background: #0f172a;
    color: #94a3b8;
    padding: 24px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
  }
</style>"""

# Replace old style block
old_style_start = content.index('<style>')
old_style_end = content.index('</style>') + len('</style>')
content = content[:old_style_start] + NEW_CSS + content[old_style_end:]

# ── 2. Inline color replacements (ordered: most specific first) ───────────────
replacements = [
    # Gradient backgrounds
    ("background:linear-gradient(135deg, #1e293b 0%, #0f172a 100%)", "background:#f8fafc"),
    ("background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%)", "background:#f8fafc"),
    # Dark specialty backgrounds
    ("background:#052e16", "background:#f0fdf4"),
    ("background:#0f2820", "background:#f0fdf4"),
    ("background:#0a1f0a", "background:#f0fdf4"),
    ("background:#14532d22", "background:#dcfce770"),
    ("background:#14532d", "background:#dcfce7"),
    ("background:#166534", "background:#dcfce7"),
    ("background:#1a0000", "background:#fff1f2"),
    ("background:#0a0f1a", "background:#eff6ff"),
    ("background:#0f0a1a", "background:#faf5ff"),
    ("background:#1a1200", "background:#fefce8"),
    ("background:#0a1a0a", "background:#f0fdf4"),
    ("background:#1e0a0a", "background:#fff1f2"),
    ("background:#0a0a0a", "background:#f9fafb"),
    ("background:#0f172a", "background:#f8fafc"),
    ("background:#111827", "background:#f1f5f9"),
    ("background:#1e293b", "background:#e9edf2"),
    # Borders (dark → light)
    ("border:1px solid #1e293b", "border:1px solid #e2e8f0"),
    ("border: 1px solid #1e293b", "border:1px solid #e2e8f0"),
    ("border-bottom:1px solid #1e293b", "border-bottom:1px solid #e2e8f0"),
    ("border-bottom: 1px solid #1e293b", "border-bottom:1px solid #e2e8f0"),
    ("border-left:3px solid #22c55e", "border-left:3px solid #16a34a"),
    ("border-left:2px solid #22c55e", "border-left:2px solid #16a34a"),
    ("border-left:3px solid #3b82f6", "border-left:3px solid #2563eb"),
    ("border:1px solid #166534", "border:1px solid #bbf7d0"),
    ("border:1px solid #22c55e", "border:1px solid #16a34a"),
    ("border-top:2px solid #ef4444", "border-top:3px solid #dc2626"),
    ("border-top:2px solid #eab308", "border-top:3px solid #d97706"),
    ("border-top:2px solid #3b82f6", "border-top:3px solid #2563eb"),
    # Light text → dark text
    ("color:#e2e8f0", "color:#1e293b"),
    ("color: #e2e8f0", "color:#1e293b"),
    ("color:#ffffff", "color:#0f172a"),
    ("color: #ffffff", "color:#0f172a"),
    ("color:#86efac", "color:#15803d"),
    ("color:#fca5a5", "color:#dc2626"),
    ("color:#fde047", "color:#ca8a04"),
    # Fix: dark text on light bg (the cross-silo sidebar was dark bg originally)
    # SVG path/stroke fixes
    ('stroke="#1e293b"', 'stroke="#e2e8f0"'),
    ('stroke="#334155"', 'stroke="#cbd5e1"'),
    ('fill="#0f172a"', 'fill="#f8fafc"'),
    # Terminal/log pre-block text (keep dark bg but fix outer container colors)
    # "score counter" line
    ('color:#334155;', 'color:#94a3b8;'),
]

for old, new in replacements:
    content = content.replace(old, new)

# Fix the close slide which had white text for emphasis
content = content.replace(
    'font-weight:600;color:#0f172a;',
    'font-weight:600;color:#0f172a;'
)
# The close slide "Now it has a voice" was color:#ffffff → now #0f172a (already replaced above, good)

# ── 3. Insert Slide 8 (User Interactions) between s_whatchanges and s10 ──────
SLIDE_8 = """

<!-- SLIDE 8: Who Gets What — User Interactions -->
<div class="slide" id="s8">
  <h3>Who Gets What</h3>
  <div style="font-size:13px;color:#94a3b8;margin-bottom:20px;">Five users. Five channels. Every output tailored by the Advisor agent.</div>

  <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;font-size:12px;">

    <!-- County Health Officer -->
    <div style="border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;">
      <div style="background:#fff1f2;padding:10px 12px;border-bottom:1px solid #e2e8f0;">
        <div style="color:#dc2626;font-weight:700;font-size:13px;">County Health Officer</div>
        <div style="margin-top:4px;display:inline-block;background:#fee2e2;color:#dc2626;font-size:10px;padding:2px 8px;border-radius:4px;">📧 Email · Monday 8:00 AM</div>
      </div>
      <div style="padding:10px 12px;background:#ffffff;">
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:10px;font-family:monospace;font-size:11px;line-height:1.6;">
          <div style="color:#94a3b8;margin-bottom:6px;padding-bottom:6px;border-bottom:1px solid #e2e8f0;">
            <span style="color:#94a3b8;">From:</span> <span style="color:#475569;">CivicPulse</span><br>
            <span style="color:#94a3b8;">To:</span> <span style="color:#475569;">Dr. Sarah Chen</span><br>
            <span style="color:#94a3b8;">Re:</span> <span style="color:#dc2626;">⚠ Weekly Risk Brief — 3 ZIPs flagged</span>
          </div>
          <div style="color:#475569;line-height:1.7;">
            <span style="color:#dc2626;font-weight:600;">ZIP 95122</span> crossed compounding risk threshold.<br><br>
            <span style="color:#94a3b8;">Risk Score:</span> 82.1/100 (rank #3)<br>
            <span style="color:#94a3b8;">Repeat offenders:</span> 22 businesses<br>
            <span style="color:#94a3b8;">Poverty rate:</span> 10.5% ($94K income)<br><br>
            <span style="color:#16a34a;">Recommendation:</span> Cross-dept surge — DEH + Sheriff + Public Health. Full brief attached.
          </div>
        </div>
        <div style="margin-top:8px;color:#94a3b8;font-size:11px;">She forwards to all three departments with one click. Advisor already drafted the intervention plan.</div>
      </div>
    </div>

    <!-- Inspection Supervisor -->
    <div style="border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;">
      <div style="background:#fefce8;padding:10px 12px;border-bottom:1px solid #e2e8f0;">
        <div style="color:#d97706;font-weight:700;font-size:13px;">Inspection Supervisor</div>
        <div style="margin-top:4px;display:inline-block;background:#fef9c3;color:#d97706;font-size:10px;padding:2px 8px;border-radius:4px;">🖥 Dashboard · 7:30 AM daily</div>
      </div>
      <div style="padding:10px 12px;background:#ffffff;">
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:10px;font-size:11px;line-height:1.6;">
          <div style="color:#94a3b8;font-size:10px;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Priority Queue — Tuesday</div>
          <div style="padding:8px;background:#fff1f2;border-left:3px solid #dc2626;border-radius:0 4px 4px 0;margin-bottom:6px;">
            <div style="color:#dc2626;font-weight:600;">1. Banh Mi Oven</div>
            <div style="color:#94a3b8;">95122 · 9 Red · 23 critical</div>
            <div style="color:#475569;margin-top:4px;font-size:10px;">Pre-visit: focus on temp control &amp; TPHC — 7 of 9 prior failures</div>
          </div>
          <div style="padding:8px;background:#f8fafc;border-left:3px solid #d97706;border-radius:0 4px 4px 0;margin-bottom:6px;">
            <div style="color:#d97706;font-weight:600;">2. Mariscos Playa Azul</div>
            <div style="color:#94a3b8;">95116 · 4 Red · 16 critical</div>
          </div>
          <div style="padding:8px;background:#f8fafc;border-left:3px solid #cbd5e1;border-radius:0 4px 4px 0;">
            <div style="color:#475569;font-weight:600;">3. Tomi Sushi</div>
            <div style="color:#94a3b8;">95122 · 5 Red · 11 critical</div>
          </div>
        </div>
        <div style="margin-top:8px;color:#94a3b8;font-size:11px;">One-click to assign inspector. Pre-visit brief auto-generated from violation history.</div>
      </div>
    </div>

    <!-- Restaurant Owner -->
    <div style="border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;">
      <div style="background:#f0fdf4;padding:10px 12px;border-bottom:1px solid #e2e8f0;">
        <div style="color:#16a34a;font-weight:700;font-size:13px;">Restaurant Owner</div>
        <div style="margin-top:4px;display:inline-block;background:#dcfce7;color:#16a34a;font-size:10px;padding:2px 8px;border-radius:4px;">💬 SMS · 7 days before inspection</div>
      </div>
      <div style="padding:10px 12px;background:#ffffff;">
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:10px;font-size:11px;">
          <div style="color:#94a3b8;font-size:10px;text-align:center;margin-bottom:8px;">Wed 10:02 AM · (408) 299-2100</div>
          <div style="background:#e2e8f0;border-radius:12px 12px 12px 4px;padding:8px 10px;margin-bottom:6px;max-width:90%;line-height:1.6;color:#1e293b;">
            Tomi Sushi inspection is next week. Most likely violations:<br>
            1. Hot holding temps — calibrate cooler<br>
            2. Time marking — label all TPHC items<br>
            3. Handwash sink — stock soap &amp; towels<br>
            Reply HELP for details.
          </div>
          <div style="background:#16a34a;border-radius:12px 12px 4px 12px;padding:8px 10px;margin-left:auto;max-width:60%;line-height:1.5;color:#ffffff;">
            thanks — what temp?
          </div>
          <div style="background:#e2e8f0;border-radius:12px 12px 12px 4px;padding:8px 10px;margin-top:6px;max-width:90%;color:#1e293b;line-height:1.6;">
            Cold holding must stay at 41°F or below. Yours was 46°F in July 2025. Check thermostat and door seals.
          </div>
        </div>
        <div style="margin-top:8px;color:#94a3b8;font-size:11px;">Two-way SMS. Owner asks follow-ups, agent answers from inspection history.</div>
      </div>
    </div>

    <!-- Resident -->
    <div style="border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;">
      <div style="background:#eff6ff;padding:10px 12px;border-bottom:1px solid #e2e8f0;">
        <div style="color:#2563eb;font-weight:700;font-size:13px;">Community Resident</div>
        <div style="margin-top:4px;display:inline-block;background:#dbeafe;color:#2563eb;font-size:10px;padding:2px 8px;border-radius:4px;">🌐 Public website · any time</div>
      </div>
      <div style="padding:10px 12px;background:#ffffff;">
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;font-size:11px;overflow:hidden;">
          <div style="background:#e2e8f0;padding:6px 10px;color:#64748b;font-size:10px;">civicpulse.scc.gov/check</div>
          <div style="padding:10px;">
            <div style="background:#dbeafe;border-radius:12px 12px 4px 12px;padding:7px 10px;margin-left:auto;max-width:80%;color:#1e40af;margin-bottom:6px;">
              is banh mi oven safe?
            </div>
            <div style="background:#f1f5f9;border-radius:4px 12px 12px 12px;padding:8px 10px;max-width:95%;color:#1e293b;line-height:1.6;margin-bottom:6px;">
              <span style="color:#dc2626;font-weight:600;">Banh Mi Oven</span> has failed 9 of 13 inspections, 23 critical violations.<br><br>
              <span style="color:#16a34a;">Nearby alternatives:</span><br>
              · Lee's Sandwiches (0.3mi) — Green<br>
              · Pho 69 (0.5mi) — Green
            </div>
            <div style="border:1px solid #e2e8f0;border-radius:6px;padding:6px 10px;color:#94a3b8;">Ask about any restaurant…</div>
          </div>
        </div>
        <div style="margin-top:8px;color:#94a3b8;font-size:11px;">No login required. Powered by Advisor with live inspection data.</div>
      </div>
    </div>

    <!-- County Supervisor -->
    <div style="border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;">
      <div style="background:#faf5ff;padding:10px 12px;border-bottom:1px solid #e2e8f0;">
        <div style="color:#7c3aed;font-weight:700;font-size:13px;">County Supervisor</div>
        <div style="margin-top:4px;display:inline-block;background:#ede9fe;color:#7c3aed;font-size:10px;padding:2px 8px;border-radius:4px;">📊 PDF Report · monthly</div>
      </div>
      <div style="padding:10px 12px;background:#ffffff;">
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:10px;font-size:11px;line-height:1.6;">
          <div style="color:#7c3aed;font-weight:700;font-size:12px;margin-bottom:4px;">District 3 Scorecard — March 2026</div>
          <div style="color:#94a3b8;font-size:10px;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #e2e8f0;">Prepared by CivicPulse · Confidential</div>
          <div style="color:#dc2626;margin-bottom:6px;font-weight:600;">⚠ 3 of county's top 10 risk ZIPs are in your district</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:8px;">
            <div style="color:#94a3b8;">Red inspections:</div><div style="color:#dc2626;font-weight:600;">234 (29% of county)</div>
            <div style="color:#94a3b8;">Repeat offenders:</div><div style="color:#dc2626;font-weight:600;">55 (34% of county)</div>
            <div style="color:#94a3b8;">Median income:</div><div style="color:#d97706;">$95K vs $153K county</div>
          </div>
          <div style="background:#f0fdf4;border-left:2px solid #16a34a;padding:6px 8px;color:#15803d;font-size:10px;border-radius:0 4px 4px 0;">
            Board talking point: "District 3 bears 34% of repeat failures with 19% of restaurants."
          </div>
        </div>
        <div style="margin-top:8px;color:#94a3b8;font-size:11px;">Monthly PDF + dashboard. Board-ready language auto-generated by Advisor.</div>
      </div>
    </div>

  </div>
</div>

"""

# Insert s8 before s10
content = content.replace(
    '\n<!-- SLIDE 10: Who Uses It — Timeline -->',
    SLIDE_8 + '\n<!-- SLIDE 10: Who Uses It — Timeline -->'
)

# ── 4. Full Architecture Slide (add to appendix, after san) ──────────────────
ARCH_SLIDE = """

<!-- APPENDIX R: Full System Architecture -->
<div class="slide" id="sar">
  <h3>Appendix R — Full System Architecture</h3>
  <div style="font-size:13px;color:#94a3b8;margin-bottom:16px;">All components running on a single NVIDIA DGX Spark (GB10)</div>

  <div style="display:grid;grid-template-columns:180px 160px 1fr 160px 200px;gap:0;align-items:center;font-size:12px;">

    <!-- Col 1: Data Sources -->
    <div style="padding-right:12px;">
      <div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;text-align:center;">Data Sources</div>
      <div style="display:grid;gap:6px;">
        <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:6px;padding:8px 10px;">
          <div style="color:#ea580c;font-weight:600;">Food Safety</div>
          <div style="color:#94a3b8;font-size:10px;">95K+ records · DEH</div>
        </div>
        <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:6px;padding:8px 10px;">
          <div style="color:#dc2626;font-weight:600;">Crime Reports</div>
          <div style="color:#94a3b8;font-size:10px;">260K incidents · SJPD</div>
        </div>
        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;padding:8px 10px;">
          <div style="color:#2563eb;font-weight:600;">Census / ACS</div>
          <div style="color:#94a3b8;font-size:10px;">62 ZIP codes</div>
        </div>
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:8px 10px;">
          <div style="color:#16a34a;font-weight:600;">CDC PLACES</div>
          <div style="color:#94a3b8;font-size:10px;">16K health tracts</div>
        </div>
      </div>
    </div>

    <!-- Col 2: Processing -->
    <div style="text-align:center;padding:0 12px;">
      <div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">Processing</div>
      <div style="font-size:22px;color:#cbd5e1;margin-bottom:8px;">→</div>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;">
        <div style="color:#475569;font-weight:600;font-size:11px;">build_risk.py</div>
        <div style="color:#94a3b8;font-size:10px;margin-top:4px;">Geographic join<br>Street normalization<br>KD-tree CDC join<br>Percentile scoring</div>
      </div>
      <div style="font-size:22px;color:#cbd5e1;margin-top:8px;">↓</div>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px;margin-top:6px;">
        <div style="color:#475569;font-weight:600;font-size:11px;">zip_risk.json</div>
        <div style="color:#94a3b8;font-size:10px;">92 ZIP profiles</div>
      </div>
    </div>

    <!-- Col 3: Agent Pipeline -->
    <div style="padding:0 12px;">
      <div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;text-align:center;">Agent Pipeline (OpenClaw · Nemotron 70B · Ollama :11434)</div>
      <div style="display:grid;grid-template-columns:1fr 20px 1fr 20px 1fr 20px 1fr;gap:0;align-items:center;">
        <div style="background:#f0fdf4;border:2px solid #16a34a;border-radius:8px;padding:10px;text-align:center;">
          <div style="color:#16a34a;font-weight:700;font-size:13px;">SENTINEL</div>
          <div style="color:#475569;font-size:10px;margin-top:4px;">Triage &amp; flag<br>Severity 1–5<br>&lt;5s per scan</div>
        </div>
        <div style="text-align:center;color:#cbd5e1;font-size:16px;">→</div>
        <div style="background:#faf5ff;border:2px solid #7c3aed;border-radius:8px;padding:10px;text-align:center;">
          <div style="color:#7c3aed;font-weight:700;font-size:13px;">ANALYST</div>
          <div style="color:#475569;font-size:10px;margin-top:4px;">Cross-silo<br>Root causes<br>128K context</div>
        </div>
        <div style="text-align:center;color:#cbd5e1;font-size:16px;">→</div>
        <div style="background:#eff6ff;border:2px solid #2563eb;border-radius:8px;padding:10px;text-align:center;">
          <div style="color:#2563eb;font-weight:700;font-size:13px;">ADVISOR</div>
          <div style="color:#475569;font-size:10px;margin-top:4px;">Tailored output<br>per recipient<br>5 formats</div>
        </div>
        <div style="text-align:center;color:#cbd5e1;font-size:16px;">→</div>
        <div style="background:#fefce8;border:2px solid #d97706;border-radius:8px;padding:10px;text-align:center;">
          <div style="color:#d97706;font-weight:700;font-size:13px;">MESSENGER</div>
          <div style="color:#475569;font-size:10px;margin-top:4px;">Route &amp; deliver<br>Track follow-up<br>4 channels</div>
        </div>
      </div>
      <div style="margin-top:10px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:8px 12px;font-size:10px;color:#64748b;text-align:center;">
        Context flows downstream: each agent sees prior agent's full output · Decision-driven, not just sequential
      </div>
    </div>

    <!-- Col 4: Channels -->
    <div style="text-align:center;padding:0 12px;">
      <div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">Channels</div>
      <div style="font-size:22px;color:#cbd5e1;margin-bottom:8px;">→</div>
      <div style="display:grid;gap:6px;font-size:11px;">
        <div style="background:#fff1f2;border:1px solid #fecaca;border-radius:6px;padding:6px 10px;color:#dc2626;">📧 Email brief</div>
        <div style="background:#fefce8;border:1px solid #fef08a;border-radius:6px;padding:6px 10px;color:#d97706;">🖥 Dashboard</div>
        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;padding:6px 10px;color:#16a34a;">💬 SMS / text</div>
        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;padding:6px 10px;color:#2563eb;">🌐 Web chat</div>
        <div style="background:#faf5ff;border:1px solid #e9d5ff;border-radius:6px;padding:6px 10px;color:#7c3aed;">📊 PDF report</div>
      </div>
    </div>

    <!-- Col 5: Recipients -->
    <div style="padding-left:12px;">
      <div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;text-align:center;">Recipients</div>
      <div style="display:grid;gap:6px;font-size:11px;">
        <div style="padding:8px 10px;border-left:3px solid #dc2626;background:#fff1f2;border-radius:0 6px 6px 0;">
          <div style="color:#dc2626;font-weight:600;">County Health Officer</div>
          <div style="color:#94a3b8;font-size:10px;">Cross-dept action</div>
        </div>
        <div style="padding:8px 10px;border-left:3px solid #d97706;background:#fefce8;border-radius:0 6px 6px 0;">
          <div style="color:#d97706;font-weight:600;">Inspection Supervisor</div>
          <div style="color:#94a3b8;font-size:10px;">Priority queue</div>
        </div>
        <div style="padding:8px 10px;border-left:3px solid #16a34a;background:#f0fdf4;border-radius:0 6px 6px 0;">
          <div style="color:#16a34a;font-weight:600;">Restaurant Owner</div>
          <div style="color:#94a3b8;font-size:10px;">Coaching checklist</div>
        </div>
        <div style="padding:8px 10px;border-left:3px solid #2563eb;background:#eff6ff;border-radius:0 6px 6px 0;">
          <div style="color:#2563eb;font-weight:600;">Community Resident</div>
          <div style="color:#94a3b8;font-size:10px;">Safety answers</div>
        </div>
        <div style="padding:8px 10px;border-left:3px solid #7c3aed;background:#faf5ff;border-radius:0 6px 6px 0;">
          <div style="color:#7c3aed;font-weight:600;">County Supervisor</div>
          <div style="color:#94a3b8;font-size:10px;">District scorecard</div>
        </div>
      </div>
    </div>

  </div>
</div>

"""

content = content.replace(
    '\n<!-- APPENDIX I: Why Agents -->',
    ARCH_SLIDE + '\n<!-- APPENDIX I: Why Agents -->'
)

# ── 5. User Guide Appendix Slides ─────────────────────────────────────────────
USER_GUIDES = """

<!-- APPENDIX S: User & Agent Guides -->
<div class="slide" id="sas_toc">
  <h3>Appendix S — User &amp; Agent Guides</h3>
  <div class="spacer"></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:40px;font-size:15px;">
    <div>
      <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:2px;margin-bottom:16px;">Agent Guides</div>
      <div style="display:grid;gap:10px;">
        <div style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;border-left:4px solid #16a34a;">
          <span style="color:#16a34a;font-weight:700;">S1 &nbsp;</span><span style="color:#1e293b;">SENTINEL — Triage Agent</span>
          <div style="color:#94a3b8;font-size:12px;margin-top:2px;">What it monitors, when it fires, what to do with a flag</div>
        </div>
        <div style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;border-left:4px solid #7c3aed;">
          <span style="color:#7c3aed;font-weight:700;">S2 &nbsp;</span><span style="color:#1e293b;">ANALYST — Deep Reasoning Agent</span>
          <div style="color:#94a3b8;font-size:12px;margin-top:2px;">Input format, output sections, how to interpret severity</div>
        </div>
        <div style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;border-left:4px solid #2563eb;">
          <span style="color:#2563eb;font-weight:700;">S3 &nbsp;</span><span style="color:#1e293b;">ADVISOR — Action Generator</span>
          <div style="color:#94a3b8;font-size:12px;margin-top:2px;">Recipient profiles, output types, customization</div>
        </div>
        <div style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;border-left:4px solid #d97706;">
          <span style="color:#d97706;font-weight:700;">S4 &nbsp;</span><span style="color:#1e293b;">MESSENGER — Routing Agent</span>
          <div style="color:#94a3b8;font-size:12px;margin-top:2px;">Channel rules, urgency levels, follow-up tracking</div>
        </div>
      </div>
    </div>
    <div>
      <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:2px;margin-bottom:16px;">User Guides</div>
      <div style="display:grid;gap:10px;">
        <div style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;border-left:4px solid #dc2626;">
          <span style="color:#dc2626;font-weight:700;">S5 &nbsp;</span><span style="color:#1e293b;">County Health Officer</span>
          <div style="color:#94a3b8;font-size:12px;margin-top:2px;">Weekly brief, forwarding workflow, escalation</div>
        </div>
        <div style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;border-left:4px solid #d97706;">
          <span style="color:#d97706;font-weight:700;">S6 &nbsp;</span><span style="color:#1e293b;">Inspection Supervisor</span>
          <div style="color:#94a3b8;font-size:12px;margin-top:2px;">Dashboard, priority queue, pre-visit briefs</div>
        </div>
        <div style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;border-left:4px solid #16a34a;">
          <span style="color:#16a34a;font-weight:700;">S7 &nbsp;</span><span style="color:#1e293b;">Restaurant Owner</span>
          <div style="color:#94a3b8;font-size:12px;margin-top:2px;">SMS opt-in, coaching messages, how to reply</div>
        </div>
        <div style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;border-left:4px solid #2563eb;">
          <span style="color:#2563eb;font-weight:700;">S8 &nbsp;</span><span style="color:#1e293b;">Community Resident</span>
          <div style="color:#94a3b8;font-size:12px;margin-top:2px;">Public web portal, what questions you can ask</div>
        </div>
        <div style="padding:12px 16px;border:1px solid #e2e8f0;border-radius:8px;border-left:4px solid #7c3aed;">
          <span style="color:#7c3aed;font-weight:700;">S9 &nbsp;</span><span style="color:#1e293b;">County Supervisor</span>
          <div style="color:#94a3b8;font-size:12px;margin-top:2px;">Monthly scorecard, board presentation format</div>
        </div>
      </div>
    </div>
  </div>
</div>


<!-- APPENDIX S1: SENTINEL Agent Guide -->
<div class="slide" id="sas1">
  <h3>Agent Guide S1 — SENTINEL</h3>
  <div class="spacer"></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:48px;">
    <div>
      <div style="border-left:4px solid #16a34a;padding-left:20px;margin-bottom:28px;">
        <div style="font-size:20px;font-weight:600;color:#0f172a;">Purpose</div>
        <p style="font-size:16px;margin-top:8px;">Fast triage across all 92 ZIP profiles. Filters noise from signal. Determines what's worth investigating.</p>
      </div>
      <div style="margin-bottom:20px;">
        <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">When it runs</div>
        <div style="display:grid;gap:8px;font-size:15px;">
          <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;">🌙 &nbsp;<strong>Nightly batch</strong> — full scan, 3:00 AM daily</div>
          <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;">⚡ &nbsp;<strong>Real-time trigger</strong> — on new inspection result upload</div>
          <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;">👤 &nbsp;<strong>On-demand</strong> — supervisor requests spot-check of specific ZIP</div>
        </div>
      </div>
      <div>
        <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">Threshold logic</div>
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
          <tr style="border-bottom:1px solid #e2e8f0;"><th style="text-align:left;padding:8px;color:#94a3b8;">Score</th><th style="text-align:left;padding:8px;color:#94a3b8;">Flag</th><th style="text-align:left;padding:8px;color:#94a3b8;">Action</th></tr>
          <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:8px;color:#dc2626;font-weight:600;">≥ 70</td><td style="padding:8px;"><span style="background:#fee2e2;color:#dc2626;padding:2px 8px;border-radius:4px;font-size:12px;">FLAGGED</span></td><td style="padding:8px;color:#475569;">Passes to Analyst immediately</td></tr>
          <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:8px;color:#d97706;font-weight:600;">50–69</td><td style="padding:8px;"><span style="background:#fef9c3;color:#d97706;padding:2px 8px;border-radius:4px;font-size:12px;">MONITOR</span></td><td style="padding:8px;color:#475569;">Weekly report, no immediate alert</td></tr>
          <tr><td style="padding:8px;color:#16a34a;font-weight:600;">&lt; 50</td><td style="padding:8px;"><span style="background:#dcfce7;color:#16a34a;padding:2px 8px;border-radius:4px;font-size:12px;">OK</span></td><td style="padding:8px;color:#475569;">No action, included in monthly summary</td></tr>
        </table>
      </div>
    </div>
    <div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">Output format</div>
      <div style="background:#0f172a;border-radius:10px;padding:20px;font-family:monospace;font-size:13px;line-height:1.8;color:#94a3b8;">
        <span style="color:#16a34a;">SEVERITY:</span> 4<br>
        <span style="color:#16a34a;">FLAG:</span> <span style="color:#dc2626;">YES</span><br>
        <span style="color:#16a34a;">REASON:</span> ZIP 95122 has 4 repeat offenders<br>
        &nbsp;&nbsp;combined with 10.5% poverty rate and<br>
        &nbsp;&nbsp;4,187 crime incidents — compounding<br>
        &nbsp;&nbsp;risk pattern across all 4 dimensions.<br>
        <span style="color:#16a34a;">TOP_CONCERN:</span> Banh Mi Oven has failed<br>
        &nbsp;&nbsp;9 consecutive inspections. Pattern<br>
        &nbsp;&nbsp;suggests systemic, not accidental.
      </div>
      <div style="margin-top:20px;">
        <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">What to do with a flag</div>
        <div style="display:grid;gap:8px;font-size:14px;color:#475569;">
          <div style="display:grid;grid-template-columns:24px 1fr;gap:8px;align-items:start;">
            <span style="color:#16a34a;font-weight:700;">1.</span>
            <span>Sentinel automatically passes the flag to Analyst — no action needed for routine cases</span>
          </div>
          <div style="display:grid;grid-template-columns:24px 1fr;gap:8px;align-items:start;">
            <span style="color:#16a34a;font-weight:700;">2.</span>
            <span>Supervisor can override threshold (via dashboard) to force Analyst on any ZIP</span>
          </div>
          <div style="display:grid;grid-template-columns:24px 1fr;gap:8px;align-items:start;">
            <span style="color:#16a34a;font-weight:700;">3.</span>
            <span>SEVERITY 5 always triggers immediate notification — Messenger bypasses queue</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>


<!-- APPENDIX S2: ANALYST Agent Guide -->
<div class="slide" id="sas2">
  <h3>Agent Guide S2 — ANALYST</h3>
  <div class="spacer"></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:48px;">
    <div>
      <div style="border-left:4px solid #7c3aed;padding-left:20px;margin-bottom:24px;">
        <div style="font-size:20px;font-weight:600;color:#0f172a;">Purpose</div>
        <p style="font-size:16px;margin-top:8px;">Deep cross-silo reasoning on flagged ZIPs. Answers: How bad? Why? Who's affected? What needs to happen?</p>
      </div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">Input context (what it receives)</div>
      <div style="display:grid;gap:6px;font-size:14px;margin-bottom:20px;">
        <div style="padding:8px 12px;background:#f8fafc;border-radius:6px;border:1px solid #e2e8f0;color:#475569;">Sentinel output (severity, reason, top concern)</div>
        <div style="padding:8px 12px;background:#f8fafc;border-radius:6px;border:1px solid #e2e8f0;color:#475569;">Full ZIP risk profile (all 12 metrics)</div>
        <div style="padding:8px 12px;background:#f8fafc;border-radius:6px;border:1px solid #e2e8f0;color:#475569;">Top 3 violators with inspection history</div>
        <div style="padding:8px 12px;background:#f8fafc;border-radius:6px;border:1px solid #e2e8f0;color:#475569;">County benchmark averages for comparison</div>
        <div style="padding:8px 12px;background:#f8fafc;border-radius:6px;border:1px solid #e2e8f0;color:#475569;">CDC health context for the tract</div>
      </div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">Reading the severity scale</div>
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <tr style="border-bottom:1px solid #e2e8f0;"><th style="padding:6px 8px;text-align:left;color:#94a3b8;">Level</th><th style="padding:6px 8px;text-align:left;color:#94a3b8;">Meaning</th><th style="padding:6px 8px;text-align:left;color:#94a3b8;">Expected response</th></tr>
        <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:6px 8px;color:#dc2626;font-weight:700;">5</td><td style="padding:6px 8px;color:#475569;">Cross-agency action needed immediately</td><td style="padding:6px 8px;color:#475569;">Health Officer brief same day</td></tr>
        <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:6px 8px;color:#d97706;font-weight:700;">4</td><td style="padding:6px 8px;color:#475569;">Compounding risk confirmed</td><td style="padding:6px 8px;color:#475569;">Weekly brief + inspection reprioritized</td></tr>
        <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:6px 8px;color:#d97706;font-weight:700;">3</td><td style="padding:6px 8px;color:#475569;">Elevated, one major signal</td><td style="padding:6px 8px;color:#475569;">Supervisor notified, monitoring</td></tr>
        <tr><td style="padding:6px 8px;color:#16a34a;font-weight:700;">1–2</td><td style="padding:6px 8px;color:#475569;">Within normal range</td><td style="padding:6px 8px;color:#475569;">Monthly summary only</td></tr>
      </table>
    </div>
    <div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">Output sections</div>
      <div style="display:grid;gap:8px;font-size:14px;">
        <div style="padding:12px;background:#faf5ff;border:1px solid #e9d5ff;border-radius:8px;">
          <div style="color:#7c3aed;font-weight:600;margin-bottom:4px;">1. SEVERITY</div>
          <div style="color:#475569;">Final severity score with justification. Overrides Sentinel if Analyst finds more/less than expected.</div>
        </div>
        <div style="padding:12px;background:#faf5ff;border:1px solid #e9d5ff;border-radius:8px;">
          <div style="color:#7c3aed;font-weight:600;margin-bottom:4px;">2. ROOT CAUSES</div>
          <div style="color:#475569;">Systemic factors behind the pattern — not just "they failed inspection" but why the failures cluster here.</div>
        </div>
        <div style="padding:12px;background:#faf5ff;border:1px solid #e9d5ff;border-radius:8px;">
          <div style="color:#7c3aed;font-weight:600;margin-bottom:4px;">3. AFFECTED POPULATION</div>
          <div style="color:#475569;">Estimated residents at risk, demographic vulnerability indicators, health burden context.</div>
        </div>
        <div style="padding:12px;background:#faf5ff;border:1px solid #e9d5ff;border-radius:8px;">
          <div style="color:#7c3aed;font-weight:600;margin-bottom:4px;">4. CROSS-SILO INSIGHT</div>
          <div style="color:#475569;">What only the combined dataset reveals — the key reason single-agency view was insufficient.</div>
        </div>
        <div style="padding:12px;background:#faf5ff;border:1px solid #e9d5ff;border-radius:8px;">
          <div style="color:#7c3aed;font-weight:600;margin-bottom:4px;">5. 30-DAY PRIORITIES</div>
          <div style="color:#475569;">Three specific actions with named responsible parties. Passed directly to Advisor for output generation.</div>
        </div>
      </div>
    </div>
  </div>
</div>


<!-- APPENDIX S3: ADVISOR Agent Guide -->
<div class="slide" id="sas3">
  <h3>Agent Guide S3 — ADVISOR</h3>
  <div class="spacer"></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:48px;">
    <div>
      <div style="border-left:4px solid #2563eb;padding-left:20px;margin-bottom:24px;">
        <div style="font-size:20px;font-weight:600;color:#0f172a;">Purpose</div>
        <p style="font-size:16px;margin-top:8px;">Translates Analyst findings into tailored, actionable outputs for each recipient type. The same risk → 5 different messages.</p>
      </div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">Recipient profiles</div>
      <div style="display:grid;gap:8px;font-size:13px;">
        <div style="display:grid;grid-template-columns:140px 1fr;gap:12px;padding:10px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;align-items:start;">
          <div style="color:#dc2626;font-weight:600;">County Health Officer</div>
          <div style="color:#475569;">Needs: cross-dept framing, decision points, board-ready language. Format: 1-page brief, bullet recommendations.</div>
        </div>
        <div style="display:grid;grid-template-columns:140px 1fr;gap:12px;padding:10px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;align-items:start;">
          <div style="color:#d97706;font-weight:600;">Insp. Supervisor</div>
          <div style="color:#475569;">Needs: ranked queue, pre-visit context, specific violation patterns. Format: dashboard list + briefs.</div>
        </div>
        <div style="display:grid;grid-template-columns:140px 1fr;gap:12px;padding:10px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;align-items:start;">
          <div style="color:#16a34a;font-weight:600;">Restaurant Owner</div>
          <div style="color:#475569;">Needs: plain language, specific fixes, actionable steps. Format: SMS checklist, conversational Q&amp;A.</div>
        </div>
        <div style="display:grid;grid-template-columns:140px 1fr;gap:12px;padding:10px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;align-items:start;">
          <div style="color:#2563eb;font-weight:600;">Resident</div>
          <div style="color:#475569;">Needs: simple safety answer, alternatives. Format: conversational web chat, no jargon.</div>
        </div>
        <div style="display:grid;grid-template-columns:140px 1fr;gap:12px;padding:10px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;align-items:start;">
          <div style="color:#7c3aed;font-weight:600;">County Supervisor</div>
          <div style="color:#475569;">Needs: district comparison, budget framing, political talking points. Format: PDF scorecard.</div>
        </div>
      </div>
    </div>
    <div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">How output gets shaped</div>
      <div style="font-size:14px;color:#475569;line-height:1.8;margin-bottom:20px;">
        Each recipient receives the same underlying finding, but the Advisor:<br><br>
        • Changes <strong style="color:#1e293b;">vocabulary</strong> (technical → plain language for owners/residents)<br>
        • Changes <strong style="color:#1e293b;">scope</strong> (single restaurant for supervisor vs. district view for elected)<br>
        • Changes <strong style="color:#1e293b;">ask</strong> (Health Officer: approve surge vs. Owner: fix cooler temp)<br>
        • Changes <strong style="color:#1e293b;">urgency framing</strong> (immediate brief vs. scheduled report)
      </div>
      <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:20px;">
        <div style="font-size:13px;font-weight:600;color:#2563eb;margin-bottom:12px;">EXAMPLE: Same ZIP 95122 finding →</div>
        <div style="display:grid;gap:8px;font-size:13px;">
          <div style="color:#dc2626;"><strong>Health Officer:</strong> <span style="color:#475569;">"Recommend cross-department surge — DEH, Sheriff, Public Health. 210K residents at risk."</span></div>
          <div style="color:#d97706;"><strong>Supervisor:</strong> <span style="color:#475569;">"Banh Mi Oven is #1 priority. Pre-visit brief: temp control and TPHC labeling."</span></div>
          <div style="color:#16a34a;"><strong>Owner:</strong> <span style="color:#475569;">"Your cooler was 46°F. It needs to be ≤41°F. Check thermostat and door seals before inspection."</span></div>
          <div style="color:#2563eb;"><strong>Resident:</strong> <span style="color:#475569;">"Banh Mi Oven has failed 9 inspections. Here are 3 safer alternatives nearby."</span></div>
        </div>
      </div>
    </div>
  </div>
</div>


<!-- APPENDIX S4: MESSENGER Agent Guide -->
<div class="slide" id="sas4">
  <h3>Agent Guide S4 — MESSENGER</h3>
  <div class="spacer"></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:48px;">
    <div>
      <div style="border-left:4px solid #d97706;padding-left:20px;margin-bottom:24px;">
        <div style="font-size:20px;font-weight:600;color:#0f172a;">Purpose</div>
        <p style="font-size:16px;margin-top:8px;">Routes Advisor outputs to the right person, via the right channel, at the right time. Tracks delivery and follow-up.</p>
      </div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">Routing rules</div>
      <table style="width:100%;border-collapse:collapse;font-size:13px;">
        <tr style="border-bottom:2px solid #e2e8f0;"><th style="padding:8px;text-align:left;color:#94a3b8;">Urgency</th><th style="padding:8px;text-align:left;color:#94a3b8;">Channel</th><th style="padding:8px;text-align:left;color:#94a3b8;">Timing</th></tr>
        <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:8px;"><span style="background:#fee2e2;color:#dc2626;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">IMMEDIATE</span></td><td style="padding:8px;color:#475569;">Email + dashboard alert</td><td style="padding:8px;color:#475569;">Within 5 minutes</td></tr>
        <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:8px;"><span style="background:#fef9c3;color:#d97706;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">MORNING</span></td><td style="padding:8px;color:#475569;">Dashboard queue</td><td style="padding:8px;color:#475569;">Ready by 7:30 AM</td></tr>
        <tr style="border-bottom:1px solid #f1f5f9;"><td style="padding:8px;"><span style="background:#dcfce7;color:#16a34a;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">SCHEDULED</span></td><td style="padding:8px;color:#475569;">SMS or email</td><td style="padding:8px;color:#475569;">Pre-set window</td></tr>
        <tr><td style="padding:8px;"><span style="background:#dbeafe;color:#2563eb;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">ON-DEMAND</span></td><td style="padding:8px;color:#475569;">Web chat</td><td style="padding:8px;color:#475569;">Real-time response</td></tr>
      </table>
      <div style="margin-top:20px;font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">Follow-up tracking</div>
      <div style="display:grid;gap:6px;font-size:14px;color:#475569;">
        <div>• Records delivery confirmation for all channels</div>
        <div>• Tracks open/read status for email outputs</div>
        <div>• Schedules reminder if Health Officer brief not actioned within 48h</div>
        <div>• Logs all owner SMS replies for Analyst context in next cycle</div>
      </div>
    </div>
    <div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">Channel specifications</div>
      <div style="display:grid;gap:12px;">
        <div style="padding:14px;background:#fff1f2;border:1px solid #fecaca;border-radius:8px;">
          <div style="color:#dc2626;font-weight:600;margin-bottom:6px;">📧 Email (Health Officer)</div>
          <div style="font-size:13px;color:#475569;line-height:1.7;">HTML formatted. 2-section layout: executive summary + recommended actions. PDF brief attached. Forwarding link included for cross-dept sharing.</div>
        </div>
        <div style="padding:14px;background:#fefce8;border:1px solid #fef08a;border-radius:8px;">
          <div style="color:#d97706;font-weight:600;margin-bottom:6px;">🖥 Dashboard (Supervisor)</div>
          <div style="font-size:13px;color:#475569;line-height:1.7;">Ranked queue updated each morning. One-click inspector assignment. Pre-visit brief expands inline. All-time violation history accessible.</div>
        </div>
        <div style="padding:14px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;">
          <div style="color:#16a34a;font-weight:600;margin-bottom:6px;">💬 SMS (Restaurant Owner)</div>
          <div style="font-size:13px;color:#475569;line-height:1.7;">Opt-in via DEH registration. Two-way: owner replies trigger Advisor for follow-up answers. Max 3 coaching messages per inspection cycle.</div>
        </div>
        <div style="padding:14px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;">
          <div style="color:#2563eb;font-weight:600;margin-bottom:6px;">🌐 Web Chat (Resident)</div>
          <div style="font-size:13px;color:#475569;line-height:1.7;">Public portal. No login. Natural language queries about any restaurant or neighborhood. Returns inspection history, risk context, and safe alternatives.</div>
        </div>
      </div>
    </div>
  </div>
</div>


<!-- APPENDIX S5: County Health Officer Guide -->
<div class="slide" id="sas5">
  <h3>User Guide S5 — County Health Officer</h3>
  <div class="spacer"></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:48px;">
    <div>
      <div style="border-left:4px solid #dc2626;padding-left:20px;margin-bottom:24px;">
        <div style="font-size:20px;font-weight:600;color:#0f172a;">What you receive</div>
        <p style="font-size:16px;margin-top:8px;">A weekly risk brief every Monday morning summarizing which neighborhoods crossed compounding risk thresholds, why, and what cross-department action is recommended.</p>
      </div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">Weekly brief structure</div>
      <div style="display:grid;gap:8px;font-size:14px;">
        <div style="padding:10px 14px;background:#fff1f2;border-radius:8px;border-left:3px solid #dc2626;">
          <strong style="color:#dc2626;">Section 1: Executive Summary</strong>
          <div style="color:#475569;margin-top:4px;">Number of ZIPs flagged, highest severity, key metric driving this week's alerts</div>
        </div>
        <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;border-left:3px solid #e2e8f0;">
          <strong style="color:#1e293b;">Section 2: Per-ZIP Profiles</strong>
          <div style="color:#475569;margin-top:4px;">One page per flagged ZIP: data snapshot, Analyst findings, cross-silo insight</div>
        </div>
        <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;border-left:3px solid #e2e8f0;">
          <strong style="color:#1e293b;">Section 3: Recommended Actions</strong>
          <div style="color:#475569;margin-top:4px;">Specific asks for DEH, Sheriff, and Public Health — with measurable outcomes</div>
        </div>
        <div style="padding:10px 14px;background:#f0fdf4;border-radius:8px;border-left:3px solid #16a34a;">
          <strong style="color:#16a34a;">Section 4: Resource Estimate</strong>
          <div style="color:#475569;margin-top:4px;">Staffing or budget needed for intervention, framed for supervisor approval</div>
        </div>
      </div>
    </div>
    <div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">Typical workflow</div>
      <div style="display:grid;gap:10px;font-size:14px;">
        <div style="display:grid;grid-template-columns:32px 1fr;gap:10px;align-items:start;">
          <div style="background:#dc2626;color:#ffffff;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex-shrink:0;">1</div>
          <div style="color:#475569;padding-top:4px;">Open weekly brief Monday AM — review top 3 flagged ZIPs and severity levels</div>
        </div>
        <div style="display:grid;grid-template-columns:32px 1fr;gap:10px;align-items:start;">
          <div style="background:#dc2626;color:#ffffff;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex-shrink:0;">2</div>
          <div style="color:#475569;padding-top:4px;">For SEVERITY 4–5: forward Advisor brief to relevant department leads with one click</div>
        </div>
        <div style="display:grid;grid-template-columns:32px 1fr;gap:10px;align-items:start;">
          <div style="background:#dc2626;color:#ffffff;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex-shrink:0;">3</div>
          <div style="color:#475569;padding-top:4px;">Approve or modify the recommended cross-department intervention plan</div>
        </div>
        <div style="display:grid;grid-template-columns:32px 1fr;gap:10px;align-items:start;">
          <div style="background:#dc2626;color:#ffffff;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex-shrink:0;">4</div>
          <div style="color:#475569;padding-top:4px;">Receive follow-up summary 30 days after intervention — did outcomes improve?</div>
        </div>
      </div>
      <div style="margin-top:24px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:16px;">
        <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;">Ad-hoc queries</div>
        <div style="font-size:14px;color:#475569;">You can request an on-demand analysis of any ZIP at any time via the dashboard. Type "Analyze ZIP 95116" and Sentinel + Analyst will run within 2 minutes.</div>
      </div>
    </div>
  </div>
</div>


<!-- APPENDIX S6: Inspection Supervisor Guide -->
<div class="slide" id="sas6">
  <h3>User Guide S6 — Inspection Supervisor</h3>
  <div class="spacer"></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:48px;">
    <div>
      <div style="border-left:4px solid #d97706;padding-left:20px;margin-bottom:24px;">
        <div style="font-size:20px;font-weight:600;color:#0f172a;">What you receive</div>
        <p style="font-size:16px;margin-top:8px;">A prioritized inspection queue each morning, pre-ranked by compounding risk score. Each entry includes a pre-visit brief built from violation history.</p>
      </div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">Dashboard features</div>
      <div style="display:grid;gap:8px;font-size:14px;">
        <div style="padding:10px 14px;background:#fefce8;border-radius:8px;border-left:3px solid #d97706;">
          <strong style="color:#d97706;">Priority Queue</strong>
          <div style="color:#475569;margin-top:4px;">All upcoming inspections ranked by risk. Red-flagged businesses at top. Drag to reorder if needed.</div>
        </div>
        <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;border-left:3px solid #e2e8f0;">
          <strong style="color:#1e293b;">Pre-Visit Brief</strong>
          <div style="color:#475569;margin-top:4px;">Click any business to see: top 3 most likely violations, prior inspection timeline, business profile.</div>
        </div>
        <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;border-left:3px solid #e2e8f0;">
          <strong style="color:#1e293b;">Inspector Assignment</strong>
          <div style="color:#475569;margin-top:4px;">One-click assign to available inspector. CivicPulse recommends senior inspector for SEVERITY 4+.</div>
        </div>
        <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;border-left:3px solid #e2e8f0;">
          <strong style="color:#1e293b;">Repeat Offender Alert</strong>
          <div style="color:#475569;margin-top:4px;">Businesses with 2+ Red inspections are flagged. You can request escalation to Health Officer directly.</div>
        </div>
      </div>
    </div>
    <div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">Pre-visit brief example</div>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:16px;font-size:13px;">
        <div style="font-weight:700;color:#dc2626;font-size:15px;margin-bottom:4px;">Banh Mi Oven — 95122</div>
        <div style="color:#94a3b8;margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid #e2e8f0;">Assigned: Senior Inspector Chen | Tue 9:00 AM</div>
        <div style="margin-bottom:10px;">
          <div style="color:#475569;font-weight:600;margin-bottom:6px;">Focus areas (based on 9 prior Red inspections):</div>
          <div style="display:grid;gap:4px;color:#475569;">
            <div style="padding:6px 10px;background:#fff1f2;border-radius:4px;">🌡 Hot/cold holding temps — 7 of 9 failures involved this</div>
            <div style="padding:6px 10px;background:#fefce8;border-radius:4px;">🏷 TPHC time marking — labels missing repeatedly</div>
            <div style="padding:6px 10px;background:#f8fafc;border-radius:4px;">🚿 Handwash sink — soap/towels absent in 3 inspections</div>
          </div>
        </div>
        <div style="color:#94a3b8;font-size:12px;">Last inspection: Red (July 2025) · 23 critical violations on record · Poverty rate: 10.5%</div>
      </div>
      <div style="margin-top:16px;background:#fefce8;border:1px solid #fef08a;border-radius:10px;padding:16px;">
        <div style="font-size:13px;font-weight:600;color:#d97706;margin-bottom:8px;">What happens after inspection</div>
        <div style="font-size:14px;color:#475569;line-height:1.7;">Results auto-sync to CivicPulse. If result is Red again, Sentinel re-evaluates the ZIP and notifies Health Officer. If result is Green, the business is removed from the priority queue for 6 months.</div>
      </div>
    </div>
  </div>
</div>


<!-- APPENDIX S7: Restaurant Owner Guide -->
<div class="slide" id="sas7">
  <h3>User Guide S7 — Restaurant Owner</h3>
  <div class="spacer"></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:48px;">
    <div>
      <div style="border-left:4px solid #16a34a;padding-left:20px;margin-bottom:24px;">
        <div style="font-size:20px;font-weight:600;color:#0f172a;">What you receive</div>
        <p style="font-size:16px;margin-top:8px;">A proactive SMS coaching message 7 days before your scheduled inspection, built from your specific violation history — not generic advice.</p>
      </div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">How to opt in</div>
      <div style="display:grid;gap:8px;font-size:14px;margin-bottom:20px;">
        <div style="padding:10px 14px;background:#f0fdf4;border-radius:8px;border-left:3px solid #16a34a;">
          <strong style="color:#16a34a;">Option 1:</strong> <span style="color:#475569;">Text "JOIN" to (408) 299-2100 with your DEH permit number</span>
        </div>
        <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;border-left:3px solid #e2e8f0;">
          <strong style="color:#1e293b;">Option 2:</strong> <span style="color:#475569;">Enroll through the DEH online portal at deh.sccgov.org</span>
        </div>
        <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;border-left:3px solid #e2e8f0;">
          <strong style="color:#1e293b;">Option 3:</strong> <span style="color:#475569;">Inspector provides enrollment card during your next inspection visit</span>
        </div>
      </div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">What the message includes</div>
      <div style="display:grid;gap:6px;font-size:14px;color:#475569;">
        <div>✓ Your top 3 most likely violations based on history</div>
        <div>✓ Specific corrective steps for each (not generic)</div>
        <div>✓ Reference to your last inspection result</div>
        <div>✓ Instructions to reply for follow-up questions</div>
      </div>
    </div>
    <div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">Two-way SMS interaction</div>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px;font-size:13px;">
        <div style="color:#94a3b8;font-size:11px;text-align:center;margin-bottom:12px;">(408) 299-2100 · CivicPulse</div>
        <div style="background:#e2e8f0;border-radius:10px 10px 10px 3px;padding:10px 12px;max-width:85%;margin-bottom:8px;color:#1e293b;line-height:1.6;">
          Inspection next week. Top concerns: (1) Hot holding temps — need ≤41°F. (2) TPHC time labels. (3) Handwash sink supplies. Reply HELP for details on any.
        </div>
        <div style="background:#16a34a;border-radius:10px 10px 3px 10px;padding:10px 12px;margin-left:auto;max-width:65%;color:#ffffff;margin-bottom:8px;">HELP 1</div>
        <div style="background:#e2e8f0;border-radius:10px 10px 10px 3px;padding:10px 12px;max-width:85%;color:#1e293b;line-height:1.6;margin-bottom:8px;">
          Hot holding: All cooked food must stay at 135°F or above. Cold holding: 41°F or below. Your reach-in cooler was at 46°F in July. Check thermostat setting and door seal condition.
        </div>
        <div style="background:#16a34a;border-radius:10px 10px 3px 10px;padding:10px 12px;margin-left:auto;max-width:65%;color:#ffffff;">Thanks!</div>
      </div>
      <div style="margin-top:14px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:14px;">
        <div style="font-size:13px;font-weight:600;color:#16a34a;margin-bottom:6px;">Privacy &amp; data use</div>
        <div style="font-size:13px;color:#475569;">Messages use only your publicly available DEH inspection records. No private business data is shared. Opt out anytime by replying STOP.</div>
      </div>
    </div>
  </div>
</div>


<!-- APPENDIX S8: Resident Guide -->
<div class="slide" id="sas8">
  <h3>User Guide S8 — Community Resident</h3>
  <div class="spacer"></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:48px;">
    <div>
      <div style="border-left:4px solid #2563eb;padding-left:20px;margin-bottom:24px;">
        <div style="font-size:20px;font-weight:600;color:#0f172a;">What you can do</div>
        <p style="font-size:16px;margin-top:8px;">Ask any question about restaurant safety or neighborhood food risk at <strong>civicpulse.scc.gov/check</strong>. No login, no form. Just ask.</p>
      </div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">What you can ask</div>
      <div style="display:grid;gap:8px;font-size:14px;">
        <div style="padding:10px 14px;background:#eff6ff;border-radius:8px;border-left:3px solid #2563eb;">
          <strong style="color:#2563eb;">Restaurant safety:</strong>
          <div style="color:#475569;margin-top:2px;">"Is [restaurant name] safe to eat at?" → Inspection history, violations, risk rating</div>
        </div>
        <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;border-left:3px solid #e2e8f0;">
          <strong style="color:#1e293b;">Neighborhood check:</strong>
          <div style="color:#475569;margin-top:2px;">"What restaurants in 95122 have clean inspection records?" → Green-rated list nearby</div>
        </div>
        <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;border-left:3px solid #e2e8f0;">
          <strong style="color:#1e293b;">Risk context:</strong>
          <div style="color:#475569;margin-top:2px;">"How does my neighborhood compare to the rest of the county?" → ZIP risk score and rank</div>
        </div>
        <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;border-left:3px solid #e2e8f0;">
          <strong style="color:#1e293b;">Alternatives:</strong>
          <div style="color:#475569;margin-top:2px;">"What are safe Vietnamese restaurants near Story Rd?" → Top-rated by inspection record within 1mi</div>
        </div>
      </div>
    </div>
    <div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">What you will NOT see</div>
      <div style="display:grid;gap:8px;font-size:14px;margin-bottom:20px;">
        <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;color:#475569;">✗ Raw violation codes or regulatory language — plain English only</div>
        <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;color:#475569;">✗ Pending or unresolved complaints — only confirmed inspection records</div>
        <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;color:#475569;">✗ Owner contact details or business financials</div>
      </div>
      <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:16px;">
        <div style="font-size:13px;font-weight:600;color:#2563eb;margin-bottom:8px;">How the agent answers</div>
        <div style="font-size:14px;color:#475569;line-height:1.7;">The Advisor agent answers using the most recent inspection data available, explains the risk in plain language, and always offers safer alternatives if the answer is concerning. It won't say "I can't answer that" — if there's relevant public data, it will use it.</div>
      </div>
      <div style="margin-top:14px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:14px;">
        <div style="font-size:13px;font-weight:600;color:#16a34a;margin-bottom:6px;">Available in Spanish &amp; Vietnamese</div>
        <div style="font-size:13px;color:#475569;">The chat interface auto-detects language and responds in kind. Core target neighborhoods (95116, 95122) are majority Spanish and Vietnamese speaking.</div>
      </div>
    </div>
  </div>
</div>


<!-- APPENDIX S9: County Supervisor Guide -->
<div class="slide" id="sas9">
  <h3>User Guide S9 — County Supervisor</h3>
  <div class="spacer"></div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:48px;">
    <div>
      <div style="border-left:4px solid #7c3aed;padding-left:20px;margin-bottom:24px;">
        <div style="font-size:20px;font-weight:600;color:#0f172a;">What you receive</div>
        <p style="font-size:16px;margin-top:8px;">A monthly District Scorecard PDF showing how your district's food safety, crime, and economic vulnerability compare to the rest of the county — with board-ready talking points.</p>
      </div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">Scorecard structure</div>
      <div style="display:grid;gap:8px;font-size:14px;">
        <div style="padding:10px 14px;background:#faf5ff;border-radius:8px;border-left:3px solid #7c3aed;">
          <strong style="color:#7c3aed;">District overview</strong>
          <div style="color:#475569;margin-top:2px;">Population, businesses, median income vs. county — one page, one look</div>
        </div>
        <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;border-left:3px solid #e2e8f0;">
          <strong style="color:#1e293b;">Risk concentration</strong>
          <div style="color:#475569;margin-top:2px;">Your district's share of county-wide Red inspections, critical violations, repeat offenders — with trend vs. prior month</div>
        </div>
        <div style="padding:10px 14px;background:#f8fafc;border-radius:8px;border-left:3px solid #e2e8f0;">
          <strong style="color:#1e293b;">Top ZIP profiles</strong>
          <div style="color:#475569;margin-top:2px;">Up to 3 highest-risk ZIP codes in your district with data summary</div>
        </div>
        <div style="padding:10px 14px;background:#f0fdf4;border-radius:8px;border-left:3px solid #16a34a;">
          <strong style="color:#16a34a;">Board talking points</strong>
          <div style="color:#475569;margin-top:2px;">Advisor-generated 2-sentence framing for use at next Board of Supervisors meeting</div>
        </div>
      </div>
    </div>
    <div>
      <div style="font-size:13px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:12px;">Example scorecard excerpt</div>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:16px;font-size:13px;">
        <div style="color:#7c3aed;font-weight:700;font-size:15px;margin-bottom:4px;">District 3 — March 2026</div>
        <div style="color:#94a3b8;font-size:11px;margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid #e2e8f0;">Covers East San Jose · Milpitas · Prepared by CivicPulse</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px;font-size:12px;">
          <div style="padding:8px;background:#fff1f2;border-radius:6px;text-align:center;">
            <div style="color:#dc2626;font-size:20px;font-weight:700;">34%</div>
            <div style="color:#94a3b8;">of county Red inspections</div>
          </div>
          <div style="padding:8px;background:#fefce8;border-radius:6px;text-align:center;">
            <div style="color:#d97706;font-size:20px;font-weight:700;">19%</div>
            <div style="color:#94a3b8;">of county restaurants</div>
          </div>
          <div style="padding:8px;background:#f8fafc;border-radius:6px;text-align:center;">
            <div style="color:#1e293b;font-size:20px;font-weight:700;">$95K</div>
            <div style="color:#94a3b8;">median income (vs $153K county)</div>
          </div>
          <div style="padding:8px;background:#f8fafc;border-radius:6px;text-align:center;">
            <div style="color:#1e293b;font-size:20px;font-weight:700;">253K</div>
            <div style="color:#94a3b8;">residents affected</div>
          </div>
        </div>
        <div style="background:#f0fdf4;border-left:3px solid #16a34a;padding:10px 12px;border-radius:0 6px 6px 0;font-size:12px;color:#15803d;line-height:1.6;">
          <strong>Board talking point:</strong> "District 3 bears 34% of the county's repeat food safety failures with only 19% of its restaurants — a structural inequity that requires cross-agency response, not just more inspections."
        </div>
      </div>
      <div style="margin-top:14px;background:#faf5ff;border:1px solid #e9d5ff;border-radius:10px;padding:14px;">
        <div style="font-size:13px;font-weight:600;color:#7c3aed;margin-bottom:6px;">Requesting a custom analysis</div>
        <div style="font-size:13px;color:#475569;">Contact your district liaison to request a ZIP-level deep-dive before a board meeting, budget hearing, or community town hall.</div>
      </div>
    </div>
  </div>
</div>

"""

# Insert user guides before the Appendix 2 section
content = content.replace(
    '\n<!-- APPENDIX 2 — OPTIONAL / DISCARDABLE SLIDES -->',
    USER_GUIDES + '\n<!-- APPENDIX 2 — OPTIONAL / DISCARDABLE SLIDES -->'
)

# ── 6. Update TOC to include R and S ─────────────────────────────────────────
content = content.replace(
    '<div style="padding:10px 14px;border:1px solid #e2e8f0;border-radius:6px;color:#94a3b8;"><span style="color:#3b82f6;font-weight:600;margin-right:10px;">Q</span>User Interactions by Channel</div>',
    '''<div style="padding:10px 14px;border:1px solid #e2e8f0;border-radius:6px;color:#94a3b8;"><span style="color:#3b82f6;font-weight:600;margin-right:10px;">Q</span>User Interactions by Channel</div>
        <div style="padding:10px 14px;border:1px solid #e2e8f0;border-radius:6px;color:#94a3b8;"><span style="color:#3b82f6;font-weight:600;margin-right:10px;">R</span>Full System Architecture</div>
        <div style="padding:10px 14px;border:1px solid #22c55e;border-radius:6px;color:#1e293b;background:#f0fdf4;"><span style="color:#16a34a;font-weight:600;margin-right:10px;">S</span>User &amp; Agent Guides (S1–S9) <span style="color:#16a34a;font-size:12px;">← new</span></div>'''
)

# ── 7. Update Gradio app map style ───────────────────────────────────────────
# (also write this fix to civicpulse_app.py)

with open('/Users/johnny/hackathon/pitch_deck.html', 'w') as f:
    f.write(content)

print("Done. Slide count:", content.count('class="slide"'))
print("Main deck slides: s1,s2,s3,s4,s5b,s7,s_whatchanges,s8,s10,s14")
print("New slides added: s8 (user interactions), sar (full arch), sas_toc + sas1-9 (user guides)")
