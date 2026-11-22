# =============================================================================
# AACT MATCHING RULE — one definition for code harvest and trial archaeology
# Source of truth: patterns/aact_matching.py (pasted into both notebooks by their builders)
# Rulings: see patterns/README.md. Worked cases are the asserts at the end.
# =============================================================================

import csv
import re

import pandas as pd

# Fields searched for codes (INN: interventions.name only)
CODE_FIELDS = [
    ("interventions.name",             "JOIN interventions f ON f.nct_id = s.nct_id",             "f.name"),
    ("intervention_other_names.name",  "JOIN intervention_other_names f ON f.nct_id = s.nct_id", "f.name"),
    ("studies.official_title",         "",                                                        "s.official_title"),
    ("studies.brief_title",            "",                                                        "s.brief_title"),
    ("id_information.id_value",        "JOIN id_information f ON f.nct_id = s.nct_id",            "f.id_value"),
]

# Code-scoped exclusions: (code key, exact matched value, lower-case) — token collisions the rule cannot see
EXCLUSIONS = {
    ("ONC201", "xm02-onc-201"),   # protocol ID of another sponsor (tbo-filgrastim, Teva), NCT02190721
}


# A separator inside the number ("H 234/09", "H 234-09", "BMS-562247-01", "NNC 0113-0217") is part of the code:
# removing it gives spellings that collide with other identifiers ("H-23409" is a Baylor IRB number, NCT00831480,
# not almokalant). Generalised from H codes after AACT check 2026-11-21: all trials of BMS-562247-01, BMS-936558-01
# and NNC 0113-0217 keep the separator in the record (KF 2026-11-21). Hyphen or slash only: a space inside the number
# can be digit grouping ("GSK 685 698" in a database for GSK685698)
INNER_SEPARATOR = re.compile(r"^\(?[a-z]{1,6}[-\s]?\d+[-/]\d+\)?$")


def match_key(code):
    """Case, spaces, hyphens, slashes and brackets removed: MK-3475, MK 3475, MK3475 -> MK3475."""
    return re.sub(r"[\s\-/()+.]", "", code).upper()


def code_variants(code):
    """Spellings searched for one code: as given, no separator, space<->hyphen, prefix/number split."""
    c = code.lower().strip()
    no_sep = re.sub(r"[-\s]", "", c)
    # Separator inside the number (INNER_SEPARATOR): no variant removes it
    keep_inner = bool(INNER_SEPARATOR.match(c))
    variants = {c} if keep_inner else {c, no_sep}
    if " " in c:
        variants.add(c.replace(" ", "-"))
    if "-" in c:
        variants.add(c.replace("-", " "))
    m = re.match(r"^([a-z]+)(\d.*)$", no_sep)
    if m and not keep_inner:
        variants.add(f"{m.group(1)}-{m.group(2)}")
        variants.add(f"{m.group(1)} {m.group(2)}")
    # Separator after the prefix dropped or swapped, number kept as given: "NNC 0113-0217" -> "nnc0113-0217"
    m = re.match(r"^([a-z]+)[-\s]?(\d.*)$", c)
    if m:
        for sep in ["", "-", " "]:
            variants.add(f"{m.group(1)}{sep}{m.group(2)}")
    return sorted(variants)


def _escape(s):
    return re.sub(r"([.^$*+?()\[\]{}|\\])", r"\\\1", s)


def token_regex(*codes):
    """Code(s) as a token: no letter or digit directly before or after. Same syntax in Python re and PostgreSQL ~*.
    Several spellings of one code (harvest candidates) give one regex with all their variants. When one of the
    spellings has a separator inside the number, only such spellings are searched: a source's own spelling without
    it ("H 37695" next to "H 376/95") is dropped (INNER_SEPARATOR)."""
    inner = [c for c in codes if INNER_SEPARATOR.match(c.lower().strip())]
    variants = sorted({v for c in (inner or codes) for v in code_variants(c)})
    return r"(^|[^a-z0-9])(" + "|".join(_escape(v) for v in variants) + r")($|[^a-z0-9])"


