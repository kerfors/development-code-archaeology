"""Derive the small figure tables a post needs from a trial archaeology run.

The run outputs (trials_verification_<collection>_<timestamp>.csv) are not tracked. This script reduces one run
to small CSVs in site/data/<run_id>/, which are tracked, so a post's figures stay fixed when later runs come.

Usage: python derive_figures.py <run_id> <collection>=<trials_verification csv> [<collection>=<csv> ...]
Example: python derive_figures.py ta_20261016 fda_novel_2025=../../.../trials_verification_fda_novel_2025_20261016_1010.csv
"""
import os
import sys

import pandas as pd

RUN_ID = sys.argv[1]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", RUN_ID)
os.makedirs(OUT, exist_ok=True)

PHASES = {"PHASE1": "Phase 1", "PHASE1/PHASE2": "Phase 1/2", "PHASE2": "Phase 2", "PHASE3": "Phase 3",
          "PHASE4": "Phase 4"}
PERIODS = [(1989, 2009, "before 2010"), (2010, 2014, "2010–2014"), (2015, 2019, "2015–2019"),
           (2020, 2099, "2020 and later")]

totals, per_drug, by_phase, by_start = [], [], [], []
for arg in sys.argv[2:]:
    collection, path = arg.split("=", 1)
    d = pd.read_csv(path, dtype=str, keep_default_na=False)
    for col in ["nct_id", "INN", "Found_via_INN", "INN_in_Title", "phase", "start_date"]:
        assert col in d.columns, f"{path} lacks column {col}"
    d["hidden"] = d["Found_via_INN"] != "True"
    h = d[d["hidden"]]
    totals.append({"collection": collection, "source_file": os.path.basename(path), "pairs": len(d),
                   "distinct_trials": d["nct_id"].nunique(), "hidden": int(d["hidden"].sum()),
                   "hidden_distinct": h["nct_id"].nunique(),
                   "hidden_inn_in_no_title": int((h["INN_in_Title"] != "True").sum()),
                   "drugs": d["INN"].nunique(), "drugs_with_hidden": int(d.groupby("INN")["hidden"].any().sum())})
    for inn, g in d.groupby("INN"):
        per_drug.append({"collection": collection, "inn": inn, "pairs": len(g), "hidden": int(g["hidden"].sum())})
    for code, label in PHASES.items():
        g = d[d["phase"] == code]
        by_phase.append({"collection": collection, "phase": label, "pairs": len(g), "hidden": int(g["hidden"].sum())})
    year = pd.to_numeric(d["start_date"].str[:4], errors="coerce")
    for lo, hi, label in PERIODS:
        g = d[(year >= lo) & (year <= hi)]
        by_start.append({"collection": collection, "period": label, "pairs": len(g), "hidden": int(g["hidden"].sum())})

for name, rows in [("totals", totals), ("per_drug", per_drug), ("by_phase", by_phase), ("by_start", by_start)]:
    pd.DataFrame(rows).to_csv(os.path.join(OUT, f"{name}.csv"), index=False)
print(pd.DataFrame(totals).to_string(index=False))
print("written to", OUT)
