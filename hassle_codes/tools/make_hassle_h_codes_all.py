"""The full list of H codes found so far, one row per code, next to the INN collection (task 5, 2026-11-22).

Run from the repo root:  python hassle_codes/tools/make_hassle_h_codes_all.py
Writes two files. No network: it only joins files already in the repo.
- collections/hassle_h_codes_all.csv       the large historical list: every code found, patents included (137 at first run)
- collections/hassle_h_codes_wikidata.csv  the small list for Wikidata (P15001 statements, aliases); no trial counts.
  Only codes of the INN collection (Kerstin, 2026-11-22). All non-patent references on hand are listed per code.
  Reference types for the Wikidata batch (Kerstin, 2026-11-22): ref_hassle_source wherever conferred_by is set (it
  supports the qualifier); ref_earliest_pmid on every row that has one; ref_mesh_ids / ref_ncit_codes only where no
  PubMed record names the code; ref_chembl_ids / ref_gsrs_uniis are context, not references (the code often sits on
  a salt record, not on the moiety). conferred_by is filled only when hassle_status is
  established; otherwise the statement goes without the P1027 qualifier (Kerstin, 2026-11-22). ready = yes only
  when the review row has a reviewer other than 'claude-proposed'.
  ref_* columns hold only records that name the code (harvest evidence, status 'kept'); linked_* columns hold
  what the harvest linked through the UNII (parents, moieties, classes) and are context, not references
  (Kerstin, 2026-11-22). wikidata_qid_by_unii comes from a Wikidata lookup of the INN's UNII (P652).

Inputs (every value in the output comes from one of these; the column names say which). The hassle_codes/inputs/
files are frozen copies of files first written under hassle_codes/output/ (gitignored), copied 2026-11-22 so the
lists can be rebuilt from the repo alone (Kerstin, 2026-11-22). A rerun of the harvest writes to output/, not here.
- hassle_codes/inputs/hassle_h_codes.csv                         harvest 2026-11-21 (53 codes)
- hassle_codes/inputs/hassle_h_codes_evidence.csv                harvest evidence, one row per record (PubMed affiliations)
- hassle_codes/inputs/hassle_findings_2026-11-21.csv             patents/literature, session 2
- hassle_codes/inputs/hassle_findings_2026-11-21b.csv            patent PDFs, session 3 (research note 3d)
- hassle_codes/inputs/hassle_findings_2026-11-22.csv             PubMed records the harvest missed (H 319/68)
- hassle_codes/inputs/hassle_findings_2026-11-26.csv             patent tables vs PDFs (corrections), US 3594478, EPO OPS
                                                                 family checks; five new codes from BE 781105 (2026-11-26).
                                                                 Rows without a code (about a document) are skipped here.
- collections/hassle_h_inns.csv                                  INN collection (h_codes column)
- collections/hassle_h_inns_code_review.csv                      review draft (code_class, rationale)
- hassle_codes/inputs/wikidata_unii_lookup_2026-11-22.csv        Wikidata items by UNII (P652), query in file
- LITERATURE below: Hässle programme histories cited in claude/hassle-h-codes-research.md section 2

Patents are recorded but never count (Kerstin, 2026-11-22: patents are a new domain; stick to the other sources).
Patent findings go to the patent_* columns and may give earliest_date (earliest_date_from says which); they never
set hassle_status. nonpatent_date is the earliest date from the other sources.

hassle_status: established | established_not_rechecked | not_established | patent_only | not_hassle.
- established: a PubMed record naming the code has a Hässle affiliation, or Astra/AstraZeneca at Mölndal.
- established_not_rechecked: the only establishing basis is a published history (LITERATURE) whose passage
  linking code and company has not been re-checked: Olbe 2003 Fig. 1 is paywalled, the PubMed abstract names no
  code (Kerstin, 2026-11-22). Shown as "established (published history, not re-checked)". conferred_by stays
  empty, in line with Wikidata decision D14.
- patent_only: the code is known only from patents (no harvest record, no non-patent finding, no literature).
hassle_basis (counting, all that apply, '; '):
- hassle_affiliated_pmid      a PubMed record naming the code has a Hässle affiliation (harvest)
- astra_molndal_pmid          a PubMed record naming the code has an Astra/AstraZeneca affiliation at Mölndal: the same
                              site and numbering after the name changes (Kerstin, 2026-11-22). Astra elsewhere
                              (Södertälje, Lund) does not count. From the harvest evidence, or from a non-patent
                              findings row whose basis says 'affiliation at Mölndal'.
- literature_hassle_programme code named in a published history of a Hässle programme (LITERATURE)
patent_basis (not counting): code_in_hassle_patent | structure_in_hassle_patent.
Patent numbers are recognised for US, BE, FR, NL, GB, DE, SE, EP and WO (2026-11-26; before: US only).
A patent counts as an AB Hässle patent when any findings row citing that patent number names Hässle as assignee.
The review is not a basis: it is built from this evidence, so it would be circular. Its class is shown.
(astrazeneca_source_only, read from the review rationale, removed 2026-11-22 for the same reason.)

Dates are latest-possible dates (publication, or patent filing/priority), never synthesis dates.
"""
import csv
import re
from pathlib import Path

