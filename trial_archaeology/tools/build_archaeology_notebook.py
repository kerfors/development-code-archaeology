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
# Development Code Trial Archaeology
## Quantifying Hidden Clinical Trial History

---

### What this notebook does

1. Loads a collection, `collections/<COLLECTION>.csv` (set in section 1): INN, current code and legacy codes per row
2. Searches AACT for clinical trials by INN and by development code
3. Identifies "hidden" trials — those found only via a development code, not via the INN
4. Records which field, value and rule matched each trial (for verification)
5. Exports results with match evidence to `trial_archaeology/output/`

### Search Strategy

- **INN:** substring of `interventions.name`
- **Development codes:** the shared matching rule `patterns/aact_matching.py` — code as a token in five fields,
  ruled study-code patterns in `id_information.id_value`, code-scoped exclusions. Details and worked cases in section 4.

### Key Outputs

`trial_archaeology_<COLLECTION>_<timestamp>.xlsx`:
- **Summary sheet:** Per-drug trial counts (INN vs codes)
- **All_Trials sheet:** Every trial with match evidence
- **Hidden_Trials sheet:** Trials found ONLY via development codes
- **Residue sheet:** id_information values containing a code key, matched by no rule; counted = trial already in All_Trials for the same INN
- **Statistics sheet:** Overall metrics, collection, AACT last update, code fields, study-code patterns

`trials_verification_<COLLECTION>_<timestamp>.csv`: All_Trials as CSV

---

*Data source: AACT (Aggregate Analysis of ClinicalTrials.gov)*  
*Documentation: https://aact.ctti-clinicaltrials.org/schema*
'''))

cells.append(markdown_cell(r'''
## 1. Configuration
'''))

cells.append(code_cell(r'''
# =============================================================================
# AACT DATABASE CREDENTIALS (REQUIRED)
# Get free account at: https://aact.ctti-clinicaltrials.org/users/sign_up
# =============================================================================

import os

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

COLLECTION = "fda_novel_2025"
COLLECTION_FILE = f"../../collections/{COLLECTION}.csv"

OUTPUT_DIR = f"{REPO_ROOT}/trial_archaeology/output"

# Matching rule: patterns/aact_matching.py (section 4); study-code patterns: patterns/study_code_patterns.csv
PATTERNS_FILE = f"{REPO_ROOT}/patterns/study_code_patterns.csv"

'''))

cells.append(markdown_cell(r'''
## 2. Setup
'''))

cells.append(code_cell(r'''
import pandas as pd
import psycopg2
import re
from datetime import datetime
import warnings
warnings.filterwarnings('ignore', message='.*pandas only supports SQLAlchemy.*')

import openpyxl  # Excel export; fails here if missing

