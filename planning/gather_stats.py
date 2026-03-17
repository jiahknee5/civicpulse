import pandas as pd, os
DATA = os.path.expanduser("~/data")

crime = pd.read_csv(f"{DATA}/Crime_Reports_20260306.csv")
crime["dt"] = pd.to_datetime(crime["incident_datetime"], format="%Y %b %d %I:%M:%S %p", errors="coerce")
valid_crime = crime[crime["dt"] > "2019-01-01"]

biz = pd.read_csv(f"{DATA}/SCC_DEH_Food_Data_BUSINESS_20260306.csv")
insp = pd.read_csv(f"{DATA}/SCC_DEH_Food_Data_INSPECTIONS_20260306.csv")
viol = pd.read_csv(f"{DATA}/SCC_DEH_Food_Data_VIOLATIONS_20260306.csv")
eeo = pd.read_csv(f"{DATA}/Employee_Breakdown_by_Equal_Employment_Opportunity_Categories_20260306.csv")
photos = pd.read_csv(f'{DATA}/County_Photographers\'_Collection_20260306.csv')

print("=== CRIME ===")
yearly = valid_crime.set_index("dt").resample("YE").size()
for k, v in yearly.items():
    print(f"  {k.year}: {v:,}")
top3 = crime["parent_incident_type"].value_counts().head(5)
for k, v in top3.items():
    print(f"  {k}: {v:,}")

print("\n=== FOOD ===")
red_count = (insp["result"] == "R").sum()
yellow_count = (insp["result"] == "Y").sum()
green_count = (insp["result"] == "G").sum()
print(f"  Green: {green_count:,}  Yellow: {yellow_count:,}  Red: {red_count:,}")
red_biz = insp[insp["result"] == "R"].merge(biz[["business_id", "name", "CITY"]], on="business_id")
repeat_red = red_biz.groupby("business_id").size()
print(f"  Businesses with 2+ red inspections: {(repeat_red >= 2).sum()}")
red_cities = red_biz["CITY"].value_counts().head(5)
for k, v in red_cities.items():
    print(f"  Red in {k}: {v}")
crit = (viol["critical"] == "true").sum()
noncrit = (viol["critical"] == "false").sum()
print(f"  Critical: {crit:,}  Non-critical: {noncrit:,}")
top_crit = viol[viol["critical"] == "true"]["DESCRIPTION"].value_counts().head(3)
for k, v in top_crit.items():
    print(f"  Critical: {k[:60]}: {v:,}")

print("\n=== EEO ===")
dept_col = [c for c in eeo.columns if "Department" in c][0]
hc = eeo[eeo[dept_col].str.contains("HEALTHCARE", na=False)]
print(f"  Healthcare: {len(hc):,} / {len(eeo):,} ({len(hc)/len(eeo):.0%})")
for k, v in eeo["Gender"].value_counts().items():
    print(f"  {k}: {v:,} ({v/len(eeo):.0%})")
for k, v in eeo["Ethnicity"].value_counts().head(5).items():
    print(f"  {k}: {v:,} ({v/len(eeo):.0%})")

print("\n=== PHOTOS ===")
photos["dt"] = pd.to_datetime(photos["Date"], unit="D", origin="1899-12-30", errors="coerce")
decade = (photos["dt"].dt.year // 10 * 10).value_counts().sort_index()
for k, v in decade.items():
    print(f"  {int(k)}s: {v:,}")
for k, v in photos["Department"].value_counts().head(5).items():
    print(f"  {k}: {v:,}")
