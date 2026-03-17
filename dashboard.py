"""Quick EDA Dashboard for Santa Clara County Datasets — runs on DELL-31"""
import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

DATA_DIR = os.path.expanduser("~/data")

# Load datasets
print("Loading datasets...")
crime = pd.read_csv(f"{DATA_DIR}/Crime_Reports_20260306.csv")
eeo = pd.read_csv(f"{DATA_DIR}/Employee_Breakdown_by_Equal_Employment_Opportunity_Categories_20260306.csv")
biz = pd.read_csv(f"{DATA_DIR}/SCC_DEH_Food_Data_BUSINESS_20260306.csv")
insp = pd.read_csv(f"{DATA_DIR}/SCC_DEH_Food_Data_INSPECTIONS_20260306.csv")
viol = pd.read_csv(f"{DATA_DIR}/SCC_DEH_Food_Data_VIOLATIONS_20260306.csv")
photos = pd.read_csv(f"{DATA_DIR}/County_Photographers'_Collection_20260306.csv")
print("All loaded.")

DARK = "plotly_dark"

def make_data_dict(df, name):
    """Generate a data dictionary markdown string for a dataframe."""
    lines = [f"### {name}", f"**{len(df):,} rows x {len(df.columns)} columns**\n",
             "| Column | Type | Non-Null | Unique | Sample Values |",
             "|--------|------|----------|--------|---------------|"]
    for col in df.columns:
        dtype = str(df[col].dtype)
        non_null = f"{df[col].notna().sum():,}"
        nunique = f"{df[col].nunique():,}"
        samples = df[col].dropna().unique()[:3]
        sample_str = ", ".join(str(s)[:30] for s in samples)
        lines.append(f"| {col} | {dtype} | {non_null} | {nunique} | {sample_str} |")
    return "\n".join(lines)

def make_sample_table(df):
    """Return first 10 rows as HTML table."""
    return df.head(10).to_html(index=False, classes="table", border=0)

# --- Pre-compute joined food data for map ---
print("Joining food tables for map...")
# Join inspections to businesses
food_joined = insp.merge(biz[["business_id", "name", "address", "CITY", "latitude", "longitude"]], on="business_id", how="left")
# Count critical violations per inspection
crit_counts = viol[viol["critical"] == "true"].groupby("inspection_id").size().reset_index(name="critical_violations")
food_joined = food_joined.merge(crit_counts, on="inspection_id", how="left")
food_joined["critical_violations"] = food_joined["critical_violations"].fillna(0).astype(int)
# Get latest inspection per business
food_joined["date"] = pd.to_datetime(food_joined["date"], errors="coerce")
latest = food_joined.sort_values("date").groupby("business_id").last().reset_index()
latest = latest.dropna(subset=["latitude", "longitude"])
print(f"Map data ready: {len(latest)} businesses with coordinates")