HARVEST = Path("hassle_codes/inputs/hassle_h_codes.csv")
EVIDENCE = Path("hassle_codes/inputs/hassle_h_codes_evidence.csv")
FINDINGS = [Path("hassle_codes/inputs/hassle_findings_2026-11-21.csv"),
            Path("hassle_codes/inputs/hassle_findings_2026-11-21b.csv"),
            Path("hassle_codes/inputs/hassle_findings_2026-11-22.csv"),
            Path("hassle_codes/inputs/hassle_findings_2026-11-26.csv")]
INNS = Path("collections/hassle_h_inns.csv")
WD_LOOKUP = Path("hassle_codes/inputs/wikidata_unii_lookup_2026-11-22.csv")
REVIEW = Path("collections/hassle_h_inns_code_review.csv")
OUT = Path("collections/hassle_h_codes_all.csv")
OUT_WD = Path("collections/hassle_h_codes_wikidata.csv")

# Published histories of the Hässle omeprazole programme, as cited in claude/hassle-h-codes-research.md section 2.
LITERATURE = {
    "H 124/26": "Olbe L, Carlsson E, Lindberg P (2003) Nat Rev Drug Discov 2:132-139, doi:10.1038/nrd1010, PMID 12563304, Fig. 1 (first benzimidazole lead, 1973)",
    "H 83/69": "Olbe L, Carlsson E, Lindberg P (2003) Nat Rev Drug Discov 2:132-139, doi:10.1038/nrd1010, PMID 12563304, Fig. 1 (timoprazole, 1974)",
    "H 149/94": "Olbe L, Carlsson E, Lindberg P (2003) Nat Rev Drug Discov 2:132-139, doi:10.1038/nrd1010, PMID 12563304, Fig. 1 (picoprazole, 1976)",
    "H 168/68": "Olbe L, Carlsson E, Lindberg P (2003) Nat Rev Drug Discov 2:132-139, doi:10.1038/nrd1010, PMID 12563304, Fig. 1 (omeprazole, 1979)",
    "H 81/75": "Sjöstrand SE, Olbe L, Fellenius E (1999) in Olbe (ed.) Proton Pump Inhibitors, pp 3-22, "
               "doi:10.1007/978-3-0348-8795-3_1 (carbamate, in human volunteers 1971-72)",
}
ESTABLISHING = {"hassle_affiliated_pmid", "astra_molndal_pmid", "literature_hassle_programme"}
RECHECKED = {"hassle_affiliated_pmid", "astra_molndal_pmid"}  # basis a reader can check in the record itself
AFFILIATION = re.compile(r"Astra/Hässle affiliation: (.*)")
PATENT = re.compile(r"\b(?:US|BE|FR|NL|GB|DE|SE|EP|WO)\s?\d{6,9}")
DATE = re.compile(r"^(\d{4})(-\d{2}-\d{2})?")


