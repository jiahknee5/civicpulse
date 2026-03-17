"""Build a District Scorecard from all datasets. SCC has 5 supervisorial districts.
We'll approximate district assignment by zip code mapping."""
import pandas as pd
import os

DATA = os.path.expanduser("~/data")
HACK = os.path.expanduser("~/hackathon")

# SCC Supervisorial District → Zip code mapping (approximate, based on public maps)
# District 1: South SJ, Morgan Hill, Gilroy
# District 2: West SJ, Cupertino, Saratoga, Los Gatos, parts of Campbell
# District 3: East SJ, Milpitas
# District 4: South SJ, parts of central SJ
# District 5: North county — Palo Alto, Mountain View, Sunnyvale, Santa Clara, Los Altos

ZIP_TO_DISTRICT = {
    # District 1 — South County (Mike Wasserman area)
    "95020": 1, "95037": 1, "95046": 1, "95138": 1, "95139": 1, "95119": 1,
    "95123": 1, "95136": 1, "95111": 1, "95141": 1,
    # District 2 — West Valley (Cindy Chavez area)
    "95014": 2, "95070": 2, "95030": 2, "95032": 2, "95008": 2, "95009": 2,
    "95129": 2, "95117": 2, "95128": 2, "95124": 2, "95125": 2, "95118": 2, "95120": 2,
    # District 3 — East SJ, Milpitas (Otto Lee area)
    "95116": 3, "95122": 3, "95127": 3, "95148": 3, "95121": 3, "95035": 3,
    "95132": 3, "95133": 3, "95134": 3,
    # District 4 — Central/South SJ (Susan Ellenberg area)
    "95112": 4, "95113": 4, "95110": 4, "95126": 4, "95131": 4,
    "95135": 4, "95140": 4,
    # District 5 — North County (Joe Simitian area)
    "94022": 5, "94024": 5, "94040": 5, "94041": 5, "94043": 5,
    "94085": 5, "94086": 5, "94087": 5, "94089": 5,
    "94301": 5, "94303": 5, "94304": 5, "94306": 5,
    "95050": 5, "95051": 5, "95054": 5, "95055": 5,
}

# Load data
print("Loading...")
biz = pd.read_csv(f"{DATA}/SCC_DEH_Food_Data_BUSINESS_20260306.csv")
insp = pd.read_csv(f"{DATA}/SCC_DEH_Food_Data_INSPECTIONS_20260306.csv")
viol = pd.read_csv(f"{DATA}/SCC_DEH_Food_Data_VIOLATIONS_20260306.csv")
crime = pd.read_csv(f"{DATA}/Crime_Reports_20260306.csv")
census = pd.read_csv(f"{HACK}/census_income.csv")
census["zip"] = census["zip"].astype(str)
cdc = pd.read_csv(f"{HACK}/cdc_places.csv")

# Assign districts
biz["zip"] = biz["postal_code"].astype(str).str[:5]
biz["district"] = biz["zip"].map(ZIP_TO_DISTRICT)

# Merge inspections + violations to biz
crit_per_biz = viol[viol["critical"] == True].merge(
    insp[["inspection_id", "business_id"]], on="inspection_id"
).groupby("business_id").size().reset_index(name="critical_violations")

red_per_biz = insp[insp["result"] == "R"].groupby("business_id").size().reset_index(name="red_inspections")
green_per_biz = insp[insp["result"] == "G"].groupby("business_id").size().reset_index(name="green_inspections")

biz_full = biz.merge(crit_per_biz, on="business_id", how="left")
biz_full = biz_full.merge(red_per_biz, on="business_id", how="left")
biz_full = biz_full.merge(green_per_biz, on="business_id", how="left")
biz_full["critical_violations"] = biz_full["critical_violations"].fillna(0).astype(int)
biz_full["red_inspections"] = biz_full["red_inspections"].fillna(0).astype(int)
biz_full["green_inspections"] = biz_full["green_inspections"].fillna(0).astype(int)

# Crime by street → zip
crime["street_norm"] = crime["address"].str.replace(r"^\d+\s+Block\s+", "", regex=True).str.strip().str.upper()
biz_full["street_norm"] = biz_full["address"].str.replace(r"^\d+\s*", "", regex=True).str.strip().str.upper()
street_to_zip = biz_full[["street_norm", "zip"]].drop_duplicates()
crime_streets = crime.groupby("street_norm").size().reset_index(name="crime_count")
crime_by_zip = crime_streets.merge(street_to_zip, on="street_norm").groupby("zip")["crime_count"].sum().reset_index()

