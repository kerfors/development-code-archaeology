import json
import os

NOTEBOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "notebooks", "hassle_h_code_harvest.ipynb")


def markdown_cell(text):
    lines = text.strip("\n").split("\n")
    return {"cell_type": "markdown", "metadata": {}, "source": [l + "\n" for l in lines[:-1]] + [lines[-1]]}


def code_cell(text):
    lines = text.strip("\n").split("\n")
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": [l + "\n" for l in lines[:-1]] + [lines[-1]]}


cells = []

cells.append(markdown_cell(r'''
# Hässle H-code harvest
## Thread A: all Hässle (Astra Hässle, Mölndal) H codes, with source for every value

### Why this notebook exists

Hässle compounds were named by codes of the form **H nnn/nn** (H 168/68 omeprazole, H 93/26 metoprolol).
The codes are spread over databases in different spellings, mostly at the level of a salt, and many
compounds never got an INN. This notebook harvests the codes from named sources only, resolves the
substance they name, and dates each code by the earliest PubMed record that names it.
Nothing is filled from memory. Wikidata is read, not written; publishing comes after human review.

### Sources, in order

| # | Source | How it is used | Wikidata reference? |
|---|--------|----------------|---------------------|
| 1 | ChEMBL API | Server-side regex on molecule synonyms: the seed list | Not planned |
| 2 | GSRS (FDA) | Phrase search per code, exact-name search per substance; all names of each record scanned; UNII, active moiety, INN, brand names, cross-references | Not planned |
| 3 | MeSH (NLM SPARQL) | Regex over all term labels; all terms of each record scanned; registry number | Not planned |
| 4 | PubChem | Name lookup per code, synonyms of the CIDs found: **cross-check only** | No (design decision 4, 2026-10-16) |
| 5 | NCI Thesaurus | Full release flat file from NCI EVS, regex over all synonyms | Possible (P1748) |
| 6 | PubMed | Hässle-affiliation records scanned for codes; per code a search, every hit verified in the text; earliest verified record | Possible (P854/PMID) |
| 7 | Wikidata | What exists: P15001 values, aliases and labels, items by UNII / ChEMBL / MeSH, INN statements with their references | — |

NCI Thesaurus is read from NCI's own release file, not BioPortal: BioPortal needs an API key, and the flat
file allows a regex over every synonym, which no search API does.

### Code pattern and normalisation

- Separator form: `H`, optional space or hyphen, 1–3 digits, `/` or `-` (optional spaces), **exactly 2 digits**,
  not followed by a digit or `/`. Normalised to `H nnn/nn`. All known codes have a two-digit second number.
- Catches "H 168/68", "H-168/68", "H 168-68", "H168/68", "H 168/68 SODIUM" (the rest of the string is kept as `suffix`).
- No-separator form ("H16868", "H 21644"): split as last two digits = second number, and **accepted only when the
  same code is found with a separator** in another record. Otherwise set aside.
- Case-sensitive capital `H`; free text (PubMed) is scanned for the separator form only.

### Rules

- Every value carries its source (`evidence` table: source, record, field, URL, retrieval time).
- Ambiguities are flagged, not resolved: a code string that is not Hässle, several active moieties for one code,
  a code without salt suffix found only on salt records, no-separator only, a single non-structured source.
- "Hässle" is not assigned by the notebook. The column `pubmed_affiliations` shows the Astra/Hässle
  affiliations of the verified PubMed records naming the code: evidence for the reviewer, not a decision.
- API results are cached in `hassle_codes/output/cache/` (one JSON file per request). Delete the folder to refresh.

### Outputs (in `hassle_codes/output/`, not tracked)

- `hassle_h_codes.xlsx` — sheets `codes` (one row per code), `test_cases`, `forms` (code × string as found ×
  record), `evidence` (every record), `pubmed`, `wikidata_items`, `set_aside`, `coverage`, `run`
- `hassle_h_codes.csv`, `hassle_h_codes_evidence.csv` — the same `codes` and `evidence` tables as CSV
'''))

cells.append(markdown_cell("## 1. Configuration"))

cells.append(code_cell(r'''
REPO_ROOT = "../.."
OUT_DIR = f"{REPO_ROOT}/hassle_codes/output"
CACHE_DIR = f"{OUT_DIR}/cache"

USER_AGENT = "development-code-archaeology/hassle-h-codes (https://github.com/kerfors/development-code-archaeology)"

CHEMBL_API = "https://www.ebi.ac.uk/chembl/api/data"
GSRS_API = "https://gsrs.ncats.nih.gov/api/v1"
GSRS_UI = "https://gsrs.ncats.nih.gov/ginas/app/beta/substances"
MESH_SPARQL = "https://id.nlm.nih.gov/mesh/sparql"
MESH_UI = "https://meshb.nlm.nih.gov/record/ui?ui="
NCIT_FLAT_URL = "https://evs.nci.nih.gov/ftp1/NCI_Thesaurus/Thesaurus.FLAT.zip"
NCIT_API = "https://api-evsrest.nci.nih.gov/api/v1"
NCIT_UI = "https://evsexplore.semantics.cancer.gov/evsexplore/concept/ncit/"
PUBCHEM_API = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
WD_SPARQL = "https://query.wikidata.org/sparql"
WD_API = "https://www.wikidata.org/w/api.php"

# ChEMBL seed: server-side regex on molecule synonyms (case-insensitive on the server, re-checked case-sensitively here)
CHEMBL_SEED_REGEX = "^H[ -]?[0-9]{1,3} ?[/-] ?[0-9]{2}"

# MeSH: regex over all term labels (SPARQL, case-sensitive)
MESH_REGEX = "^H[ -]?[0-9]{1,3} ?[/-] ?[0-9]{2}([^0-9/]|$)"

# PubMed records with a Hässle affiliation, scanned for codes (discovery)
PUBMED_AFFILIATION_QUERY = 'Hassle[ad] OR Hässle[ad]'
PUBMED_RETMAX = 5000

# NCIt semantic types that make a concept a substance; other concepts with a matching synonym are set aside
NCIT_SUBSTANCE_TYPES = ["Pharmacologic Substance", "Organic Chemical", "Inorganic Chemical", "Clinical Drug",
                        "Chemical", "Element, Ion, or Isotope", "Hazardous or Poisonous Substance",
                        "Biologically Active Substance", "Antibiotic", "Hormone", "Steroid"]
NCIT_NOT_SUBSTANCE_TYPES = ["Gene or Genome", "Cell", "Cell Component", "Molecular Sequence",
                            "Amino Acid, Peptide, or Protein"]

# A string whose suffix starts with one of these words names a gene or protein (e.g. MeSH "H1-10 protein, human",
# filed as SCR_Chemical): set aside in every source
GENE_PROTEIN_SUFFIX = ["protein", "gene", "allele"]

# Test cases with their source: claude/hassle-h-codes-research.md section 2
# (Olbe, Carlsson, Lindberg 2003 Nat Rev Drug Discov 2:132; Sjöstrand, Olbe, Fellenius 1999; EP 0005129; EP 7293)
TEST_CASES = {
    "H 168/68": "omeprazole",
    "H 93/26": "metoprolol",
    "H 154/82": "felodipine",
    "H 376/95": "ximelagatran",
    "H 149/94": "picoprazole",
    "H 83/69": "timoprazole",
    "H 124/26": "first benzimidazole lead, 1973 (no INN)",
    "H 81/75": "carbamate, in volunteers 1971-72 (no INN)",
}
'''))

cells.append(markdown_cell("## 2. Setup: HTTP session, cache, code pattern, record collector"))

