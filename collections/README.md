# Collections

One CSV per collection. A collection is a list of marketed products to trace through development codes.

## fda_novel_2025.csv

FDA novel drug approvals 2025. Copied by script from `development_code_trial_archaeology.ipynb` (October 2026).

| Column | Content |
|--------|---------|
| `brand` | US brand name |
| `inn` | INN |
| `current_code` | Sponsor code at approval |
| `legacy_codes` | Earlier codes, `; `-separated |
| `sponsor` | Sponsor(s) |
| `ncit_code` | NCI Thesaurus concept per INN (added 2026-11-07; read by the code harvest only) |
| `moiety_unii` | FDA UNII per NCIt concept (added 2026-11-07) |

Codes verified against DrugBank, AdisInsight, Wikipedia, company press releases and SEC filings, patent assignee
history and PubChem synonym lists. NSC (NCI) codes excluded except Grafapex (only code).

Kygevvi (doxecitine and doxribtimine) is a combination; the February 2026 PubChem checks excluded it (29 single-entity drugs; `site/notes/00-where-it-started.md`).

`ncit_code` and `moiety_unii`, 2026-11-07: NCIt exact-name search per INN (NCI EVS API, NCIt 26.10d), concept property
`FDA_UNII_Code`; each UNII cross-checked in GSRS (preferred name, substance class, active-moiety relationship).
One NCIt concept per INN; no UNII is a salt. Accepted by KF 2026-11-07. Flags:
- rilzabrutinib: GSRS substance class mixture, (E)- and (Z)-isomers; NWN58M4F5T is its own active moiety in GSRS.
- sepiapterin: GSRS record has no relationships, so the active-moiety relation cannot be checked; single neutral
  moiety C9H11N5O3, the only GSRS substance of that name.

Kygevvi is left out of the code harvest (`EXCLUDE_BRANDS` in `code_harvest/tools/build_harvest_notebook.py`,
KF 2026-11-07): its only code, MT-1621, names the combination, and the components are the nucleosides
deoxycytidine and thymidine. Its `ncit_code` and `moiety_unii` are therefore empty. Looked up, for the record:
doxecitine C420 / 0W860991D6; doxribtimine C880 (NCIt preferred name Thymidine) / VC2W18DGKR.
It stays in this file unchanged for trial archaeology.

Code harvest, 2026-11-07 (AACT 2026-11-07): 81 candidates for 29 brands; 8 URL-cited web candidates for December codes
the harvest did not find (`fda_novel_2025_web_candidates.csv`). Review walked through by KF and Claude,
conservative/strict: 61 review rows, 54 confirmed by KF, 7 held (`claude-proposed`): atrasentan CHK-01, EXV811 (prefix
origin not verified); avutometinib CKI-27, R-7304, RG7304 and mirdametinib PD-901 (AACT only in academic records that
copy the NCIt synonym list, not independent of NCIt); vimseltinib DP-6865 (no trials). Held rows stay in search
(precedent AGN241780, CH5534262); all their trials name the INN. The other 20 candidates are PubChem-only without
trials (`unconfirmed`).

Review against this file (the December codes are not changed here; trial archaeology keeps using them):
- Classes reversed: acoltremon AR-15512 current, AVX-012 legacy (Avizorex code, NCT03162094; Aerie acquired Avizorex
  2019); atrasentan ABT-627 legacy (Abbott); delgocitinib LEO 124249 current (LEO sponsors the US approval), JTE-052 legacy
  (Japan Tobacco). Elamipretide SS-31 legacy (Szeto-Schiller research name), no current code.
- Tryptyr `sponsor` "Averitas/Arcutis" matches none of the sources (Avizorex, Aerie, Alcon).
- Treosulfan NSC-39069: `not_a_code` (NSC number), not used in the harvest output; 0 trials.
- Combinations kept out: aceclidine PRX-100 (aceclidine + tropicamide, NCT03201562), LNZ101 (aceclidine + brimonidine).
- Added by the harvest: taletrectinib DS-6051, DS-6051a (free base of DS-6051b, NCT02279433); mirdametinib PD-325901;
  held: CHK-01, EXV811, CKI-27, R-7304, RG7304, PD-901, DP-6865.
- Accepted on one Registry line: LNZ100, SAR444671, DS-6051b, and the held CHK-01, EXV811.
- For Wikidata, beyond D0–D10: SS-31 and TIC10 are research names, not company codes (hold); ETX0914 is web-only (hold).

## top_sellers_fy2025.csv

Top three selling medicines per company, FY2025, for 12 companies with FY2025 revenue USD 41–65 B.
Source: graphic by Joanna Sadowska, PhD, shared by Spencer Knight on LinkedIn
(https://www.linkedin.com/feed/update/urn:li:activity:7516079780761427969/), based on company financial reports.
Brand names and revenue figures read from the graphic on 2026-10-14.

Excluded: vaccines (Shingrix, Gardasil 9, ProQuad, Prevnar 20, Flublok, Quadracel). The graphic itself marks
Quadracel and Flublok as "(example)".

| Column | Content |
|--------|---------|
| `company` | Company as in the graphic |
| `company_fy2025_revenue_usd_b` | Total FY2025 company revenue, USD billion, as in the graphic |
| `brand` | Brand |
| `inn` | Active moiety INN(s); `; `-separated for combinations |
| `ncit_code` | NCI Thesaurus concept per INN |
| `moiety_unii` | FDA UNII per NCIt concept |
| `is_combination` | Y/N |
| `brand_to_inn_source` | openFDA drug label, or NCIt brand synonym where openFDA had no label match |

Notes:
- Eliquis appears twice (BMS and Pfizer). Semaglutide (Ozempic, Wegovy, Rybelsus) and tirzepatide (Mounjaro, Zepbound)
  are shared across brands. Trial search is therefore by active moiety, not by brand.
- Umeclidinium: NCIt concept and UNII are for umeclidinium bromide, not the free moiety.

Trial archaeology, AACT snapshot 2026-10-15, shared matching rule (`patterns/aact_matching.py`): 631 of 11,027
trials (5.7%) found only via a development code (556 unique trials; 418 of these have the INN in neither the brief
nor the official title). 101 of the 631 (82 unique trials) are found only via a sponsor study-code pattern
(`patterns/study_code_patterns.csv`).
Product Clan check (option 2, single-moiety codes of other products from the review file): +3 hidden trials,
all dapagliflozin, Boryung trial labels (BR3006A, BR3003C; identity inferred from sibling trials).

## <collection>_code_review.csv

Human review of harvested candidate codes (see `code_harvest/`).

| Column | Content |
|--------|---------|
| `inn`, `code_key` | Candidate: INN × code with case and separators removed |
| `code_class` | current, legacy, partner, other_product, biosimilar, other_drug, typo, not_a_code |
| `use_in_search` | Y/N |
| `rationale` | Evidence behind the class |
| `reviewer` | `claude-proposed` until confirmed by a person |
| `verification` | Outcome of an independent check: confirmed, unresolved, refuted, or AACT record read; date and source |
| `clan_relation` | For other_product: combination, pharmaceutical_product, medicinal_product, trial_label |

## <collection>_code_evidence.csv, <collection>_codes.csv

Written by `code_harvest/notebooks/development_code_harvest.ipynb`: all candidates with sources and AACT evidence,
and the accepted codes per brand.
