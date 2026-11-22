"""Wikidata batch (P15001 development code) for the Hässle INN codes.

Reads collections/hassle_h_codes_wikidata.csv (the small list, rows with ready = yes) and the cached PubMed
records under hassle_codes/output/cache*/. Writes a review table and QuickStatements V1 commands to
wikidata/output/. No network: a referenced PubMed record missing from the cache stops the run. Nothing is sent.

Rules (Kerstin, 2026-11-22):
- All ready rows are published (17). Value = the list spelling "H nnn/nn".
- Target item: the item found by UNII; where several items carry the UNII, the one with P2275, else the one with
  most sitelinks (felodipine: Q420644; Q72478142 logged).
- A PubMed record is used as a reference only if its title or abstract contains the code (any spacing, "/" or "-").
  Excluded by decision: PMID 29999713 (LactMed book chapter; code only in an aggregated synonym list).
- P1027 conferred by Hässle AB (Q105106991) only where a used PubMed record names the company line in its
  affiliation (Hässle, or Astra/AstraZeneca at Mölndal). Olbe 2003 (PMID 12563304) names no code in its abstract
  (codes in Fig. 1, not read): not used, so H 83/69, H 149/94, H 168/68 go without P1027 (decision D14).
- References, at most two per statement: the earliest company-line record (supports P1027) and the earliest record
  naming the code, if different. Without a usable PubMed record: MeSH (P486), else NCIt (P1748).
- Rank normal. No alias edits.
"""
import glob
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import pandas as pd

LIST = "collections/hassle_h_codes_wikidata.csv"
CACHE_GLOB = "hassle_codes/output/cache*/*.json"
OUT_DIR = "wikidata/output"
COLLECTION = "hassle_h_inns"

PUBMED = "Q180686"
MESH = "Q199897"
NCIT = "Q19404626"
HASSLE = "Q105106991"  # Hässle AB; sv.wikipedia "Hässle AB" (KF 2026-11-22)

EXCLUDED_PMIDS = {
    "29999713": "LactMed book chapter (NBK500654): code only in an aggregated synonym list (KF 2026-11-22)",
}
EXPECTED_READY = 17

run = datetime.now(timezone.utc)
RETRIEVED = run.strftime("+%Y-%m-%dT00:00:00Z/11")
STAMP = run.strftime("%Y%m%d_%H%M")


def load_pubmed_cache():
    recs = {}
    for path in glob.glob(CACHE_GLOB):
        try:
            with open(path, encoding="utf-8") as fh:
                j = json.load(fh)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        body = j.get("body") if isinstance(j, dict) else None
        if not isinstance(body, str) or "efetch" not in j.get("url", ""):
            continue
        if "<PubmedArticle" not in body and "<PubmedBookArticle" not in body:
            continue
        root = ET.fromstring(body)
        for a in root.iter("PubmedArticle"):
            pmid = a.findtext(".//MedlineCitation/PMID")
            title_el = a.find(".//ArticleTitle")
            recs[pmid] = {
                "kind": "article",
                "title": "".join(title_el.itertext()) if title_el is not None else "",
                "abstract": " ".join("".join(x.itertext()) for x in a.iter("AbstractText")),
                "affiliation": " | ".join(sorted(set(x.text or "" for x in a.iter("Affiliation")))),
                "year": a.findtext(".//PubDate/Year") or (a.findtext(".//PubDate/MedlineDate") or "")[:4],
            }
        for a in root.iter("PubmedBookArticle"):
            pmid = a.findtext(".//PMID")
            recs[pmid] = {"kind": "book", "title": "", "abstract": " ".join(a.itertext()), "affiliation": "",
                          "year": ""}
    return recs


def code_pattern(code):
    m = re.fullmatch(r"H (\d+)/(\d+)", code)
    assert m, f"unexpected code spelling: {code}"
    return re.compile(r"H\s?-?\s?" + m.group(1) + r"\s?[/-]\s?" + m.group(2) + r"(?!\d)")


def company_line(affiliation):
    a = affiliation.lower()
    return "hässle" in a or "hassle" in a or ("mölndal" in a and "astra" in a)


def pick_item(text):
    entries = []
    for part in text.split(" | "):
        m = re.match(r"(Q\d+) \((.*?); P2275 (yes|no); (\d+) sitelinks\)", part.strip())
        assert m, f"cannot parse wikidata_qid_by_unii entry: {part}"
        entries.append({"qid": m.group(1), "label": m.group(2), "p2275": m.group(3) == "yes",
                        "sitelinks": int(m.group(4))})
    with_inn = [e for e in entries if e["p2275"]]
    pool = with_inn if with_inn else entries
    best = max(pool, key=lambda e: e["sitelinks"])
    assert sum(e["sitelinks"] == best["sitelinks"] for e in pool) == 1, f"no unique item: {text}"
    others = [e["qid"] for e in entries if e["qid"] != best["qid"]]
    return best, others


