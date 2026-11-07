import hashlib
import json
import os
import sys

# Shared matching rule, pasted into a cell so the notebook stays self-contained
MATCHING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "patterns", "aact_matching.py")
with open(MATCHING_FILE, encoding="utf-8") as f:
    MATCHING_SRC = f.read()
RULE_HASH = hashlib.sha1(MATCHING_SRC.encode("utf-8")).hexdigest()[:8]


def markdown_cell(text):
    lines = text.strip("\n").split("\n")
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in lines[:-1]] + [lines[-1]]}


def code_cell(text):
    lines = text.strip("\n").split("\n")
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": [l + "\n" for l in lines[:-1]] + [lines[-1]]}


cells = []

cells.append(markdown_cell(r'''
# Development Code Harvest
## Sourced candidate codes for a drug collection — with registry evidence

### Why this notebook exists

The 2025 FDA collection used an AI discovery prompt followed by human verification. That works, but the
provenance of each code lives in someone's head. This notebook reverses the order:

1. **Harvest** candidate codes only from named sources — never generated
2. **Collect evidence** from ClinicalTrials.gov (AACT) for every candidate
3. **Human review** classifies each candidate in a review file kept in the repo
4. **Export** accepted codes in the format the trial archaeology notebook reads

### Sources

| Source | What it gives | Known weakness |
|--------|---------------|----------------|
| NCI Thesaurus (EVS REST API) | Curated synonyms incl. development codes | Merges biosimilar codes into the originator concept (labelled "X Biosimilar CODE") |
| PubChem synonyms (PUG REST) | Depositor synonyms for small molecules and peptides | Vendor catalogue numbers, depositor typos (e.g. GSK685968 vs GSK685698) |
| AACT `intervention_other_names` | What sponsors actually registered | Other drugs of combination trials attached to the wrong intervention; typos; NCI CTRP copies NCIt synonyms into NCI-sponsored records, so not independent of NCIt for oncology |
| AACT `interventions.name`, code extensions | Registered intervention names that extend a candidate code with a letter suffix (ONO-4538 → ONO-4538HSC): other formulations and products, often in records that name neither the INN nor the parent code | Extends every candidate, also `other_drug` ones; counts as `Registry`, not as an evidence line of its own |
| Web (LLM-assisted, `collections/<COLLECTION>_web_candidates.csv`) | Combination-product, originator and partner codes from press releases, protocols, regulatory documents | Every code must cite the URL where it was seen; same registry evidence and review as the other sources |

### Inputs and outputs

- **Input:** `collections/<COLLECTION>.csv` — one row per brand, column `inn` (`; `-separated for combinations) and `ncit_code`
- **Sponsor column:** `SPONSOR_COLUMN` in section 1, per collection (top_sellers_fy2025: `company`; fda_novel_2025: `sponsor`)
- **Excluded brands:** `EXCLUDE_BRANDS` in section 1, per collection, with the reason (fda_novel_2025: Kygevvi)
- **Input (optional):** `collections/<COLLECTION>_code_review.csv` — human review decisions
- **Input (optional):** `collections/<COLLECTION>_web_candidates.csv` — URL-cited web candidates
- **Output:** `collections/<COLLECTION>_code_evidence.csv` — one row per INN × candidate code, with sources, evidence and review class
- **Output:** `collections/<COLLECTION>_review_exceptions.csv` — rows where review decision and acceptance rule disagree
- **Output:** `collections/<COLLECTION>_codes.csv` — accepted codes per brand, in trial-archaeology format
- **Output:** `collections/<COLLECTION>_moiety_codes.csv` — accepted codes per active moiety, the unit of trial search
- **Working files (not tracked):** `code_harvest/output/<COLLECTION>_aact_evidence_cache_<rule hash>.csv`,
  `code_harvest/output/<COLLECTION>_pubchem_set_aside.csv`
'''))

cells.append(markdown_cell("## 1. Configuration"))

