---
title: "Before the repository: December 2025 and February 2026"
description: "The holiday project that started it, and a short test of code to structure in PubChem: method, results and what carried over."
date: 2026-11-08
covers: December 2025 – February 2026
order: 0
---

# Before the repository: December 2025 and February 2026

The repository starts in October 2026. Two earlier rounds of work led to it. Their notebooks are not
part of the repository; this post records what was done and what was learned.

## December 2025: development codes and hidden trials

A holiday project ("mellandagsprojekt"). The question: how much of the ClinicalTrials.gov history of the
2025 FDA novel small-molecule approvals can be found by INN alone, and how much only by development code?

Method, in three steps:

1. AI-assisted discovery of candidate codes (Claude, Gemini) from press releases, patent filings and
   early trial registrations. Prompt below.
2. Verification by web search against company, regulator and reference sources. This step caught
   fabricated codes: for elamipretide, "SBT-31" and "SPI-31" appeared in no source at all.
3. AACT queries, INN against codes, with word-boundary matching for short codes ("SS-31" matched
   "COMPASS31"; "WS-12" matched "AEWS1221").

Published 30 December 2025:

- [LinkedIn post](https://www.linkedin.com/feed/update/urn:li:activity:7411710435722280960/)
- [Data Archaeology: Tracing Drug Development Codes Through Name Changes, Mergers, and Licensing Deals](https://www.linkedin.com/pulse/data-archaeology-tracing-drug-development-codes-through-forsberg-89t1e/)
- [Searching AACT for Development Codes: A Practical Guide](https://www.linkedin.com/pulse/searching-aact-development-codes-practical-guide-kerstin-forsberg-2rhze/)

Result as published: of 572 trials, 191 (33%) reachable only by a development code; 147 via the
current sponsor code, 44 via legacy codes. 24 of 29 drugs had hidden trials.

The same collection rerun in October 2026 with the shared matching rule of the repository, AACT snapshot
2026-10-16: 197 of 679 drug–trial pairs reachable only by a code (29.0%); 655 distinct trials, the 197
hidden ones all distinct; 26 of 30 drugs with hidden trials. The matching rule and the snapshot both changed;
their effects are not separated. Whether the December total counted drug–trial pairs or distinct trials is
not recorded.

### Discovery prompt (December 2025)

```markdown
# Drug Development Code Discovery

## Your Role
Data archaeologist finding historical development codes for approved drugs.

## Input
[Drug list with INN and Brand names]

## Task
For each drug, find:

1. **Current development code** - The sponsor's code at time of approval
2. **Legacy codes** - Earlier codes from:
   - Original discoverer (before licensing)
   - Previous corporate owner (before acquisition)
   - Academic/government origin (NIH, NCI codes if applicable)

## Search Strategy
- Phase 1 trial titles (often code-only, before INN assigned)
- "Drug X licensed from Company Y" announcements
- Patent assignee history
- Wikipedia "List of pharmaceutical compound number prefixes" for sponsor attribution

## Output Format
| INN | Current Code | Legacy Codes | Company Transitions | Confidence | Source Type |

## Critical Rules
- Mark uncertain codes as "VERIFY: [code]"
- Never invent codes - if you can't find it, say "None found"
- Distinguish code TYPES: development code (compound) vs protocol code (study)
- Note format variations you encountered (AZD-0914 vs AZD0914)
```

### Lessons (December 2025)

- AI discovery needs verification: it produces plausible codes that exist nowhere.
- Format tolerance: AZD-0914, AZD0914 and AZD 0914 are the same code.
- Short codes need word-boundary matching.
- Sponsor study codes can embed the development code (CLOU064A2402 contains LOU064).

## February 2026: development code to structure (PubChem)

Exploratory, after discussions with Chris Southan (TW2Informatics) on structure coverage. The December
work tested code → trials; this tested code → structure via the PubChem PUG REST API.

**Launched drugs**: the 29 single-entity small molecules of the December set (Kygevvi, a combination,
excluded).

| Test | Result |
|------|--------|
| INN → CID with InChIKey | 29/29 |
| Current code → same CID as INN | 26/28 |
| Legacy code → same CID as INN | 10/13 |
| Legacy code → same parent CID (active moiety) | 11/13 |

Three failure modes:

1. **Salt form.** DS-6051b resolves to the adipate salt CID, the INN to the free base. The parent
   CID lookup shows the same active moiety. Not an error, but a direct CID comparison flags it.
2. **Substance/compound disconnect.** GSK1144814 exists as a synonym on a substance record (SID)
   that is not linked to the elinzanetant compound record. Present in PubChem, not findable by
   compound name search.
3. **Never deposited.** SAR444671, Sanofi's code for rilzabrutinib after the Principia acquisition,
   is absent from PubChem. The originator code PRN1008 resolves.

**Early-stage compounds**: 15 codes of AI-designed candidates in Phase I/II: 6 resolved at compound
level, 9 not deposited at all (type 3), none of type 2.

**Cross-references**: INN → CID, UNII, CAS, ChEMBL, DrugBank, parent CID. Of the 29: UNII 25,
ChEMBL 28, DrugBank 11. PubChem's additional codes (NSC numbers, suffix variants such as GSK1144814A)
did not appear in ClinicalTrials.gov.

## What carried over into October 2026

- **Active moiety as the unit.** The parent lookup became `moiety_unii` in the collections; UNII is
  also how Wikidata items are found.
- **No code without a source.** From the fabricated codes in December: every harvested code cites
  where it was seen, and the evidence rule needs two independent lines.
- **PubChem as a source, not as evidence on its own.** Synonyms are depositor aggregations. Codes
  found only in PubChem are set aside, and PubChem is not used as a Wikidata reference.
- **Token matching and residue review.** Word-boundary matching became the shared rule
  ([`patterns/aact_matching.py`](repo:patterns/aact_matching.py)); the residue report shows what the rule leaves out.

The December articles ended with open questions. Two of them are what the repository works on:

- *Are there databases that can be queried programmatically for development codes?* The code
  harvest (NCI Thesaurus, PubChem, AACT, cited web sources) with a checkable evidence rule.
- *Can open data communities help?* The Wikidata property P15001 "development code", created
  October 2026, with referenced statements.

Not carried over: patent counts per compound, and structure coverage by development phase. That is
Chris Southan's question, not this repository's.

Next: [Two 2025 collections: harvest, review, Wikidata](2026-11-08-two-2025-collections.html).
