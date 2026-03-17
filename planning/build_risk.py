"""
build_risk.py — CivicPulse Data Pipeline
Runs on DELL-31. Joins food + crime + census + CDC into per-ZIP risk profiles.
Output: ~/hackathon/zip_risk.json
"""
import pandas as pd
import numpy as np
import json
import re
from pathlib import Path

DATA = Path.home() / "data"
HACK = Path.home() / "hackathon"

print("Loading datasets...")
biz   = pd.read_csv(DATA / "SCC_DEH_Food_Data_BUSINESS_20260306.csv")
insp  = pd.read_csv(DATA / "SCC_DEH_Food_Data_INSPECTIONS_20260306.csv")
viol  = pd.read_csv(DATA / "SCC_DEH_Food_Data_VIOLATIONS_20260306.csv")
crime = pd.read_csv(DATA / "Crime_Reports_20260306.csv")
census = pd.read_csv(HACK / "census_income.csv")
cdc    = pd.read_csv(HACK / "cdc_places.csv")
print("  All loaded.")

# --- Food: violations & inspections per business ---
# Handle critical as bool or string
if viol["critical"].dtype == object:
    crit_mask = viol["critical"].astype(str).str.strip().str.lower() == "true"
else:
    crit_mask = viol["critical"] == True

crit_per_biz = (
    viol[crit_mask]
    .merge(insp[["inspection_id", "business_id"]], on="inspection_id")
    .groupby("business_id").size()
    .reset_index(name="critical_violations")
)
red_per_biz   = insp[insp["result"] == "R"].groupby("business_id").size().reset_index(name="red_inspections")
yel_per_biz   = insp[insp["result"] == "Y"].groupby("business_id").size().reset_index(name="yellow_inspections")
green_per_biz = insp[insp["result"] == "G"].groupby("business_id").size().reset_index(name="green_inspections")

biz["zip"] = biz["postal_code"].astype(str).str[:5]
biz_full = biz.copy()
for df in [crit_per_biz, red_per_biz, yel_per_biz, green_per_biz]:
    biz_full = biz_full.merge(df, on="business_id", how="left")

for col in ["critical_violations", "red_inspections", "yellow_inspections", "green_inspections"]:
    biz_full[col] = biz_full[col].fillna(0).astype(int)

# --- Crime: normalize street names, join to zip via food biz streets ---
def norm_street(s):
    s = str(s).upper().strip()
    s = re.sub(r"^\d+\s+BLOCK\s+OF\s+", "", s)
    s = re.sub(r"^\d+\s+BLOCK\s+", "", s)
    s = re.sub(r"^\d+\s+", "", s)
    return s.strip()

crime["street_norm"] = crime["address"].apply(norm_street)
biz_full["street_norm"] = biz_full["address"].apply(norm_street)

street_to_zip = biz_full[["street_norm", "zip"]].drop_duplicates()
crime_by_street = crime.groupby("street_norm").size().reset_index(name="crime_count")
crime_by_zip = (
    crime_by_street
    .merge(street_to_zip, on="street_norm")
    .groupby("zip")["crime_count"].sum()
    .reset_index()
)

# --- Census: zip-level income & poverty ---
census["zip"] = census["zip"].astype(str)
census["poverty_rate"] = census["poverty_pop"] / census["total_pop"].replace(0, np.nan) * 100

# --- CDC: parse lat/lon from geolocation, assign to nearest ZIP centroid ---
print("Joining CDC to ZIP codes...")
zip_centroids = biz_full.dropna(subset=["latitude", "longitude"]).groupby("zip").agg(
    clat=("latitude", "mean"), clon=("longitude", "mean")
).reset_index()

def parse_cdc_point(geo):
    m = re.search(r"POINT \((-?[\d.]+) (-?[\d.]+)\)", str(geo))
    if m:
        return float(m.group(2)), float(m.group(1))  # lat, lon
    return None, None

cdc_pts = cdc[["locationid", "geolocation"]].drop_duplicates("locationid").copy()
cdc_pts["clat"], cdc_pts["clon"] = zip(*cdc_pts["geolocation"].map(parse_cdc_point))
cdc_pts = cdc_pts.dropna(subset=["clat", "clon"])

# Pivot CDC to wide format (one row per tract, columns = measure values)
cdc_wide = cdc.pivot_table(
    index="locationid", columns="measureid", values="data_value", aggfunc="first"
).reset_index()
cdc_pts = cdc_pts.merge(cdc_wide, on="locationid", how="left")