cells.append(code_cell(r'''
import os

from dotenv import dotenv_values

COLLECTION = "top_sellers_fy2025"
REPO_ROOT = "../.."

# Column holding the company/sponsor per brand; collections name it differently
SPONSOR_COLUMN = {"top_sellers_fy2025": "company", "fda_novel_2025": "sponsor"}

# Brands left out of the harvest, per collection. They stay in the collection file (trial archaeology uses it).
# fda_novel_2025 Kygevvi: combination of two nucleosides; its only code MT-1621 names the combination (KF 2026-11-07)
EXCLUDE_BRANDS = {"fda_novel_2025": ["Kygevvi"]}

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

NCIT_API = "https://api-evsrest.nci.nih.gov/api/v1"
PUBCHEM_API = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

# Cache of AACT evidence per code key (slow regex scans) — delete file to force refresh.
# Suffix = first 8 hex of SHA-1 of patterns/aact_matching.py, set by the builder: a rule change starts a new cache.
EVIDENCE_CACHE = f"{REPO_ROOT}/code_harvest/output/{COLLECTION}_aact_evidence_cache_RULE_HASH.csv"
PATTERNS_FILE = f"{REPO_ROOT}/patterns/study_code_patterns.csv"
'''))

cells.append(markdown_cell("## 2. Setup"))

cells.append(code_cell(r'''
import os
import re
import time
from datetime import datetime

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

# Retry transient server errors (NCI EVS returned sporadic 500s, 2026-10-14); 404 is not retried
http = requests.Session()
http.mount("https://", HTTPAdapter(max_retries=Retry(total=5, backoff_factor=1,
                                                     status_forcelist=[429, 500, 502, 503, 504],
                                                     allowed_methods=["GET"], raise_on_status=False)))

os.makedirs(f"{REPO_ROOT}/code_harvest/output", exist_ok=True)

collection = pd.read_csv(f"{REPO_ROOT}/collections/{COLLECTION}.csv", dtype=str)
for col in ["brand", "inn", "ncit_code", SPONSOR_COLUMN[COLLECTION]]:
    assert col in collection.columns, f"Collection file lacks column '{col}'"
excluded = EXCLUDE_BRANDS.get(COLLECTION, [])
unknown = [b for b in excluded if b not in set(collection["brand"])]
assert not unknown, f"EXCLUDE_BRANDS not in {COLLECTION}.csv: {unknown}"
collection = collection[~collection["brand"].isin(excluded)].reset_index(drop=True)

# One row per (INN, NCIt code) — combinations split into components
inn_rows = []
for _, r in collection.iterrows():
    inns = [x.strip() for x in r["inn"].split(";")]
    ncits = [x.strip() for x in r["ncit_code"].split(";")]
    assert len(inns) == len(ncits), f"{r['brand']}: inn and ncit_code counts differ"
    inn_rows.extend(zip(inns, ncits))
inns = pd.DataFrame(sorted(set(inn_rows)), columns=["inn", "ncit_code"])

print(f"Harvest started: {datetime.now():%Y-%m-%d %H:%M}")
print(f"Collection: {COLLECTION} — {len(collection)} rows, {collection['brand'].nunique()} brands, {len(inns)} active moieties")
'''))

cells.append(markdown_cell(r'''
## 3. Code-likeness and normalisation

A development code here is: 1–6 letters, optional separator, at least two digits, short optional suffix.
The **code key** removes case, spaces, hyphens and brackets so `MK-3475`, `MK 3475` and `MK3475` group together.
Original spellings are kept as `variants` — formats are never normalised in the published data.
'''))

cells.append(code_cell(r'''
CODE_PATTERN = re.compile(r"^\(?[-+]?\)?-?[A-Za-z]{1,6}[\s-]?\d{2,}[A-Za-z0-9\s-]{0,8}\)?$")
ATC_PATTERN = re.compile(r"^[A-Z]\d{2}[A-Z]{2}\d{2}$")
# Registry other names also carry doses, placebo labels, molecular formulas and ATC codes
NOISE_PATTERN = re.compile(r"\d\s*(mg|mcg|µg|ug|ml|iu)\b|placebo|^C\d+H\d+|^ATC\b", re.IGNORECASE)


def is_code_like(s, inn):
    s = s.strip()
    if inn.split()[0].lower() in s.lower():
        return False
    if NOISE_PATTERN.search(s):
        return False
    return bool(CODE_PATTERN.match(s)) and not ATC_PATTERN.match(code_key(s))


def code_key(s):
    return re.sub(r"[\s\-()+]", "", s).upper()


assert code_key("MK-3475") == code_key("MK 3475") == code_key("(MK3475)") == "MK3475"
assert not is_code_like("J05AX12", "dolutegravir")
assert is_code_like("GSK 573719A", "umeclidinium")
assert not is_code_like("AIN457 300 mg", "secukinumab")
assert not is_code_like("LEE011 Placebo", "ribociclib")
assert not is_code_like("C27H32F2N8", "abemaciclib")
assert not is_code_like("B01A F02", "apixaban")
'''))

