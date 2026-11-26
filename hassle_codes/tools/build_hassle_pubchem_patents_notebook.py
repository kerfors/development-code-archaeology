"""Builds hassle_codes/notebooks/hassle_pubchem_patents.ipynb.

Hässle patent-table codes against PubChem (Kerstin, 2026-11-26, after the talk with Chris Southan and his post
https://cdsouthan.blogspot.com/2026/09/acs-fall-2026-first-disclosures-in.html):
1. structures from the transcribed patent tables, 2. PubChem lookup, 3. salt records, 4. PubChem patent
mappings against the patents we already know, 5. submitter-level (SID) name search for every H code.
Step 7-8 (added 2026-11-26): patent families and page images from EPO OPS (credentials in ~/.config/epo_ops.env).

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
RETRY_CODES = {502, 503, 504}  # PubChem server-side errors, usually transient
RETRY_PAUSES = [5, 15, 45]  # seconds before attempt 2, 3, 4; then the error is raised
RUN_STARTED = datetime.now(timezone.utc).isoformat(timespec="seconds")
'''))

cells.append(markdown_cell(r'''
## 2. Cached PubChem requests

One JSON file per request. A 404 ("not found") is a valid answer and is cached as `null`.
PubChem server errors 502, 503 and 504 are retried up to 3 times (pauses 5, 15, 45 s); after that, and for
any other HTTP error, the run stops. Retries are never cached, only the final answer.
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
    data = urllib.parse.urlencode(post).encode() if post else None
    for attempt, wait in enumerate([PAUSE] + RETRY_PAUSES):
        time.sleep(wait)
        req = urllib.request.Request(f"{PUG}/{path}", data=data, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                result = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                result = None
                break
            if e.code in RETRY_CODES and attempt < len(RETRY_PAUSES):
                print(f"PubChem {e.code} on {path} — retry {attempt + 1} of {len(RETRY_PAUSES)} "
                      f"in {RETRY_PAUSES[attempt]} s")
                continue
            raise
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
    "3-methoxyphenyl": "c1cccc(OC)c1", "3-chlorophenyl": "c1cccc(Cl)c1",
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

cells.append(markdown_cell(r'''
## 7. Patent families from EPO OPS

Every patent named in our files plus the new ones PubChem mapped is sent to the OPS family service (INPADOC
extended family), as publication number in epodoc form (country + number, no kind code). Each family member is
listed with its publication date, application and priorities.

- Credentials: `~/.config/epo_ops.env` with two lines, `EPO_OPS_KEY="..."` and `EPO_OPS_SECRET="..."` — outside
  the repo, never printed. A missing file or line stops the run.
- One access token, renewed after 15 minutes (OPS tokens last 20).
- Every OPS answer is cached in `hassle_codes/output/cache_epo/`; the token is never cached.
- A 404 means OPS does not know the number in that form: listed as `not_found`, not retried in another form.
- OPS answers are JSON renderings of its XML (`$` = text, `@` = attribute). The parsing below asserts the
  structure it expects, so a different answer stops the run with the element that did not fit.
'''))

cells.append(code_cell(r'''
import base64

EPO_ENV = Path.home() / ".config/epo_ops.env"
OPS = "https://ops.epo.org/3.2"
CACHE_EPO = REPO_ROOT / "hassle_codes/output/cache_epo"
CACHE_EPO.mkdir(parents=True, exist_ok=True)
OPS_PAUSE = 1.0  # seconds between OPS requests (fair use)


def read_epo_credentials(path):
    assert path.exists(), f"{path} not found: it needs EPO_OPS_KEY and EPO_OPS_SECRET (see the markdown above)"
    vals = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            k, v = line.split("=", 1)
            vals[k.strip().removeprefix("export ").strip()] = v.strip().strip('"').strip("'")
    missing = [k for k in ("EPO_OPS_KEY", "EPO_OPS_SECRET") if not vals.get(k)]
    assert not missing, f"missing in {path}: {missing}"
    return vals["EPO_OPS_KEY"], vals["EPO_OPS_SECRET"]


_token = {"value": None, "fetched": 0.0}


def ops_token():
    if _token["value"] and time.time() - _token["fetched"] < 15 * 60:
        return _token["value"]
    key, secret = read_epo_credentials(EPO_ENV)
    basic = base64.b64encode(f"{key}:{secret}".encode()).decode()
    req = urllib.request.Request(f"{OPS}/auth/accesstoken", data=b"grant_type=client_credentials",
                                 headers={"Authorization": f"Basic {basic}",
                                          "Content-Type": "application/x-www-form-urlencoded",
                                          "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        _token["value"] = json.load(r)["access_token"]
    _token["fetched"] = time.time()
    return _token["value"]


def ops_get(path, accept="application/json", binary=False):
    """GET {OPS}/rest-services/{path}. Cached. Returns parsed JSON, or bytes when binary; None for not found."""
    f = CACHE_EPO / (hashlib.sha1(f"{path}|{accept}".encode()).hexdigest() + (".bin" if binary else ".json"))
    if f.exists():
        return f.read_bytes() if binary else json.loads(f.read_text())["data"]
    for attempt, wait in enumerate([OPS_PAUSE] + RETRY_PAUSES):
        time.sleep(wait)
        req = urllib.request.Request(f"{OPS}/rest-services/{path}",
                                     headers={"Authorization": f"Bearer {ops_token()}", "Accept": accept,
                                              "User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                body = None
                break
            if e.code in RETRY_CODES and attempt < len(RETRY_PAUSES):
                print(f"OPS {e.code} on {path} — retry {attempt + 1} of {len(RETRY_PAUSES)} "
                      f"in {RETRY_PAUSES[attempt]} s")
                continue
            raise
    if binary:
        if body is not None:
            f.write_bytes(body)
        return body
    data = json.loads(body) if body is not None else None
    f.write_text(json.dumps({"key": path, "retrieved": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                             "data": data}))
    return data


def as_list(x):
    return x if isinstance(x, list) else ([] if x is None else [x])


def docdb_id(ref):
    """(country, number, kind, date) from the docdb document-id of a publication/application/priority element."""
    for d in as_list(ref.get("document-id")):
        if d.get("@document-id-type") == "docdb":
            return tuple(d.get(k, {}).get("$", "") for k in ("country", "doc-number", "kind", "date"))
    raise AssertionError(f"no docdb document-id in {ref}")


def iso(d):
    return f"{d[:4]}-{d[4:6]}-{d[6:]}" if len(d) == 8 else d


ALL_KNOWN = KNOWN | set(new_patents.patent)
fam_rows, not_found = [], []
for p in sorted(ALL_KNOWN):
    data = ops_get(f"family/publication/epodoc/{p}")
    if data is None:
        not_found.append(p)
        continue
    fam = data["ops:world-patent-data"]["ops:patent-family"]
    for m in as_list(fam["ops:family-member"]):
        for pub in as_list(m["publication-reference"]):
            pc, pn, pk, pdate = docdb_id(pub)
            ac, an, ak, adate = docdb_id(m["application-reference"])
            prios = [docdb_id(pr) for pr in as_list(m.get("priority-claim"))]
            fam_rows.append({"queried": p, "family_id": m.get("@family-id", ""),
                             "member": f"{pc}{pn}{pk}", "country": pc, "number": pn, "kind": pk,
                             "published": iso(pdate), "application": f"{ac}{an}", "filed": iso(adate),
                             "priorities": "; ".join(f"{c}{n} {iso(d)}" for c, n, k, d in prios),
                             "known": f"{pc}{pn}" in ALL_KNOWN})
family_members = pd.DataFrame(fam_rows, columns=["queried", "family_id", "member", "country", "number", "kind",
                                                 "published", "application", "filed", "priorities", "known"])
print(f"patents queried: {len(ALL_KNOWN)}, not found in OPS: {not_found}")
print(f"family members: {family_members.member.nunique()}, of which not in our files: "
      f"{family_members.loc[~family_members.known, 'member'].nunique()}")

# Dating candidates: members of the code-table families published before the table patent's US filing date
# (our latest-possible date for those codes). Filing dates from hassle_findings_2026-11-21b.csv and -2026-11-26.csv.
TABLE_PATENTS = {"US3485835": "1968-04-10", "US3558616": "1969-11-10", "US3594478": "1969-11-24"}
cand = family_members[family_members.queried.isin(TABLE_PATENTS)].copy()
cand["table_patent_filed"] = cand.queried.map(TABLE_PATENTS)
dating_candidates = (cand[(cand.published != "") & (cand.published < cand.table_patent_filed)]
                     .sort_values("published").drop_duplicates("member"))
dating_candidates
'''))

cells.append(markdown_cell(r'''
## 8. Page images of the dating candidates

For each dating candidate, OPS lists the stored page images; the full document is fetched page by page as PDF
into `hassle_codes/output/epo_images/<member>/`. These pages are for reading by eye: does the member print the
code table? If it does, the codes get that member's publication date as their latest-possible date.
'''))

cells.append(code_cell(r'''
IMG_DIR = REPO_ROOT / "hassle_codes/output/epo_images"
img_rows = []
for r in dating_candidates.itertuples():
    inq = ops_get(f"published-data/publication/docdb/{r.country}.{r.number}.{r.kind}/images")
    if inq is None:
        img_rows.append({"member": r.member, "published": r.published, "pages": 0, "status": "no images in OPS"})
        continue
    results = as_list(inq["ops:world-patent-data"]["ops:document-inquiry"]["ops:inquiry-result"])
    full = [i for res in results for i in as_list(res.get("ops:document-instance"))
            if i.get("@desc") == "FullDocument"]
    if not full:
        img_rows.append({"member": r.member, "published": r.published, "pages": 0, "status": "no full document"})
        continue
    inst = full[0]
    pages = int(inst["@number-of-pages"])
    d = IMG_DIR / r.member
    d.mkdir(parents=True, exist_ok=True)
    for n in range(1, pages + 1):
        pdf = ops_get(f"{inst['@link']}?Range={n}", accept="application/pdf", binary=True)
        assert pdf is not None, f"{r.member} page {n} listed but not delivered"
        (d / f"page_{n:03d}.pdf").write_bytes(pdf)
    img_rows.append({"member": r.member, "published": r.published, "pages": pages, "status": f"saved to {d}"})
epo_images = pd.DataFrame(img_rows, columns=["member", "published", "pages", "status"])
epo_images
'''))

cells.append(markdown_cell("## 9. Write outputs"))

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
    {"item": "patents_queried_in_ops", "value": len(ALL_KNOWN)},
    {"item": "ops_not_found", "value": "; ".join(not_found)},
    {"item": "family_members", "value": family_members.member.nunique()},
    {"item": "family_members_not_in_our_files", "value": family_members.loc[~family_members.known, "member"].nunique()},
    {"item": "dating_candidates", "value": len(dating_candidates)},
    {"item": "cache_dir", "value": str(CACHE_DIR)},
])
sheets = {"structures": structures, "cids": cids, "patent_mappings": patent_mappings,
          "new_patents": new_patents, "name_hits": name_hits, "family_members": family_members,
          "dating_candidates": dating_candidates, "epo_images": epo_images, "run": run}
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
