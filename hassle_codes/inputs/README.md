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
| `hassle_findings_2026-11-26.csv` | 2026-11-26 | US 3594478, a second print of the benzothiophene table (all 24 rows agree; H 53/84 conflict and H 43/49 missing branch are in both prints); corrections H 11/46 and H 26/38 (meta, not ortho) after checking all 76 table rows against the PDFs; the 1965 family (SE 7128/65): none of the 8 members published before 1969-11-10 prints the codes; the 1971 zimelidine family (SE 5496/71): codes printed in SE, BE, FR, NL and GB, not in DE; five new codes (H 102/01, 102/04, 102/30, 94/94, 99/68) first in BE 781105; no EPO page images of the omeprazole Swedish application SE 7804231 | Google Patents PDF and family pages; PubChem patent mappings; page images from EPO OPS | `notebooks/hassle_pubchem_patents.ipynb` (known patents); `make_hassle_h_codes_all.py` (rows with a code) |
| `hassle_findings_2026-11-27.csv` | 2026-11-27 | EP 0005129 A1 (1979 filing of the omeprazole family SE 7804231): omeprazole is Example 23 and in claim 7, applicant AB Hässle, but no compound codes are printed (examples by number only); its search report cites DE-A-2 548 340 (AB Hässle, filed 1975-10-29, published 1977-07-14), which also prints no codes | page images from EPO OPS | `make_hassle_h_codes_all.py` (rows with a code) |

## Background

- Research notes and session notes are kept in the claude.ai project "Products in clinical trials", not in this repo.
- 2026-11-26: after a talk with Chris Southan, his post
  [ACS Fall 2026 First disclosures: PubChem and patent mappings](https://cdsouthan.blogspot.com/2026/09/acs-fall-2026-first-disclosures-in.html)
  gave the method behind `hassle_pubchem_patents.ipynb`: PubChem patent mappings, salt records, and the
  submitter-level (SID) name search to see who first linked a code to a structure.
- Field note 04: <https://kerfors.github.io/development-code-archaeology/notes/04-hassle-what-we-learned.html>