cells.append(markdown_cell(r'''
## 4. Harvest — NCI Thesaurus

Fetched by NCIt concept code from the collection file (not by name search), so the concept is fixed.
Synonyms of the form `<INN> Biosimilar <CODE>` mark the code as a biosimilar of another company.
'''))

cells.append(code_cell(r'''
def ncit_synonyms(ncit_code):
    r = http.get(f"{NCIT_API}/concept/ncit/{ncit_code}", params={"include": "synonyms"}, timeout=60)
    r.raise_for_status()
    return sorted({s["name"] for s in r.json()["synonyms"]})


ncit_records = []
for _, r in inns.iterrows():
    syns = ncit_synonyms(r["ncit_code"])
    biosimilar_keys = {code_key(m.group(1)) for s in syns
                       if (m := re.match(r".*Biosimilar\s+(.+)$", s, flags=re.IGNORECASE))}
    for s in syns:
        if is_code_like(s, r["inn"]):
            ncit_records.append({"inn": r["inn"], "variant": s, "source": "NCIt",
                                 "ncit_biosimilar": code_key(s) in biosimilar_keys})
    time.sleep(0.2)

ncit_df = pd.DataFrame(ncit_records)
print(f"NCIt: {len(ncit_df)} code-like synonyms, {ncit_df['ncit_biosimilar'].sum()} flagged biosimilar")
'''))

cells.append(markdown_cell(r'''
## 5. Harvest — PubChem synonyms

Looked up by INN; only the first CID is used. Monoclonal antibodies and fusion proteins are normally not
PubChem compounds — a 404 is recorded, not an error.
'''))

cells.append(code_cell(r'''
pubchem_records = []
pubchem_cids = {}
for inn in inns["inn"]:
    r = http.get(f"{PUBCHEM_API}/compound/name/{inn}/cids/JSON", timeout=60)
    if r.status_code == 404:
        pubchem_cids[inn] = None
        continue
    r.raise_for_status()
    cid = r.json()["IdentifierList"]["CID"][0]
    pubchem_cids[inn] = cid
    s = http.get(f"{PUBCHEM_API}/compound/cid/{cid}/synonyms/JSON", timeout=60)
    s.raise_for_status()
    for syn in s.json()["InformationList"]["Information"][0]["Synonym"]:
        if is_code_like(syn, inn):
            pubchem_records.append({"inn": inn, "variant": syn, "source": "PubChem"})
    time.sleep(0.3)

pubchem_df = pd.DataFrame(pubchem_records)
print(f"PubChem: CID found for {sum(v is not None for v in pubchem_cids.values())} of {len(inns)}; "
      f"{len(pubchem_df)} code-like synonyms")
'''))

cells.append(markdown_cell(r'''
## 5b. Sponsor prefixes — Wikipedia

"List of pharmaceutical compound number prefixes" (wikitext via the MediaWiki API). Used to (a) annotate each
candidate with the company the prefix belongs to and (b) keep PubChem-only candidates whose prefix is a known
sponsor prefix. Single-letter prefixes are ignored for both — they collide with KEGG IDs (D00400) and formulas.

The list is incomplete: RGH (Gedeon Richter), NN (Novo Nordisk) and FX (FoldRx) are missing as of October 2026.
'''))