# Nearest ZIP for each CDC tract (vectorized)
from scipy.spatial import cKDTree
zip_coords = zip_centroids[["clat", "clon"]].values
cdc_coords = cdc_pts[["clat", "clon"]].values
tree = cKDTree(zip_coords)
_, idx = tree.query(cdc_coords)
cdc_pts["zip"] = zip_centroids["zip"].iloc[idx].values

# Aggregate CDC metrics by zip
cdc_measures = ["FOODINSECU", "DIABETES", "OBESITY", "MHLTH", "CSMOKING", "STROKE"]
cdc_available = [c for c in cdc_measures if c in cdc_pts.columns]
if cdc_available:
    cdc_by_zip = cdc_pts.groupby("zip")[cdc_available].mean().reset_index()
else:
    print("  Warning: CDC measure columns not found, skipping CDC join.")
    cdc_by_zip = pd.DataFrame({"zip": zip_centroids["zip"]})

# --- Aggregate all metrics by ZIP ---
print("Computing ZIP-level risk profiles...")

def top_violators(group):
    top = group.nlargest(3, "critical_violations")
    return top[["name", "CITY", "critical_violations", "red_inspections"]].to_dict("records")

zip_stats = biz_full.groupby("zip").agg(
    businesses        = ("business_id", "count"),
    red_count         = ("red_inspections", "sum"),
    yellow_count      = ("yellow_inspections", "sum"),
    green_count       = ("green_inspections", "sum"),
    critical_violations = ("critical_violations", "sum"),
    repeat_offenders  = ("red_inspections", lambda x: (x >= 2).sum()),
    avg_lat           = ("latitude", "mean"),
    avg_lon           = ("longitude", "mean"),
).reset_index()

top_by_zip = biz_full.groupby("zip").apply(top_violators).reset_index(name="top_violators")

zip_stats = zip_stats.merge(top_by_zip, on="zip", how="left")
zip_stats = zip_stats.merge(crime_by_zip.rename(columns={"crime_count": "crime_on_food_streets"}), on="zip", how="left")
zip_stats = zip_stats.merge(census[["zip", "median_income", "poverty_rate", "total_pop"]], on="zip", how="left")
zip_stats = zip_stats.merge(cdc_by_zip, on="zip", how="left")

zip_stats["crime_on_food_streets"] = zip_stats["crime_on_food_streets"].fillna(0).astype(int)
zip_stats["poverty_rate"] = zip_stats["poverty_rate"].fillna(zip_stats["poverty_rate"].median())
zip_stats["median_income"] = zip_stats["median_income"].fillna(zip_stats["median_income"].median())

# Per-business rates
zip_stats["crit_per_biz"] = zip_stats["critical_violations"] / zip_stats["businesses"].clip(lower=1)
zip_stats["red_per_biz"]  = zip_stats["red_count"] / zip_stats["businesses"].clip(lower=1)
zip_stats["crime_per_biz"] = zip_stats["crime_on_food_streets"] / zip_stats["businesses"].clip(lower=1)

# --- Composite Risk Score: percentile rank, 25% each ---
def pct_rank(s):
    return s.rank(pct=True)

zip_stats["rank_crit"]    = pct_rank(zip_stats["crit_per_biz"])
zip_stats["rank_red"]     = pct_rank(zip_stats["red_per_biz"])
zip_stats["rank_poverty"] = pct_rank(zip_stats["poverty_rate"])
zip_stats["rank_crime"]   = pct_rank(zip_stats["crime_per_biz"])

zip_stats["risk_score"] = (
    zip_stats["rank_crit"]    * 0.25 +
    zip_stats["rank_red"]     * 0.25 +
    zip_stats["rank_poverty"] * 0.25 +
    zip_stats["rank_crime"]   * 0.25
) * 100

zip_stats = zip_stats.sort_values("risk_score", ascending=False)

# --- Save ---
output = zip_stats.to_dict("records")
out_path = HACK / "zip_risk.json"
with open(out_path, "w") as f:
    json.dump(output, f, indent=2, default=str)

print(f"\nSaved {len(output)} ZIP profiles → {out_path}")
print("\nTop 10 highest risk ZIPs:")
print(f"  {'ZIP':8s} {'Score':>6s} {'Red':>5s} {'Crit':>6s} {'Crit/Biz':>9s} {'Poverty':>8s} {'Crime':>7s}")
for r in output[:10]:
    print(f"  {r['zip']:8s} {r['risk_score']:>6.1f} {r['red_count']:>5} {r['critical_violations']:>6} "
          f"{r['crit_per_biz']:>9.1f} {r['poverty_rate']:>7.1f}% {r['crime_on_food_streets']:>7,}")
