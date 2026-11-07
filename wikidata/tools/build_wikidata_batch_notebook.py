"""Builds wikidata/notebooks/wikidata_batch.ipynb.

Usage: python wikidata/tools/build_wikidata_batch_notebook.py wikidata/notebooks/wikidata_batch.ipynb
"""
import json
import os
import sys

# Shared matching rule, pasted into a cell so the notebook stays self-contained
MATCHING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "patterns", "aact_matching.py")
with open(MATCHING_FILE, encoding="utf-8") as f:
    MATCHING_SRC = f.read()


def markdown_cell(text):
    lines = text.strip("\n").split("\n")
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in lines[:-1]] + [lines[-1]]}


def code_cell(text):
    lines = text.strip("\n").split("\n")
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": [l + "\n" for l in lines[:-1]] + [lines[-1]]}


cells = []

cells.append(markdown_cell(r'''
# Wikidata batch: development code statements (P15001)

### What this notebook does

Prepares QuickStatements commands for P15001 "development code" from reviewed codes, each with a reference.
Nothing is sent to Wikidata: the notebook writes a review table and the commands; a person reads the table
and pastes the commands into QuickStatements.

### Inputs

| File | Content |
|------|---------|
| `collections/<collection>_code_evidence.csv` | Harvested codes with review (`use_in_search`, `rule`, `reviewer`) |
| `wikidata/<collection>_code_targets.csv` | Per code: target item, company (P1027), AACT lead sponsor names, status, decision |
| `collections/<collection>.csv` | NCIt concept per INN |

### Rules (`wikidata/README.md`, decisions D0–D8)

- Only rows confirmed by a person in both files; `status` include.
- Every target item and company item is checked live on Wikidata.
- D6: each AACT sponsor name must equal, without legal suffix, the label or an alias (en, mul) of the company item.
- Trial pick: the code as a token (shared rule, `patterns/aact_matching.py`) in `interventions.name` or
  `intervention_other_names.name`, lead sponsor one of the company's names, earliest start date. The value is
  the code as written in that record.
- Without such a trial: NCIt, only if NCIt is a source of the code, the target is the moiety, the INN has one
  NCIt concept, and the concept still carries the code as a synonym (checked live). The value is the code as
  written in NCIt. Otherwise the code is not published.
- Codes already on Wikidata as P15001 (any item, any spelling) are not published again.

### Outputs (`wikidata/output/`, not tracked)

- `<collection>_batch_<run>.csv` — review table, one row per code, with reason for every code not published
- `<collection>_batch_<run>.qs` — QuickStatements V1 commands, `|`-separated

After a batch has been sent, copy both files to `wikidata/batches/` and commit them: that is the record of what
was published from what evidence.
'''))

cells.append(markdown_cell(r'''
## 1. Configuration
'''))

cells.append(code_cell(r'''
import os
from datetime import datetime

from dotenv import dotenv_values

REPO_ROOT = "../.."

# AACT credentials from REPO_ROOT/.env (git-ignored, keys as in .env.example); values are never printed
ENV_FILE = f"{REPO_ROOT}/.env"
assert os.path.isfile(ENV_FILE), f"{ENV_FILE} not found: copy .env.example to .env and fill in the AACT keys"
env = dotenv_values(ENV_FILE)
missing = [k for k in ["AACT_USER", "AACT_PASSWORD"] if not env.get(k)]
assert not missing, f"{ENV_FILE} has no value for: {missing}"
AACT_USER = env["AACT_USER"]
AACT_PASSWORD = env["AACT_PASSWORD"]

AACT_HOST = "aact-db.ctti-clinicaltrials.org"
AACT_PORT = 5432
AACT_DATABASE = "aact"
AACT_SCHEMA = "ctgov"

COLLECTION = "top_sellers_fy2025"
EVIDENCE_FILE = f"{REPO_ROOT}/collections/{COLLECTION}_code_evidence.csv"
TARGETS_FILE = f"{REPO_ROOT}/wikidata/{COLLECTION}_code_targets.csv"
COLLECTION_FILE = f"{REPO_ROOT}/collections/{COLLECTION}.csv"

OUTPUT_DIR = f"{REPO_ROOT}/wikidata/output"
RUN = datetime.now().strftime("%Y%m%d_%H%M")
RUN_DATE = datetime.now().strftime("%Y-%m-%d")   # P813 retrieved

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
NCIT_API = "https://api-evsrest.nci.nih.gov/api/v1"
USER_AGENT = "development-code-archaeology (github.com/kerfors)"

# Reference items (Wikidata)
Q_CLINICALTRIALS_GOV = "Q5133746"
Q_NCI_THESAURUS = "Q19404626"
'''))

