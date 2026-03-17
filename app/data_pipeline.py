"""Data pipeline — joins all datasets into unified risk profiles. Run once."""
import pandas as pd
import os
import json

DATA = os.path.expanduser("~/data")
HACK = os.path.expanduser("~/hackathon")
OUT = os.path.expanduser("~/hackathon/app/data")
os.makedirs(OUT, exist_ok=True)

def build():
    print("[pipeline] Loading datasets...")
    biz = pd.read_csv(f"{DATA}/SCC_DEH_Food_Data_BUSINESS_20260306.csv")
    insp = pd.read_csv(f"{DATA}/SCC_DEH_Food_Data_INSPECTIONS_20260306.csv")
    viol = pd.read_csv(f"{DATA}/SCC_DEH_Food_Data_VIOLATIONS_20260306.csv")
    crime = pd.read_csv(f"{DATA}/Crime_Reports_20260306.csv")
    census = pd.read_csv(f"{HACK}/census_income.csv")
    census["zip"] = census["zip"].astype(str)
    cdc = pd.read_csv(f"{HACK}/cdc_places.csv")

    # --- Business risk profiles ---
    print("[pipeline] Building business risk profiles...")
    biz["zip"] = biz["postal_code"].astype(str).str[:5]

    # Critical violations per business
    crit_per_biz = viol[viol["critical"] == True].merge(
        insp[["inspection_id", "business_id"]], on="inspection_id"
    ).groupby("business_id").size().reset_index(name="critical_violations")

    # Red inspections per business
    red_per_biz = insp[insp["result"] == "R"].groupby("business_id").size().reset_index(name="red_inspections")

    # Total inspections per business
    total_per_biz = insp.groupby("business_id").size().reset_index(name="total_inspections")

    # Top violation descriptions per business
    top_viol_per_biz = viol[viol["critical"] == True].merge(
        insp[["inspection_id", "business_id"]], on="inspection_id"
    ).groupby(["business_id", "DESCRIPTION"]).size().reset_index(name="count")
    top_viol_per_biz = top_viol_per_biz.sort_values("count", ascending=False).groupby("business_id").head(3)
    top_viols_str = top_viol_per_biz.groupby("business_id").apply(
        lambda x: "; ".join(f"{r['DESCRIPTION'][:50]} ({r['count']}x)" for _, r in x.iterrows())
    ).reset_index(name="top_violations")

    biz_full = biz.merge(crit_per_biz, on="business_id", how="left")
    biz_full = biz_full.merge(red_per_biz, on="business_id", how="left")
    biz_full = biz_full.merge(total_per_biz, on="business_id", how="left")
    biz_full = biz_full.merge(top_viols_str, on="business_id", how="left")
    for col in ["critical_violations", "red_inspections", "total_inspections"]:
        biz_full[col] = biz_full[col].fillna(0).astype(int)
    biz_full["top_violations"] = biz_full["top_violations"].fillna("")

    # --- Crime by street ---
    print("[pipeline] Matching crime to food streets...")
    crime["street_norm"] = crime["address"].str.replace(r"^\d+\s+Block\s+", "", regex=True).str.strip().str.upper()
    biz_full["street_norm"] = biz_full["address"].str.replace(r"^\d+\s*", "", regex=True).str.strip().str.upper()
    crime_streets = crime.groupby("street_norm").size().reset_index(name="crime_count")
    street_to_zip = biz_full[["street_norm", "zip"]].drop_duplicates()
    crime_by_zip = crime_streets.merge(street_to_zip, on="street_norm").groupby("zip")["crime_count"].sum().reset_index()

    # --- ZIP-level risk profiles ---
    print("[pipeline] Computing ZIP risk profiles...")
    zip_agg = biz_full.groupby("zip").agg(
        businesses=("business_id", "count"),
        total_critical=("critical_violations", "sum"),
        total_red=("red_inspections", "sum"),
        avg_critical=("critical_violations", "mean"),
        repeat_offenders=("red_inspections", lambda x: (x >= 2).sum()),
    ).reset_index()

    zip_full = zip_agg.merge(census, on="zip", how="left")
    zip_full = zip_full.merge(crime_by_zip, on="zip", how="left")
    zip_full["crime_count"] = zip_full["crime_count"].fillna(0).astype(int)
    zip_full["poverty_rate"] = zip_full["poverty_pop"] / zip_full["total_pop"] * 100

    # CDC health data by zip (approximate — average across all tracts)
    fi = cdc[cdc["short_question_text"] == "Food Insecurity"][["locationid", "data_value"]].copy()
    fi.columns = ["tract", "food_insecurity_pct"]
    diabetes = cdc[cdc["short_question_text"] == "Diabetes"][["locationid", "data_value"]].copy()
    diabetes.columns = ["tract", "diabetes_pct"]
    obesity = cdc[cdc["short_question_text"] == "Obesity"][["locationid", "data_value"]].copy()
    obesity.columns = ["tract", "obesity_pct"]
    mental = cdc[cdc["short_question_text"] == "Frequent Mental Distress"][["locationid", "data_value"]].copy()
    mental.columns = ["tract", "mental_distress_pct"]

    # County averages for CDC (we'll attach to zips later via agent reasoning)
    cdc_avg = {
        "food_insecurity_pct": fi["food_insecurity_pct"].mean(),
        "diabetes_pct": diabetes["diabetes_pct"].mean(),
        "obesity_pct": obesity["obesity_pct"].mean(),
        "mental_distress_pct": mental["mental_distress_pct"].mean(),
    }

    # Risk score
    zip_full["risk_score"] = (
        zip_full["avg_critical"].rank(pct=True) * 25 +
        zip_full["poverty_rate"].rank(pct=True) * 25 +
        (zip_full["crime_count"] / zip_full["businesses"].clip(lower=1)).rank(pct=True) * 25 +
        zip_full["total_red"].rank(pct=True) * 25
    )

    # --- Save outputs ---
    print("[pipeline] Saving...")
    zip_full.to_csv(f"{OUT}/zip_risk_profiles.csv", index=False)
    biz_full.to_csv(f"{OUT}/business_profiles.csv", index=False)

    # Top 10 risk zips as JSON for agent context
    top_zips = zip_full.nlargest(10, "risk_score")
    top_zips_list = []
    for _, z in top_zips.iterrows():
        # Get top 5 worst businesses in this zip
        worst_biz = biz_full[biz_full["zip"] == z["zip"]].nlargest(5, "critical_violations")
        top_zips_list.append({
            "zip": z["zip"],
            "name": str(z.get("name", "")),
            "risk_score": round(z["risk_score"], 1),
            "businesses": int(z["businesses"]),
            "total_red": int(z["total_red"]),
            "total_critical": int(z["total_critical"]),
            "repeat_offenders": int(z["repeat_offenders"]),
            "poverty_rate": round(z["poverty_rate"], 1) if pd.notna(z["poverty_rate"]) else None,
            "median_income": int(z["median_income"]) if pd.notna(z["median_income"]) else None,
            "crime_on_food_streets": int(z["crime_count"]),
            "worst_businesses": [
                {
                    "name": r["name"],
                    "city": r["CITY"],
                    "critical_violations": int(r["critical_violations"]),
                    "red_inspections": int(r["red_inspections"]),
                    "top_violations": r["top_violations"],
                }
                for _, r in worst_biz.iterrows()
            ],
        })

    with open(f"{OUT}/top_risk_zips.json", "w") as f:
        json.dump(top_zips_list, f, indent=2)

    with open(f"{OUT}/cdc_averages.json", "w") as f:
        json.dump(cdc_avg, f, indent=2)

    # County summary stats
    summary = {
        "total_businesses": int(len(biz)),
        "total_inspections": int(len(insp)),
        "total_red": int((insp["result"] == "R").sum()),
        "total_critical": int((viol["critical"] == True).sum()),
        "total_repeat_offenders": int((biz_full["red_inspections"] >= 2).sum()),
        "temperature_violations": int(viol[(viol["critical"] == True) & (viol["DESCRIPTION"].str.contains("temperature", case=False, na=False))].shape[0]),
        "county_avg_food_insecurity": round(cdc_avg["food_insecurity_pct"], 1),
        "county_avg_diabetes": round(cdc_avg["diabetes_pct"], 1),
    }
    with open(f"{OUT}/county_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"[pipeline] Done. Saved to {OUT}/")
    print(f"  zip_risk_profiles.csv: {len(zip_full)} zips")
    print(f"  business_profiles.csv: {len(biz_full)} businesses")
    print(f"  top_risk_zips.json: {len(top_zips_list)} zips")
    return zip_full, biz_full, top_zips_list, summary

if __name__ == "__main__":
    build()