def key(code):
    """'H 168/68' -> 'H16868' (the code_key used by the harvest notebook)."""
    return code.replace(" ", "").replace("/", "")


def parse_date(s):
    m = DATE.match((s or "").strip())
    return (m.group(1) + (m.group(2) or "")) if m else None


def earlier(a, b):
    """a, b: (date, kind, source). Earlier year wins; same year, a full date wins over a year."""
    if b is None:
        return a
    if a is None:
        return b
    if a[0][:4] != b[0][:4]:
        return a if a[0][:4] < b[0][:4] else b
    if len(a[0]) == len(b[0]) == 10 and a[0] != b[0]:
        return a if a[0] < b[0] else b  # same year, both full dates: the earlier date wins (2026-11-26)
    return a if len(a[0]) >= len(b[0]) else b


def add(d, k, v):
    if v and v not in d.setdefault(k, []):
        d[k].append(v)


codes = {}  # code -> dict of lists


def row(code):
    return codes.setdefault(code, {"_date": None})


# Findings: patents and literature
findings = []
for f in FINDINGS:
    for r in csv.DictReader(open(f, encoding="utf-8")):
        r["_file"] = f.name
        findings.append(r)
hassle_patents = {p.replace(" ", "") for r in findings if "Hässle" in r["source"]
                  for p in PATENT.findall(r["source"])}

for r in findings:
    c, ft, basis = r["code"], r["finding_type"], r["basis"]
    if not c:
        continue  # a row about a document or a pattern, not about one code (kept in the findings file only)
    x = row(c)
    src = f"{r['source']} [{r['_file']}]"
    add(x, "finding_types", ft)
    add(x, "flags", f"{r['flag']} [{r['_file']}]" if r["flag"] else "")
    if ft.startswith("candidate settled: not Hässle"):
        add(x, "not_hassle", src)
    is_patent = bool(PATENT.search(r["source"]))
    patents = {p.replace(" ", "") for p in PATENT.findall(r["source"])} & hassle_patents
    if patents and not ft.startswith("candidate"):
        if basis.startswith("code in patent"):
            add(x, "patent_basis", "code_in_hassle_patent"); add(x, "patent_source", src)
        elif "structure" in basis:
            add(x, "patent_basis", "structure_in_hassle_patent"); add(x, "patent_source", src)
    if not is_patent:
        x["_nonpatent"] = True
        if "affiliation at Mölndal" in basis:
            add(x, "basis", "astra_molndal_pmid")
            add(x, "hassle_source", f"{r['source']} (Astra/AstraZeneca, Mölndal) [{r['_file']}]")
    if not ft.startswith("candidate settled") and ft not in ("date", "observation"):
        add(x, "identity", r["value"]); add(x, "identity_source", src)
    d = parse_date(r["date"])
    if d:
        key_ = "_patent_date" if is_patent else "_date"
        x[key_] = earlier((d, r["date_kind"], src), x.get(key_))

# Harvest
for r in csv.DictReader(open(HARVEST, encoding="utf-8")):
    x = row(r["code_norm"])
    x["_nonpatent"] = True
    x["_harvest"] = r
    add(x, "harvest_sources", r["sources"])
    add(x, "harvest_substance", r["substance_names"])
    add(x, "mesh_ids", r["mesh_ids"])
    add(x, "gsrs_carrier_uniis", r["carrier_uniis"])
    add(x, "flags", f"{r['flags']} [hassle_h_codes.csv]" if r["flags"] else "")
    if r["hassle_affiliated_pmids"]:
        add(x, "basis", "hassle_affiliated_pmid")
        add(x, "hassle_source", f"PMID {r['hassle_affiliated_pmids']} [hassle_h_codes.csv]")
    if r["earliest_pubmed_year"]:
        y = r["earliest_pubmed_year"].split(".")[0]
        x["_date"] = earlier((y, "latest-possible (publication)", f"PMID {r['earliest_pmid']} [hassle_h_codes.csv]"),
                             x["_date"])