cells.append(code_cell(r'''
WIKI_PAGE = "List of pharmaceutical compound number prefixes"
r = http.get("https://en.wikipedia.org/w/api.php",
                 params={"action": "parse", "page": WIKI_PAGE, "prop": "wikitext|revid", "format": "json", "formatversion": 2},
                 headers={"User-Agent": "development-code-archaeology (github.com/kerfors)"}, timeout=60)
r.raise_for_status()
wikitext = r.json()["parse"]["wikitext"]
wiki_revid = r.json()["parse"]["revid"]


def wiki_clean(s):
    s = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", s)
    s = re.sub(r"\[\[([^|\]]*\|)?([^\]]*)\]\]", r"\2", s)
    s = re.sub(r"\{\{.*?\}\}", "", s)
    return s.strip()


prefix_rows = []
for line in wikitext.splitlines():
    m = re.match(r"^\*\s*([^–—]+?)\s*[–—-]\s+(.*)$", line)
    if not m:
        continue
    for p in re.split(r"[,/]| or ", m.group(1)):
        p = wiki_clean(p).strip(" '")
        if re.fullmatch(r"[A-Za-z]{2,6}", p):
            prefix_rows.append((p.upper(), wiki_clean(m.group(2))))
prefixes = (pd.DataFrame(prefix_rows, columns=["prefix", "company"])
            .groupby("prefix")["company"].apply(lambda x: " / ".join(x)).to_dict())
print(f"Wikipedia revision {wiki_revid}: {len(prefixes)} prefixes (2–6 letters)")


def code_prefix(key):
    return re.match(r"[A-Z]*", key).group(0)
'''))

cells.append(markdown_cell(r'''
## 6. Harvest — AACT intervention other names

Other names registered on interventions whose name contains the INN.
`intervention_other_names` joins via `intervention_id`, not `nct_id`.
'''))

cells.append(code_cell(r'''
def run_query(query, params=None):
    conn = psycopg2.connect(host=AACT_HOST, port=AACT_PORT, database=AACT_DATABASE,
                            user=AACT_USER, password=AACT_PASSWORD,
                            options=f"-c search_path={AACT_SCHEMA}")
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


print(run_query("SELECT COUNT(*) AS studies, MAX(updated_at) AS last_update FROM studies"))

aact_on = run_query("""
    SELECT inn.n AS inn, o.name AS variant, COUNT(DISTINCT i.nct_id) AS othername_trials
    FROM (SELECT unnest(%s) AS n) inn
    JOIN interventions i ON LOWER(i.name) LIKE '%%' || inn.n || '%%'
    JOIN intervention_other_names o ON o.intervention_id = i.id
    GROUP BY inn.n, o.name
""", (list(inns["inn"].str.lower()),))

aact_on = aact_on[aact_on.apply(lambda r: is_code_like(r["variant"], r["inn"]), axis=1)].copy()
aact_on["source"] = "AACT"
print(f"AACT other names: {len(aact_on)} code-like (variant, INN) pairs")
'''))

cells.append(markdown_cell(r'''
## 7. Candidate table

One row per INN × code key. All spellings and sources retained.
'''))