cells.append(code_cell(r'''
import csv
import hashlib
import io
import json
import os
import re
import time
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from datetime import datetime, timezone

import pandas as pd
import requests
import urllib3.util.connection
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Force IPv4: on this Mac some hosts resolve to IPv6 first and stall ~20 s per call (2026-10-14)
urllib3.util.connection.HAS_IPV6 = False

http = requests.Session()
http.headers.update({"User-Agent": USER_AGENT})
http.mount("https://", HTTPAdapter(max_retries=Retry(total=5, backoff_factor=1,
                                                     status_forcelist=[429, 500, 502, 503, 504],
                                                     allowed_methods=["GET", "POST"], raise_on_status=False)))

os.makedirs(CACHE_DIR, exist_ok=True)

# Seconds to wait after an uncached call, per host (NCBI allows 3 requests/s without key)
PAUSE = {"eutils.ncbi.nlm.nih.gov": 0.4, "pubchem.ncbi.nlm.nih.gov": 0.25, "query.wikidata.org": 0.5}


def cached_request(url, params=None, data=None, as_json=True, headers=None):
    """GET (or POST when data is given) with a file cache. Returns dict: url, status, retrieved_utc, body.
    404 is cached as body None; any other HTTP error stops the notebook."""
    key_src = json.dumps({"url": url, "params": params, "data": data}, sort_keys=True, ensure_ascii=False)
    path = f"{CACHE_DIR}/{hashlib.sha1(key_src.encode('utf-8')).hexdigest()}.json"
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    # Transfers cut off mid-response (ChunkedEncodingError, seen on PubMed efetch 2026-11-21) are tried twice more
    for attempt in range(3):
        try:
            if data is None:
                r = http.get(url, params=params, headers=headers, timeout=180)
            else:
                r = http.post(url, params=params, data=data, headers=headers, timeout=180)
            r.content
            break
        except (requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError,
                requests.exceptions.Timeout) as err:
            assert attempt < 2, f"Request failed 3 times: {url} ({err})"
            time.sleep(10)
    retrieved = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if r.status_code == 404:
        entry = {"url": r.url, "status": 404, "retrieved_utc": retrieved, "body": None}
    else:
        assert r.status_code == 200, f"HTTP {r.status_code} for {r.url}\n{r.text[:500]}"
        entry = {"url": r.url, "status": 200, "retrieved_utc": retrieved, "body": r.json() if as_json else r.text}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False)
    time.sleep(PAUSE.get(requests.utils.urlparse(url).hostname, 0.1))
    return entry


CODE_RX = re.compile(r"(?<![A-Za-z0-9])H[ \-]?(\d{1,3}) ?[/\-] ?(\d{2})(?![0-9/])")
NOSEP_RX = re.compile(r"(?<![A-Za-z0-9])H[ \-]?(\d{3,5})(?![0-9/\-])")
UNII_RX = re.compile(r"^[A-Z0-9]{10}$")


def norm(a, b):
    return f"H {a}/{b}"


def find_codes(text, allow_nosep=True):
    """All code occurrences in a string: list of dicts code_norm, form, span, start, end."""
    found = []
    for m in CODE_RX.finditer(text):
        found.append({"code_norm": norm(m.group(1), m.group(2)), "form": "sep",
                      "span": m.group(0), "start": m.start(), "end": m.end()})
    if allow_nosep:
        for m in NOSEP_RX.finditer(text):
            d = m.group(1)
            found.append({"code_norm": norm(d[:-2], d[-2:]), "form": "nosep",
                          "span": m.group(0), "start": m.start(), "end": m.end()})
    return found


REC_COLS = ["code_norm", "form", "string_as_found", "suffix", "source", "record_id", "record_label",
            "record_level", "unii", "unii_link", "field", "url", "retrieved_utc", "reference_use", "note"]
records = []


def add_names(source, record_id, record_label, record_level, names, field, url, retrieved,
              reference_use="", unii="", unii_link="", note="", allow_nosep=True):
    """Scan short name strings (synonyms, entry terms, aliases) and add one record per code occurrence."""
    for name in names:
        for c in find_codes(name, allow_nosep):
            prefix = name[:c["start"]].strip()
            suffix = name[c["end"]:].strip(" ,;()-")
            records.append({"code_norm": c["code_norm"], "form": c["form"], "string_as_found": name,
                            "suffix": suffix, "source": source, "record_id": record_id,
                            "record_label": record_label, "record_level": record_level, "unii": unii,
                            "unii_link": unii_link, "field": field, "url": url, "retrieved_utc": retrieved,
                            "reference_use": reference_use,
                            "note": (note + "; " if note else "") + (f"text before code: '{prefix}'" if prefix else "")})


def codes_so_far(sources=None, sep_only=True):
    return sorted({r["code_norm"] for r in records
                   if (sources is None or r["source"] in sources) and (not sep_only or r["form"] == "sep")})


def split_code(code_norm):
    m = re.fullmatch(r"H (\d{1,3})/(\d{2})", code_norm)
    assert m, f"Not a normalised code: {code_norm}"
    return m.group(1), m.group(2)


# Self-test of the pattern on the variants the harvest must catch
for s, expected in [("H 168/68", "H 168/68"), ("H-168/68", "H 168/68"), ("H 168-68", "H 168/68"),
                    ("H168/68", "H 168/68"), ("H 168/68 SODIUM", "H 168/68"), ("H199/18 MAGNESIUM TRIHYDRATE", "H 199/18")]:
    got = [c["code_norm"] for c in find_codes(s) if c["form"] == "sep"]
    assert got == [expected], f"{s!r}: {got}"
assert [c["code_norm"] for c in find_codes("H16868")] == ["H 168/68"]
assert find_codes("H1-100 Gene") == [] and find_codes("HOE 33378") == []
print("Pattern self-test passed")
'''))

cells.append(markdown_cell(r'''
## 3. ChEMBL: synonym regex (seed)

One server-side regex on `molecule_synonyms`. ChEMBL keeps codes on the record they were registered for, often the
salt (child) record; the parent is ChEMBL's normalised form. Trade names (`TRADE_NAME` synonyms) are collected
for parents and children.
'''))

cells.append(code_cell(r'''
chembl_mols = {}


def chembl_molecule(chembl_id):
    if chembl_id not in chembl_mols:
        e = cached_request(f"{CHEMBL_API}/molecule/{chembl_id}.json")
        assert e["body"] is not None, f"ChEMBL {chembl_id} not found"
        chembl_mols[chembl_id] = {"mol": e["body"], "retrieved": e["retrieved_utc"], "url": e["url"]}
    return chembl_mols[chembl_id]


def chembl_info(chembl_id):
    m = chembl_molecule(chembl_id)["mol"]
    parent = (m.get("molecule_hierarchy") or {}).get("parent_chembl_id") or chembl_id
    syns = m.get("molecule_synonyms") or []
    return {"pref_name": m.get("pref_name") or "", "parent": parent,
            "level": "ChEMBL parent" if parent == chembl_id else f"ChEMBL child of {parent}",
            "synonyms": sorted({s["molecule_synonym"] for s in syns}),
            "trade_names": sorted({s["molecule_synonym"] for s in syns if s.get("syn_type") == "TRADE_NAME"})}


def add_chembl(chembl_id, note=""):
    info = chembl_info(chembl_id)
    entry = chembl_molecule(chembl_id)
    add_names("ChEMBL", chembl_id, info["pref_name"], info["level"], info["synonyms"], "molecule_synonym",
              f"https://www.ebi.ac.uk/chembl/compound_report_card/{chembl_id}/", entry["retrieved"], note=note)


seed_ids, offset = [], 0
while True:
    e = cached_request(f"{CHEMBL_API}/molecule.json",
                       params={"molecule_synonyms__molecule_synonym__iregex": CHEMBL_SEED_REGEX,
                               "only": "molecule_chembl_id", "limit": 1000, "offset": offset})
    seed_ids += [m["molecule_chembl_id"] for m in e["body"]["molecules"]]
    if not e["body"]["page_meta"]["next"]:
        break
    offset += 1000

for cid in seed_ids:
    add_chembl(cid, note="ChEMBL synonym regex seed")
# Parents of seed children: their synonyms and trade names belong to the same compound
for cid in seed_ids:
    p = chembl_info(cid)["parent"]
    if p not in seed_ids:
        add_chembl(p, note=f"parent of seed record {cid}")

chembl_seed = pd.DataFrame([r for r in records if r["source"] == "ChEMBL"])
print(f"ChEMBL seed: {len(seed_ids)} molecules, {chembl_seed['code_norm'].nunique()} codes")
print("Test cases found in ChEMBL seed:", [c for c in TEST_CASES if c in set(chembl_seed["code_norm"])])
print("Test cases NOT found:          ", [c for c in TEST_CASES if c not in set(chembl_seed["code_norm"])])
chembl_seed[["code_norm", "string_as_found", "record_id", "record_label", "record_level"]].sort_values("code_norm")
'''))

cells.append(markdown_cell(r'''
## 4. MeSH: regex over all term labels

MeSH (mostly Supplementary Concept Records) writes the codes with a hyphen ("H 216-44"). Step 1 finds records with a
matching term; step 2 reads all terms of those records, so no-separator and salt variants on the same record are seen.
The registry number is a UNII only when it has the UNII form (10 characters, no hyphen); otherwise CAS or none.
'''))