cells.append(markdown_cell(r'''
## 2. Setup
'''))

cells.append(code_cell(r'''
import re

import pandas as pd
import psycopg2
import requests
import urllib3.util.connection
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import warnings
warnings.filterwarnings("ignore", message=".*pandas only supports SQLAlchemy.*")

# Force IPv4 for requests: on this Mac the NCI EVS host resolves to IPv6 first, which stalls
# ~20 s per call before falling back (measured 20.5 s vs 0.4 s, 2026-10-14)
urllib3.util.connection.HAS_IPV6 = False

# Retry transient server errors; 404 is not retried
http = requests.Session()
http.headers.update({"User-Agent": USER_AGENT})
http.mount("https://", HTTPAdapter(max_retries=Retry(total=5, backoff_factor=1,
                                                     status_forcelist=[429, 500, 502, 503, 504],
                                                     allowed_methods=["GET"], raise_on_status=False)))

os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_connection():
    return psycopg2.connect(host=AACT_HOST, port=AACT_PORT, database=AACT_DATABASE,
                            user=AACT_USER, password=AACT_PASSWORD,
                            options=f"-c search_path={AACT_SCHEMA}")


def run_query(query, params=None):
    conn = get_connection()
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def sparql(query):
    r = http.get(SPARQL_ENDPOINT, params={"query": query, "format": "json"}, timeout=120)
    r.raise_for_status()
    return [{k: v["value"] for k, v in b.items()} for b in r.json()["results"]["bindings"]]


aact_date = run_query("SELECT max(updated_at)::date AS d FROM studies")["d"].iloc[0]
print(f"Run {RUN}; AACT data updated up to {aact_date}")
'''))

cells.append(markdown_cell(r'''
## 3. Shared matching rule

`patterns/aact_matching.py`, pasted by the builder. Its worked cases run as asserts.
'''))

cells.append(code_cell(MATCHING_SRC))

cells.append(markdown_cell(r'''
## 4. Inputs

Confirmed evidence rows, the reviewed targets, and NCIt concepts per INN.
'''))

cells.append(code_cell(r'''
evidence = pd.read_csv(EVIDENCE_FILE, dtype=str, keep_default_na=False)
confirmed = evidence[(evidence["use_in_search"] == "Y") & (evidence["rule"] == "accept")
                     & (evidence["reviewer"] != "") & (evidence["reviewer"] != "claude-proposed")]

targets = pd.read_csv(TARGETS_FILE, dtype=str, keep_default_na=False)
for col in ["inn", "code_key", "code_class", "level", "target_qid", "target_label", "company_label",
            "company_qid", "lead_sponsor_names", "status", "decision", "reviewer", "note"]:
    assert col in targets.columns, f"{TARGETS_FILE} lacks column '{col}'"
assert targets["code_key"].is_unique, "code_key must be unique in the targets file"
unreviewed = targets[targets["reviewer"].isin(["", "claude-proposed"])]["code_key"].tolist()
assert not unreviewed, f"Targets not confirmed by a person: {unreviewed}"
assert set(targets["status"]) <= {"include", "hold"}, f"Unknown status: {set(targets['status'])}"
assert set(targets["level"]) <= {"moiety", "salt", "combination"}, f"Unknown level: {set(targets['level'])}"
not_confirmed = sorted(set(targets["code_key"]) - set(confirmed["code_key"]))
assert not not_confirmed, f"Targets without a confirmed evidence row: {not_confirmed}"

# Evidence per code: sources and variants (a code key may sit on several INN rows, e.g. a combination code)
ev = confirmed.groupby("code_key").agg(sources=("sources", lambda s: "; ".join(sorted(set("; ".join(s).split("; "))))),
                                       variants=("variants", lambda s: " | ".join(s)),
                                       evidence_inns=("inn", lambda s: "; ".join(sorted(set(s))))).reset_index()

# NCIt concept per single INN (combination rows split into components)
collection = pd.read_csv(COLLECTION_FILE, dtype=str, keep_default_na=False)
ncit_by_inn = {}
for _, r in collection.iterrows():
    inns = [x.strip() for x in r["inn"].split(";")]
    ncits = [x.strip() for x in r["ncit_code"].split(";")]
    assert len(inns) == len(ncits), f"{r['inn']}: inn and ncit_code counts differ"
    for i, n in zip(inns, ncits):
        ncit_by_inn.setdefault(i, set()).add(n)

include = targets[targets["status"] == "include"].merge(ev, on="code_key", how="left")
held = targets[targets["status"] == "hold"]
print(f"Confirmed evidence codes: {confirmed['code_key'].nunique()}; targets: {len(targets)} "
      f"(include {len(include)}, hold {len(held)})")
print("Confirmed codes not in the targets file (held or already on Wikidata, see README):",
      sorted(set(confirmed["code_key"]) - set(targets["code_key"])))
'''))