def pattern_code_regex(code):
    """Code inside a study-code pattern: optional space/hyphen between letter prefix and number (lou[- ]?064)."""
    k = match_key(code).lower()
    m = re.match(r"^([a-z]+)(\d.*)$", k)
    assert m, f"Pattern codes need a letter prefix and a number: {code}"
    return f"{m.group(1)}[- ]?{_escape(m.group(2))}"


def load_patterns(path):
    """Ruled rows of patterns/study_code_patterns.csv; rows with status 'proposed' are not used."""
    with open(path, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["status"].startswith("ruled")]
    for r in rows:
        assert "{code}" in r["regex"], f"{r['pattern_id']}: regex lacks {{code}}"
        assert r["field"] == "id_information.id_value", f"{r['pattern_id']}: only id_information is supported"
    return rows


def pattern_regexes(code, patterns):
    """(pattern_id, regex) for every ruled pattern that lists this code."""
    k = match_key(code)
    return [(p["pattern_id"], p["regex"].replace("{code}", pattern_code_regex(code)))
            for p in patterns if k in {match_key(c) for c in p["applies_to_codes"].split(";")}]


def is_excluded(code, matched_value):
    return (match_key(code), str(matched_value).strip().lower()) in EXCLUSIONS


def trials_for_code(run_query, code, patterns):
    """All matches for one code: token search in CODE_FIELDS plus ruled study-code patterns.
    Returns DataFrame nct_id, matched_field, matched_value, search_term, rule."""
    rx = token_regex(code)
    parts = [run_query(f"""SELECT DISTINCT s.nct_id, '{label}' AS matched_field, {col} AS matched_value,
                               %s AS search_term, 'token' AS rule
                           FROM studies s {join} WHERE {col} ~* %s""", (code, rx))
             for label, join, col in CODE_FIELDS]
    for pid, prx in pattern_regexes(code, patterns):
        parts.append(run_query("""SELECT DISTINCT f.nct_id, 'id_information.id_value' AS matched_field,
                                      f.id_value AS matched_value, %s AS search_term, %s AS rule
                                  FROM id_information f WHERE f.id_value ~* %s""", (code, pid, prx)))
    found = [p for p in parts if len(p)]
    df = pd.concat(found, ignore_index=True) if found else parts[0]
    return df[~df["matched_value"].map(lambda v: is_excluded(code, v))].reset_index(drop=True)


def trials_for_inn(run_query, inn):
    """INN as a substring of interventions.name (full INN; combinations are split upstream into components)."""
    return run_query("""SELECT DISTINCT s.nct_id, 'interventions.name' AS matched_field, f.name AS matched_value,
                            %s AS search_term, 'inn' AS rule
                        FROM studies s JOIN interventions f ON f.nct_id = s.nct_id
                        WHERE LOWER(f.name) LIKE %s""", (inn.lower(), f"%{inn.lower()}%"))


def residue(run_query, code, patterns):
    """id_information values containing the code key (separators ignored) that neither the token rule nor a
    ruled pattern matches — for human review, never fed back automatically."""
    k = match_key(code).lower()
    rxs = [token_regex(code)] + [r for _, r in pattern_regexes(code, patterns)]
    df = run_query("""SELECT DISTINCT nct_id, id_value FROM id_information
                      WHERE regexp_replace(LOWER(id_value), '[^a-z0-9]', '', 'g') LIKE %s""", (f"%{k}%",))
    keep = ~df["id_value"].map(lambda v: any(re.search(r, v, re.I) for r in rxs) or is_excluded(code, v))
    return df[keep].reset_index(drop=True)


# -----------------------------------------------------------------------------
# Worked cases (AACT, 2026-10-15). A new review finding becomes a new line here.
# -----------------------------------------------------------------------------
def _tok(code, value):
    return bool(re.search(token_regex(code), value, re.I)) and not is_excluded(code, value)