cells.append(code_cell(r'''
# Fourth source: LLM-assisted web discovery — every code carries the URL where it was seen
WEB_FILE = f"{REPO_ROOT}/collections/{COLLECTION}_web_candidates.csv"
web_df = pd.DataFrame(columns=["inn", "variant", "source", "web_url"])
if os.path.exists(WEB_FILE):
    web_df = pd.read_csv(WEB_FILE, dtype=str)
    web_df = web_df.assign(inn=web_df["inn"].str.split(";")).explode("inn")   # combination codes → each component
    web_df["inn"] = web_df["inn"].str.strip()
    web_df = web_df.rename(columns={"code": "variant", "url": "web_url"})[["inn", "variant", "web_url"]]
    web_df["source"] = "Web"
    unknown = set(web_df["inn"]) - set(inns["inn"])
    assert not unknown, f"Web candidates for INNs not in the collection: {unknown}"
print(f"Web (LLM-assisted, URL-cited): {len(web_df)} rows")

raw = pd.concat([ncit_df, pubchem_df, aact_on, web_df], ignore_index=True)
raw["code_key"] = raw["variant"].map(code_key)

# Fifth source: interventions.name extending a candidate code with a letter suffix (ONO-4538 -> ONO-4538HSC).
# Reaches records that name neither the INN nor the parent code as a token. Parents: every candidate except
# PubChem-only ones; one regex scan of interventions.name for all parents together.
def spelling_rx(v):
    return "[- ]?".join(re.escape(p) for p in re.split(r"[-\s]+", v.strip().strip("()")))


parents = raw[raw["source"] != "PubChem"].groupby(["inn", "code_key"])["variant"].apply(set)
parent_rx = {k: "|".join(sorted({spelling_rx(v) for v in vs})) for k, vs in parents.items()}
ext_names = run_query("SELECT name, COUNT(DISTINCT nct_id) AS trials FROM interventions WHERE name ~* %s GROUP BY name",
                      (r"(^|[^a-z0-9])(" + "|".join(sorted(set(parent_rx.values()))) + r")[a-z]",))
ext_records = []
for (inn_, key), rx in parent_rx.items():
    hit = ext_names["name"].str.contains(r"(?:^|[^a-z0-9])(?:" + rx + r")[a-z]", case=False, regex=True)
    for name in ext_names.loc[hit, "name"]:
        for frag in re.split(r"[()\[\],;/+:]", name):
            frag = frag.strip(" .-")
            if frag and is_code_like(frag, inn_) and code_key(frag) != key and code_key(frag).startswith(key):
                ext_records.append({"inn": inn_, "variant": frag, "source": "AACT-name"})
ext_df = pd.DataFrame(ext_records, columns=["inn", "variant", "source"]).drop_duplicates()
ext_df["code_key"] = ext_df["variant"].map(code_key)
print(f"AACT intervention-name extensions: {len(ext_df)} (variant, INN) rows")
raw = pd.concat([raw, ext_df], ignore_index=True)

cand = (raw.groupby(["inn", "code_key"])
        .agg(variants=("variant", lambda x: " | ".join(sorted(set(x)))),
             sources=("source", lambda x: "; ".join(sorted(set(x)))),
             ncit_biosimilar=("ncit_biosimilar", lambda x: bool(x.fillna(False).any())),
             othername_trials=("othername_trials", "max"),
             web_urls=("web_url", lambda x: " | ".join(sorted(set(x.dropna())))))
        .reset_index())
cand["othername_trials"] = cand["othername_trials"].fillna(0).astype(int)
cand["prefix_company_wikipedia"] = cand["code_key"].map(lambda k: prefixes.get(code_prefix(k), ""))

# PubChem-only candidates need a known sponsor prefix; the rest are set aside (database IDs, vendor numbers)
pubchem_only = cand["sources"] == "PubChem"
set_aside = cand[pubchem_only & (cand["prefix_company_wikipedia"] == "")]
set_aside.to_csv(f"{REPO_ROOT}/code_harvest/output/{COLLECTION}_pubchem_set_aside.csv", index=False)
cand = cand[~(pubchem_only & (cand["prefix_company_wikipedia"] == ""))].reset_index(drop=True)

print(f"Candidates: {len(cand)} (INN × code key); PubChem-only set aside: {len(set_aside)}")
print(cand["sources"].value_counts().to_string())
'''))

cells.append(markdown_cell(r'''
## 8. Registry evidence per candidate

For each candidate: trials where any of its spellings appears under the shared matching rule
(`patterns/aact_matching.py`, pasted below — do not edit the cell here): the code as a token in
`interventions.name`, `intervention_other_names.name`, `studies.official_title`, `studies.brief_title` or
`id_information.id_value`, plus ruled study-code patterns. Also: how many of those trials name the INN in
`interventions.name`, and the most frequent lead sponsors.

Slow (one regex scan per field and candidate) — results cached in `code_harvest/output/`.
'''))

cells.append(code_cell(MATCHING_SRC))