cells.append(markdown_cell(r'''
## 5. Wikidata checks

Target items: exist, and carry a UNII (P652) or, for a combination, at least a label. Company items: exist, and
every sponsor name in the targets file equals, without legal suffix, the label or an alias (en, mul) of the
company item (D6). A failed check stops the notebook: fix the targets file, do not work around it here.
'''))

cells.append(code_cell(r'''
def values_clause(qids):
    return " ".join(f"wd:{q}" for q in sorted(set(qids)))


item_rows = sparql(f"""SELECT ?item ?label ?unii WHERE {{
  VALUES ?item {{ {values_clause(include['target_qid'])} }}
  OPTIONAL {{ ?item rdfs:label ?label FILTER(LANG(?label) IN ("en","mul")) }}
  OPTIONAL {{ ?item wdt:P652 ?unii }} }}""")
items = {}
for b in item_rows:
    q = b["item"].rsplit("/", 1)[1]
    d = items.setdefault(q, {"labels": set(), "uniis": set()})
    if "label" in b:
        d["labels"].add(b["label"])
    if "unii" in b:
        d["uniis"].add(b["unii"])
no_label = sorted(q for q in set(include["target_qid"]) if not items.get(q, {}).get("labels"))
assert not no_label, f"Target items without label (missing or redirected?): {no_label}"
no_unii = sorted(set(include.loc[include["level"] != "combination", "target_qid"])
                 - {q for q, d in items.items() if d["uniis"]})
assert not no_unii, f"Moiety or salt targets without UNII: {no_unii}"

name_rows = sparql(f"""SELECT ?item ?name WHERE {{
  VALUES ?item {{ {values_clause(include['company_qid'])} }}
  {{ ?item rdfs:label ?name }} UNION {{ ?item skos:altLabel ?name }}
  FILTER(LANG(?name) IN ("en","mul")) }}""")
company_names = {}
for b in name_rows:
    company_names.setdefault(b["item"].rsplit("/", 1)[1], set()).add(b["name"])

LEGAL_SUFFIX = re.compile(r"[,\s]+(inc|llc|l\.l\.c|ltd|limited|co|corp|corporation|plc|a/s|ag|gmbh|s\.a|n\.v)\.?$",
                          re.I)


def core_name(name):
    """Name without trailing legal-form suffixes, lower case: 'Ono Pharmaceutical Co., Ltd.' -> 'ono pharmaceutical'."""
    s = name.strip()
    while True:
        t = LEGAL_SUFFIX.sub("", s).strip()
        if t == s:
            return s.lower()
        s = t


d6_fail = []
for _, r in include.iterrows():
    cores = {core_name(n) for n in company_names.get(r["company_qid"], set())}
    assert cores, f"{r['code_key']}: company item {r['company_qid']} has no label or alias"
    for sponsor in [s.strip() for s in r["lead_sponsor_names"].split(";") if s.strip()]:
        if core_name(sponsor) not in cores:
            d6_fail.append((r["code_key"], sponsor, r["company_qid"]))
assert not d6_fail, f"D6: sponsor names not matching label or alias of the company item: {d6_fail}"
print(f"Target items checked: {len(items)}; company items checked: {len(company_names)}; D6 passed")
'''))

cells.append(markdown_cell(r'''
## 6. Trial pick (ClinicalTrials.gov reference)

Per code: trials whose intervention name or other name contains the code as a token, with a lead sponsor from
the company's names; the earliest start date wins (ties: lowest NCT ID). The value is the token as written in
that record. Codes without sponsor names in the targets file have no trial pick.
'''))

