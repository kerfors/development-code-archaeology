"""Builds hassle_codes/notebooks/hassle_pubchem_patents.ipynb.

Hässle patent-table codes against PubChem (Kerstin, 2026-11-26, after the talk with Chris Southan and his post
https://cdsouthan.blogspot.com/2026/09/acs-fall-2026-first-disclosures-in.html):
1. structures from the transcribed patent tables, 2. PubChem lookup, 3. salt records, 4. PubChem patent
mappings against the patents we already know, 5. submitter-level (SID) name search for every H code.

Change this builder, not the notebook. Run: python hassle_codes/tools/build_hassle_pubchem_patents_notebook.py
"""
import json
import os

NOTEBOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "notebooks", "hassle_pubchem_patents.ipynb")


def markdown_cell(text):
    lines = text.strip("\n").split("\n")
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in lines[:-1]] + [lines[-1]]}


def code_cell(text):
    lines = text.strip("\n").split("\n")
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": [l + "\n" for l in lines[:-1]] + [lines[-1]]}


cells = []

cells.append(markdown_cell(r'''
# Hässle patent-table codes against PubChem

### Why this notebook exists

Two AB Hässle patents print 76 codes in tables, without the "H": US 3485835 (52 benzofurans) and US 3558616
(24 benzothiophenes). The rows give substituents on one generic formula, not names. This notebook builds a
structure per row and asks PubChem four things:

1. Is the structure in PubChem (exact, or same connectivity)?
2. Is it there as a salt (same parent)?
3. Which patents does PubChem map to those records, and are any of them patents we do not have yet?
   (This is how US 3594478 was found on 2026-11-26.)
4. Has any submitter ever deposited an H code as a name? Searched per submitter record (SID) with its deposition
   date, for all codes in `collections/hassle_h_codes_all.csv` — the method in Chris Southan's post on
   name-to-structure (n2s): a CID's date tells when the structure came in, not when a name was attached.

Patent source: Google Patents only, as in the sessions of 2026-11-21. PubChem is the only other source here.

### Rules

- Substituents come only from the input file; an unknown token stops the run (no guessing).
- Rows that cannot be built (`smiles` empty in the input logic, e.g. H 43/49) are kept, with the reason.
- Structures are free bases as drawn by the generic formula; the patents give no salt form.
- Every PubChem request is cached in `hassle_codes/output/cache_pubchem/` (one JSON per request). Delete to refresh.
- PubChem results are evidence for review, not decisions (no Wikidata reference, design decision 4).

### Inputs

- `hassle_codes/inputs/hassle_patent_tables_2026-11-26.csv` — one row per code: patent, core, A, R, R1, R2, NR3R4,
  table location, when transcribed, when the page was checked against the PDF, note
- `collections/hassle_h_codes_all.csv` — all H codes (for the name search)
- `hassle_codes/inputs/hassle_findings_*.csv`, `collections/hassle_h_codes_all.csv` — patents already known

### Outputs (in `hassle_codes/output/pubchem_patents/`, not tracked)

- `hassle_pubchem_patents.xlsx` — sheets `structures`, `cids`, `patent_mappings`, `new_patents`, `name_hits`, `run`
- the same tables as CSV
'''))

cells.append(markdown_cell("## 1. Configuration"))

cells.append(code_cell(r'''
import json
import re
import time
import hashlib
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from rdkit import Chem
from rdkit.Chem.rdMolDescriptors import CalcMolFormula

REPO_ROOT = Path("../..")
TABLES = REPO_ROOT / "hassle_codes/inputs/hassle_patent_tables_2026-11-26.csv"
ALL_CODES = REPO_ROOT / "collections/hassle_h_codes_all.csv"
FINDINGS = sorted((REPO_ROOT / "hassle_codes/inputs").glob("hassle_findings_*.csv"))
OUT_DIR = REPO_ROOT / "hassle_codes/output/pubchem_patents"
CACHE_DIR = REPO_ROOT / "hassle_codes/output/cache_pubchem"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
USER_AGENT = "development-code-archaeology/hassle-pubchem-patents (https://github.com/kerfors/development-code-archaeology)"
PAUSE = 0.25  # PubChem asks for at most 5 requests per second
RUN_STARTED = datetime.now(timezone.utc).isoformat(timespec="seconds")
'''))