cells.append(code_cell(r'''
MESH_PREFIX = """PREFIX meshv: <http://id.nlm.nih.gov/mesh/vocab#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""


def mesh_sparql(query):
    out, offset = [], 0
    while True:
        e = cached_request(MESH_SPARQL, params={"query": MESH_PREFIX + query, "format": "JSON",
                                                "limit": 1000, "offset": offset})
        rows = e["body"]["results"]["bindings"]
        out += rows
        if len(rows) < 1000:
            return out, e["retrieved_utc"]
        offset += 1000


rows, mesh_retrieved = mesh_sparql(f"""
SELECT DISTINCT ?rec WHERE {{
  ?t a meshv:Term ; meshv:prefLabel ?label .
  FILTER(STRSTARTS(STR(?label), "H"))
  FILTER(REGEX(STR(?label), "{MESH_REGEX}"))
  ?c meshv:preferredTerm|meshv:term ?t .
  ?rec meshv:preferredConcept|meshv:concept ?c .
}} ORDER BY ?rec""")
mesh_ids = sorted({r["rec"]["value"].rsplit("/", 1)[1] for r in rows})
print(f"MeSH records with a matching term: {len(mesh_ids)}")

mesh_info = {}


def load_mesh(ids, note=""):
    todo = [i for i in ids if i not in mesh_info]
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        values = " ".join(f"<http://id.nlm.nih.gov/mesh/{x}>" for x in batch)
        rows, retrieved = mesh_sparql(f"""
SELECT ?rec ?recLabel ?type ?label ?rn WHERE {{
  VALUES ?rec {{ {values} }}
  ?rec rdfs:label ?recLabel ; a ?type ; meshv:preferredConcept|meshv:concept ?c .
  ?c meshv:preferredTerm|meshv:term ?t . ?t meshv:prefLabel ?label .
  OPTIONAL {{ ?rec meshv:preferredConcept/meshv:registryNumber ?rn }}
}} ORDER BY ?rec ?label""")
        for r in rows:
            mid = r["rec"]["value"].rsplit("/", 1)[1]
            d = mesh_info.setdefault(mid, {"label": r["recLabel"]["value"], "type": r["type"]["value"].rsplit("#", 1)[1],
                                           "terms": set(), "rn": set(), "retrieved": retrieved, "note": note})
            d["terms"].add(r["label"]["value"])
            if "rn" in r and r["rn"]["value"] != "0":
                d["rn"].add(r["rn"]["value"])
    for mid in todo:
        assert mid in mesh_info, f"MeSH {mid}: no terms returned"
        d = mesh_info[mid]
        uniis = sorted(x for x in d["rn"] if UNII_RX.match(x))
        add_names("MeSH", mid, d["label"], d["type"], sorted(d["terms"]), "term label", MESH_UI + mid, d["retrieved"],
                  unii=";".join(uniis), unii_link="MeSH registry number" if uniis else "", note=d["note"])


load_mesh(mesh_ids, note="MeSH term regex")
mesh_df = pd.DataFrame([r for r in records if r["source"] == "MeSH"])
print(f"MeSH: {mesh_df['code_norm'].nunique()} codes on {mesh_df['record_id'].nunique()} records")
print("Test cases found in MeSH:", [c for c in TEST_CASES if c in set(mesh_df["code_norm"])])
'''))

cells.append(markdown_cell(r'''
## 5. NCI Thesaurus: regex over every synonym of the full release

The flat file (tab-separated: code, IRI, parents, synonyms, definition, display name, status, semantic type) is
downloaded once into the cache folder. The release version is read from the EVS REST API.
Concepts whose semantic type is not a substance (e.g. histone genes "H1-10") go to `set_aside`.
'''))

cells.append(code_cell(r'''
ncit_zip = f"{CACHE_DIR}/Thesaurus.FLAT.zip"
if not os.path.exists(ncit_zip):
    r = http.get(NCIT_FLAT_URL, timeout=600)
    assert r.status_code == 200, f"NCIt flat file: HTTP {r.status_code}"
    with open(ncit_zip, "wb") as f:
        f.write(r.content)
ncit_retrieved = datetime.fromtimestamp(os.path.getmtime(ncit_zip), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
NCIT_VERSION = cached_request(f"{NCIT_API}/concept/ncit/C716", params={"include": "minimal"})["body"]["version"]
print(f"NCIt release {NCIT_VERSION}, file retrieved {ncit_retrieved}")

ncit_info = {}
with zipfile.ZipFile(ncit_zip) as z:
    with z.open("Thesaurus.txt") as f:
        for line in io.TextIOWrapper(f, encoding="utf-8"):
            col = line.rstrip("\n").split("\t")
            syns = col[3].split("|")
            if not any(CODE_RX.search(s) for s in syns):
                continue
            stypes = col[7].split("|") if len(col) > 7 else []
            pref = col[5] if len(col) > 5 and col[5] else syns[0]
            ncit_info[col[0]] = {"pref": pref, "synonyms": syns, "semantic_types": stypes,
                                 "status": col[6] if len(col) > 6 else ""}

for code, d in ncit_info.items():
    is_substance = any(t in NCIT_SUBSTANCE_TYPES for t in d["semantic_types"]) and \
        not any(t in NCIT_NOT_SUBSTANCE_TYPES for t in d["semantic_types"])
    add_names("NCIt", code, d["pref"], "|".join(d["semantic_types"]), d["synonyms"], f"synonym (NCIt {NCIT_VERSION})",
              NCIT_UI + code, ncit_retrieved,
              note="" if is_substance else "SET_ASIDE: NCIt semantic type is not a substance")

ncit_df = pd.DataFrame([r for r in records if r["source"] == "NCIt"])
print(f"NCIt: {len(ncit_info)} concepts with a matching synonym")
ncit_df[["code_norm", "string_as_found", "record_id", "record_label", "record_level", "note"]]
'''))

cells.append(markdown_cell(r'''
## 6. GSRS: UNII, active moiety, INN, brand names

1. Phrase search for every code found so far and every test case, in three spellings.
2. Exact-name search for every substance name seen in ChEMBL, MeSH and NCIt records.
3. Full record of every hit; its active moiety; and the salts/solvates of each moiety. **All names** of every record
   are scanned for codes.

INN = a name whose naming organisation is INN (or a name tagged "[INN]"). The WHO INN number is the GSRS code of
system `INN`. Brand names = GSRS names of type `bn`.
'''))