cells.append(code_cell(r'''
PICK_SQL = """
SELECT s.nct_id, s.start_date, sp.name AS lead_sponsor, x.field AS matched_field, x.value AS matched_value
FROM studies s
JOIN sponsors sp ON sp.nct_id = s.nct_id AND sp.lead_or_collaborator = 'lead' AND sp.name = ANY(%s)
JOIN (SELECT nct_id, 'interventions.name' AS field, name AS value FROM interventions
      UNION ALL
      SELECT nct_id, 'intervention_other_names.name' AS field, name AS value FROM intervention_other_names) x
  ON x.nct_id = s.nct_id
WHERE x.value ~* %s
ORDER BY s.start_date NULLS LAST, s.nct_id
"""


def code_regex(r):
    # Variants as harvested; surrounding parentheses removed ("(BMS-188667)" -> "BMS-188667")
    variants = [v.strip().strip("()").strip() for v in str(r["variants"]).split("|")]
    return token_regex(r["code_key"], *[v for v in variants if v])


VALUE_FORM = re.compile(r"[A-Za-z0-9][A-Za-z0-9 \-/.]*[A-Za-z0-9]")


def checked_value(code_key, value):
    assert VALUE_FORM.fullmatch(value), f"{code_key}: value '{value}' is not a bare code"
    assert match_key(value) == match_key(code_key), f"{code_key}: value '{value}' has another match key"
    return value


picks = {}
for _, r in include.iterrows():
    sponsors = [s.strip() for s in r["lead_sponsor_names"].split(";") if s.strip()]
    if not sponsors:
        continue
    rx = code_regex(r)
    df = run_query(PICK_SQL, (sponsors, rx))
    df = df[~df["matched_value"].map(lambda v: is_excluded(r["code_key"], v))]
    if len(df):
        top = df.iloc[0]
        value = checked_value(r["code_key"], re.search(rx, top["matched_value"], re.I).group(2))
        picks[r["code_key"]] = {"nct_id": top["nct_id"], "start_date": str(top["start_date"]),
                                "lead_sponsor": top["lead_sponsor"], "matched_field": top["matched_field"],
                                "matched_value": top["matched_value"], "value": value,
                                "n_trials": df["nct_id"].nunique()}
print(f"Trial picks: {len(picks)} of {len(include)} codes")
'''))

cells.append(markdown_cell(r'''
## 7. NCIt fallback

For codes without a trial pick: only if NCIt is a source of the code, the target level is the moiety, the INN
has one NCIt concept, and that concept's FDA UNII is a UNII of the target item (so a salt concept is not used for
a moiety item). The concept is read live; the value is the code as written in its synonyms.
If NCIt writes the code in more than one spelling: NCIT_MULTIPLE = "hold" (default) does not publish the code;
NCIT_MULTIPLE = "CN" uses the one spelling with NCIt term type CN (drug study code, NCIt C45773), and holds the
code if there is not exactly one. The term types of all matching spellings are shown in the reason.
'''))

cells.append(code_cell(r'''
NCIT_MULTIPLE = "hold"   # "hold" or "CN"
assert NCIT_MULTIPLE in ("hold", "CN")


def ncit_concept(ncit_code):
    """Synonyms as (name, termType) and FDA UNII codes (property FDA_UNII_Code, NCIT_P319) of one NCIt concept."""
    r = http.get(f"{NCIT_API}/concept/ncit/{ncit_code}", params={"include": "synonyms,properties"}, timeout=60)
    r.raise_for_status()
    c = r.json()
    return ([(s["name"], s.get("termType", "")) for s in c.get("synonyms", [])],
            {p["value"] for p in c.get("properties", []) if p["type"] == "FDA_UNII_Code"})


ncit_refs, ncit_reasons = {}, {}
for _, r in include.iterrows():
    k = r["code_key"]
    if k in picks:
        continue
    if "NCIt" not in r["sources"].split("; "):
        ncit_reasons[k] = "no trial pick; NCIt not a source"
        continue
    if r["level"] != "moiety":
        ncit_reasons[k] = f"no trial pick; NCIt fallback only for moiety targets (level {r['level']})"
        continue
    concepts = sorted(ncit_by_inn.get(r["inn"], set()))
    if len(concepts) != 1:
        ncit_reasons[k] = f"no trial pick; INN has {len(concepts)} NCIt concepts"
        continue
    synonyms, concept_uniis = ncit_concept(concepts[0])
    if not concept_uniis & items[r["target_qid"]]["uniis"]:
        ncit_reasons[k] = (f"no trial pick; NCIt {concepts[0]} UNII {sorted(concept_uniis)} is not a UNII of "
                           f"{r['target_qid']} {sorted(items[r['target_qid']]['uniis'])}")
        continue
    rx = code_regex(r)
    hits = sorted({(m.group(2), tt) for s, tt in synonyms for m in [re.search(rx, s, re.I)] if m})
    spellings = sorted({v for v, _ in hits})
    cn = sorted({v for v, tt in hits if tt == "CN"})
    if not spellings:
        ncit_reasons[k] = f"no trial pick; code not a synonym of NCIt {concepts[0]} today"
    elif len(spellings) > 1 and (NCIT_MULTIPLE == "hold" or len(cn) != 1):
        ncit_reasons[k] = f"no trial pick; NCIt {concepts[0]} has several spellings (term types): {hits}"
    else:
        value = spellings[0] if len(spellings) == 1 else cn[0]
        ncit_refs[k] = {"ncit_code": concepts[0], "value": checked_value(k, value)}
print(f"NCIt references: {len(ncit_refs)}; not published after fallback: {len(ncit_reasons)}")
'''))