print(f"Analysis started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
'''))

cells.append(code_cell(r'''
# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_connection():
    """Create a new database connection."""
    return psycopg2.connect(
        host=AACT_HOST, port=AACT_PORT, database=AACT_DATABASE,
        user=AACT_USER, password=AACT_PASSWORD,
        options=f"-c search_path={AACT_SCHEMA}"
    )

def run_query(query, params=None):
    """Execute a query and return results as DataFrame."""
    conn = get_connection()
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()

# Test connection and show database stats (fails here if AACT is unreachable)
stats = run_query("""
    SELECT 
        (SELECT COUNT(*) FROM studies) as total_studies,
        (SELECT COUNT(*) FROM interventions) as total_interventions,
        (SELECT COUNT(*) FROM intervention_other_names) as total_other_names,
        (SELECT MAX(updated_at) FROM studies) as last_update
""")
AACT_LAST_UPDATE = str(stats['last_update'].iloc[0])
print(f"✓ Connected to AACT database")
print(f"  Studies:                  {stats['total_studies'].iloc[0]:,}")
print(f"  Interventions:            {stats['total_interventions'].iloc[0]:,}")
print(f"  Intervention other names: {stats['total_other_names'].iloc[0]:,}")
print(f"  Last update (studies):    {AACT_LAST_UPDATE}")
'''))

cells.append(markdown_cell(r'''
## 3. Drug Collection

Loaded from `collections/<COLLECTION>.csv`, columns `brand, inn, current_code, legacy_codes, sponsor`.
Provenance of each collection and its codes: `collections/README.md`.

**Code types:**
- **Current Code:** Sponsor's code at time of approval
- **Legacy Codes:** Earlier codes from originators, licensors, previous owners or partners
'''))

cells.append(code_cell(r'''
# =============================================================================
# DRUG COLLECTION — loaded from collections/<COLLECTION>.csv (COLLECTION set in section 1)
# =============================================================================

drugs_df = pd.read_csv(COLLECTION_FILE, dtype=str, keep_default_na=False)
drugs_df = drugs_df.rename(columns={'brand': 'Brand', 'inn': 'INN', 'current_code': 'Current_Code',
                                    'legacy_codes': 'Legacy_Codes', 'sponsor': 'Sponsor'})
drugs_df = drugs_df[['Brand', 'INN', 'Current_Code', 'Legacy_Codes', 'Sponsor']]
drugs_df['Legacy_Codes'] = drugs_df['Legacy_Codes'].apply(lambda x: [c.strip() for c in x.split(';')] if x else [])
drugs_df['Legacy_Codes_Str'] = drugs_df['Legacy_Codes'].apply(lambda x: '; '.join(x) if x else '')

print(f"Collection: {COLLECTION}")
print(f"Loaded {len(drugs_df)} drugs")
print(f"  With current code: {(drugs_df['Current_Code'] != '').sum()}")
print(f"  With legacy codes: {(drugs_df['Legacy_Codes'].apply(len) > 0).sum()}")
print(f"  Total codes to search: {(drugs_df['Current_Code'] != '').sum() + drugs_df['Legacy_Codes'].apply(len).sum()}")

'''))

cells.append(markdown_cell(r'''
## 4. Matching Rule

One rule for code harvest and trial archaeology, defined in `patterns/aact_matching.py` and pasted below by
the builder (`trial_archaeology/tools/build_archaeology_notebook.py`). Do not edit the cell here.

- **Code as a token:** no letter or digit directly before or after the code, in every spelling
  (as given, no separator, space/hyphen swapped, prefix/number split). MK-3475 finds MK-3475-001 but not MK-3475A.
- **Study-code patterns:** ruled rows of `patterns/study_code_patterns.csv` find codes embedded in sponsor
  study codes, e.g. CLOU064A1301 for LOU064.
- **Exclusions:** code-scoped, for token collisions the rule cannot see (XM02-ONC-201 for ONC201).
- **Worked cases** are asserts at the end of the cell; the cell fails if the rule changes.

### Fields Searched

| Table | Field | Purpose |
|-------|-------|--------|
| `interventions` | `name` | Primary drug/intervention name (also INN search) |
| `intervention_other_names` | `name` | Aliases, synonyms, development codes |
| `studies` | `official_title`, `brief_title` | Trial titles (may contain code) |
| `id_information` | `id_value` | Sponsor study codes and secondary IDs |
'''))

cells.append(code_cell(MATCHING_SRC))

cells.append(code_cell(r'''
PATTERNS = load_patterns(PATTERNS_FILE)
print(f"Study-code patterns in use: {[p['pattern_id'] for p in PATTERNS]}")
'''))

cells.append(code_cell(r'''
# =============================================================================
# SEARCH FUNCTIONS
# =============================================================================

def get_trial_details(nct_ids):
    """
    Fetch trial metadata for a set of NCT IDs.
    
    Returns: phase, start_date, overall_status, enrollment, brief_title
    """
    if not nct_ids:
        return pd.DataFrame()
    nct_list = list(nct_ids)
    placeholders = ','.join(['%s'] * len(nct_list))
    query = f"""
        SELECT s.nct_id, s.phase, s.start_date, s.overall_status,
               s.enrollment, s.brief_title, s.official_title
        FROM studies s
        WHERE s.nct_id IN ({placeholders})
        ORDER BY s.start_date NULLS LAST
    """
    return run_query(query, tuple(nct_list))


print("✓ Search functions defined")
print(f"  Code fields: {[label for label, _, _ in CODE_FIELDS]}")
'''))

cells.append(markdown_cell(r'''
## 5. Run Analysis

This cell iterates through all drugs and searches for trials.

**Output columns:**
- **INN:** Trials found by generic name
- **Curr:** Trials found by current development code
- **Leg:** Trials found by legacy codes
- **Hidden:** Trials found ONLY by codes (not INN)
'''))

cells.append(code_cell(r'''
# =============================================================================
# MAIN ANALYSIS LOOP
# =============================================================================

print("Searching AACT database...")
print("=" * 90)
print(f"{'Drug':<28} {'INN':<6} {'Curr':<6} {'Leg':<6} {'Hidden':<8} Status")
print("=" * 90)

results = []
all_matches = []

for idx, drug in drugs_df.iterrows():
    brand = drug['Brand']
    inn = drug['INN']
    current_code = drug['Current_Code']
    legacy_codes = drug['Legacy_Codes']
    
    # -------------------------------------------------------------------------
    # 1. INN Search
    # -------------------------------------------------------------------------
    inn_matches = trials_for_inn(run_query, inn)
    inn_matches['search_type'] = 'INN'
    inn_matches['Brand'] = brand
    inn_matches['INN'] = inn
    all_matches.append(inn_matches)
    inn_ncts = set(inn_matches['nct_id'].tolist()) if len(inn_matches) > 0 else set()
    
    # -------------------------------------------------------------------------
    # 2. Current Code Search
    # -------------------------------------------------------------------------
    current_codes = [c.strip() for c in current_code.split(';') if c.strip()]
    current_matches = pd.concat([trials_for_code(run_query, c, PATTERNS) for c in current_codes],
                                ignore_index=True) if current_codes else pd.DataFrame()
    if len(current_matches) > 0:
        current_matches['code_label'] = current_code
        current_matches['search_type'] = 'Current_Code'
        current_matches['Brand'] = brand
        current_matches['INN'] = inn
        all_matches.append(current_matches)
    current_ncts = set(current_matches['nct_id'].tolist()) if len(current_matches) > 0 else set()
    
    # -------------------------------------------------------------------------
    # 3. Legacy Code Search
    # -------------------------------------------------------------------------
    legacy_ncts = set()
    for lc in legacy_codes:
        lc_matches = trials_for_code(run_query, lc, PATTERNS)
        if len(lc_matches) > 0:
            lc_matches['code_label'] = lc
            lc_matches['search_type'] = 'Legacy_Code'
            lc_matches['Brand'] = brand
            lc_matches['INN'] = inn
            all_matches.append(lc_matches)
            legacy_ncts.update(lc_matches['nct_id'].tolist())
    
    # -------------------------------------------------------------------------
    # Calculate hidden trials (found by code but NOT by INN)
    # -------------------------------------------------------------------------
    hidden_current = current_ncts - inn_ncts
    hidden_legacy = legacy_ncts - inn_ncts
    all_ncts = inn_ncts | current_ncts | legacy_ncts
    total_hidden = len(all_ncts - inn_ncts)   # union: a trial found by both current and legacy code counts once
    
    results.append({
        'Brand': brand,
        'INN': inn,
        'Current_Code': current_code,
        'Legacy_Codes': '; '.join(legacy_codes) if legacy_codes else '',
        'Trials_via_INN': len(inn_ncts),
        'Trials_via_Current': len(current_ncts),
        'Trials_via_Legacy': len(legacy_ncts),
        'Hidden_via_Current': len(hidden_current),
        'Hidden_via_Legacy': len(hidden_legacy),
        'Total_Hidden': total_hidden,
        'Total_Unique': len(all_ncts),
        'INN_NCTs': inn_ncts,
        'Current_NCTs': current_ncts,
        'Legacy_NCTs': legacy_ncts,
    })
    
    status = f"⚠️ {total_hidden} hidden" if total_hidden > 0 else "✓"
    print(f"{brand:<28} {len(inn_ncts):<6} {len(current_ncts):<6} {len(legacy_ncts):<6} {total_hidden:<8} {status}")

all_matches_df = pd.concat(all_matches, ignore_index=True) if all_matches else pd.DataFrame()
print("=" * 90)
print(f"\n✓ Analysis complete. Total match records: {len(all_matches_df):,}")
'''))

cells.append(code_cell(r'''
# =============================================================================
# SUMMARY STATISTICS
# =============================================================================

results_df = pd.DataFrame([{k: v for k, v in r.items() if not k.endswith('_NCTs')} for r in results])

total_unique = results_df['Total_Unique'].sum()
total_inn = results_df['Trials_via_INN'].sum()
total_hidden_current = results_df['Hidden_via_Current'].sum()
total_hidden_legacy = results_df['Hidden_via_Legacy'].sum()
total_hidden = results_df['Total_Hidden'].sum()   # per-drug union, no double count

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Total unique trials found:     {total_unique:,}")
print(f"Trials via INN:                {total_inn:,}")
print(f"Hidden via current code:       {total_hidden_current:,} ({total_hidden_current/total_unique*100:.1f}%)")
print(f"Hidden via legacy code:        {total_hidden_legacy:,} ({total_hidden_legacy/total_unique*100:.1f}%)")
print(f"Total hidden:                  {total_hidden:,} ({total_hidden/total_unique*100:.1f}%)")
print(f"\nDrugs with hidden trials:      {(results_df['Total_Hidden'] > 0).sum()} of {len(results_df)}")
'''))

cells.append(markdown_cell(r'''
## 5b. Residue — id_information values for human review

`id_information` values that contain a code key (separators ignored) but that neither the token rule nor a
ruled study-code pattern matches. Candidates for a new pattern or exclusion under the admission rule in
`patterns/README.md`. Never fed back into the counts.
'''))

cells.append(code_cell(r'''
residue_rows = []
for _, drug in drugs_df.iterrows():
    codes = [c.strip() for c in drug['Current_Code'].split(';') if c.strip()] + list(drug['Legacy_Codes'])
    for code in codes:
        r = residue(run_query, code, PATTERNS)
        if len(r) > 0:
            r.insert(0, 'code', code)
            r.insert(0, 'INN', drug['INN'])
            r.insert(0, 'Brand', drug['Brand'])
            residue_rows.append(r)

residue_df = (pd.concat(residue_rows, ignore_index=True) if residue_rows
              else pd.DataFrame(columns=['Brand', 'INN', 'code', 'nct_id', 'id_value']))
residue_df = residue_df.sort_values(['Brand', 'INN', 'code', 'nct_id']).reset_index(drop=True)
print(f"Residue: {len(residue_df)} id_information values, {residue_df['code'].nunique()} codes, "
      f"{residue_df['nct_id'].nunique()} trials")
display(residue_df.head(20))
'''))

cells.append(markdown_cell(r'''
## 6. Build Verification Table

Creates a per-trial table showing exactly what matched where.

**Purpose:** Enable human review for false positives.

**Columns:**
- `Found_via_*`: Boolean flags for how the trial was found
- `*_Match_Field`: Which database field matched
- `*_Match_Term`: Which search term matched
- `*_Match_Value`: The actual text that matched (for verification)
'''))

cells.append(code_cell(r'''
# =============================================================================
# BUILD PER-TRIAL TABLE WITH MATCH EVIDENCE
# =============================================================================

trial_records = []

for r in results:
    brand, inn = r['Brand'], r['INN']
    current_code, legacy_codes = r['Current_Code'], r['Legacy_Codes']
    inn_ncts, current_ncts, legacy_ncts = r['INN_NCTs'], r['Current_NCTs'], r['Legacy_NCTs']
    all_ncts = inn_ncts | current_ncts | legacy_ncts
    
    for nct_id in all_ncts:
        trial_records.append({
            'nct_id': nct_id,
            'Brand': brand,
            'INN': inn,
            'Current_Code': current_code,
            'Legacy_Codes': legacy_codes,
            'Found_via_INN': nct_id in inn_ncts,
            'Found_via_Current': nct_id in current_ncts,
            'Found_via_Legacy': nct_id in legacy_ncts,
        })

trials_df = pd.DataFrame(trial_records)

# Add match detail columns
def get_match_info(nct_id, search_type):
    """Get match details for a trial and search type."""
    matches = all_matches_df[(all_matches_df['nct_id'] == nct_id) & 
                              (all_matches_df['search_type'] == search_type)]
    if len(matches) == 0:
        return '', '', ''
    fields = '; '.join(matches['matched_field'].unique())
    terms = '; '.join(matches['search_term'].unique())
    vals = '; '.join([str(v)[:60] for v in matches['matched_value'].unique()[:2]])
    return fields, terms, vals

print("Adding match details...")
for stype in ['INN', 'Current_Code', 'Legacy_Code']:
    key = stype.split('_')[0] if '_' in stype else stype
    fields, terms, vals = [], [], []
    for nct in trials_df['nct_id']:
        f, t, v = get_match_info(nct, stype)
        fields.append(f)
        terms.append(t)
        vals.append(v)
    trials_df[f'{key}_Match_Field'] = fields
    trials_df[f'{key}_Match_Term'] = terms
    trials_df[f'{key}_Match_Value'] = vals

# Get trial details
print("Fetching trial details...")
details = get_trial_details(set(trials_df['nct_id']))
trials_complete = trials_df.merge(details, on='nct_id', how='left')

# INN in brief or official title: such trials are hidden from an intervention-name search,
# but a full-text search on ClinicalTrials.gov would find them
trials_complete['INN_in_Title'] = [
    inn.lower() in f"{b} {o}".lower()
    for inn, b, o in zip(trials_complete['INN'], trials_complete['brief_title'], trials_complete['official_title'])
]

# Found only via a study-code pattern (patterns/study_code_patterns.csv): every code match came from a pattern
# rule (P1, P2, ...), none from a token match, and the trial is not found via INN
code_rules = (all_matches_df[all_matches_df['search_type'].isin(['Current_Code', 'Legacy_Code'])]
              .groupby(['nct_id', 'INN'])['rule'].agg(set))
pattern_only = {key for key, rules in code_rules.items() if 'token' not in rules}
trials_complete['Found_only_via_pattern'] = [
    (n, i) in pattern_only and not f
    for n, i, f in zip(trials_complete['nct_id'], trials_complete['INN'], trials_complete['Found_via_INN'])
]

# Reorder columns for readability
cols = ['nct_id', 'Brand', 'INN',
        'Found_via_INN', 'INN_Match_Field', 'INN_Match_Term', 'INN_Match_Value',
        'Found_via_Current', 'Current_Match_Field', 'Current_Match_Term', 'Current_Match_Value',
        'Found_via_Legacy', 'Legacy_Match_Field', 'Legacy_Match_Term', 'Legacy_Match_Value',
        'Current_Code', 'Legacy_Codes', 'INN_in_Title', 'Found_only_via_pattern', 'phase', 'start_date', 'overall_status', 'brief_title']
cols = [c for c in cols if c in trials_complete.columns]
trials_complete = trials_complete[cols]

# Deterministic row order: runs can be compared row by row
trials_complete = trials_complete.sort_values(['Brand', 'INN', 'nct_id']).reset_index(drop=True)

print(f"✓ Built verification table: {len(trials_complete)} trials")

# Residue (section 5b): counted = trial already in All_Trials for the same INN (review aid, not fed into counts)
counted_keys = set(zip(trials_complete['nct_id'], trials_complete['INN']))
residue_df['counted'] = [(n, i) in counted_keys for n, i in zip(residue_df['nct_id'], residue_df['INN'])]
not_counted = residue_df[~residue_df['counted']]
print(f"Residue: {len(residue_df)} values, {residue_df['counted'].sum()} in counted trials; "
      f"not counted: {len(not_counted)} values in {not_counted['nct_id'].nunique()} trials")
'''))

cells.append(code_cell(r'''
# =============================================================================
# HIDDEN TRIALS ANALYSIS
# =============================================================================

hidden = trials_complete[~trials_complete['Found_via_INN']].copy()
print(f"\nHidden trials (not found via INN): {len(hidden)}")
print(f"  of which INN appears in the title: {hidden['INN_in_Title'].sum()}"
      f" — hidden from intervention search only; {(~hidden['INN_in_Title']).sum()} hidden from both")
print(f"  of which found only via a study-code pattern: {hidden['Found_only_via_pattern'].sum()}")

# Breakdown by match field (to see impact of intervention_other_names)
print("\nHidden trials by match field:")
for field in hidden['Current_Match_Field'].dropna().unique():
    if field:
        count = (hidden['Current_Match_Field'].str.contains(field, na=False)).sum()
        print(f"  {field}: {count}")

for field in hidden['Legacy_Match_Field'].dropna().unique():
    if field:
        count = (hidden['Legacy_Match_Field'].str.contains(field, na=False)).sum()
        print(f"  {field}: {count}")

# Display sample with match evidence
print("\nSample hidden trials:")
display_cols = ['nct_id', 'INN', 'Found_via_Current', 'Current_Match_Field', 
                'Current_Match_Term', 'Found_via_Legacy', 'Legacy_Match_Term', 'brief_title']
display(hidden[display_cols].head(15))
'''))

cells.append(markdown_cell(r'''
## 7. Export Results
'''))

cells.append(code_cell(r'''
# =============================================================================
# EXPORT TO EXCEL AND CSV
# =============================================================================

timestamp = datetime.now().strftime('%Y%m%d_%H%M')

# Excel export (multiple sheets)
excel_file = f"{OUTPUT_DIR}/trial_archaeology_{COLLECTION}_{timestamp}.xlsx"

with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
    # Summary per drug
    results_df.to_excel(writer, sheet_name='Summary', index=False)
    
    # All trials with match evidence
    trials_complete.to_excel(writer, sheet_name='All_Trials', index=False)
    
    # Hidden trials only (for focused review)
    hidden.to_excel(writer, sheet_name='Hidden_Trials', index=False)

    # Residue: id_information values containing a code key, matched by no rule (human review only)
    residue_df.to_excel(writer, sheet_name='Residue', index=False)
    
    # Statistics
    stats = pd.DataFrame({
        'Metric': [
            'Analysis date', 
            'Collection',
            'AACT last update (studies.updated_at)',
            'Total drugs', 
            'Total unique trials',
            'Trials via INN', 
            'Hidden via current code', 
            'Hidden via legacy',
            'Total hidden', 
            'Pct hidden',
            '',
            'Code fields',
            'Study-code patterns',
        ],
        'Value': [
            datetime.now().strftime('%Y-%m-%d %H:%M'), 
            COLLECTION,
            AACT_LAST_UPDATE,
            len(drugs_df), 
            total_unique, 
            total_inn, 
            total_hidden_current, 
            total_hidden_legacy,
            total_hidden, 
            f"{total_hidden/total_unique*100:.1f}%",
            '',
            '; '.join(label for label, _, _ in CODE_FIELDS),
            '; '.join(p['pattern_id'] for p in PATTERNS),
        ]
    })
    stats.to_excel(writer, sheet_name='Statistics', index=False)

print(f"✓ Exported: {excel_file}")

# CSV export
csv_file = f"{OUTPUT_DIR}/trials_verification_{COLLECTION}_{timestamp}.csv"
trials_complete.to_csv(csv_file, index=False)
print(f"✓ Exported: {csv_file}")
'''))

cells.append(markdown_cell(r'''
---

## Appendix: Schema Reference

### Tables Used

| Table | Key Field | Purpose |
|-------|-----------|--------|
| `studies` | `nct_id`, `official_title` | Core trial metadata |
| `interventions` | `name` | Primary intervention/drug names |
| `intervention_other_names` | `name` | Aliases, synonyms, development codes |
| `id_information` | `id_value` | Secondary IDs including sponsor protocol codes |

### AACT Documentation

- Schema: https://aact.ctti-clinicaltrials.org/schema
- Data dictionary: https://aact.ctti-clinicaltrials.org/data_dictionary

### Sponsor Code Prefixes

Source: https://en.wikipedia.org/wiki/List_of_pharmaceutical_compound_number_prefixes

| Sponsor | Pattern | Example |
|---------|---------|--------|
| AstraZeneca | AZD + numbers | AZD0914 |
| Bayer | BAY + space + numbers | BAY 3427080 |
| Boehringer Ingelheim | BI + space + numbers | BI 1015550 |
| GSK | GSK + numbers | GSK2140944 |
| Novartis | LOU + numbers | LOU064 |
| Pfizer | PF- + numbers | PF-04554878 |
| Vertex | VX- + numbers | VX-548 |
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