cells.append(code_cell(r'''
gsrs = {}            # uuid -> parsed record
gsrs_by_unii = {}    # UNII -> uuid
gsrs_hits = []       # (query, uuid) for the evidence of how a record was found


def gsrs_search(q):
    """All uuids for a Lucene query, paged by 50. GSRS search is slow (6-60 s per call, 2026-11-21);
    a call that times out or returns an empty body is tried twice more, then the notebook stops."""
    uuids, skip = [], 0
    while True:
        for attempt in range(3):
            try:
                e = cached_request(f"{GSRS_API}/substances/search", params={"q": q, "top": 50, "skip": skip, "fdim": 0})
                break
            except (requests.exceptions.RequestException, ValueError) as err:
                assert attempt < 2, f"GSRS search failed 3 times: {q[:200]} ({err})"
                time.sleep(10)
        assert e["body"] is not None, f"GSRS search failed: {q[:200]}"
        uuids += [c["uuid"] for c in e["body"]["content"]]
        skip += 50
        if skip >= e["body"]["total"]:
            return uuids


def chunks(items, n):
    items = sorted(items)
    return [items[i:i + n] for i in range(0, len(items), n)]


def gsrs_load(ref):
    """ref = uuid or UNII. Returns uuid."""
    if ref in gsrs_by_unii:
        return gsrs_by_unii[ref]
    if ref in gsrs:
        return ref
    e = cached_request(f"{GSRS_API}/substances({ref})", params={"view": "full"})
    assert e["body"] is not None, f"GSRS record not found: {ref}"
    s = e["body"]
    names = s.get("names") or []
    rels = s.get("relationships") or []
    moiety = [r["relatedSubstance"] for r in rels if r["type"] == "ACTIVE MOIETY"]
    inn = sorted({re.sub(r"\s*\[INN\]$", "", n["name"]) for n in names
                  if any(o.get("nameOrg") == "INN" for o in (n.get("nameOrgs") or [])) or n["name"].endswith("[INN]")})
    codes = defaultdict(list)
    for c in s.get("codes") or []:
        codes[c["codeSystem"]].append(c["code"])
    d = {"uuid": s["uuid"], "unii": s.get("approvalID") or "", "name": s.get("_name") or "",
         "class": s.get("substanceClass") or "", "names": [n["name"] for n in names],
         "moiety_unii": moiety[0].get("approvalID") if len(moiety) == 1 else "",
         "moiety_name": moiety[0].get("refPname") if len(moiety) == 1 else "",
         "moiety_count": len(moiety),
         "moieties": [m.get("approvalID") for m in moiety if m.get("approvalID")],
         "salts": [r["relatedSubstance"].get("approvalID") or r["relatedSubstance"].get("refuuid")
                   for r in rels if "SALT/SOLVATE" in r["type"]],
         "inn": inn, "inn_number": sorted(set(codes.get("INN", []))),
         "brands": sorted({re.sub(r"\s*\[.*\]$", "", n["name"]) for n in names if n.get("type") == "bn"}),
         "chembl": sorted(set(codes.get("ChEMBL", []))), "mesh": sorted(set(codes.get("MESH", []))),
         "ncit": sorted(set(codes.get("NCI_THESAURUS", []))), "pubchem": sorted(set(codes.get("PUBCHEM", []))),
         "retrieved": e["retrieved_utc"]}
    gsrs[d["uuid"]] = d
    if d["unii"]:
        gsrs_by_unii[d["unii"]] = d["uuid"]
    return d["uuid"]


def gsrs_level(d):
    if d["moiety_count"] == 0:
        return "GSRS: no active moiety relationship"
    if d["moiety_count"] > 1:
        return "GSRS: several active moieties"
    return "GSRS: active moiety" if d["moiety_unii"] == d["unii"] else f"GSRS: form of moiety {d['moiety_unii']}"


# 1. Phrase search per code, 10 codes per query. GSRS indexes "/" and "-" alike ("H 168-68" finds "H 168/68",
#    checked 2026-11-21), so two spellings per code: with separator and without.
for batch in chunks(set(codes_so_far()) | set(TEST_CASES), 10):
    clauses = []
    for code in batch:
        a, b = split_code(code)
        clauses += [f'root_names_name:"H {a}/{b}"', f'root_names_name:"H{a}{b}"']
    q = " OR ".join(clauses)
    for u in gsrs_search(q):
        gsrs_hits.append((q, u))

# 2. Exact-name search per substance name seen in other sources (names that are themselves codes are covered by 1)
other_names = set()
for r in records:
    if r["source"] in ("ChEMBL", "MeSH", "NCIt") and "SET_ASIDE" not in r["note"]:
        if r["record_label"] and not find_codes(r["record_label"]):
            other_names.add(r["record_label"])
for cid in list(chembl_mols):
    p = chembl_info(cid)["pref_name"]
    if p:
        other_names.add(p)
for batch in chunks(other_names, 10):
    q = " OR ".join('root_names_name:"^' + n.replace('"', '\\"') + '$"' for n in batch)
    for u in gsrs_search(q):
        gsrs_hits.append((q, u))

# Exact-name link (record label -> GSRS uuid), checked against the names of the loaded records below
name_hits = defaultdict(list)

# 3. Full records, their moieties, and the salts of each moiety
for _, u in gsrs_hits:
    gsrs_load(u)
for u in list(gsrs):
    if gsrs[u]["moiety_unii"]:
        gsrs_load(gsrs[u]["moiety_unii"])
for u in list(gsrs):
    d = gsrs[u]
    if d["moiety_unii"] == d["unii"]:
        for s in d["salts"]:
            if s:
                gsrs_load(s)

other_upper = {n.upper() for n in other_names}
for u, d in gsrs.items():
    for n in {x.upper() for x in d["names"]} & other_upper:
        name_hits[n].append(u)

for u, d in gsrs.items():
    add_names("GSRS", d["unii"] or u, d["name"], gsrs_level(d), d["names"], "name", f"{GSRS_UI}/{u}", d["retrieved"],
              unii=d["unii"], unii_link="GSRS record")

gsrs_df = pd.DataFrame([r for r in records if r["source"] == "GSRS"])
print(f"GSRS: {len(gsrs)} records loaded, {gsrs_df['code_norm'].nunique()} codes in their names")
print("Test cases found in GSRS:", [c for c in TEST_CASES if c in set(gsrs_df["code_norm"])])
'''))

cells.append(markdown_cell(r'''
### 6b. Link records of the other sources to a UNII, and follow GSRS cross-references

A ChEMBL, MeSH or NCIt record is linked to a GSRS record by the MeSH registry number when it is a UNII, else by exact
name (record label = a GSRS name), else by GSRS's own cross-reference (code systems ChEMBL, MESH, NCI_THESAURUS).
GSRS puts the same cross-reference on the moiety and its salts, so a cross-reference link to several UNIIs drops the
salts of a UNII in the same set. The link method is kept in
`unii_link`. ChEMBL, MeSH and NCIt records named by GSRS cross-references of the moieties and salts are read and
scanned too (catches codes on compounds the seed regexes did not reach).
'''))

cells.append(code_cell(r'''
xref = {"ChEMBL": defaultdict(set), "MeSH": defaultdict(set), "NCIt": defaultdict(set), "PubChem": defaultdict(set)}
for d in gsrs.values():
    for sys_, key in [("ChEMBL", "chembl"), ("MeSH", "mesh"), ("NCIt", "ncit"), ("PubChem", "pubchem")]:
        for x in d[key]:
            if d["unii"]:
                xref[sys_][x].add(d["unii"])

# Read records named by GSRS cross-references that are not loaded yet
for d in list(gsrs.values()):
    for x in d["chembl"]:
        if x not in chembl_mols:
            add_chembl(x, note=f"via GSRS cross-reference of {d['unii']}")
    load_mesh([x for x in d["mesh"] if re.fullmatch(r"[CD]\d+", x)], note=f"via GSRS cross-reference")
missing_ncit = sorted({x for d in gsrs.values() for x in d["ncit"]} - set(ncit_info))
# NCIt concepts without a code synonym are not in ncit_info and need no scan (the flat-file regex saw all synonyms)


def reduce_to_moiety(uniis):
    """A MeSH descriptor, NCIt concept or ChEMBL parent is cross-referenced from the moiety and its salts in GSRS.
    When a link reaches several UNIIs, drop those whose GSRS active moiety is another UNII in the same set."""
    if len(uniis) < 2:
        return uniis, ""
    keep = [u for u in uniis if not (set(gsrs[gsrs_by_unii[u]]["moieties"]) - {u}) & set(uniis)]
    return (keep, f" (reduced from {len(uniis)} UNIIs: salts of a UNII in the set dropped)") \
        if keep and len(keep) < len(uniis) else (uniis, "")


def link_unii(r):
    """Exact name first (most specific), then GSRS cross-reference."""
    if r["source"] in ("GSRS",) or r["unii"]:
        return r
    by_name = sorted({gsrs[u]["unii"] for u in name_hits.get((r["record_label"] or "").upper(), []) if gsrs[u]["unii"]})
    if by_name:
        u, how = reduce_to_moiety(by_name)
        r["unii"], r["unii_link"] = ";".join(u), f"GSRS exact name = record label{how}"
        return r
    by_xref = sorted(xref.get(r["source"], {}).get(r["record_id"], set()))
    if by_xref:
        u, how = reduce_to_moiety(by_xref)
        r["unii"], r["unii_link"] = ";".join(u), f"GSRS cross-reference {r['source']}{how}"
    return r


records = [link_unii(r) for r in records]
print(f"Records: {len(records)}; without UNII: {sum(1 for r in records if not r['unii'])}")
'''))

cells.append(markdown_cell(r'''
## 7. PubChem: cross-check only

Name lookup (POST, so the slash in the code is safe) for each code in five spellings, then the synonyms of every CID
found. PubChem synonyms are depositor aggregations: they confirm or contradict, they are never a Wikidata reference.
'''))

cells.append(code_cell(r'''
pubchem_cids = defaultdict(set)   # cid -> codes looked up
for code in sorted(set(codes_so_far()) | set(TEST_CASES)):
    a, b = split_code(code)
    for form in [f"H {a}/{b}", f"H-{a}/{b}", f"H {a}-{b}", f"H{a}/{b}", f"H{a}{b}"]:
        e = cached_request(f"{PUBCHEM_API}/compound/name/cids/JSON", data={"name": form})
        if e["body"]:
            for cid in e["body"]["IdentifierList"]["CID"]:
                pubchem_cids[cid].add(code)

cids = sorted(pubchem_cids)
for i in range(0, len(cids), 100):
    batch = cids[i:i + 100]
    e = cached_request(f"{PUBCHEM_API}/compound/cid/synonyms/JSON", data={"cid": ",".join(map(str, batch))})
    for info in e["body"]["InformationList"]["Information"]:
        cid = info["CID"]
        unii = sorted(xref["PubChem"].get(str(cid), set()))
        add_names("PubChem", str(cid), (info.get("Synonym") or [""])[0], "PubChem CID", info.get("Synonym") or [],
                  "synonym", f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}", e["retrieved_utc"],
                  reference_use="N (cross-check only)", unii=";".join(unii),
                  unii_link="GSRS cross-reference PUBCHEM" if unii else "",
                  note=f"found by name lookup of {', '.join(sorted(pubchem_cids[cid]))}")

pc_df = pd.DataFrame([r for r in records if r["source"] == "PubChem"])
print(f"PubChem: {len(cids)} CIDs, {pc_df['code_norm'].nunique() if len(pc_df) else 0} codes in their synonyms")
'''))

