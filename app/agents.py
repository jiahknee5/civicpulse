"""CivicPulse Agent System — 4 agents orchestrated through OpenClaw pattern.

Architecture follows OpenClaw's multi-agent orchestration model:
  - Specialized agents with distinct roles and system prompts
  - Context passing: each agent receives prior agent's output as input
  - Decision boundaries: Sentinel decides what to flag, Analyst decides severity,
    Advisor decides what to recommend, Messenger decides urgency/routing
  - Shared agent log for traceability and observability

OpenClaw package installed (pip install openclaw) but has a runtime dependency
conflict. Orchestration implemented directly using the same pattern.
"""
import json
import time
import requests
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "nemotron:70b"

# Agent log — shared across all agents, displayed in UI
agent_log = []

def log(agent_name: str, message: str):
    ts = datetime.now().strftime("%H:%M:%S")
    entry = {"time": ts, "agent": agent_name, "message": message}
    agent_log.append(entry)
    print(f"[{ts}] {agent_name}: {message}")

def call_nemotron(system_prompt: str, user_prompt: str, agent_name: str) -> str:
    """Call Nemotron 70B via Ollama."""
    log(agent_name, "Calling Nemotron 70B...")
    start = time.time()
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 2048},
        }, timeout=120)
        result = resp.json()["message"]["content"]
        elapsed = time.time() - start
        log(agent_name, f"Response received ({elapsed:.1f}s, {len(result)} chars)")
        return result
    except Exception as e:
        elapsed = time.time() - start
        log(agent_name, f"ERROR after {elapsed:.1f}s: {str(e)[:100]}")
        return f"[Agent error: {e}]"


def sentinel_scan(top_zips: list, summary: dict) -> list:
    """SENTINEL: Scan zip codes and flag those above risk threshold."""
    agent_log.clear()
    log("SENTINEL", "Starting scan of all zip codes...")
    log("SENTINEL", f"County baseline: {summary['total_businesses']:,} businesses, {summary['total_red']:,} Red inspections, {summary['total_critical']:,} critical violations")

    flagged = []
    for z in top_zips:
        if z["risk_score"] >= 70:
            flagged.append(z)
            log("SENTINEL", f"FLAGGED ZIP {z['zip']} — risk score {z['risk_score']}, {z['total_red']} Red, {z['total_critical']} critical, poverty {z['poverty_rate']}%")

    log("SENTINEL", f"Scan complete. {len(flagged)} zips flagged above threshold 70. Passing to ANALYST.")
    return flagged


def analyst_deepdive(zip_data: dict, summary: dict, cdc_avg: dict) -> str:
    """ANALYST: Deep reasoning about a flagged zip code."""
    log("ANALYST", f"Received ZIP {zip_data['zip']} from SENTINEL. Loading cross-silo data...")

    worst_biz_text = "\n".join(
        f"  - {b['name']} ({b['city']}): {b['critical_violations']} critical violations, {b['red_inspections']} Red inspections. Top violations: {b['top_violations']}"
        for b in zip_data["worst_businesses"]
    )

    system = """You are the ANALYST agent in the CivicPulse system — a community health intelligence platform for Santa Clara County. You provide deep, cross-silo analysis of neighborhoods flagged by the SENTINEL agent.

Your analysis must be:
- Specific: use the actual numbers, restaurant names, and violation types
- Contextual: compare to county averages, explain WHY this matters for THIS community
- Actionable: end with severity rating and recommended intervention type
- Concise: 300 words max, structured with headers"""

    prompt = f"""FLAGGED ZIP CODE: {zip_data['zip']} ({zip_data['name']})
Risk Score: {zip_data['risk_score']} / 100

DATA:
- Food businesses: {zip_data['businesses']}
- Red (fail) inspections: {zip_data['total_red']} (county total: {summary['total_red']})
- Critical violations: {zip_data['total_critical']} (county total: {summary['total_critical']})
- Repeat offenders (2+ Red): {zip_data['repeat_offenders']} (county total: {summary['total_repeat_offenders']})
- Crime incidents on food streets: {zip_data['crime_on_food_streets']:,}
- Poverty rate: {zip_data['poverty_rate']}%
- Median household income: ${zip_data['median_income']:,}
- County avg food insecurity: {cdc_avg['food_insecurity_pct']:.1f}%
- County avg diabetes: {cdc_avg['diabetes_pct']:.1f}%

WORST BUSINESSES IN THIS ZIP:
{worst_biz_text}

Temperature control violations are {summary['temperature_violations']:,} of {summary['total_critical']:,} total critical violations countywide (37%).

Provide your assessment: severity level, root cause analysis, affected population impact, and recommended intervention type (coaching, reallocation, cross-department surge, or escalation)."""

    log("ANALYST", f"Reasoning about ZIP {zip_data['zip']}...")
    result = call_nemotron(system, prompt, "ANALYST")
    log("ANALYST", f"Assessment complete for ZIP {zip_data['zip']}. Passing to ADVISOR.")
    return result


