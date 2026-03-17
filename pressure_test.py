"""Find real examples from the data that prove each pressure test scenario."""
import pandas as pd
import os
import numpy as np

DATA = os.path.expanduser("~/data")
HACK = os.path.expanduser("~/hackathon")

# Load all data
print("Loading datasets...")
crime = pd.read_csv(f"{DATA}/Crime_Reports_20260306.csv")
biz = pd.read_csv(f"{DATA}/SCC_DEH_Food_Data_BUSINESS_20260306.csv")
insp = pd.read_csv(f"{DATA}/SCC_DEH_Food_Data_INSPECTIONS_20260306.csv")
viol = pd.read_csv(f"{DATA}/SCC_DEH_Food_Data_VIOLATIONS_20260306.csv")
census = pd.read_csv(f"{HACK}/census_income.csv")
cdc = pd.read_csv(f"{HACK}/cdc_places.csv")

# ============================================================
# PRESSURE TEST 1: Find census tracts with compounding failures
# ============================================================
print("\n" + "="*70)
print("PRESSURE TEST 1: Tracts with compounding risk")
print("="*70)

# Get food insecurity by tract
fi = cdc[cdc["short_question_text"] == "Food Insecurity"][["locationid", "data_value", "totalpopulation"]].copy()
fi.columns = ["tract", "food_insecurity_pct", "population"]

# Get diabetes by tract
diab = cdc[cdc["short_question_text"] == "Diabetes"][["locationid", "data_value"]].copy()
diab.columns = ["tract", "diabetes_pct"]

# Get depression by tract
dep = cdc[cdc["short_question_text"] == "Depression"][["locationid", "data_value"]].copy()
dep.columns = ["tract", "depression_pct"]

# Merge health data
health = fi.merge(diab, on="tract").merge(dep, on="tract")

# Map food businesses to census tracts via zip code
# biz has lat/lon but we need tract. Use zip as proxy.
biz["zip"] = biz["postal_code"].astype(str).str[:5]
census["zip"] = census["zip"].astype(str)

# Get critical violations per business
crit_per_biz = viol[viol["critical"] == True].merge(
    insp[["inspection_id", "business_id"]], on="inspection_id"
).groupby("business_id").size().reset_index(name="critical_violations")

# Get red inspections per business
red_per_biz = insp[insp["result"] == "R"].groupby("business_id").size().reset_index(name="red_inspections")

# Merge to business
biz_risk = biz.merge(crit_per_biz, on="business_id", how="left")
biz_risk = biz_risk.merge(red_per_biz, on="business_id", how="left")
biz_risk["critical_violations"] = biz_risk["critical_violations"].fillna(0).astype(int)
biz_risk["red_inspections"] = biz_risk["red_inspections"].fillna(0).astype(int)

# Aggregate by zip
zip_food = biz_risk.groupby("zip").agg(
    businesses=("business_id", "count"),
    total_critical=("critical_violations", "sum"),
    total_red=("red_inspections", "sum"),
    avg_critical=("critical_violations", "mean"),
).reset_index()

# Merge with census
zip_food = zip_food.merge(census, on="zip", how="inner")
zip_food["poverty_rate"] = zip_food["poverty_pop"] / zip_food["total_pop"] * 100

# Crime by street — aggregate to zip (approximate using address patterns)
# We'll use the food biz zip as our geographic unit
crime["street_norm"] = crime["address"].str.replace(r"^\d+\s+Block\s+", "", regex=True).str.strip().str.upper()
biz_risk["street_norm"] = biz_risk["address"].str.replace(r"^\d+\s*", "", regex=True).str.strip().str.upper()

# Crime per zip (via street → business → zip mapping)
street_to_zip = biz_risk[["street_norm", "zip"]].drop_duplicates()
crime_streets = crime.groupby("street_norm").size().reset_index(name="crime_count")
crime_by_zip = crime_streets.merge(street_to_zip, on="street_norm").groupby("zip")["crime_count"].sum().reset_index()

zip_full = zip_food.merge(crime_by_zip, on="zip", how="left")
zip_full["crime_count"] = zip_full["crime_count"].fillna(0).astype(int)
zip_full["crime_per_biz"] = zip_full["crime_count"] / zip_full["businesses"]

# Find the compounding risk zips
zip_full["risk_score"] = (
    zip_full["avg_critical"].rank(pct=True) * 25 +
    zip_full["poverty_rate"].rank(pct=True) * 25 +
    zip_full["crime_per_biz"].rank(pct=True) * 25 +
    zip_full["total_red"].rank(pct=True) * 25
)

print("\nTop 10 Compounding Risk Zip Codes:")
print("-" * 70)
top_zips = zip_full.nlargest(10, "risk_score")
for _, row in top_zips.iterrows():
    print(f"  ZIP {row['zip']} ({row['name']})")
    print(f"    Businesses: {row['businesses']}  |  Critical violations: {row['total_critical']}  |  Red inspections: {row['total_red']}")
    print(f"    Poverty rate: {row['poverty_rate']:.1f}%  |  Median income: ${row['median_income']:,.0f}")
    print(f"    Crime on food streets: {row['crime_count']:,}  |  Risk score: {row['risk_score']:.1f}")
    print()

# ============================================================
# PRESSURE TEST 2: Repeat offender restaurants in vulnerable areas
# ============================================================
print("="*70)
print("PRESSURE TEST 2: Repeat offenders in vulnerable neighborhoods")
print("="*70)

repeat_offenders = biz_risk[biz_risk["red_inspections"] >= 2].merge(
    census[["zip", "median_income", "poverty_pop", "total_pop"]], on="zip", how="left"
)
repeat_offenders["poverty_rate"] = repeat_offenders["poverty_pop"] / repeat_offenders["total_pop"] * 100