cells.append(markdown_cell(r'''
## 2. Cached PubChem requests

One JSON file per request. A 404 ("not found") is a valid answer and is cached as `null`; any other HTTP error stops the run.
'''))

cells.append(code_cell(r'''
def _cache_file(key):
    return CACHE_DIR / (hashlib.sha1(key.encode()).hexdigest() + ".json")


def pug(path, post=None):
    """GET {PUG}/{path}, or POST form data when post is a dict. Returns parsed JSON or None for not found."""
    key = path + ("|" + json.dumps(post, sort_keys=True) if post else "")
    f = _cache_file(key)
    if f.exists():
        return json.loads(f.read_text())["data"]
    time.sleep(PAUSE)
    data = urllib.parse.urlencode(post).encode() if post else None
    req = urllib.request.Request(f"{PUG}/{path}", data=data, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            result = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        result = None
    f.write_text(json.dumps({"key": key, "retrieved": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                             "data": result}))
    return result


def id_list(result, field="CID"):
    return result["IdentifierList"][field] if result else []


def info_list(result):
    return result["InformationList"]["Information"] if result else []
'''))

cells.append(markdown_cell(r'''
## 3. Structures from the patent tables

Generic formulas (claim 1 of each patent): **2-(R-CO)-3-(O-A-NR3R4)** on benzofuran (US 3485835) or
benzothiophene (US 3558616); R1/R2 on the benzo ring at the positions printed in the table (4–7).
A is read left to right as written, O-A-N: CH(CH3)CH2 = O-CH(CH3)-CH2-N.
Ring closure digits in the fragments are renumbered (8, 9) so they never collide with the core's 1 and 2.
'''))