cells.append(markdown_cell(r'''
## 8. PubMed: discovery from Hässle affiliations, then earliest verified record per code

- **Discovery:** all records matching `PUBMED_AFFILIATION_QUERY` are scanned (title, abstract, substance names,
  keywords). PubMed has author affiliations mainly from 1988 on, so this finds late codes.
- **Verification:** per code one search in several spellings. PubMed splits "H 124/26" into `h AND "124 26"`, so
  every hit is checked: the code must be in title, abstract, substance list or keywords. Also, when a code is a
  MeSH entry term (felodipine "H 154/82"), PubMed's All Fields search returns every paper indexed with that compound.
- **Earliest record** = lowest publication year (then PMID) among verified records: a latest-possible date for the
  synthesis. Before ~1975 many records have no abstract, so early mentions can be missed.
'''))

cells.append(code_cell(r'''
pubmed = {}   # pmid -> parsed article


def esearch(term):
    e = cached_request(f"{EUTILS}/esearch.fcgi", params={"db": "pubmed", "term": term, "retmax": PUBMED_RETMAX,
                                                         "retmode": "json", "tool": "development-code-archaeology"})
    res = e["body"]["esearchresult"]
    assert int(res["count"]) <= PUBMED_RETMAX, f"PubMed search > {PUBMED_RETMAX} hits: {term}"
    return res["idlist"], res.get("querytranslation", "")


def text_of(el):
    return "".join(el.itertext()).strip() if el is not None else ""


def efetch(pmids):
    todo = sorted(set(pmids) - set(pubmed), key=int)
    for i in range(0, len(todo), 100):
        batch = todo[i:i + 100]
        e = cached_request(f"{EUTILS}/efetch.fcgi", params={"db": "pubmed", "id": ",".join(batch), "retmode": "xml",
                                                            "tool": "development-code-archaeology"}, as_json=False)
        root = ET.fromstring(e["body"])
        for art in root.findall("PubmedArticle"):
            pmid = art.findtext("MedlineCitation/PMID")
            a = art.find("MedlineCitation/Article")
            pd_ = a.find("Journal/JournalIssue/PubDate")
            year = pd_.findtext("Year") or (pd_.findtext("MedlineDate") or "")[:4]
            pubmed[pmid] = {
                "pmid": pmid, "year": int(year) if year.isdigit() else None,
                "journal": a.findtext("Journal/ISOAbbreviation") or a.findtext("Journal/Title") or "",
                "title": text_of(a.find("ArticleTitle")),
                "abstract": " ".join(text_of(x) for x in a.findall("Abstract/AbstractText")),
                "substances": [text_of(x) for x in art.findall("MedlineCitation/ChemicalList/Chemical/NameOfSubstance")],
                "keywords": [text_of(x) for x in art.findall("MedlineCitation/KeywordList/Keyword")],
                "affiliations": sorted({text_of(x) for x in a.findall("AuthorList/Author/AffiliationInfo/Affiliation")}),
                "retrieved": e["retrieved_utc"]}
        # Book records (e.g. LactMed chapters) come as PubmedBookArticle
        for art in root.findall("PubmedBookArticle"):
            doc = art.find("BookDocument")
            pmid = doc.findtext("PMID")
            year = doc.findtext("Book/PubDate/Year") or ""
            pubmed[pmid] = {
                "pmid": pmid, "year": int(year) if year.isdigit() else None,
                "journal": "Book: " + text_of(doc.find("Book/BookTitle")),
                "title": text_of(doc.find("ArticleTitle")) or text_of(doc.find("Book/BookTitle")),
                "abstract": " ".join(text_of(x) for x in doc.findall("Abstract/AbstractText")),
                "substances": [], "keywords": [text_of(x) for x in doc.findall("KeywordList/Keyword")],
                "affiliations": [], "retrieved": e["retrieved_utc"]}
        missing = set(batch) - set(pubmed)
        assert not missing, f"efetch returned no record for {sorted(missing)[:5]}"


def pubmed_codes(p):
    """Codes in an article, per field (separator form only)."""
    out = []
    for field, texts in [("title", [p["title"]]), ("abstract", [p["abstract"]]),
                         ("substance", p["substances"]), ("keyword", p["keywords"])]:
        for t in texts:
            for c in find_codes(t, allow_nosep=False):
                ctx = t[max(0, c["start"] - 60):c["end"] + 60].replace("\n", " ")
                out.append((c["code_norm"], c["span"], field, ctx))
    return out


ASTRA_RX = re.compile(r"H[äa]ssle|Astra", re.I)


def add_pubmed(pmid, only_codes=None, note=""):
    p = pubmed[pmid]
    affil = "; ".join(x for x in p["affiliations"] if ASTRA_RX.search(x))
    for code, span, field, ctx in pubmed_codes(p):
        if only_codes is not None and code not in only_codes:
            continue
        records.append({"code_norm": code, "form": "sep", "string_as_found": span, "suffix": "", "source": "PubMed",
                        "record_id": pmid, "record_label": p["title"][:200], "record_level": f"article {p['year']}",
                        "unii": "", "unii_link": "", "field": field,
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", "retrieved_utc": p["retrieved"],
                        "reference_use": "", "note": f"{note}; context: ...{ctx}...; Astra/Hässle affiliation: {affil or 'none'}"})


# Discovery
disc_ids, disc_translation = esearch(PUBMED_AFFILIATION_QUERY)
efetch(disc_ids)
for pmid in disc_ids:
    add_pubmed(pmid, note="Hässle-affiliation discovery")
print(f"Discovery: {len(disc_ids)} Hässle-affiliation records ({disc_translation})")

# Verification per code
all_codes = sorted(set(codes_so_far()) | set(TEST_CASES) | {r["code_norm"] for r in records if r["source"] == "PubMed"})
search_log = []
for code in all_codes:
    a, b = split_code(code)
    forms = [f'"H {a}/{b}"', f'"H-{a}/{b}"', f'"H {a}-{b}"', f'"H{a}/{b}"', f'"H{a}-{b}"']
    term = " OR ".join(forms)
    ids, translation = esearch(term)
    efetch(ids)
    seen = {(r["record_id"]) for r in records if r["source"] == "PubMed" and r["code_norm"] == code}
    for pmid in ids:
        if pmid not in seen:
            add_pubmed(pmid, only_codes={code}, note="code search")
    verified = {r["record_id"] for r in records if r["source"] == "PubMed" and r["code_norm"] == code}
    search_log.append({"code_norm": code, "pubmed_term": term, "hits": len(ids), "verified": len(verified & set(ids)),
                       "query_translation": translation})

search_log = pd.DataFrame(search_log)
print(f"PubMed records fetched: {len(pubmed)}")
search_log[search_log["code_norm"].isin(TEST_CASES)]
'''))

cells.append(markdown_cell(r'''
## 9. Wikidata: what exists already (read only)

Items are found four ways: P15001 values matching the pattern; P652 (UNII) for every GSRS UNII; P592 (ChEMBL) and
P486 (MeSH) for every ID seen; full-text search per code. All labels and aliases (all languages) and P15001 values of
those items are scanned. INN statements (P2275) are read with the item cited in their references (P1433 / P248, P577).
'''))