cells.append(code_cell(r'''
PATTERNS = load_patterns(PATTERNS_FILE)


def candidate_regex(variants):
    # every registered spelling of the candidate, each as a token; brackets of "(MK3475)" removed
    spellings = {v.strip().strip("()").strip() for v in variants.split(" | ")}
    return token_regex(*sorted(s for s in spellings if s))


def evidence_sql(pattern_rx, excluded):
    # code-scoped exclusions (aact_matching.EXCLUSIONS): matched values dropped, as in trials_for_code
    excl = " AND LOWER(TRIM({col})) NOT IN %(excl)s" if excluded else ""
    hits = " UNION ".join(f"SELECT s.nct_id FROM studies s {join} WHERE {col} ~* %(rx)s" + excl.format(col=col)
                          for _, join, col in CODE_FIELDS)
    if pattern_rx:
        hits += " UNION SELECT f.nct_id FROM id_information f WHERE f.id_value ~* %(prx)s" + excl.format(col="f.id_value")
    return f"""
WITH hits AS ({hits}),
with_inn AS (
    SELECT DISTINCT h.nct_id FROM hits h
    JOIN interventions i ON i.nct_id = h.nct_id
    WHERE LOWER(i.name) LIKE %(inn)s
),
spons AS (
    SELECT sp.name, COUNT(*) AS n FROM hits h
    JOIN sponsors sp ON sp.nct_id = h.nct_id AND sp.lead_or_collaborator = 'lead'
    GROUP BY sp.name ORDER BY n DESC LIMIT 3
)
SELECT (SELECT COUNT(*) FROM hits) AS registry_trials,
       (SELECT COUNT(*) FROM with_inn) AS trials_with_inn,
       (SELECT string_agg(name || ' (' || n || ')', '; ') FROM spons) AS top_lead_sponsors
"""


cache = pd.read_csv(EVIDENCE_CACHE, dtype={"code_key": str}) if os.path.exists(EVIDENCE_CACHE) else \
    pd.DataFrame(columns=["inn", "code_key", "registry_trials", "trials_with_inn", "top_lead_sponsors"])
done = set(zip(cache["inn"], cache["code_key"]))

todo = cand[[(i, k) not in done for i, k in zip(cand["inn"], cand["code_key"])]]
print(f"Evidence: {len(done)} cached, {len(todo)} to query")
new_rows = []
for n, (_, r) in enumerate(todo.iterrows(), 1):
    first = r["variants"].split(" | ")[0].strip("()")
    prx = "|".join(rx for _, rx in pattern_regexes(first, PATTERNS))
    excluded = tuple(sorted(v for k, v in EXCLUSIONS if k == match_key(r["code_key"])))
    ev = run_query(evidence_sql(prx, excluded), {"rx": candidate_regex(r["variants"]), "prx": prx,
                                                 "inn": f"%{r['inn'].lower()}%", "excl": excluded})
    new_rows.append({"inn": r["inn"], "code_key": r["code_key"], **ev.iloc[0].to_dict()})
    if n % 25 == 0:
        print(f"  {n}/{len(todo)}")
        pd.concat([cache, pd.DataFrame(new_rows)]).to_csv(EVIDENCE_CACHE, index=False)
cache = pd.concat([cache, pd.DataFrame(new_rows)], ignore_index=True)
cache.to_csv(EVIDENCE_CACHE, index=False)

evidence = cand.merge(cache, on=["inn", "code_key"], how="left")
print(f"Candidates with registry evidence: {(evidence['registry_trials'] > 0).sum()} of {len(evidence)}")
'''))