cells.append(code_cell(r'''
R_SMI = {
    "methyl": "C", "ethyl": "CC", "tert-butyl": "C(C)(C)C",
    "phenyl": "c1ccccc1",
    "2-methoxyphenyl": "c1ccccc1OC", "4-methoxyphenyl": "c1ccc(OC)cc1",
    "4-ethoxyphenyl": "c1ccc(OCC)cc1", "4-isopropoxyphenyl": "c1ccc(OC(C)C)cc1",
    "4-methylphenyl": "c1ccc(C)cc1", "2-chlorophenyl": "c1ccccc1Cl",
    "4-chlorophenyl": "c1ccc(Cl)cc1", "4-fluorophenyl": "c1ccc(F)cc1",
    "3-trifluoromethylphenyl": "c1cccc(C(F)(F)F)c1",
    "4-tert-butylphenyl": "c1ccc(C(C)(C)C)cc1",
}
A_SMI = {"CH2CH2": "CC", "CH2CH2CH2": "CCC", "CH(CH3)CH2": "C(C)C"}
N_SMI = {
    "diethylamino": "N(CC)CC", "dimethylamino": "N(C)C",
    "pyrrolidino": "N1CCCC1", "piperidino": "N1CCCCC1",
    "morpholino": "N1CCOCC1", "2,6-dimethylmorpholino": "N1CC(C)OC(C)C1",
    "1,2,3,6-tetrahydropyridino": "N1CC=CCC1",
    "4-methylpiperazino": "N1CCN(C)CC1", "hexamethyleneimino": "N1CCCCCC1",
}
SUB_SMI = {"CH3": "C", "OCH3": "OC", "Br": "Br", "Cl": "Cl", "F": "F",
           "NO2": "[N+](=O)[O-]", "NH2": "N", "OH": "O", "CF3": "C(F)(F)F"}
HETERO = {"benzofuran": "o", "benzothiophene": "s"}


def ring_substituents(*tokens):
    subs = {}
    for tok in tokens:
        if tok == "H":
            continue
        pos, grp = tok.split("-", 1)
        pos = int(pos)
        assert pos not in subs, f"two substituents at position {pos}"
        subs[pos] = SUB_SMI[grp]
    return subs


def build_smiles(row):
    """Free-base SMILES for one table row, or (None, reason) when the row cannot be built."""
    if row.A not in A_SMI:
        return None, f"A '{row.A}' not buildable"
    subs = ring_substituents(row.R1, row.R2)
    p = {k: (f"({subs[k]})" if k in subs else "") for k in (4, 5, 6, 7)}
    r = R_SMI[row.R].replace("1", "8")
    n = N_SMI[row.NR3R4].replace("1", "9")
    smi = f"{HETERO[row.core]}1c(C(=O){r})c(O{A_SMI[row.A]}{n})c2c{p[4]}c{p[5]}c{p[6]}c{p[7]}c12"
    mol = Chem.MolFromSmiles(smi)
    assert mol is not None, (row.code, smi)
    return Chem.MolToSmiles(mol), ""


tables = pd.read_csv(TABLES, dtype=str).fillna("")
unknown = {c: sorted(set(tables[c]) - set(v) - {""}) for c, v in
           [("R", R_SMI), ("NR3R4", N_SMI)]}
assert not any(unknown.values()), f"unknown substituent tokens: {unknown}"

rows = []
for row in tables.itertuples():
    smi, reason = build_smiles(row)
    mol = Chem.MolFromSmiles(smi) if smi else None
    rows.append({"code": row.code, "patent": row.patent, "core": row.core,
                 "smiles": smi or "", "inchikey": Chem.MolToInchiKey(mol) if mol else "",
                 "formula": CalcMolFormula(mol) if mol else "", "not_built_reason": reason,
                 "page_checked": row.page_checked, "note": row.note})
structures = pd.DataFrame(rows)

built = structures[structures.smiles != ""]
assert built.inchikey.is_unique, built[built.inchikey.duplicated(keep=False)]
core_pat = {"benzofuran": Chem.MolFromSmarts("o1c(C=O)c(O)c2ccccc12"),
            "benzothiophene": Chem.MolFromSmarts("s1c(C=O)c(O)c2ccccc12")}
for r in built.itertuples():
    assert len(Chem.MolFromSmiles(r.smiles).GetSubstructMatches(core_pat[r.core])) == 1, r.code
print(f"{len(structures)} rows, {len(built)} structures built, not built: "
      f"{structures.loc[structures.smiles == '', 'code'].tolist()}")
'''))

cells.append(markdown_cell(r'''
## 4. PubChem: exact match, same connectivity, salts

- exact: InChIKey → CID
- same connectivity (stereo/isotope may differ): SMILES POST to `fastidentity`
- salts and mixtures: `cids_type=same_parent` on every CID found (this is how the benzothiophene hydrochlorides were found)
'''))