# Sort by critical violations
worst = repeat_offenders.nlargest(15, "critical_violations")
print(f"\nRepeat Red restaurants (2+ failures) with most critical violations:")
print("-" * 70)
for _, row in worst.iterrows():
    poverty = f"{row['poverty_rate']:.1f}%" if pd.notna(row['poverty_rate']) else "N/A"
    income = f"${row['median_income']:,.0f}" if pd.notna(row['median_income']) else "N/A"
    print(f"  {row['name'][:40]:40s} | {row['CITY']:15s} | ZIP {row['zip']}")
    print(f"    Red inspections: {row['red_inspections']}  |  Critical violations: {row['critical_violations']}")
    print(f"    Zip poverty rate: {poverty}  |  Zip median income: {income}")
    print()

# ============================================================
# PRESSURE TEST 3: Crime + food safety correlation by street
# ============================================================
print("="*70)
print("PRESSURE TEST 3: High-crime streets with food safety failures")
print("="*70)

# Streets with both high crime AND red-rated restaurants
biz_street = biz_risk.groupby("street_norm").agg(
    businesses=("business_id", "count"),
    total_critical=("critical_violations", "sum"),
    total_red=("red_inspections", "sum"),
    cities=("CITY", "first"),
).reset_index()

street_combined = biz_street.merge(crime_streets, on="street_norm", how="inner")
street_combined = street_combined[street_combined["total_red"] > 0]
street_combined["danger_score"] = street_combined["crime_count"] * street_combined["total_critical"]
street_combined = street_combined.nlargest(15, "danger_score")

print(f"\nStreets with BOTH high crime AND food safety failures:")
print("-" * 70)
for _, row in street_combined.iterrows():
    print(f"  {row['street_norm'][:35]:35s} ({row['cities']})")
    print(f"    {row['businesses']} restaurants  |  {row['total_red']} Red inspections  |  {row['total_critical']} critical violations")
    print(f"    {row['crime_count']:,} crime incidents on this street")
    print()

# ============================================================
# PRESSURE TEST 4: Health outcomes in high-violation areas
# ============================================================
print("="*70)
print("PRESSURE TEST 4: Health outcomes vs food safety (by zip → tract)")
print("="*70)

# Get average health metrics for high vs low food safety zips
median_critical = zip_full["avg_critical"].median()
high_risk_zips = zip_full[zip_full["avg_critical"] > median_critical]["zip"].tolist()
low_risk_zips = zip_full[zip_full["avg_critical"] <= median_critical]["zip"].tolist()

# Map zips to tracts (approximate — tract FIPS starts with state+county, 06085)
# CDC tracts are like 06085030102. We can't perfectly map zip→tract, but we can
# use census data to bridge. For now, compare high-poverty vs low-poverty tracts in CDC.
median_fi = health["food_insecurity_pct"].median()
high_fi_tracts = health[health["food_insecurity_pct"] > median_fi]
low_fi_tracts = health[health["food_insecurity_pct"] <= median_fi]

measures = ["Diabetes", "Obesity", "Depression", "High Blood Pressure", "Frequent Mental Distress", "Food Stamps"]
print(f"\nHealth outcomes: Food-INSECURE tracts vs Food-SECURE tracts")
print(f"(Split at median food insecurity rate of {median_fi:.1f}%)")
print("-" * 70)
print(f"  {'Measure':35s} {'Food Insecure':>15s} {'Food Secure':>15s} {'Difference':>12s}")
print(f"  {'':35s} {'(avg %)':>15s} {'(avg %)':>15s} {'':>12s}")
print("-" * 70)

for measure in measures:
    m = cdc[cdc["short_question_text"] == measure]
    hi = m[m["locationid"].isin(high_fi_tracts["tract"])]["data_value"].mean()
    lo = m[m["locationid"].isin(low_fi_tracts["tract"])]["data_value"].mean()
    diff = hi - lo
    pct_diff = (hi / lo - 1) * 100 if lo > 0 else 0
    print(f"  {measure:35s} {hi:>14.1f}% {lo:>14.1f}% {'+' if diff > 0 else ''}{diff:>10.1f}pp ({pct_diff:+.0f}%)")

print()
high_pop = high_fi_tracts["population"].sum()
low_pop = low_fi_tracts["population"].sum()
print(f"  Population in food-insecure tracts: {high_pop:,.0f}")
print(f"  Population in food-secure tracts:   {low_pop:,.0f}")

# ============================================================
# SUMMARY: The killer stats
# ============================================================
print("\n" + "="*70)
print("KILLER STATS FOR THE PITCH")
print("="*70)

total_crit = (viol["critical"] == True).sum()
temp_crit = viol[(viol["critical"] == True) & (viol["DESCRIPTION"].str.contains("temperature", case=False, na=False))].shape[0]
repeat_count = (biz_risk["red_inspections"] >= 2).sum()
total_red = (insp["result"] == "R").sum()

print(f"  - {total_crit:,} critical food safety violations in 2 years")
print(f"  - {temp_crit:,} ({temp_crit/total_crit*100:.0f}%) are temperature control failures — the #1 killer")
print(f"  - {repeat_count} restaurants have failed 2+ inspections — repeat offenders")
print(f"  - {total_red} Red (fail) inspections out of 21,895 total ({total_red/21895*100:.1f}%)")
print(f"  - Top risk zip: {top_zips.iloc[0]['zip']} with {top_zips.iloc[0]['total_critical']} critical violations, {top_zips.iloc[0]['poverty_rate']:.1f}% poverty")