cells.append(markdown_cell(r'''
## 8. Already on Wikidata

All P15001 statements, compared by match key (spelling-insensitive). A code already present on any item is not
published again.
'''))

cells.append(code_cell(r'''
existing = {}
for b in sparql("SELECT ?item ?v WHERE { ?item wdt:P15001 ?v }"):
    existing.setdefault(match_key(b["v"]), []).append((b["item"].rsplit("/", 1)[1], b["v"]))
print(f"P15001 statements on Wikidata: {sum(len(v) for v in existing.values())}")
'''))

cells.append(markdown_cell(r'''
## 9. Review table and QuickStatements

One row per code in the targets file. `result` is `publish`, `not published` or `hold`; `reason` says why.
Read the table before pasting the commands.
'''))

cells.append(code_cell(r'''
def qs_date(d):
    return f"+{d}T00:00:00Z/11"


rows, commands = [], []
for _, r in targets.iterrows():
    k = r["code_key"]
    row = {"code_key": k, "inn": r["inn"], "level": r["level"], "target_qid": r["target_qid"],
           "target_label": r["target_label"], "company_qid": r["company_qid"], "company_label": r["company_label"],
           "decision": r["decision"], "value": "", "reference": "", "nct_id": "", "start_date": "",
           "lead_sponsor": "", "matched_field": "", "matched_value": "", "n_trials": "", "ncit_code": "",
           "result": "", "reason": ""}
    if r["status"] == "hold":
        row.update(result="hold", reason=f"held ({r['decision']}): {r['note']}")
    elif match_key(k) in existing:
        row.update(result="not published", reason=f"already on Wikidata: {existing[match_key(k)]}")
    elif k in picks:
        p = picks[k]
        row.update(value=p["value"], reference="ClinicalTrials.gov", nct_id=p["nct_id"], start_date=p["start_date"],
                   lead_sponsor=p["lead_sponsor"], matched_field=p["matched_field"],
                   matched_value=p["matched_value"], n_trials=p["n_trials"], result="publish")
        commands.append(f'{r["target_qid"]}|P15001|"{p["value"]}"|P1027|{r["company_qid"]}'
                        f'|S248|{Q_CLINICALTRIALS_GOV}|S3098|"{p["nct_id"]}"|S813|{qs_date(RUN_DATE)}')
    elif k in ncit_refs:
        n = ncit_refs[k]
        row.update(value=n["value"], reference="NCI Thesaurus", ncit_code=n["ncit_code"], result="publish")
        commands.append(f'{r["target_qid"]}|P15001|"{n["value"]}"|P1027|{r["company_qid"]}'
                        f'|S248|{Q_NCI_THESAURUS}|S1748|"{n["ncit_code"]}"|S813|{qs_date(RUN_DATE)}')
    else:
        row.update(result="not published", reason=ncit_reasons[k])
    rows.append(row)

review = pd.DataFrame(rows)
quoted = [v for v in review["value"] if '"' in v]
assert not quoted, f"Values containing a quote: {quoted}"
review_file = f"{OUTPUT_DIR}/{COLLECTION}_batch_{RUN}.csv"
qs_file = f"{OUTPUT_DIR}/{COLLECTION}_batch_{RUN}.qs"
review.to_csv(review_file, index=False)
with open(qs_file, "w", encoding="utf-8") as f:
    f.write("\n".join(commands) + "\n")

print(review["result"].value_counts().to_string())
print(f"\nReview table: {review_file}\nCommands ({len(commands)}): {qs_file}")
pd.set_option("display.max_colwidth", 60)
review[["code_key", "target_qid", "value", "reference", "nct_id", "start_date", "lead_sponsor", "ncit_code",
        "result", "reason"]]
'''))

cells.append(code_cell(r'''
print("\n".join(commands))
'''))

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
for i, c in enumerate(nb["cells"]):
    c["id"] = f"cell-{i:02d}"

with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print("written", sys.argv[1], len(cells), "cells")