# Astra/AstraZeneca at Mölndal (harvest evidence, per PubMed record), where no Hässle affiliation is recorded;
# records that name the code, per source, for the ref_* columns of the Wikidata list
molndal = {}
naming = {}  # (code, source) -> set of record ids
for r in csv.DictReader(open(EVIDENCE, encoding="utf-8")):
    if r["status"] == "kept":
        naming.setdefault((r["code_norm"], r["source"]), set()).add(r["record_id"])
    m = AFFILIATION.search(r["note"])
    if r["source"] == "PubMed" and m and "Mölndal" in m.group(1) and "Astra" in m.group(1):
        molndal.setdefault(r["code_norm"], set()).add(r["record_id"])
for c, pmids in molndal.items():
    x = row(c)
    if "hassle_affiliated_pmid" in x.get("basis", []):
        continue
    add(x, "basis", "astra_molndal_pmid")
    add(x, "hassle_source", f"PMID {', '.join(sorted(pmids))} (Astra/AstraZeneca, Mölndal) [hassle_h_codes_evidence.csv]")

# Literature
for c, ref in LITERATURE.items():
    x = row(c)
    x["_nonpatent"] = True
    add(x, "basis", "literature_hassle_programme")
    add(x, "hassle_source", f"{ref} [research notes section 2]")

# INN collection and review draft
inn_of = {}
unii_of = {}
for r in csv.DictReader(open(INNS, encoding="utf-8")):
    for c in r["h_codes"].split("; "):
        inn_of[c] = r["inn"]
        unii_of[c] = r["moiety_unii"]
        row(c)
wd_by_unii = {}
for r in csv.DictReader(open(WD_LOOKUP, encoding="utf-8")):
    wd_by_unii.setdefault(r["unii"], []).append(f"{r['qid']} ({r['label_en']}; P2275 {r['has_p2275']}; {r['sitelinks']} sitelinks)")
review = {(r["inn"], r["code_key"]): r for r in csv.DictReader(open(REVIEW, encoding="utf-8"))}
for c, inn in inn_of.items():
    rv = review.get((inn, key(c)))
    x = codes[c]
    if rv is None:
        add(x, "flags", "no row in hassle_h_inns_code_review.csv (no candidate in the v2 harvest)")
        continue
    x["review_class"] = rv["code_class"]
    x["review_reviewer"] = rv["reviewer"]
    if rv["verification"]:
        add(x, "flags", f"{rv['verification']} [hassle_h_inns_code_review.csv]")

# Write
out = []
for c, x in codes.items():
    m = re.fullmatch(r"H (\d+)/(\d+)", c)
    assert m, f"code not in 'H n/nn' form: {c!r}"
    basis = x.get("basis", [])
    if x.get("not_hassle"):
        assert not set(basis) & ESTABLISHING, f"{c}: settled not Hässle but has {basis}"
        status = "not_hassle"
    elif set(basis) & ESTABLISHING:
        status = "established" if set(basis) & RECHECKED else "established_not_rechecked"
    elif not x.get("_nonpatent"):
        status = "patent_only"
    else:
        status = "not_established"
    d = x["_date"] or ("", "", "")
    pd_ = x.get("_patent_date") or ("", "", "")
    e = earlier(x["_date"], x.get("_patent_date")) or ("", "", "")
    e_from = "" if not e[0] else ("patent" if x.get("_patent_date") is e else "non-patent")
    j = "; ".join
    out.append({
        "code": c, "first_number": int(m.group(1)), "second_number": m.group(2),
        "inn": inn_of.get(c, ""), "in_inn_collection": "yes" if c in inn_of else "no",
        "hassle_status": status, "hassle_basis": j(basis),
        "hassle_source": j(x.get("hassle_source", []) + x.get("not_hassle", [])),
        "earliest_date": e[0], "earliest_date_from": e_from, "earliest_date_kind": e[1], "earliest_date_source": e[2],
        "nonpatent_date": d[0], "nonpatent_date_kind": d[1], "nonpatent_date_source": d[2],
        "patent_basis": j(x.get("patent_basis", [])), "patent_source": j(x.get("patent_source", [])),
        "patent_date": pd_[0], "patent_date_kind": pd_[1], "patent_date_source": pd_[2],
        "identity": " || ".join(x.get("identity", [])), "identity_source": " || ".join(x.get("identity_source", [])),
        "harvest_substance": j(x.get("harvest_substance", [])), "harvest_sources": j(x.get("harvest_sources", [])),
        "mesh_ids": j(x.get("mesh_ids", [])), "gsrs_carrier_uniis": j(x.get("gsrs_carrier_uniis", [])),
        "review_class": x.get("review_class", ""), "review_reviewer": x.get("review_reviewer", ""),
        "finding_types": j(x.get("finding_types", [])), "flags": " || ".join(x.get("flags", [])),
    })