def pmids(text):
    return re.findall(r"(?<![\d.])(\d{5,8})(?!\d)", text)


recs = load_pubmed_cache()
wl = pd.read_csv(LIST, dtype=str).fillna("")
wl = wl[wl["ready"] == "yes"]
assert len(wl) == EXPECTED_READY, f"expected {EXPECTED_READY} ready rows, found {len(wl)}"

review, commands = [], []
for _, r in wl.iterrows():
    code = r["code"]
    pat = code_pattern(code)
    item, other_items = pick_item(r["wikidata_qid_by_unii"])

    checked = {}
    for p in dict.fromkeys(pmids(r["ref_hassle_source"]) + pmids(r["ref_hassle_affiliated_pmids"])
                           + pmids(r["ref_earliest_pmid"])):
        assert p in recs, f"{code}: PubMed {p} not in cache"
        rec = recs[p]
        m = pat.search(rec["title"] + " " + rec["abstract"])
        checked[p] = {
            "found": m.group(0) if m else "",
            "excluded": EXCLUDED_PMIDS.get(p, ""),
            "company": company_line(rec["affiliation"]),
            "year": rec["year"],
            "affiliation": rec["affiliation"],
        }
    usable = {p: c for p, c in checked.items() if c["found"] and not c["excluded"]}
    by_age = sorted(usable, key=lambda p: (usable[p]["year"] or "9999", int(p)))
    company_refs = [p for p in by_age if usable[p]["company"]]

    refs = []
    if company_refs:
        refs.append(company_refs[0])
    if by_age and by_age[0] not in refs:
        refs.append(by_age[0])
    conferred = HASSLE if company_refs else ""
    assert not conferred or r["conferred_by"] == "AB Hässle", f"{code}: company line found but not established"

    ref_rows = [("PubMed", p, usable[p]["found"], usable[p]["affiliation"][:120]) for p in refs]
    if not ref_rows:
        mesh = [x for x in r["ref_mesh_ids"].split(" | ") if x]
        ncit = [x for x in r["ref_ncit_codes"].split(" | ") if x]
        if mesh:
            assert len(mesh) == 1, f"{code}: several MeSH ids {mesh}"
            ref_rows = [("MeSH", mesh[0], "", "")]
        elif ncit:
            assert len(ncit) == 1, f"{code}: several NCIt codes {ncit}"
            ref_rows = [("NCIt", ncit[0], "", "")]
    assert ref_rows, f"{code}: no usable reference"

    head = f'{item["qid"]}|P15001|"{code}"' + (f"|P1027|{conferred}" if conferred else "")
    for kind, ident, _, _ in ref_rows:
        if kind == "PubMed":
            src = f'S248|{PUBMED}|S698|"{ident}"'
        elif kind == "MeSH":
            src = f'S248|{MESH}|S486|"{ident}"'
        else:
            src = f'S248|{NCIT}|S1748|"{ident}"'
        commands.append(f"{head}|{src}|S813|{RETRIEVED}")

    not_used = "; ".join(f"{p}: " + ("excluded — " + c["excluded"] if c["excluded"] else "code not in title/abstract")
                         for p, c in checked.items() if p not in usable)
    review.append({
        "code": code, "inn": r["inn"], "hassle_status": r["hassle_status"],
        "target_qid": item["qid"], "target_label": item["label"], "other_items_same_unii": " | ".join(other_items),
        "conferred_by_qid": conferred, "value": code,
        "ref1": f"{ref_rows[0][0]} {ref_rows[0][1]}", "ref1_code_as_printed": ref_rows[0][2],
        "ref1_affiliation": ref_rows[0][3],
        "ref2": f"{ref_rows[1][0]} {ref_rows[1][1]}" if len(ref_rows) > 1 else "",
        "ref2_code_as_printed": ref_rows[1][2] if len(ref_rows) > 1 else "",
        "pubmed_not_used": not_used,
    })

rv = pd.DataFrame(review)
csv_path = f"{OUT_DIR}/{COLLECTION}_batch_{STAMP}.csv"
qs_path = f"{OUT_DIR}/{COLLECTION}_batch_{STAMP}.qs"
rv.to_csv(csv_path, index=False)
with open(qs_path, "w", encoding="utf-8") as fh:
    fh.write("\n".join(commands) + "\n")

print(f"{csv_path}: {len(rv)} statements, {(rv['conferred_by_qid'] != '').sum()} with P1027")
print(f"{qs_path}: {len(commands)} command lines")
print(rv["ref1"].str.split().str[0].value_counts().to_string())