cells.append(code_cell(r'''
cid_rows = []
for r in built.itertuples():
    exact = id_list(pug(f"compound/inchikey/{r.inchikey}/cids/JSON"))
    conn = id_list(pug("compound/fastidentity/smiles/cids/JSON?identity_type=same_connectivity",
                       post={"smiles": r.smiles}))
    found = {c: "exact" for c in exact}
    for c in conn:
        found.setdefault(c, "same connectivity")
    for c in list(found):
        for s in id_list(pug(f"compound/cid/{c}/cids/JSON?cids_type=same_parent")):
            found.setdefault(s, f"same parent as {c}")
    for c, how in found.items():
        cid_rows.append({"code": r.code, "cid": c, "match": how})

cids = pd.DataFrame(cid_rows, columns=["code", "cid", "match"])
if len(cids):
    props = {}
    for c in sorted(set(cids.cid)):
        p = pug(f"compound/cid/{c}/property/MolecularFormula,InChIKey/JSON")
        props[c] = p["PropertyTable"]["Properties"][0]
    cids["formula"] = cids.cid.map(lambda c: props[c]["MolecularFormula"])
    cids["inchikey"] = cids.cid.map(lambda c: props[c]["InChIKey"])
    syn = {c: [s for i in info_list(pug(f"compound/cid/{c}/synonyms/JSON")) for s in i.get("Synonym", [])]
           for c in sorted(set(cids.cid))}
    cids["n_synonyms"] = cids.cid.map(lambda c: len(syn[c]))
    cids["synonyms"] = cids.cid.map(lambda c: " | ".join(syn[c][:10]))
    cids["url"] = cids.cid.map(lambda c: f"https://pubchem.ncbi.nlm.nih.gov/compound/{c}")

structures["pubchem_cids"] = structures.code.map(
    cids.groupby("code").cid.apply(lambda s: ";".join(map(str, s))) if len(cids) else {}).fillna("")
print(f"codes with any CID: {(structures.pubchem_cids != '').sum()} of {len(built)} built")
cids
'''))

cells.append(markdown_cell(r'''
## 5. Patent mappings in PubChem, against the patents we know

PubChem patent IDs come as `US-3594478-A`, `WO2013083991A1`, `DE-1645913-A1`. They are normalised to
country + number (kind code dropped) and compared with every patent number named in our findings files and
the large code list. Patents not in that set are listed in `new_patents` for review.
'''))

cells.append(code_cell(r'''
PAT_RE = re.compile(r"^([A-Z]{2})-?(\d+)-?([A-Z]\d?)?$")


def norm_patent(pid):
    m = PAT_RE.match(pid.replace(" ", ""))
    assert m, f"unexpected patent id format: {pid}"
    return m.group(1) + m.group(2)


known_text = " ".join(pd.read_csv(f, dtype=str).fillna("").to_string() for f in FINDINGS + [ALL_CODES])
KNOWN = {m[0] + m[1] for m in re.findall(r"\b(US|EP|WO|DE|GB|SE)\s?-?(\d{6,9})", known_text)}
print(f"{len(KNOWN)} patent numbers already named in our files")

map_rows = []
for c in sorted(set(cids.cid)):
    pats = [p for i in info_list(pug(f"compound/cid/{c}/xrefs/PatentID/JSON")) for p in i.get("PatentID", [])]
    for p in sorted(set(pats)):
        map_rows.append({"cid": c, "patent_id": p, "patent": norm_patent(p)})
patent_mappings = pd.DataFrame(map_rows, columns=["cid", "patent_id", "patent"])
patent_mappings = patent_mappings.merge(cids[["code", "cid", "match"]], on="cid")
patent_mappings["known"] = patent_mappings.patent.isin(KNOWN)
patent_mappings["google_patents"] = "https://patents.google.com/patent/" + patent_mappings.patent_id.str.replace("-", "")

new_patents = (patent_mappings[~patent_mappings.known]
               .groupby("patent")
               .agg(codes=("code", lambda s: ", ".join(sorted(set(s)))),
                    cids=("cid", lambda s: ";".join(map(str, sorted(set(s))))),
                    google_patents=("google_patents", "first"))
               .reset_index())
new_patents
'''))

cells.append(markdown_cell(r'''
## 6. Submitter-level name search for every H code (Chris Southan's n2s check)

For each code in the large list, the spellings `H 168/68`, `H-168/68`, `H168/68`, `H 168-68`, `H-168-68` are
searched as substance names (POST, so the slash is safe). Every SID found gets its depositor, deposition date and
the CIDs it standardises to. The question is not only *whether* a code is in PubChem, but *who* first attached it
to a structure, and when.

The bare table form ("43/47") is not searched: far too ambiguous.
'''))

