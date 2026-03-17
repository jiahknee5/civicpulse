"""Pre-compute agent outputs for top risk zips so demo is instant."""
import json
import os
from agents import run_full_pipeline

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

with open(os.path.join(DATA_DIR, "top_risk_zips.json")) as f:
    top_zips = json.load(f)
with open(os.path.join(DATA_DIR, "county_summary.json")) as f:
    summary = json.load(f)
with open(os.path.join(DATA_DIR, "cdc_averages.json")) as f:
    cdc_avg = json.load(f)

# Pre-compute for top 3 flagged zips
precomputed = {}
for z in top_zips[:3]:
    if z["risk_score"] >= 70:
        print(f"\n{'='*60}")
        print(f"  Pre-computing for ZIP {z['zip']}...")
        print(f"{'='*60}")
        result = run_full_pipeline(z, summary, cdc_avg)
        precomputed[z["zip"]] = result
        print(f"  Done. Status: {result['status']}")

out_path = os.path.join(DATA_DIR, "precomputed_outputs.json")
with open(out_path, "w") as f:
    json.dump(precomputed, f, indent=2)

print(f"\nSaved {len(precomputed)} pre-computed outputs to {out_path}")