def food_map():
    """Plotly scattermapbox of food businesses colored by last inspection result."""
    result_labels = {"G": "Green (Pass)", "Y": "Yellow (Conditional)", "R": "Red (Fail)"}
    latest["result_label"] = latest["result"].map(result_labels)

    fig = px.scatter_mapbox(
        latest, lat="latitude", lon="longitude",
        color="result_label",
        color_discrete_map={"Green (Pass)": "#22c55e", "Yellow (Conditional)": "#eab308", "Red (Fail)": "#ef4444"},
        hover_name="name",
        hover_data={"address": True, "CITY": True, "SCORE": True, "critical_violations": True, "date": True, "latitude": False, "longitude": False},
        title=f"Food Business Inspection Results — {len(latest):,} locations",
        height=700,
        zoom=10,
        center={"lat": 37.35, "lon": -121.9},
    )
    fig.update_layout(
        mapbox_style="carto-darkmatter",
        template=DARK,
        legend_title="Last Inspection Result",
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig

def food_violations_heatmap():
    """Heatmap of critical violations by location."""
    crit_biz = food_joined[food_joined["critical_violations"] > 0].dropna(subset=["latitude", "longitude"])
    fig = px.density_mapbox(
        crit_biz, lat="latitude", lon="longitude",
        z="critical_violations", radius=15,
        title="Critical Violation Density Heatmap",
        height=700,
        zoom=10,
        center={"lat": 37.35, "lon": -121.9},
    )
    fig.update_layout(
        mapbox_style="carto-darkmatter",
        template=DARK,
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig

def crime_food_overlay_map():
    """Overlay map: food businesses sized by crime on their street, colored by inspection result."""
    overlay_path = os.path.expanduser("~/hackathon/biz_crime_overlay.csv")
    if not os.path.exists(overlay_path):
        return go.Figure().update_layout(title="Run data join first", template=DARK)

    ov = pd.read_csv(overlay_path)
    ov = ov.dropna(subset=["latitude", "longitude", "result"])
    result_labels = {"G": "Green (Pass)", "Y": "Yellow (Conditional)", "R": "Red (Fail)"}
    ov["result_label"] = ov["result"].map(result_labels)
    # Log scale for bubble size
    import numpy as np
    ov["crime_log"] = np.log1p(ov["crime_count"])

    fig = px.scatter_mapbox(
        ov, lat="latitude", lon="longitude",
        color="result_label",
        size="crime_log",
        size_max=20,
        color_discrete_map={"Green (Pass)": "#22c55e", "Yellow (Conditional)": "#eab308", "Red (Fail)": "#ef4444"},
        hover_name="name",
        hover_data={
            "address": True, "CITY": True, "crime_count": True,
            "top_crime": True, "crit_viols": True, "SCORE": True,
            "latitude": False, "longitude": False, "crime_log": False, "result_label": False,
        },
        title=f"Crime x Food Safety Overlay — {len(ov):,} businesses on streets with crime reports",
        height=750,
        zoom=10,
        center={"lat": 37.35, "lon": -121.9},
    )
    fig.update_layout(
        mapbox_style="carto-darkmatter",
        template=DARK,
        legend_title="Inspection Result",
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig

def crime_tab():
    top = crime["parent_incident_type"].value_counts().head(15)
    fig1 = px.bar(x=top.values, y=top.index, orientation="h", template=DARK,
                  title="Top 15 Incident Categories (260K reports)",
                  labels={"x": "Count", "y": ""})
    fig1.update_layout(yaxis=dict(autorange="reversed"), height=500)

    top2 = crime["incident_type_primary"].value_counts().head(20)
    fig2 = px.bar(x=top2.values, y=top2.index, orientation="h", template=DARK,
                  title="Top 20 Specific Incident Types",
                  labels={"x": "Count", "y": ""})
    fig2.update_layout(yaxis=dict(autorange="reversed"), height=600)

    try:
        crime["dt"] = pd.to_datetime(crime["incident_datetime"], format="%Y %b %d %I:%M:%S %p", errors="coerce")
        valid = crime[crime["dt"] > "2019-01-01"].copy()
        # Top 8 categories for stacked chart, rest as "Other Categories"
        top_cats = valid["parent_incident_type"].value_counts().head(8).index.tolist()
        valid["category"] = valid["parent_incident_type"].where(valid["parent_incident_type"].isin(top_cats), "Other Categories")
        monthly_cat = valid.groupby([pd.Grouper(key="dt", freq="ME"), "category"]).size().reset_index(name="count")
        fig3 = px.area(monthly_cat, x="dt", y="count", color="category", template=DARK,
                       title="Monthly Incidents by Category (2020-2026)",
                       labels={"dt": "Month", "count": "Incidents", "category": "Category"})
        fig3.update_layout(height=550, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    except:
        fig3 = go.Figure().update_layout(title="Could not parse dates", template=DARK)

    return fig1, fig2, fig3

def food_charts():
    result_map = {"G": "Green (Pass)", "Y": "Yellow (Conditional)", "R": "Red (Fail)"}
    insp["result_label"] = insp["result"].map(result_map)
    rc = insp["result_label"].value_counts()
    fig1 = px.pie(values=rc.values, names=rc.index, template=DARK,
                  title="Inspection Results (22K inspections)",
                  color_discrete_sequence=["#22c55e", "#eab308", "#ef4444"])

    city_counts = biz["CITY"].value_counts().head(15)
    fig2 = px.bar(x=city_counts.values, y=city_counts.index, orientation="h", template=DARK,
                  title="Food Businesses by City",
                  labels={"x": "Count", "y": ""})
    fig2.update_layout(yaxis=dict(autorange="reversed"), height=500)

    top_viol = viol["DESCRIPTION"].value_counts().head(15)
    fig3 = px.bar(x=top_viol.values, y=top_viol.index, orientation="h", template=DARK,
                  title="Top 15 Violation Types (64K violations)",
                  labels={"x": "Count", "y": ""})
    fig3.update_layout(yaxis=dict(autorange="reversed"), height=500)

    crit = viol["critical"].value_counts()
    fig4 = px.pie(values=crit.values, names=["Non-Critical", "Critical"], template=DARK,
                  title="Critical vs Non-Critical Violations",
                  color_discrete_sequence=["#3b82f6", "#ef4444"])

    return fig1, fig2, fig3, fig4

def eeo_tab():
    g = eeo["Gender"].value_counts()
    fig1 = px.pie(values=g.values, names=g.index, template=DARK,
                  title="County Workforce by Gender (26K employees)")

    e = eeo["Ethnicity"].value_counts()
    fig2 = px.bar(x=e.values, y=e.index, orientation="h", template=DARK,
                  title="Workforce by Ethnicity",
                  labels={"x": "Count", "y": ""})
    fig2.update_layout(yaxis=dict(autorange="reversed"))

    dept_col = [c for c in eeo.columns if "Department" in c][0]
    d = eeo[dept_col].value_counts().head(15)
    fig3 = px.bar(x=d.values, y=d.index, orientation="h", template=DARK,
                  title="Top 15 Departments by Headcount",
                  labels={"x": "Count", "y": ""})
    fig3.update_layout(yaxis=dict(autorange="reversed"), height=500)

    top_depts = eeo[dept_col].value_counts().head(8).index
    sub = eeo[eeo[dept_col].isin(top_depts)]
    fig4 = px.histogram(sub, y=dept_col, color="Ethnicity", template=DARK,
                        title="Ethnicity Breakdown — Top 8 Departments",
                        barmode="stack", height=500)

    return fig1, fig2, fig3, fig4

def photos_tab():
    dept = photos["Department"].value_counts().head(15)
    fig1 = px.bar(x=dept.values, y=dept.index, orientation="h", template=DARK,
                  title="Photos by Department",
                  labels={"x": "Count", "y": ""})
    fig1.update_layout(yaxis=dict(autorange="reversed"))

    color = photos["Color"].value_counts()
    fig2 = px.pie(values=color.values, names=color.index, template=DARK,
                  title="Color vs B&W Photos")

    return fig1, fig2

# Build Gradio UI
print("Building UI...")
with gr.Blocks(title="SCC Data Explorer") as app:
    gr.Markdown("# Santa Clara County Data Explorer\n### 6 datasets | NVIDIA DGX Spark (DELL-31)")

    with gr.Tab("1. Data Analysis"):
        gr.Markdown("""
## Step 1: Data Analysis

### What We Have
6 datasets from Santa Clara County — all public records, all siloed by department. Together they paint a picture no single department can see.

---

### 1. Crime Reports — 259,660 incidents (Dec 2019 – Mar 2026)

**What's in it:** Every incident reported to the Santa Clara County Sheriff's Office over ~6 years. Each record includes a case number, timestamp, address (block-level), incident description, and classification at two levels — a broad parent category (56 types) and a specific incident type (325 types).

**How it's currently used:** Reactive record-keeping. Dispatchers log calls, analysts produce monthly CompStat reports, and the data feeds public transparency portals. Resource allocation decisions (patrol routes, staffing) are made from quarterly trend summaries.

**Key insights:**
- **2020 was an anomaly** — 108K incidents (nearly 2x any other year), likely reflecting pandemic-era reporting patterns
- **"Other" dominates** at 92K incidents (35%) — a classification catch-all that masks real patterns
- **Community Policing is #2** (51K, 20%) — these aren't crimes but proactive engagement, inflating the count
- **Disorder (34K) and Alarm (19K)** are the real high-volume categories
- The top specific incident type is "DISTURBANCE" (21K) — more than Theft (9K) and Assault (5K) combined
- **No coordinates in the data** — only block-level addresses, limiting spatial analysis

---

### 2. Food Businesses — 8,588 establishments

**What's in it:** Every food-serving business registered with the SCC Dept of Environmental Health. Includes name, address, city, lat/lon coordinates, and phone number. Covers restaurants, food trucks, cafeterias, grocery delis — anything that serves food.

**How it's currently used:** The DEH maintains this as its master registry. Inspectors are assigned routes based on geography and schedule. The public can look up any restaurant's inspection history.

**Key insights:**
- **San Jose dominates** with 3,921 businesses (46%) — expected as the county seat and largest city
- **23 cities represented** — from Palo Alto (423) to tiny unincorporated areas
- Every business has geocoordinates — this is the **only dataset with precise lat/lon**, making it the geographic anchor for any map-based analysis

---

### 3. Food Inspections — 21,895 inspections (Mar 2024 – Mar 2026)

**What's in it:** Every health inspection conducted in the last 2 years. Each record links to a business, includes a date, score, result (Green/Yellow/Red), inspection type, and inspector comments.

**How it's currently used:** Inspectors visit, score, and log. Green = pass, Yellow = conditional pass (minor issues), Red = fail (significant hazards). Failed businesses get a follow-up. Results are public.

**Key insights:**
- **90% pass (Green)**, 6% conditional (Yellow), 4% fail (Red)
- **161 businesses have failed 2+ times** — repeat offenders that the current system doesn't prioritize differently
- **87% are routine inspections**, 12% follow-ups, <1% risk factor inspections
- **San Jose accounts for 52% of Red inspections** (419 of 800) — disproportionate even to its 46% share of businesses
- Milpitas has a surprisingly high Red rate relative to its size

---

### 4. Food Violations — 64,364 violations

**What's in it:** Every individual violation cited during an inspection. Links to an inspection ID and includes a description, code, critical flag, and inspector comments. One inspection can have multiple violations.

**How it's currently used:** Violations are cited during inspections and documented. Critical violations require immediate correction. The data feeds the inspection score.

**Key insights:**
- **86% non-critical, 14% critical** (9,255 critical violations)
- **Top violation: improper hot/cold holding temperatures** (5,326) — the single most common food safety failure
- **Inadequate handwash facilities** (4,822) and **equipment condition** (4,042) round out the top 3
- 49 unique violation types — a manageable taxonomy for pattern analysis
- The most dangerous violations (temperature, handwashing) are also the most common — a systemic issue, not isolated incidents

---

### 5. County Employees (EEO) — 26,042 employees (point-in-time snapshot)

**What's in it:** Every current Santa Clara County employee broken down by gender, ethnicity, EEO job category, department, employment status, and age. This is a compliance dataset — required for federal EEO-4 reporting.

**How it's currently used:** Annual reporting to the federal government. HR and DEI teams use it for benchmarking and hiring target-setting. Mostly static analysis — "here's where we are."

**Key insights:**
- **Santa Clara Valley Healthcare is 47% of the entire county workforce** (12,357 people) — the county is essentially a healthcare operation with other departments attached
- **65% female, 35% male** — driven by healthcare's gender composition
- **Asian (34%), Hispanic/Latino (24%), White (17%)** — reflects Silicon Valley demographics but with notable gaps in leadership representation
- **70% are permanent classified employees** — stable workforce, low turnover signal
- 46 departments total — but the top 8 account for 75% of all employees

---

### 6. County Photographers' Collection — 4,541 historical photos (1950–1993)

**What's in it:** A catalog of the county's official photographic archive spanning 43 years. Each record includes an order number, date, subject description, color/B&W indicator, media counts (negatives, prints, slides), and the requesting department.

**How it's currently used:** Archival reference. Researchers and media request historical photos, and archivists search this catalog. The photos themselves are physical media — this is just the metadata.

**Key insights:**
- **Peak activity in the 1970s** (1,981 photos) — corresponds to major county infrastructure expansion
- **1960s were second** (1,541) — likely documenting the suburbanization of Santa Clara Valley
- **Office of the County Executive** commissioned the most photos (1,290) — official documentation of county milestones
- **Public Works (563) and School Department (235)** are the next top requesters — infrastructure and education documentation
- The collection is **metadata only** — no image files, but the subject descriptions contain rich narrative information about county history

---

## Cross-Dataset Connections

These 6 datasets are **currently siloed** — each serves one department for one purpose. But they share geography (Santa Clara County), time (overlapping years), and institutions (county departments). The unexplored connections:

- **Crime + Food**: 5,757 food businesses sit on streets with crime reports. Do high-crime corridors have worse food safety outcomes?
- **EEO + Food**: Does the DEH's workforce composition affect inspection patterns across diverse neighborhoods?
- **Crime + EEO**: Do Sheriff's Office demographics correlate with community policing patterns?
- **Photos + All**: The 1950-1993 photo archive documents how today's high-crime or food-desert neighborhoods were shaped by historical land use decisions

""")

    with gr.Tab("2. Three Tracks"):
        gr.Markdown("""
## Step 2: Review the Three Tracks

Each track asks a fundamentally different question. The data supports all three — the choice is about which story you want to tell and which agent architecture is most compelling.

---

### Track 1: Human Impact
*"Who is falling through the cracks, and can AI catch them?"*

| Objective | What We're Solving | Datasets | Impact Metric |
|-----------|-------------------|----------|---------------|
| **Predictive food safety triage** | 161 restaurants have failed 2+ inspections. The system treats all businesses equally instead of prioritizing repeat offenders | Food (3 tables) | Critical violations caught early; foodborne illness prevented |
| **Crime pattern intelligence** | 35% of incidents classified as "Other" — a black hole hiding real patterns. No predictive tools for dispatchers | Crime | Incidents reclassified; response time improved |
| **Cross-silo risk detection** | Nobody connects food safety failures to crime patterns. High-crime + low-food-safety areas = compounding risk | Crime + Food + Census + CDC | Neighborhoods where multiple systems fail simultaneously |
| **Workforce-service equity audit** | Does the county serve diverse communities equitably? Healthcare is 47% of workforce but gaps exist | EEO + Crime + Food | Gaps between workforce composition and community needs |

**Strongest data fit.** 3 relational food tables + 260K crime records + CDC health outcomes = deep, cross-domain analysis.

---

### Track 2: Eco Impact
*"Where is the county wasting resources, and can AI optimize them?"*

| Objective | What We're Solving | Datasets | Impact Metric |
|-----------|-------------------|----------|---------------|
| **Inspection route optimization** | Inspectors visit 8,588 businesses on fixed schedules regardless of risk | Food (3) + geo | Vehicle miles saved, emissions reduced |
| **Food waste reduction** | Red inspections = food destroyed. 800 Reds in 2 years. Predict and prevent instead | Food (3) | Tons of food saved from unnecessary destruction |
| **Traffic incident congestion** | 14,710 traffic incidents + 10,995 vehicle stops create congestion patterns | Crime | Hours of congestion avoided, CO2 from idling |
| **Resource allocation efficiency** | 26K employees across 46 departments. Are resources where impact is highest? | EEO + Crime + Food | Cost per outcome improvement |

**Viable but derivative.** The optimization angle works but may feel like a feature of the Human Impact project rather than its own story.

---

### Track 3: Culture Impact
*"What stories are hidden in this data, and can AI tell them?"*

| Objective | What We're Solving | Datasets | Impact Metric |
|-----------|-------------------|----------|---------------|
| **Historical archive intelligence** | 4,541 photos (1950-1993) in a catalog nobody searches | Photos | Stories surfaced, queries served |
| **Cultural food heritage mapper** | 8,588 food businesses = a living cultural map. Trace culinary traditions | Food Businesses | Cultural corridors identified |
| **Neighborhood evolution storyteller** | Connect 1950s photos to modern data — how did neighborhoods transform? | Photos + Food + Crime | Communities connected to their history |
| **Civic memory agent** | No institutional memory connecting dots across decades | All datasets | Cross-era insights surfaced |

**Most creative but thinnest data.** Photo dataset is metadata-only (no images). Would need strong narrative from Nemotron to compensate.

---

### Track Comparison Matrix

| Factor | Human Impact | Eco Impact | Culture Impact |
|--------|-------------|-----------|---------------|
| Data depth | 5/5 | 3/5 | 2/5 |
| Agent innovation potential | 5/5 | 3/5 | 4/5 |
| Demo wow factor | 4/5 | 3/5 | 4/5 |
| Competition (other teams) | High | Medium | Low |
| OpenClaw fit | 5/5 | 3/5 | 4/5 |
| Supplemental data boost | 5/5 (Census+CDC) | 3/5 | 2/5 |
""")

    with gr.Tab("3. Supplemental Data"):
        gr.Markdown("""
## Step 3: Supplemental Data

### Acquired

| Source | File | Records | Key Fields | Status |
|--------|------|---------|------------|--------|
| **US Census ACS 2022** | census_income.csv | 62 zip codes | Median household income, poverty population, total population | Ready |
| **CDC PLACES 2023** | cdc_places.csv | 16,320 rows (408 tracts x 40 measures) | Diabetes, obesity, food insecurity, mental health, and 36 more health outcomes by census tract | Ready |

### CDC PLACES Highlights (Santa Clara County averages)

| Measure | Avg % | Why It Matters |
|---------|-------|---------------|
| Food Insecurity | 12.7% | Direct link to where people eat — and food safety risk exposure |
| Diabetes | 10.3% | Diet-related — correlates with food access and quality |
| Obesity | 22.7% | Neighborhood food environment indicator |
| Depression | 18.4% | Mental health burden by neighborhood |
| Frequent Mental Distress | 14.2% | Stress indicator — correlates with crime exposure |
| High Blood Pressure | 26.8% | Diet and stress related |
| Loneliness | 38.5% | Social isolation — community engagement signal |
| Food Stamps | 9.6% | Economic vulnerability marker |

### Available on SCC Open Data Portal (data.sccgov.org)

**Tier 1 — High value, quick to pull:**

| Dataset | API ID | What It Adds |
|---------|--------|-------------|
| Medical Examiner-Coroner | s3fb-yrjp | Geocoded deaths since 2018 — drug, homicide, firearm, heat |
| Population by Census Tract | 8xqv-zjjk | Per-capita denominators for all rates |
| Supervisorial Districts | e8s8-f89v | Political boundaries for policy-relevant aggregation |
| Flood Hazard Zones | sa78-t43w | Environmental risk overlay |

**Tier 2 — Strong complementary value:**

| Dataset | What It Adds |
|---------|-------------|
| COVID-19 by Census Tract | Pandemic impact overlay — did inspection gaps during COVID cause lasting food safety issues? |
| Parcels + Zoning + General Plan | Spatial backbone — land use context for every location |
| Homelessness Point-in-Time | Vulnerability overlay with crime and food access |
| Permit Processing Time | Development activity — new restaurants in underserved areas? |
| County Archives Catalog | Enriches photographers' collection |

### Cross-Dataset Power Combinations

The real value is in joining these:

```
Food Violations (by business lat/lon)
  + Census Income (by zip)
  + CDC Health Outcomes (by tract)
  + Crime Reports (by street)
  = "Which neighborhoods have the most dangerous restaurants,
     the lowest incomes, the worst health outcomes, AND the
     highest crime — and nobody is connecting these dots?"
```

This is the story that wins Human Impact.
""")

    with gr.Tab("4. Brainstorm"):
        gr.Markdown("""
## Step 4: Brainstorm & Decision

---

### 4a. How This Data Is Currently Used (and how it could be used differently)

| Dataset | Current Use | Current Owner | What's Missing |
|---------|------------|--------------|----------------|
| **Crime Reports** | Reactive logging. CompStat reports. Transparency portal. | Sheriff's Office | No prediction, no cross-department insight, no community-facing tools |
| **Food Businesses** | Master registry for inspector assignments | Dept of Environmental Health | Static list — no risk scoring, no neighborhood context |
| **Food Inspections** | Schedule-based visits, score, publish | DEH Inspectors | No prioritization by risk. Safe restaurants get same cadence as dangerous ones |
| **Food Violations** | Cited during inspections, feed the score | DEH | Violations treated individually — nobody sees systemic patterns across businesses |
| **EEO Employees** | Annual federal compliance reports (EEO-4) | County HR | Snapshot only. Never cross-referenced with service delivery or community outcomes |
| **Photos Collection** | Archival catalog for researcher requests | County Archives | No discovery layer. No connection to modern geography or cultural context |

**Key insight: None of these datasets are used PROACTIVELY. They're all backward-looking compliance tools.**

#### Alternative Uses (aligned with tracks)

**Human Impact — Don't improve the inspection process. Build the thing that doesn't exist:**
- A **community health intelligence agent** that fuses food safety, crime, income, and health data to identify neighborhoods where multiple systems are failing simultaneously
- Not "better inspections" but "which communities need intervention across ALL dimensions?"
- The agent doesn't replace an inspector — it alerts a **county health officer** to systemic failures no single department can see

**Eco Impact — Don't optimize routes. Quantify the environmental cost of the status quo:**
- An agent that calculates the **carbon and waste footprint** of the current inspection system vs. a risk-based one
- "The county drives X unnecessary miles per year inspecting safe restaurants while dangerous ones go unvisited"

**Culture Impact — Don't build a photo search. Build a neighborhood narrator:**
- An agent that tells the **story of any address** by pulling from every dataset: what was here in 1960 (photos), what's here now (food, crime), who lives here (census), how healthy are they (CDC)
- Not a tool — a storyteller. "This block was farmland in 1955, became a strip mall in 1975, now has 3 restaurants with critical violations and is in a food-insecure census tract"

---

### 4b. Decision Framework

#### Data Availability Score

| Project Concept | Primary Data | Supplemental | Geo-Joinable? | Score |
|----------------|-------------|-------------|---------------|-------|
| Community Health Intelligence (Human) | Food (3 tables) + Crime (260K) + EEO (26K) | Census + CDC (408 tracts) | Yes (food has lat/lon, census by zip/tract) | 5/5 |
| Environmental Cost Calculator (Eco) | Food (3 tables, with lat/lon) | Census (for population density) | Yes | 3/5 |
| Neighborhood Narrator (Culture) | Photos (4.5K) + Food + Crime | Census | Partial (photos have no geo) | 2/5 |

#### Impact Score (from judge's perspective)

| Project Concept | "So What?" Clarity | Quantifiable? | Emotional Response | Novel? |
|----------------|-------------------|--------------|-------------------|--------|
| Community Health Intelligence | "12.7% food insecurity in tracts with 2x critical violations" | Yes — lives, dollars, health outcomes | Fear + urgency | Moderate — cross-silo is the innovation |
| Environmental Cost Calculator | "X tons of food wasted, Y miles driven unnecessarily" | Yes — CO2, miles, dollars | Frustration | Low — optimization is expected |
| Neighborhood Narrator | "This block went from farmland to food desert in 50 years" | Partially — qualitative | Surprise + empathy | High — nobody does this |

#### Judge's Perspective (from EXPERTISE-LAYERS.md)

Judges see 15-30 demos in 2 hours. They are tired, overstimulated, and making fast gut decisions.

**What wins:**
- "We discovered that {specific shocking insight} in this data"
- One perfect visualization > five mediocre ones
- A live demo that makes the audience gasp or laugh
- A clear villain (the problem) and hero (your tool)
- Confidence — even if 70% done, present it like it's exactly what you intended

**What loses:**
- "We built a dashboard" (everyone builds a dashboard)
- "We used AI to analyze data" (everyone does this)
- Feature lists that bore people
- Apologizing for bugs

**OpenClaw prize judges specifically want:**
- Agent orchestration, not a wrapper
- Show the agent communication log
- Agents making DECISIONS (routing, prioritization), not just executing sequentially
- Different models for different agents

#### The Thinking Framework (from hackathon prep docs)

**The "Who Suffers?" Test:**
> Who is currently HARMED because this data isn't being used well?
> What decision is someone making BLIND right now that this data could illuminate?
> If I showed this to a mayor — what would make them say "I needed this yesterday"?

**The Inversion Test:**
> What's the OBVIOUS project everyone will build? → "A dashboard" or "A chatbot that answers questions about crime/food data"
> What's the PERPENDICULAR angle? → An agent system that discovers what nobody is looking for

**The Pitch Sentence:**
> [WHO] currently can't [WHAT] because [WHY]. We built [PRODUCT] that [HOW], reducing [BAD THING] by [METRIC].

**Feasibility Gate:**

| Question | Community Health Intel | Env Cost Calc | Neighborhood Narrator |
|----------|----------------------|--------------|----------------------|
| Working demo in 4 hours? | Yes | Yes | Uncertain (photo data thin) |
| Uses 2+ models? | Yes (Nemotron 70B + Nano) | Yes | Yes |
| Multi-agent OpenClaw pipeline? | Yes (Analyst + Risk Scorer + Reporter + Advisor) | Partial | Yes (Researcher + Narrator) |
| Visually compelling 3-min demo? | Yes (maps + risk scores + agent debate) | Moderate | Yes if narrative is strong |
| One-sentence impact? | Yes | Yes | Harder to quantify |

---

### Decision Matrix Summary

| | Community Health Intelligence | Environmental Cost Calculator | Neighborhood Narrator |
|---|---|---|---|
| **Data** | 5/5 | 3/5 | 2/5 |
| **Impact** | 5/5 | 3/5 | 4/5 |
| **Judge Appeal** | 4/5 | 2/5 | 4/5 |
| **Agent Innovation** | 5/5 | 2/5 | 4/5 |
| **Feasibility** | 5/5 | 4/5 | 3/5 |
| **OpenClaw Prize** | 5/5 | 2/5 | 3/5 |
| **TOTAL** | **29/30** | **16/30** | **20/30** |

---

## 4c. Beyond Analysis — Actionable Agent Concepts

The ideas above are data analysis. Hackathon judges want agents that **act**, not just report. Here are concepts where the agent IS the product:

### Digital Agents (OpenClaw)

#### 1. "SafeGuard" — Proactive Restaurant Coach Agent
The agent doesn't wait for inspections. It autonomously:
- **Reaches out** to restaurant owners before their next inspection: "Based on your history, you'll likely be cited for temperature control. Here's exactly what to fix."
- **Generates a customized prep checklist** from their specific violation history
- **Follows up** after inspection: "You passed!" or "You failed on X — here's a remediation plan"
- **Escalates** to health officers if a business ignores repeated coaching

| Agent | Model | Role |
|-------|-------|------|
| Coach Agent | Nemotron 70B | Generates personalized guidance for restaurant owners |
| Analyst Agent | Nemotron 70B | Builds risk profiles from violation + inspection + crime + census data |
| Scheduler Agent | Nemotron Nano | Decides who to contact and when (fast triage) |
| Escalation Agent | Nemotron 70B | Routes to human officials when agent coaching fails |

**Demo moment:** Show the agent generating a real coaching message for an actual restaurant from the data, with its full violation history and neighborhood context.

---

#### 2. "CivicPulse" — Cross-Department Alert System
An autonomous monitoring agent that:
- **Monitors** all datasets for emerging patterns
- **Detects** when a neighborhood crosses a risk threshold (3+ new critical violations + crime spike + high food insecurity in same tract)
- **Drafts and sends alerts** to the right county official: "Attention: East San Jose District 5 is showing compounding risk. Here's the brief."
- **Tracks** whether action was taken and re-escalates if not

| Agent | Model | Role |
|-------|-------|------|
| Sentinel Agent | Nemotron Nano | Continuous monitoring, fast anomaly detection |
| Analyst Agent | Nemotron 70B | Deep assessment of flagged patterns, severity scoring |
| Router Agent | Nemotron Nano | Decides which department/official gets notified |
| Messenger Agent | Nemotron 70B | Generates context-rich, actionable alert briefs |

**Demo moment:** Simulate a real-time data feed, watch the agents detect a pattern, debate severity, and generate an alert — all visible in the agent communication log.

---

#### 3. "StreetSmart" — Resident-Facing Neighborhood Agent
A conversational agent any resident can interact with:
- *"Is it safe to eat at Pho Palace?"* → pulls inspection history, violations, gives plain-language advice
- *"What's going on in my neighborhood?"* → synthesizes crime trends, food safety, health data for their zip code
- *"I think the restaurant on Main St has rats"* → logs report, cross-references existing violations, routes to DEH
- *"Why is my neighborhood getting worse?"* → pulls historical photos, census changes, crime trends

| Agent | Model | Role |
|-------|-------|------|
| Intake Agent | Nemotron Nano | Understands the question, classifies intent (fast) |
| Research Agent | Nemotron 70B | Queries all datasets, joins cross-silo data |
| Narrative Agent | Nemotron 70B | Generates human-friendly, empathetic answers |
| Action Agent | Nemotron Nano | Files reports, sends referrals, triggers follow-ups |

**Demo moment:** Judge asks a question live. Agent responds with a fused answer drawing from 6+ datasets. Immediate wow factor.

---

### Physical / IoT Agent Concepts

#### 4. "InspectAR" — Inspector Field Companion
An agent on the inspector's phone/tablet:
- **Briefs** before each visit: violation history, risk score, what to look for, neighborhood context
- **Auto-generates** the inspection report from notes
- **Suggests next stop** based on proximity + risk, not schedule
- **Flags** if inspector is spending too long at a low-risk location

#### 5. "WatchTower" — IoT Kitchen Monitor (simulated)
Agent receives simulated temperature sensor data from restaurant refrigerators:
- Detects when food enters the danger zone (41-135F) — the **#1 critical violation** (3,420 cases, 37% of all critical)
- Alerts restaurant owner AND health department in real-time
- *"We prevented the violation before the inspector even arrived"*
- Demo with simulated sensor data stream + Nemotron reasoning about the alert

---

### Agent Concept Comparison

| Concept | Actionability | Demo Quality | OpenClaw Fit | Build in 4hrs? | Innovation |
|---------|-------------|-------------|-------------|---------------|-----------|
| **SafeGuard** (Coach) | 5/5 — directly contacts businesses | 4/5 — show real coaching message | 5/5 — 4 distinct agents | Yes | 4/5 |
| **CivicPulse** (Alerts) | 5/5 — generates and sends alerts | 5/5 — watch agents detect + debate | 5/5 — 4 agents with decision-making | Yes | 5/5 |
| **StreetSmart** (Resident) | 4/5 — answers questions, files reports | 5/5 — live Q&A with judge | 4/5 — 4 agents in conversational flow | Yes | 4/5 |
| **InspectAR** (Field) | 4/5 — briefs inspectors | 3/5 — harder to demo without mobile | 3/5 — mostly single agent | Yes | 3/5 |
| **WatchTower** (IoT) | 5/5 — real-time prevention | 4/5 — simulated but compelling | 3/5 — event-driven, fewer agents | Tight | 5/5 |

---

### Recommendation

**Top picks (pick one or combine):**

1. **CivicPulse** — Most innovative agent architecture. Agents that monitor, detect, debate, and alert. The demo shows the full agent lifecycle. Strongest OpenClaw prize play.

2. **StreetSmart** — Best live demo. Judge asks a question, gets a fused multi-dataset answer. Most accessible to non-technical judges.

3. **SafeGuard** — Most directly impactful. The agent literally prevents food safety violations. Strongest "who uses this tomorrow" answer.

**The hybrid play:** Build CivicPulse as the backend (multi-agent detection + alerting) with a StreetSmart conversational interface on top. The agent system monitors AND responds to questions. This gives you both the autonomous agent story AND the live demo wow factor.

**The pitch:** *"Today, Santa Clara County's food safety, crime, health, and workforce data sit in separate databases — nobody connects them. We built an AI agent system that autonomously monitors all of them, detects when a neighborhood is failing across multiple dimensions, and takes action: alerting officials, coaching restaurant owners, and answering resident questions. Four specialized agents, each with a different model, orchestrated through OpenClaw — all running on a single GB10."*
""")

    with gr.Tab("5. Design & Pressure Test"):
        gr.Markdown("""
## Step 5: Design — Community Health Intelligence Agent

### Selected Direction: Human Impact Track + CivicPulse/StreetSmart Hybrid

---

## The Hard Question: What Impact Does This Actually Create?

Overlaying datasets is interesting. It's not impactful. **Impact = someone does something different tomorrow because this agent exists.**

Let's pressure test by asking: **What specific action does each agent output trigger?**

---

### Real Data: The Compounding Risk is Real

We ran the numbers. Here's what the data actually shows:

#### Ground Zero: ZIP 95122 (East San Jose)
- **341 restaurants** with **100 Red (fail) inspections** and **683 critical violations**
- Poverty rate: 10.5% | Median income: $94,924
- 4,187 crime incidents on food business streets
- **4 of the top 15 repeat-offender restaurants are in this single zip code**
- Repeat offenders include: Banh Mi Oven (9 Red inspections, 23 critical violations), Tomi Sushi (5 Red, 11 critical), Los Arcos (2 Red, 14 critical), Banh Cuon Ong Ta (4 Red, 11 critical)

#### The Danger Corridor: E Santa Clara St (Downtown San Jose)
- 46 restaurants | **22 Red inspections** | 103 critical violations | 1,421 crime incidents — all on one street

#### ZIP 95113 (Downtown San Jose)
- 18.8% poverty rate — the highest of any zip with significant food businesses
- 359 critical violations | 41 Red inspections | 4,264 crime incidents

#### The Health Gap
Food-insecure census tracts (960,780 residents) vs food-secure tracts:

| Health Outcome | Food-Insecure Tracts | Food-Secure Tracts | Gap |
|----------------|---------------------|-------------------|-----|
| **Diabetes** | 11.6% | 9.1% | **+28% higher** |
| **Obesity** | 25.0% | 20.4% | **+23% higher** |
| **Mental Distress** | 15.9% | 12.5% | **+27% higher** |
| **Food Stamps** | 13.9% | 5.3% | **+160% higher** |

**The people who can least afford to get sick are eating at the most dangerous restaurants in the highest-crime neighborhoods. And nobody in county government is connecting these dots.**

---

### Pressure Test #1: "So what?" Chain (with real examples)

Every output must survive 3 rounds of "so what?"

| Agent Output (real data) | So What? (1) | So What? (2) | So What? (3) — The Action |
|-------------|-------------|-------------|--------------------------|
| "ZIP 95122 has 100 Red inspections, 683 critical violations, 10.5% poverty, and 4,187 crime incidents on food streets" | East San Jose is failing across food safety, crime, AND economic indicators simultaneously | No single department sees this — DEH sees violations, Sheriff sees crime, Public Health sees diabetes. Nobody sees all three. | **County Health Officer convenes a cross-department intervention for ZIP 95122 specifically** |
| "Banh Mi Oven has failed 9 inspections with 23 critical violations in a 10.5% poverty zip code" | This restaurant is a persistent public health threat to a vulnerable community | The current system just schedules another inspection. 9 failures and they're still operating the same way. | **Agent generates a remediation plan for the owner AND escalates to DEH supervisor: "This business needs supervised corrective action, not another routine follow-up"** |
| "E Santa Clara St: 22 Red inspections + 1,421 crime incidents across 46 restaurants" | This single street has more food safety failures than most entire cities in the county | The combination of food safety failure + crime creates a neighborhood where residents face compounding daily risk | **Community development team targets E Santa Clara St for combined code enforcement + business support program** |
| "Food-insecure tracts have 28% more diabetes and 27% more mental distress than food-secure tracts" | The health equity gap is measurable and directly linked to food environment | 960,780 people live in these tracts — nearly half the county | **Public health launches targeted food safety + nutrition campaign in the 204 highest-risk tracts** |

### Pressure Test #2: Who Receives the Agent's Output?

An agent that produces a report nobody reads creates zero impact. **Every output needs a named recipient and a clear ask.**

| Recipient | What They Get | What They Do With It | Why They Care |
|-----------|--------------|---------------------|---------------|
| **County Health Officer** | Weekly "Neighborhood Risk Brief" — top 5 tracts where food safety + crime + health indicators are compounding | Convenes cross-department meetings, allocates intervention resources | They're accountable for population health outcomes but currently blind to cross-silo patterns |
| **DEH Inspection Supervisor** | Daily prioritized inspection queue ranked by community risk, not schedule | Reassigns inspectors from low-risk to high-risk businesses | They have limited inspectors — sending them to safe restaurants wastes public resources |
| **Restaurant Owner** | Personalized coaching: "Your 3 most likely violations, with step-by-step fixes" | Fixes problems before the inspector arrives | They want to pass — most failures are from ignorance, not negligence |
| **County Supervisor (elected)** | District-level scorecard: "Your district has X% of the county's compounding risk neighborhoods" | Asks questions in board meetings, directs funding | Political pressure = fastest path to systemic change |
| **Community Resident** | Plain-language neighborhood profile: "Here's what's happening on your block" | Makes informed choices, reports concerns, engages civic process | They live there. They deserve to know. |

### Pressure Test #3: What's the Counterfactual?

**Without this agent, what happens?**
- Inspectors visit safe restaurants on schedule while dangerous ones serving food-insecure populations go unvisited
- Nobody notices that the same 5 census tracts keep showing up across crime, food safety, and health datasets
- A restaurant owner who would have fixed their violations if warned fails their inspection, gets shut down, throws away $10K in food, and the neighborhood loses a food source
- County departments each produce separate reports about the same neighborhoods and never connect the dots
- Elected officials make resource allocation decisions based on department-by-department data instead of integrated community risk

**With this agent:**
- Inspectors go where the risk is highest AND the community impact is greatest
- Cross-silo patterns surface automatically — no human could monitor 6 datasets simultaneously
- Restaurant owners get coached before they fail, reducing closures and food waste
- Officials see integrated neighborhood health, not department silos

---

## Architecture: The Agent System

```
                    ┌─────────────────────────────┐
                    │      OpenClaw Orchestrator    │
                    └──────────┬──────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │  SENTINEL     │   │  ANALYST     │   │  ADVISOR     │
   │  (Nano)       │   │  (70B)       │   │  (70B)       │
   │               │   │              │   │              │
   │  Monitors all │   │  Deep-dives  │   │  Generates   │
   │  datasets for │   │  flagged     │   │  actionable  │
   │  anomalies &  │──▶│  patterns.   │──▶│  outputs for │
   │  threshold    │   │  Joins cross-│   │  each        │
   │  crossings.   │   │  silo data.  │   │  recipient.  │
   │  Fast triage. │   │  Scores      │   │  Coaching,   │
   │               │   │  severity.   │   │  alerts,     │
   └──────────────┘   └──────────────┘   │  briefs.     │
                                          └──────┬───────┘
                                                 │
                                          ┌──────▼───────┐
                                          │  MESSENGER   │
                                          │  (Nano)      │
                                          │              │
                                          │  Routes each │
                                          │  output to   │
                                          │  the right   │
                                          │  recipient.  │
                                          │  Tracks      │
                                          │  delivery &  │
                                          │  follow-up.  │
                                          └──────────────┘
```

### Agent Detail

| Agent | Model | Input | Output | Key Decision |
|-------|-------|-------|--------|-------------|
| **Sentinel** | Nemotron Nano | All 6 datasets + Census + CDC | Flagged patterns with preliminary risk score | "Is this worth investigating?" (fast yes/no) |
| **Analyst** | Nemotron 70B | Flagged patterns + full cross-silo data | Severity assessment, root cause hypothesis, affected population size | "How bad is this, and why?" (deep reasoning) |
| **Advisor** | Nemotron 70B | Analyst findings + recipient context | Tailored action plans: coaching for owners, briefs for officials, profiles for residents | "What should each person DO about this?" |
| **Messenger** | Nemotron Nano | Advisor outputs + routing rules | Formatted messages delivered to recipients | "Who gets this, and in what format?" (fast routing) |

### The Key Innovation: Agents Make Decisions

This isn't a sequential pipeline. Agents make real decisions:

1. **Sentinel DECIDES** what's worth flagging (not everything is an alert — that's noise)
2. **Analyst DECIDES** severity and which datasets to cross-reference (not always all of them)
3. **Advisor DECIDES** what action to recommend based on recipient role (a health officer gets strategy; a restaurant owner gets a checklist)
4. **Messenger DECIDES** urgency and channel (critical = immediate alert; moderate = weekly digest)

---

## The Demo Flow (3 minutes)

**[0:00-0:20] Hook:**
"37% of all critical food safety violations in Santa Clara County are temperature control failures. The county inspects 8,600 restaurants — but the ones in food-insecure neighborhoods with high crime get inspected on the same schedule as Michelin-starred restaurants in Palo Alto. Nobody connects these dots."

**[0:20-0:50] Problem:**
"Today, the Sheriff's Office, Environmental Health, and Public Health each have data about the same neighborhoods — stored in separate systems, analyzed by separate teams, reported to separate boards. When a census tract is failing across food safety, crime, AND health outcomes, nobody knows."

**[0:50-1:40] Solution + Live Demo:**
"We built a 4-agent system running entirely on this GB10. Watch:"
- Sentinel scans data → flags East San Jose tract with 3x critical violations + rising crime + 15% food insecurity
- Analyst cross-references → "This tract has the highest compounding risk in the county. 12,000 residents affected."
- Advisor generates outputs → coaching message for the worst restaurant, alert brief for the Health Officer, neighborhood profile for residents
- Show the agent communication log — agents reasoning, deciding, routing

**[1:40-2:20] Impact:**
"Without this agent, that tract stays invisible. With it, the Health Officer sees the pattern Monday morning. The inspector visits Tuesday. The restaurant owner gets coaching Wednesday. By Friday, the neighborhood is safer."

**[2:20-3:00] Close:**
"Temperature control is the #1 violation because nobody tells restaurant owners how to fix it until after they've failed. Our agent tells them before. Four agents, four models, one GB10 — no cloud, no data leaving the building. The neighborhoods falling through every crack at once finally have someone watching."

---

## Build Plan (remaining time)

| Phase | Time | What |
|-------|------|------|
| Data pipeline | 30 min | Join all datasets by geography (zip/tract/street). Create unified risk scores per tract. |
| Agent framework | 45 min | OpenClaw 4-agent system with Nemotron 70B + Nano |
| Sentinel logic | 20 min | Threshold detection + anomaly flagging |
| Analyst prompts | 20 min | Cross-silo reasoning prompts |
| Advisor outputs | 30 min | Templates for each recipient type |
| Gradio UI | 30 min | Map + agent log + output panels |
| Polish + demo prep | 30 min | Run 3 times, pre-compute wow examples |

**Total: ~3.5 hours. We have ~4 hours left. This is buildable.**

---

## Who Uses CivicPulse and How?

The agent system serves 5 distinct users. Each interacts differently and gets different outputs from the same underlying intelligence.

### User 1: County Health Officer
**Role:** Senior public health official responsible for population-level health outcomes.

**Current pain:** Gets separate reports from DEH (food safety), Sheriff (crime), Public Health (health outcomes), HR (workforce). No one synthesizes them. She has to manually connect dots across 4 departments and often doesn't.

**How CivicPulse helps:**
- **Monday morning:** Opens the dashboard. The Sentinel has flagged 3 neighborhoods that crossed compounding risk thresholds over the weekend.
- **Reads** the Analyst's deep-dive for each: what's happening, how severe, who's affected.
- **Clicks** "Generate Intervention Plan" — the Advisor produces a cross-department action brief.
- **Forwards** it to DEH, Sheriff, and Public Health leads with specific asks.

**OpenClaw flow:** Sentinel (detected the pattern) → Analyst (scored severity, identified root causes) → Advisor (generated the brief tailored to a health officer's needs) → Messenger (formatted for email, tracked delivery)

---

### User 2: DEH Inspection Supervisor
**Role:** Manages the daily inspection schedule for 15-20 field inspectors.

**Current pain:** Assigns inspections by geography and schedule — safe restaurants in Palo Alto get the same cadence as repeat offenders in East San Jose. No risk-based prioritization. Limited inspectors, wasted trips.

**How CivicPulse helps:**
- **Every morning:** Opens "Today's Priority Queue" — the system has re-ranked inspections by community risk, not schedule. Banh Mi Oven (9 Red, 23 critical, food-insecure zip) is #1.
- **Assigns** inspectors based on the queue. Each inspector gets a pre-visit brief: violation history, what to look for, neighborhood context.
- **After inspections:** Results feed back into the system — the Sentinel updates risk scores in real-time.

**OpenClaw flow:** Sentinel (monitors incoming inspection results) → Analyst (recalculates risk scores nightly) → Advisor (generates prioritized queue + inspector briefs) → Messenger (delivers to supervisor's dashboard)

---

### User 3: Restaurant Owner
**Role:** Small business owner trying to pass their next health inspection.

**Current pain:** Gets inspected, fails, fixes the problem, waits 6 months, gets inspected again. Nobody tells them what to fix BEFORE they fail. Most violations are from ignorance, not negligence — they just don't know the codes.

**How CivicPulse helps:**
- **2 weeks before inspection:** Receives a message from the Advisor agent: "Your next inspection is approaching. Based on your history, your 3 most likely violations are: (1) Hot holding temps — check your reach-in cooler calibration. (2) Handwash sink — ensure soap and paper towels are stocked. (3) Time marking — label all TPHC items with prep time."
- **Can reply** with questions — the agent responds with specific, actionable guidance.
- **After inspection:** Gets a follow-up: "You passed! Here's what kept you clean" or "You failed on X — here's a step-by-step remediation plan."

**OpenClaw flow:** Analyst (built the risk profile from violation history + neighborhood data) → Advisor (generated personalized coaching in plain language) → Messenger (delivered via email/SMS, tracked whether owner opened it, scheduled follow-up)

---

### User 4: County Supervisor (Elected Official)
**Role:** Elected representative for a district. Controls funding and policy.

**Current pain:** Gets department-by-department briefings. Sees crime stats OR food safety stats OR health stats — never all three overlaid on their district. Can't make integrated resource decisions.

**How CivicPulse helps:**
- **Monthly:** Receives a "District Health Scorecard" — compounding risk trends for their district vs county average, with specific neighborhoods flagged.
- **Uses it** in board meetings to ask pointed questions: "Why does ZIP 95122 have 100 Red inspections and we're not doing anything cross-departmental about it?"
- **Directs funding** to neighborhoods where the data shows compounding risk.

**OpenClaw flow:** Analyst (aggregated all data by supervisorial district) → Advisor (generated politician-friendly scorecard with talking points) → Messenger (delivered monthly, formatted for print/PDF)

---

### User 5: Community Resident
**Role:** Lives in the neighborhood. Eats at local restaurants. Wants to know if it's safe.

**Current pain:** Can look up individual restaurant inspection scores on a county website — but can't see the neighborhood-level picture. Doesn't know that their zip code has 3x the critical violations of the county average AND higher diabetes rates AND more crime on food streets.

**How CivicPulse helps:**
- **On-demand:** Accesses a web interface. Asks "Is it safe to eat at Banh Mi Oven?" → Gets: "This restaurant has failed 9 of its last inspections. 23 critical violations. The most common issue is temperature control. We recommend choosing an alternative."
- **Asks** "What's going on in my neighborhood?" → Gets a synthesized profile: food safety, crime trends, health data, compared to county average.
- **Reports** a concern: "I saw cockroaches at the restaurant on Story Rd" → Agent logs it, cross-references with existing violations, routes to DEH if pattern matches.

**OpenClaw flow:** Intake Agent/Sentinel (understood the question, classified intent) → Analyst (queried all datasets, joined cross-silo data) → Advisor (generated plain-language, empathetic answer) → Messenger (delivered in chat UI, logged the interaction for follow-up)
""")

    with gr.Tab("6. Pitch Deck"):
        gr.Markdown("## Pitch Deck\nEmbedded below. Use arrow keys inside the frame to navigate slides. For full-screen: right-click the frame → Open in new tab.")
        pitch_path = os.path.expanduser("~/hackathon/pitch_deck.html")
        gr.HTML(f'<iframe src="/file={pitch_path}" width="100%" height="750" style="border:1px solid #1e293b; border-radius:8px; background:#0a0a0a;"></iframe>')
        gr.Markdown("""
### Slide Outline

| # | Slide | Key Message |
|---|-------|-------------|
| 1 | **Title** | CivicPulse — "The neighborhoods falling through every crack at once finally have someone watching" |
| 2 | **Problem** | 6 county datasets, zero connections between them |
| 3 | **The Data** | 260K crime + 9,255 critical violations + 26K employees + Census + CDC health + photos |
| 4 | **Ground Zero** | ZIP 95122: 100 Red inspections, 683 critical violations, real restaurant names |
| 5 | **Health Equity Gap** | +28% diabetes, +23% obesity, +160% food stamps in food-insecure tracts |
| 6 | **Danger Corridors** | E Santa Clara St: 22 Red inspections + 1,421 crime incidents on one street |
| 7 | **Solution** | 4-agent pipeline: Sentinel → Analyst → Advisor → Messenger |
| 8 | **Outputs** | Named recipients: Health Officer, Supervisor, Owner, Resident — each gets a specific action |
| 9 | **Counterfactual** | Without vs With CivicPulse — side by side |
| 10 | **Tech Stack** | GB10, Nemotron 70B + Nano, OpenClaw, on-device, no cloud |
| 11 | **Close** | "161 restaurants have failed 2+ inspections" — four agents, six datasets, one GB10, zero blind spots |
""")

    with gr.Tab("Maps"):
        gr.Markdown("## Food Business Inspection Map\nEach dot = a restaurant. Color = last inspection result. Hover for details.")
        gr.Plot(food_map())
        gr.Markdown("## Critical Violation Heatmap\nDensity of critical food safety violations across the county.")
        gr.Plot(food_violations_heatmap())
        gr.Markdown("## Crime x Food Safety Overlay\nBubble size = crime volume on that street. Color = inspection result. Hover for crime type + violation count.")
        gr.Plot(crime_food_overlay_map())

    with gr.Tab("Crime Reports (260K)"):
        c1, c2, c3 = crime_tab()
        gr.Plot(c1)
        gr.Plot(c3)
        gr.Plot(c2)
        gr.Markdown("### Filter & Explore")
        crime_cats = ["All"] + sorted(crime["parent_incident_type"].dropna().unique().tolist())
        crime_filter = gr.Dropdown(choices=crime_cats, value="All", label="Filter by Incident Category")
        crime_table = gr.Dataframe(value=crime.head(20), label="Filtered Data")
        crime_count = gr.Markdown("Showing 20 of 259,660 rows")
        def filter_crime(cat):
            if cat == "All":
                filtered = crime
            else:
                filtered = crime[crime["parent_incident_type"] == cat]
            return filtered.head(100), f"Showing up to 100 of {len(filtered):,} rows (category: {cat})"
        crime_filter.change(filter_crime, inputs=crime_filter, outputs=[crime_table, crime_count])
        gr.Markdown(make_data_dict(crime, "Crime Reports"))

    with gr.Tab("Food — Businesses (8.6K)"):
        _, f2, _, _ = food_charts()
        gr.Plot(f2)
        gr.Markdown("### Filter & Explore")
        biz_cities = ["All"] + sorted(biz["CITY"].dropna().unique().tolist())
        biz_filter = gr.Dropdown(choices=biz_cities, value="All", label="Filter by City")
        biz_table = gr.Dataframe(value=biz.head(20), label="Filtered Data")
        biz_count = gr.Markdown("Showing 20 of 8,588 rows")
        def filter_biz(city):
            if city == "All":
                filtered = biz
            else:
                filtered = biz[biz["CITY"] == city]
            return filtered.head(100), f"Showing up to 100 of {len(filtered):,} rows (city: {city})"
        biz_filter.change(filter_biz, inputs=biz_filter, outputs=[biz_table, biz_count])
        gr.Markdown(make_data_dict(biz, "Food Businesses"))

    with gr.Tab("Food — Inspections (22K)"):
        f1, _, _, _ = food_charts()
        gr.Plot(f1)
        gr.Markdown("### Filter & Explore")
        insp_results = ["All", "G - Green (Pass)", "Y - Yellow (Conditional)", "R - Red (Fail)"]
        insp_filter = gr.Dropdown(choices=insp_results, value="All", label="Filter by Result")
        insp_table = gr.Dataframe(value=insp.head(20), label="Filtered Data")
        insp_count = gr.Markdown("Showing 20 of 21,895 rows")
        def filter_insp(result):
            if result == "All":
                filtered = insp
            else:
                code = result[0]  # "G", "Y", or "R"
                filtered = insp[insp["result"] == code]
            return filtered.head(100), f"Showing up to 100 of {len(filtered):,} rows (result: {result})"
        insp_filter.change(filter_insp, inputs=insp_filter, outputs=[insp_table, insp_count])
        gr.Markdown(make_data_dict(insp, "Food Inspections"))

    with gr.Tab("Food — Violations (64K)"):
        _, _, f3, f4 = food_charts()
        with gr.Row():
            gr.Plot(f4)
            gr.Plot(f3)

        # Critical violations deep dive
        gr.Markdown("## Critical Violations Deep Dive (9,255 violations)")
        crit_viol = viol[viol["critical"] == True].copy()
        crit_desc = crit_viol["DESCRIPTION"].value_counts()
        fig_crit = px.bar(
            x=crit_desc.values, y=crit_desc.index, orientation="h", template=DARK,
            title="Critical Violations by Type — What's Actually Failing?",
            labels={"x": "Count", "y": ""},
            color=crit_desc.values,
            color_continuous_scale=["#22c55e", "#eab308", "#ef4444"],
        )
        fig_crit.update_layout(
            yaxis=dict(autorange="reversed"), height=650,
            coloraxis_showscale=False,
            margin=dict(l=350),
        )
        gr.Plot(fig_crit)

        gr.Markdown("""
### What the critical violations tell us

| Rank | Violation | Count | % of Critical | What it means |
|------|-----------|-------|--------------|---------------|
| 1 | **Improper hot/cold holding temps** | 3,420 | 37% | Food stored in the "danger zone" (41-135F) where bacteria multiply rapidly |
| 2 | **Inadequate handwash facilities** | 1,763 | 19% | No soap, no hot water, blocked sinks — workers can't wash hands properly |
| 3 | **Food contact surfaces not clean** | 902 | 10% | Cutting boards, prep tables, utensils harboring bacteria |
| 4 | **Rodents, insects, birds, animals** | 852 | 9% | Active pest infestations in food areas |
| 5 | **Time as public health control** | 591 | 6% | Food left out without time-marking — no way to know if it's safe |

**The top 2 violations alone account for 56% of all critical failures.** These are systemic — not one-off incidents but recurring patterns across hundreds of businesses. Temperature control and handwashing are the two most basic food safety requirements, and they're failing at scale.
""")

        # Sample critical violation comments
        gr.Markdown("### Sample Critical Violation Comments")
        crit_sample = crit_viol[crit_viol["violation_comment"].notna()].head(10)[["DESCRIPTION", "violation_comment"]].copy()
        crit_sample["DESCRIPTION"] = crit_sample["DESCRIPTION"].str[:50]
        crit_sample["violation_comment"] = crit_sample["violation_comment"].str[:300]
        gr.HTML(crit_sample.to_html(index=False, classes="table", border=0))

        gr.Markdown("### Filter & Explore Violations")
        viol_types = ["All", "Critical Only", "Non-Critical Only"] + sorted(viol["DESCRIPTION"].dropna().unique().tolist())
        viol_filter = gr.Dropdown(choices=viol_types, value="All", label="Filter by Type")
        viol_table = gr.Dataframe(value=viol.head(20), label="Filtered Data")
        viol_count = gr.Markdown("Showing 20 of 64,364 rows")
        def filter_viol(vtype):
            if vtype == "All":
                filtered = viol
            elif vtype == "Critical Only":
                filtered = viol[viol["critical"] == True]
            elif vtype == "Non-Critical Only":
                filtered = viol[viol["critical"] == False]
            else:
                filtered = viol[viol["DESCRIPTION"] == vtype]
            return filtered.head(100), f"Showing up to 100 of {len(filtered):,} rows (filter: {vtype})"
        viol_filter.change(filter_viol, inputs=viol_filter, outputs=[viol_table, viol_count])
        gr.Markdown(make_data_dict(viol, "Food Violations"))

    with gr.Tab("County Employees (26K)"):
        e1, e2, e3, e4 = eeo_tab()
        with gr.Row():
            gr.Plot(e1)
            gr.Plot(e2)
        gr.Plot(e3)
        gr.Plot(e4)
        gr.Markdown("### Filter & Explore")
        dept_col = [c for c in eeo.columns if "Department" in c][0]
        eeo_depts = ["All"] + sorted(eeo[dept_col].dropna().unique().tolist())
        eeo_filter = gr.Dropdown(choices=eeo_depts, value="All", label="Filter by Department")
        eeo_table = gr.Dataframe(value=eeo.head(20), label="Filtered Data")
        eeo_count = gr.Markdown("Showing 20 of 26,042 rows")
        def filter_eeo(dept):
            if dept == "All":
                filtered = eeo
            else:
                filtered = eeo[eeo[dept_col] == dept]
            return filtered.head(100), f"Showing up to 100 of {len(filtered):,} rows (dept: {dept})"
        eeo_filter.change(filter_eeo, inputs=eeo_filter, outputs=[eeo_table, eeo_count])
        gr.Markdown(make_data_dict(eeo, "EEO Employee Breakdown"))

    with gr.Tab("Photo Collection (4.5K)"):
        p1, p2 = photos_tab()
        with gr.Row():
            gr.Plot(p1)
            gr.Plot(p2)
        gr.Markdown("### Sample Data (10 rows)")
        gr.HTML(make_sample_table(photos))
        gr.Markdown(make_data_dict(photos, "County Photographers' Collection"))

app.launch(server_name="0.0.0.0", server_port=7860, allowed_paths=[os.path.expanduser("~/hackathon")])