cells.append(code_cell(r'''
def wd_sparql(query):
    e = cached_request(WD_SPARQL, data={"query": query}, headers={"Accept": "application/sparql-results+json"})
    return e["body"]["results"]["bindings"], e["retrieved_utc"]


wd_found = defaultdict(set)   # qid -> how found

rows, _ = wd_sparql('SELECT ?item ?code WHERE { ?item wdt:P15001 ?code . '
                    'FILTER(REGEX(?code, "^H[ -]?[0-9]{1,3} ?[/-] ?[0-9]{2}")) }')
for r in rows:
    wd_found[r["item"]["value"].rsplit("/", 1)[1]].add("P15001 pattern")

id_sets = {"P652": sorted({d["unii"] for d in gsrs.values() if d["unii"]}),
           "P592": sorted({r["record_id"] for r in records if r["source"] == "ChEMBL"} |
                          {x for d in gsrs.values() for x in d["chembl"]}),
           "P486": sorted({r["record_id"] for r in records if r["source"] == "MeSH"} |
                          {x for d in gsrs.values() for x in d["mesh"]})}
for prop, ids in id_sets.items():
    for i in range(0, len(ids), 200):
        values = " ".join(json.dumps(x) for x in ids[i:i + 200])
        rows, _ = wd_sparql(f"SELECT ?item ?v WHERE {{ VALUES ?v {{ {values} }} ?item wdt:{prop} ?v . }}")
        for r in rows:
            wd_found[r["item"]["value"].rsplit("/", 1)[1]].add(f"{prop} {r['v']['value']}")

for code in all_codes:
    a, b = split_code(code)
    for q in [f'"H {a}/{b}"', f'"H {a}-{b}"']:
        e = cached_request(WD_API, params={"action": "query", "list": "search", "srsearch": q, "srnamespace": 0,
                                           "srlimit": 20, "format": "json"})
        for hit in e["body"]["query"]["search"]:
            wd_found[hit["title"]].add(f"text search {q}")

wd_items = {}
qids = sorted(wd_found)
for i in range(0, len(qids), 50):
    e = cached_request(WD_API, params={"action": "wbgetentities", "ids": "|".join(qids[i:i + 50]),
                                       "props": "labels|aliases|claims|sitelinks", "format": "json"})
    for qid, ent in e["body"]["entities"].items():
        ent["_retrieved"] = e["retrieved_utc"]
        wd_items[qid] = ent


def claim_values(ent, prop):
    out = []
    for c in ent.get("claims", {}).get(prop, []):
        dv = c["mainsnak"].get("datavalue")
        if dv:
            v = dv["value"]
            out.append((v["id"] if isinstance(v, dict) and "id" in v else v, c))
    return out


# INN list items referenced by P2275 statements
list_qids = set()
for ent in wd_items.values():
    for _, c in claim_values(ent, "P2275"):
        for ref in c.get("references", []):
            for p in ("P1433", "P248"):
                for s in ref["snaks"].get(p, []):
                    if s.get("datavalue"):
                        list_qids.add(s["datavalue"]["value"]["id"])
list_labels = {}
lq = sorted(list_qids)
for i in range(0, len(lq), 50):
    e = cached_request(WD_API, params={"action": "wbgetentities", "ids": "|".join(lq[i:i + 50]),
                                       "props": "labels", "languages": "en", "format": "json"})
    for qid, ent in e["body"]["entities"].items():
        list_labels[qid] = ent.get("labels", {}).get("en", {}).get("value", "")


def inn_statements(ent):
    out = []
    for v, c in claim_values(ent, "P2275"):
        lang = v.get("language", "") if isinstance(v, dict) else ""
        text = v.get("text", v) if isinstance(v, dict) else v
        if lang not in ("en", ""):
            continue
        refs = []
        for ref in c.get("references", []):
            lists = [s["datavalue"]["value"]["id"] for p in ("P1433", "P248") for s in ref["snaks"].get(p, [])
                     if s.get("datavalue")]
            dates = [s["datavalue"]["value"]["time"][1:5] for s in ref["snaks"].get("P577", []) if s.get("datavalue")]
            if lists:
                refs.append(f"{', '.join(list_labels.get(q, q) + ' (' + q + ')' for q in lists)}"
                            f"{' ' + ','.join(dates) if dates else ''}")
        out.append(f"{text}" + (f" [{'; '.join(refs)}]" if refs else " [no P1433/P248 reference]"))
    return out


SCHOLARLY_ARTICLE = "Q13442814"
wd_rows = []
for qid, ent in wd_items.items():
    labels = {l: v["value"] for l, v in ent.get("labels", {}).items()}
    url = f"https://www.wikidata.org/wiki/{qid}"
    p31 = [v for v, _ in claim_values(ent, "P31")]
    # Text search also returns scholarly-article items whose title names a code: dating evidence, not compound items
    wd_note = "SET_ASIDE: Wikidata scholarly article (title names the code)" if SCHOLARLY_ARTICLE in p31 else ""
    for lang, vals in ent.get("aliases", {}).items():
        add_names("Wikidata", qid, labels.get("en", ""), "item", [v["value"] for v in vals], f"alias ({lang})",
                  url, ent["_retrieved"], note=wd_note)
    for lang, lab in labels.items():
        add_names("Wikidata", qid, labels.get("en", ""), "item", [lab], f"label ({lang})", url, ent["_retrieved"],
                  note=wd_note)
    add_names("Wikidata", qid, labels.get("en", ""), "item", [v for v, _ in claim_values(ent, "P15001")], "P15001",
              url, ent["_retrieved"], note=wd_note)
    wd_rows.append({"qid": qid, "label_en": labels.get("en", ""), "found_by": "; ".join(sorted(wd_found[qid])),
                    "P31": "; ".join(p31), "scholarly_article": "Y" if wd_note else "",
                    "P652_unii": "; ".join(v for v, _ in claim_values(ent, "P652")),
                    "P592_chembl": "; ".join(v for v, _ in claim_values(ent, "P592")),
                    "P486_mesh": "; ".join(v for v, _ in claim_values(ent, "P486")),
                    "P2275_inn": "; ".join(inn_statements(ent)),
                    "P15001": "; ".join(v for v, _ in claim_values(ent, "P15001")),
                    "sitelinks": len(ent.get("sitelinks", {})), "retrieved_utc": ent["_retrieved"]})
wd_df = pd.DataFrame(wd_rows).sort_values("qid") if wd_rows else pd.DataFrame()
print(f"Wikidata: {len(wd_items)} items read")
'''))

cells.append(markdown_cell(r'''
## 10. Evidence table, set-aside and accepted no-separator forms
'''))

cells.append(code_cell(r'''
ev = pd.DataFrame(records, columns=REC_COLS).drop_duplicates(
    subset=["code_norm", "string_as_found", "source", "record_id", "field"]).reset_index(drop=True)

STRUCTURED = ["ChEMBL", "GSRS", "MeSH", "NCIt"]

# A no-separator form counts only when the same record also has the code with a separator
# (PubChem name lookup of "H37695" returned trimethylarsine, CID 68978, 2026-11-21)
sep_on_record = set(zip(ev.loc[ev["form"] == "sep", "code_norm"], ev.loc[ev["form"] == "sep", "source"],
                        ev.loc[ev["form"] == "sep", "record_id"]))

ev["status"] = "kept"
nosep = ev["form"] == "nosep"
same_rec = pd.Series([(c, s, r) in sep_on_record for c, s, r in zip(ev["code_norm"], ev["source"], ev["record_id"])],
                     index=ev.index)
ev.loc[nosep & same_rec, "status"] = "kept: no-separator form, same record has the code with separator"
ev.loc[nosep & ~same_rec, "status"] = "set aside: no-separator form, record has no separator form of the code"
first_word = ev["suffix"].str.lower().str.extract(r"^([a-z]+)", expand=False).fillna("")
ev.loc[first_word.isin(GENE_PROTEIN_SUFFIX), "status"] = "set aside: gene or protein name"
ev.loc[ev["note"].str.contains("SET_ASIDE: NCIt"), "status"] = "set aside: NCIt semantic type is not a substance"
ev.loc[ev["note"].str.contains("SET_ASIDE: Wikidata scholarly"), "status"] = "set aside: Wikidata scholarly article"

# A code whose structured and Wikidata records are all set aside (e.g. histone "H1-10") is set aside as a whole:
# its PubMed and PubChem hits name the same gene/protein
kept_main = set(ev.loc[ev["status"].str.startswith("kept") & ev["source"].isin(STRUCTURED + ["Wikidata"]), "code_norm"])
aside_main = set(ev.loc[~ev["status"].str.startswith("kept") & ev["source"].isin(STRUCTURED + ["Wikidata"]), "code_norm"])
whole = aside_main - kept_main
ev.loc[ev["code_norm"].isin(whole) & ev["status"].str.startswith("kept"), "status"] = \
    "set aside: all structured records of this code set aside"

kept = ev[ev["status"].str.startswith("kept")].copy()
set_aside = ev[~ev["status"].str.startswith("kept")].copy()
print(f"Evidence rows: {len(ev)} kept {len(kept)}, set aside {len(set_aside)}")
print(kept.groupby("source")["code_norm"].nunique().rename("codes"))
'''))

