# hassle_codes/inputs

Frozen input files for the Hässle H-code work. Each file was written once, in a named session, and is not
regenerated: a rerun of a harvest or notebook writes to `hassle_codes/output/` (not tracked), never here.
Every value in the Hässle lists and notebooks can be traced back to one of these files.

Patent source throughout: Google Patents (lists, full texts, PDFs). PubChem is used as a cross-check and for
patent mappings, never as a Wikidata reference.

| File | Made | What it holds | How it was made | Read by |
|---|---|---|---|---|
| `hassle_h_codes.csv` | harvest 2026-11-21, frozen 2026-11-22 | 53 H codes from ChEMBL, GSRS, MeSH, PubChem, NCIt, PubMed, Wikidata | `notebooks/hassle_h_code_harvest.ipynb` | `make_hassle_h_codes_all.py` |
| `hassle_h_codes_evidence.csv` | harvest 2026-11-21, frozen 2026-11-22 | one row per record that names a code (incl. PubMed affiliations) | same harvest | `make_hassle_h_codes_all.py` |
| `hassle_findings_2026-11-21.csv` | session 2, 2026-11-21 | patents and literature: code tables found by regex, structure matches, dates | Google Patents full texts (43 US patents), PubMed sweep of Hässle authors | `make_hassle_h_codes_all.py` |
| `hassle_findings_2026-11-21b.csv` | session 3, 2026-11-21 | patent PDFs read page by page: the two code tables printed without "H" (52 benzofurans, 24 benzothiophenes), more structure matches, candidates settled | Google Patents PDFs, read by eye | `make_hassle_h_codes_all.py` |
| `hassle_findings_2026-11-22.csv` | 2026-11-22 | PubMed records the harvest missed (H 319/68, H 77/67) | PubMed, read by eye | `make_hassle_h_codes_all.py` |
| `wikidata_unii_lookup_2026-11-22.csv` | 2026-11-22 | Wikidata items by UNII (P652); the query is in the file | Wikidata SPARQL | `make_hassle_h_codes_all.py` |
| `hassle_patent_tables_2026-11-26.csv` | 2026-11-26 | the two patent tables as one row per code: patent, core, A, R, R1, R2, NR3R4, when transcribed, when the page was checked against the PDF, note | benzofurans from `hassle_findings_2026-11-21b.csv`; benzothiophenes copied from the US 3558616 page images on 2026-11-26 | `notebooks/hassle_pubchem_patents.ipynb` |
| `hassle_findings_2026-11-26.csv` | 2026-11-26 | US 3594478, a second print of the benzothiophene table (all 24 rows agree; H 53/84 conflict and H 43/49 missing branch are in both prints); dates of the 1965 family members (BE, NL, GB, DE); how US 3594478 was found | Google Patents PDF and family pages; PubChem patent mappings | `notebooks/hassle_pubchem_patents.ipynb` (known patents); not yet read by `make_hassle_h_codes_all.py` |

## Background

- Research notes and session notes are kept in the claude.ai project "Products in clinical trials", not in this repo.
- 2026-11-26: after a talk with Chris Southan, his post
  [ACS Fall 2026 First disclosures: PubChem and patent mappings](https://cdsouthan.blogspot.com/2026/09/acs-fall-2026-first-disclosures-in.html)
  gave the method behind `hassle_pubchem_patents.ipynb`: PubChem patent mappings, salt records, and the
  submitter-level (SID) name search to see who first linked a code to a structure.
- Field note 04: <https://kerfors.github.io/development-code-archaeology/notes/04-hassle-what-we-learned.html>
