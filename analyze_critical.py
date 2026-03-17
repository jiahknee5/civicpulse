import pandas as pd
import os

DATA = os.path.expanduser("~/data")
viol = pd.read_csv(f"{DATA}/SCC_DEH_Food_Data_VIOLATIONS_20260306.csv")

print(f"Total rows: {len(viol):,}")
print(f"Critical dtype: {viol['critical'].dtype}")
print(f"Critical unique: {viol['critical'].unique()}")
print(f"Critical value_counts:")
print(viol["critical"].value_counts())

# Match as bool (pandas reads true/false as bool)
crit = viol[viol["critical"] == True].copy()
if len(crit) == 0:
    crit = viol[viol["critical"].astype(str).str.strip().str.lower() == "true"].copy()
print(f"\nCritical violations: {len(crit):,}")

print(f"\n=== DESCRIPTION (violation type) histogram ===")
desc_counts = crit["DESCRIPTION"].value_counts()
for k, v in desc_counts.items():
    bar = "#" * (v // 20)
    print(f"  {v:>5,}  {k[:70]}")
    print(f"         {bar}")

print(f"\n=== violation_comment fill rate ===")
print(f"  Non-null: {crit['violation_comment'].notna().sum():,} / {len(crit):,}")

print(f"\n=== Sample violation_comments (first 30) ===")
samples = crit[crit["violation_comment"].notna()].head(30)
for _, row in samples.iterrows():
    desc = str(row["DESCRIPTION"])[:35].ljust(35)
    comment = str(row["violation_comment"])[:150]
    print(f"  [{desc}] {comment}")

print(f"\n=== violation_comment length stats ===")
lens = crit["violation_comment"].dropna().str.len()
print(f"  Mean: {lens.mean():.0f}, Median: {lens.median():.0f}, Max: {lens.max():.0f}")