_P = [{"pattern_id": "P1", "applies_to_codes": "LOU064; AIN457", "regex": "(^|[^a-z0-9])c{code}[a-z]",
       "field": "id_information.id_value", "status": "ruled"},
      {"pattern_id": "P2", "applies_to_codes": "CNTO1959", "regex": "(^|[^a-z0-9]){code}[a-z]{3,5}[0-9]{4}",
       "field": "id_information.id_value", "status": "ruled"}]


def _pat(code, value):
    return any(re.search(r, value, re.I) for _, r in pattern_regexes(code, _P))


# Format variants
assert _tok("BI 1015550", "BI1015550") and _tok("BI 1015550", "BI 1015550 (Nerandomilast)")
assert _tok("BMS 562247-01", "BMS-562247-01") and _tok("LY3298176", "LY-3298176")
assert _tok("NNC 0113-0217", "NNC0113-0217") and _tok("NNC 0113-0217", "NNC 0113-0217")   # titles NCT02016911, NCT02070510
# Separator inside the number is kept (Baylor IRB number H-23409, NCT00831480)
assert not _tok("H 234-09", "H-23409") and not _tok("H 234-09", "H23409") and not _tok("H 234/09", "H 23409")
assert _tok("H 234-09", "H234-09") and _tok("H 234-09", "H-234-09") and _tok("H 234/09", "H234/09")
assert not _tok("BMS-562247-01", "BMS56224701") and _tok("BMS 562247-01", "BMS-562247-01")
# ... also when a source gives the spelling without it next to one with it
assert not re.search(token_regex("H 376/95", "H 37695"), "H-37695", re.I)
assert re.search(token_regex("H 376/95", "H 37695"), "H376/95", re.I)
assert re.search(token_regex("H 37695"), "H-37695", re.I)   # no spelling with the separator: unchanged
assert re.search(token_regex("GSK 685 698", "GSK 685698"), "GSK685698", re.I)   # a space is not an inner separator
# Short codes inside other tokens
assert not _tok("SS-31", "COMPASS-31") and not _tok("SS-31", "COMPASS31") and not _tok("SS-31", "CAPSS-314")
assert not _tok("WS-12", "AEWS1221") and _tok("SS-31", "SS-31")
assert not _tok("SB27", "compass27")
assert not _tok("TIC10", "HTIC-10-22") and not _tok("TIC10", "STIC/10/03")
assert not _tok("AB-106", "Sobi.EMAPALUMAB-106") and not _tok("AB-106", "CLI-05993AB1-06")
assert _tok("AB-106", "AB-106-C110")
# Digit after the code: a different number
assert not _tok("ONC201", "ONC-2010-001") and not _tok("ONC201", "R1979-ONC-20103")
assert not _tok("GSK572", "GSK572016")
# Code-scoped exclusion
assert not _tok("ONC201", "XM02-ONC-201") and _tok("ONC201", "ONC201-108")
# Letter after the code: another product or form (MK-3475A = s.c. co-formulation, review: other_product)
assert not _tok("MK-3475", "MK-3475A") and not _tok("MK-3475", "MK-3475A-C18")
assert not _tok("ONO-4538", "ONO-4538HSC")   # s.c. nivolumab + hyaluronidase (= BMS-986298, review: other_product)
assert not _tok("GSK1349572", "GSK1349572A")
# Separator then study number: the moiety's own study codes, also on partners' records
assert _tok("MK-3475", "MK-3475-001") and _tok("MK-3475", "KEYNOTE-C98, MK-3475-C98") and _tok("MK-3475", "MK-3475-A17")
assert _tok("NN9535", "NN9535-1820") and _tok("ONO-4538", "ONO-4538-24/CA209-473")
# Study-code patterns (P1, P2)
assert not _tok("LOU064", "CLOU064A1301") and _pat("LOU064", "CLOU064A1301") and _pat("LOU064", "CLOU064C12301")
assert _pat("AIN457", "CAIN457F2302/E1") and not _pat("AIN457", "MAIN457A_FVMBO009")   # residue, not a pattern
assert not _tok("CNTO1959", "CNTO1959PAP4001") and _pat("CNTO1959", "CNTO1959PAP4001")
assert not _pat("MK-3475", "MK-3475A-C18")   # no pattern row for MK-3475