cells.append(markdown_cell(r'''
## 11. One row per code

- **Moiety**: the GSRS active moiety of every UNII linked to a record of the code. Caution: GSRS ACTIVE MOIETY can be
  the pharmacologically active species, not the regulatory moiety: for omeprazole and esomeprazole GSRS lists the
  acid-activated sulfenamide / sulfenic acid forms (checked 2026-11-21). Such cases show as "several active moieties"
  or "UNII without GSRS active moiety" and are left to the reviewer. One moiety = resolved; several =
  flagged and all listed; none = names from the other sources only.
- **Level**: `moiety` when the code (without salt suffix) is on a record at moiety level (GSRS active moiety, ChEMBL
  parent, or a MeSH/NCIt/Wikidata record linked to the moiety UNII). Strings with a suffix are listed in `salt_forms`
  with their record. A code without suffix found only on salt-level records is flagged.
- **INN, WHO INN number, brands**: GSRS records of the carriers and the active moiety, each with its UNII
  (brands also from GSRS salt records and ChEMBL trade names). Wikidata P2275 is shown with the item cited in its reference (P1433 / P248 + P577): a WHO Recommended INN list
  item where present, otherwise whatever is cited (often ChEMBL or ChEBI). WHO list numbers are not looked up here.
- **Carrier**: the UNII(s) of records that carry the code *without* a salt suffix. When a carrier's GSRS active moiety
  is another substance (salt, or prodrug: GSRS gives melagatran as active moiety of ximelagatran) it is flagged.
- **Wikidata QIDs**: compound items with P652 = carrier UNII and = moiety UNII (design rule: if several, prefer the one
  with P2275 or sitelinks). Scholarly-article items are not compound items.
- **Hässle flag**: raised only when verified PubMed records naming the code have affiliations and none is Hässle.
'''))

cells.append(code_cell(r'''
def uniis_of(df):
    return sorted({u for x in df["unii"] if x for u in x.split(";")})


def moiety_of(unii):
    u = gsrs_by_unii.get(unii)
    return gsrs[u]["moiety_unii"] if u and gsrs[u]["moiety_unii"] else ""


def gs(unii):
    return gsrs[gsrs_by_unii[unii]] if unii in gsrs_by_unii else None


def inn_list(uniis, moiety):
    """INN names of the given GSRS records, case-insensitively deduplicated (lowercase form kept), with record."""
    out, seen = [], set()
    for u in uniis + ([moiety] if moiety and moiety not in uniis else []):
        d = gs(u)
        if not d:
            continue
        names = sorted(d["inn"], key=lambda n: (n != n.lower(), n))
        for n in names:
            if n.casefold() in seen:
                continue
            seen.add(n.casefold())
            out.append(f"{n} [GSRS {u}{', active moiety' if u == moiety else ''}]")
    return out


def qids_for(uniis):
    return sorted(q for q, ent in wd_items.items()
                  if set(uniis) & {v for v, _ in claim_values(ent, "P652")} and q in wd_compound_items)


wd_compound_items = {q for q, ent in wd_items.items() if SCHOLARLY_ARTICLE not in [v for v, _ in claim_values(ent, "P31")]}

rows = []
for code, g in kept.groupby("code_norm"):
    flags = []
    srcs = sorted(g["source"].unique())
    structured = [s for s in srcs if s in STRUCTURED]
    if not structured:
        flags.append(f"only in {', '.join(srcs)}")

    # UNIIs: all linked (not PubChem), carriers = records with the code without salt suffix
    uniis = uniis_of(g[g["source"] != "PubChem"])
    no_suffix = g[(g["suffix"] == "") & g["source"].isin(STRUCTURED)]
    carriers = uniis_of(no_suffix)
    moieties = sorted({moiety_of(u) for u in uniis if moiety_of(u)})
    if len(moieties) > 1:
        flags.append("several active moieties: " + ", ".join(f"{gs(m)['name'] if gs(m) else ''} ({m})" for m in moieties))
    if uniis and not moieties:
        flags.append("UNII without GSRS active moiety")
    moiety = moieties[0] if len(moieties) == 1 else ""
    md = gs(moiety) if moiety else None
    for u in carriers:
        m = moiety_of(u)
        if m and m != u:
            flags.append(f"code without suffix on {gs(u)['name']} ({u}), GSRS active moiety {gs(m)['name'] if gs(m) else ''} ({m})")

    names = sorted({f"{r.record_label} [{r.source} {r.record_id}]" for r in g.itertuples()
                    if r.source in STRUCTURED and r.record_label and not find_codes(r.record_label)})

    # Level
    def at_moiety(r):
        if r.source == "GSRS":
            return r.record_level == "GSRS: active moiety"
        if r.source == "ChEMBL":
            return r.record_level == "ChEMBL parent"
        if r.source in ("MeSH", "NCIt"):
            return (bool(moiety) and moiety in (r.unii or "").split(";")) or not r.unii
        return False
    level = "moiety" if any(at_moiety(r) for r in no_suffix.itertuples()) else ""
    if len(no_suffix) and not level:
        flags.append("code without salt suffix only on salt-level records")
    with_suffix = g[(g["suffix"] != "") & g["source"].isin(STRUCTURED + ["Wikidata"])]
    salt_forms = sorted({f"{r.string_as_found} [{r.source} {r.record_id}]" for r in with_suffix.itertuples()})
    salt_recs = sorted({f"{gs(u)['name']} ({u})" for u in uniis if gs(u) and moiety and u != moiety})

    # INN and brands (carriers first, then active moiety)
    inn = inn_list(carriers or uniis, moiety)
    inn_no = sorted({f"{n} [GSRS {u}]" for u in (carriers or uniis) + ([moiety] if moiety else []) if gs(u)
                     for n in gs(u)["inn_number"]})
    brands = []
    b = set()
    for u in set(uniis) | ({moiety} if moiety else set()):
        if gs(u):
            b |= set(gs(u)["brands"])
    if md:
        for s_ in md["salts"]:
            if gs(s_):
                b |= set(gs(s_)["brands"])
    if b:
        brands.append("GSRS: " + ", ".join(sorted(b)))
    chembl_ids = sorted(set(g.loc[g["source"] == "ChEMBL", "record_id"]) |
                        {x for u in uniis if gs(u) for x in gs(u)["chembl"]})
    tn = sorted({t for c in chembl_ids if c in chembl_mols for t in chembl_info(c)["trade_names"]})
    if tn:
        brands.append("ChEMBL: " + ", ".join(tn))
    chembl_parents = sorted({chembl_info(c)["parent"] for c in chembl_ids if c in chembl_mols})
    mesh_ids = sorted(set(g.loc[g["source"] == "MeSH", "record_id"]) | {x for u in uniis if gs(u) for x in gs(u)["mesh"]})
    ncit_ids = sorted(set(g.loc[g["source"] == "NCIt", "record_id"]) | {x for u in uniis if gs(u) for x in gs(u)["ncit"]})

    # Wikidata (compound items only)
    wd_carrier = qids_for(carriers)
    wd_moiety = qids_for([moiety]) if moiety else []
    for u in sorted(set(carriers) | ({moiety} if moiety else set())):
        qs = qids_for([u])
        if len(qs) > 1:
            flags.append(f"several Wikidata items with UNII {u}: {', '.join(qs)}")
    wd_code = g[(g["source"] == "Wikidata") & g["record_id"].isin(wd_compound_items)]
    wd_alias = sorted({f"{r.string_as_found} [{r.record_id} {r.field}]" for r in wd_code.itertuples() if r.field != "P15001"})
    wd_p15001 = sorted({f"{r.string_as_found} [{r.record_id}]" for r in wd_code.itertuples() if r.field == "P15001"})
    other_items = sorted(set(wd_code["record_id"]) - set(wd_carrier) - set(wd_moiety))
    if other_items and (wd_carrier or wd_moiety):
        flags.append(f"code on Wikidata item(s) {', '.join(other_items)}, not the carrier/moiety item")
    wd_inn = " | ".join(f"{q}: " + "; ".join(inn_statements(wd_items[q])) for q in sorted(set(wd_carrier + wd_moiety))
                        if inn_statements(wd_items[q]))

    # PubMed
    pm = g[g["source"] == "PubMed"]
    pm_years = sorted({(pubmed[p]["year"] or 9999, int(p)) for p in pm["record_id"]})
    first = pubmed[str(pm_years[0][1])] if pm_years else None
    first_fields = sorted(set(pm.loc[pm["record_id"] == first["pmid"], "field"])) if first else []
    affils = sorted({a for p in pm["record_id"] for a in pubmed[p]["affiliations"] if ASTRA_RX.search(a)})
    hassle_pmids = sorted({p for p in pm["record_id"]
                           if any(re.search(r"H[äa]ssle", a, re.I) for a in pubmed[p]["affiliations"])}, key=int)
    with_affil = sorted({p for p in pm["record_id"] if pubmed[p]["affiliations"]}, key=int)
    if with_affil and not hassle_pmids:
        flags.append(f"{len(with_affil)} PubMed record(s) naming the code have affiliations, none Hässle")
    pc = g[g["source"] == "PubChem"]

    rows.append({
        "code_norm": code,
        "test_case": TEST_CASES.get(code, ""),
        "strings_as_found": " | ".join(sorted(set(g.loc[g["source"] != "PubMed", "string_as_found"]))),
        "substance_names": " | ".join(names),
        "level": level,
        "carrier_uniis": " | ".join(f"{gs(u)['name'] if gs(u) else ''} ({u})" for u in carriers),
        "salt_forms": " | ".join(salt_forms),
        "moiety_unii": moiety or " | ".join(moieties),
        "moiety_name": md["name"] if md else "",
        "salt_records_gsrs": " | ".join(salt_recs),
        "uniis_linked": " | ".join(uniis),
        "pubchem_linked_uniis": " | ".join(uniis_of(pc)) if len(pc) else "",
        "inn": " | ".join(inn),
        "who_inn_number": " | ".join(inn_no),
        "wikidata_inn_with_reference": wd_inn,
        "brand_names": " | ".join(brands),
        "chembl_ids": " | ".join(chembl_ids), "chembl_parents": " | ".join(chembl_parents),
        "mesh_ids": " | ".join(mesh_ids), "ncit_codes": " | ".join(ncit_ids),
        "wikidata_qid_carrier": " | ".join(wd_carrier),
        "wikidata_qid_moiety": " | ".join(wd_moiety),
        "wikidata_code_as_alias_or_label": " | ".join(wd_alias),
        "wikidata_p15001": " | ".join(wd_p15001),
        "earliest_pubmed_year": first["year"] if first else None,
        "earliest_pmid": first["pmid"] if first else "",
        "earliest_journal": first["journal"] if first else "",
        "earliest_title": first["title"] if first else "",
        "earliest_found_in": ", ".join(first_fields),
        "pubmed_verified_n": len(pm_years),
        "hassle_affiliated_pmids": ", ".join(hassle_pmids),
        "pubmed_affiliations": " | ".join(affils)[:2000],
        "pubchem_cids": " | ".join(sorted(set(pc["record_id"]), key=int)),
        "sources": ", ".join(srcs),
        "n_structured_sources": len(structured),
        "flags": "; ".join(flags),
    })

codes = pd.DataFrame(rows)
# Codes that resolve to the same active moiety (racemate/enantiomer, salt, or a renumbered compound)
shared = codes[codes["moiety_unii"] != ""].groupby("moiety_unii")["code_norm"].apply(list)
for m, cs in shared.items():
    if len(cs) > 1:
        for c in cs:
            i = codes.index[codes["code_norm"] == c][0]
            others = ", ".join(x for x in cs if x != c)
            codes.at[i, "flags"] = "; ".join(x for x in [codes.at[i, "flags"], f"same active moiety as {others}"] if x)
for t in TEST_CASES:
    if t not in set(codes["code_norm"]):
        codes = pd.concat([codes, pd.DataFrame([{"code_norm": t, "test_case": TEST_CASES[t],
                                                 "flags": "test case: not found in any source"}])], ignore_index=True)
codes["_a"] = codes["code_norm"].map(lambda c: int(split_code(c)[0]))
codes["_b"] = codes["code_norm"].map(lambda c: int(split_code(c)[1]))
codes = codes.sort_values(["_a", "_b"]).drop(columns=["_a", "_b"]).reset_index(drop=True)
print(f"Codes: {len(codes)}  (with moiety UNII: {(codes['moiety_unii'].fillna('') != '').sum()}, "
      f"with INN: {(codes['inn'].fillna('') != '').sum()}, dated by PubMed: {codes['earliest_pmid'].fillna('').ne('').sum()})")
codes[["code_norm", "moiety_name", "inn", "level", "earliest_pubmed_year", "sources", "flags"]]
'''))

