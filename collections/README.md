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

Codes verified against DrugBank, AdisInsight, Wikipedia, company press releases and SEC filings, patent assignee
history and PubChem synonym lists. NSC (NCI) codes excluded except Grafapex (only code).

Kygevvi (doxecitine and doxribtimine) is a combination; the February 2026 PubChem checks excluded it (29 single-entity drugs; `docs/background.md`).

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