out.sort(key=lambda r: (r["first_number"], r["second_number"]))
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)

from collections import Counter
print(f"{OUT}: {len(out)} codes")
print("hassle_status:", dict(Counter(r["hassle_status"] for r in out)))
print("with INN:", sum(r["inn"] != "" for r in out))
print("no date at all:", [r["code"] for r in out if not r["earliest_date"]])
print("earliest date from a patent:", sum(r["earliest_date_from"] == "patent" for r in out))

# Small list for Wikidata: codes of the INN collection only
wd = []
for r in out:
    if not r["inn"]:
        continue
    h = codes[r["code"]].get("_harvest") or {}
    c = r["code"]
    ref = lambda src: "; ".join(sorted(naming.get((c, src), set())))
    assert unii_of[c] in wd_by_unii, f"{c}: UNII {unii_of[c]} not in {WD_LOOKUP}"
    # earliest PubMed record naming the code: PMID and year from the same record
    pmid = h.get("earliest_pmid", "")
    pmid_year = h.get("earliest_pubmed_year", "").split(".")[0] if pmid else ""
    if not pmid:
        m_ = re.match(r"PMID (\d+)", r["nonpatent_date_source"])
        if m_:
            pmid, pmid_year = m_.group(1), r["nonpatent_date"]
    wd.append({
        "inn": r["inn"], "code": r["code"], "level": h.get("level", ""),
        "wikidata_qid_by_unii": " | ".join(wd_by_unii[unii_of[c]]),
        "wikidata_qid_carrier": h.get("wikidata_qid_carrier", ""), "wikidata_qid_moiety": h.get("wikidata_qid_moiety", ""),
        "gsrs_carrier_uniis": h.get("carrier_uniis", ""), "salt_forms": h.get("salt_forms", ""),
        "already_on_wikidata": h.get("wikidata_code_as_alias_or_label", ""), "wikidata_p15001": h.get("wikidata_p15001", ""),
        "hassle_status": r["hassle_status"], "conferred_by": "AB Hässle" if r["hassle_status"] == "established" else "",
        "ref_hassle_source": r["hassle_source"],
        "ref_earliest_pmid": pmid, "ref_earliest_year": pmid_year,
        "ref_earliest_title": h.get("earliest_title", ""), "ref_hassle_affiliated_pmids": h.get("hassle_affiliated_pmids", ""),
        "ref_mesh_ids": ref("MeSH"), "ref_ncit_codes": ref("NCIt"), "ref_chembl_ids": ref("ChEMBL"),
        "ref_gsrs_uniis": ref("GSRS"),
        "linked_mesh_ids": h.get("mesh_ids", ""), "linked_ncit_codes": h.get("ncit_codes", ""),
        "linked_chembl_ids": h.get("chembl_ids", ""), "linked_gsrs_uniis": h.get("uniis_linked", ""),
        "harvest_sources": h.get("sources", ""),
        "review_class": r["review_class"], "review_reviewer": r["review_reviewer"],
        "ready": "yes" if r["review_reviewer"] not in ("", "claude-proposed") else "no",
        "flags": r["flags"],
    })
with open(OUT_WD, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(wd[0]))
    w.writeheader()
    w.writerows(wd)
print(f"{OUT_WD}: {len(wd)} codes, ready: {sum(r['ready'] == 'yes' for r in wd)}")