# Census by district
census["district"] = census["zip"].map(ZIP_TO_DISTRICT)

# Aggregate by district
print("\n" + "="*80)
print("DISTRICT SCORECARDS")
print("="*80)

for d in sorted(ZIP_TO_DISTRICT.values()):
    if d not in [1,2,3,4,5]:
        continue
    d_biz = biz_full[biz_full["district"] == d]
    d_census = census[census["district"] == d]
    d_crime_zips = crime_by_zip[crime_by_zip["zip"].map(ZIP_TO_DISTRICT) == d]

    n_biz = len(d_biz)
    n_red = d_biz["red_inspections"].sum()
    n_critical = d_biz["critical_violations"].sum()
    n_repeat = (d_biz["red_inspections"] >= 2).sum()
    pass_rate = d_biz["green_inspections"].sum() / max(1, d_biz[["green_inspections","red_inspections"]].sum().sum()) * 100
    total_crime = d_crime_zips["crime_count"].sum()
    pop = d_census["total_pop"].sum()
    poverty_pop = d_census["poverty_pop"].sum()
    poverty_rate = poverty_pop / max(1, pop) * 100
    med_income = d_census["median_income"].median()

    # Top offenders in district
    top_offenders = d_biz.nlargest(3, "critical_violations")

    print(f"\n{'─'*80}")
    print(f"  DISTRICT {d}")
    print(f"{'─'*80}")
    print(f"  Population:        {pop:>10,}")
    print(f"  Median income:     ${med_income:>10,.0f}")
    print(f"  Poverty rate:      {poverty_rate:>10.1f}%")
    print(f"  Food businesses:   {n_biz:>10,}")
    print(f"  Red inspections:   {n_red:>10,}")
    print(f"  Critical viols:    {n_critical:>10,}")
    print(f"  Repeat offenders:  {n_repeat:>10}")
    print(f"  Inspection pass %: {pass_rate:>10.1f}%")
    print(f"  Crime on food st:  {total_crime:>10,}")
    print(f"  Crime per biz:     {total_crime/max(1,n_biz):>10.1f}")
    print(f"\n  Top violators:")
    for _, row in top_offenders.iterrows():
        print(f"    {row['name'][:35]:35s} | {row['CITY']:15s} | {row['critical_violations']} critical, {row['red_inspections']} Red")

# County totals
print(f"\n{'═'*80}")
print(f"  COUNTY TOTALS")
print(f"{'═'*80}")
total_biz = len(biz_full[biz_full["district"].notna()])
total_red = biz_full[biz_full["district"].notna()]["red_inspections"].sum()
total_crit = biz_full[biz_full["district"].notna()]["critical_violations"].sum()
total_repeat = (biz_full[biz_full["district"].notna()]["red_inspections"] >= 2).sum()
total_pop = census[census["district"].notna()]["total_pop"].sum()
print(f"  Population:        {total_pop:>10,}")
print(f"  Food businesses:   {total_biz:>10,}")
print(f"  Red inspections:   {total_red:>10,}")
print(f"  Critical viols:    {total_crit:>10,}")
print(f"  Repeat offenders:  {total_repeat:>10}")

# District comparison
print(f"\n{'═'*80}")
print(f"  DISTRICT COMPARISON — Share of County Problems")
print(f"{'═'*80}")
print(f"  {'District':10s} {'% of Biz':>10s} {'% of Red':>10s} {'% of Critical':>15s} {'% of Repeat':>12s} {'% of Crime':>12s}")
for d in [1,2,3,4,5]:
    d_biz = biz_full[biz_full["district"] == d]
    d_crime_zips = crime_by_zip[crime_by_zip["zip"].map(ZIP_TO_DISTRICT) == d]
    pct_biz = len(d_biz) / max(1, total_biz) * 100
    pct_red = d_biz["red_inspections"].sum() / max(1, total_red) * 100
    pct_crit = d_biz["critical_violations"].sum() / max(1, total_crit) * 100
    pct_repeat = (d_biz["red_inspections"] >= 2).sum() / max(1, total_repeat) * 100
    pct_crime = d_crime_zips["crime_count"].sum() / max(1, crime_by_zip[crime_by_zip["zip"].map(ZIP_TO_DISTRICT).notna()]["crime_count"].sum()) * 100
    flag = " ⚠️" if pct_red > pct_biz * 1.3 else ""
    print(f"  District {d:1d}  {pct_biz:>10.1f}% {pct_red:>10.1f}% {pct_crit:>14.1f}% {pct_repeat:>11.1f}% {pct_crime:>11.1f}%{flag}")