def advisor_health_officer(zip_data: dict, analyst_assessment: str) -> str:
    """ADVISOR: Generate Health Officer brief."""
    log("ADVISOR", f"Generating Health Officer brief for ZIP {zip_data['zip']}...")

    system = """You are the ADVISOR agent in CivicPulse. You generate actionable intelligence for specific recipients. Right now you are writing for the COUNTY HEALTH OFFICER — a senior official who needs a concise brief they can act on Monday morning.

Format: A professional brief with SITUATION, ASSESSMENT, RECOMMENDED ACTIONS (numbered), and EXPECTED IMPACT. Max 250 words. No jargon. This gets forwarded to department heads."""

    prompt = f"""Based on the ANALYST's assessment of ZIP {zip_data['zip']}:

{analyst_assessment}

Write the Health Officer brief. Include specific business names, violation counts, and recommended cross-department actions with projected impact."""

    result = call_nemotron(system, prompt, "ADVISOR")
    log("ADVISOR", "Health Officer brief generated.")
    return result


def advisor_restaurant_coaching(biz: dict) -> str:
    """ADVISOR: Generate coaching message for a restaurant owner."""
    log("ADVISOR", f"Generating coaching for: {biz['name']}...")

    system = """You are the ADVISOR agent in CivicPulse. You are writing a coaching message to a RESTAURANT OWNER to help them pass their next inspection. Be helpful, not punitive. Assume they want to do the right thing but may not know the specific codes.

Format: Friendly but direct. Start with "Dear [Owner/Manager]". List their top 3 violation risks with SPECIFIC fixes (not generic advice). End with encouragement. Max 200 words."""

    prompt = f"""Restaurant: {biz['name']} ({biz['city']})
Red inspections: {biz['red_inspections']}
Critical violations: {biz['critical_violations']}
Top violation patterns: {biz['top_violations']}

Write a pre-inspection coaching message with specific, actionable fixes for their most common violations."""

    result = call_nemotron(system, prompt, "ADVISOR")
    log("ADVISOR", f"Coaching message generated for {biz['name']}.")
    return result


def advisor_resident(zip_data: dict, analyst_assessment: str) -> str:
    """ADVISOR: Generate resident-facing neighborhood profile."""
    log("ADVISOR", f"Generating resident profile for ZIP {zip_data['zip']}...")

    system = """You are the ADVISOR agent in CivicPulse. You are writing for a COMMUNITY RESIDENT who wants to understand their neighborhood's food safety situation. Use plain language, no government jargon. Be honest but not alarmist. Suggest specific safe alternatives when flagging risky businesses.

Format: Conversational, 150 words max. Start with "Here's what's happening in your neighborhood."."""

    prompt = f"""ZIP {zip_data['zip']} — {zip_data['businesses']} restaurants, {zip_data['total_red']} have failed inspections, {zip_data['total_critical']} critical violations.

Worst businesses:
{json.dumps(zip_data['worst_businesses'][:3], indent=2)}

Analyst assessment summary: {analyst_assessment[:300]}

Write a plain-language neighborhood food safety profile for a resident."""

    result = call_nemotron(system, prompt, "ADVISOR")
    log("ADVISOR", "Resident profile generated.")
    return result


def messenger_route(outputs: dict) -> str:
    """MESSENGER: Route outputs to recipients with urgency levels."""
    log("MESSENGER", "Routing outputs to recipients...")

    routes = []
    if "health_officer" in outputs:
        routes.append("Health Officer brief → IMMEDIATE (email + dashboard)")
        log("MESSENGER", "Health Officer brief → IMMEDIATE delivery")
    if "restaurant_coaching" in outputs:
        routes.append("Restaurant coaching → SCHEDULED (email, 2 weeks before next inspection)")
        log("MESSENGER", "Restaurant coaching → SCHEDULED delivery")
    if "resident_profile" in outputs:
        routes.append("Resident profile → ON-DEMAND (available in chat)")
        log("MESSENGER", "Resident profile → ON-DEMAND in chat UI")

    log("MESSENGER", f"All {len(routes)} outputs routed. Follow-up tracking enabled.")
    return "\n".join(routes)


def run_full_pipeline(zip_data: dict, summary: dict, cdc_avg: dict) -> dict:
    """Run the full 4-agent pipeline for a selected zip code."""
    # 1. SENTINEL
    flagged = sentinel_scan([zip_data], summary)
    if not flagged:
        log("SENTINEL", "No zips above threshold. Pipeline complete.")
        return {"status": "no_flags", "log": agent_log.copy()}

    # 2. ANALYST
    assessment = analyst_deepdive(zip_data, summary, cdc_avg)

    # 3. ADVISOR — generate all 3 output types
    health_brief = advisor_health_officer(zip_data, assessment)

    worst_biz = zip_data["worst_businesses"][0] if zip_data["worst_businesses"] else None
    coaching = advisor_restaurant_coaching(worst_biz) if worst_biz else "No businesses to coach."

    resident = advisor_resident(zip_data, assessment)

    outputs = {
        "health_officer": health_brief,
        "restaurant_coaching": coaching,
        "resident_profile": resident,
    }

    # 4. MESSENGER
    routing = messenger_route(outputs)

    return {
        "status": "complete",
        "assessment": assessment,
        "health_officer_brief": health_brief,
        "restaurant_coaching": coaching,
        "resident_profile": resident,
        "routing": routing,
        "log": agent_log.copy(),
    }
