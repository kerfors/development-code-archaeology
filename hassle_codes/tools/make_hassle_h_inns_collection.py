"""Draft collection hassle_h_inns.csv: Hässle substances with an INN (one row per INN, brand left empty — row unit
not yet decided). INN, UNII and H code from hassle_h_codes.csv (harvest 2026-11-21) plus timoprazole (GSRS INN 3985).
UNII = the INN's own GSRS record (not GSRS ACTIVE MOIETY: omeprazole/esomeprazole would give the sulfenamide,
ximelagatran melagatran). NCIt concept = the concept whose FDA_UNII_Code equals that UNII (NCI EVS search)."""
import json, sys, requests, time, csv
EVS = "https://api-evsrest.nci.nih.gov/api/v1"
GSRS = "https://gsrs.ncats.nih.gov/api/v1"
rows = [  # inn, own UNII, H codes (as in the harvest)
    ("alprenolol", "877K5MQ27W", "H 56/28"), ("prenalterol", "M4G34404CX", "H 80/62; H 133/22"),
    ("metoprolol", "GEB06NHM23", "H 93/26"), ("zimeldine", "3J928617DW", "H 102/09"),
    ("pamatolol", "20G2S6V53L", "H 104/08"), ("tazolol", "B64Q38TX4G", "H 110/38"),
    ("nebidrazine", "SYD5G2AE8M", "H 113/75"), ("picoprazole", "S882YC38OJ", "H 149/94"),
    ("felodipine", "OL961R6O2C", "H 154/82"), ("omeprazole", "KG60484QX9", "H 168/68"),
    ("esomeprazole", "N3PA6559FT", "H 199/18"), ("almokalant", "I9NG89L275", "H 234/09"),
    ("inogatran", "428409I84L", "H 314/27"), ("clevidipine", "19O2GP3B7Q", "H 324/38"),
    ("ximelagatran", "49HFB70472", "H 376/95"), ("melagatran", "2A9QP32MD4", "H 319/68"),
    ("timoprazole", "95H6S1X9CC", "H 83/69"),
]
out = []
for inn, unii, hcodes in rows:
    g = requests.get(f"{GSRS}/substances({unii})", params={"view": "full"}, timeout=180).json()
    inn_names = [n["name"] for n in g["names"] if any(o.get("nameOrg") == "INN" for o in n.get("nameOrgs") or [])]
    inn_no = [c["code"] for c in g.get("codes", []) if c["codeSystem"] == "INN"]
    ncits = [c["code"] for c in g.get("codes", []) if c["codeSystem"] == "NCI_THESAURUS"]
    hit = []
    for c in ncits:
        r = requests.get(f"{EVS}/concept/ncit/{c}", params={"include": "properties"}, timeout=60).json()
        if any(p["type"] == "FDA_UNII_Code" and p["value"] == unii for p in r.get("properties", [])):
            hit.append((c, r["name"]))
        time.sleep(0.2)
    assert len(hit) == 1, f"{inn}: NCIt concepts with FDA_UNII_Code {unii}: {hit} (GSRS xrefs {ncits})"
    out.append({"brand": "", "inn": inn, "ncit_code": hit[0][0], "moiety_unii": unii, "sponsor": "Hässle",
                "h_codes": hcodes, "inn_number": ";".join(inn_no), "gsrs_inn_name": ";".join(inn_names),
                "ncit_name": hit[0][1]})
    print(inn, unii, hit[0], inn_no, inn_names)
with open("hassle_h_inns.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]))
    w.writeheader(); w.writerows(out)