cells.append(markdown_cell("## 12. Test cases and coverage per source"))

cells.append(code_cell(r'''
SOURCES = ["ChEMBL", "GSRS", "MeSH", "PubChem", "NCIt", "PubMed", "Wikidata"]
by_src = kept.groupby("source")["code_norm"].apply(set).to_dict()

tc = []
for t, name in TEST_CASES.items():
    row = {"code_norm": t, "expected": name}
    for s in SOURCES:
        row[s] = "Y" if t in by_src.get(s, set()) else ""
    r = codes[codes["code_norm"] == t].iloc[0]
    row["moiety_name"] = r.get("moiety_name", "")
    row["inn"] = r.get("inn", "")
    row["earliest_pubmed_year"] = r.get("earliest_pubmed_year")
    tc.append(row)
test_cases = pd.DataFrame(tc)

cov = []
all_kept = set(kept["code_norm"])
for s in SOURCES:
    cs = by_src.get(s, set())
    others = set().union(*[v for k, v in by_src.items() if k != s]) if len(by_src) > 1 else set()
    cov.append({"source": s, "evidence_rows": int((kept["source"] == s).sum()), "codes": len(cs),
                "codes_only_here": len(cs - others), "test_cases_found": f"{sum(t in cs for t in TEST_CASES)}/{len(TEST_CASES)}",
                "share_of_all_codes": f"{len(cs) / len(all_kept):.0%}" if all_kept else ""})
coverage = pd.DataFrame(cov)
display(test_cases)
coverage
'''))

cells.append(markdown_cell("## 13. Write review files"))

cells.append(code_cell(r'''
forms = kept[kept["source"] != "PubMed"].groupby(["code_norm", "string_as_found", "suffix", "source", "record_id"]).agg(
    record_label=("record_label", "first"), record_level=("record_level", "first"), unii=("unii", "first"),
    unii_link=("unii_link", "first"), fields=("field", lambda x: ", ".join(sorted(set(x))))).reset_index()

pm_rows = []
for r in kept[kept["source"] == "PubMed"].itertuples():
    p = pubmed[r.record_id]
    pm_rows.append({"code_norm": r.code_norm, "pmid": r.record_id, "year": p["year"], "journal": p["journal"],
                    "title": p["title"], "found_in": r.field, "string_as_found": r.string_as_found,
                    "astra_hassle_affiliation": "; ".join(a for a in p["affiliations"] if ASTRA_RX.search(a)),
                    "note": r.note})
pm_table = pd.DataFrame(pm_rows).sort_values(["code_norm", "year", "pmid"]) if pm_rows else pd.DataFrame()

run = pd.DataFrame([
    {"item": "run_utc", "value": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")},
    {"item": "chembl_seed_regex", "value": CHEMBL_SEED_REGEX},
    {"item": "mesh_regex", "value": MESH_REGEX},
    {"item": "ncit_release", "value": f"{NCIT_VERSION} (flat file retrieved {ncit_retrieved})"},
    {"item": "pubmed_affiliation_query", "value": f"{PUBMED_AFFILIATION_QUERY} -> {len(disc_ids)} records"},
    {"item": "code_pattern", "value": CODE_RX.pattern},
    {"item": "nosep_pattern", "value": NOSEP_RX.pattern},
    {"item": "cache_dir", "value": CACHE_DIR},
])

xlsx = f"{OUT_DIR}/hassle_h_codes.xlsx"
with pd.ExcelWriter(xlsx, engine="openpyxl") as xw:
    for name, df in [("codes", codes), ("test_cases", test_cases), ("forms", forms), ("evidence", ev),
                     ("pubmed", pm_table), ("pubmed_searches", search_log), ("wikidata_items", wd_df),
                     ("set_aside", set_aside), ("coverage", coverage), ("run", run)]:
        df.to_excel(xw, sheet_name=name, index=False)
        ws = xw.sheets[name]
        ws.freeze_panes = "B2"
        for i, col in enumerate(df.columns, start=1):
            width = min(60, max(10, int(df[col].astype(str).str.len().quantile(0.9)) if len(df) else 10, len(str(col)) + 2))
            ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = width
codes.to_csv(f"{OUT_DIR}/hassle_h_codes.csv", index=False)
ev.to_csv(f"{OUT_DIR}/hassle_h_codes_evidence.csv", index=False)
print(f"Written: {xlsx}")
print(coverage.to_string(index=False))
'''))

notebook = {
    "cells": cells,
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                 "language_info": {"name": "python"}},
    "nbformat": 4,
    "nbformat_minor": 4,
}
with open(NOTEBOOK, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1, ensure_ascii=False)
print(f"Written {os.path.normpath(NOTEBOOK)} ({len(cells)} cells)")