cells.append(code_cell(r'''
def spellings(code):
    a, b = code[2:].split("/")
    return [f"H {a}/{b}", f"H-{a}/{b}", f"H{a}/{b}", f"H {a}-{b}", f"H-{a}-{b}"]


all_codes = pd.read_csv(ALL_CODES, dtype=str).fillna("")
assert all_codes.code.is_unique
hit_rows = []
for code in all_codes.code:
    for name in spellings(code):
        for sid in id_list(pug("substance/name/sids/JSON", post={"name": name}), "SID"):
            hit_rows.append({"code": code, "name_searched": name, "sid": sid})
name_hits = pd.DataFrame(hit_rows, columns=["code", "name_searched", "sid"])

sid_info = {}
for sid in sorted(set(name_hits.sid)):
    sub = pug(f"substance/sid/{sid}/JSON")["PC_Substances"][0]
    dep = info_list(pug(f"substance/sid/{sid}/dates/JSON"))[0]["DepositionDate"]
    sid_cids = [c for i in info_list(pug(f"substance/sid/{sid}/cids/JSON")) for c in i.get("CID", [])]
    sid_info[sid] = {"source_name": sub["source"]["db"]["name"],
                     "source_id": sub["source"]["db"]["source_id"].get("str", ""),
                     "deposited": f"{dep['Year']:04d}-{dep['Month']:02d}-{dep['Day']:02d}",
                     "cids": ";".join(map(str, sid_cids))}
for k in ["source_name", "source_id", "deposited", "cids"]:
    name_hits[k] = name_hits.sid.map(lambda s: sid_info[s][k])
name_hits["url"] = "https://pubchem.ncbi.nlm.nih.gov/substance/" + name_hits.sid.astype(str)
name_hits = name_hits.sort_values(["code", "deposited", "sid"]).drop_duplicates(["code", "sid"])

first_n2s = name_hits.groupby("code").agg(first_deposited=("deposited", "min"), n_sids=("sid", "nunique"),
                                          depositors=("source_name", lambda s: ", ".join(sorted(set(s)))))
print(f"codes searched: {len(all_codes)}, codes with any SID: {len(first_n2s)}")
table_codes_hit = sorted(set(first_n2s.index) & set(tables.code))
print(f"patent-table codes with any SID: {table_codes_hit}")
first_n2s
'''))

cells.append(markdown_cell("## 7. Write outputs"))

cells.append(code_cell(r'''
run = pd.DataFrame([
    {"item": "run_started_utc", "value": RUN_STARTED},
    {"item": "tables_input", "value": str(TABLES)},
    {"item": "codes_input", "value": str(ALL_CODES)},
    {"item": "table_rows", "value": len(structures)},
    {"item": "structures_built", "value": len(built)},
    {"item": "codes_with_cid", "value": int((structures.pubchem_cids != "").sum())},
    {"item": "patent_mappings", "value": len(patent_mappings)},
    {"item": "new_patents", "value": len(new_patents)},
    {"item": "codes_searched_by_name", "value": len(all_codes)},
    {"item": "codes_with_sid", "value": len(first_n2s)},
    {"item": "cache_dir", "value": str(CACHE_DIR)},
])
sheets = {"structures": structures, "cids": cids, "patent_mappings": patent_mappings,
          "new_patents": new_patents, "name_hits": name_hits, "run": run}
with pd.ExcelWriter(OUT_DIR / "hassle_pubchem_patents.xlsx") as xw:
    for name, df in sheets.items():
        df.to_excel(xw, sheet_name=name, index=False)
for name, df in sheets.items():
    df.to_csv(OUT_DIR / f"hassle_pubchem_patents_{name}.csv", index=False)
print(f"written to {OUT_DIR}")
run
'''))

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 4,
}

with open(NOTEBOOK, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)
print(f"wrote {NOTEBOOK}")