cells.append(markdown_cell(r'''
## 9. Apply human review

`collections/<COLLECTION>_code_review.csv` columns: `inn, code_key, code_class, use_in_search, rationale, reviewer,
verification, clan_relation`.

`reviewer` = `claude-proposed` for AI-proposed rows; replace with your initials when confirmed. The notebook reports
how many accepted codes still rest on unconfirmed proposals.

| code_class | Meaning | use_in_search |
|------------|---------|---------------|
| `current` | Sponsor code at approval | Y |
| `legacy` | Earlier code: originator, licensor, predecessor company | Y |
| `partner` | Code of a co-development or regional partner | Y |
| `other_product` | Different product containing the moiety: fixed-dose combination, co-formulation, other formulation | N |
| `biosimilar` | Another company's copy | N |
| `other_drug` | Code of a different drug, attached to this intervention in the registry | N |
| `typo` | Misspelled code seen in the registry or PubChem | N |
| `not_a_code` | Vendor, ATC, NSC, approval number, clone name | N |

`verification`: outcome of an independent check of a code — `confirmed`, `unresolved` or
`refuted as sponsor code` with date and source, or the AACT record (date, intervention) the code was read from.

`clan_relation` (for `other_product` rows): how the other product relates to the moiety.

| clan_relation | Meaning | Example |
|---------------|---------|---------|
| `combination` | Fixed-dose combination or co-formulation with another moiety | MK-7684A |
| `pharmaceutical_product` | Same moiety, own code for another formulation | MK-3475A, BMS-986298 |
| `medicinal_product` | Another company's product of the moiety | TAH3311ODF |
| `trial_label` | Code used as a label in trial records for a product | BR3006A, BR3003C |

Candidates without a review row are `pending`. Candidates with no registry evidence and only a PubChem source are
`unconfirmed` and not reviewed individually.

**Acceptance rule** — checkable without domain expertise. Evidence lines: each harvest source (NCIt, PubChem,
AACT other names), each distinct web publisher, and `Registry` when trials are found by title/intervention search.
A code extension read from `interventions.name` (source `AACT-name`) counts as `Registry`, not as a line of its own:
both read the same trial records.

| rule | Condition |
|------|-----------|
| `accept` | 2 or more evidence lines, not an NCIt-labelled biosimilar |
| `exclude` | NCIt labels the code as a biosimilar |
| `insufficient` | one evidence line |

The rule does not override the review. Where they disagree — accepted on one line of evidence, or excluded despite
two — the row goes to `collections/<COLLECTION>_review_exceptions.csv` for independent verification or an expert check.
'''))

cells.append(code_cell(r'''
REVIEW_FILE = f"{REPO_ROOT}/collections/{COLLECTION}_code_review.csv"
CLASSES = {"current", "legacy", "partner", "other_product", "biosimilar", "other_drug", "typo", "not_a_code"}

review = pd.read_csv(REVIEW_FILE, dtype=str) if os.path.exists(REVIEW_FILE) else \
    pd.DataFrame(columns=["inn", "code_key", "code_class", "use_in_search", "rationale", "reviewer",
                          "verification", "clan_relation"])
bad = set(review["code_class"]) - CLASSES
assert not bad, f"Unknown code_class in review file: {bad}"
orphan = review.merge(evidence[["inn", "code_key"]], how="left", indicator=True)
orphan = orphan[orphan["_merge"] == "left_only"]
assert orphan.empty, f"Review rows without a harvested candidate:\n{orphan[['inn', 'code_key']]}"

out = evidence.merge(review, on=["inn", "code_key"], how="left")

# --- Acceptance rule: checkable without domain expertise -------------------------------
# Evidence lines: each harvest source (NCIt, PubChem, AACT other names); each distinct web publisher
# (domain); and "Registry" when trials are found by title/intervention search but AACT other names
# did not list the code.
def evidence_lines(r):
    lines = {s for s in r["sources"].split("; ") if s not in ("Web", "AACT-name")}
    for url in str(r["web_urls"]).split(" | "):
        if url.startswith("http"):
            lines.add("Web:" + re.sub(r"^https?://(www\.)?", "", url).split("/")[0])
    if (r["registry_trials"] > 0 or "AACT-name" in r["sources"]) and "AACT" not in lines:
        lines.add("Registry")
    return "; ".join(sorted(lines))


out["evidence_lines"] = out.apply(evidence_lines, axis=1)
out["n_evidence"] = out["evidence_lines"].str.split("; ").map(len)
out["rule"] = "insufficient"
out.loc[out["n_evidence"] >= 2, "rule"] = "accept"
out.loc[out["ncit_biosimilar"], "rule"] = "exclude"

unconfirmed = out["code_class"].isna() & (out["sources"] == "PubChem") & (out["registry_trials"] == 0)
out.loc[unconfirmed, "code_class"] = "unconfirmed"
out["code_class"] = out["code_class"].fillna("pending")
out["use_in_search"] = out["use_in_search"].fillna("N")
out["harvest_date"] = f"{datetime.now():%Y-%m-%d}"

out = out.sort_values(["inn", "code_class", "registry_trials"], ascending=[True, True, False])
out.to_csv(f"{REPO_ROOT}/collections/{COLLECTION}_code_evidence.csv", index=False)
print(out["code_class"].value_counts().to_string())
accepted = out[out["use_in_search"] == "Y"]
print(f"\nAccepted for search: {len(accepted)} — by reviewer: {accepted['reviewer'].value_counts().to_dict()}")

# Exceptions: where the review decision and the rule disagree → independent verification / expert check
exc = out[((out["use_in_search"] == "Y") & (out["rule"] != "accept")) |
          ((out["use_in_search"] == "N") & (out["rule"] == "accept") & (out["code_class"] != "biosimilar"))].copy()
exc["exception"] = exc["use_in_search"].map({"Y": "accepted on one line of evidence",
                                             "N": "excluded despite two lines of evidence"})
exc.to_csv(f"{REPO_ROOT}/collections/{COLLECTION}_review_exceptions.csv", index=False)
print(pd.crosstab(out["rule"], out["use_in_search"]))
print(f"Exceptions for verification: {len(exc)}")
'''))

cells.append(markdown_cell(r'''
## 10. Export accepted codes per brand

Format matches the trial archaeology notebook: `current_code` (sponsor code at approval) and `legacy_codes`
(legacy + partner). Preferred spelling: hyphenated, else spaced, else as found — the archaeology notebook expands
separator variants from it.
'''))

cells.append(code_cell(r'''
use = out[out["use_in_search"] == "Y"].copy()


def preferred(variants):
    # The archaeology notebook derives no-separator and space/hyphen variants from a code that has a separator,
    # but not the reverse — so prefer a hyphenated spelling, then a spaced one; never a bracketed one.
    vs = [v for v in variants.split(" | ") if not v.startswith("(")]
    for sep in ["-", " "]:
        with_sep = [v for v in vs if sep in v.strip()]
        if with_sep:
            return with_sep[0]
    return vs[0]


rows = []
for _, b in collection.iterrows():
    comps = [x.strip() for x in b["inn"].split(";")]
    u = use[use["inn"].isin(comps)]
    current = sorted(set(preferred(v) for v in u.loc[u["code_class"] == "current", "variants"]))
    legacy = sorted(set(preferred(v) for v in u.loc[u["code_class"].isin(["legacy", "partner"]), "variants"]))
    legacy = [c for c in legacy if c not in current]
    rows.append({"brand": b["brand"], "inn": b["inn"], "current_code": "; ".join(current),
                 "legacy_codes": "; ".join(legacy), "sponsor": b[SPONSOR_COLUMN[COLLECTION]]})

codes = pd.DataFrame(rows)
codes.to_csv(f"{REPO_ROOT}/collections/{COLLECTION}_codes.csv", index=False)

# Moiety-level view — the unit of trial search. One row per active moiety; brands sharing a moiety are joined;
# combination-product codes sit on each component. Same columns as fda_novel_2025.csv, so the archaeology
# notebook loads it with COLLECTION = "<COLLECTION>_moiety_codes".
moiety_rows = []
for inn_ in inns["inn"]:
    in_brand = collection["inn"].apply(lambda s: inn_ in [x.strip() for x in s.split(";")])
    u = use[use["inn"] == inn_]
    current = sorted(set(preferred(v) for v in u.loc[u["code_class"] == "current", "variants"]))
    legacy = sorted(set(preferred(v) for v in u.loc[u["code_class"].isin(["legacy", "partner"]), "variants"]))
    legacy = [c for c in legacy if c not in current]
    moiety_rows.append({"brand": "; ".join(collection.loc[in_brand, "brand"].unique()), "inn": inn_,
                        "current_code": "; ".join(current), "legacy_codes": "; ".join(legacy),
                        "sponsor": "; ".join(collection.loc[in_brand, SPONSOR_COLUMN[COLLECTION]].unique())})
moiety_codes = pd.DataFrame(moiety_rows)
moiety_codes.to_csv(f"{REPO_ROOT}/collections/{COLLECTION}_moiety_codes.csv", index=False)
print(f"Moiety-level file: {len(moiety_codes)} active moieties")
pending = (out["code_class"] == "pending").sum()
print(f"Exported {len(codes)} brand rows. Pending review: {pending}")
codes
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
    c["source"] = [line.replace("RULE_HASH", RULE_HASH) for line in c["source"]]

with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print("written", sys.argv[1], len(cells), "cells")
